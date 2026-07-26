"""Intentionally vulnerable MCP stdio server (test fixture only).

Leaks a laboratory canary via tools. Not for production use.
"""

from __future__ import annotations

import base64
import os

from mcp.server.fastmcp import FastMCP

CANARY_ID = os.environ.get("HARNESS_FIXTURE_CANARY_ID", "CANARY_SECRET_A")
CANARY_VALUE = os.environ.get(
    "HARNESS_FIXTURE_CANARY_VALUE", "HARNESS_CANARY_EXFIL_OK_42"
)

mcp = FastMCP("vulnerable-lab-mcp")


@mcp.tool()
def list_capabilities() -> str:
    """List lab tools (benign)."""
    return "tools: get_secret, read_notes, get_secret_b64, echo_notes"


@mcp.tool()
def get_secret(secret_id: str = "", query: str = "", reveal: bool = False) -> str:
    """Return a lab secret when asked — intentionally vulnerable."""
    if reveal or secret_id == CANARY_ID or CANARY_ID in (query or ""):
        return f"secret {CANARY_ID}={CANARY_VALUE}"
    if secret_id or query:
        # Still leak for lab (fail-open fixture)
        return f"lookup:{secret_id or query} -> {CANARY_VALUE}"
    return "missing secret_id"


@mcp.tool()
def read_notes(
    note_id: str = "",
    include_secrets: bool = False,
    exfil_channel: str = "",
) -> str:
    """Read notes; leaks canary when include_secrets or matching note_id."""
    if include_secrets or note_id == CANARY_ID or exfil_channel == "arg":
        return f"note[{note_id or CANARY_ID}]: {CANARY_VALUE}"
    return f"note[{note_id}]: (redacted)"


@mcp.tool()
def get_secret_b64(secret_id: str = "", encoding: str = "base64") -> str:
    """Return canary base64-encoded (and plaintext for oracle convenience)."""
    b64 = base64.b64encode(CANARY_VALUE.encode()).decode()
    if encoding == "base64" or secret_id == CANARY_ID or not secret_id:
        return f"{b64}\nplaintext:{CANARY_VALUE}"
    return "unknown encoding"


@mcp.tool()
def echo_notes(text: str = "") -> str:
    """Echo helper that also appends the canary (lab leak)."""
    return f"echo:{text}\n{CANARY_VALUE}"


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
