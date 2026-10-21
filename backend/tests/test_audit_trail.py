"""Unit and integration tests for SHA-256 Hash-Chained Audit Trail and Metrics."""

import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.db.models import AuditLogRecord
from app.services.audit_service import audit_service


@pytest.fixture
def audit_db():
    """In-memory SQLite session fixture for audit tests."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def test_hash_chain_creation_and_integrity(audit_db):
    """Verify sequential creation of hash-chained blocks and cryptographic validation."""
    # Log 3 events
    e1 = audit_service.log_event(
        db=audit_db,
        actor_username="meteo1@imd.gov.in",
        actor_role="meteorologist",
        action="ADVISORY_GENERATED",
        resource_type="advisory",
        resource_id=101,
        details={"status": "DRAFT"},
    )
    assert e1.prev_hash == "0" * 64
    assert len(e1.current_hash) == 64

    e2 = audit_service.log_event(
        db=audit_db,
        actor_username="meteo1@imd.gov.in",
        actor_role="meteorologist",
        action="ADVISORY_APPROVED",
        resource_type="advisory",
        resource_id=101,
        details={"comments": "Passed check"},
    )
    assert e2.prev_hash == e1.current_hash

    e3 = audit_service.log_event(
        db=audit_db,
        actor_username="admin@imd.gov.in",
        actor_role="admin",
        action="ADVISORY_DISSEMINATED",
        resource_type="advisory",
        resource_id=101,
        details={"channel": "sms"},
    )
    assert e3.prev_hash == e2.current_hash

    # Verify integrity
    integrity = audit_service.verify_chain_integrity(audit_db)
    assert integrity["valid"] is True
    assert integrity["total_records"] == 3


def test_detects_tampered_audit_record(audit_db):
    """Modifying an existing audit log row must cause cryptographic verification to FAIL."""
    # Create 3 blocks
    for i in range(3):
        audit_service.log_event(
            db=audit_db,
            actor_username=f"user_{i}@imd.gov.in",
            actor_role="meteorologist",
            action="ACTION_STEP",
            resource_type="advisory",
            resource_id=i,
            details={"step": i},
        )

    # Intentionally tamper with record ID 2
    rec2 = audit_db.query(AuditLogRecord).filter(AuditLogRecord.id == 2).first()
    rec2.details_json = '{"step": 999, "tampered": true}'
    audit_db.commit()

    # Integrity verification must catch tampering
    check = audit_service.verify_chain_integrity(audit_db)
    assert check["valid"] is False
    assert check["tampered_record_id"] == 2
    assert "tampering detected" in check["reason"].lower()


def test_pii_redaction_in_audit_logs(audit_db):
    """Personal email or phone number in details must be automatically redacted."""
    sensitive_details = {
        "operator_contact": "alert.officer@gmail.com",
        "mobile": "+91 9876543210",
        "secret_token": "SUPER_SECRET_1234",
    }
    rec = audit_service.log_event(
        db=audit_db,
        actor_username="officer",
        actor_role="admin",
        action="LOG_SENSITIVE",
        resource_type="test",
        details=sensitive_details,
    )
    assert "alert.officer@gmail.com" not in rec.details_json
    assert "[REDACTED_PII]" in rec.details_json
    assert "SUPER_SECRET_1234" not in rec.details_json


@pytest.mark.asyncio
async def test_audit_and_metrics_api_endpoints(async_client: AsyncClient):
    """Test GET /api/v1/audit, GET /api/v1/audit/verify, and GET /api/v1/metrics."""
    # 1. Fetch audit log
    audit_res = await async_client.get("/api/v1/audit?limit=20")
    assert audit_res.status_code == 200
    assert isinstance(audit_res.json(), list)

    # 2. Check cryptographic verification endpoint
    verify_res = await async_client.get("/api/v1/audit/verify")
    assert verify_res.status_code == 200
    assert verify_res.json()["valid"] is True

    # 3. Check operational metrics endpoint
    metrics_res = await async_client.get("/api/v1/metrics")
    assert metrics_res.status_code == 200
    m_data = metrics_res.json()
    assert "forecasts" in m_data
    assert "advisories" in m_data
    assert "security_and_governance" in m_data
    assert m_data["security_and_governance"]["tamper_evident_chain_integrity"] is True
