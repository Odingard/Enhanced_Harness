#!/usr/bin/env bash
# Stand up OWASP FinBot CTF locally (Juice Shop for Agentic AI).
# Fair lab use only — does NOT encode challenges, flags, or walkthroughs.
#
# Prefer Docker Compose when the daemon can run containers.
# Falls back to native uv + local Redis when Docker overlay mounts are broken
# (common in nested/cloud agent VMs).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAB_DIR="${FINBOT_LAB_DIR:-$ROOT/labs/finbot-ctf}"
REPO_URL="${FINBOT_REPO_URL:-https://github.com/GenAI-Security-Project/finbot-ctf.git}"
PORT="${PORT:-8000}"
MODE="${FINBOT_LAB_MODE:-auto}"   # auto | docker | native
PID_FILE="$ROOT/labs/finbot.pid"
LOG_FILE="$ROOT/labs/finbot.log"

mkdir -p "$ROOT/labs"

if [[ ! -d "$LAB_DIR/.git" ]]; then
  echo "== cloning OWASP FinBot CTF =="
  git clone --depth 1 "$REPO_URL" "$LAB_DIR"
fi

cd "$LAB_DIR"

prepare_env() {
  if [[ ! -f .env ]]; then
    cp .env.example .env
    if grep -q '^DATABASE_URL=sqlite://finbot.db' .env; then
      sed -i 's|^DATABASE_URL=sqlite://finbot.db|DATABASE_URL=sqlite://data/finbot.db|' .env
    fi
    sed -i "s|^PORT=.*|PORT=${PORT}|" .env
    sed -i "s|^MAGIC_LINK_BASE_URL=.*|MAGIC_LINK_BASE_URL=http://127.0.0.1:${PORT}|" .env
    mkdir -p data uploads cache
    echo "Wrote $LAB_DIR/.env from .env.example"
  fi
  if [[ -n "${OPENAI_API_KEY:-}" ]]; then
    if grep -q '^OPENAI_API_KEY=' .env; then
      sed -i "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=${OPENAI_API_KEY}|" .env
    else
      echo "OPENAI_API_KEY=${OPENAI_API_KEY}" >> .env
    fi
    echo "OPENAI_API_KEY detected — injected into FinBot .env"
  else
    echo "NOTE: OPENAI_API_KEY not set. UI will start; AI agent challenges need a key or Ollama."
  fi
  # Ensure redis URL for native/local
  if ! grep -q '^REDIS_URL=' .env; then
    echo "REDIS_URL=redis://127.0.0.1:6379" >> .env
  else
    sed -i 's|^REDIS_URL=.*|REDIS_URL=redis://127.0.0.1:6379|' .env
  fi
}

docker_usable() {
  docker info >/dev/null 2>&1 || return 1
  # Probe whether containers can actually start (overlayfs may be broken)
  docker run --rm hello-world >/dev/null 2>&1
}

wait_ready() {
  echo "== waiting for http://127.0.0.1:${PORT}/ =="
  for _ in $(seq 1 90); do
    if curl -fsS "http://127.0.0.1:${PORT}/" >/dev/null 2>&1; then
      echo "FinBot is up: http://127.0.0.1:${PORT}/"
      echo "Vendor AI assistant (after auth/onboarding): /vendor/assistant"
      echo "Harness scope template: $ROOT/scope.finbot.example.json"
      echo "Docs: $ROOT/docs/FINBOT_LAB.md"
      return 0
    fi
    sleep 2
  done
  return 1
}

start_docker() {
  echo "== docker compose up (FinBot + Redis) =="
  # Prefer classic builder when BuildKit overlay mounts fail
  export DOCKER_BUILDKIT="${DOCKER_BUILDKIT:-0}"
  export COMPOSE_DOCKER_CLI_BUILD=0
  if [[ -f "$ROOT/labs/Dockerfile.finbot-workaround" ]]; then
    cp "$ROOT/labs/Dockerfile.finbot-workaround" "$LAB_DIR/Dockerfile.harness"
    docker compose build --build-arg unused=1 2>/dev/null || true
  fi
  docker compose up -d --build
  if ! wait_ready; then
    echo "FinBot docker did not become ready. Recent logs:" >&2
    docker compose logs --tail=80 >&2 || true
    return 1
  fi
}

ensure_redis_native() {
  if redis-cli ping >/dev/null 2>&1; then
    echo "Redis OK"
    return 0
  fi
  if command -v redis-server >/dev/null 2>&1; then
    redis-server --daemonize yes --port 6379
    sleep 1
  else
    echo "Installing redis-server..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq redis-server
    redis-server --daemonize yes --port 6379 || sudo service redis-server start || true
    sleep 1
  fi
  redis-cli ping >/dev/null
}

start_native() {
  echo "== native mode (uv + local Redis) =="
  ensure_redis_native
  export PATH="$HOME/.local/bin:$PATH"
  if ! command -v uv >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # shellcheck disable=SC1091
    source "$HOME/.local/bin/env"
  fi

  # FinBot requires Python >=3.13; uv will fetch it
  uv python install 3.13
  uv sync

  mkdir -p data uploads cache
  # Prefer sqlite file under data/
  if grep -q '^DATABASE_URL=sqlite://data/finbot.db' .env; then
    :
  else
    sed -i 's|^DATABASE_URL=.*|DATABASE_URL=sqlite://data/finbot.db|' .env || true
  fi

  echo "Running FinBot bootstrap..."
  uv run python scripts/bootstrap.py || echo "Bootstrap warned — continuing"

  if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "FinBot already running (pid $(cat "$PID_FILE"))"
  else
    echo "Starting FinBot on :${PORT} (log: $LOG_FILE)"
    nohup uv run uvicorn finbot.main:app --host 0.0.0.0 --port "$PORT" >"$LOG_FILE" 2>&1 &
    echo $! >"$PID_FILE"
  fi

  if ! wait_ready; then
    echo "FinBot native start failed. Log tail:" >&2
    tail -80 "$LOG_FILE" >&2 || true
    return 1
  fi
}

prepare_env

case "$MODE" in
  docker) start_docker ;;
  native) start_native ;;
  auto)
    if docker_usable; then
      start_docker || {
        echo "Docker path failed — falling back to native."
        start_native
      }
    else
      echo "Docker not usable in this environment — using native uv + Redis."
      start_native
    fi
    ;;
  *)
    echo "Unknown FINBOT_LAB_MODE=$MODE (use auto|docker|native)" >&2
    exit 2
    ;;
esac
