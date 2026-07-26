"""Scribe — transcript, findings, coverage, report."""

from __future__ import annotations

from enhanced_harness.agents.bus import AgentBus, Event
from enhanced_harness.checkpoint import Checkpoint
from enhanced_harness.evidence.package import EvidencePackage
from enhanced_harness.scope import Scope


class Scribe:
    role = "Scribe"

    def __init__(
        self,
        bus: AgentBus,
        scope: Scope,
        evidence: EvidencePackage,
        checkpoint: Checkpoint,
    ) -> None:
        self.bus = bus
        self.scope = scope
        self.evidence = evidence
        self.checkpoint = checkpoint

    async def record_spawn(self, strike_id: str, reason: str, mode: str) -> None:
        payload = {
            "kind": "spawn",
            "source": "scribe",
            "strike_id": strike_id,
            "reason": reason,
            "mode": mode,
        }
        await self.bus.publish(Event(kind="spawn", source="scribe", payload=payload))
        self.evidence.append_transcript(payload)

    async def record_retire(self, strike_id: str, reason: str) -> None:
        payload = {
            "kind": "retire",
            "source": "scribe",
            "strike_id": strike_id,
            "reason": reason,
        }
        await self.bus.publish(Event(kind="retire", source="scribe", payload=payload))
        self.evidence.append_transcript(payload)

    def write_report(self) -> None:
        self.evidence.finalize(self.scope)
        self.checkpoint.save(self.evidence.out_dir / "checkpoint.json")
        self.evidence.append_transcript(
            {
                "kind": "adapt",
                "source": "scribe",
                "phase": self.checkpoint.phase,
                "confirmed_count": self.checkpoint.confirmed_count,
                "stop_reason": self.checkpoint.stop_reason,
            }
        )
