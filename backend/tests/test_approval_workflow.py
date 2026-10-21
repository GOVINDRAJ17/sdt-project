"""Unit and integration tests for Approval Workflow, State Machine, RBAC, and Fallback."""

import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.domain.advisory_models import (
    AdvisoryGenerateRequest,
    LanguageCode,
    StakeholderType,
)
from app.domain.models import ForecastCreate, RegionType
from app.llm.mock import MockFailureMode, MockLLMClient
from app.security.auth import create_access_token, seed_default_users
from app.services.advisory_generator import advisory_service


@pytest.fixture
def workflow_db():
    """In-memory SQLite session with default users seeded."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()
    seed_default_users(session)
    try:
        yield session
    finally:
        session.close()


@pytest.mark.asyncio
async def test_fallback_triggered_on_repeated_verifier_failure(workflow_db):
    """When LLM repeatedly produces wrong severity, fallback safe template must be used."""
    # Configure mock client to always output wrong severity
    client = MockLLMClient(failure_mode=MockFailureMode.WRONG_SEVERITY)

    forecast_in = ForecastCreate(
        region_name="Nagpur Vidarbha",
        region_type=RegionType.PLAINS,
        date="2026-05-24",
        forecast_tmax_c=47.5,
        normal_tmax_c=41.0,
        confidence=0.92,
    )
    req = AdvisoryGenerateRequest(
        forecast_data=forecast_in,
        stakeholder=StakeholderType.CITIZEN,
        language=LanguageCode.EN,
    )

    record = await advisory_service.generate_advisory(
        db=workflow_db,
        request=req,
        client=client,
        max_retries=2,
    )

    # Must be marked as fallback
    assert record.is_fallback is True
    assert record.verification_passed is False
    assert record.regeneration_count == 2
    assert record.status == "PENDING_REVIEW"
    assert "Pre-Approved" in record.headline


def test_approval_state_machine_transitions(workflow_db):
    """Test state machine: PENDING_REVIEW -> APPROVED -> DISSEMINATED, or -> REJECTED."""
    # 1. Manually create an advisory in PENDING_REVIEW
    from app.db.models import AdvisoryRecord

    rec = AdvisoryRecord(
        stakeholder="farmer",
        language="en",
        severity="HEATWAVE",
        region_name="West Rajasthan",
        date="2026-05-20",
        tmax_c=45.5,
        headline="Heatwave Advisory",
        body="Heat advisory body text.",
        actions_json='["Irrigate early morning"]',
        uncertainty_statement="High confidence 90%.",
        status="PENDING_REVIEW",
    )
    workflow_db.add(rec)
    workflow_db.commit()
    workflow_db.refresh(rec)

    # Cannot disseminate before approval
    with pytest.raises(ValueError, match="Cannot disseminate"):
        advisory_service.disseminate_advisory(
            db=workflow_db,
            advisory_id=rec.id,
            actor_username="meteorologist@imd.gov.in",
            actor_role="meteorologist",
        )

    # Approve
    approved = advisory_service.approve_advisory(
        db=workflow_db,
        advisory_id=rec.id,
        actor_username="meteorologist@imd.gov.in",
        actor_role="meteorologist",
        comments="Clinically and meteorologically sound.",
    )
    assert approved.status == "APPROVED"
    assert approved.reviewed_by == "meteorologist@imd.gov.in"

    # Disseminate
    disseminated_export = advisory_service.disseminate_advisory(
        db=workflow_db,
        advisory_id=rec.id,
        actor_username="meteorologist@imd.gov.in",
        actor_role="meteorologist",
    )
    assert "channel_sms" in disseminated_export
    assert "channel_email" in disseminated_export
    assert approved.status == "DISSEMINATED"


# ============================================================================
# API ENDPOINT RBAC TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_rbac_approval_restrictions(async_client: AsyncClient):
    """Verify viewer role is rejected (403) while meteorologist can approve."""
    # 1. Create tokens
    viewer_token = create_access_token({"sub": "viewer@imd.gov.in", "role": "viewer"})
    meteo_token = create_access_token({"sub": "meteorologist@imd.gov.in", "role": "meteorologist"})

    # 2. Create advisory
    f_res = await async_client.post(
        "/api/v1/forecasts",
        json={
            "region_name": "Shimla Western Hills",
            "region_type": "hilly",
            "date": "2026-05-22",
            "forecast_tmax_c": 32.0,
            "normal_tmax_c": 25.0,
            "confidence": 0.89,
        },
    )
    f_id = f_res.json()["id"]

    adv_res = await async_client.post(
        "/api/v1/advisories/generate",
        json={"forecast_id": f_id, "stakeholder": "citizen", "language": "en"},
    )
    adv_id = adv_res.json()["id"]

    # 3. Viewer attempts approval -> 403 Forbidden
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}
    appr_fail = await async_client.post(
        f"/api/v1/advisories/{adv_id}/approve", headers=viewer_headers
    )
    assert appr_fail.status_code == 403

    # 4. Meteorologist approves -> 200 OK
    meteo_headers = {"Authorization": f"Bearer {meteo_token}"}
    appr_ok = await async_client.post(
        f"/api/v1/advisories/{adv_id}/approve",
        headers=meteo_headers,
        json={"comments": "Checked against radar and model consensus."},
    )
    assert appr_ok.status_code == 200
    assert appr_ok.json()["status"] == "APPROVED"
    assert appr_ok.json()["reviewed_by"] == "meteorologist@imd.gov.in"

    # 5. Meteorologist disseminates -> 200 OK
    diss_ok = await async_client.post(
        f"/api/v1/advisories/{adv_id}/disseminate", headers=meteo_headers
    )
    assert diss_ok.status_code == 200
    assert diss_ok.json()["status"] == "success"
    assert "channel_sms" in diss_ok.json()["dissemination_details"]
