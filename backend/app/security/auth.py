"""Authentication, JWT token lifecycle, and Role-Based Access Control (RBAC)."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.db.models import UserRecord

security_bearer = HTTPBearer(auto_error=False)


class UserLoginRequest(BaseModel):
    """Credentials for authentication."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """JWT bearer token and authenticated user profile."""

    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    full_name: str


class UserProfile(BaseModel):
    """Active user profile representation."""

    id: int
    username: str
    role: str
    full_name: str
    is_active: bool


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    pw_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash."""
    try:
        pw_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pw_bytes, hash_bytes)
    except Exception:
        return False


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Generate signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(UTC)})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token has expired. Please re-authenticate.",
        ) from e
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token signature.",
        ) from e


def seed_default_users(db: Session) -> None:
    """Seed baseline role-based accounts if absent."""
    default_users = [
        {
            "username": "viewer@imd.gov.in",
            "password": "viewer123",
            "role": "viewer",
            "name": "General Viewer",
        },
        {
            "username": "meteorologist@imd.gov.in",
            "password": "meteo123",
            "role": "meteorologist",
            "name": "Senior Meteorologist Approver",
        },
        {
            "username": "admin@imd.gov.in",
            "password": "admin123",
            "role": "admin",
            "name": "System Administrator",
        },
    ]
    for u in default_users:
        existing = db.query(UserRecord).filter(UserRecord.username == u["username"]).first()
        if not existing:
            rec = UserRecord(
                username=u["username"],
                hashed_password=hash_password(u["password"]),
                role=u["role"],
                full_name=u["name"],
                is_active=True,
            )
            db.add(rec)
    db.commit()


def get_current_user(
    auth: HTTPAuthorizationCredentials | None = Depends(security_bearer),
    db: Session = Depends(get_db),
) -> UserProfile:
    """Dependency extracting and verifying authenticated user from Bearer JWT."""
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization Bearer header.",
        )

    payload = decode_access_token(auth.credentials)
    username: str | None = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing subject identifier.",
        )

    user = db.query(UserRecord).filter(UserRecord.username == username).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive or not found.",
        )

    return UserProfile(
        id=user.id,
        username=user.username,
        role=user.role,
        full_name=user.full_name,
        is_active=user.is_active,
    )


def require_role(allowed_roles: list[str]) -> Callable[[UserProfile], UserProfile]:
    """Dependency factory checking that user holds at least one of the allowed roles."""

    def role_checker(current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: role '{current_user.role}' not authorized. Requires: {allowed_roles}",
            )
        return current_user

    return role_checker
