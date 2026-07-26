# Competitive landscape — what makes Enhanced Harness supreme

Source surveyed: [scadastrangelove/awesome-ai-security-tools](https://github.com/scadastrangelove/awesome-ai-security-tools)
(snapshot referenced in that repo: 2026-07-23).

This note maps the awesome-list categories onto Enhanced Harness V1 intent and
calls out **gaps to close** after Milestone 1 so the product stays Shannon-class
for Agentic AI / MCP — not a generic web pentester and not a prompt-only scanner.

## Where Enhanced Harness already aims higher

Most tools in the list are **one of**:

1. **Static scanners** for MCP/skills/agents (SkillSpector, Ramparts, mcp-scanner,
   agent-scan, aguara, mcp-armor, AgentShield, …)
2. **LLM red-team scanners / eval harnesses** (garak, PyRIT, promptfoo, DeepTeam,
   Augustus, HackAgent, …)
3. **Runtime proxies / guardrails** (ToolHive, Pipelock, mcp-context-protector,
   MCP Gateway, Parallax, …)
4. **Generic autonomous pentest agents** for web/AD/infra (Shannon, PentAGI,
   Strix, PentestGPT, HexStrike, …)
5. **Model supply-chain scanners** (modelscan, Fickling, picklescan, GuardDog, …)

Enhanced Harness V1 is different by design:

| Differentiator | Why it matters |
|----------------|----------------|
| Multi-agent roster with elastic Strike spawn | Matches Shannon-style orchestration, not a single probe loop |
| Proof-by-exploitation + oracle confirmation | Client-facing `confirmed` only with O1–O5 proof (Verifier-only) |
| MCP + agentic LLM adapters as first-class targets | Attacks the tool/runtime plane, not just chat prompts |
| Skills registry under modules | Parallel Dive can pin distinct techniques on one signal |
| Fail-closed ROE / allowlist / budgets / kill switch | Engagement-safe for authorized work |
| Honest coverage (`secure_claim_allowed: false`) | Never certifies “secure” |

M1 ships the runnable spine: Conductor/Scout/Strategist/Strike/Verifier/Scribe,
MCP stdio + LLM HTTP adapters, M08 via ≥3 skills, O1 canary oracle, evidence pack.

## Priority upgrades to become supreme

Ordered for product leverage (absorb patterns — do not vendor-lock or rebrand).

### P0 — must land in V1 (already on roadmap M2–M5 / CAPABILITIES)

1. **Elastic Drive/Dive/Steer for real (M2)**  
   Learn from multi-agent pentest swarms (PentAGI, Pentest-Swarm-AI, T3MP3ST):
   live strike counts must rise on signal; Dive must not freeze Drive; resume
   must restore spawn state.

2. **Full MCP attack surface modules (M3–M4)**  
   Align module coverage with threats that static MCP scanners only *detect*:
   tool coercion, prompt injection (direct/indirect), argument injection,
   authz bypass (tools/resources), confused deputy, schema rug-pull, tool-result
   injection, resource poisoning, prompt-tool chaining.  
   Reference checklists: SlowMist MCP-Security-Checklist, OWASP-ish MCP Top 10
   mappings used by Ramparts / skilltotal.

3. **Oracle depth O2–O5**  
   Static scanners stop at “suspicious description.” Supreme requires
   side-effect markers, authz differentials, policy-break logs, transcript proof.

### P1 — absorb best techniques from the awesome list

4. **Static pre-scout pass (optional module / Scout enricher)**  
   Before dynamic Strike, optionally ingest findings from OSS MCP/skill scanners
   as *hypotheses* (never as confirmed):
   - [Cisco mcp-scanner](https://github.com/cisco-ai-defense/mcp-scanner)
   - [Snyk agent-scan](https://github.com/snyk/agent-scan)
   - [NVIDIA SkillSpector](https://github.com/NVIDIA/SkillSpector)
   - [Ramparts](https://github.com/highflame-ai/ramparts)
   - [mcp-armor](https://github.com/aira-security/mcp-armor)
   - [aguara](https://github.com/garagon/aguara)  
   Pattern: scanner JSON → Strategist hypotheses → dynamic oracle proof.

5. **LLM attack plugin depth (feed skills, don’t become garak)**  
   Borrow probe families from [garak](https://github.com/NVIDIA/garak),
   [PyRIT](https://github.com/microsoft/PyRIT),
   [promptfoo](https://github.com/promptfoo/promptfoo),
   [HackAgent](https://github.com/AISecurityLab/hackagent) as **skill packs**
   under M03/M04/M08/M10 — always ending in Verifier oracles, not LLM-as-judge
   alone.

6. **Model-hub supply chain (M16)**  
   Wire sandboxed use of [modelscan](https://github.com/protectai/modelscan) /
   [Fickling](https://github.com/trailofbits/fickling) /
   [picklescan](https://github.com/mmaitre314/picklescan) behind
   `allow_model_hub` + sandbox. Supreme = exploit/prove unsafe deserialize paths,
   not only lint pickles.

7. **Agent threat rules interchange**  
   Emit/consume [ATR – Agent Threat Rules](https://github.com/panguard-ai/agent-threat-rules)
   (“Sigma for agents”) and SARIF so harness findings plug into SOC/autotriage
   tools (seclab-taskflow-agent, nuclei-autotriage patterns).

### P2 — platform edges (flag-gated)

8. **Cloud / IAM / infra packs (M19/M21)** — keep ROE-gated; study how
   defenseclaw / ToolHive / microsandbox isolate agent tool runtime and invert
   those controls as attack hypotheses for lab breakout modules.

9. **RAG / poisoning / taint (M17/M20)** — few awesome-list tools do
   end-to-end taint through tool→model→tool; this is a white-space win.

10. **Evasion / telemetry (M22) + DoW (M15)** — noisy; flag-gated; almost
    absent as *authorized engagement modules* in the list.

## Explicit non-goals (stay sharp)

- Do **not** become Shannon/Strix/PentAGI for generic web XSS/SQLi.
- Do **not** ship a dashboard (CLI-first).
- Do **not** treat LLM-as-judge as confirmation.
- Do **not** encode FinBot CTF solutions.
- Do **not** brand as ARGUS/ALEC.

## Scoreboard (honest)

| Capability | Awesome-list leaders | Harness M1 | Harness V1 target |
|------------|----------------------|------------|-------------------|
| MCP static scan | SkillSpector, mcp-scanner, Ramparts | — | Optional Scout enricher |
| LLM prompt probes | garak, PyRIT, promptfoo | M08 skills only | M03/M04/M10 skill packs |
| Multi-agent elastic spawn | PentAGI, T3MP3ST, Shannon (web) | Baseline spawn | Full Drive/Dive/Steer |
| Oracle-confirmed exploit proof | Rare outside custom harnesses | O1 + M08 | O1–O5 + M01–M22 |
| Model supply chain | modelscan/Fickling | — | M16 sandboxed |
| Fail-closed ROE engagement | Sparse | Yes | Yes |
| Agentic AI / MCP focus | Fragmented | Yes | Yes |

## Recommended next moves after M1 acceptance

1. Land **Milestone 2** elastic spawn tests (live_strikes increases on signal).
2. Add Scout **static enricher** adapter (mcp-scanner / agent-scan JSON in).
3. Expand skills from garak/PyRIT plugin inventories into registry.yaml
   (flag-gated where needed).
4. Implement M16 hub skills with modelscan/Fickling behind sandbox.
5. Add ATR/SARIF export on Scribe reports for autotriage interoperability.
