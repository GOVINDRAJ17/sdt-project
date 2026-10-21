"""Forecast service managing forecast persistence and rule evaluations."""

from sqlalchemy.orm import Session

from app.db.models import ForecastRecord
from app.domain.models import ForecastCreate
from app.domain.rule_engine import evaluate_heatwave_severity


class ForecastService:
    """Service to create, query, and manage weather forecast records."""

    @staticmethod
    def create_forecast(db: Session, forecast_in: ForecastCreate) -> ForecastRecord:
        """Evaluate severity with IMD rule engine and store forecast."""
        rule_result = evaluate_heatwave_severity(
            region_type=forecast_in.region_type,
            forecast_tmax_c=forecast_in.forecast_tmax_c,
            normal_tmax_c=forecast_in.normal_tmax_c,
        )

        record = ForecastRecord(
            region_name=forecast_in.region_name,
            region_type=forecast_in.region_type.value,
            date=forecast_in.date,
            forecast_tmax_c=forecast_in.forecast_tmax_c,
            normal_tmax_c=forecast_in.normal_tmax_c,
            departure_c=rule_result.departure_c,
            severity=rule_result.severity.value,
            confidence=forecast_in.confidence,
            lead_time_days=forecast_in.lead_time_days,
            source=forecast_in.source,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_forecast(db: Session, forecast_id: int) -> ForecastRecord | None:
        """Fetch single forecast by primary key."""
        return db.query(ForecastRecord).filter(ForecastRecord.id == forecast_id).first()

    @staticmethod
    def list_forecasts(
        db: Session,
        region_type: str | None = None,
        severity: str | None = None,
        region_name: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ForecastRecord]:
        """List forecasts with optional filters."""
        query = db.query(ForecastRecord)
        if region_type:
            query = query.filter(ForecastRecord.region_type == region_type.lower())
        if severity:
            query = query.filter(ForecastRecord.severity == severity.upper())
        if region_name:
            query = query.filter(ForecastRecord.region_name.ilike(f"%{region_name}%"))
        return (
            query.order_by(ForecastRecord.date.desc(), ForecastRecord.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def delete_forecast(db: Session, forecast_id: int) -> bool:
        """Delete forecast by ID."""
        record = db.query(ForecastRecord).filter(ForecastRecord.id == forecast_id).first()
        if not record:
            return False
        db.delete(record)
        db.commit()
        return True


forecast_service = ForecastService()
