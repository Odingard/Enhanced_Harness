"""Conductor — session, ROE, budgets, kill switch, SPAWN/RETIRE, stop."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from enhanced_harness.adapters.llm_app import LLMAppAdapter
from enhanced_harness.adapters.mcp_client import MCPClientAdapter
from enhanced_harness.agents.bus import AgentBus
from enhanced_harness.agents.scout import Scout
from enhanced_harness.agents.scribe import Scribe
from enhanced_harness.agents.strategist import Strategist
from enhanced_harness.agents.strike import Strike
from enhanced_harness.agents.verifier import Verifier
from enhanced_harness.budgets import BudgetLedger
from enhanced_harness.checkpoint import Checkpoint
from enhanced_harness.evidence.package import EvidencePackage
from enhanced_harness.models import FindingStatus, Hypothesis
from enhanced_harness.modules import load_modules
from enhanced_harness.safety import SafetyError, kill_switch_active
from enhanced_harness.scope import Scope
from enhanced_harness.skills.loader import load_registry


class Conductor:
    role = "Conductor"

    def __init__(self, scope: Scope, out_dir: Path) -> None:
        self.scope = scope
        self.out_dir = out_dir
        self.session_id = f"sess-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:6]}"
        self.bus = AgentBus()
        self.evidence = EvidencePackage(out_dir)
        self.budgets = BudgetLedger(scope.budgets)
        self.checkpoint = Checkpoint(session_id=self.session_id, phase="init")
        self.skills = load_registry()
        self.modules_list = load_modules(scope.modules_enabled)
        self.modules = {m.id: m for m in self.modules_list}
        self.mcp_clients: dict[str, MCPClientAdapter] = {}
        self.llm_clients: dict[str, LLMAppAdapter] = {}
        self.live_strikes = 0
        self._strike_seq = 0
        self.scribe = Scribe(self.bus, scope, self.evidence, self.checkpoint)
        self.strategist = Strategist(
            self.bus, scope, self.evidence, self.modules_list, self.skills
        )
        self.verifier = Verifier(self.bus, scope, self.evidence, self.modules)

    async def _connect_targets(self) -> None:
        for t in self.scope.targets.mcp:
            client = MCPClientAdapter(t, self.scope)
            await client.connect()
            self.mcp_clients[t.name] = client
        for t in self.scope.targets.llm_apps:
            client = LLMAppAdapter(t, self.scope)
            await client.connect()
            self.llm_clients[t.name] = client

    async def _close_targets(self) -> None:
        for c in self.mcp_clients.values():
            await c.close()
        for c in self.llm_clients.values():
            await c.close()

    def _spawn_strike(self, pinned_skills: list[str] | None = None) -> Strike | None:
        if kill_switch_active(self.scope.kill_switch_path):
            return None
        if self.budgets.check():
            return None
        if self.live_strikes >= self.scope.planner.max_parallel_strikes:
            return None
        self._strike_seq += 1
        strike_id = f"strike-{self._strike_seq}"
        ctx: dict[str, Any] = {
            "skills": self.skills,
            "scope": self.scope,
            "mcp_clients": self.mcp_clients,
            "llm_clients": self.llm_clients,
        }
        strike = Strike(
            strike_id=strike_id,
            bus=self.bus,
            evidence=self.evidence,
            modules=self.modules,
            ctx=ctx,
            budgets=self.budgets,
            pinned_skills=pinned_skills,
        )
        self.live_strikes += 1
        self.checkpoint.live_strikes = self.live_strikes
        return strike

    async def run(self) -> Path:
        if self.scope.roe.authorized is not True:
            raise SafetyError("ROE not authorized — refuse start")

        self.evidence.write_scope(self.scope)
        self.evidence._log.info(
            "Conductor starting session %s (agents: Conductor/Scout/Strategist/Strike/Verifier/Scribe)",
            self.session_id,
        )
        self.checkpoint.phase = "connect"
        await self._connect_targets()

        try:
            scout = Scout(
                scout_id="scout-1",
                bus=self.bus,
                scope=self.scope,
                evidence=self.evidence,
                mcp_clients=self.mcp_clients,
                llm_clients=self.llm_clients,
            )
            self.checkpoint.phase = "scout"
            obs = await scout.run()

            self.checkpoint.phase = "plan"
            hyps, spawn_reqs = await self.strategist.plan(obs)
            if not hyps:
                self.checkpoint.stop_reason = "no_hypotheses"
                self.checkpoint.phase = "done"
                self.scribe.write_report()
                return self.out_dir

            # Assign hypotheses round-robin across spawned strikes
            pending = list(hyps)
            confirmed = 0

            # Baseline spawn
            baseline = self.scope.planner.min_parallel_strikes
            if spawn_reqs:
                baseline = max(baseline, spawn_reqs[0].count)
            baseline = max(1, min(baseline, self.scope.planner.max_parallel_strikes))

            workers: list[Strike] = []
            for i in range(baseline):
                pinned = []
                if spawn_reqs and spawn_reqs[0].skill_ids:
                    pinned = [spawn_reqs[0].skill_ids[i % len(spawn_reqs[0].skill_ids)]]
                strike = self._spawn_strike(pinned)
                if strike is None:
                    break
                workers.append(strike)
                await self.scribe.record_spawn(
                    strike.strike_id, reason="drive:baseline", mode="drive"
                )

            if not workers:
                self.checkpoint.stop_reason = self.budgets.stopped_reason or "spawn_refused"
                self.checkpoint.phase = "done"
                self.scribe.write_report()
                return self.out_dir

            self.checkpoint.phase = "strike"
            wi = 0
            while pending:
                if kill_switch_active(self.scope.kill_switch_path):
                    self.checkpoint.stop_reason = "kill_switch"
                    break
                stop = self.budgets.check()
                if stop:
                    self.checkpoint.stop_reason = stop
                    break

                hyp = pending.pop(0)
                strike = workers[wi % len(workers)]
                wi += 1

                # Prefer pinned skill match when possible
                if strike.pinned_skills and hyp.skill_id not in strike.pinned_skills:
                    alt = next(
                        (w for w in workers if hyp.skill_id in (w.pinned_skills or [])),
                        strike,
                    )
                    strike = alt

                probe = await strike.execute(hyp)
                self.checkpoint.hypotheses_done.append(hyp.id)

                finding = await self.verifier.verify(hyp, probe)
                if finding.status == FindingStatus.CONFIRMED:
                    confirmed += 1
                    self.checkpoint.confirmed_count = confirmed
                    # On signal: attempt dive spawn (elastic — M1 may still be 1 pool)
                    dive = self.strategist.on_signal(hyp)
                    if dive and self.live_strikes < self.scope.planner.max_parallel_strikes:
                        extra = self._spawn_strike(dive.skill_ids[:1])
                        if extra is not None:
                            workers.append(extra)
                            await self.scribe.record_spawn(
                                extra.strike_id, reason=dive.reason, mode="dive"
                            )
                    if self.scope.flags.stop_on_first_confirmed:
                        self.checkpoint.stop_reason = "stop_on_first_confirmed"
                        break

            if self.checkpoint.stop_reason is None:
                self.checkpoint.stop_reason = "no_hypotheses_left"

            # Retire strikes
            for strike in workers:
                await self.scribe.record_retire(strike.strike_id, reason="session_end")
                self.live_strikes = max(0, self.live_strikes - 1)
            self.checkpoint.live_strikes = self.live_strikes
            self.checkpoint.phase = "done"
            self.scribe.write_report()
            self.evidence._log.info(
                "Session complete: confirmed=%s stop=%s out=%s",
                self.checkpoint.confirmed_count,
                self.checkpoint.stop_reason,
                self.out_dir,
            )
            return self.out_dir
        finally:
            await self._close_targets()


async def run_session(scope: Scope, out_dir: Path) -> Path:
    conductor = Conductor(scope, out_dir)
    return await conductor.run()


def run_session_sync(scope: Scope, out_dir: Path) -> Path:
    return asyncio.run(run_session(scope, out_dir))
