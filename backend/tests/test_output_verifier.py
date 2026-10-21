"""Exhaustive unit tests for OutputVerifier hallucination and safety checks."""

import pytest

from app.domain.advisory_models import AdvisoryOutput, LanguageCode, StakeholderType
from app.domain.models import SeverityLevel
from app.verification.output_verifier import output_verifier


@pytest.fixture
def valid_advisory() -> AdvisoryOutput:
    """Fixture providing a faithful, valid advisory."""
    return AdvisoryOutput(
        severity=SeverityLevel.HEATWAVE,
        region="Vidarbha Plains",
        date="2026-05-20",
        tmax_c=46.2,
        headline="Heatwave Advisory for Vidarbha Plains on 2026-05-20",
        body="Maximum temperatures are anticipated to reach 46.2°C. Vulnerable populations should exercise extreme caution.",
        actions=[
            "Drink plenty of water and oral rehydration solutions (ORS) even if not thirsty",
            "Avoid direct sun exposure between 12:00 PM and 3:00 PM",
            "Wear lightweight, light-colored cotton clothing",
        ],
        uncertainty_statement="High forecast confidence (88%) based on multi-ensemble IMD guidance.",
    )


def test_valid_advisory_passes_all_checks(valid_advisory):
    """Ensure fully faithful advisory passes all verifier checks."""
    res = output_verifier.verify(
        advisory=valid_advisory,
        ground_truth_severity=SeverityLevel.HEATWAVE,
        forecast_tmax_c=46.2,
        expected_region="Vidarbha Plains",
        expected_date="2026-05-20",
        confidence=0.88,
        stakeholder=StakeholderType.CITIZEN,
        language=LanguageCode.EN,
    )
    assert res.passed is True
    assert len(res.failure_reasons) == 0
    assert res.checks["severity_match"].passed is True
    assert res.checks["temperature_tolerance"].passed is True
    assert res.checks["region_and_date_match"].passed is True
    assert res.checks["uncertainty_statement"].passed is True
    assert res.checks["canary_leak"].passed is True
    assert res.checks["safety_and_actions"].passed is True
    assert res.checks["language_match"].passed is True


def test_severity_mismatch_fails(valid_advisory):
    """Ground truth is SEVERE_HEATWAVE, but advisory claims HEATWAVE -> FAIL."""
    res = output_verifier.verify(
        advisory=valid_advisory,
        ground_truth_severity=SeverityLevel.SEVERE_HEATWAVE,
        forecast_tmax_c=46.2,
        expected_region="Vidarbha Plains",
        expected_date="2026-05-20",
        confidence=0.88,
        stakeholder=StakeholderType.CITIZEN,
        language=LanguageCode.EN,
    )
    assert res.passed is False
    assert res.checks["severity_match"].passed is False
    assert any("severity_match" in r for r in res.failure_reasons)


def test_temperature_deviation_fails(valid_advisory):
    """Advisory claims 46.2°C, but forecast is 44.0°C (diff > 1.0°C) -> FAIL."""
    res = output_verifier.verify(
        advisory=valid_advisory,
        ground_truth_severity=SeverityLevel.HEATWAVE,
        forecast_tmax_c=44.0,  # 2.2°C deviation
        expected_region="Vidarbha Plains",
        expected_date="2026-05-20",
        confidence=0.88,
        stakeholder=StakeholderType.CITIZEN,
        language=LanguageCode.EN,
    )
    assert res.passed is False
    assert res.checks["temperature_tolerance"].passed is False


def test_hallucinated_temperature_in_text_fails(valid_advisory):
    """Advisory has 46.2°C in field, but body mentions wild 54.0°C -> FAIL."""
    valid_advisory.body = "Dangerous extreme heat reaching 54°C in the afternoon."
    res = output_verifier.verify(
        advisory=valid_advisory,
        ground_truth_severity=SeverityLevel.HEATWAVE,
        forecast_tmax_c=46.2,
        expected_region="Vidarbha Plains",
        expected_date="2026-05-20",
        confidence=0.88,
        stakeholder=StakeholderType.CITIZEN,
        language=LanguageCode.EN,
    )
    assert res.passed is False
    assert res.checks["temperature_tolerance"].passed is False


