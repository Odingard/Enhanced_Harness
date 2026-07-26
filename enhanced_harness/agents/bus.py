"""Async message bus for agent coordination."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Event:
    kind: str
    source: str
    payload: dict[str, Any] = field(default_factory=dict)


class AgentBus:
    def __init__(self) -> None:
        self._subs: dict[str, list[asyncio.Queue[Event]]] = defaultdict(list)
        self._all: list[asyncio.Queue[Event]] = []
        self.transcript: list[Event] = []

    def subscribe(self, kind: str | None = None) -> asyncio.Queue[Event]:
        q: asyncio.Queue[Event] = asyncio.Queue()
        if kind is None:
            self._all.append(q)
        else:
            self._subs[kind].append(q)
        return q

    async def publish(self, event: Event) -> None:
        self.transcript.append(event)
        for q in list(self._all):
            await q.put(event)
        for q in list(self._subs.get(event.kind, [])):
            await q.put(event)
