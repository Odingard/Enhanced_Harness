"""LLM / Agentic app HTTP adapter (chat + tool-calling loops)."""

from __future__ import annotations

from typing import Any

import httpx

from enhanced_harness.safety import assert_url_allowed
from enhanced_harness.scope import LLMTarget, Scope


class LLMAppAdapter:
    """Real HTTP adapter for agentic chat endpoints."""

    def __init__(self, target: LLMTarget, scope: Scope) -> None:
        self.target = target
        self.scope = scope
        self._client: httpx.AsyncClient | None = None

    async def connect(self) -> None:
        assert_url_allowed(self.target.base_url, self.scope)
        self._client = httpx.AsyncClient(
            base_url=self.target.base_url.rstrip("/"),
            headers=self.target.headers,
            timeout=30.0,
        )

    async def health(self) -> dict[str, Any]:
        assert self._client is not None
        r = await self._client.get("/health")
        r.raise_for_status()
        return r.json()

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        assert self._client is not None
        assert_url_allowed(self.target.base_url, self.scope)
        payload: dict[str, Any] = {"messages": messages}
        if tools:
            payload["tools"] = tools
        r = await self._client.post(self.target.chat_path, json=payload)
        r.raise_for_status()
        data = r.json()
        return {
            "content": data.get("content", ""),
            "tool_calls": data.get("tool_calls") or [],
            "raw": data,
        }

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
