# AGENTS.md — builder instructions for Enhanced Harness

## Repository identity

- **Repo:** https://github.com/Odingard/Enhanced_Harness
- **Product:** Enhanced Harness
- **CLI:** `harness`
- **Package:** `enhanced_harness`
- **Not:** ARGUS · ALEC · generic web pentester

If the workspace is any other repository, stop and switch to
`Odingard/Enhanced_Harness`.

## Source of truth for the build

1. Read [`DOWNLOAD_THIS_PROMPT.md`](DOWNLOAD_THIS_PROMPT.md) in full.
2. Copy the fenced build prompt into your session (or follow it in place).
3. Follow [`HANDOFF_TO_GIT.md`](HANDOFF_TO_GIT.md) for git/push workflow notes.

## Build rules

- Start at **Milestone 1**. Do not begin Milestone 2 until M1 acceptance passes.
- Deliver a runnable REAL multi-agent harness, not a design doc.
- Multi-agent roster is mandatory: Conductor, Scout, Strategist, Strike,
  Verifier, Scribe.
- Only **Verifier** may set finding status `confirmed` (oracle proof required).
- Fail closed on ROE / allowlist / budgets.
- No ARGUS or ALEC branding in CLI, package, paths, or env vars.
- Do not encode OWASP FinBot CTF challenges, flags, detectors, or walkthroughs.

## Milestone 1 gate

`scripts/run_acceptance.sh` must produce ≥1 **CONFIRMED** finding with oracle
proof and a full evidence package under the session output directory.
