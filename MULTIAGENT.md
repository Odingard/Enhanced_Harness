# Multi-agent roster — Enhanced Harness

Enhanced Harness is a **real concurrent multi-agent** system (asyncio actors),
not a single-prompt chain branded as agents.

## Roster

| Agent | Role |
|-------|------|
| **Conductor** | Session lifecycle, ROE/allowlist/budgets, kill switch, SPAWN/RETIRE workers, stop conditions |
| **Scout** | Observe MCP + LLM surfaces; re-spawnable for refresh |
| **Strategist** | Hypotheses + Drive / Dive / Steer + `spawn_requests` |
| **Strike-*** | Elastic workers; execute module skills; **cannot** set `confirmed` |
| **Verifier** | Oracles O1–O5; **only** agent that may set `confirmed` |
| **Scribe** | Transcript (incl. spawn events), findings, coverage, report |

## Navigation

```
Scout → Strategist → Strike workers → Verifier → Scribe
Verifier/Scout signals → Strategist → Conductor SPAWNS more Strikes in PARALLEL
```

## Elastic spawn (Milestone 2 completes full behavior)

- Baseline: `min_parallel_strikes` (default 2; M1 may use 1)
- On signal: spawn up to `max_spawn_per_signal` new Strike agents in parallel
- Hard ceiling: `max_parallel_strikes`
- Refuse spawn if over cap, over budget, kill switch, or ROE/allowlist fail
- Every spawn/retire is logged to `transcript.jsonl`

## Drive / Dive / Steer

- **DRIVE** — breadth; cover skill/surface holes
- **DIVE** — focus parallel Strikes on a hot chain (does not freeze Drive)
- **STEER** — retire barren workers; spawn replacements; optional Scout respawn

## Stop conditions

Budget exhausted · kill switch · no hypotheses left · optional `stop_on_first_confirmed`
