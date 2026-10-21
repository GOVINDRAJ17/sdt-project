"""Tamper-evident audit logging service with SHA-256 hash chaining."""

import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import AuditLogRecord
from app.domain.action_library import PII_PATTERNS

GENESIS_HASH = "0" * 64


def redact_pii(text: str) -> str:
    """Redact sensitive information like emails, phone numbers, and credentials."""
    redacted = text
    for pii in PII_PATTERNS:
        redacted = re.sub(pii, "[REDACTED_PII]", redacted)
    # Redact secret tokens and keys
    redacted = re.sub(
        r'(?:password|secret|token|key)["\']?\s*:\s*["\']?([^,"\n]+)',
        r'token": "[REDACTED_SECRET]',
        redacted,
        flags=re.IGNORECASE,
    )
    return redacted


class AuditService:
    """Service providing append-only, SHA-256 hash-chained tamper-evident audit records."""

    @staticmethod
    def log_event(
        db: Session,
        actor_username: str,
        actor_role: str,
        action: str,
        resource_type: str,
        resource_id: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditLogRecord:
        """Create and append an immutable hash-chained audit record."""
        # Retrieve previous block hash
        last_record = db.query(AuditLogRecord).order_by(AuditLogRecord.id.desc()).first()
        prev_hash = last_record.current_hash if last_record else GENESIS_HASH

        now_utc = datetime.now(UTC)
        timestamp_str = now_utc.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        details_raw = json.dumps(details or {}, ensure_ascii=False, default=str)
        details_redacted = redact_pii(details_raw)

        # Compute SHA-256 block hash over the chained fields
        chain_string = (
            f"{prev_hash}|"
            f"{timestamp_str}|"
            f"{actor_username}|"
            f"{actor_role}|"
            f"{action}|"
            f"{resource_type}|"
            f"{resource_id}|"
            f"{details_redacted}"
        )
        current_hash = hashlib.sha256(chain_string.encode("utf-8")).hexdigest()

        record = AuditLogRecord(
            timestamp=now_utc,
            timestamp_str=timestamp_str,
            actor_username=actor_username,
            actor_role=actor_role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details_json=details_redacted,
            prev_hash=prev_hash,
            current_hash=current_hash,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def verify_chain_integrity(db: Session) -> dict[str, Any]:
        """Verify the cryptographic SHA-256 integrity of the entire audit chain."""
        records = db.query(AuditLogRecord).order_by(AuditLogRecord.id.asc()).all()
        if not records:
            return {"valid": True, "total_records": 0, "message": "Audit chain is empty and valid."}

        expected_prev_hash = GENESIS_HASH

        for idx, rec in enumerate(records):
            # 1. Verify link to previous block
            if rec.prev_hash != expected_prev_hash:
                return {
                    "valid": False,
                    "tampered_record_id": rec.id,
                    "reason": f"Hash chain broken at record ID {rec.id}: expected prev_hash '{expected_prev_hash}', got '{rec.prev_hash}'",
                    "total_records": len(records),
                }

            # 2. Re-calculate hash
            chain_string = (
                f"{rec.prev_hash}|"
                f"{rec.timestamp_str}|"
                f"{rec.actor_username}|"
                f"{rec.actor_role}|"
                f"{rec.action}|"
                f"{rec.resource_type}|"
                f"{rec.resource_id}|"
                f"{rec.details_json}"
            )
            recalculated = hashlib.sha256(chain_string.encode("utf-8")).hexdigest()
            if recalculated != rec.current_hash:
                return {
                    "valid": False,
                    "tampered_record_id": rec.id,
                    "reason": f"Content tampering detected at record ID {rec.id}: stored hash '{rec.current_hash}' != recomputed '{recalculated}'",
                    "total_records": len(records),
                }

            expected_prev_hash = rec.current_hash

        return {
            "valid": True,
            "total_records": len(records),
            "message": f"Cryptographic integrity verified across {len(records)} audit log blocks.",
            "latest_block_hash": expected_prev_hash,
        }

    @staticmethod
    def list_logs(
        db: Session,
        action: str | None = None,
        actor_username: str | None = None,
        resource_type: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AuditLogRecord]:
        """Fetch audit log records with filtering."""
        q = db.query(AuditLogRecord)
        if action:
            q = q.filter(AuditLogRecord.action == action.upper())
        if actor_username:
            q = q.filter(AuditLogRecord.actor_username == actor_username)
        if resource_type:
            q = q.filter(AuditLogRecord.resource_type == resource_type)
        return q.order_by(AuditLogRecord.id.desc()).offset(skip).limit(limit).all()


audit_service = AuditService()
