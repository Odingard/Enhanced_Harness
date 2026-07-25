# Enhanced Harness

**Odingard Security** — Shannon-class autonomous multi-agent red team for
**Agentic AI / MCP / model-hub / AI cloud supply chain**.

> Shannon (Keygraph) = autonomous terminal multi-agent red team for web apps/APIs  
> **Enhanced Harness** = the same job for Agentic AI and MCP surfaces

This repository is **not** ARGUS and **not** ALEC. Related Odingard products may
be mentioned only as adjacent tools — they are not this CLI, package, or brand.

## Status

**Seed charter.** The full autonomous build prompt lives in
[`DOWNLOAD_THIS_PROMPT.md`](DOWNLOAD_THIS_PROMPT.md). Hand-off steps:
[`HANDOFF_TO_GIT.md`](HANDOFF_TO_GIT.md). Builder instructions:
[`AGENTS.md`](AGENTS.md).

Milestone 1 (runnable multi-agent path + ≥1 oracle-confirmed finding) has not
been implemented yet — start from the download prompt.

## Product (V1 intent)

Enhanced Harness is a full V1 multi-agent red team for authorized Agentic AI,
MCP, model-hub supply chain, cloud/IAM, poisoning, infra, OSINT, and
control-validation engagements. Scout maps surfaces; Strategist
drives/dives/steers; Strike agents spawn in parallel on signal; Verifier
confirms only with oracle proof. Dangerous packs are ROE flag-gated and
sandboxed — included, not omitted. Suspected items are labeled unverified. It
does not certify that a system is secure.

## Planned operator path (after Milestone 1)

```bash
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/harness setup
.venv/bin/harness doctor --scope scope.json
.venv/bin/harness start --scope scope.json
.venv/bin/harness logs --follow
.venv/bin/harness report --out harness-out/<session>/
```

CLI command: `harness` · Python package: `enhanced_harness`

## Boundaries

- Terminal-first CLI only in v1 (no web UI / dashboard).
- Optional Playwright Agent Chat UI is Phase B, default OFF — allowlisted chat
  box only; not a generic web XSS/SQLi pack.
- Lab target https://owasp-finbot-ctf.org/ may be used for fair live testing
  only. Do not encode FinBot challenges, flags, detectors, or walkthroughs.
- Confirmed findings require oracle proof; only the Verifier agent may set
  `confirmed`.

## License

TBD by Odingard Security.
