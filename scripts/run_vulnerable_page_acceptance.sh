#!/usr/bin/env bash
# Acceptance against the local vulnerable AI chat PAGE fixture (Playwright).
# Proves Scout→Strategist→Strike→Verifier→Scribe yields ≥1 CONFIRMED on web UI.
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
export HARNESS_CHAT_HOST="127.0.0.1"
export HARNESS_CHAT_PORT="8766"

OUT_ROOT="$ROOT/harness-out"
SESSION_DIR="$OUT_ROOT/chat-page-acceptance-$(date -u +%Y%m%dT%H%M%SZ)"
SCOPE_FILE="$SESSION_DIR/scope.json"
mkdir -p "$SESSION_DIR"

# Ensure Playwright chromium is available
$PYTHON - <<'PY'
import sys
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("FAIL: playwright missing. Install with: pip install -e '.[lab]'", file=sys.stderr)
    sys.exit(1)
print("playwright import OK")
PY

if ! $PYTHON -c "from playwright.sync_api import sync_playwright; sync_playwright().start().chromium.launch(headless=True).close()" 2>/dev/null; then
  echo "== installing Playwright chromium =="
  $PYTHON -m playwright install chromium
fi

PAGE_LOG="$SESSION_DIR/chat_page.log"
$PYTHON -m tests.fixtures.vulnerable_ai_page.server >"$PAGE_LOG" 2>&1 &
PAGE_PID=$!
cleanup() {
  if kill -0 "$PAGE_PID" 2>/dev/null; then
    kill "$PAGE_PID" 2>/dev/null || true
    wait "$PAGE_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

for i in $(seq 1 40); do
  if $PYTHON - <<PY
import sys, httpx
try:
    r = httpx.get("http://127.0.0.1:8766/health", timeout=0.5)
    sys.exit(0 if r.status_code == 200 else 1)
except Exception:
    sys.exit(1)
PY
  then
    break
  fi
  sleep 0.25
  if [[ "$i" -eq 40 ]]; then
    echo "Chat page fixture failed to start; log:" >&2
    cat "$PAGE_LOG" >&2 || true
    exit 1
  fi
done

$PYTHON - <<PY
import json
from pathlib import Path
scope = {
  "engagement": {"name": "chat-page-acceptance", "client_name": "Odingard Lab"},
  "roe": {"authorized": True, "client_name": "Odingard Lab"},
  "targets": {
    "mcp": [],
    "llm_apps": [],
    "agent_chat_ui": [{
      "name": "lab-chat-page",
      "url": "http://127.0.0.1:8766/",
      "input_selector": "#chat-input",
      "send_selector": "#send-btn",
      "messages_selector": "#messages",
    }],
  },
  "allowlist": {
    "hosts": ["127.0.0.1", "localhost"],
    "commands": ["python", "python3"],
    "tool_names": ["*"],
  },
  "budgets": {
    "max_minutes": 5,
    "max_requests": 40,
    "max_tool_calls": 40,
    "max_tokens": 20000,
    "anomaly_tool_calls": 20,
    "dive_tool_call_fraction": 0.4,
  },
  "flags": {
    "allow_destructive": False,
    "allow_dow_probe": False,
    "stop_on_first_confirmed": True,
    "enable_agent_chat_ui": True,
  },
  "canaries": [{
    "id": "$HARNESS_FIXTURE_CANARY_ID",
    "value": "$HARNESS_FIXTURE_CANARY_VALUE",
    "kind": "secret",
  }],
  "oracle_hooks": {},
  "planner": {
    "min_parallel_strikes": 1,
    "max_parallel_strikes": 2,
    "max_spawn_per_signal": 1,
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

echo "== harness start (chat page) =="
$PYTHON -m enhanced_harness.cli start --scope "$SCOPE_FILE" --out "$SESSION_DIR"

echo "== chat-page acceptance checks =="
$PYTHON - <<PY
import json, sys
from pathlib import Path
session = Path("$SESSION_DIR")
required = [
    "scope.used.json", "transcript.jsonl", "checkpoint.json",
    "findings.json", "findings.md", "coverage.json", "harness.log",
]
missing = [r for r in required if not (session / r).exists()]
if missing:
    print("MISSING artifacts:", missing, file=sys.stderr)
    sys.exit(1)

findings = json.loads((session / "findings.json").read_text())
confirmed = [f for f in findings if f.get("status") == "confirmed"]
if not confirmed:
    print("FAIL: expected ≥1 CONFIRMED finding against chat page", file=sys.stderr)
    print(json.dumps(findings, indent=2), file=sys.stderr)
    sys.exit(1)

web_confirmed = [f for f in confirmed if f.get("surface") == "web"]
if not web_confirmed:
    print("FAIL: confirmed finding must be on web/chat-ui surface", file=sys.stderr)
    sys.exit(1)

for f in web_confirmed:
    if not f.get("proof_hash"):
        print("FAIL: missing proof_hash", f, file=sys.stderr)
        sys.exit(1)

md = (session / "findings.md").read_text()
if "$HARNESS_FIXTURE_CANARY_VALUE" in md:
    print("FAIL: canary leaked into findings.md", file=sys.stderr)
    sys.exit(1)

transcript = (session / "transcript.jsonl").read_text()
if "chat_ui" not in transcript and "lab-chat-page" not in transcript:
    print("FAIL: transcript missing chat UI scout evidence", file=sys.stderr)
    sys.exit(1)

print("CHAT PAGE ACCEPTANCE PASS")
print(f"session: {session}")
print(f"web confirmed: {len(web_confirmed)}")
for f in web_confirmed:
    print(f"  - {f['id']} skill={f['skill_id']} proof={f['proof_hash'][:16]}...")
PY
