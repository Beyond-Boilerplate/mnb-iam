#!/usr/bin/env bash
# Host-path sidecars: OpenAPI docs (:8765) + IIQ MCP (:8766).
# Sourced by tools/lab/up.sh; can also run: ./tools/lab/start-sidecars.sh

_lab_sidecars_root() {
  cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd
}

_lab_sidecars_state_dir() {
  echo "${IIQ_LAB_STATE_DIR:-$HOME/.iiq-lab}"
}

iiq_sidecar_openapi_up() {
  curl -sf -o /dev/null --max-time 2 "http://127.0.0.1:${API_DOCS_PORT:-8765}/swagger/" 2>/dev/null
}

iiq_sidecar_mcp_up() {
  curl -sf -o /dev/null --max-time 2 "http://127.0.0.1:${MCP_PORT:-8766}/healthz" 2>/dev/null
}

ensure_openapi_docs() {
  local root state port bind log pidfile
  root="${ROOT:-$(_lab_sidecars_root)}"
  state="$(_lab_sidecars_state_dir)"
  port="${API_DOCS_PORT:-8765}"
  bind="${API_DOCS_BIND:-127.0.0.1}"
  log="${state}/api-docs.log"
  pidfile="${state}/api-docs.pid"

  if iiq_sidecar_openapi_up; then
    echo "==> OpenAPI docs already up (http://${bind}:${port}/swagger/)"
    return 0
  fi

  mkdir -p "$state"
  echo "==> Starting OpenAPI / Swagger docs on :${port}"
  # Prefer repo serve.py (CORS-safe IIQ proxy)
  nohup env IIQ_BASE="${IIQ_BASE:-http://127.0.0.1:${IIQ_HTTP_PORT:-8080}}" \
    python3 "$root/docs/api/serve.py" --bind "$bind" --port "$port" \
    >"$log" 2>&1 &
  echo $! >"$pidfile"
  sleep 1
  if iiq_sidecar_openapi_up; then
    echo "    OpenAPI: http://${bind}:${port}/swagger/"
  else
    echo "WARNING: OpenAPI docs did not become ready — see $log" >&2
  fi
}

ensure_iiq_mcp() {
  local root state port host log pidfile mcp_dir
  root="${ROOT:-$(_lab_sidecars_root)}"
  state="$(_lab_sidecars_state_dir)"
  port="${MCP_PORT:-8766}"
  host="${MCP_HOST:-127.0.0.1}"
  log="${state}/iiq-mcp.log"
  pidfile="${state}/iiq-mcp.pid"
  mcp_dir="$root/tools/iiq-mcp"

  if iiq_sidecar_mcp_up; then
    echo "==> IIQ MCP already up (http://${host}:${port}/mcp)"
    return 0
  fi

  if [[ ! -x "$mcp_dir/.venv/bin/python" ]]; then
    echo "==> Creating IIQ MCP venv + installing package…"
    python3 -m venv "$mcp_dir/.venv"
    # Prefer non-editable install (editable .pth is flaky on some Pythons)
    "$mcp_dir/.venv/bin/pip" install -q -U pip
    (cd "$mcp_dir" && "$mcp_dir/.venv/bin/pip" install -q .)
  fi

  if [[ ! -f "$mcp_dir/.env" ]]; then
    echo "==> Seeding tools/iiq-mcp/.env from .env.example"
    cp "$mcp_dir/.env.example" "$mcp_dir/.env"
    # Lab defaults so first start works against local IIQ
    if grep -q '^IIQ_PASSWORD=$' "$mcp_dir/.env" 2>/dev/null || ! grep -q '^IIQ_PASSWORD=.' "$mcp_dir/.env"; then
      # shellcheck disable=SC2016
      sed -i.bak 's|^IIQ_PASSWORD=.*|IIQ_PASSWORD=admin|' "$mcp_dir/.env"
      sed -i.bak 's|^IIQ_USER=.*|IIQ_USER=spadmin|' "$mcp_dir/.env"
      rm -f "$mcp_dir/.env.bak"
    fi
  fi

  mkdir -p "$state" "$mcp_dir/var"
  echo "==> Starting IIQ MCP on :${port}"
  (
    cd "$mcp_dir"
    # run.sh puts src on PYTHONPATH; inherit .env via pydantic-settings
    export MCP_HOST="$host"
    export MCP_PORT="$port"
    export IIQ_BASE_URL="${IIQ_BASE_URL:-http://localhost:${IIQ_HTTP_PORT:-8080}/identityiq}"
    export IIQ_USER="${IIQ_USER:-spadmin}"
    export IIQ_PASSWORD="${IIQ_PASSWORD:-admin}"
    export IIQ_MCP_ENABLED_PHASES="${IIQ_MCP_ENABLED_PHASES:-1,2,3,4}"
    nohup ./run.sh >"$log" 2>&1 &
    echo $! >"$pidfile"
  )
  sleep 2
  if iiq_sidecar_mcp_up; then
    echo "    MCP:     http://${host}:${port}/mcp  (healthz ok)"
  else
    echo "WARNING: IIQ MCP did not become ready — see $log" >&2
  fi
}

