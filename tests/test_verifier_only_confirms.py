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
    """Only verifier.py may assign FindingStatus.CONFIRMED (others may compare)."""
    agents = Path("enhanced_harness/agents")
    writers = []
    for p in agents.glob("*.py"):
        text = p.read_text(encoding="utf-8")
        if "status = FindingStatus.CONFIRMED" in text:
            writers.append(p.name)
    assert writers == ["verifier.py"]
