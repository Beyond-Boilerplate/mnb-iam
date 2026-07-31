#!/usr/bin/env bash
# Run blackbox Teller agent eval against a live lab.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
export TELLER_URL="${TELLER_URL:-http://127.0.0.1:4180}"
export IIQ_MCP_URL="${IIQ_MCP_URL:-http://127.0.0.1:8766/mcp}"
export MCP_API_KEY="${MCP_API_KEY:-mnb-lab-mcp-key}"

echo "Teller: $TELLER_URL"
curl -sf "$TELLER_URL/api/health" >/dev/null || {
  echo "ERROR: Teller not healthy at $TELLER_URL — start stack (./tools/lab/docker/up.sh)" >&2
  exit 2
}

exec python3 "$ROOT/tools/iiq-chat/eval/runner.py" --refresh-tools "$@"
