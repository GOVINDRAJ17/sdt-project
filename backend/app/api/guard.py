"""API endpoint for testing and auditing the input security guard."""

from fastapi import APIRouter

from app.security.guard_models import GuardCheckRequest, GuardResult
from app.security.input_guard import input_guard

router = APIRouter(prefix="/guard", tags=["Security Guard"])


@router.post("/check", response_model=GuardResult)
def check_text_security(request: GuardCheckRequest):
    """
    Evaluate arbitrary untrusted text through the multi-layer Input Guard.
    Inspects Unicode, homoglyphs, delimiter breakouts, base64 payloads, and injection patterns.
    """
    return input_guard.check(request.text)
