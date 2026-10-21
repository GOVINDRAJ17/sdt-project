"""API v1 master router."""

from fastapi import APIRouter

from app.api.advisories import router as advisory_router
from app.api.audit import router as audit_router
from app.api.auth import router as auth_router
from app.api.forecasts import router as forecast_router
from app.api.guard import router as guard_router
from app.api.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="", tags=["Health"])
api_router.include_router(auth_router, tags=["Authentication"])
api_router.include_router(forecast_router, tags=["Forecasts"])
api_router.include_router(advisory_router, tags=["Advisories"])
api_router.include_router(guard_router, tags=["Security Guard"])
api_router.include_router(audit_router, tags=["Audit & Metrics"])
