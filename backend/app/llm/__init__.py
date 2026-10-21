"""LLM client interface, mock client, and factory."""

from app.core.config import settings
from app.llm.client import LLMClient, LLMMessage, LLMResponse
from app.llm.mock import MockFailureMode, MockLLMClient


def get_llm_client(provider: str | None = None) -> LLMClient:
    """Factory to retrieve configured LLM client instance (mock, openai, anthropic)."""
    selected = (provider or settings.LLM_PROVIDER).lower()

    if selected == "openai":
        from app.llm.openai_client import OpenAIClient

        return OpenAIClient(
            api_key=settings.OPENAI_API_KEY,
            model_name=settings.OPENAI_MODEL,
        )

    if selected == "anthropic":
        from app.llm.anthropic_client import AnthropicClient

        return AnthropicClient(
            api_key=settings.ANTHROPIC_API_KEY,
            model_name=settings.ANTHROPIC_MODEL,
        )

    # Default to deterministic mock client
    return MockLLMClient(
        failure_mode=MockFailureMode(settings.MOCK_LLM_FAILURE_MODE),
        canary_token=settings.SYSTEM_CANARY_TOKEN,
        simulated_latency_ms=settings.MOCK_LLM_LATENCY_MS,
    )


__all__ = [
    "LLMClient",
    "LLMMessage",
    "LLMResponse",
    "MockLLMClient",
    "MockFailureMode",
    "get_llm_client",
]
