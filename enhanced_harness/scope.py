"""Scope loading and fail-closed validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class Engagement(BaseModel):
    name: str
    client_name: str | None = None


class ROE(BaseModel):
    authorized: bool
    client_name: str


class MCPTarget(BaseModel):
    name: str
    transport: str = "stdio"
    command: list[str] = Field(default_factory=list)
    cwd: str | None = None
    url: str | None = None
    env: dict[str, str] = Field(default_factory=dict)


class LLMTarget(BaseModel):
    name: str
    base_url: str
    chat_path: str = "/v1/chat"
    headers: dict[str, str] = Field(default_factory=dict)


class Targets(BaseModel):
    mcp: list[MCPTarget] = Field(default_factory=list)
    llm_apps: list[LLMTarget] = Field(default_factory=list)


class Allowlist(BaseModel):
    hosts: list[str] = Field(default_factory=list)
    commands: list[str] = Field(default_factory=list)
    tool_names: list[str] = Field(default_factory=lambda: ["*"])


class Budgets(BaseModel):
    max_minutes: int = 30
    max_requests: int = 500
    max_tool_calls: int = 200
    max_tokens: int = 200000
    anomaly_tool_calls: int = 80
    dive_tool_call_fraction: float = 0.4


class Flags(BaseModel):
    allow_destructive: bool = False
    allow_dow_probe: bool = False
    allow_model_hub: bool = False
    allow_cloud: bool = False
    allow_infra: bool = False
    allow_osint: bool = False
    allow_poison: bool = False
    allow_evasion: bool = False
    stop_on_first_confirmed: bool = False
    enable_agent_chat_ui: bool = False


class Canary(BaseModel):
    id: str
    value: str
    kind: str = "secret"


class PlannerConfig(BaseModel):
    min_parallel_strikes: int = 2
    max_parallel_strikes: int = 8
    max_spawn_per_signal: int = 3
    max_scout_instances: int = 2


class Scope(BaseModel):
    engagement: Engagement
    roe: ROE
    targets: Targets
    allowlist: Allowlist
    budgets: Budgets
    flags: Flags = Field(default_factory=Flags)
    canaries: list[Canary] = Field(default_factory=list)
    oracle_hooks: dict[str, Any] = Field(default_factory=dict)
    planner: PlannerConfig = Field(default_factory=PlannerConfig)
    kill_switch_path: str = "harness-out/KILL"
    modules_enabled: list[str] = Field(default_factory=lambda: ["M08"])

    @field_validator("modules_enabled")
    @classmethod
    def _nonempty_modules(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("modules_enabled must not be empty")
        return v

    @model_validator(mode="after")
    def _fail_closed(self) -> Scope:
        if self.roe.authorized is not True:
            raise ValueError("ROE not authorized: roe.authorized must be true")
        if not self.allowlist.hosts:
            raise ValueError("allowlist.hosts is required (fail closed)")
        if not self.allowlist.commands:
            raise ValueError("allowlist.commands is required (fail closed)")
        if self.budgets.max_minutes <= 0:
            raise ValueError("budgets.max_minutes must be > 0")
        if self.budgets.max_requests <= 0:
            raise ValueError("budgets.max_requests must be > 0")
        if self.budgets.max_tool_calls <= 0:
            raise ValueError("budgets.max_tool_calls must be > 0")
        if not self.targets.mcp and not self.targets.llm_apps:
            raise ValueError("at least one MCP or LLM target is required")
        return self

    def canary_map(self) -> dict[str, str]:
        return {c.id: c.value for c in self.canaries}


def load_scope(path: str | Path) -> Scope:
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    return Scope.model_validate(data)


def dump_scope(scope: Scope, path: str | Path) -> None:
    Path(path).write_text(
        json.dumps(scope.model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8",
    )
