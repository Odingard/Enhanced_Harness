# DOWNLOAD THIS — Enhanced Harness Build Prompt

**Odingard Security**  
**Repo to build in:** https://github.com/Odingard/Enhanced_Harness  
**Product:** Enhanced Harness (Shannon-class AI/MCP red team)  
**Not:** ARGUS · ALEC · a web pentester

When you are at a computer: copy everything inside the text block below into
Devin, Codex, or a Cloud Agent whose environment is Enhanced_Harness only.

Also see [HANDOFF_TO_GIT.md](HANDOFF_TO_GIT.md) for pushing this seed to GitHub.  
Lab target https://owasp-finbot-ctf.org/ is for fair live testing only — no CTF mapping/spoiling.

---

```text
# Enhanced Harness — Autonomous AI Red Team for Agentic AI and MCPs
# Odingard Security | Repo: Odingard/Enhanced_Harness | Shannon-class | REAL only

###############################################################################
# IDENTITY
###############################################################################
You are building Enhanced Harness in THIS repository only:
  https://github.com/Odingard/Enhanced_Harness

Product name: Enhanced Harness
CLI command: harness
Python package: enhanced_harness

This product is NOT ARGUS and NOT ALEC.
Do not use ARGUS or ALEC names for CLI, package, paths, env vars, or branding
(except a short "related products" note in README).

Shannon analogy (keep this exact framing):
  Shannon (Keygraph)  = autonomous terminal MULTI-AGENT red team for web apps/APIs
  Enhanced Harness    = same job for Agentic AI / MCP / model-hub / AI cloud-supply chain
                        (also MULTI-AGENT)

V1 INCLUDES EVERYTHING in CAPABILITIES.md — nothing deferred to a later product phase.
Dangerous packs are flag-gated (allow_model_hub, allow_cloud, allow_infra, etc.) and
sandboxed where needed — gated ≠ left out.

Proof-by-exploitation. Terminal-first. MULTI-AGENT. ELASTIC SPAWN. FULL V1 MAP.

###############################################################################
# WHAT YOU WILL BUILD (complete inventory)
###############################################################################

## A) Shannon-class terminal CLI
harness setup
harness doctor --scope scope.json
harness start  --scope scope.json [--out DIR]     # alias: harness engage
harness logs   [--out DIR] [--follow]
harness resume --out DIR
harness report --out DIR
harness modules
harness version

Operator happy path (document in README):
  python -m venv .venv && .venv/bin/pip install -e ".[dev]"
  .venv/bin/harness setup
  .venv/bin/harness doctor --scope scope.json
  .venv/bin/harness start --scope scope.json
  .venv/bin/harness logs --follow
  .venv/bin/harness report --out harness-out/<session>/

## B) MULTI-AGENT system with ELASTIC SPAWN (mandatory)
Implement these agents as real concurrent actors (asyncio OK). See MULTIAGENT.md.

  Conductor   — session, ROE, budgets, kill switch, SPAWN/RETIRE workers, stop
  Scout       — observe MCP + LLM surfaces; re-spawnable for refresh
  Strategist  — hypotheses + Drive/Dive/Steer + spawn_requests
  Strike-*    — ELASTIC workers; spawned on findings; CANNOT set confirmed
  Verifier    — oracles O1–O5; ONLY agent that may set confirmed
  Scribe      — transcript (incl. spawn events), findings, coverage, report

Navigation:
  Scout → Strategist → Strike workers → Verifier → Scribe
  Verifier/Scout signals → Strategist → Conductor SPAWNS more Strikes in PARALLEL

Elastic spawn (mandatory):
  Baseline: min_parallel_strikes (default 2)
  On signal/suspected/confirmed/new surface:
    spawn up to max_spawn_per_signal (default 3) NEW Strike agents
    they run IN PARALLEL with existing Drive Strikes (Dive does not freeze Drive)
  Hard ceiling: max_parallel_strikes (default 8)
  Also: max_scout_instances (default 2)
  Refuse spawn if over cap, over budget, kill switch, or ROE/allowlist fail
  Log every spawn/retire to transcript

Drive / Dive / Steer (owned by Strategist):
  DRIVE  — breadth; spawn toward coverage holes up to max
  DIVE   — spawn Dive Strikes on hot chain in parallel; keep Drive if budget allows
  STEER  — retire barren; spawn replacements; optional Scout respawn

Stop only on: budget | kill_switch | no hypotheses left |
              optional stop_on_first_confirmed

## C) Target adapters (REAL — no stubs; full V1 surfaces)
1) MCP client via official Python `mcp` SDK (pin mcp>=1.x,<2 until v2 stable)
   - list/call tools, read resources, get prompts
   - transports: stdio + streamable HTTP/SSE
2) LLM / Agentic app HTTP adapter
   - chat + tool-calling multi-turn loops (may call MCP)
3) Model hub adapter (HF/repos) — for M16 hub.* skills
4) Cloud adapter (AWS/GCP/Azure AI hosting) — for M19
5) Infra adapter (k8s/serverless lab targets) — for M21
6) RAG/pipeline adapter — for M17/M20

Optional UI (default OFF):
7) Agent Chat UI (Playwright) — allowlisted chat box only
   NOT a Shannon-style generic web XSS/SQLi pack

## D) Attack modules — FULL V1 SET (implement all M01–M22)
M01 tool_enumeration_abuse
M02 tool_coercion
M03 prompt_injection_direct
M04 prompt_injection_indirect
M05 argument_injection
M06 authz_bypass_tools
M07 authz_bypass_resources
M08 secret_exfiltration
M09 confused_deputy
M10 sampling_prompt_leak
M11 schema_rugpull
M12 tool_result_injection
M13 resource_poisoning
M14 prompt_tool_chaining
M15 denial_of_wallet_bounded      # allow_dow_probe
M16 model_hub_supply_chain        # allow_model_hub + sandbox for RCE
M17 taint_rag_propagation
M18 ai_tprm_osint                 # allow_osint for noisy OSINT
M19 cloud_iam_exploitation        # allow_cloud
M20 data_model_poisoning          # allow_poison
M21 container_serverless_breakout # allow_infra + lab
M22 evasion_telemetry             # allow_evasion for noisy evasion
Plus CLI: harness retest (remediation validation)

Module contract (every module):
  id, name, surfaces (mcp|llm|hub|cloud|infra|rag|web as needed)
  enumerate_hypotheses(obs, scope) -> list[Hypothesis]
  execute(hyp, ctx) -> ProbeResult
  oracle_spec(hyp) -> OracleSpec

V1 is incomplete if any CAPABILITIES.md row lacks module/skills/oracles.
Flag-gated ≠ left out.

## E) Skills registry (granular techniques — mandatory)
See SKILLS.md + skills/registry.yaml.
Capability map (v1 vs roadmap): CAPABILITIES.md — do NOT implement phase-2/3 as if shipped.

Modules = attack class. Skills = how Strike executes.
Strike selects skills from registry (applicability score).
Dive spawn pins DIFFERENT skills in parallel on the same module signal.
Every act/finding records skill_id.

M1 minimum: implement registry loader + ≥3 skills for M08:
  exfil.canary_direct_ask
  exfil.canary_tool_arg_smuggle
  exfil.encoding_base64

Skills never set confirmed. Flag-gated skills honor requires_flags.
hub.* and all CAPABILITIES.md packs are V1. Implement all skill families in registry.
Flag-gate dangerous ones; require sandbox for serialize/loader RCE and infra breakouts.
Milestone order sequences build — it does NOT shrink V1 scope.

## F) Oracles (authoritative truth — planner LLM never confirms)
O1 canary_match
O2 side_effect_marker
O3 authz_differential
O4 policy_break_log
O5 transcript_proof

Finding status only:
  confirmed  = oracle passed (required for client-facing "we found X")
  suspected  = signal, no proof (label UNVERIFIED)
  refuted    = tested, failed

## G) Evidence package (per session DIR)
scope.used.json
transcript.jsonl          # every observe/act/oracle/adapt
checkpoint.json
findings.json
findings.md               # confirmed first; suspected marked UNVERIFIED
coverage.json             # secure_claim_allowed MUST be false always
harness.log

## H) Scope / safety (fail closed)
scope.json must support:
  engagement, roe(authorized+client_name), targets.mcp[], targets.llm_apps[],
  allowlist, budgets{max_minutes,max_requests,max_tool_calls,max_tokens,
  anomaly_tool_calls,dive_tool_call_fraction},
  flags{allow_destructive,allow_dow_probe,stop_on_first_confirmed,
  enable_agent_chat_ui},
  canaries[], oracle_hooks, planner, kill_switch_path, modules_enabled[]

Rules:
- refuse start if roe.authorized != true or allowlist/budgets missing
- allowlist every host/command/call
- destructive + DoW default false
- redact canary values from findings.md; store proof hash in findings.json
- kill switch file aborts loop

## I) Repo layout
enhanced_harness/
  cli.py, scope.py, config.py, checkpoint.py, budgets.py, safety.py
  agents/
    conductor.py, scout.py, strategist.py, strike.py,
    verifier.py, scribe.py, bus.py
  adapters/         # mcp_client.py, llm_app.py (, agent_chat_ui.py Phase B)
  modules/          # M01–M15
  skills/           # runtime Skill implementations matching registry IDs
  oracles/          # O1–O5
  evidence/
skills/                 # registry.yaml + human skill docs
  registry.yaml
scripts/
  run_acceptance.sh
  check_no_stubs.sh
tests/
  fixtures/mcp/
  fixtures/llm_app/
pyproject.toml
README.md
ENHANCED_HARNESS_SPEC.md
MULTIAGENT.md
DOWNLOAD_THIS_PROMPT.md
MASTER_PROMPT.md
DEVIN_MILESTONES.md
MODULE_CATALOG.md
OPERATOR_RUNBOOK.md
scope.example.json
AGENTS.md

## J) Tech
Python 3.12, asyncio, official mcp SDK, httpx, pydantic v2, typer, rich(optional),
pytest + pytest-asyncio. Prefer small real modules over framework sprawl.

###############################################################################
# NON-NEGOTIABLES (client protection)
###############################################################################
1. REAL only — no NotImplemented adapters pretending to work; no fake findings
2. confirmed = oracle proof only — and ONLY Verifier may set confirmed
3. Multi-agent is mandatory (Conductor/Scout/Strategist/Strike/Verifier/Scribe)
4. Never claim target is "secure"; coverage must list what was not tested
5. CLI only in v1 — no web UI / dashboard
6. Fail closed on ROE / allowlist / budgets
7. Fixtures under tests/ only — zero fixture data in shippable wheel
8. Live tests gated: HARNESS_LIVE=1 + marker `live`
9. Do not implement ALEC seal/TSA here
10. Do not brand this as ARGUS

###############################################################################
# BUILD ORDER (one milestone at a time)
###############################################################################

### Milestone 1 — prove REAL multi-agent path (do this first; stop when done)
1) harness CLI: setup, doctor, start, logs, report, modules
2) Scope validation + safety fail-closed
3) All 6 agents exist and run end-to-end:
   Conductor, Scout, Strategist, Strike, Verifier, Scribe
   (Strike pool size may be 1 in M1)
4) MCP stdio adapter + LLM HTTP adapter (against fixtures)
5) skills/registry.yaml loader + ≥3 M08 skills (direct_ask, tool_arg_smuggle, encoding)
6) Oracle O1 canary_match on Verifier only
7) Module M08 on Strike via skills (not a monolith)
8) Path Scout→Strategist→Strike→Verifier→Scribe yields ≥1 CONFIRMED
9) Local vulnerable MCP + LLM fixtures that leak canary
10) scripts/run_acceptance.sh → ≥1 CONFIRMED finding
11) scripts/check_no_stubs.sh
12) README happy path + multi-agent + skills description
Do NOT build Playwright chat UI yet (optional). Do NOT brand as ALEC/ARGUS.
Other modules/skills come in M3–M4 — but V1 definition includes them all.
pytest -m "not live" green.

### Milestone 2 — elastic spawn + Drive / Dive / Steer for real
On signal, Conductor spawns ≤ max_spawn_per_signal new Strikes in parallel
while Drive continues. Respect max_parallel_strikes + shared budget ledger.
Strategist Drive/Dive/Steer real; spawn_requests wired; resume restores state.
Tests: live_strikes increases on signal; Dive or Steer occurs.
No new modules. No browser.

### Milestone 3 — Core modules
M02, M03, M04, M05, M06, M07, M09 + oracles O2–O4 as needed.
Fixtures prove ≥ M02 and M03 can CONFIRMED.

### Milestone 4 — Complete module set + honesty
M01, M10–M15 (M15 gated), O5 transcript_proof, coverage skip disclosure,
README promises/non-promises + browser boundary.

### Milestone 5 — optional Phase B
Playwright Agent Chat UI adapter only (allowlisted chat). Default OFF.
Hard-ban classic web vuln packs.

###############################################################################
# ACCEPTANCE (product done only if all true)
###############################################################################
1) harness setup/doctor/start/logs/report/modules work
2) run_acceptance.sh → ≥1 CONFIRMED with oracle proof + full artifacts
3) All six agents present; only Verifier sets confirmed
4) Elastic spawn on signal (after M2) + Dive or Steer proven in tests/transcript
5) Budget stop → honest coverage, never "secure"
6) check_no_stubs.sh passes
7) pytest -m "not live" green
8) README states Shannon analogy, multi-agent roster, browser boundary
9) CAPABILITIES.md fully covered (M01–M22 + retest + all registry skills)
10) No ARGUS product branding in CLI/package

###############################################################################
# CLIENT LANGUAGE (use in README)
###############################################################################
Enhanced Harness is a full V1 multi-agent red team for authorized Agentic AI, MCP,
model-hub supply chain, cloud/IAM, poisoning, infra, OSINT, and control-validation
engagements. Scout maps surfaces; Strategist drives/dives/steers; Strike agents
spawn in parallel on signal; Verifier confirms only with oracle proof. Dangerous
packs are ROE flag-gated and sandboxed — included, not omitted. Suspected items
are labeled unverified. It does not certify that a system is secure.

Lab target OWASP FinBot CTF may be used for fair live testing only.
Do NOT encode FinBot challenges, flags, detectors, or walkthroughs.

START AT MILESTONE 1. Deliver a runnable REAL multi-agent harness, not a design doc.
```

---

## After you paste

1. Confirm the agent’s repo is `Odingard/Enhanced_Harness` (not ALEC).
2. Let it finish Milestone 1 before Milestone 2.
3. Gate: `scripts/run_acceptance.sh` must produce ≥1 confirmed finding.
