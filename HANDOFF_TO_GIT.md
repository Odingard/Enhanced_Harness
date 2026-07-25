# Handoff — push Enhanced Harness seed to GitHub

**Repo:** https://github.com/Odingard/Enhanced_Harness  
**Product:** Enhanced Harness (not ARGUS, not ALEC)

## What this seed is

`DOWNLOAD_THIS_PROMPT.md` is the autonomous build prompt for Devin, Codex, or a
Cursor Cloud Agent whose workspace is **this repository only**.

## Push the seed (this PR / commit)

1. Confirm remote is `Odingard/Enhanced_Harness`.
2. Commit at least:
   - `DOWNLOAD_THIS_PROMPT.md`
   - `HANDOFF_TO_GIT.md`
   - `README.md`
   - `AGENTS.md`
3. Push the branch and open a PR into `main` (or land directly on `main` if that
   is the agreed workflow for an empty seed repo).

## Next: build Milestone 1

After the seed is on GitHub:

1. Start a Cloud Agent / Devin / Codex with **only** this repo checked out.
2. Paste the fenced build prompt from `DOWNLOAD_THIS_PROMPT.md`.
3. Stop when Milestone 1 acceptance gates pass:
   - `scripts/run_acceptance.sh` → ≥1 **CONFIRMED** finding
   - `scripts/check_no_stubs.sh` passes
   - `pytest -m "not live"` green
4. Do **not** start Milestone 2 until Milestone 1 is done.

## Safety reminders

- Lab target https://owasp-finbot-ctf.org/ is for fair live testing only.
- Do not encode FinBot challenges, flags, detectors, or walkthroughs.
- Fail closed on ROE / allowlist / budgets.
- Never brand this product as ARGUS or ALEC.
