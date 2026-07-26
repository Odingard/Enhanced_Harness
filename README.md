# Enhanced Harness

**Odingard Security** — Shannon-class autonomous multi-agent red team for
**Agentic AI / MCP / model-hub / AI cloud supply chain**.

> Shannon (Keygraph) = autonomous terminal multi-agent red team for web apps/APIs  
> **Enhanced Harness** = the same job for Agentic AI and MCP surfaces

This repository is **not** ARGUS and **not** ALEC. Related Odingard products may
be mentioned only as adjacent tools — they are not this CLI, package, or brand.

## Status

**Runnable multi-agent harness.** Scout → Strategist → Strike → Verifier → Scribe
produces oracle-**CONFIRMED** findings (O1 canary_match) against:

- local vulnerable MCP + LLM API fixtures
- local **vulnerable AI chat page** fixture (Playwright, allowlisted chat box)
- local **OWASP FinBot CTF** (Juice Shop for Agentic AI) via Docker

Visuals: [`docs/VISUALS.md`](docs/VISUALS.md) · FinBot lab: [`docs/FINBOT_LAB.md`](docs/FINBOT_LAB.md)

## Install

```bash
python -m venv .venv && .venv/bin/pip install -e ".[lab]"
.venv/bin/playwright install chromium
```

`[dev]` is enough for MCP/LLM fixtures; `[lab]` adds Playwright for the chat page.

## Operator happy path

```bash
.venv/bin/harness setup
.venv/bin/harness doctor --scope scope.json
.venv/bin/harness start --scope scope.json
.venv/bin/harness logs --follow
.venv/bin/harness report --out harness-out/<session>/
```

CLI: `harness` · Package: `enhanced_harness` · Alias: `harness engage`

## Test against the vulnerable AI chat page

Local lab page (intentionally leaks a canary when asked):

```bash
# terminal A — start the page
.venv/bin/harness lab-page
# open http://127.0.0.1:8766/ in a browser if you want to poke it manually

# terminal B — run the harness against it
cp scope.vulnerable_ai_page.example.json scope.json
.venv/bin/harness doctor --scope scope.json
.venv/bin/harness start --scope scope.json
.venv/bin/harness report
```

One-shot acceptance for the chat page:

```bash
./scripts/run_vulnerable_page_acceptance.sh
```

### OWASP FinBot CTF (Juice Shop for Agentic AI)

```bash
export OPENAI_API_KEY=sk-...   # needed for live AI-agent challenges
./scripts/lab_finbot_up.sh     # http://127.0.0.1:8000/
# uses Docker Compose when healthy; falls back to native uv+Redis otherwise
# complete FinBot signup/onboarding in the browser, open Vendor AI Assistant
cp scope.finbot.example.json scope.json
# set engagement canaries; keep ROE/allowlist honest
.venv/bin/harness start --scope scope.json
./scripts/lab_finbot_down.sh
```

Fair use only — this repo does **not** encode FinBot challenges, flags, or walkthroughs.
See [`docs/FINBOT_LAB.md`](docs/FINBOT_LAB.md) · visuals [`docs/VISUALS.md`](docs/VISUALS.md).

Requires `flags.enable_agent_chat_ui: true` and an allowlisted
`targets.agent_chat_ui[]` entry with chat selectors. This is **not** a generic
web XSS/SQLi pack — only the configured chat box.

## Multi-agent roster

| Agent | Job |
|-------|-----|
| Conductor | Session, ROE, budgets, kill switch, spawn/retire |
| Scout | Map MCP tools/resources + LLM health + chat UI |
| Strategist | Hypotheses + Drive/Dive/Steer spawn requests |
| Strike-* | Execute module **skills** (cannot confirm) |
| Verifier | Oracles only — sole writer of `confirmed` |
| Scribe | Transcript, findings, coverage, report |

Details: [`MULTIAGENT.md`](MULTIAGENT.md).

## Skills (M08)

Registry: `skills/registry.yaml`. Surfaces: `mcp`, `llm`, `web`.

- `exfil.canary_direct_ask`
- `exfil.canary_tool_arg_smuggle`
- `exfil.encoding_base64`

Skills never set `confirmed`. Verifier confirms with oracle **O1 canary_match**.

## Acceptance

```bash
./scripts/run_acceptance.sh                 # MCP + LLM fixtures
./scripts/run_vulnerable_page_acceptance.sh # AI chat page (Playwright)
./scripts/check_no_stubs.sh
.venv/bin/pytest -m "not live"
```

Evidence package per session:

`scope.used.json` · `transcript.jsonl` · `checkpoint.json` · `findings.json` ·
`findings.md` · `coverage.json` · `harness.log`

## Scope / safety

Fail closed: `roe.authorized` must be true; allowlist + budgets required;
destructive/DoW default false; kill-switch file aborts the loop; canary values
are redacted from `findings.md` (proof hash retained in `findings.json`).
See `scope.example.json` and `scope.vulnerable_ai_page.example.json`.

## Product language

Enhanced Harness is a full V1 multi-agent red team for authorized Agentic AI,
MCP, model-hub supply chain, cloud/IAM, poisoning, infra, OSINT, and
control-validation engagements. Scout maps surfaces; Strategist
drives/dives/steers; Strike agents spawn in parallel on signal; Verifier
confirms only with oracle proof. Dangerous packs are ROE flag-gated and
sandboxed — included, not omitted. Suspected items are labeled unverified. It
does not certify that a system is secure.

## Boundaries

- Terminal-first CLI (no product web UI / dashboard).
- Agent Chat UI adapter is flag-gated (`enable_agent_chat_ui`), allowlisted chat
  box only — not a generic web XSS/SQLi pack.
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
