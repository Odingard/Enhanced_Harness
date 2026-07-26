"""Runtime configuration helpers."""

from __future__ import annotations

from pathlib import Path

DEFAULT_OUT_ROOT = Path("harness-out")
PRODUCT_NAME = "Enhanced Harness"
CLI_NAME = "harness"
PACKAGE_NAME = "enhanced_harness"


def ensure_out_dir(out: str | Path | None = None) -> Path:
    root = Path(out) if out else DEFAULT_OUT_ROOT
    root.mkdir(parents=True, exist_ok=True)
    return root
