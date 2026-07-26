# OWASP FinBot CTF lab (fair use)

FinBot is the **Juice Shop of Agentic AI** — an intentionally vulnerable
multi-agent vendor platform from the OWASP GenAI Security Project.

- Public site: https://owasp-finbot-ctf.org/
- Upstream repo: https://github.com/GenAI-Security-Project/finbot-ctf

Enhanced Harness may use FinBot for **authorized / fair live testing only**.

## Hard rules

- Do **not** encode FinBot challenges, flags, detectors, or walkthroughs in this repo.
- Do **not** commit FinBot challenge YAML or spoiler material.
- Operators discover engagement details themselves during authorized prep.
- Confirmed findings still require Enhanced Harness oracle proof (Verifier-only).

## Stand up locally

```bash
# optional but needed for live AI-agent challenges
export OPENAI_API_KEY=sk-...

./scripts/lab_finbot_up.sh
# → http://127.0.0.1:8000/

./scripts/lab_finbot_down.sh
```

### Modes

| Mode | When |
|------|------|
| `FINBOT_LAB_MODE=auto` (default) | Try Docker Compose; fall back to native |
| `FINBOT_LAB_MODE=docker` | Force `docker compose up` (needs working Docker) |
| `FINBOT_LAB_MODE=native` | `uv` + local Redis (used when Docker overlay mounts are broken) |

The helper clones FinBot into `labs/finbot-ctf/` (gitignored).

On this Cloud Agent host, Docker’s overlayfs could not start containers, so the
lab helper uses **native mode** successfully:

- Redis via `redis-server`
- FinBot via `uv` + Python 3.13 on port **8000**

On a normal developer machine with healthy Docker, `./scripts/lab_finbot_up.sh`
uses Compose (app + Redis) as upstream documents.

## Point the harness at FinBot

1. Open http://127.0.0.1:8000/ and complete FinBot signup / vendor onboarding
   (magic links print to FinBot logs when `EMAIL_PROVIDER=console`).
2. Open the Vendor Portal **AI Assistant** (`/vendor/assistant`).
3. Copy `scope.finbot.example.json` → `scope.json` and set:
   - honest `roe.authorized` for your engagement
   - allowlisted host `127.0.0.1`
   - `flags.enable_agent_chat_ui: true`
   - authenticated assistant URL you are authorized to test
   - chat selectors (`#chat-input`, `#chat-send`, `#chat-messages` on upstream UI)
   - your own canaries / oracle hooks
4. Run:

```bash
.venv/bin/pip install -e ".[lab]"
.venv/bin/playwright install chromium
.venv/bin/harness doctor --scope scope.json
.venv/bin/harness start --scope scope.json
```

## What this is / isn’t

| Is | Isn’t |
|----|-------|
| Local Juice-Shop-style AI lab target | A FinBot writeup or cheat sheet |
| Fair adapter/scope wiring for chat UI | Encoded challenge solutions |
| Docker/native lab bring-up helper | Generic web XSS/SQLi pack |

## Visuals

See [`VISUALS.md`](VISUALS.md).
