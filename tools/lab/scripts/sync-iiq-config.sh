#!/usr/bin/env bash
# Pull live IIQ UI objects into config/ (export → scrub → diff → optional write).
#
#   ./tools/lab/scripts/sync-iiq-config.sh              # check / print diffs
#   ./tools/lab/scripts/sync-iiq-config.sh --write       # update config/
#   ./tools/lab/scripts/sync-iiq-config.sh --discover --write
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
export IIQ_MCP_URL="${IIQ_MCP_URL:-http://127.0.0.1:8766/mcp}"
export MCP_API_KEY="${MCP_API_KEY:-mnb-lab-mcp-key}"
exec python3 "$ROOT/tools/lab/scripts/sync_iiq_config.py" "$@"
