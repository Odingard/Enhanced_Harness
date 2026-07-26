"""Shared budget ledger — fail closed when exhausted."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from enhanced_harness.scope import Budgets


@dataclass
class BudgetLedger:
    budgets: Budgets
    started_at: float = field(default_factory=time.time)
    requests: int = 0
    tool_calls: int = 0
    tokens: int = 0
    stopped_reason: str | None = None

    def remaining_minutes(self) -> float:
        elapsed = (time.time() - self.started_at) / 60.0
        return self.budgets.max_minutes - elapsed

    def check(self) -> str | None:
        if self.stopped_reason:
            return self.stopped_reason
        if self.remaining_minutes() <= 0:
            self.stopped_reason = "budget:max_minutes"
            return self.stopped_reason
        if self.requests >= self.budgets.max_requests:
            self.stopped_reason = "budget:max_requests"
            return self.stopped_reason
        if self.tool_calls >= self.budgets.max_tool_calls:
            self.stopped_reason = "budget:max_tool_calls"
            return self.stopped_reason
        if self.tokens >= self.budgets.max_tokens:
            self.stopped_reason = "budget:max_tokens"
            return self.stopped_reason
        return None

    def record_request(self, n: int = 1, tokens: int = 0) -> None:
        self.requests += n
        self.tokens += tokens

    def record_tool_call(self, n: int = 1) -> None:
        self.tool_calls += n

    def snapshot(self) -> dict:
        return {
            "requests": self.requests,
            "tool_calls": self.tool_calls,
            "tokens": self.tokens,
            "remaining_minutes": round(self.remaining_minutes(), 3),
            "stopped_reason": self.stopped_reason,
            "limits": self.budgets.model_dump(),
        }
