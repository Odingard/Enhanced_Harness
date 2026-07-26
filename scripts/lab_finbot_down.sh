#!/usr/bin/env bash
# Tear down local OWASP FinBot CTF (Docker and/or native).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAB_DIR="${FINBOT_LAB_DIR:-$ROOT/labs/finbot-ctf}"
PID_FILE="$ROOT/labs/finbot.pid"

if [[ -d "$LAB_DIR" ]]; then
  cd "$LAB_DIR"
  if docker compose ps >/dev/null 2>&1; then
    docker compose down 2>/dev/null || true
  fi
fi

if [[ -f "$PID_FILE" ]]; then
  pid="$(cat "$PID_FILE")"
  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
    echo "Stopped native FinBot pid $pid"
  fi
  rm -f "$PID_FILE"
fi

echo "FinBot lab stopped."
