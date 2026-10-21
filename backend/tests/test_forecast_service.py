"""Unit tests for ForecastService and Synthetic Seeder."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.db.models import ForecastRecord
from app.db.seed import seed_forecasts
from app.domain.models import ForecastCreate, RegionType, SeverityLevel
from app.services.forecast_service import ForecastService


@pytest.fixture
def db_session():
    """In-memory SQLite database session fixture."""
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()


def test_create_forecast_service(db_session):
    """Test creating a forecast record computes departure and severity automatically."""
    forecast_in = ForecastCreate(
        region_name="Nagpur Vidarbha",
        region_type=RegionType.PLAINS,
        date="2026-05-20",
        forecast_tmax_c=47.5,
        normal_tmax_c=41.0,
        confidence=0.92,
        lead_time_days=1,
        source="unit-test",
    )
    record = ForecastService.create_forecast(db=db_session, forecast_in=forecast_in)

    assert record.id is not None
    assert record.departure_c == 6.5
    assert record.severity == SeverityLevel.SEVERE_HEATWAVE.value
    assert record.region_name == "Nagpur Vidarbha"


def test_list_and_filter_forecasts(db_session):
    """Test filtering forecasts by region_type and severity."""
    ForecastService.create_forecast(
        db=db_session,
        forecast_in=ForecastCreate(
            region_name="Coastal Vizag",
            region_type=RegionType.COASTAL,
            date="2026-05-20",
            forecast_tmax_c=36.0,
            normal_tmax_c=32.0,
            confidence=0.88,
        ),
    )
    ForecastService.create_forecast(
        db=db_session,
        forecast_in=ForecastCreate(
            region_name="Shimla Hilltop",
            region_type=RegionType.HILLY,
            date="2026-05-20",
            forecast_tmax_c=22.0,
            normal_tmax_c=21.0,
            confidence=0.90,
        ),
    )

    coastal_list = ForecastService.list_forecasts(db=db_session, region_type="coastal")
    assert len(coastal_list) == 1
    assert coastal_list[0].region_name == "Coastal Vizag"

    hilly_list = ForecastService.list_forecasts(db=db_session, region_type="hilly")
    assert len(hilly_list) == 1
    assert hilly_list[0].region_name == "Shimla Hilltop"


def test_seed_forecasts(db_session):
    """Test synthetic seeder creates all 7 regions across 4 seasons (28 records)."""
    count = seed_forecasts(db=db_session, force=True)
    assert count == 28

    total_in_db = db_session.query(ForecastRecord).count()
    assert total_in_db == 28

    # Check that diverse severities were generated
    severe_count = (
        db_session.query(ForecastRecord)
        .filter(ForecastRecord.severity == "SEVERE_HEATWAVE")
        .count()
    )
    heatwave_count = (
        db_session.query(ForecastRecord).filter(ForecastRecord.severity == "HEATWAVE").count()
    )
    none_count = db_session.query(ForecastRecord).filter(ForecastRecord.severity == "NONE").count()

    assert severe_count > 0
    assert heatwave_count > 0
    assert none_count > 0
