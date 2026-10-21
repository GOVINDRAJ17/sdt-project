"""OpenAI provider adapter implementing LLMClient."""

import time
from typing import Any

from app.llm.client import LLMClient, LLMMessage, LLMResponse


class OpenAIClient(LLMClient):
    """Adapter for OpenAI Chat Completions API."""

    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini"):
        super().__init__(model_name=model_name)
        if not api_key:
            raise ValueError("OpenAI API key must be provided.")
        self.api_key = api_key
        try:
            from openai import AsyncOpenAI

            self.client = AsyncOpenAI(api_key=api_key)
        except ImportError as e:
            raise ImportError(
                "openai package is required to use OpenAIClient. Run `pip install openai`."
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
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response_format = {"type": "json_object"} if json_mode else None

        start_time = time.perf_counter()
        resp = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
            **kwargs,
        )
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        content = resp.choices[0].message.content or ""
        tokens = resp.usage.total_tokens if resp.usage else 0

        return LLMResponse(
            content=content,
            model=self.model_name,
            provider="openai",
            tokens_used=tokens,
            latency_ms=round(latency_ms, 2),
            raw=resp.model_dump(),
            finish_reason=resp.choices[0].finish_reason,
        )

    async def generate_messages(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int = 1500,
        json_mode: bool = True,
        **kwargs: Any,
    ) -> LLMResponse:
        formatted = [{"role": m.role, "content": m.content} for m in messages]
        response_format = {"type": "json_object"} if json_mode else None

        start_time = time.perf_counter()
        resp = await self.client.chat.completions.create(
            model=self.model_name,
            messages=formatted,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
            **kwargs,
        )
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        content = resp.choices[0].message.content or ""
        tokens = resp.usage.total_tokens if resp.usage else 0

        return LLMResponse(
            content=content,
            model=self.model_name,
            provider="openai",
            tokens_used=tokens,
            latency_ms=round(latency_ms, 2),
            raw=resp.model_dump(),
            finish_reason=resp.choices[0].finish_reason,
        )
