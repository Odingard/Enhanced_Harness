"""M08 secret_exfiltration — executed via skills (not a monolith)."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from enhanced_harness.models import (
    Hypothesis,
    Observation,
    OracleSpec,
    ProbeResult,
    Surface,
)
from enhanced_harness.modules.base import Module
from enhanced_harness.scope import Scope
from enhanced_harness.skills.loader import SkillRegistry


class M08SecretExfiltration(Module):
    id = "M08"
    name = "secret_exfiltration"
    surfaces = ["mcp", "llm", "web"]

    def enumerate_hypotheses(
        self, obs: Observation, scope: Scope, skills: SkillRegistry
    ) -> list[Hypothesis]:
        hyps: list[Hypothesis] = []
        if not scope.canaries:
            return hyps

        skill_metas = skills.for_module("M08")
        flag_vals = scope.flags.model_dump()
        canary = scope.canaries[0]

        targets: list[tuple[Surface, str]] = []
        if obs.mcp_tools:
            for t in scope.targets.mcp:
                targets.append((Surface.MCP, t.name))
        if obs.llm_apps or scope.targets.llm_apps:
            for t in scope.targets.llm_apps:
                targets.append((Surface.LLM, t.name))
        if obs.chat_uis or scope.targets.agent_chat_ui:
            for t in scope.targets.agent_chat_ui:
                targets.append((Surface.WEB, t.name))

        for surface, target_name in targets:
            for meta in skill_metas:
                if surface.value not in meta.surfaces:
                    continue
                if not skills.allowed(meta.id, flag_vals):
                    continue
                hyps.append(
                    Hypothesis(
                        id=f"hyp-{uuid4().hex[:10]}",
                        module_id=self.id,
                        skill_id=meta.id,
                        title=f"M08 {meta.name} on {target_name}",
                        surface=surface,
                        target=target_name,
                        rationale=meta.description,
                        params={"canary_id": canary.id},
                        canary_ids=[canary.id],
                    )
                )
        return hyps

    async def execute(self, hyp: Hypothesis, ctx: dict[str, Any]) -> ProbeResult:
        skills: SkillRegistry = ctx["skills"]
        scope: Scope = ctx["scope"]
        mcp_clients = ctx.get("mcp_clients") or {}
        llm_clients = ctx.get("llm_clients") or {}
        chat_ui_clients = ctx.get("chat_ui_clients") or {}

        canary_id = hyp.params.get("canary_id") or (
            hyp.canary_ids[0] if hyp.canary_ids else None
        )
        if not canary_id:
            return ProbeResult(
                hypothesis_id=hyp.id,
                module_id=self.id,
                skill_id=hyp.skill_id,
                success_signal=False,
                evidence_text="No canary configured",
            )
        canary_value = scope.canary_map()[canary_id]

        mcp = mcp_clients.get(hyp.target) if hyp.surface == Surface.MCP else None
        llm = llm_clients.get(hyp.target) if hyp.surface == Surface.LLM else None
        chat_ui = (
            chat_ui_clients.get(hyp.target) if hyp.surface == Surface.WEB else None
        )

        fn = skills.impl(hyp.skill_id)
        out = await fn(
            mcp=mcp,
            llm=llm,
            chat_ui=chat_ui,
            canary_id=canary_id,
            canary_value=canary_value,
        )
        return ProbeResult(
            hypothesis_id=hyp.id,
            module_id=self.id,
            skill_id=hyp.skill_id,
            success_signal=bool(out.get("success_signal")),
            evidence_text=out.get("evidence_text") or "",
            raw=out.get("raw") or {},
            tool_calls=int(out.get("tool_calls") or 0),
            requests=int(out.get("requests") or 0),
        )

    def oracle_spec(self, hyp: Hypothesis) -> OracleSpec:
        return OracleSpec(oracle_id="O1", canary_ids=list(hyp.canary_ids))
