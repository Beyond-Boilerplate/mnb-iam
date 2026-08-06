#!/usr/bin/env bash
# Run Enterprise Sandbox lesson asserts (PASS/FAIL + assert text).
# Usage:
#   ./tools/lab/enterprise/verify-lesson.sh 203
#   ./tools/lab/enterprise/verify-lesson.sh 201 202 203
#   ./tools/lab/enterprise/verify-lesson.sh --all
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
export IIQ_MCP_URL="${IIQ_MCP_URL:-http://127.0.0.1:8766/mcp}"
export MCP_API_KEY="${MCP_API_KEY:-mnb-lab-mcp-key}"
export IIQ_BASE_URL="${IIQ_BASE_URL:-http://127.0.0.1:8080/identityiq}"
exec python3 "$ROOT/tools/lab/enterprise/verify_enterprise_lesson.py" "$@"
