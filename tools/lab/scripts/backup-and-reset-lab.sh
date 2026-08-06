#!/usr/bin/env bash
# Backup live Meridian IIQ objects via MCP extract, then wipe for a clean seed.
# Used automatically by docker/up.sh + seed-mnb-lab-data unless --keep-existing.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
export IIQ_MCP_URL="${IIQ_MCP_URL:-http://127.0.0.1:8766/mcp}"
export MCP_API_KEY="${MCP_API_KEY:-mnb-lab-mcp-key}"
exec python3 "$ROOT/tools/lab/scripts/backup_and_reset_lab.py" "$@"
