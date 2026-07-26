# Enhanced Harness

**Odingard Security** — Shannon-class autonomous multi-agent red team for
**Agentic AI / MCP / model-hub / AI cloud supply chain**.

> Shannon (Keygraph) = autonomous terminal multi-agent red team for web apps/APIs  
> **Enhanced Harness** = the same job for Agentic AI and MCP surfaces

This repository is **not** ARGUS and **not** ALEC. Related Odingard products may
be mentioned only as adjacent tools — they are not this CLI, package, or brand.

## Status

**Milestone 1 runnable.** Multi-agent path
Scout → Strategist → Strike → Verifier → Scribe produces ≥1 oracle-**CONFIRMED**
finding (O1 canary_match) against local vulnerable MCP + LLM fixtures.

Competitive gap analysis vs the public awesome-list:
[`COMPETITIVE_LANDSCAPE.md`](COMPETITIVE_LANDSCAPE.md).

## Install

```bash
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
```

## Operator happy path

```bash
.venv/bin/harness setup
.venv/bin/harness doctor --scope scope.json
.venv/bin/harness start --scope scope.json
.venv/bin/harness logs --follow
.venv/bin/harness report --out harness-out/<session>/
```

CLI: `harness` · Package: `enhanced_harness` · Alias: `harness engage`

Useful commands:

```bash
harness modules
harness version
harness resume --out harness-out/<session>/
```

## Multi-agent roster

| Agent | Job |
|-------|-----|
| Conductor | Session, ROE, budgets, kill switch, spawn/retire |
| Scout | Map MCP tools/resources + LLM app health |
| Strategist | Hypotheses + Drive/Dive/Steer spawn requests |
| Strike-* | Execute module **skills** (cannot confirm) |
| Verifier | Oracles only — sole writer of `confirmed` |
| Scribe | Transcript, findings, coverage, report |

Details: [`MULTIAGENT.md`](MULTIAGENT.md).

## Skills (M1)

Registry: `skills/registry.yaml`. Module **M08 secret_exfiltration** runs via:

- `exfil.canary_direct_ask`
- `exfil.canary_tool_arg_smuggle`
- `exfil.encoding_base64`

Skills never set `confirmed`. Verifier confirms with oracle **O1 canary_match**.

## Acceptance

```bash
./scripts/run_acceptance.sh
./scripts/check_no_stubs.sh
.venv/bin/pytest -m "not live"
```

`run_acceptance.sh` must produce ≥1 **CONFIRMED** finding with `proof_hash` and a
full evidence package:

`scope.used.json` · `transcript.jsonl` · `checkpoint.json` · `findings.json` ·
`findings.md` · `coverage.json` · `harness.log`

## Scope / safety

Fail closed: `roe.authorized` must be true; allowlist + budgets required;
destructive/DoW default false; kill-switch file aborts the loop; canary values
are redacted from `findings.md` (proof hash retained in `findings.json`).
See `scope.example.json`.

## Product language

Enhanced Harness is a full V1 multi-agent red team for authorized Agentic AI,
MCP, model-hub supply chain, cloud/IAM, poisoning, infra, OSINT, and
control-validation engagements. Scout maps surfaces; Strategist
drives/dives/steers; Strike agents spawn in parallel on signal; Verifier
confirms only with oracle proof. Dangerous packs are ROE flag-gated and
sandboxed — included, not omitted. Suspected items are labeled unverified. It
does not certify that a system is secure.

## Boundaries

- Terminal-first CLI only in v1 (no web UI / dashboard).
- Optional Playwright Agent Chat UI is Phase B, default OFF — allowlisted chat
  box only; not a generic web XSS/SQLi pack.
- Lab target https://owasp-finbot-ctf.org/ may be used for fair live testing
  only. Do not encode FinBot challenges, flags, detectors, or walkthroughs.
- Confirmed findings require oracle proof; only the Verifier agent may set
  `confirmed`.
- `coverage.json` always sets `secure_claim_allowed: false`.

## Build prompt

Autonomous builder prompt: [`DOWNLOAD_THIS_PROMPT.md`](DOWNLOAD_THIS_PROMPT.md).  
Agent instructions: [`AGENTS.md`](AGENTS.md).

## License

TBD by Odingard Security.
