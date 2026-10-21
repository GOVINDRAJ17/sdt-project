"""Anthropic provider adapter implementing LLMClient."""

import time
from typing import Any

from app.llm.client import LLMClient, LLMMessage, LLMResponse


class AnthropicClient(LLMClient):
    """Adapter for Anthropic Messages API."""

    def __init__(self, api_key: str, model_name: str = "claude-3-5-sonnet-20241022"):
        super().__init__(model_name=model_name)
        if not api_key:
            raise ValueError("Anthropic API key must be provided.")
        self.api_key = api_key
        try:
            from anthropic import AsyncAnthropic

            self.client = AsyncAnthropic(api_key=api_key)
        except ImportError as e:
            raise ImportError(
                "anthropic package is required to use AnthropicClient. Run `pip install anthropic`."
            ) from e

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 1500,
        json_mode: bool = True,
        **kwargs: Any,
    ) -> LLMResponse:
        system = system_prompt or ""
        if json_mode and "json" not in system.lower() and "json" not in prompt.lower():
            prompt = f"{prompt}\n\nPlease respond strictly with valid JSON."

        messages = [{"role": "user", "content": prompt}]

        start_time = time.perf_counter()
        resp = await self.client.messages.create(
            model=self.model_name,
            system=system if system else None,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        content = ""
        for block in resp.content:
            if getattr(block, "text", None):
                content += block.text

        tokens = (resp.usage.input_tokens + resp.usage.output_tokens) if resp.usage else 0

        return LLMResponse(
            content=content,
            model=self.model_name,
            provider="anthropic",
            tokens_used=tokens,
            latency_ms=round(latency_ms, 2),
            raw=resp.model_dump(),
            finish_reason=resp.stop_reason,
        )

    async def generate_messages(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int = 1500,
        json_mode: bool = True,
        **kwargs: Any,
    ) -> LLMResponse:
        system = next((m.content for m in messages if m.role == "system"), "")
        user_messages = [
            {"role": m.role, "content": m.content} for m in messages if m.role != "system"
        ]

        start_time = time.perf_counter()
        resp = await self.client.messages.create(
            model=self.model_name,
            system=system if system else None,
            messages=user_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        content = ""
        for block in resp.content:
            if getattr(block, "text", None):
                content += block.text

        tokens = (resp.usage.input_tokens + resp.usage.output_tokens) if resp.usage else 0

        return LLMResponse(
            content=content,
            model=self.model_name,
            provider="anthropic",
            tokens_used=tokens,
            latency_ms=round(latency_ms, 2),
            raw=resp.model_dump(),
            finish_reason=resp.stop_reason,
        )
