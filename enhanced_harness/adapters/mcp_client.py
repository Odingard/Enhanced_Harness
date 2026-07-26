"""MCP client adapter via official Python mcp SDK (stdio + streamable HTTP)."""

from __future__ import annotations

import logging
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from enhanced_harness.safety import SafetyError, assert_mcp_target_allowed, tool_allowed
from enhanced_harness.scope import MCPTarget, Scope

log = logging.getLogger("harness.adapters.mcp")


class MCPClientAdapter:
    """Real MCP client. Supports stdio transport for Milestone 1."""

    def __init__(self, target: MCPTarget, scope: Scope) -> None:
        self.target = target
        self.scope = scope
        self._stack: AsyncExitStack | None = None
        self._session: ClientSession | None = None
        self.tools: list[dict[str, Any]] = []
        self.resources: list[dict[str, Any]] = []
        self.prompts: list[dict[str, Any]] = []

    async def connect(self) -> None:
        assert_mcp_target_allowed(self.target, self.scope)
        if self.target.transport != "stdio":
            raise SafetyError(
                f"Milestone 1 MCP adapter supports stdio; got {self.target.transport}"
            )
        if not self.target.command:
            raise SafetyError(f"MCP target {self.target.name} missing command")

        params = StdioServerParameters(
            command=self.target.command[0],
            args=list(self.target.command[1:]),
            cwd=self.target.cwd,
            env=self.target.env or None,
        )
        self._stack = AsyncExitStack()
        read, write = await self._stack.enter_async_context(stdio_client(params))
        self._session = await self._stack.enter_async_context(ClientSession(read, write))
        await self._session.initialize()
        await self.refresh()

    async def refresh(self) -> None:
        assert self._session is not None
        tools_result = await self._session.list_tools()
        self.tools = [
            {
                "name": t.name,
                "description": t.description or "",
                "inputSchema": getattr(t, "inputSchema", {}) or {},
            }
            for t in tools_result.tools
        ]
        try:
            res = await self._session.list_resources()
            self.resources = [
                {"uri": str(r.uri), "name": getattr(r, "name", ""), "description": getattr(r, "description", "")}
                for r in res.resources
            ]
        except Exception as e:  # noqa: BLE001 — optional surface
            log.debug("list_resources unavailable: %s", e)
            self.resources = []
        try:
            prompts = await self._session.list_prompts()
            self.prompts = [
                {"name": p.name, "description": getattr(p, "description", "")}
                for p in prompts.prompts
            ]
        except Exception as e:  # noqa: BLE001
            log.debug("list_prompts unavailable: %s", e)
            self.prompts = []

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        assert self._session is not None
        if not tool_allowed(name, self.scope.allowlist):
            raise SafetyError(f"Tool not allowlisted: {name}")
        result = await self._session.call_tool(name, arguments or {})
        texts: list[str] = []
        for block in result.content:
            text = getattr(block, "text", None)
            if text is not None:
                texts.append(text)
            else:
                texts.append(str(block))
        return {
            "tool": name,
            "arguments": arguments or {},
            "text": "\n".join(texts),
            "isError": bool(getattr(result, "isError", False)),
            "raw_content": [str(b) for b in result.content],
        }

    async def read_resource(self, uri: str) -> dict[str, Any]:
        assert self._session is not None
        result = await self._session.read_resource(uri)
        texts: list[str] = []
        for c in result.contents:
            text = getattr(c, "text", None)
            if text is not None:
                texts.append(text)
            else:
                texts.append(str(c))
        return {"uri": uri, "text": "\n".join(texts)}

    async def close(self) -> None:
        if self._stack is not None:
            await self._stack.aclose()
            self._stack = None
            self._session = None