ensure_iiq_chat() {
  local root state port bind log pidfile
  root="${ROOT:-$(_lab_sidecars_root)}"
  state="$(_lab_sidecars_state_dir)"
  port="${CHAT_PORT:-4180}"
  bind="${CHAT_HOST:-127.0.0.1}"
  log="${state}/iiq-chat.log"
  pidfile="${state}/iiq-chat.pid"

  if curl -sf -o /dev/null --max-time 2 "http://127.0.0.1:${port}/api/config" 2>/dev/null; then
    echo "==> IIQ Teller already up (http://${bind}:${port}/)"
    return 0
  fi

  mkdir -p "$state"
  echo "==> Starting IIQ Teller chatbot on :${port}"
  (
    cd "$root/tools/iiq-chat"
    export CHAT_HOST="$bind"
    export CHAT_PORT="$port"
    export IIQ_MCP_URL="${IIQ_MCP_URL:-http://127.0.0.1:${MCP_PORT:-8766}/mcp}"
    export MCP_API_KEY="${MCP_API_KEY:-}"
    nohup python3 serve.py >"$log" 2>&1 &
    echo $! >"$pidfile"
  )
  sleep 1
  if curl -sf -o /dev/null --max-time 2 "http://127.0.0.1:${port}/api/config" 2>/dev/null; then
    echo "    Teller:  http://${bind}:${port}/"
  else
    echo "WARNING: IIQ Teller did not become ready — see $log" >&2
  fi
}

ensure_lab_sidecars() {
  ensure_openapi_docs
  ensure_iiq_mcp
  ensure_iiq_chat
}

stop_lab_sidecars() {
  local state
  state="$(_lab_sidecars_state_dir)"
  for name in api-docs iiq-mcp iiq-chat; do
    local pidfile="${state}/${name}.pid"
    if [[ -f "$pidfile" ]]; then
      local pid
      pid="$(cat "$pidfile" 2>/dev/null || true)"
      if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null || true
        echo "Stopped $name (pid $pid)"
      fi
      rm -f "$pidfile"
    fi
  done
  # Port fallbacks
  local p
  for p in "${API_DOCS_PORT:-8765}" "${MCP_PORT:-8766}" "${CHAT_PORT:-4180}"; do
    local pids
    pids="$(lsof -nP -iTCP:"$p" -sTCP:LISTEN -t 2>/dev/null || true)"
    if [[ -n "$pids" ]]; then
      # shellcheck disable=SC2086
      kill $pids 2>/dev/null || true
    fi
  done
}

# Direct invocation
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  set -euo pipefail
  ROOT="$(_lab_sidecars_root)"
  case "${1:-start}" in
    start) ensure_lab_sidecars ;;
    stop) stop_lab_sidecars ;;
    status)
      iiq_sidecar_openapi_up && echo "openapi: up" || echo "openapi: down"
      iiq_sidecar_mcp_up && echo "mcp: up" || echo "mcp: down"
      curl -sf -o /dev/null --max-time 2 "http://127.0.0.1:${CHAT_PORT:-4180}/api/config" 2>/dev/null \
        && echo "teller: up" || echo "teller: down"
      ;;
    *)
      echo "Usage: $0 {start|stop|status}" >&2
      exit 2
      ;;
  esac
fi
