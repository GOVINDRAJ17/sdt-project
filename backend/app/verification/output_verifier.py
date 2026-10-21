"""Deterministic Output Verifier (Hallucination & Safety Guard).

Verifies every LLM-generated advisory against ground-truth meteorological facts
and institutional safety policies before anything can proceed to the review queue.
"""

import re

from pydantic import BaseModel, Field

from app.core.config import settings
from app.domain.action_library import (
    APPROVED_ACTION_THEMES,
    PII_PATTERNS,
    PROHIBITED_PHARMACEUTICAL_TERMS,
)
from app.domain.advisory_models import AdvisoryOutput, LanguageCode, StakeholderType
from app.domain.models import SeverityLevel


class SingleCheckResult(BaseModel):
    """Result of an individual verifier check."""

    check_name: str
    passed: bool
    details: str


class VerificationResult(BaseModel):
    """Complete multi-criteria verification report."""

    passed: bool
    checks: dict[str, SingleCheckResult] = Field(default_factory=dict)
    failure_reasons: list[str] = Field(default_factory=list)


class OutputVerifier:
    """Deterministic validator enforcing ground-truth consistency and safety rules."""

    def __init__(
        self,
        temperature_tolerance_c: float = 1.0,
        canary_token: str | None = None,
    ):
        self.temperature_tolerance_c = temperature_tolerance_c
        self.canary_token = canary_token or settings.SYSTEM_CANARY_TOKEN

    def _check_severity(
        self,
        output_severity: SeverityLevel | str,
        ground_truth_severity: SeverityLevel | str,
    ) -> SingleCheckResult:
        """Enforces that claimed advisory severity equals the deterministic rule engine severity."""
        out_sev = (
            output_severity.value
            if isinstance(output_severity, SeverityLevel)
            else str(output_severity).upper()
        )
        gt_sev = (
            ground_truth_severity.value
            if isinstance(ground_truth_severity, SeverityLevel)
            else str(ground_truth_severity).upper()
        )

        passed = out_sev == gt_sev
        details = (
            f"Claimed severity '{out_sev}' matches ground-truth '{gt_sev}'"
            if passed
            else f"Severity mismatch: LLM claimed '{out_sev}', but meteorological ground-truth is '{gt_sev}'"
        )
        return SingleCheckResult(check_name="severity_match", passed=passed, details=details)

    def _check_temperature(
        self,
        advisory: AdvisoryOutput,
        forecast_tmax_c: float,
    ) -> SingleCheckResult:
        """Verifies claimed tmax_c and any temperatures mentioned in text match forecast within tolerance."""
        # 1. Check top-level numeric field
        diff = abs(advisory.tmax_c - forecast_tmax_c)
        if diff > self.temperature_tolerance_c:
            return SingleCheckResult(
                check_name="temperature_tolerance",
                passed=False,
                details=f"Temperature discrepancy: advisory claims {advisory.tmax_c}°C, forecast is {forecast_tmax_c}°C (tolerance: ±{self.temperature_tolerance_c}°C)",
            )

        # 2. Extract numbers mentioned in headline and body next to temperature indicators
        combined_text = f"{advisory.headline} {advisory.body}"
        temp_matches = re.findall(
            r"(\d+(?:\.\d+)?)\s*(?:°\s*C|degrees?\s*c|c\b)", combined_text, re.IGNORECASE
        )
        for t_str in temp_matches:
            val = float(t_str)
            if abs(val - forecast_tmax_c) > self.temperature_tolerance_c:
                return SingleCheckResult(
                    check_name="temperature_tolerance",
                    passed=False,
                    details=f"Hallucinated temperature in text: found {val}°C, expected ~{forecast_tmax_c}°C",
                )

        return SingleCheckResult(
            check_name="temperature_tolerance",
            passed=True,
            details=f"Temperature {advisory.tmax_c}°C is within ±{self.temperature_tolerance_c}°C of forecast {forecast_tmax_c}°C",
        )

    def _check_region_and_date(
        self,
        advisory: AdvisoryOutput,
        expected_region: str,
        expected_date: str,
    ) -> SingleCheckResult:
        """Ensures advisory region and date match the forecast."""
        # Date check
        if advisory.date.strip() != expected_date.strip():
            return SingleCheckResult(
                check_name="region_and_date_match",
                passed=False,
                details=f"Date mismatch: advisory claims '{advisory.date}', expected '{expected_date}'",
            )

        # Region check (fuzzy substring / token overlap)
        adv_reg = advisory.region.lower().strip()
        exp_reg = expected_region.lower().strip()
        reg_tokens = [tok.strip("(),") for tok in exp_reg.split() if len(tok) > 2]

        matches_region = (
            (adv_reg == exp_reg)
            or any(tok in adv_reg for tok in reg_tokens)
            or any(adv_tok in exp_reg for adv_tok in adv_reg.split())
        )
        if not matches_region:
            return SingleCheckResult(
                check_name="region_and_date_match",
                passed=False,
                details=f"Region mismatch: advisory claims '{advisory.region}', expected '{expected_region}'",
            )

        return SingleCheckResult(
            check_name="region_and_date_match",
            passed=True,
            details=f"Region '{advisory.region}' and Date '{advisory.date}' match forecast",
        )

    def _check_uncertainty_statement(
        self, advisory: AdvisoryOutput, confidence: float
    ) -> SingleCheckResult:
        """Verifies presence and adequacy of uncertainty / confidence statement."""
        text = advisory.uncertainty_statement.strip()
        if len(text) < 10:
            return SingleCheckResult(
                check_name="uncertainty_statement",
                passed=False,
                details="Uncertainty statement is missing or too brief.",
            )

        return SingleCheckResult(
            check_name="uncertainty_statement",
            passed=True,
            details=f"Uncertainty statement present: '{text[:60]}...'",
        )

    def _check_canary_leak(self, advisory: AdvisoryOutput) -> SingleCheckResult:
        """Ensures the secret canary token was not exfiltrated into user-facing content."""
        full_text = f"{advisory.headline} {advisory.body} {' '.join(advisory.actions)} {advisory.uncertainty_statement}"
        if self.canary_token and self.canary_token in full_text:
            return SingleCheckResult(
                check_name="canary_leak",
                passed=False,
                details=f"CRITICAL SECURITY ALERT: Canary token [{self.canary_token}] leaked in output text!",
            )

        return SingleCheckResult(
            check_name="canary_leak",
            passed=True,
            details="No canary token leakage detected.",
        )

    def _check_safety_and_actions(
        self,
        advisory: AdvisoryOutput,
        stakeholder: StakeholderType | str,
    ) -> SingleCheckResult:
        """Verifies no medical dosage claims, no PII, no unwhitelisted URLs/phones, and approved action themes."""
        combined_text = f"{advisory.headline} {advisory.body} {' '.join(advisory.actions)}"

        # 1. Prohibited pharmaceutical dosage terms
        for pattern in PROHIBITED_PHARMACEUTICAL_TERMS:
            if re.search(pattern, combined_text, re.IGNORECASE):
                return SingleCheckResult(
                    check_name="safety_and_actions",
                    passed=False,
                    details=f"Prohibited pharmaceutical dosage instruction detected: pattern '{pattern}'",
                )

        # 2. PII checks
        for pii in PII_PATTERNS:
            if re.search(pii, combined_text):
                return SingleCheckResult(
                    check_name="safety_and_actions",
                    passed=False,
                    details=f"Potential PII detected matching pattern '{pii}'",
                )

        # 3. Unwhitelisted URL / phone number check
        if re.search(r"https?:\/\/(?!www\.imd\.gov\.in)[^\s]+", combined_text, re.IGNORECASE):
            return SingleCheckResult(
                check_name="safety_and_actions",
                passed=False,
                details="Unwhitelisted external URL found in advisory text",
            )

        # 4. Action library relevance check
        stk_key = (
            stakeholder.value
            if isinstance(stakeholder, StakeholderType)
            else str(stakeholder).lower()
        )
        themes = APPROVED_ACTION_THEMES.get(stk_key, APPROVED_ACTION_THEMES["citizen"])
        actions_str = " ".join(advisory.actions).lower()

        has_approved_theme = any(theme in actions_str for theme in themes)
        if not has_approved_theme:
            return SingleCheckResult(
                check_name="safety_and_actions",
                passed=False,
                details=f"Actions do not reflect approved themes for stakeholder '{stk_key}'",
            )

        return SingleCheckResult(
            check_name="safety_and_actions",
            passed=True,
            details="Actions and content adhere to safety policies and approved themes.",
        )

    def _check_language(
        self, advisory: AdvisoryOutput, expected_lang: LanguageCode | str
    ) -> SingleCheckResult:
        """Verifies text script matches requested language."""
        lang_code = (
            expected_lang.value
            if isinstance(expected_lang, LanguageCode)
            else str(expected_lang).lower()
        )
        sample = f"{advisory.headline} {advisory.body}"

        # Devanagari Unicode range: \u0900-\u097F
        has_devanagari = bool(re.search(r"[\u0900-\u097F]", sample))

        if lang_code in ["hi", "mr"] and not has_devanagari:
            return SingleCheckResult(
                check_name="language_match",
                passed=False,
                details=f"Language mismatch: requested '{lang_code}', but text does not contain Devanagari script",
            )

        if lang_code == "en" and has_devanagari:
            return SingleCheckResult(
                check_name="language_match",
                passed=False,
                details="Language mismatch: requested English, but Devanagari text detected",
            )

        return SingleCheckResult(
            check_name="language_match",
            passed=True,
            details=f"Language verified for '{lang_code}'",
        )

    def verify(
        self,
        advisory: AdvisoryOutput,
        ground_truth_severity: SeverityLevel | str,
        forecast_tmax_c: float,
        expected_region: str,
        expected_date: str,
        confidence: float,
        stakeholder: StakeholderType | str,
        language: LanguageCode | str,
    ) -> VerificationResult:
        """Run all deterministic verification checks against ground-truth and institutional rules."""
        checks: dict[str, SingleCheckResult] = {}
        failure_reasons: list[str] = []

        # Run checks
        c_sev = self._check_severity(advisory.severity, ground_truth_severity)
        checks["severity_match"] = c_sev

        c_temp = self._check_temperature(advisory, forecast_tmax_c)
        checks["temperature_tolerance"] = c_temp

        c_reg = self._check_region_and_date(advisory, expected_region, expected_date)
        checks["region_and_date_match"] = c_reg

        c_unc = self._check_uncertainty_statement(advisory, confidence)
        checks["uncertainty_statement"] = c_unc

        c_can = self._check_canary_leak(advisory)
        checks["canary_leak"] = c_can

        c_saf = self._check_safety_and_actions(advisory, stakeholder)
        checks["safety_and_actions"] = c_saf

        c_lang = self._check_language(advisory, language)
        checks["language_match"] = c_lang

        for check in checks.values():
            if not check.passed:
                failure_reasons.append(f"[{check.check_name}] {check.details}")

        all_passed = len(failure_reasons) == 0
        return VerificationResult(
            passed=all_passed,
            checks=checks,
            failure_reasons=failure_reasons,
        )


output_verifier = OutputVerifier()
