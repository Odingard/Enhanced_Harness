"""Scout — observe MCP + LLM surfaces."""

from __future__ import annotations

from typing import Any

from enhanced_harness.adapters.llm_app import LLMAppAdapter
from enhanced_harness.adapters.mcp_client import MCPClientAdapter
from enhanced_harness.agents.bus import AgentBus, Event
from enhanced_harness.evidence.package import EvidencePackage
from enhanced_harness.models import Observation, Surface
from enhanced_harness.scope import Scope


class Scout:
    role = "Scout"

    def __init__(
        self,
        scout_id: str,
        bus: AgentBus,
        scope: Scope,
        evidence: EvidencePackage,
        mcp_clients: dict[str, MCPClientAdapter],
        llm_clients: dict[str, LLMAppAdapter],
    ) -> None:
        self.scout_id = scout_id
        self.bus = bus
        self.scope = scope
        self.evidence = evidence
        self.mcp_clients = mcp_clients
        self.llm_clients = llm_clients

    async def run(self) -> Observation:
        mcp_tools: list[dict[str, Any]] = []
        mcp_resources: list[dict[str, Any]] = []
        llm_apps: list[dict[str, Any]] = []
        surfaces: list[Surface] = []
        notes: list[str] = []

        for name, client in self.mcp_clients.items():
            await client.refresh()
            for t in client.tools:
                mcp_tools.append({"target": name, **t})
            for r in client.resources:
                mcp_resources.append({"target": name, **r})
            surfaces.append(Surface.MCP)
            notes.append(f"Scouted MCP target {name}: {len(client.tools)} tools")
            self.evidence.mark_tested(f"mcp:{name}:list_tools")

        for name, client in self.llm_clients.items():
            try:
                health = await client.health()
            except Exception as e:  # noqa: BLE001
                health = {"ok": False, "error": str(e)}
            llm_apps.append({"target": name, "health": health})
            surfaces.append(Surface.LLM)
            notes.append(f"Scouted LLM app {name}")
            self.evidence.mark_tested(f"llm:{name}:health")

        # Honest coverage: modules/surfaces not in this M1 pass
        for item in [
            "hub:model_hub",
            "cloud:iam",
            "infra:breakout",
            "web:agent_chat_ui",
        ]:
            self.evidence.mark_not_tested(item)

        obs = Observation(
            scout_id=self.scout_id,
            surfaces=list(dict.fromkeys(surfaces)),
            mcp_tools=mcp_tools,
            mcp_resources=mcp_resources,
            llm_apps=llm_apps,
            notes=notes,
        )
        await self.bus.publish(
            Event(
                kind="observe",
                source=self.scout_id,
                payload=obs.model_dump(mode="json"),
            )
        )
        self.evidence.append_transcript(
            {"kind": "observe", "source": self.scout_id, "payload": obs.model_dump(mode="json")}
        )
        return obs
