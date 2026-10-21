"""Exhaustive boundary unit tests for IMD Heatwave Criteria Rule Engine."""

import pytest

from app.domain.models import RegionType, SeverityLevel
from app.domain.rule_engine import evaluate_heatwave_severity
from app.domain.thresholds_config import RegionThreshold

# ============================================================================
# PLAINS REGION BOUNDARY TESTS
# IMD Criteria:
# - Heatwave if D is 4.5-6.4°C OR Tmax >= 45.0°C
# - Severe heatwave if D > 6.4°C OR Tmax >= 47.0°C
# ============================================================================


def test_plains_normal_conditions():
    """Tmax and departure well below threshold."""
    res = evaluate_heatwave_severity(RegionType.PLAINS, forecast_tmax_c=38.0, normal_tmax_c=36.0)
    assert res.severity == SeverityLevel.NONE
    assert res.departure_c == 2.0
    assert not res.is_departure_triggered
    assert not res.is_absolute_triggered


def test_plains_departure_below_4_5():
    """Departure at 4.49°C should NOT trigger heatwave."""
    res = evaluate_heatwave_severity(RegionType.PLAINS, forecast_tmax_c=40.49, normal_tmax_c=36.0)
    assert res.severity == SeverityLevel.NONE
    assert res.departure_c == 4.49


def test_plains_departure_exact_4_5_boundary():
    """Boundary test: exactly D = 4.50°C MUST trigger HEATWAVE."""
    res = evaluate_heatwave_severity(RegionType.PLAINS, forecast_tmax_c=40.5, normal_tmax_c=36.0)
    assert res.severity == SeverityLevel.HEATWAVE
    assert res.departure_c == 4.5
    assert res.is_departure_triggered


def test_plains_departure_exact_6_4_boundary():
    """Boundary test: exactly D = 6.40°C is within 4.5-6.4°C range -> HEATWAVE."""
    res = evaluate_heatwave_severity(RegionType.PLAINS, forecast_tmax_c=42.4, normal_tmax_c=36.0)
    assert res.severity == SeverityLevel.HEATWAVE
    assert res.departure_c == 6.4
    assert res.is_departure_triggered


def test_plains_departure_above_6_4_severe():
    """Boundary test: D = 6.41°C (> 6.4°C) MUST trigger SEVERE_HEATWAVE."""
    res = evaluate_heatwave_severity(RegionType.PLAINS, forecast_tmax_c=42.41, normal_tmax_c=36.0)
    assert res.severity == SeverityLevel.SEVERE_HEATWAVE
    assert res.departure_c == 6.41
    assert res.is_departure_triggered


def test_plains_absolute_below_45():
    """Absolute Tmax 44.9°C with low departure should NOT trigger heatwave."""
    res = evaluate_heatwave_severity(RegionType.PLAINS, forecast_tmax_c=44.9, normal_tmax_c=42.0)
    assert res.severity == SeverityLevel.NONE
    assert res.departure_c == 2.9


def test_plains_absolute_exact_45_boundary():
    """Boundary test: exactly Tmax = 45.0°C MUST trigger HEATWAVE regardless of departure."""
    res = evaluate_heatwave_severity(RegionType.PLAINS, forecast_tmax_c=45.0, normal_tmax_c=42.0)
    assert res.severity == SeverityLevel.HEATWAVE
    assert res.is_absolute_triggered


def test_plains_absolute_below_47():
    """Absolute Tmax 46.9°C (normal 43.0, D = 3.9) triggers HEATWAVE, not severe."""
    res = evaluate_heatwave_severity(RegionType.PLAINS, forecast_tmax_c=46.9, normal_tmax_c=43.0)
    assert res.severity == SeverityLevel.HEATWAVE
    assert res.is_absolute_triggered


def test_plains_absolute_exact_47_boundary():
    """Boundary test: exactly Tmax = 47.0°C MUST trigger SEVERE_HEATWAVE."""
    res = evaluate_heatwave_severity(RegionType.PLAINS, forecast_tmax_c=47.0, normal_tmax_c=43.0)
    assert res.severity == SeverityLevel.SEVERE_HEATWAVE
    assert res.is_absolute_triggered


# ============================================================================
# HILLY REGIONS BOUNDARY TESTS
# IMD Criteria:
# - Heatwave if Tmax >= 30.0°C (or D 4.5-6.4°C)
# - Severe if Tmax >= 35.0°C (or D > 6.4°C)
# ============================================================================


def test_hilly_normal_conditions():
    """Normal hilly weather."""
    res = evaluate_heatwave_severity(RegionType.HILLY, forecast_tmax_c=22.0, normal_tmax_c=20.0)
    assert res.severity == SeverityLevel.NONE


def test_hilly_absolute_below_30():
    """Tmax 29.9°C with modest departure should NOT trigger heatwave."""
    res = evaluate_heatwave_severity(RegionType.HILLY, forecast_tmax_c=29.9, normal_tmax_c=27.0)
    assert res.severity == SeverityLevel.NONE


def test_hilly_absolute_exact_30_boundary():
    """Boundary test: exactly Tmax = 30.0°C in hilly region MUST trigger HEATWAVE."""
    res = evaluate_heatwave_severity(RegionType.HILLY, forecast_tmax_c=30.0, normal_tmax_c=27.0)
    assert res.severity == SeverityLevel.HEATWAVE
    assert res.is_absolute_triggered


