"""Authentication API endpoints for login and user profile inspection."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import UserRecord
from app.security.auth import (
    TokenResponse,
    UserLoginRequest,
    UserProfile,
    create_access_token,
    get_current_user,
    verify_password,
)
from app.services.audit_service import audit_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login_for_access_token(
    credentials: UserLoginRequest,
    db: Session = Depends(get_db),
):
    """Authenticate with username and password to obtain a JWT bearer token."""
    user = db.query(UserRecord).filter(UserRecord.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is deactivated.",
        )

    # Generate token
    token = create_access_token(
        data={"sub": user.username, "role": user.role, "name": user.full_name}
    )

    # Audit login event
    audit_service.log_event(
        db=db,
        actor_username=user.username,
        actor_role=user.role,
        action="USER_LOGIN",
        resource_type="auth",
        resource_id=user.id,
        details={"status": "success"},
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role=user.role,
        username=user.username,
        full_name=user.full_name,
    )


@router.get("/me", response_model=UserProfile)
def get_authenticated_user_profile(
    current_user: UserProfile = Depends(get_current_user),
):
    """Retrieve profile and permissions for the currently authenticated session."""
    return current_user
