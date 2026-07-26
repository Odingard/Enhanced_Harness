"""Shared domain models for Enhanced Harness."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FindingStatus(str, Enum):
    CONFIRMED = "confirmed"
    SUSPECTED = "suspected"
    REFUTED = "refuted"


class Surface(str, Enum):
    MCP = "mcp"
    LLM = "llm"
    HUB = "hub"
    CLOUD = "cloud"
    INFRA = "infra"
    RAG = "rag"
    WEB = "web"


class Hypothesis(BaseModel):
    id: str
    module_id: str
    skill_id: str
    title: str
    surface: Surface
    target: str
    rationale: str = ""
    params: dict[str, Any] = Field(default_factory=dict)
    canary_ids: list[str] = Field(default_factory=list)


class ProbeResult(BaseModel):
    hypothesis_id: str
    module_id: str
    skill_id: str
    success_signal: bool = False
    evidence_text: str = ""
    raw: dict[str, Any] = Field(default_factory=dict)
    tool_calls: int = 0
    requests: int = 0


class OracleSpec(BaseModel):
    oracle_id: str
    canary_ids: list[str] = Field(default_factory=list)
    params: dict[str, Any] = Field(default_factory=dict)


class OracleResult(BaseModel):
    oracle_id: str
    passed: bool
    proof_hash: str | None = None
    detail: str = ""
    matched_canary_ids: list[str] = Field(default_factory=list)


class Finding(BaseModel):
    id: str
    module_id: str
    skill_id: str
    title: str
    status: FindingStatus
    surface: Surface
    target: str
    summary: str
    evidence_text: str = ""
    proof_hash: str | None = None
    oracle_id: str | None = None
    hypothesis_id: str | None = None
    unverified: bool = False


class Observation(BaseModel):
    scout_id: str
    surfaces: list[Surface] = Field(default_factory=list)
    mcp_tools: list[dict[str, Any]] = Field(default_factory=list)
    mcp_resources: list[dict[str, Any]] = Field(default_factory=list)
    llm_apps: list[dict[str, Any]] = Field(default_factory=list)
    chat_uis: list[dict[str, Any]] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class SpawnRequest(BaseModel):
    reason: str
    module_id: str
    skill_ids: list[str] = Field(default_factory=list)
    count: int = 1
    mode: str = "drive"  # drive | dive | steer