def test_hilly_absolute_below_35():
    """Tmax 34.9°C in hilly region triggers HEATWAVE."""
    res = evaluate_heatwave_severity(RegionType.HILLY, forecast_tmax_c=34.9, normal_tmax_c=31.0)
    assert res.severity == SeverityLevel.HEATWAVE


def test_hilly_absolute_exact_35_boundary():
    """Boundary test: exactly Tmax = 35.0°C in hilly region MUST trigger SEVERE_HEATWAVE."""
    res = evaluate_heatwave_severity(RegionType.HILLY, forecast_tmax_c=35.0, normal_tmax_c=31.0)
    assert res.severity == SeverityLevel.SEVERE_HEATWAVE
    assert res.is_absolute_triggered


def test_hilly_departure_trigger():
    """Departure > 6.4°C in hilly region triggers SEVERE_HEATWAVE even if Tmax < 30°C."""
    # e.g., Normal 18.0, Forecast 24.5 -> D = 6.5°C
    res = evaluate_heatwave_severity(RegionType.HILLY, forecast_tmax_c=24.5, normal_tmax_c=18.0)
    assert res.severity == SeverityLevel.SEVERE_HEATWAVE
    assert res.departure_c == 6.5
    assert res.is_departure_triggered


# ============================================================================
# COASTAL REGIONS BOUNDARY TESTS
# IMD Criteria:
# - Heatwave if D is 4.5-6.4°C OR Tmax >= 35.0°C
# - Severe if D > 6.4°C OR Tmax >= 37.0°C
# ============================================================================


def test_coastal_normal_conditions():
    """Normal coastal conditions."""
    res = evaluate_heatwave_severity(RegionType.COASTAL, forecast_tmax_c=31.0, normal_tmax_c=30.0)
    assert res.severity == SeverityLevel.NONE


def test_coastal_absolute_below_35():
    """Tmax 34.9°C with low departure is NONE."""
    res = evaluate_heatwave_severity(RegionType.COASTAL, forecast_tmax_c=34.9, normal_tmax_c=32.0)
    assert res.severity == SeverityLevel.NONE


def test_coastal_absolute_exact_35_boundary():
    """Boundary test: exactly Tmax = 35.0°C in coastal region MUST trigger HEATWAVE."""
    res = evaluate_heatwave_severity(RegionType.COASTAL, forecast_tmax_c=35.0, normal_tmax_c=32.0)
    assert res.severity == SeverityLevel.HEATWAVE
    assert res.is_absolute_triggered


def test_coastal_absolute_exact_37_boundary():
    """Boundary test: exactly Tmax = 37.0°C in coastal region MUST trigger SEVERE_HEATWAVE."""
    res = evaluate_heatwave_severity(RegionType.COASTAL, forecast_tmax_c=37.0, normal_tmax_c=32.0)
    assert res.severity == SeverityLevel.SEVERE_HEATWAVE
    assert res.is_absolute_triggered


def test_coastal_departure_boundaries():
    """Test departure boundaries 4.5°C and 6.4°C in coastal region."""
    # D = 4.50°C -> HEATWAVE
    res_hw = evaluate_heatwave_severity(
        RegionType.COASTAL, forecast_tmax_c=33.5, normal_tmax_c=29.0
    )
    assert res_hw.severity == SeverityLevel.HEATWAVE

    # D = 6.40°C -> HEATWAVE
    res_hw_max = evaluate_heatwave_severity(
        RegionType.COASTAL, forecast_tmax_c=34.4, normal_tmax_c=28.0
    )
    assert res_hw_max.severity == SeverityLevel.HEATWAVE

    # D = 6.50°C -> SEVERE_HEATWAVE
    res_sev = evaluate_heatwave_severity(
        RegionType.COASTAL, forecast_tmax_c=34.5, normal_tmax_c=28.0
    )
    assert res_sev.severity == SeverityLevel.SEVERE_HEATWAVE


# ============================================================================
# NEGATIVE DEPARTURES & EDGE CASES
# ============================================================================


def test_negative_departure_colder_than_normal():
    """Negative departure (colder than normal) must never trigger heatwave."""
    res = evaluate_heatwave_severity(RegionType.PLAINS, forecast_tmax_c=28.0, normal_tmax_c=38.0)
    assert res.severity == SeverityLevel.NONE
    assert res.departure_c == -10.0


def test_unknown_region_type_raises():
    """Unknown region type string must raise ValueError."""
    with pytest.raises(ValueError):
        evaluate_heatwave_severity("antarctic", forecast_tmax_c=40.0, normal_tmax_c=30.0)


def test_custom_threshold_override():
    """Verify that thresholds can be calibrated via custom configuration dict."""
    custom = {
        "plains": RegionThreshold(
            name="Calibrated Plains",
            heatwave_min_tmax=44.0,  # lowered from 45.0
            severe_min_tmax=46.0,  # lowered from 47.0
        )
    }
    # 44.2°C would be NONE in standard, but HEATWAVE in calibrated
    res = evaluate_heatwave_severity(
        RegionType.PLAINS,
        forecast_tmax_c=44.2,
        normal_tmax_c=41.0,
        custom_thresholds=custom,
    )
    assert res.severity == SeverityLevel.HEATWAVE
