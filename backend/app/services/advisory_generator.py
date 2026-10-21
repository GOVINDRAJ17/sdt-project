"""Advisory generation service with deterministic verification, auto-regeneration, and fallback."""

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import AdvisoryRecord, ForecastRecord
from app.domain.action_library import FALLBACK_TEMPLATES
from app.domain.advisory_models import (
    AdvisoryGenerateRequest,
    AdvisoryOutput,
)
from app.domain.models import SeverityLevel
from app.llm import LLMClient, get_llm_client
from app.prompts.templates import build_system_prompt, build_user_prompt
from app.security.guard_models import GuardDecision
from app.security.input_guard import input_guard
from app.services.audit_service import audit_service
from app.services.forecast_service import forecast_service
from app.verification.output_verifier import VerificationResult, output_verifier


def clean_json_markdown(text: str) -> str:
    """Strips markdown code fence wrappers from raw LLM responses."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


class AdvisoryGenerationService:
    """Orchestrates secure prompt construction, verified LLM generation, and review lifecycle."""

    @staticmethod
    async def generate_advisory(
        db: Session,
        request: AdvisoryGenerateRequest,
        client: LLMClient | None = None,
        max_retries: int = 2,
        actor_username: str = "system",
        actor_role: str = "system",
    ) -> AdvisoryRecord:
        """
        Generates an advisory through a verified pipeline:
        1. Guard: Screen untrusted operator notes.
        2. Prompt: Assemble structured forecast & system prompt.
        3. Generate & Verify: Deterministically check LLM output against ground truth.
        4. Regenerate on failure up to max_retries.
        5. Fallback: If still failing, inject safe pre-approved template with audit flags.
        """
        # 1. Resolve forecast data
        forecast: ForecastRecord | None = None
        if request.forecast_id:
            forecast = forecast_service.get_forecast(db=db, forecast_id=request.forecast_id)
            if not forecast:
                raise ValueError(f"Forecast record with ID {request.forecast_id} not found.")
        elif request.forecast_data:
            forecast = forecast_service.create_forecast(db=db, forecast_in=request.forecast_data)
        else:
            raise ValueError("Either 'forecast_id' or 'forecast_data' must be provided.")

        # 2. Defense Layer: Inspect untrusted operator notes
        sanitized_operator_notes = ""
        if request.operator_notes and request.operator_notes.strip():
            guard_res = input_guard.check(request.operator_notes)
            audit_service.log_event(
                db=db,
                actor_username=actor_username,
                actor_role=actor_role,
                action="GUARD_CHECK",
                resource_type="operator_notes",
                resource_id=forecast.id,
                details=guard_res.model_dump(),
            )
            if guard_res.decision == GuardDecision.BLOCK:
                reasons = (
                    ", ".join(guard_res.detected_patterns) or "Malicious prompt injection detected"
                )
                raise ValueError(
                    f"Security Alert: Operator notes blocked by Input Guard [{reasons}]"
                )
            sanitized_operator_notes = guard_res.sanitized_text

        # 3. Build prompts
        system_prompt = build_system_prompt()
        user_prompt = build_user_prompt(
            region_name=forecast.region_name,
            region_type=forecast.region_type,
            date=forecast.date,
            forecast_tmax_c=forecast.forecast_tmax_c,
            normal_tmax_c=forecast.normal_tmax_c,
            departure_c=forecast.departure_c,
            severity=forecast.severity,
            confidence=forecast.confidence,
            lead_time_days=forecast.lead_time_days,
            stakeholder=request.stakeholder,
            language=request.language,
            operator_notes=sanitized_operator_notes,
        )

        active_client = client or get_llm_client()
        advisory_output: AdvisoryOutput | None = None
        verification_result: VerificationResult | None = None
        last_raw_response = ""
        regeneration_attempts = 0

        # 4. Generate & Verify Loop (Up to 1 + max_retries attempts)
        for attempt in range(max_retries + 1):
            if attempt > 0:
                regeneration_attempts += 1
                audit_service.log_event(
                    db=db,
                    actor_username=actor_username,
                    actor_role=actor_role,
                    action="REGENERATION_ATTEMPT",
                    resource_type="advisory",
                    resource_id=forecast.id,
                    details={
                        "attempt": attempt,
                        "previous_failures": verification_result.failure_reasons
                        if verification_result
                        else [],
                    },
                )

            llm_resp = await active_client.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                json_mode=True,
            )
            last_raw_response = llm_resp.content

            # Parse JSON
            try:
                cleaned_json = clean_json_markdown(llm_resp.content)
                parsed_data = json.loads(cleaned_json)
                candidate_output = AdvisoryOutput(**parsed_data)
            except Exception as parse_err:
                candidate_output = None
                verification_result = VerificationResult(
                    passed=False,
                    checks={},
                    failure_reasons=[f"JSON Schema Parsing Failure: {str(parse_err)}"],
                )
                continue

            # Deterministic Verification against ground truth
            v_res = output_verifier.verify(
                advisory=candidate_output,
                ground_truth_severity=forecast.severity,
                forecast_tmax_c=forecast.forecast_tmax_c,
                expected_region=forecast.region_name,
                expected_date=forecast.date,
                confidence=forecast.confidence,
                stakeholder=request.stakeholder,
                language=request.language,
            )

            if v_res.passed:
                advisory_output = candidate_output
                verification_result = v_res
                break
            else:
                verification_result = v_res

        # 5. Check if Fallback Template is Required
        is_fallback = False
        if not advisory_output or (verification_result and not verification_result.passed):
            is_fallback = True
            stk_key = request.stakeholder.value
            lang_key = request.language.value
            tmpl = FALLBACK_TEMPLATES.get(
                (stk_key, lang_key),
                FALLBACK_TEMPLATES.get((stk_key, "en"), FALLBACK_TEMPLATES[("citizen", "en")]),
            )

            advisory_output = AdvisoryOutput(
                severity=SeverityLevel(forecast.severity),
                region=forecast.region_name,
                date=forecast.date,
                tmax_c=forecast.forecast_tmax_c,
                headline=tmpl["headline"].format(
                    region=forecast.region_name, date=forecast.date, tmax_c=forecast.forecast_tmax_c
                ),
                body=tmpl["body"].format(
                    region=forecast.region_name, date=forecast.date, tmax_c=forecast.forecast_tmax_c
                ),
                actions=tmpl["actions"],
                uncertainty_statement=tmpl["uncertainty_statement"],
            )

            audit_service.log_event(
                db=db,
                actor_username=actor_username,
                actor_role=actor_role,
                action="FALLBACK_TRIGGERED",
                resource_type="advisory",
                resource_id=forecast.id,
                details={
                    "reason": "Verifier rejected all LLM candidate generations",
                    "verification_failures": verification_result.failure_reasons
                    if verification_result
                    else [],
                },
            )

        # 6. Persist Advisory Record in Database
        v_passed = (
            verification_result.passed if verification_result else False
        ) and not is_fallback
        v_details_json = json.dumps(
            verification_result.model_dump() if verification_result else {}, ensure_ascii=False
        )

        record = AdvisoryRecord(
            forecast_id=forecast.id,
            stakeholder=request.stakeholder.value,
            language=request.language.value,
            severity=advisory_output.severity.value,
            region_name=advisory_output.region,
            date=advisory_output.date,
            tmax_c=advisory_output.tmax_c,
            headline=advisory_output.headline,
            body=advisory_output.body,
            actions_json=json.dumps(advisory_output.actions, ensure_ascii=False),
            uncertainty_statement=advisory_output.uncertainty_statement,
            operator_notes=request.operator_notes,
            raw_llm_response=last_raw_response,
            verification_passed=v_passed,
            verification_details=v_details_json,
            is_fallback=is_fallback,
            regeneration_count=regeneration_attempts,
            status="PENDING_REVIEW",  # Automatically enters Human-in-the-Loop review queue
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        audit_service.log_event(
            db=db,
            actor_username=actor_username,
            actor_role=actor_role,
            action="ADVISORY_GENERATED",
            resource_type="advisory",
            resource_id=record.id,
            details={
                "verification_passed": v_passed,
                "is_fallback": is_fallback,
                "regeneration_count": regeneration_attempts,
                "severity": record.severity,
            },
        )
        return record

    @staticmethod
    def get_advisory(db: Session, advisory_id: int) -> AdvisoryRecord | None:
        """Fetch single advisory by ID."""
        return db.query(AdvisoryRecord).filter(AdvisoryRecord.id == advisory_id).first()

    @staticmethod
    def list_advisories(
        db: Session,
        stakeholder: str | None = None,
        language: str | None = None,
        severity: str | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AdvisoryRecord]:
        """List stored advisories with optional filters."""
        query = db.query(AdvisoryRecord)
        if stakeholder:
            query = query.filter(AdvisoryRecord.stakeholder == stakeholder.lower())
        if language:
            query = query.filter(AdvisoryRecord.language == language.lower())
        if severity:
            query = query.filter(AdvisoryRecord.severity == severity.upper())
        if status:
            query = query.filter(AdvisoryRecord.status == status.upper())
        return (
            query.order_by(AdvisoryRecord.created_at.desc(), AdvisoryRecord.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    # =========================================================================
    # APPROVAL STATE MACHINE TRANSITIONS
    # DRAFT -> PENDING_REVIEW -> APPROVED | REJECTED -> DISSEMINATED
    # =========================================================================

    @staticmethod
    def approve_advisory(
        db: Session,
        advisory_id: int,
        actor_username: str,
        actor_role: str,
        comments: str | None = None,
    ) -> AdvisoryRecord:
        """Approve an advisory. Restricted to meteorologist or admin."""
        record = db.query(AdvisoryRecord).filter(AdvisoryRecord.id == advisory_id).first()
        if not record:
            raise ValueError(f"Advisory {advisory_id} not found.")

        if record.status in ["APPROVED", "DISSEMINATED"]:
            return record

        record.status = "APPROVED"
        record.reviewed_by = actor_username
        record.reviewed_at = datetime.now(UTC)
        record.review_comments = comments or "Approved after meteorological verification."
        db.commit()
        db.refresh(record)

        audit_service.log_event(
            db=db,
            actor_username=actor_username,
            actor_role=actor_role,
            action="ADVISORY_APPROVED",
            resource_type="advisory",
            resource_id=record.id,
            details={"comments": record.review_comments},
        )
        return record

    @staticmethod
    def reject_advisory(
        db: Session,
        advisory_id: int,
        actor_username: str,
        actor_role: str,
        reason: str,
    ) -> AdvisoryRecord:
        """Reject an advisory with reason. Restricted to meteorologist or admin."""
        record = db.query(AdvisoryRecord).filter(AdvisoryRecord.id == advisory_id).first()
        if not record:
            raise ValueError(f"Advisory {advisory_id} not found.")

        record.status = "REJECTED"
        record.reviewed_by = actor_username
        record.reviewed_at = datetime.now(UTC)
        record.review_comments = reason
        db.commit()
        db.refresh(record)

        audit_service.log_event(
            db=db,
            actor_username=actor_username,
            actor_role=actor_role,
            action="ADVISORY_REJECTED",
            resource_type="advisory",
            resource_id=record.id,
            details={"rejection_reason": reason},
        )
        return record

    @staticmethod
    def disseminate_advisory(
        db: Session,
        advisory_id: int,
        actor_username: str,
        actor_role: str,
    ) -> dict[str, Any]:
        """
        Stub dissemination export: generates SMS, email, and API push payloads.
        Transitions status from APPROVED to DISSEMINATED.
        """
        record = db.query(AdvisoryRecord).filter(AdvisoryRecord.id == advisory_id).first()
        if not record:
            raise ValueError(f"Advisory {advisory_id} not found.")

        if record.status != "APPROVED":
            raise ValueError(
                f"Cannot disseminate advisory in status '{record.status}'. Must be 'APPROVED'."
            )

        try:
            actions_list = json.loads(record.actions_json)
        except Exception:
            actions_list = [record.actions_json]

        # Generate multi-channel exportable payloads
        sms_text = f"IMD ALERT [{record.severity}]: {record.headline}. Max Temp: {record.tmax_c}C on {record.date}. Actions: {actions_list[0]}."[
            :160
        ]
        email_html = (
            f"<h2>{record.headline}</h2>"
            f"<p><strong>Severity:</strong> {record.severity} | <strong>Region:</strong> {record.region_name}</p>"
            f"<p>{record.body}</p>"
            f"<ul>" + "".join(f"<li>{a}</li>" for a in actions_list) + "</ul>"
            f"<p><em>{record.uncertainty_statement}</em></p>"
        )

        payload_export = {
            "advisory_id": record.id,
            "channel_sms": sms_text,
            "channel_email": email_html,
            "disseminated_at": datetime.now(UTC).isoformat(),
            "authorized_by": record.reviewed_by or actor_username,
        }

        record.status = "DISSEMINATED"
        record.disseminated_at = datetime.now(UTC)
        record.dissemination_payload = json.dumps(payload_export, ensure_ascii=False)
        db.commit()
        db.refresh(record)

        audit_service.log_event(
            db=db,
            actor_username=actor_username,
            actor_role=actor_role,
            action="ADVISORY_DISSEMINATED",
            resource_type="advisory",
            resource_id=record.id,
            details={"channels": ["sms", "email", "api_push"], "authorized_by": record.reviewed_by},
        )

        return payload_export


advisory_service = AdvisoryGenerationService()
