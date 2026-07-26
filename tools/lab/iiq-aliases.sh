#!/usr/bin/env bash
# IdentityIQ lab aliases — sourced from ~/.zshrc by setup-local.sh
# Safe to source multiple times.

_iiq_lab_load() {
  local env_file="${IIQ_LAB_ENV_FILE:-$HOME/.iiq-lab/env}"
  if [[ -f "$env_file" ]]; then
    # shellcheck disable=SC1090
    source "$env_file"
  fi
}

_iiq_lab_load

iiq-env() {
  _iiq_lab_load
  echo "SAILPOINT_ROOT=${SAILPOINT_ROOT:-}"
  echo "IIQ_LAB_HOME=${IIQ_LAB_HOME:-}"
  echo "CATALINA_HOME=${CATALINA_HOME:-}"
  echo "IIQ_HOME=${IIQ_HOME:-}"
  echo "JAVA_HOME=${JAVA_HOME:-}"
  echo "IIQ_URL=${IIQ_URL:-}"
  echo "IIQ_LAB_DATA=${IIQ_LAB_DATA:-}"
  echo "IIQ_LAB_ENV_FILE=${IIQ_LAB_ENV_FILE:-$HOME/.iiq-lab/env}"
}

iiq-status() {
  _iiq_lab_load
  local port="${IIQ_HTTP_PORT:-8080}"
  local dbport="${IIQ_DB_PORT:-3307}"
  echo "--- Java ---"
  if [[ -n "${JAVA_HOME:-}" && -x "${JAVA_HOME}/bin/java" ]]; then
    "${JAVA_HOME}/bin/java" -version 2>&1 | head -1
  else
    java -version 2>&1 | head -1 || echo "java not found"
  fi
  echo "--- Tomcat port :$port ---"
  if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    lsof -nP -iTCP:"$port" -sTCP:LISTEN | head -5
    echo "LISTEN: yes"
  else
    echo "LISTEN: no"
  fi
  echo "--- Lab MySQL port :$dbport ---"
  if lsof -nP -iTCP:"$dbport" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "LISTEN: yes"
  else
    echo "LISTEN: no (try: iiq-mysql-start)"
  fi
  echo "--- HTTP ---"
  local url="${IIQ_URL:-http://localhost:$port/identityiq}/login.jsf"
  if curl -fsS -o /dev/null --max-time 3 "$url" 2>/dev/null; then
    echo "IdentityIQ login page: UP ($url)"
  else
    echo "IdentityIQ login page: DOWN ($url)"
  fi
  echo "--- MySQL identityiq ---"
  if [[ -n "${IIQ_MYSQL_BIN:-}" && -x "${IIQ_MYSQL_BIN}/mysql" ]]; then
    local margs=( -u identityiq -pidentityiq -h 127.0.0.1 -P "$dbport" )
    if [[ -n "${IIQ_MYSQL_SOCKET:-}" ]]; then
      margs=( -u identityiq -pidentityiq --socket="$IIQ_MYSQL_SOCKET" )
    fi
    "${IIQ_MYSQL_BIN}/mysql" "${margs[@]}" -N -e "SELECT COUNT(*) AS identities FROM identityiq.spt_identity;" 2>/dev/null \
      || echo "Cannot query identityiq DB"
  else
    echo "mysql client not configured"
  fi
}

iiq-start() {
  _iiq_lab_load
  [[ -n "${CATALINA_HOME:-}" && -x "$CATALINA_HOME/bin/startup.sh" ]] || {
    echo "CATALINA_HOME not configured. Run tools/lab/setup-local.sh first." >&2
    return 1
  }
  if lsof -nP -iTCP:"${IIQ_HTTP_PORT:-8080}" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "Already listening on :${IIQ_HTTP_PORT:-8080}"
    return 0
  fi
  export JAVA_HOME
  "$CATALINA_HOME/bin/startup.sh"
  echo "Starting… try: iiq-logs   or   iiq-status"
}

iiq-stop() {
  _iiq_lab_load
  [[ -n "${CATALINA_HOME:-}" && -x "$CATALINA_HOME/bin/shutdown.sh" ]] || {
    echo "CATALINA_HOME not configured." >&2
    return 1
  }
  "$CATALINA_HOME/bin/shutdown.sh" || true
  sleep 2
  local pids
  pids="$(lsof -nP -iTCP:"${IIQ_HTTP_PORT:-8080}" -sTCP:LISTEN -t 2>/dev/null || true)"
  if [[ -n "$pids" ]]; then
    echo "Force-stopping leftover PIDs: $pids"
    # shellcheck disable=SC2086
    kill $pids 2>/dev/null || true
  fi
  echo "Stopped."
}

iiq-restart() {
  iiq-stop
  sleep 2
  iiq-start
}

iiq-logs() {
  _iiq_lab_load
  local log="${CATALINA_HOME:-}/logs/catalina.out"
  [[ -f "$log" ]] || {
    echo "No catalina.out at $log" >&2
    return 1
  }
  tail -n "${1:-100}" -f "$log"
}

