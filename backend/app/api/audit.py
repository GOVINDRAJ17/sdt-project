"""Audit trail and operational metrics API endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import AdvisoryRecord, AuditLogRecord, ForecastRecord
from app.services.audit_service import audit_service

router = APIRouter(tags=["Audit & Metrics"])


@router.get("/audit", response_model=list[dict[str, Any]])
def get_audit_trail(
    action: str | None = Query(None, description="Filter by event action"),
    actor: str | None = Query(None, description="Filter by actor username"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Retrieve append-only audit trail logs with SHA-256 hash chains."""
    records = audit_service.list_logs(
        db=db, action=action, actor_username=actor, skip=skip, limit=limit
    )
    return [
        {
            "id": r.id,
            "timestamp": r.timestamp.isoformat(),
            "actor_username": r.actor_username,
            "actor_role": r.actor_role,
            "action": r.action,
            "resource_type": r.resource_type,
            "resource_id": r.resource_id,
            "details": r.details_json,
            "prev_hash": r.prev_hash,
            "current_hash": r.current_hash,
        }
        for r in records
    ]


@router.get("/audit/verify")
def verify_audit_chain_integrity(db: Session = Depends(get_db)):
    """
    Cryptographic verification endpoint:
    Iterates through the entire SHA-256 hash chain and confirms no records were modified or deleted.
    """
    return audit_service.verify_chain_integrity(db=db)


@router.get("/metrics")
def get_operational_metrics(db: Session = Depends(get_db)):
    """Retrieve operational and responsible AI reliability metrics."""
    total_forecasts = db.query(ForecastRecord).count()
    total_advisories = db.query(AdvisoryRecord).count()

    pending_review = (
        db.query(AdvisoryRecord).filter(AdvisoryRecord.status == "PENDING_REVIEW").count()
    )
    approved = db.query(AdvisoryRecord).filter(AdvisoryRecord.status == "APPROVED").count()
    rejected = db.query(AdvisoryRecord).filter(AdvisoryRecord.status == "REJECTED").count()
    disseminated = db.query(AdvisoryRecord).filter(AdvisoryRecord.status == "DISSEMINATED").count()

    verified_pass = (
        db.query(AdvisoryRecord).filter(AdvisoryRecord.verification_passed.is_(True)).count()
    )
    fallback_used = db.query(AdvisoryRecord).filter(AdvisoryRecord.is_fallback.is_(True)).count()

    total_audit_events = db.query(AuditLogRecord).count()
    guard_blocks = db.query(AuditLogRecord).filter(AuditLogRecord.action == "GUARD_CHECK").count()

    chain_status = audit_service.verify_chain_integrity(db=db)

    return {
        "forecasts": {
            "total_forecasts": total_forecasts,
        },
        "advisories": {
            "total_generated": total_advisories,
            "pending_review": pending_review,
            "approved": approved,
            "rejected": rejected,
            "disseminated": disseminated,
            "verification_passed_first_try": verified_pass,
            "fallback_templates_triggered": fallback_used,
            "human_approval_rate": round(
                (approved + disseminated) / max(1, total_advisories) * 100, 1
            ),
        },
        "security_and_governance": {
            "total_audit_records": total_audit_events,
            "guard_evaluations": guard_blocks,
            "tamper_evident_chain_integrity": chain_status["valid"],
            "latest_block_hash": chain_status.get("latest_block_hash"),
        },
    }
