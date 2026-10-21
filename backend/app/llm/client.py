"""Provider-agnostic LLM client interface and response models."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class LLMMessage(BaseModel):
    """Chat message structure."""

    role: str  # "system", "user", "assistant"
    content: str


class LLMResponse(BaseModel):
    """Standardized response from any LLM provider."""

    content: str
    model: str
    provider: str
    tokens_used: int = 0
    latency_ms: float = 0.0
    raw: dict[str, Any] | None = None
    finish_reason: str | None = "stop"


class LLMClient(ABC):
    """Abstract base class for all LLM providers (Mock, OpenAI, Anthropic)."""

    def __init__(self, model_name: str = "default"):
        self.model_name = model_name

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 1500,
        json_mode: bool = True,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a completion for the given prompt."""
        pass

    @abstractmethod
    async def generate_messages(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int = 1500,
        json_mode: bool = True,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a completion for multi-turn messages."""
        pass
