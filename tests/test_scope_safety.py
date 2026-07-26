"""Scope + safety fail-closed tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from enhanced_harness.safety import doctor_checks
from enhanced_harness.scope import Scope, load_scope


def _valid_scope_dict() -> dict:
    return {
        "engagement": {"name": "t", "client_name": "c"},
        "roe": {"authorized": True, "client_name": "c"},
        "targets": {
            "mcp": [
                {
                    "name": "m",
                    "transport": "stdio",
                    "command": ["python", "-m", "tests.fixtures.mcp.vulnerable_server"],
                }
            ],
            "llm_apps": [],
        },
        "allowlist": {"hosts": ["127.0.0.1"], "commands": ["python", "python3"]},
        "budgets": {
            "max_minutes": 5,
            "max_requests": 10,
            "max_tool_calls": 10,
            "max_tokens": 1000,
            "anomaly_tool_calls": 5,
            "dive_tool_call_fraction": 0.4,
        },
        "canaries": [{"id": "C1", "value": "SECRET"}],
        "modules_enabled": ["M08"],
    }


def test_scope_requires_authorized(tmp_path: Path) -> None:
    data = _valid_scope_dict()
    data["roe"]["authorized"] = False
    p = tmp_path / "scope.json"
    p.write_text(json.dumps(data))
    with pytest.raises(Exception):
        load_scope(p)


def test_scope_requires_allowlist_hosts() -> None:
    data = _valid_scope_dict()
    data["allowlist"]["hosts"] = []
    with pytest.raises(Exception):
        Scope.model_validate(data)


def test_doctor_ok() -> None:
    sc = Scope.model_validate(_valid_scope_dict())
    issues = [i for i in doctor_checks(sc) if not i.startswith("warning:")]
    assert issues == []
