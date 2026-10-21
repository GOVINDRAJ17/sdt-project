"""Domain models and schemas for stakeholder advisories and human review workflows."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.domain.models import ForecastCreate, SeverityLevel


class StakeholderType(StrEnum):
    """Target stakeholder groups with tailored protective action recommendations."""

    CITIZEN = "citizen"
    FARMER = "farmer"
    HEALTH_AGENCY = "health_agency"
    DISASTER_AUTHORITY = "disaster_authority"


class LanguageCode(StrEnum):
    """Supported regional advisory languages."""

    EN = "en"  # English
    HI = "hi"  # Hindi
    MR = "mr"  # Marathi


class AdvisoryOutput(BaseModel):
    """Strict JSON schema required from LLM advisory generation."""

    severity: SeverityLevel = Field(
        ..., description="Alert severity level: NONE, HEATWAVE, SEVERE_HEATWAVE"
    )
    region: str = Field(..., description="Region or meteorological division name")
    date: str = Field(..., description="Target forecast date (YYYY-MM-DD)")
    tmax_c: float = Field(..., description="Forecast maximum temperature in Celsius")
    headline: str = Field(..., description="Concise, impactful advisory headline")
    body: str = Field(..., description="Detailed contextual advisory paragraph")
    actions: list[str] = Field(
        ..., min_length=1, description="List of specific protective action instructions"
    )
    uncertainty_statement: str = Field(
        ..., description="Clear communication of forecast confidence/uncertainty"
    )


class AdvisoryGenerateRequest(BaseModel):
    """Payload to trigger advisory generation for a specific stakeholder and language."""

    forecast_id: int | None = Field(None, description="Existing forecast ID in database")
    forecast_data: ForecastCreate | None = Field(
        None, description="Inline forecast data if not using forecast_id"
    )
    stakeholder: StakeholderType = Field(
        default=StakeholderType.CITIZEN, description="Target stakeholder group"
    )
    language: LanguageCode = Field(default=LanguageCode.EN, description="Target output language")
    operator_notes: str | None = Field(
        default="",
        max_length=500,
        description="Optional free-text notes from the duty meteorologist (treated as untrusted input)",
    )


class AdvisoryReviewRequest(BaseModel):
    """Review approval payload."""

    comments: str | None = Field(default="Approved after meteorological review", max_length=500)


class AdvisoryRejectRequest(BaseModel):
    """Review rejection payload with mandatory reason."""

    reason: str = Field(
        ..., min_length=3, max_length=500, description="Meteorological justification for rejection"
    )


class AdvisoryResponse(BaseModel):
    """Standard API response for generated advisory including verification & review metadata."""

    id: int
    forecast_id: int | None
    stakeholder: StakeholderType
    language: LanguageCode
    severity: SeverityLevel
    region_name: str
    date: str
    tmax_c: float
    headline: str
    body: str
    actions: list[str]
    uncertainty_statement: str

    # Verification details
    verification_passed: bool
    verification_details: dict[str, Any] | None = None
    is_fallback: bool
    regeneration_count: int

    # Approval state machine & metadata
    status: str
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    review_comments: str | None = None
    disseminated_at: datetime | None = None

    created_at: datetime

    class Config:
        from_attributes = True
