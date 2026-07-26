"""Strategist — hypotheses + Drive/Dive/Steer + spawn_requests."""

from __future__ import annotations

from enhanced_harness.agents.bus import AgentBus, Event
from enhanced_harness.evidence.package import EvidencePackage
from enhanced_harness.models import Hypothesis, Observation, SpawnRequest
from enhanced_harness.modules.base import Module
from enhanced_harness.scope import Scope
from enhanced_harness.skills.loader import SkillRegistry


class Strategist:
    role = "Strategist"

    def __init__(
        self,
        bus: AgentBus,
        scope: Scope,
        evidence: EvidencePackage,
        modules: list[Module],
        skills: SkillRegistry,
    ) -> None:
        self.bus = bus
        self.scope = scope
        self.evidence = evidence
        self.modules = modules
        self.skills = skills
        self.mode = "drive"

    async def plan(self, obs: Observation) -> tuple[list[Hypothesis], list[SpawnRequest]]:
        hyps: list[Hypothesis] = []
        for mod in self.modules:
            hyps.extend(mod.enumerate_hypotheses(obs, self.scope, self.skills))

        spawn_requests: list[SpawnRequest] = []
        if hyps:
            # Drive: breadth across skills
            by_skill: dict[str, list[Hypothesis]] = {}
            for h in hyps:
                by_skill.setdefault(h.skill_id, []).append(h)
            # Ask conductor for baseline strikes covering distinct skills
            skill_ids = list(by_skill.keys())
            spawn_requests.append(
                SpawnRequest(
                    reason="drive:initial_coverage",
                    module_id=hyps[0].module_id,
                    skill_ids=skill_ids,
                    count=min(
                        max(1, self.scope.planner.min_parallel_strikes),
                        len(skill_ids) or 1,
                    ),
                    mode="drive",
                )
            )
            self.mode = "drive"

        await self.bus.publish(
            Event(
                kind="plan",
                source="strategist",
                payload={
                    "mode": self.mode,
                    "hypothesis_count": len(hyps),
                    "spawn_requests": [s.model_dump() for s in spawn_requests],
                    "hypotheses": [h.model_dump(mode="json") for h in hyps],
                },
            )
        )
        self.evidence.append_transcript(
            {
                "kind": "plan",
                "source": "strategist",
                "mode": self.mode,
                "hypothesis_count": len(hyps),
            }
        )
        return hyps, spawn_requests

    def on_signal(self, hyp: Hypothesis) -> SpawnRequest | None:
        """Emit dive spawn request on suspected/confirmed signal (M1 records intent)."""
        self.mode = "dive"
        req = SpawnRequest(
            reason=f"dive:signal:{hyp.id}",
            module_id=hyp.module_id,
            skill_ids=[hyp.skill_id],
            count=1,
            mode="dive",
        )
        return req
