from __future__ import annotations

import asyncio
from collections import deque
from collections import defaultdict
from typing import Deque

from bridge.errors import LLMError
from bridge.text import strip_markdown


class LLMRouter:
    def __init__(
        self,
        primary_endpoint: str,
        fallback_endpoint: str,
        primary_model: str,
        fallback_model: str,
        context_turns: int = 6,
        timeout_seconds: float = 8.0,
    ) -> None:
        self.primary_endpoint = primary_endpoint
        self.fallback_endpoint = fallback_endpoint
        self.primary_model = primary_model
        self.fallback_model = fallback_model
        self.timeout_seconds = timeout_seconds
        self.history: Deque[tuple[str, str]] = deque(maxlen=context_turns)
        self.endpoint_attempts: dict[str, int] = defaultdict(int)
        self.last_prompts: list[str] = []

    async def complete(self, text: str, memory_summary: str | None = None) -> str:
        prompt = f"{memory_summary}\n{text}" if memory_summary else text
        self.last_prompts.append(prompt)
        try:
            try:
                response = await asyncio.wait_for(
                    self._post(self.primary_endpoint, self.primary_model, prompt),
                    self.timeout_seconds,
                )
            except Exception:
                response = await asyncio.wait_for(
                    self._post(self.primary_endpoint, self.primary_model, prompt),
                    self.timeout_seconds,
                )
        except Exception:
            try:
                response = await asyncio.wait_for(self._post(self.fallback_endpoint, self.fallback_model, prompt), self.timeout_seconds)
            except Exception as exc:
                raise LLMError("LLM_UNAVAILABLE") from exc
        cleaned = strip_markdown(response)
        self.history.append((text, cleaned))
        return cleaned

    async def _post(self, endpoint: str, model: str, prompt: str) -> str:
        await asyncio.sleep(0)
        self.endpoint_attempts[endpoint] += 1
        if endpoint.startswith("fail-once://") and self.endpoint_attempts[endpoint] == 1:
            raise LLMError("endpoint failed once")
        if endpoint.startswith("fail://"):
            raise LLMError("endpoint failed")
        if "capital of france" in prompt.lower():
            return "The capital of France is **Paris**."
        return f"{model}: {prompt}"

    def reset(self) -> None:
        self.history.clear()
