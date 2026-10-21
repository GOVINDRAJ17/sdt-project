"""Configuration loader and schema for IMD heatwave criteria thresholds."""

import json
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field


class RegionThreshold(BaseModel):
    """Threshold settings for a specific climatic region."""

    name: str
    normal_tmax_range: list[float] = Field(default_factory=lambda: [30.0, 40.0])
    heatwave_min_departure: float = 4.5
    severe_min_departure: float = 6.4
    heatwave_min_tmax: float = 45.0
    severe_min_tmax: float = 47.0
    departure_heatwave_inclusive: bool = True  # True: D >= 4.5, False: D > 4.5
    departure_severe_strict: bool = True  # True: D > 6.4, False: D >= 6.4
    tmax_inclusive: bool = True  # True: Tmax >= limit, False: Tmax > limit


DEFAULT_THRESHOLDS: dict[str, RegionThreshold] = {
    "plains": RegionThreshold(
        name="Plains",
        normal_tmax_range=[30.0, 40.0],
        heatwave_min_departure=4.5,
        severe_min_departure=6.4,
        heatwave_min_tmax=45.0,
        severe_min_tmax=47.0,
        departure_heatwave_inclusive=True,
        departure_severe_strict=True,
        tmax_inclusive=True,
    ),
    "hilly": RegionThreshold(
        name="Hilly regions",
        normal_tmax_range=[20.0, 30.0],
        heatwave_min_departure=4.5,
        severe_min_departure=6.4,
        heatwave_min_tmax=30.0,
        severe_min_tmax=35.0,
        departure_heatwave_inclusive=True,
        departure_severe_strict=True,
        tmax_inclusive=True,
    ),
    "coastal": RegionThreshold(
        name="Coastal regions",
        normal_tmax_range=[25.0, 35.0],
        heatwave_min_departure=4.5,
        severe_min_departure=6.4,
        heatwave_min_tmax=35.0,
        severe_min_tmax=37.0,
        departure_heatwave_inclusive=True,
        departure_severe_strict=True,
        tmax_inclusive=True,
    ),
}


@lru_cache
def load_imd_thresholds(custom_path: Path | None = None) -> dict[str, RegionThreshold]:
    """
    Load IMD thresholds from JSON file or fall back to standard defaults.
    NOTE: Real-world operational deployments must calibrate and confirm thresholds with IMD.
    """
    path = custom_path or (Path(__file__).parent / "imd_thresholds.json")
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                return {k: RegionThreshold(**v) for k, v in data.get("regions", {}).items()}
        except Exception:
            pass
    return DEFAULT_THRESHOLDS.copy()
