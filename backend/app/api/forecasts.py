"""API endpoints for weather forecasts and IMD rule evaluations."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.seed import seed_forecasts
from app.domain.models import (
    ForecastCreate,
    ForecastResponse,
    ForecastRuleResult,
    RegionType,
    SeverityLevel,
)
from app.domain.rule_engine import evaluate_heatwave_severity
from app.services.forecast_service import forecast_service

router = APIRouter(prefix="/forecasts", tags=["Forecasts"])


@router.post("", response_model=ForecastResponse, status_code=status.HTTP_201_CREATED)
def create_forecast(forecast_in: ForecastCreate, db: Session = Depends(get_db)):
    """Create a new forecast record; departure and severity are computed deterministically."""
    record = forecast_service.create_forecast(db=db, forecast_in=forecast_in)
    return record


@router.get("", response_model=list[ForecastResponse])
def list_forecasts(
    region_type: RegionType | None = Query(None, description="Filter by region type"),
    severity: SeverityLevel | None = Query(None, description="Filter by severity level"),
    region_name: str | None = Query(None, description="Search by region name substring"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Retrieve list of stored forecasts with optional filtering."""
    return forecast_service.list_forecasts(
        db=db,
        region_type=region_type.value if region_type else None,
        severity=severity.value if severity else None,
        region_name=region_name,
        skip=skip,
        limit=limit,
    )


@router.get("/{forecast_id}", response_model=ForecastResponse)
def get_forecast(forecast_id: int, db: Session = Depends(get_db)):
    """Retrieve single forecast by ID."""
    record = forecast_service.get_forecast(db=db, forecast_id=forecast_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Forecast with ID {forecast_id} not found",
        )
    return record


@router.post("/evaluate", response_model=ForecastRuleResult)
def evaluate_forecast_parameters(
    region_type: RegionType,
    forecast_tmax_c: float,
    normal_tmax_c: float,
):
    """Stateless evaluation of heatwave severity via deterministic IMD rule engine."""
    return evaluate_heatwave_severity(
        region_type=region_type,
        forecast_tmax_c=forecast_tmax_c,
        normal_tmax_c=normal_tmax_c,
    )


@router.post("/seed", status_code=status.HTTP_200_OK)
def trigger_seed(force: bool = False, db: Session = Depends(get_db)):
    """Populate database with synthetic forecasts for 7 IMD regions across 4 seasons."""
    count = seed_forecasts(db=db, force=force)
    return {
        "status": "success",
        "message": f"Forecast database seeded with {count} records.",
        "record_count": count,
    }
