"""Strike — elastic worker; CANNOT set confirmed."""

from __future__ import annotations

from typing import Any

from enhanced_harness.agents.bus import AgentBus, Event
from enhanced_harness.budgets import BudgetLedger
from enhanced_harness.evidence.package import EvidencePackage
from enhanced_harness.models import FindingStatus, Hypothesis, ProbeResult
from enhanced_harness.modules.base import Module


class Strike:
    role = "Strike"

    def __init__(
        self,
        strike_id: str,
        bus: AgentBus,
        evidence: EvidencePackage,
        modules: dict[str, Module],
        ctx: dict[str, Any],
        budgets: BudgetLedger,
        pinned_skills: list[str] | None = None,
    ) -> None:
        self.strike_id = strike_id
        self.bus = bus
        self.evidence = evidence
        self.modules = modules
        self.ctx = ctx
        self.budgets = budgets
        self.pinned_skills = pinned_skills or []

    async def execute(self, hyp: Hypothesis) -> ProbeResult:
        stop = self.budgets.check()
        if stop:
            result = ProbeResult(
                hypothesis_id=hyp.id,
                module_id=hyp.module_id,
                skill_id=hyp.skill_id,
                success_signal=False,
                evidence_text=f"Skipped due to {stop}",
            )
            await self._emit_act(hyp, result, skipped=True)
            return result

        mod = self.modules[hyp.module_id]
        result = await mod.execute(hyp, self.ctx)
        self.budgets.record_tool_call(result.tool_calls)
        self.budgets.record_request(result.requests)

        await self._emit_act(hyp, result, skipped=False)
        # Strike may only emit suspected/refuted signals — never confirmed
        status = (
            FindingStatus.SUSPECTED if result.success_signal else FindingStatus.REFUTED
        )
        await self.bus.publish(
            Event(
                kind="signal",
                source=self.strike_id,
                payload={
                    "status": status.value,
                    "hypothesis": hyp.model_dump(mode="json"),
                    "probe": result.model_dump(mode="json"),
                },
            )
        )
        return result

    async def _emit_act(
        self, hyp: Hypothesis, result: ProbeResult, skipped: bool
    ) -> None:
        payload = {
            "strike_id": self.strike_id,
            "hypothesis_id": hyp.id,
            "module_id": hyp.module_id,
            "skill_id": hyp.skill_id,
            "success_signal": result.success_signal,
            "skipped": skipped,
        }
        await self.bus.publish(Event(kind="act", source=self.strike_id, payload=payload))
        self.evidence.append_transcript({"kind": "act", "source": self.strike_id, **payload})
