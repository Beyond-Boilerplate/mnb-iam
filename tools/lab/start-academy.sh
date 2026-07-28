#!/usr/bin/env bash
# Build + serve Meridian learn site locally with live Verify API.
# Requires IIQ reachable at IIQ_BASE_URL (default localhost:8080).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

export IIQ_BASE_URL="${IIQ_BASE_URL:-http://localhost:8080/identityiq}"
export IIQ_USER="${IIQ_USER:-spadmin}"
export IIQ_PASSWORD="${IIQ_PASSWORD:-admin}"
export IIQ_HOME="${IIQ_HOME:-$HOME/iiq-lab/tomcat/webapps/identityiq}"
export IIQ_VERIFY_MODE="${IIQ_VERIFY_MODE:-auto}"
export ACADEMY_PORT="${ACADEMY_PORT:-4173}"

echo "==> Building learn site"
python3 learn/build.py

echo "==> Starting academy at http://127.0.0.1:${ACADEMY_PORT}/"
echo "    IIQ: ${IIQ_BASE_URL}"
echo "    Open a lesson → Lesson verify → Verify now"
exec python3 tools/academy/serve.py
