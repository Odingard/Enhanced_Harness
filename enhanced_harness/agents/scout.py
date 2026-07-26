"""Scout — observe MCP + LLM + allowlisted Agent Chat UI surfaces."""

from __future__ import annotations

from typing import Any

from enhanced_harness.adapters.agent_chat_ui import AgentChatUIAdapter
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
        chat_ui_clients: dict[str, AgentChatUIAdapter] | None = None,
    ) -> None:
        self.scout_id = scout_id
        self.bus = bus
        self.scope = scope
        self.evidence = evidence
        self.mcp_clients = mcp_clients
        self.llm_clients = llm_clients
        self.chat_ui_clients = chat_ui_clients or {}

    async def run(self) -> Observation:
        mcp_tools: list[dict[str, Any]] = []
        mcp_resources: list[dict[str, Any]] = []
        llm_apps: list[dict[str, Any]] = []
        chat_uis: list[dict[str, Any]] = []
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

        for name, client in self.chat_ui_clients.items():
            obs = await client.observe()
            chat_uis.append(obs)
            surfaces.append(Surface.WEB)
            notes.append(f"Scouted Agent Chat UI {name}: title={obs.get('title')}")
            self.evidence.mark_tested(f"web:{name}:chat_ui")

        # Honest coverage for surfaces not exercised this session
        for item in ["hub:model_hub", "cloud:iam", "infra:breakout"]:
            self.evidence.mark_not_tested(item)
        if not self.chat_ui_clients:
            self.evidence.mark_not_tested("web:agent_chat_ui")

        obs = Observation(
            scout_id=self.scout_id,
            surfaces=list(dict.fromkeys(surfaces)),
            mcp_tools=mcp_tools,
            mcp_resources=mcp_resources,
            llm_apps=llm_apps,
            chat_uis=chat_uis,
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
