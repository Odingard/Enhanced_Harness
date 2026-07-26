#!/usr/bin/env bash
# Milestone 1 acceptance: ≥1 CONFIRMED finding with oracle proof + full evidence package.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
fi

export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
export HARNESS_FIXTURE_CANARY_ID="CANARY_SECRET_A"
export HARNESS_FIXTURE_CANARY_VALUE="HARNESS_CANARY_EXFIL_OK_42"
export HARNESS_LLM_HOST="127.0.0.1"
export HARNESS_LLM_PORT="8765"

OUT_ROOT="$ROOT/harness-out"
SESSION_DIR="$OUT_ROOT/acceptance-$(date -u +%Y%m%dT%H%M%SZ)"
SCOPE_FILE="$SESSION_DIR/scope.json"
mkdir -p "$SESSION_DIR"

# Start vulnerable LLM fixture
LLM_LOG="$SESSION_DIR/llm_fixture.log"
$PYTHON -m tests.fixtures.llm_app.server >"$LLM_LOG" 2>&1 &
LLM_PID=$!
cleanup() {
  if kill -0 "$LLM_PID" 2>/dev/null; then
    kill "$LLM_PID" 2>/dev/null || true
    wait "$LLM_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

# Wait for health
for i in $(seq 1 40); do
  if $PYTHON - <<PY
import sys, httpx
try:
    r = httpx.get("http://127.0.0.1:8765/health", timeout=0.5)
    sys.exit(0 if r.status_code == 200 else 1)
except Exception:
    sys.exit(1)
PY
  then
    break
  fi
  sleep 0.25
  if [[ "$i" -eq 40 ]]; then
    echo "LLM fixture failed to start; log:" >&2
    cat "$LLM_LOG" >&2 || true
    exit 1
  fi
done

# Build acceptance scope (MCP stdio fixture + LLM HTTP fixture)
$PYTHON - <<PY
import json
from pathlib import Path

scope = {
  "engagement": {"name": "m1-acceptance", "client_name": "Odingard Lab"},
  "roe": {"authorized": True, "client_name": "Odingard Lab"},
  "targets": {
    "mcp": [{
      "name": "lab-mcp",
      "transport": "stdio",
      "command": ["$PYTHON", "-m", "tests.fixtures.mcp.vulnerable_server"],
      "cwd": "$ROOT",
      "env": {
        "HARNESS_FIXTURE_CANARY_ID": "$HARNESS_FIXTURE_CANARY_ID",
        "HARNESS_FIXTURE_CANARY_VALUE": "$HARNESS_FIXTURE_CANARY_VALUE",
      },
    }],
    "llm_apps": [{
      "name": "lab-llm",
      "base_url": "http://127.0.0.1:8765",
      "chat_path": "/v1/chat",
    }],
  },
  "allowlist": {
    "hosts": ["127.0.0.1", "localhost"],
    "commands": ["python", "python3", Path("$PYTHON").name],
    "tool_names": ["*"],
  },
  "budgets": {
    "max_minutes": 5,
    "max_requests": 100,
    "max_tool_calls": 50,
    "max_tokens": 50000,
    "anomaly_tool_calls": 40,
    "dive_tool_call_fraction": 0.4,
  },
  "flags": {
    "allow_destructive": False,
    "allow_dow_probe": False,
    "stop_on_first_confirmed": True,
    "enable_agent_chat_ui": False,
  },
  "canaries": [{
    "id": "$HARNESS_FIXTURE_CANARY_ID",
    "value": "$HARNESS_FIXTURE_CANARY_VALUE",
    "kind": "secret",
  }],
  "oracle_hooks": {},
  "planner": {
    "min_parallel_strikes": 1,
    "max_parallel_strikes": 4,
    "max_spawn_per_signal": 2,
    "max_scout_instances": 1,
  },
  "kill_switch_path": "$SESSION_DIR/KILL",
  "modules_enabled": ["M08"],
}
Path("$SCOPE_FILE").write_text(json.dumps(scope, indent=2) + "\n")
print("$SCOPE_FILE")
PY

echo "== harness doctor =="
$PYTHON -m enhanced_harness.cli doctor --scope "$SCOPE_FILE"

echo "== harness start =="
$PYTHON -m enhanced_harness.cli start --scope "$SCOPE_FILE" --out "$SESSION_DIR"

echo "== acceptance checks =="
$PYTHON - <<PY
import json
import sys
from pathlib import Path

session = Path("$SESSION_DIR")
required = [
    "scope.used.json",
    "transcript.jsonl",
    "checkpoint.json",
    "findings.json",
    "findings.md",
    "coverage.json",
    "harness.log",
]
missing = [r for r in required if not (session / r).exists()]
if missing:
    print("MISSING artifacts:", missing, file=sys.stderr)
    sys.exit(1)

findings = json.loads((session / "findings.json").read_text())
confirmed = [f for f in findings if f.get("status") == "confirmed"]
if not confirmed:
    print("FAIL: expected ≥1 CONFIRMED finding", file=sys.stderr)
    print(json.dumps(findings, indent=2), file=sys.stderr)
    sys.exit(1)

for f in confirmed:
    if not f.get("proof_hash"):
        print("FAIL: confirmed finding missing proof_hash", f, file=sys.stderr)
        sys.exit(1)
    if f.get("oracle_id") != "O1":
        print("FAIL: expected O1 oracle on confirmed finding", f, file=sys.stderr)
        sys.exit(1)

coverage = json.loads((session / "coverage.json").read_text())
if coverage.get("secure_claim_allowed") is not False:
    print("FAIL: secure_claim_allowed must be false", file=sys.stderr)
    sys.exit(1)

# Ensure canary value redacted from markdown
md = (session / "findings.md").read_text()
if "$HARNESS_FIXTURE_CANARY_VALUE" in md:
    print("FAIL: canary value leaked into findings.md", file=sys.stderr)
    sys.exit(1)

# Multi-agent path present in transcript
text = (session / "transcript.jsonl").read_text()
for kind in ("observe", "plan", "act", "oracle"):
    if f'"kind": "{kind}"' not in text and f'"kind":"{kind}"' not in text:
        # also accept without space
        if kind not in text:
            print(f"FAIL: transcript missing {kind} events", file=sys.stderr)
            sys.exit(1)

print("ACCEPTANCE PASS")
print(f"session: {session}")
print(f"confirmed: {len(confirmed)}")
for f in confirmed:
    print(f"  - {f['id']} skill={f['skill_id']} proof={f['proof_hash'][:16]}...")
PY
