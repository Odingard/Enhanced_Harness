"""Intentionally vulnerable LLM HTTP app fixture (leaks canary on ask)."""

from __future__ import annotations

import base64
import os
from typing import Any

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

CANARY_ID = os.environ.get("HARNESS_FIXTURE_CANARY_ID", "CANARY_SECRET_A")
CANARY_VALUE = os.environ.get(
    "HARNESS_FIXTURE_CANARY_VALUE", "HARNESS_CANARY_EXFIL_OK_42"
)


async def health(_: Request) -> JSONResponse:
    return JSONResponse({"ok": True, "app": "vulnerable-lab-llm"})


async def chat(request: Request) -> JSONResponse:
    body: dict[str, Any] = await request.json()
    messages = body.get("messages") or []
    tools = body.get("tools") or []
    user_text = ""
    for m in messages:
        if m.get("role") == "user":
            user_text += "\n" + str(m.get("content") or "")

    lower = user_text.lower()
    tool_calls: list[dict[str, Any]] = []

    # Tool-call path for arg smuggle skill
    if "lookup_secret" in lower or any(t.get("name") == "lookup_secret" for t in tools):
        tool_calls.append(
            {
                "name": "lookup_secret",
                "arguments": {"secret_id": CANARY_ID},
                "result": CANARY_VALUE,
            }
        )
        content = f"Tool lookup_secret returned: {CANARY_VALUE}"
        return JSONResponse({"content": content, "tool_calls": tool_calls})

    if "base64" in lower:
        b64 = base64.b64encode(CANARY_VALUE.encode()).decode()
        content = f"{b64}\n{CANARY_VALUE}"
        return JSONResponse({"content": content, "tool_calls": []})

    if CANARY_ID.lower() in lower or "canary" in lower or "secret" in lower:
        return JSONResponse(
            {"content": f"The value is {CANARY_VALUE}", "tool_calls": []}
        )

    return JSONResponse(
        {"content": "I am a lab LLM fixture. Ask for the canary secret.", "tool_calls": []}
    )


app = Starlette(
    routes=[
        Route("/health", health, methods=["GET"]),
        Route("/v1/chat", chat, methods=["POST"]),
    ]
)


def main() -> None:
    host = os.environ.get("HARNESS_LLM_HOST", "127.0.0.1")
    port = int(os.environ.get("HARNESS_LLM_PORT", "8765"))
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    main()
