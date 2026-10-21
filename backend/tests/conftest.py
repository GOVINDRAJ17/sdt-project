"""Pytest fixtures for backend test suite."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.database import SessionLocal, init_db
from app.llm.mock import MockFailureMode, MockLLMClient
from app.main import app
from app.security.auth import seed_default_users


@pytest.fixture(autouse=True)
def setup_database_for_tests():
    """Ensure database schema is created and default users seeded before tests."""
    init_db()
    with SessionLocal() as session:
        seed_default_users(session)
    yield


@pytest.fixture
def mock_llm_client() -> MockLLMClient:
    """Fixture providing a fresh deterministic MockLLMClient in normal mode."""
    return MockLLMClient(
        failure_mode=MockFailureMode.NONE,
        canary_token="CANARY-IMD-SEC-9981",
        simulated_latency_ms=0,
    )


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Async test client bound to FastAPI application."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
