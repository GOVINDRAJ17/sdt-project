"""API endpoints for generating, reviewing, approving, and disseminating stakeholder advisories."""

import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import AdvisoryRecord
from app.domain.advisory_models import (
    AdvisoryGenerateRequest,
    AdvisoryRejectRequest,
    AdvisoryResponse,
    AdvisoryReviewRequest,
    LanguageCode,
    StakeholderType,
)
from app.domain.models import SeverityLevel
from app.llm import LLMClient, get_llm_client
from app.security.auth import UserProfile, require_role
from app.services.advisory_generator import advisory_service

router = APIRouter(prefix="/advisories", tags=["Advisories"])


def format_advisory_response(record: AdvisoryRecord) -> AdvisoryResponse:
    """Format SQLAlchemy AdvisoryRecord to Pydantic AdvisoryResponse with full verification details."""
    try:
        actions = json.loads(record.actions_json)
    except Exception:
        actions = [record.actions_json]

    v_details = None
    if record.verification_details:
        try:
            v_details = json.loads(record.verification_details)
        except Exception:
            pass

    return AdvisoryResponse(
        id=record.id,
        forecast_id=record.forecast_id,
        stakeholder=StakeholderType(record.stakeholder),
        language=LanguageCode(record.language),
        severity=SeverityLevel(record.severity),
        region_name=record.region_name,
        date=record.date,
        tmax_c=record.tmax_c,
        headline=record.headline,
        body=record.body,
        actions=actions,
        uncertainty_statement=record.uncertainty_statement,
        verification_passed=record.verification_passed,
        verification_details=v_details,
        is_fallback=record.is_fallback,
        regeneration_count=record.regeneration_count,
        status=record.status,
        reviewed_by=record.reviewed_by,
        reviewed_at=record.reviewed_at,
        review_comments=record.review_comments,
        disseminated_at=record.disseminated_at,
        created_at=record.created_at,
    )


@router.post("/generate", response_model=AdvisoryResponse, status_code=status.HTTP_201_CREATED)
async def generate_advisory_endpoint(
    request: AdvisoryGenerateRequest,
    db: Session = Depends(get_db),
    llm_client: LLMClient = Depends(get_llm_client),
):
    """
    Generate a new stakeholder-specific advisory using structured forecast inputs.
    Executes prompt synthesis, calls LLM, deterministically verifies against ground truth,
    retries on failure, and falls back to safe template if needed.
    """
    try:
        record = await advisory_service.generate_advisory(
            db=db,
            request=request,
            client=llm_client,
            max_retries=2,
            actor_username="system_generator",
            actor_role="generator",
        )
        return format_advisory_response(record)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(err),
        ) from err
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Advisory generation failed: {str(err)}",
        ) from err


@router.get("", response_model=list[AdvisoryResponse])
def list_advisories_endpoint(
    stakeholder: StakeholderType | None = Query(None, description="Filter by stakeholder"),
    language: LanguageCode | None = Query(None, description="Filter by language"),
    severity: SeverityLevel | None = Query(None, description="Filter by severity level"),
    status: str | None = Query(
        None,
        description="Filter by status: DRAFT, PENDING_REVIEW, APPROVED, REJECTED, DISSEMINATED",
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Retrieve list of generated advisories with optional filtering."""
    records = advisory_service.list_advisories(
        db=db,
        stakeholder=stakeholder.value if stakeholder else None,
        language=language.value if language else None,
        severity=severity.value if severity else None,
        status=status,
        skip=skip,
        limit=limit,
    )
    return [format_advisory_response(r) for r in records]


@router.get("/{advisory_id}", response_model=AdvisoryResponse)
def get_advisory_endpoint(advisory_id: int, db: Session = Depends(get_db)):
    """Retrieve single advisory by ID with full verification report."""
    record = advisory_service.get_advisory(db=db, advisory_id=advisory_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Advisory with ID {advisory_id} not found",
        )
    return format_advisory_response(record)


@router.post("/{advisory_id}/approve", response_model=AdvisoryResponse)
def approve_advisory_endpoint(
    advisory_id: int,
    review_in: AdvisoryReviewRequest = AdvisoryReviewRequest(),
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_role(["meteorologist", "admin"])),
):
    """
    Approve an advisory. Restricted to meteorologist or admin roles.
    Transitions advisory from PENDING_REVIEW -> APPROVED.
    """
    try:
        record = advisory_service.approve_advisory(
            db=db,
            advisory_id=advisory_id,
            actor_username=current_user.username,
            actor_role=current_user.role,
            comments=review_in.comments,
        )
        return format_advisory_response(record)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


@router.post("/{advisory_id}/reject", response_model=AdvisoryResponse)
def reject_advisory_endpoint(
    advisory_id: int,
    reject_in: AdvisoryRejectRequest,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_role(["meteorologist", "admin"])),
):
    """
    Reject an advisory with justification. Restricted to meteorologist or admin roles.
    Transitions advisory to REJECTED status.
    """
    try:
        record = advisory_service.reject_advisory(
            db=db,
            advisory_id=advisory_id,
            actor_username=current_user.username,
            actor_role=current_user.role,
            reason=reject_in.reason,
        )
        return format_advisory_response(record)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


@router.post("/{advisory_id}/disseminate")
def disseminate_advisory_endpoint(
    advisory_id: int,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_role(["meteorologist", "admin"])),
):
    """
    Disseminate an approved advisory.
    Transitions status to DISSEMINATED and exports SMS and email payloads.
    """
    try:
        payload = advisory_service.disseminate_advisory(
            db=db,
            advisory_id=advisory_id,
            actor_username=current_user.username,
            actor_role=current_user.role,
        )
        return {
            "status": "success",
            "message": "Advisory successfully exported for dissemination.",
            "dissemination_details": payload,
        }
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
