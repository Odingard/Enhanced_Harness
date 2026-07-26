"""Only Verifier may set confirmed."""

from __future__ import annotations

import ast
from pathlib import Path


def test_strike_source_never_assigns_confirmed() -> None:
    src = Path("enhanced_harness/agents/strike.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "CONFIRMED":
            # Allow referencing enum for comparison exclusion only via SUSPECTED/REFUTED path
            pass
    assert "FindingStatus.CONFIRMED" not in src
    assert "status=\"confirmed\"" not in src
    assert 'status="confirmed"' not in src


def test_verifier_is_only_confirm_writer() -> None:
    agents = Path("enhanced_harness/agents")
    confirmed_files = []
    for p in agents.glob("*.py"):
        text = p.read_text(encoding="utf-8")
        if "FindingStatus.CONFIRMED" in text or 'status = FindingStatus.CONFIRMED' in text:
            confirmed_files.append(p.name)
    assert confirmed_files == ["verifier.py"]
