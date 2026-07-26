"""Skills registry + O1 oracle unit tests."""

from __future__ import annotations

from enhanced_harness.models import OracleSpec, ProbeResult
from enhanced_harness.oracles.o1_canary_match import canary_match
from enhanced_harness.scope import Scope
from enhanced_harness.skills.loader import load_registry


def test_registry_has_m08_skills() -> None:
    reg = load_registry()
    ids = {s.id for s in reg.for_module("M08")}
    assert "exfil.canary_direct_ask" in ids
    assert "exfil.canary_tool_arg_smuggle" in ids
    assert "exfil.encoding_base64" in ids
    for sid in ids:
        assert callable(reg.impl(sid))


def test_o1_canary_match_pass_and_hash() -> None:
    scope = Scope.model_validate(
        {
            "engagement": {"name": "t"},
            "roe": {"authorized": True, "client_name": "c"},
            "targets": {
                "mcp": [
                    {
                        "name": "m",
                        "transport": "stdio",
                        "command": ["python", "-c", "pass"],
                    }
                ]
            },
            "allowlist": {"hosts": ["127.0.0.1"], "commands": ["python"]},
            "budgets": {
                "max_minutes": 1,
                "max_requests": 1,
                "max_tool_calls": 1,
                "max_tokens": 1,
                "anomaly_tool_calls": 1,
                "dive_tool_call_fraction": 0.1,
            },
            "canaries": [{"id": "C1", "value": "CANARY123"}],
            "modules_enabled": ["M08"],
        }
    )
    probe = ProbeResult(
        hypothesis_id="h1",
        module_id="M08",
        skill_id="exfil.canary_direct_ask",
        success_signal=True,
        evidence_text="leaked CANARY123 here",
    )
    result = canary_match(probe, OracleSpec(oracle_id="O1", canary_ids=["C1"]), scope)
    assert result.passed is True
    assert result.proof_hash
    assert result.matched_canary_ids == ["C1"]


def test_o1_canary_match_fail() -> None:
    scope = Scope.model_validate(
        {
            "engagement": {"name": "t"},
            "roe": {"authorized": True, "client_name": "c"},
            "targets": {
                "llm_apps": [{"name": "l", "base_url": "http://127.0.0.1:9"}]
            },
            "allowlist": {"hosts": ["127.0.0.1"], "commands": ["python"]},
            "budgets": {
                "max_minutes": 1,
                "max_requests": 1,
                "max_tool_calls": 1,
                "max_tokens": 1,
                "anomaly_tool_calls": 1,
                "dive_tool_call_fraction": 0.1,
            },
            "canaries": [{"id": "C1", "value": "CANARY123"}],
            "modules_enabled": ["M08"],
        }
    )
    probe = ProbeResult(
        hypothesis_id="h1",
        module_id="M08",
        skill_id="exfil.canary_direct_ask",
        evidence_text="nothing",
    )
    result = canary_match(probe, OracleSpec(oracle_id="O1"), scope)
    assert result.passed is False
