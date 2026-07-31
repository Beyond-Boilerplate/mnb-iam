#!/usr/bin/env bash
# Seed Meridian lab IIQ: MNB-HR (authoritative) + MNB-OpenLDAP via MCP.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
export IIQ_MCP_URL="${IIQ_MCP_URL:-http://127.0.0.1:8766/mcp}"
export MCP_API_KEY="${MCP_API_KEY:-mnb-lab-mcp-key}"
exec python3 "$ROOT/tools/lab/scripts/seed_mnb_lab_data.py" "$@"
