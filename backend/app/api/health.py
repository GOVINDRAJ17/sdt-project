"""Health check endpoints."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends

from app.core.config import settings
from app.llm import LLMClient, get_llm_client

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Basic service health check."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "llm_provider": settings.LLM_PROVIDER,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/health/llm")
async def llm_health_check(client: LLMClient = Depends(get_llm_client)):
    """Verifies that the configured LLM client is operational."""
    resp = await client.generate(
        prompt="Respond with a basic status ping for health monitoring in JSON: {'status': 'ok'}",
        system_prompt="You are a system health monitor. Output valid JSON only.",
        json_mode=True,
    )
    return {
        "status": "connected",
        "provider": resp.provider,
        "model": resp.model,
        "latency_ms": resp.latency_ms,
        "sample_output_preview": resp.content[:100],
    }
