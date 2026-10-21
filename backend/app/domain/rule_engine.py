"""Deterministic IMD Heatwave Criteria Rule Engine.

Pure, unit-tested rule engine implementing India Meteorological Department (IMD)
heatwave and severe heatwave classification standards across climatic regions:
- Plains
- Hilly regions
- Coastal regions

DISCLAIMER: Threshold values are loaded from configuration. Real-world operational
deployments MUST confirm exact values and regional definitions directly with IMD.
"""

from app.domain.models import ForecastRuleResult, RegionType, SeverityLevel
from app.domain.thresholds_config import RegionThreshold, load_imd_thresholds


def compute_departure(forecast_tmax_c: float, normal_tmax_c: float) -> float:
    """Compute temperature departure from normal maximum, rounded to 2 decimal places."""
    return round(float(forecast_tmax_c) - float(normal_tmax_c), 2)


def evaluate_heatwave_severity(
    region_type: RegionType | str,
    forecast_tmax_c: float,
    normal_tmax_c: float,
    custom_thresholds: dict[str, RegionThreshold] | None = None,
) -> ForecastRuleResult:
    """
    Evaluate heatwave severity according to IMD meteorological criteria.

    Args:
        region_type: Climatic region ('plains', 'hilly', 'coastal')
        forecast_tmax_c: Forecast maximum temperature in Celsius
        normal_tmax_c: Climatological normal maximum temperature in Celsius
        custom_thresholds: Optional threshold override for testing or calibration

    Returns:
        ForecastRuleResult containing severity level, departure, and triggered criteria.
    """
    if isinstance(region_type, str):
        region_type = RegionType(region_type.lower())

    thresholds = custom_thresholds or load_imd_thresholds()
    reg_key = region_type.value
    if reg_key not in thresholds:
        raise ValueError(
            f"Unknown region type: '{reg_key}'. Must be one of {list(thresholds.keys())}"
        )

    cfg = thresholds[reg_key]
    departure_c = compute_departure(forecast_tmax_c, normal_tmax_c)

    criteria_triggered: list[str] = []
    is_departure_triggered = False
    is_absolute_triggered = False

    # 1. Evaluate SEVERE HEATWAVE criteria
    # Departure check for severe heatwave
    severe_dep_met = (
        (departure_c > cfg.severe_min_departure)
        if cfg.departure_severe_strict
        else (departure_c >= cfg.severe_min_departure)
    )
    if severe_dep_met:
        op_str = ">" if cfg.departure_severe_strict else ">="
        criteria_triggered.append(
            f"Departure {departure_c:.2f}°C {op_str} {cfg.severe_min_departure}°C threshold (SEVERE_HEATWAVE)"
        )
        is_departure_triggered = True

    # Absolute Tmax check for severe heatwave
    severe_tmax_met = (
        (forecast_tmax_c >= cfg.severe_min_tmax)
        if cfg.tmax_inclusive
        else (forecast_tmax_c > cfg.severe_min_tmax)
    )
    if severe_tmax_met:
        op_str = ">=" if cfg.tmax_inclusive else ">"
        criteria_triggered.append(
            f"Absolute Tmax {forecast_tmax_c:.2f}°C {op_str} {cfg.severe_min_tmax}°C threshold (SEVERE_HEATWAVE)"
        )
        is_absolute_triggered = True

    if severe_dep_met or severe_tmax_met:
        return ForecastRuleResult(
            severity=SeverityLevel.SEVERE_HEATWAVE,
            forecast_tmax_c=forecast_tmax_c,
            normal_tmax_c=normal_tmax_c,
            departure_c=departure_c,
            region_type=region_type,
            criteria_triggered=criteria_triggered,
            is_departure_triggered=is_departure_triggered,
            is_absolute_triggered=is_absolute_triggered,
        )

    # 2. Evaluate HEATWAVE criteria (if not severe)
    # Departure check for heatwave
    heatwave_dep_met = (
        (departure_c >= cfg.heatwave_min_departure)
        if cfg.departure_heatwave_inclusive
        else (departure_c > cfg.heatwave_min_departure)
    )
    if heatwave_dep_met:
        op_str = ">=" if cfg.departure_heatwave_inclusive else ">"
        criteria_triggered.append(
            f"Departure {departure_c:.2f}°C {op_str} {cfg.heatwave_min_departure}°C threshold (HEATWAVE)"
        )
        is_departure_triggered = True

    # Absolute Tmax check for heatwave
    heatwave_tmax_met = (
        (forecast_tmax_c >= cfg.heatwave_min_tmax)
        if cfg.tmax_inclusive
        else (forecast_tmax_c > cfg.heatwave_min_tmax)
    )
    if heatwave_tmax_met:
        op_str = ">=" if cfg.tmax_inclusive else ">"
        criteria_triggered.append(
            f"Absolute Tmax {forecast_tmax_c:.2f}°C {op_str} {cfg.heatwave_min_tmax}°C threshold (HEATWAVE)"
        )
        is_absolute_triggered = True

    if heatwave_dep_met or heatwave_tmax_met:
        return ForecastRuleResult(
            severity=SeverityLevel.HEATWAVE,
            forecast_tmax_c=forecast_tmax_c,
            normal_tmax_c=normal_tmax_c,
            departure_c=departure_c,
            region_type=region_type,
            criteria_triggered=criteria_triggered,
            is_departure_triggered=is_departure_triggered,
            is_absolute_triggered=is_absolute_triggered,
        )

    # 3. Normal / No Heatwave
    return ForecastRuleResult(
        severity=SeverityLevel.NONE,
        forecast_tmax_c=forecast_tmax_c,
        normal_tmax_c=normal_tmax_c,
        departure_c=departure_c,
        region_type=region_type,
        criteria_triggered=["Normal conditions within seasonal meteorological limits"],
        is_departure_triggered=False,
        is_absolute_triggered=False,
    )
