"""Integration tests for Forecast API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_get_forecast(async_client: AsyncClient):
    """Test creating a forecast via POST /api/v1/forecasts and fetching it via GET."""
    payload = {
        "region_name": "API Test Plains",
        "region_type": "plains",
        "date": "2026-05-25",
        "forecast_tmax_c": 46.5,
        "normal_tmax_c": 41.0,
        "confidence": 0.91,
        "lead_time_days": 1,
        "source": "api-test",
    }
    post_res = await async_client.post("/api/v1/forecasts", json=payload)
    assert post_res.status_code == 201
    data = post_res.json()

    assert data["id"] is not None
    assert data["departure_c"] == 5.5
    assert data["severity"] == "HEATWAVE"

    forecast_id = data["id"]
    get_res = await async_client.get(f"/api/v1/forecasts/{forecast_id}")
    assert get_res.status_code == 200
    assert get_res.json()["region_name"] == "API Test Plains"


@pytest.mark.asyncio
async def test_stateless_evaluate_endpoint(async_client: AsyncClient):
    """Test POST /api/v1/forecasts/evaluate runs rule engine without database mutation."""
    res = await async_client.post(
        "/api/v1/forecasts/evaluate",
        params={
            "region_type": "coastal",
            "forecast_tmax_c": 37.5,
            "normal_tmax_c": 32.0,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["severity"] == "SEVERE_HEATWAVE"
    assert data["is_absolute_triggered"] is True
    assert "disclaimer" in data


@pytest.mark.asyncio
async def test_seed_api_endpoint(async_client: AsyncClient):
    """Test triggering database seed via POST /api/v1/forecasts/seed."""
    seed_res = await async_client.post("/api/v1/forecasts/seed", params={"force": True})
    assert seed_res.status_code == 200
    seed_data = seed_res.json()
    assert seed_data["status"] == "success"
    assert seed_data["record_count"] == 28

    list_res = await async_client.get("/api/v1/forecasts?limit=50")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 28