iiq-console() {
  _iiq_lab_load
  [[ -n "${IIQ_HOME:-}" && -x "$IIQ_HOME/WEB-INF/bin/iiq" ]] || {
    echo "IIQ_HOME not configured / iiq binary missing." >&2
    return 1
  }
  export JAVA_HOME SPHOME="$IIQ_HOME"
  (
    cd "$IIQ_HOME/WEB-INF/bin"
    ./iiq console "$@"
  )
}

iiq-encrypt() {
  _iiq_lab_load
  [[ -n "${IIQ_HOME:-}" && -x "$IIQ_HOME/WEB-INF/bin/iiq" ]] || {
    echo "IIQ_HOME not configured." >&2
    return 1
  }
  [[ $# -ge 1 ]] || {
    echo "Usage: iiq-encrypt <plaintext>" >&2
    return 1
  }
  export JAVA_HOME SPHOME="$IIQ_HOME"
  (
    cd "$IIQ_HOME/WEB-INF/bin"
    ./iiq encrypt "$1"
  )
}

iiq-open() {
  _iiq_lab_load
  local url="${IIQ_URL:-http://localhost:8080/identityiq}"
  if command -v open >/dev/null 2>&1; then
    open "$url"
  else
    echo "$url"
  fi
}

iiq-data() {
  _iiq_lab_load
  echo "${IIQ_LAB_DATA:-$HOME/iiq-lab/data}"
  ls -la "${IIQ_LAB_DATA:-$HOME/iiq-lab/data}" 2>/dev/null || true
}

iiq-mysql-start() {
  _iiq_lab_load
  [[ "${IIQ_USE_LAB_MYSQL:-0}" == "1" ]] || {
    echo "Lab MySQL not configured (IIQ_USE_LAB_MYSQL!=1)." >&2
    return 1
  }
  if [[ -n "${IIQ_MYSQL_SOCKET:-}" ]] && "$IIQ_MYSQL_BIN/mysql" --socket="$IIQ_MYSQL_SOCKET" -u root -e "SELECT 1" >/dev/null 2>&1; then
    echo "Lab MySQL already up on :${IIQ_DB_PORT}"
    return 0
  fi
  mkdir -p "$(dirname "$IIQ_MYSQL_DATA")"
  nohup "$IIQ_MYSQL_BIN/mysqld" \
    --datadir="$IIQ_MYSQL_DATA" \
    --basedir="$(cd "$IIQ_MYSQL_BIN/.." && pwd)" \
    --port="${IIQ_DB_PORT}" \
    --bind-address=127.0.0.1 \
    --socket="$IIQ_MYSQL_SOCKET" \
    --pid-file="$IIQ_MYSQL_PID" \
    --mysqlx=0 \
    >>"${IIQ_LAB_HOME}/mysql/mysqld.err" 2>&1 &
  echo "Started lab MySQL (port ${IIQ_DB_PORT})."
}

iiq-mysql-stop() {
  _iiq_lab_load
  if [[ -n "${IIQ_MYSQL_PID:-}" && -f "$IIQ_MYSQL_PID" ]]; then
    local pid
    pid="$(cat "$IIQ_MYSQL_PID")"
    kill "$pid" 2>/dev/null || true
    rm -f "$IIQ_MYSQL_PID"
    echo "Stopped lab MySQL pid $pid"
    return 0
  fi
  # Fallback: kill by port
  local pids
  pids="$(lsof -nP -iTCP:"${IIQ_DB_PORT:-3307}" -sTCP:LISTEN -t 2>/dev/null || true)"
  if [[ -n "$pids" ]]; then
    # shellcheck disable=SC2086
    kill $pids 2>/dev/null || true
    echo "Stopped listeners on :${IIQ_DB_PORT}"
  else
    echo "Lab MySQL not running"
  fi
}

iiq-help() {
  cat <<'EOF'
IdentityIQ lab aliases

  iiq-env          Show lab paths / URL
  iiq-status       Java, ports, HTTP, DB smoke check
  iiq-start        Start Tomcat
  iiq-stop         Stop Tomcat
  iiq-restart      Restart Tomcat
  iiq-mysql-start  Start lab MySQL (port 3307 by default)
  iiq-mysql-stop   Stop lab MySQL
  iiq-logs         Tail catalina.out (optional: iiq-logs 200)
  iiq-console      Open IdentityIQ console
  iiq-encrypt      Encrypt a secret for iiq.properties
  iiq-open         Open IIQ in the browser
  iiq-data         Show lab CSV folder
  iiq-help         This help

Setup / teardown (from repo):
  ./tools/lab/setup-local.sh
  ./tools/lab/teardown-local.sh --yes
EOF
}

# zsh/bash friendly message once per interactive shell
if [[ -n "${PS1:-}" || -n "${ZSH_VERSION:-}" ]]; then
  if [[ -z "${IIQ_LAB_ALIASES_QUIET:-}" && -z "${IIQ_LAB_ALIASES_SHOWN:-}" ]]; then
    export IIQ_LAB_ALIASES_SHOWN=1
    # Only print when env exists (setup done)
    if [[ -f "${IIQ_LAB_ENV_FILE:-$HOME/.iiq-lab/env}" ]]; then
      echo "IdentityIQ lab aliases loaded. Try: iiq-help"
    fi
  fi
fi
