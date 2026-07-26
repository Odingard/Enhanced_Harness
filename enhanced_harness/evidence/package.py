"""Per-session evidence package."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from enhanced_harness.models import Finding, FindingStatus
from enhanced_harness.scope import Scope, dump_scope


class EvidencePackage:
    def __init__(self, out_dir: Path) -> None:
        self.out_dir = out_dir
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.transcript_path = self.out_dir / "transcript.jsonl"
        self.findings: list[Finding] = []
        self.coverage: dict[str, Any] = {
            "secure_claim_allowed": False,
            "tested": [],
            "not_tested": [],
            "notes": [
                "Enhanced Harness never claims a target is secure.",
                "Coverage lists what was and was not exercised this session.",
            ],
        }
        self._log = self._setup_log()

    def _setup_log(self) -> logging.Logger:
        logger = logging.getLogger("harness")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        fh = logging.FileHandler(self.out_dir / "harness.log", encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(fh)
        sh = logging.StreamHandler()
        sh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(sh)
        return logger

    def write_scope(self, scope: Scope) -> None:
        dump_scope(scope, self.out_dir / "scope.used.json")

    def append_transcript(self, event: dict[str, Any]) -> None:
        with self.transcript_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, default=str) + "\n")

    def add_finding(self, finding: Finding) -> None:
        self.findings.append(finding)

    def mark_tested(self, item: str) -> None:
        if item not in self.coverage["tested"]:
            self.coverage["tested"].append(item)

    def mark_not_tested(self, item: str) -> None:
        if item not in self.coverage["not_tested"]:
            self.coverage["not_tested"].append(item)

    def redact_canaries(self, text: str, scope: Scope) -> str:
        out = text
        for c in scope.canaries:
            if c.value:
                out = out.replace(c.value, f"[REDACTED:{c.id}]")
        return out

    def write_findings(self, scope: Scope) -> None:
        ordered = sorted(
            self.findings,
            key=lambda f: (
                0 if f.status == FindingStatus.CONFIRMED else 1 if f.status == FindingStatus.SUSPECTED else 2,
                f.id,
            ),
        )
        # JSON keeps proof_hash; values not embedded
        payload = [f.model_dump(mode="json") for f in ordered]
        (self.out_dir / "findings.json").write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8"
        )

        lines = ["# Findings", ""]
        confirmed = [f for f in ordered if f.status == FindingStatus.CONFIRMED]
        suspected = [f for f in ordered if f.status == FindingStatus.SUSPECTED]
        refuted = [f for f in ordered if f.status == FindingStatus.REFUTED]

        lines.append(f"Confirmed: {len(confirmed)}")
        lines.append(f"Suspected (UNVERIFIED): {len(suspected)}")
        lines.append(f"Refuted: {len(refuted)}")
        lines.append("")

        for section, items, label in [
            ("Confirmed", confirmed, None),
            ("Suspected (UNVERIFIED)", suspected, "UNVERIFIED"),
            ("Refuted", refuted, None),
        ]:
            lines.append(f"## {section}")
            lines.append("")
            if not items:
                lines.append("_None_")
                lines.append("")
                continue
            for f in items:
                title = f.title
                if label:
                    title = f"{title} — {label}"
                lines.append(f"### {f.id}: {title}")
                lines.append(f"- module: `{f.module_id}`")
                lines.append(f"- skill: `{f.skill_id}`")
                lines.append(f"- status: `{f.status.value}`")
                lines.append(f"- surface/target: `{f.surface.value}` / `{f.target}`")
                if f.proof_hash:
                    lines.append(f"- proof_hash: `{f.proof_hash}`")
                lines.append("")
                lines.append(self.redact_canaries(f.summary, scope))
                lines.append("")
                if f.evidence_text:
                    lines.append("Evidence (redacted):")
                    lines.append("```")
                    lines.append(self.redact_canaries(f.evidence_text, scope))
                    lines.append("```")
                    lines.append("")

        (self.out_dir / "findings.md").write_text("\n".join(lines), encoding="utf-8")

    def write_coverage(self) -> None:
        # Non-negotiable
        self.coverage["secure_claim_allowed"] = False
        (self.out_dir / "coverage.json").write_text(
            json.dumps(self.coverage, indent=2) + "\n", encoding="utf-8"
        )

    def finalize(self, scope: Scope) -> None:
        self.write_findings(scope)
        self.write_coverage()
