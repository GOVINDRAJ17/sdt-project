"""Unit and integration tests for Advisory Generation and Prompt Templates."""

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
from app.domain.models import ForecastCreate, RegionType, SeverityLevel
from app.llm.mock import MockFailureMode, MockLLMClient
from app.prompts.templates import build_system_prompt, build_user_prompt
from app.services.advisory_generator import advisory_service


@pytest.fixture
def memory_db():
    """In-memory SQLite session fixture for advisory tests."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def test_build_system_prompt_canary_embedded():
    """Verify system prompt contains the secret canary and security boundaries."""
    canary = "TEST-CANARY-SEC-1234"
    sys_prompt = build_system_prompt(canary_token=canary)
    assert canary in sys_prompt
    assert "STRICT JSON ONLY" in sys_prompt
    assert "UNTRUSTED" in sys_prompt


def test_build_user_prompt_encapsulation():
    """Verify user prompt isolates structured forecast and operator notes."""
    prompt = build_user_prompt(
        region_name="Nagpur Vidarbha",
        region_type=RegionType.PLAINS,
        date="2026-05-19",
        forecast_tmax_c=47.2,
        normal_tmax_c=41.0,
        departure_c=6.2,
        severity=SeverityLevel.HEATWAVE,
        confidence=0.92,
        lead_time_days=1,
        stakeholder=StakeholderType.FARMER,
        language=LanguageCode.EN,
        operator_notes="High wind conditions reported locally.",
    )
    assert "=== BEGIN STRUCTURED FORECAST DATA ===" in prompt
    assert "=== BEGIN UNTRUSTED OPERATOR NOTES ===" in prompt
    assert "High wind conditions reported locally." in prompt
    assert "FARMER" in prompt


@pytest.mark.asyncio
async def test_generate_advisory_all_stakeholders(memory_db):
    """Test generating advisories for Citizen, Farmer, Health Agency, and Disaster Authority."""
    client = MockLLMClient(failure_mode=MockFailureMode.NONE)

    forecast_in = ForecastCreate(
        region_name="Delhi NCR",
        region_type=RegionType.PLAINS,
        date="2026-05-20",
        forecast_tmax_c=46.5,
        normal_tmax_c=40.5,
        confidence=0.90,
    )

    for stakeholder in [
        StakeholderType.CITIZEN,
        StakeholderType.FARMER,
        StakeholderType.HEALTH_AGENCY,
        StakeholderType.DISASTER_AUTHORITY,
    ]:
        req = AdvisoryGenerateRequest(
            forecast_data=forecast_in,
            stakeholder=stakeholder,
            language=LanguageCode.EN,
        )
        record = await advisory_service.generate_advisory(db=memory_db, request=req, client=client)

        assert record.id is not None
        assert record.stakeholder == stakeholder.value
        assert record.severity == "HEATWAVE"
        assert record.region_name == "Delhi NCR"
        assert record.tmax_c == 46.5
        assert len(record.actions_json) > 10
        assert record.status in ["DRAFT", "PENDING_REVIEW"]


@pytest.mark.asyncio
async def test_generate_advisory_multilingual(memory_db):
    """Test advisory generation in English, Hindi, and Marathi."""
    client = MockLLMClient(failure_mode=MockFailureMode.NONE)

    forecast_in = ForecastCreate(
        region_name="Pune Konkan",
        region_type=RegionType.COASTAL,
        date="2026-05-22",
        forecast_tmax_c=36.5,
        normal_tmax_c=32.0,
        confidence=0.88,
    )

    # Hindi
    req_hi = AdvisoryGenerateRequest(
        forecast_data=forecast_in,
        stakeholder=StakeholderType.CITIZEN,
        language=LanguageCode.HI,
    )
    rec_hi = await advisory_service.generate_advisory(db=memory_db, request=req_hi, client=client)
    assert rec_hi.language == "hi"
    assert "हीटवेव" in rec_hi.headline or "चेतावनी" in rec_hi.headline or "परामर्श" in rec_hi.headline

    # Marathi
    req_mr = AdvisoryGenerateRequest(
        forecast_data=forecast_in,
        stakeholder=StakeholderType.FARMER,
        language=LanguageCode.MR,
    )
    rec_mr = await advisory_service.generate_advisory(db=memory_db, request=req_mr, client=client)
    assert rec_mr.language == "mr"
    assert "इशारा" in rec_mr.headline or "उष्णते" in rec_mr.headline


@pytest.mark.asyncio
async def test_advisory_generation_invalid_json_fallback(memory_db):
    """Test that malformed JSON from LLM gracefully triggers safe fallback template."""
    client = MockLLMClient(failure_mode=MockFailureMode.INVALID_JSON)
    req = AdvisoryGenerateRequest(
        forecast_data=ForecastCreate(
            region_name="Test Area",
            region_type=RegionType.PLAINS,
            date="2026-05-20",
            forecast_tmax_c=45.5,
            normal_tmax_c=40.0,
            confidence=0.85,
        ),
        stakeholder=StakeholderType.CITIZEN,
        language=LanguageCode.EN,
    )
    record = await advisory_service.generate_advisory(
        db=memory_db, request=req, client=client, max_retries=1
    )
    assert record.is_fallback is True
    assert record.status == "PENDING_REVIEW"
    assert "Pre-Approved" in record.headline


# ============================================================================
# API ENDPOINT INTEGRATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_api_advisory_generate_and_list(async_client: AsyncClient):
    """Test POST /api/v1/advisories/generate and GET /api/v1/advisories."""
    # 1. First seed or create forecast
    forecast_payload = {
        "region_name": "Vidarbha East",
        "region_type": "plains",
        "date": "2026-05-24",
        "forecast_tmax_c": 47.8,
        "normal_tmax_c": 41.0,
        "confidence": 0.94,
    }
    f_res = await async_client.post("/api/v1/forecasts", json=forecast_payload)
    assert f_res.status_code == 201
    f_id = f_res.json()["id"]

    # 2. Generate advisory using forecast_id
    gen_payload = {
        "forecast_id": f_id,
        "stakeholder": "farmer",
        "language": "en",
        "operator_notes": "Dry easterly winds prevailing.",
    }
    adv_res = await async_client.post("/api/v1/advisories/generate", json=gen_payload)
    assert adv_res.status_code == 201
    adv_data = adv_res.json()

    assert adv_data["id"] is not None
    assert adv_data["stakeholder"] == "farmer"
    assert adv_data["language"] == "en"
    assert adv_data["severity"] == "SEVERE_HEATWAVE"
    assert adv_data["tmax_c"] == 47.8
    assert isinstance(adv_data["actions"], list)
    assert len(adv_data["actions"]) >= 2
    assert "uncertainty_statement" in adv_data

    advisory_id = adv_data["id"]

    # 3. Retrieve by ID
    get_res = await async_client.get(f"/api/v1/advisories/{advisory_id}")
    assert get_res.status_code == 200
    assert get_res.json()["headline"] == adv_data["headline"]

    # 4. List with filter
    list_res = await async_client.get("/api/v1/advisories?stakeholder=farmer&language=en")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1
