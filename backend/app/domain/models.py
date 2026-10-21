"""Domain models and schemas for weather forecasts and IMD rule evaluations."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class RegionType(StrEnum):
    """Supported geographical region types with distinct meteorological thresholds."""

    PLAINS = "plains"
    HILLY = "hilly"
    COASTAL = "coastal"


class SeverityLevel(StrEnum):
    """IMD heatwave advisory alert severity levels."""

    NONE = "NONE"
    HEATWAVE = "HEATWAVE"
    SEVERE_HEATWAVE = "SEVERE_HEATWAVE"


class ForecastBase(BaseModel):
    """Base schema for heatwave forecast data."""

    region_name: str = Field(..., description="Name of the forecast region/city")
    region_type: RegionType = Field(
        ..., description="Climatic classification: plains, hilly, coastal"
    )
    date: str = Field(..., description="Target forecast date (YYYY-MM-DD)")
    forecast_tmax_c: float = Field(..., description="Forecast maximum temperature in Celsius")
    normal_tmax_c: float = Field(
        ..., description="Climatological normal maximum temperature in Celsius"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Model forecast confidence score between 0 and 1"
    )
    lead_time_days: int = Field(default=1, ge=0, description="Forecast lead time in days")
    source: str = Field(
        default="synthetic", description="Data source (e.g. IMD LRF, AWS, synthetic)"
    )

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError as err:
            raise ValueError("date must be in YYYY-MM-DD format") from err


class ForecastCreate(ForecastBase):
    """Schema for creating a new forecast record."""

    pass


class ForecastResponse(ForecastBase):
    """Schema for returning a stored forecast record with computed fields."""

    id: int
    departure_c: float = Field(
        ..., description="Departure from normal maximum temperature (computed)"
    )
    severity: SeverityLevel = Field(
        ..., description="Evaluated severity according to IMD rule engine"
    )
    created_at: datetime

    class Config:
        from_attributes = True


class ForecastRuleResult(BaseModel):
    """Detailed evaluation result returned by the deterministic IMD rule engine."""

    severity: SeverityLevel
    forecast_tmax_c: float
    normal_tmax_c: float
    departure_c: float
    region_type: RegionType
    criteria_triggered: list[str] = Field(default_factory=list)
    is_departure_triggered: bool = False
    is_absolute_triggered: bool = False
    disclaimer: str = "Evaluated via deterministic IMD criteria. Operational systems must confirm thresholds with IMD."
