"""Verifier — oracles O1–O5; ONLY agent that may set confirmed."""

from __future__ import annotations

from uuid import uuid4

from enhanced_harness.agents.bus import AgentBus, Event
from enhanced_harness.evidence.package import EvidencePackage
from enhanced_harness.models import (
    Finding,
    FindingStatus,
    Hypothesis,
    OracleResult,
    ProbeResult,
)
from enhanced_harness.modules.base import Module
from enhanced_harness.oracles.o1_canary_match import canary_match
from enhanced_harness.scope import Scope


class Verifier:
    role = "Verifier"

    def __init__(
        self,
        bus: AgentBus,
        scope: Scope,
        evidence: EvidencePackage,
        modules: dict[str, Module],
    ) -> None:
        self.bus = bus
        self.scope = scope
        self.evidence = evidence
        self.modules = modules

    async def verify(self, hyp: Hypothesis, probe: ProbeResult) -> Finding:
        mod = self.modules[hyp.module_id]
        spec = mod.oracle_spec(hyp)

        if spec.oracle_id == "O1":
            oracle: OracleResult = canary_match(probe, spec, self.scope)
        else:
            oracle = OracleResult(
                oracle_id=spec.oracle_id,
                passed=False,
                detail=f"Oracle {spec.oracle_id} not implemented in Milestone 1",
            )

        if oracle.passed:
            status = FindingStatus.CONFIRMED
            summary = (
                f"Oracle {oracle.oracle_id} passed. {oracle.detail}. "
                "CONFIRMED with proof hash (canary values redacted from markdown)."
            )
        elif probe.success_signal:
            status = FindingStatus.SUSPECTED
            summary = (
                "Strike reported a signal but oracle did not confirm. "
                "Labeled UNVERIFIED."
            )
        else:
            status = FindingStatus.REFUTED
            summary = "Probe did not produce a signal; oracle did not confirm."

        finding = Finding(
            id=f"finding-{uuid4().hex[:10]}",
            module_id=hyp.module_id,
            skill_id=hyp.skill_id,
            title=hyp.title,
            status=status,
            surface=hyp.surface,
            target=hyp.target,
            summary=summary,
            evidence_text=probe.evidence_text,
            proof_hash=oracle.proof_hash,
            oracle_id=oracle.oracle_id,
            hypothesis_id=hyp.id,
            unverified=status == FindingStatus.SUSPECTED,
        )

        # ONLY Verifier sets confirmed
        assert (
            status != FindingStatus.CONFIRMED or oracle.passed
        ), "confirmed requires oracle proof"

        await self.bus.publish(
            Event(
                kind="oracle",
                source="verifier",
                payload={
                    "finding": finding.model_dump(mode="json"),
                    "oracle": oracle.model_dump(mode="json"),
                },
            )
        )
        self.evidence.append_transcript(
            {
                "kind": "oracle",
                "source": "verifier",
                "oracle_id": oracle.oracle_id,
                "passed": oracle.passed,
                "finding_id": finding.id,
                "status": finding.status.value,
                "proof_hash": finding.proof_hash,
            }
        )
        self.evidence.add_finding(finding)
        return finding
