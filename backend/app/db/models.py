"""SQLAlchemy models for forecasts, advisories, users, and hash-chained audit logs."""

from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text

from app.db.database import Base


class UserRecord(Base):
    """System users with role-based access control (viewer, meteorologist, admin)."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, default="viewer")  # viewer, meteorologist, admin
    full_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


class ForecastRecord(Base):
    """Database model for storing weather forecast inputs and computed severity."""

    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    region_name = Column(String(100), nullable=False, index=True)
    region_type = Column(String(20), nullable=False, index=True)  # plains, hilly, coastal
    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    forecast_tmax_c = Column(Float, nullable=False)
    normal_tmax_c = Column(Float, nullable=False)
    departure_c = Column(Float, nullable=False)
    severity = Column(String(30), nullable=False, index=True)  # NONE, HEATWAVE, SEVERE_HEATWAVE
    confidence = Column(Float, nullable=False, default=0.85)
    lead_time_days = Column(Integer, nullable=False, default=1)
    source = Column(String(50), nullable=False, default="synthetic")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


class AdvisoryRecord(Base):
    """Database model for storing generated stakeholder advisories with review state machine."""

    __tablename__ = "advisories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    forecast_id = Column(Integer, nullable=True, index=True)
    stakeholder = Column(String(50), nullable=False, index=True)
    language = Column(String(10), nullable=False, index=True)
    severity = Column(String(30), nullable=False, index=True)
    region_name = Column(String(100), nullable=False)
    date = Column(String(10), nullable=False)
    tmax_c = Column(Float, nullable=False)
    headline = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    actions_json = Column(Text, nullable=False)
    uncertainty_statement = Column(String(500), nullable=False)
    operator_notes = Column(String(500), nullable=True)
    raw_llm_response = Column(Text, nullable=True)

    # Verification & Fallback tracking
    verification_passed = Column(Boolean, default=False, nullable=False)
    verification_details = Column(Text, nullable=True)
    is_fallback = Column(Boolean, default=False, nullable=False)
    regeneration_count = Column(Integer, default=0, nullable=False)

    # Approval state machine: DRAFT -> PENDING_REVIEW -> APPROVED | REJECTED -> DISSEMINATED
    status = Column(String(30), nullable=False, default="DRAFT", index=True)
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_comments = Column(String(500), nullable=True)

    # Dissemination export stub
    disseminated_at = Column(DateTime(timezone=True), nullable=True)
    dissemination_payload = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


class AuditLogRecord(Base):
    """Append-only, SHA-256 hash-chained audit log for tamper evidence."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        index=True,
    )
    timestamp_str = Column(String(50), nullable=False)
    actor_username = Column(String(100), nullable=False, index=True)
    actor_role = Column(String(30), nullable=False)
    action = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(Integer, nullable=True)
    details_json = Column(Text, nullable=False)
    prev_hash = Column(String(64), nullable=False)
    current_hash = Column(String(64), nullable=False, unique=True, index=True)
