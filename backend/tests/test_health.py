"""API endpoint tests for health and root endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient):
    """Test service root endpoint returns metadata and docs URL."""
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "docs_url" in data
    assert data["docs_url"] == "/api/v1/docs"


@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient):
    """Test health check returns status healthy and timestamp."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["llm_provider"] == "mock"


@pytest.mark.asyncio
async def test_llm_health_endpoint(async_client: AsyncClient):
    """Test LLM health endpoint verifies connectivity to active mock client."""
    response = await async_client.get("/api/v1/health/llm")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "connected"
    assert data["provider"] == "mock"
    assert "sample_output_preview" in data
