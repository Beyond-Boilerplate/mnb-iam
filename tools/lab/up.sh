#!/usr/bin/env bash
# One command: host Tomcat IdentityIQ + Academy (lessons + Verify now).
#
# First run: full setup-local.sh (MySQL + Tomcat + init), then Academy.
# Later: start lab MySQL/Tomcat if needed, then Academy.
#
# Usage:
#   ./tools/lab/up.sh
#   ./tools/lab/up.sh --force-db     # rebuild DB via setup-local, then Academy
#   ./tools/lab/up.sh --check        # preflight only (setup-local --check)
#   ./tools/lab/up.sh --academy-only # Academy only (IIQ must already be up)
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LAB="$ROOT/tools/lab"
ENV_FILE="${IIQ_LAB_ENV_FILE:-$HOME/.iiq-lab/env}"
PORT="${IIQ_HTTP_PORT:-8080}"
LOGIN_URL="http://127.0.0.1:${PORT}/identityiq/login.jsf"

ACADEMY_ONLY=0
SETUP_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --academy-only) ACADEMY_ONLY=1 ;;
    -h|--help)
      sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) SETUP_ARGS+=("$1") ;;
  esac
  shift
done

iiq_login_up() {
  curl -sf -o /dev/null --max-time 3 "$LOGIN_URL" 2>/dev/null
}

wait_iiq() {
  local i
  echo "==> Waiting for IdentityIQ login page…"
  for i in $(seq 1 90); do
    if iiq_login_up; then
      echo "    IdentityIQ is up ($LOGIN_URL)"
      return 0
    fi
    sleep 5
  done
  echo "ERROR: timed out waiting for $LOGIN_URL" >&2
  return 1
}

ensure_iiq() {
  if iiq_login_up && [[ ${#SETUP_ARGS[@]} -eq 0 ]]; then
    echo "==> IdentityIQ already up"
    return 0
  fi

  # First install, or explicit setup flags (--force-db, etc.)
  if [[ ${#SETUP_ARGS[@]} -gt 0 || ! -f "$ENV_FILE" ]]; then
    echo "==> Running host lab setup (Tomcat + MySQL)…"
    "$LAB/setup-local.sh" "${SETUP_ARGS[@]}"
    wait_iiq
    return 0
  fi

  # Day-2: start MySQL + Tomcat from saved env
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  # shellcheck disable=SC1091
  source "$LAB/iiq-aliases.sh"

  if [[ ! -x "${CATALINA_HOME:-}/bin/startup.sh" ]]; then
    echo "==> Lab env present but Tomcat missing — running full setup…"
    "$LAB/setup-local.sh"
    wait_iiq
    return 0
  fi

  echo "==> Starting lab MySQL + Tomcat…"
  iiq-mysql-start || true
  iiq-start
  wait_iiq
}

start_academy() {
  export IIQ_BASE_URL="${IIQ_BASE_URL:-http://localhost:${PORT}/identityiq}"
  export IIQ_USER="${IIQ_USER:-spadmin}"
  export IIQ_PASSWORD="${IIQ_PASSWORD:-admin}"
  export IIQ_HOME="${IIQ_HOME:-$HOME/iiq-lab/tomcat/webapps/identityiq}"
  export IIQ_VERIFY_MODE="${IIQ_VERIFY_MODE:-auto}"
  export ACADEMY_PORT="${ACADEMY_PORT:-4173}"

  echo "==> Building learn site"
  python3 "$ROOT/learn/build.py"

  echo
  echo "Ready."
  echo "  Academy:  http://localhost:${ACADEMY_PORT}/"
  echo "  IIQ:      http://localhost:${PORT}/identityiq  (spadmin / admin)"
  echo
  echo "Open Academy → Lesson 01 → Lesson verify → Verify now"
  echo "==> Starting academy (Ctrl+C to stop Academy; IIQ keeps running)"
  exec python3 "$ROOT/tools/academy/serve.py"
}

# --check: setup preflight only
if [[ ${#SETUP_ARGS[@]} -gt 0 && "${SETUP_ARGS[0]}" == "--check" ]]; then
  exec "$LAB/setup-local.sh" --check
fi

if [[ "$ACADEMY_ONLY" -eq 0 ]]; then
  ensure_iiq
else
  if ! iiq_login_up; then
    echo "ERROR: --academy-only requires IdentityIQ at $LOGIN_URL" >&2
    echo "Run: ./tools/lab/up.sh" >&2
    exit 1
  fi
fi

start_academy
