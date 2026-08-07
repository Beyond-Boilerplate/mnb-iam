#!/usr/bin/env bash
# Backup live Meridian IIQ objects via MCP extract, then wipe for a clean seed.
# Opt-in only: ./tools/lab/docker/up.sh --wipe  (or call this script / seed --wipe).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
export IIQ_MCP_URL="${IIQ_MCP_URL:-http://127.0.0.1:8766/mcp}"
export MCP_API_KEY="${MCP_API_KEY:-mnb-lab-mcp-key}"
exec python3 "$ROOT/tools/lab/scripts/backup_and_reset_lab.py" "$@"
