#!/usr/bin/env bash
# Robust launcher: always put src on PYTHONPATH (works even if editable .pth flakes).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
export PYTHONPATH="${ROOT}/src${PYTHONPATH:+:$PYTHONPATH}"
if [[ -x "${ROOT}/.venv/bin/python" ]]; then
  exec "${ROOT}/.venv/bin/python" -m iiq_mcp "$@"
fi
exec python3 -m iiq_mcp "$@"
