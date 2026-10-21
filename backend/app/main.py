"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.db.database import SessionLocal, init_db
from app.security.auth import seed_default_users


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown hooks."""
    init_db()
    with SessionLocal() as session:
        seed_default_users(session)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Secure, Fact-Checked LLM Advisory Generator for Heatwave Early Warning",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)

# CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS if isinstance(settings.ALLOWED_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
async def root():
    """Service status and quick links."""
    return {
        "service": settings.PROJECT_NAME,
        "version": "0.1.0",
        "docs_url": f"{settings.API_V1_PREFIX}/docs",
        "health_url": f"{settings.API_V1_PREFIX}/health",
    }
