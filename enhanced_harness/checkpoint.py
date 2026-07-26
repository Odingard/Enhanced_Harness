"""Session checkpoint persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class Checkpoint(BaseModel):
    session_id: str
    phase: str = "init"
    live_strikes: int = 0
    hypotheses_done: list[str] = Field(default_factory=list)
    confirmed_count: int = 0
    stop_reason: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(
            json.dumps(self.model_dump(mode="json"), indent=2) + "\n",
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: str | Path) -> Checkpoint:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.model_validate(data)
