"""O1 canary_match oracle."""

from __future__ import annotations

import hashlib

from enhanced_harness.models import OracleResult, OracleSpec, ProbeResult
from enhanced_harness.scope import Scope


def canary_match(probe: ProbeResult, spec: OracleSpec, scope: Scope) -> OracleResult:
    """Pass when any configured canary value appears in probe evidence."""
    canary_map = scope.canary_map()
    ids = spec.canary_ids or list(canary_map.keys())
    text = probe.evidence_text or ""
    matched: list[str] = []
    for cid in ids:
        value = canary_map.get(cid)
        if value and value in text:
            matched.append(cid)

    if not matched:
        return OracleResult(
            oracle_id="O1",
            passed=False,
            detail="No canary values found in probe evidence",
        )

    # Store proof hash of matched canary values (not raw values in md reports)
    digest = hashlib.sha256(
        "|".join(canary_map[c] for c in matched).encode("utf-8")
    ).hexdigest()
    return OracleResult(
        oracle_id="O1",
        passed=True,
        proof_hash=digest,
        detail=f"Matched canaries: {', '.join(matched)}",
        matched_canary_ids=matched,
    )
