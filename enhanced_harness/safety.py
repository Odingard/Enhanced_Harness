"""Allowlist and kill-switch enforcement (fail closed)."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from enhanced_harness.scope import AgentChatUITarget, Allowlist, MCPTarget, Scope


class SafetyError(RuntimeError):
    pass


def kill_switch_active(path: str | Path) -> bool:
    return Path(path).exists()


def host_allowed(host: str, allowlist: Allowlist) -> bool:
    host = (host or "").lower().strip()
    allowed = {h.lower().strip() for h in allowlist.hosts}
    return host in allowed


def command_allowed(command: list[str], allowlist: Allowlist) -> bool:
    if not command:
        return False
    exe = Path(command[0]).name.lower()
    allowed = {c.lower() for c in allowlist.commands}
    return exe in allowed


def tool_allowed(tool_name: str, allowlist: Allowlist) -> bool:
    names = allowlist.tool_names or []
    if "*" in names:
        return True
    return tool_name in names


def assert_mcp_target_allowed(target: MCPTarget, scope: Scope) -> None:
    if target.transport == "stdio":
        if not command_allowed(target.command, scope.allowlist):
            raise SafetyError(
                f"MCP command not allowlisted for target {target.name}: {target.command}"
            )
        return
    if target.transport in {"http", "sse", "streamable_http"}:
        if not target.url:
            raise SafetyError(f"MCP target {target.name} missing url")
        host = urlparse(target.url).hostname or ""
        if not host_allowed(host, scope.allowlist):
            raise SafetyError(f"MCP host not allowlisted: {host}")
        return
    raise SafetyError(f"Unsupported MCP transport: {target.transport}")


def assert_url_allowed(url: str, scope: Scope) -> None:
    host = urlparse(url).hostname or ""
    if not host_allowed(host, scope.allowlist):
        raise SafetyError(f"Host not allowlisted: {host}")


def assert_chat_ui_allowed(target: AgentChatUITarget, scope: Scope) -> None:
    if not scope.flags.enable_agent_chat_ui:
        raise SafetyError("flags.enable_agent_chat_ui must be true for chat UI targets")
    assert_url_allowed(target.url, scope)
    for sel_name, sel in (
        ("input_selector", target.input_selector),
        ("send_selector", target.send_selector),
        ("messages_selector", target.messages_selector),
    ):
        if not sel or not sel.strip():
            raise SafetyError(f"agent_chat_ui.{sel_name} is required")


def doctor_checks(scope: Scope) -> list[str]:
    """Return human-readable issues; empty means OK."""
    issues: list[str] = []
    if scope.roe.authorized is not True:
        issues.append("roe.authorized is not true")
    if not scope.allowlist.hosts:
        issues.append("allowlist.hosts missing")
    if not scope.allowlist.commands:
        issues.append("allowlist.commands missing")
    if not scope.canaries:
        issues.append("warning: no canaries configured (oracle O1 will not confirm)")
    for t in scope.targets.mcp:
        try:
            assert_mcp_target_allowed(t, scope)
        except SafetyError as e:
            issues.append(str(e))
    for t in scope.targets.llm_apps:
        try:
            assert_url_allowed(t.base_url, scope)
        except SafetyError as e:
            issues.append(str(e))
    for t in scope.targets.agent_chat_ui:
        try:
            assert_chat_ui_allowed(t, scope)
        except SafetyError as e:
            issues.append(str(e))
    return issues
