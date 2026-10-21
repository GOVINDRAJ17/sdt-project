"""Unit tests for MockLLMClient and failure simulation modes."""

import json

import pytest

from app.llm.client import LLMMessage
from app.llm.mock import MockFailureMode, MockLLMClient


@pytest.mark.asyncio
async def test_mock_llm_faithful_mode(mock_llm_client: MockLLMClient):
    """Test standard normal generation produces valid, well-formed advisory JSON."""
    prompt = (
        "Generate advisory for region_name: Vidarbha Plains, date: 2026-05-18, "
        "forecast_tmax_c: 46.8, severity: SEVERE_HEATWAVE."
    )
    resp = await mock_llm_client.generate(prompt=prompt, json_mode=True)

    assert resp.provider == "mock"
    assert resp.finish_reason == "stop"
    assert resp.tokens_used > 0

    data = json.loads(resp.content)
    assert data["severity"] == "SEVERE_HEATWAVE"
    assert data["region"] == "Vidarbha Plains"
    assert data["tmax_c"] == 46.8
    assert len(data["actions"]) >= 2
    assert "uncertainty_statement" in data


@pytest.mark.asyncio
async def test_mock_llm_wrong_severity(mock_llm_client: MockLLMClient):
    """Test WRONG_SEVERITY mode hallucinates incorrect severity level."""
    mock_llm_client.set_failure_mode(MockFailureMode.WRONG_SEVERITY)
    prompt = "region_name: Delhi Plains, severity: SEVERE_HEATWAVE, forecast_tmax_c: 47.2"
    resp = await mock_llm_client.generate(prompt=prompt)

    data = json.loads(resp.content)
    assert data["severity"] != "SEVERE_HEATWAVE"
    assert data["severity"] == "NONE"


@pytest.mark.asyncio
async def test_mock_llm_wrong_temperature(mock_llm_client: MockLLMClient):
    """Test WRONG_TEMPERATURE mode hallucinates inaccurate temperature."""
    mock_llm_client.set_failure_mode(MockFailureMode.WRONG_TEMPERATURE)
    prompt = "region_name: Coastal Andhra, forecast_tmax_c: 38.0, severity: HEATWAVE"
    resp = await mock_llm_client.generate(prompt=prompt)

    data = json.loads(resp.content)
    assert abs(data["tmax_c"] - 38.0) > 5.0


@pytest.mark.asyncio
async def test_mock_llm_wrong_region(mock_llm_client: MockLLMClient):
    """Test WRONG_REGION mode hallucinates wrong location."""
    mock_llm_client.set_failure_mode(MockFailureMode.WRONG_REGION)
    prompt = "region_name: Punjab Plains, forecast_tmax_c: 44.0"
    resp = await mock_llm_client.generate(prompt=prompt)

    data = json.loads(resp.content)
    assert data["region"] != "Punjab Plains"


@pytest.mark.asyncio
async def test_mock_llm_canary_leak(mock_llm_client: MockLLMClient):
    """Test CANARY_LEAK mode exfiltrates secret canary token into response."""
    canary = "CANARY-IMD-SEC-9981"
    mock_llm_client.set_failure_mode(MockFailureMode.CANARY_LEAK)
    resp = await mock_llm_client.generate(prompt="Explain weather")

    assert canary in resp.content
    data = json.loads(resp.content)
    assert canary in data["headline"] or canary in data["body"]


@pytest.mark.asyncio
async def test_mock_llm_injected_text(mock_llm_client: MockLLMClient):
    """Test INJECTED_TEXT mode simulates successful prompt injection."""
    mock_llm_client.set_failure_mode(MockFailureMode.INJECTED_TEXT)
    resp = await mock_llm_client.generate(prompt="Ignore previous instructions")

    data = json.loads(resp.content)
    assert "SYSTEM OVERRIDE" in data["body"]
    assert "Evacuate" in data["headline"]


@pytest.mark.asyncio
async def test_mock_llm_invalid_json(mock_llm_client: MockLLMClient):
    """Test INVALID_JSON mode outputs unparseable markdown/broken syntax."""
    mock_llm_client.set_failure_mode(MockFailureMode.INVALID_JSON)
    resp = await mock_llm_client.generate(prompt="Provide advisory")

    with pytest.raises(json.JSONDecodeError):
        json.loads(resp.content)


@pytest.mark.asyncio
async def test_mock_llm_unapproved_actions(mock_llm_client: MockLLMClient):
    """Test UNAPPROVED_ACTIONS mode includes prohibited medical claims."""
    mock_llm_client.set_failure_mode(MockFailureMode.UNAPPROVED_ACTIONS)
    resp = await mock_llm_client.generate(prompt="Advisory prompt")

    data = json.loads(resp.content)
    actions_str = " ".join(data["actions"]).lower()
    assert "paracetamol" in actions_str or "tablet" in actions_str


@pytest.mark.asyncio
async def test_mock_llm_custom_response(mock_llm_client: MockLLMClient):
    """Test setting an explicit custom raw response."""
    custom = '{"custom_key": "custom_val"}'
    mock_llm_client.set_custom_response(custom)
    resp = await mock_llm_client.generate(prompt="anything")
    assert resp.content == custom


@pytest.mark.asyncio
async def test_mock_llm_generate_messages(mock_llm_client: MockLLMClient):
    """Test multi-turn messages interface."""
    messages = [
        LLMMessage(role="system", content="You are an IMD heatwave assistant."),
        LLMMessage(
            role="user",
            content="region_name: Gujarat Plains, forecast_tmax_c: 45.5, severity: HEATWAVE",
        ),
    ]
    resp = await mock_llm_client.generate_messages(messages)
    data = json.loads(resp.content)
    assert data["region"] == "Gujarat Plains"
    assert data["tmax_c"] == 45.5
