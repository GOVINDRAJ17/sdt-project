"""Seed script generating realistic synthetic forecasts for 7 IMD-style regions across 4 seasons."""

from sqlalchemy.orm import Session

from app.db.database import SessionLocal, init_db
from app.db.models import ForecastRecord
from app.domain.models import ForecastCreate, RegionType
from app.services.forecast_service import forecast_service

# 7 IMD Representative Regions
IMD_REGIONS = [
    {"name": "North Plains (Delhi NCR)", "type": RegionType.PLAINS},
    {"name": "Vidarbha (Nagpur & Akola)", "type": RegionType.PLAINS},
    {"name": "West Rajasthan (Churu & Bikaner)", "type": RegionType.PLAINS},
    {"name": "Coastal Andhra (Visakhapatnam)", "type": RegionType.COASTAL},
    {"name": "Konkan Coast (Mumbai & Ratnagiri)", "type": RegionType.COASTAL},
    {"name": "Western Himalayas (Shimla & Solan)", "type": RegionType.HILLY},
    {"name": "Eastern Himalayas (Darjeeling & Sikkim)", "type": RegionType.HILLY},
]

# 4 Distinct Climatological Seasons
SEASONAL_SCENARIOS = [
    {
        "season": "Summer / Pre-Monsoon Peak",
        "date": "2026-05-18",
        "lead_time": 1,
        "temps": {
            "North Plains (Delhi NCR)": {
                "forecast": 46.2,
                "normal": 40.5,
                "conf": 0.92,
            },  # Heatwave (D +5.7, Tmax > 45)
            "Vidarbha (Nagpur & Akola)": {
                "forecast": 47.4,
                "normal": 42.0,
                "conf": 0.94,
            },  # Severe (Tmax >= 47.0)
            "West Rajasthan (Churu & Bikaner)": {
                "forecast": 48.1,
                "normal": 42.5,
                "conf": 0.95,
            },  # Severe (Tmax >= 47.0)
            "Coastal Andhra (Visakhapatnam)": {
                "forecast": 38.2,
                "normal": 33.0,
                "conf": 0.88,
            },  # Severe (Tmax >= 37.0)
            "Konkan Coast (Mumbai & Ratnagiri)": {
                "forecast": 35.8,
                "normal": 33.2,
                "conf": 0.85,
            },  # Heatwave (Tmax >= 35.0)
            "Western Himalayas (Shimla & Solan)": {
                "forecast": 31.4,
                "normal": 25.0,
                "conf": 0.89,
            },  # Heatwave (Tmax >= 30.0, D +6.4)
            "Eastern Himalayas (Darjeeling & Sikkim)": {
                "forecast": 27.2,
                "normal": 20.2,
                "conf": 0.82,
            },  # Severe (D > 6.4)
        },
    },
    {
        "season": "Monsoon",
        "date": "2026-07-22",
        "lead_time": 2,
        "temps": {
            "North Plains (Delhi NCR)": {"forecast": 35.0, "normal": 35.5, "conf": 0.86},
            "Vidarbha (Nagpur & Akola)": {"forecast": 32.5, "normal": 32.8, "conf": 0.85},
            "West Rajasthan (Churu & Bikaner)": {"forecast": 38.0, "normal": 38.2, "conf": 0.83},
            "Coastal Andhra (Visakhapatnam)": {"forecast": 32.2, "normal": 32.5, "conf": 0.84},
            "Konkan Coast (Mumbai & Ratnagiri)": {"forecast": 30.1, "normal": 30.4, "conf": 0.88},
            "Western Himalayas (Shimla & Solan)": {"forecast": 21.0, "normal": 21.5, "conf": 0.87},
            "Eastern Himalayas (Darjeeling & Sikkim)": {
                "forecast": 19.5,
                "normal": 19.8,
                "conf": 0.85,
            },
        },
    },
    {
        "season": "Post-Monsoon Transition",
        "date": "2026-10-14",
        "lead_time": 3,
        "temps": {
            "North Plains (Delhi NCR)": {"forecast": 32.4, "normal": 31.8, "conf": 0.84},
            "Vidarbha (Nagpur & Akola)": {"forecast": 33.0, "normal": 32.5, "conf": 0.85},
            "West Rajasthan (Churu & Bikaner)": {"forecast": 34.8, "normal": 34.2, "conf": 0.82},
            "Coastal Andhra (Visakhapatnam)": {"forecast": 31.0, "normal": 31.2, "conf": 0.86},
            "Konkan Coast (Mumbai & Ratnagiri)": {"forecast": 33.0, "normal": 32.8, "conf": 0.84},
            "Western Himalayas (Shimla & Solan)": {"forecast": 18.5, "normal": 18.2, "conf": 0.89},
            "Eastern Himalayas (Darjeeling & Sikkim)": {
                "forecast": 16.8,
                "normal": 16.5,
                "conf": 0.86,
            },
        },
    },
    {
        "season": "Winter",
        "date": "2026-01-16",
        "lead_time": 1,
        "temps": {
            "North Plains (Delhi NCR)": {"forecast": 19.2, "normal": 20.0, "conf": 0.90},
            "Vidarbha (Nagpur & Akola)": {"forecast": 27.5, "normal": 28.0, "conf": 0.91},
            "West Rajasthan (Churu & Bikaner)": {"forecast": 22.0, "normal": 22.5, "conf": 0.89},
            "Coastal Andhra (Visakhapatnam)": {"forecast": 28.2, "normal": 28.5, "conf": 0.88},
            "Konkan Coast (Mumbai & Ratnagiri)": {"forecast": 30.5, "normal": 31.0, "conf": 0.92},
            "Western Himalayas (Shimla & Solan)": {"forecast": 11.2, "normal": 11.8, "conf": 0.87},
            "Eastern Himalayas (Darjeeling & Sikkim)": {
                "forecast": 9.4,
                "normal": 10.0,
                "conf": 0.85,
            },
        },
    },
]


def seed_forecasts(db: Session, force: bool = False) -> int:
    """Populate database with synthetic forecasts for 7 IMD regions across 4 seasons."""
    existing_count = db.query(ForecastRecord).count()
    if existing_count > 0 and not force:
        return existing_count

    if force and existing_count > 0:
        db.query(ForecastRecord).delete()
        db.commit()

    created_records = 0
    for scenario in SEASONAL_SCENARIOS:
        date_str = scenario["date"]
        lead_time = scenario["lead_time"]
        temps_map = scenario["temps"]

        for region in IMD_REGIONS:
            reg_name = region["name"]
            reg_type = region["type"]
            data = temps_map[reg_name]

            forecast_in = ForecastCreate(
                region_name=reg_name,
                region_type=reg_type,
                date=date_str,
                forecast_tmax_c=data["forecast"],
                normal_tmax_c=data["normal"],
                confidence=data["conf"],
                lead_time_days=lead_time,
                source="synthetic-imd-scenarios",
            )
            forecast_service.create_forecast(db=db, forecast_in=forecast_in)
            created_records += 1

    return created_records


if __name__ == "__main__":
    init_db()
    with SessionLocal() as session:
        count = seed_forecasts(session, force=True)
        print(f"Successfully seeded {count} IMD seasonal forecast records.")
