#!/usr/bin/env bash
# Fail if shippable package contains stub/fake markers.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TARGET="${1:-enhanced_harness}"

# Disallow obvious stub markers in product package (not tests/docs).
if grep -RInE \
  --exclude-dir='__pycache__' \
  -e 'NotImplementedError' \
  -e 'TODO:\s*implement' \
  -e 'pass\s*#\s*stub' \
  -e '\bfake_finding\b' \
  -e '\bARGUS\b' \
  -e '\bALEC\b' \
  "$TARGET"; then
  echo "FAIL: stub/branding markers found in $TARGET" >&2
  exit 1
fi

echo "OK: no stub/branding markers in $TARGET"