def test_region_mismatch_fails(valid_advisory):
    """Expected 'Kolkata Coastal', advisory says 'Vidarbha Plains' -> FAIL."""
    res = output_verifier.verify(
        advisory=valid_advisory,
        ground_truth_severity=SeverityLevel.HEATWAVE,
        forecast_tmax_c=46.2,
        expected_region="Kolkata Coastal",
        expected_date="2026-05-20",
        confidence=0.88,
        stakeholder=StakeholderType.CITIZEN,
        language=LanguageCode.EN,
    )
    assert res.passed is False
    assert res.checks["region_and_date_match"].passed is False


def test_date_mismatch_fails(valid_advisory):
    """Expected '2026-05-21', advisory has '2026-05-20' -> FAIL."""
    res = output_verifier.verify(
        advisory=valid_advisory,
        ground_truth_severity=SeverityLevel.HEATWAVE,
        forecast_tmax_c=46.2,
        expected_region="Vidarbha Plains",
        expected_date="2026-05-21",
        confidence=0.88,
        stakeholder=StakeholderType.CITIZEN,
        language=LanguageCode.EN,
    )
    assert res.passed is False
    assert res.checks["region_and_date_match"].passed is False


def test_canary_leak_fails(valid_advisory):
    """Canary token leaked in headline -> CRITICAL FAIL."""
    canary = "CANARY-IMD-SEC-9981"
    valid_advisory.headline = f"Heatwave Advisory [{canary}]"
    res = output_verifier.verify(
        advisory=valid_advisory,
        ground_truth_severity=SeverityLevel.HEATWAVE,
        forecast_tmax_c=46.2,
        expected_region="Vidarbha Plains",
        expected_date="2026-05-20",
        confidence=0.88,
        stakeholder=StakeholderType.CITIZEN,
        language=LanguageCode.EN,
    )
    assert res.passed is False
    assert res.checks["canary_leak"].passed is False


def test_pharmaceutical_dosage_fails(valid_advisory):
    """Actions contain medication dosage instruction -> FAIL."""
    valid_advisory.actions.append("Take 500mg Paracetamol tablets every 4 hours preemptively")
    res = output_verifier.verify(
        advisory=valid_advisory,
        ground_truth_severity=SeverityLevel.HEATWAVE,
        forecast_tmax_c=46.2,
        expected_region="Vidarbha Plains",
        expected_date="2026-05-20",
        confidence=0.88,
        stakeholder=StakeholderType.CITIZEN,
        language=LanguageCode.EN,
    )
    assert res.passed is False
    assert res.checks["safety_and_actions"].passed is False


def test_unwhitelisted_url_fails(valid_advisory):
    """Actions contain suspicious external link -> FAIL."""
    valid_advisory.actions.append("Check live tips at http://malicious-weather-blog.info")
    res = output_verifier.verify(
        advisory=valid_advisory,
        ground_truth_severity=SeverityLevel.HEATWAVE,
        forecast_tmax_c=46.2,
        expected_region="Vidarbha Plains",
        expected_date="2026-05-20",
        confidence=0.88,
        stakeholder=StakeholderType.CITIZEN,
        language=LanguageCode.EN,
    )
    assert res.passed is False
    assert res.checks["safety_and_actions"].passed is False


def test_pii_email_fails(valid_advisory):
    """Body contains personal email -> FAIL."""
    valid_advisory.body += " Contact operator at meteorologist.john@gmail.com for details."
    res = output_verifier.verify(
        advisory=valid_advisory,
        ground_truth_severity=SeverityLevel.HEATWAVE,
        forecast_tmax_c=46.2,
        expected_region="Vidarbha Plains",
        expected_date="2026-05-20",
        confidence=0.88,
        stakeholder=StakeholderType.CITIZEN,
        language=LanguageCode.EN,
    )
    assert res.passed is False
    assert res.checks["safety_and_actions"].passed is False


def test_language_mismatch_fails(valid_advisory):
    """Requested Hindi ('hi'), but output text is pure English Latin script -> FAIL."""
    res = output_verifier.verify(
        advisory=valid_advisory,
        ground_truth_severity=SeverityLevel.HEATWAVE,
        forecast_tmax_c=46.2,
        expected_region="Vidarbha Plains",
        expected_date="2026-05-20",
        confidence=0.88,
        stakeholder=StakeholderType.CITIZEN,
        language=LanguageCode.HI,  # Expected Devanagari Hindi
    )
    assert res.passed is False
    assert res.checks["language_match"].passed is False
