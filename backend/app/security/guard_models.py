"""Input Guard data models and decision classifications."""

from enum import StrEnum

from pydantic import BaseModel, Field


class GuardDecision(StrEnum):
    """Actionable security decision for untrusted text inputs."""

    ALLOW = "ALLOW"  # Safe to process directly (risk_score < 0.3)
    SANITIZE = "SANITIZE"  # Process with sanitized text (0.3 <= risk_score < 0.7)
    BLOCK = "BLOCK"  # Unsafe / attack detected; rejected (risk_score >= 0.7)


class GuardCheckRequest(BaseModel):
    """Payload to test or evaluate untrusted text via the input guard."""

    text: str = Field(..., max_length=2000, description="Untrusted text string to inspect")
    source: str | None = Field(
        default="operator_notes", description="Context source of the input text"
    )


class GuardResult(BaseModel):
    """Comprehensive security evaluation outcome from the multi-layer input guard."""

    decision: GuardDecision
    risk_score: float = Field(
        ..., ge=0.0, le=1.0, description="Computed threat risk score between 0 and 1"
    )
    original_text: str
    sanitized_text: str
    flags: list[str] = Field(
        default_factory=list, description="Specific security warnings or normalization steps"
    )
    detected_patterns: list[str] = Field(
        default_factory=list, description="Identified attack patterns or triggers"
    )
    is_blocked: bool = False
