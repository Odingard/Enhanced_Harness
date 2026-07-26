# Enhanced Harness — visuals

Terminal-first multi-agent red team (no product dashboard).

## Architecture

<img alt="Enhanced Harness multi-agent architecture" src="visuals/enhanced-harness-architecture.png" />

Roster flow:

`Scout → Strategist → Strike-* → Verifier → Scribe`  
Conductor owns ROE / budgets / kill switch / elastic spawn.

## CLI look

<img alt="Enhanced Harness CLI session visual" src="visuals/enhanced-harness-cli-visual.png" />

Live snapshot from this workspace: [`visuals/harness-cli-live.html`](visuals/harness-cli-live.html)

```bash
harness setup
harness doctor --scope scope.json
harness start --scope scope.json
harness logs --follow
harness report --out harness-out/<session>/
```

Evidence package (files, not a web UI):

- `findings.md` / `findings.json` — confirmed first; suspected marked UNVERIFIED
- `transcript.jsonl` — observe / plan / act / oracle / spawn
- `coverage.json` — never claims “secure”
- `harness.log`

## Lab targets

### Local vulnerable AI chat page

```bash
harness lab-page   # http://127.0.0.1:8766/
```

### OWASP FinBot CTF (Juice Shop for Agentic AI)

<img alt="OWASP FinBot CTF home" src="visuals/finbot-home.png" />

<img alt="OWASP FinBot portals" src="visuals/finbot-portals.png" />

```bash
./scripts/lab_finbot_up.sh     # http://127.0.0.1:8000/
./scripts/lab_finbot_down.sh
```

Lab notes (fair use, no spoilers): [`FINBOT_LAB.md`](FINBOT_LAB.md).
