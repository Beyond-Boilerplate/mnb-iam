#!/usr/bin/env bash
# One command: Postgres + OpenLDAP + IdentityIQ + Academy + MCP + OpenAPI + Teller.
#
# Fail-fast on occupied ports. Default path also installs the Meridian plugin and seeds
# MNB-HR + MNB-OpenLDAP. Speeds: skip image rebuild when local images exist; parallel
# readiness probes; package plugin while the stack is coming up.
#
# Usage:
#   ./tools/lab/docker/up.sh
#   ./tools/lab/docker/up.sh --check
#   ./tools/lab/docker/up.sh --rebuild
#   ./tools/lab/docker/up.sh --skip-seed
#   ./tools/lab/docker/up.sh --kill-host-sidecars
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"
COMPOSE=(docker compose -f docker-compose.iiq.yml)
PROJECT_NAME="mnb-iiq-lab"

CHECK_ONLY=0
KILL_HOST_SIDECARS=0
DO_SEED=1
FORCE_REBUILD=0
for arg in "$@"; do
  case "$arg" in
    --check) CHECK_ONLY=1 ;;
    --kill-host-sidecars) KILL_HOST_SIDECARS=1 ;;
    --skip-seed) DO_SEED=0 ;;
    --seed) DO_SEED=1 ;;
    --rebuild|--build) FORCE_REBUILD=1 ;;
    -h|--help)
      cat <<'EOF'
Usage: ./tools/lab/docker/up.sh [options]

  (default)               Start stack, verify, install/enable plugin, seed lab apps
  --check                 Preflight ports only
  --rebuild               Force docker compose build (slower)
  --kill-host-sidecars    Stop host listeners on MCP/OpenAPI ports, then start
  --skip-seed             Start + verify only (no plugin seed / HR aggregation)
  --seed                  Explicitly enable seed (default)
EOF
      exit 0
      ;;
    *)
      echo "Unknown arg: $arg (try --help)" >&2
      exit 2
      ;;
  esac
done

IIQ_HTTP_PORT="${IIQ_HTTP_PORT:-8080}"
MCP_PORT="${MCP_PORT:-8766}"
API_DOCS_PORT="${API_DOCS_PORT:-8765}"
CHAT_PORT="${CHAT_PORT:-4180}"
ACADEMY_PORT="${ACADEMY_PORT:-4173}"
LDAP_PORT="${LDAP_PORT:-389}"
LDAPS_PORT="${LDAPS_PORT:-636}"
PG_PORT="${PG_PORT:-5433}"

PORTS=(
  "IIQ:${IIQ_HTTP_PORT}"
  "MCP:${MCP_PORT}"
  "OpenAPI:${API_DOCS_PORT}"
  "Teller:${CHAT_PORT}"
  "Academy:${ACADEMY_PORT}"
  "OpenLDAP:${LDAP_PORT}"
  "LDAPS:${LDAPS_PORT}"
  "Postgres:${PG_PORT}"
)

# Images we build locally (pull-only IIQ image is separate).
LOCAL_IMAGES=(
  "${MCP_IMAGE:-mnb-iiq-mcp:local}"
  "${CHAT_IMAGE:-mnb-iiq-chat:local}"
  "${OPENLDAP_IMAGE:-mnb-openldap:local}"
  "${API_DOCS_IMAGE:-mnb-api-docs:local}"
  "${ACADEMY_IMAGE:-mnb-academy:local}"
)

die() { echo "ERROR: $*" >&2; exit 1; }
info() { echo "==> $*"; }

require_docker() {
  command -v docker >/dev/null 2>&1 || die "docker not found on PATH"
  docker info >/dev/null 2>&1 || die "Docker daemon not reachable - start Docker Desktop / dockerd"
  docker compose version >/dev/null 2>&1 || die "docker compose plugin missing"
}

is_docker_proxy_pid() {
  local pid="$1"
  local cmd
  cmd="$(ps -p "$pid" -o comm= 2>/dev/null || true)"
  case "$cmd" in
    *docker*|*com.docke*|*vpnkit*) return 0 ;;
    *) return 1 ;;
  esac
}

our_stack_owns_port() {
  local port="$1"
  local ports_blob
  ports_blob="$(docker ps --filter "label=com.docker.compose.project=${PROJECT_NAME}" \
    --format '{{.Ports}}' 2>/dev/null || true)"
  printf '%s\n' "$ports_blob" | grep -F ":${port}->" >/dev/null 2>&1
}

describe_listeners() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    lsof -nP -iTCP:"$port" -sTCP:LISTEN 2>/dev/null | sed 's/^/    /' || true
  else
    echo "    (install lsof for listener details)"
  fi
}

listener_pids() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    lsof -nP -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null || true
  fi
}

maybe_kill_host_sidecars() {
  local port pid cmd
  for port in "$MCP_PORT" "$API_DOCS_PORT"; do
    for pid in $(listener_pids "$port"); do
      if is_docker_proxy_pid "$pid"; then
        continue
      fi
      cmd="$(ps -p "$pid" -o comm= 2>/dev/null || true)"
      info "Stopping host sidecar on :${port} (pid $pid, $cmd)"
      kill "$pid" 2>/dev/null || true
      sleep 0.3
    done
  done
}

preflight_ports() {
  local blocked=0 entry label port pids pid foreign
  echo "==> Preflight: host ports"
  for entry in "${PORTS[@]}"; do
    label="${entry%%:*}"
    port="${entry#*:}"
    pids="$(listener_pids "$port")"
    if [[ -z "$pids" ]]; then
      echo "    OK  :${port}  free (${label})"
      continue
    fi

    if our_stack_owns_port "$port"; then
      echo "    OK  :${port}  already ${PROJECT_NAME} (${label})"
      continue
    fi

    foreign=0
    for pid in $pids; do
      if ! is_docker_proxy_pid "$pid"; then
        foreign=1
        break
      fi
    done

    if [[ "$foreign" -eq 0 ]]; then
      echo "    FAIL :${port}  in use by another Docker publish (${label})" >&2
    else
      echo "    FAIL :${port}  in use by a host process (${label})" >&2
    fi
    describe_listeners "$port"
    blocked=1
  done

  if [[ "$blocked" -eq 1 ]]; then
    cat >&2 <<EOF

ERROR: Port conflict - refuse to start a half-broken stack.

Fix options:
  1) Free the port(s) above, then re-run ./tools/lab/docker/up.sh
  2) If host MCP/OpenAPI leftovers on ${MCP_PORT}/${API_DOCS_PORT}:
       ./tools/lab/docker/up.sh --kill-host-sidecars
  3) Stop a host Tomcat IIQ on :${IIQ_HTTP_PORT}:
       ./tools/lab/teardown-local.sh
  4) Full wipe + retry:
       ./tools/lab/docker/down.sh
       ./tools/lab/docker/up.sh

Do not mix host Tomcat IIQ with Docker MCP - MCP expects hostname 'identityiq'.
EOF
    exit 1
  fi
}

need_image_build() {
  local img
  if [[ "$FORCE_REBUILD" -eq 1 ]]; then
    return 0
  fi
  for img in "${LOCAL_IMAGES[@]}"; do
    if ! docker image inspect "$img" >/dev/null 2>&1; then
      return 0
    fi
  done
  return 1
}

wait_http() {
  local url="$1" label="$2" attempts="$3" delay="$4"
  local i
  for i in $(seq 1 "$attempts"); do
    if curl -sf -o /dev/null --connect-timeout 2 --max-time 5 "$url"; then
      echo "    OK  ${label}"
      return 0
    fi
    sleep "$delay"
  done
  echo "    FAIL ${label} - ${url}" >&2
  return 1
}

# Run several wait_http jobs in parallel; return 1 if any failed.
wait_http_parallel() {
  # Args: triples of url label attempts delay, separated by ---
  # Simpler: use background jobs with status files.
  local tmpdir status f
  tmpdir="$(mktemp -d)"
  local pids=()

  while [[ $# -ge 4 ]]; do
    local url="$1" label="$2" attempts="$3" delay="$4"
    shift 4
    (
      if wait_http "$url" "$label" "$attempts" "$delay"; then
        echo ok >"${tmpdir}/$(echo "$label" | tr -c 'A-Za-z0-9._-' '_')"
      else
        echo fail >"${tmpdir}/$(echo "$label" | tr -c 'A-Za-z0-9._-' '_')"
      fi
    ) &
    pids+=("$!")
  done

  local rc=0
  for pid in "${pids[@]+"${pids[@]}"}"; do
    wait "$pid" || rc=1
  done
  for f in "$tmpdir"/*; do
    [[ -f "$f" ]] || continue
    if [[ "$(cat "$f")" != "ok" ]]; then
      rc=1
    fi
  done
  rm -rf "$tmpdir"
  return "$rc"
}

verify_identityiq_container() {
  if ! docker ps --format '{{.Names}}' | grep -qx 'mnb-identityiq'; then
    cat >&2 <<'EOF'
ERROR: Container mnb-identityiq is not running.
MCP will fail with 'Name or service not known' for host 'identityiq'.
Check: docker compose -f docker-compose.iiq.yml ps
Logs:  docker compose -f docker-compose.iiq.yml logs --tail=80 identityiq
EOF
    exit 1
  fi
  local status
  status="$(docker inspect -f '{{.State.Health.Status}}' mnb-identityiq 2>/dev/null || echo unknown)"
  echo "    OK  mnb-identityiq container (${status})"
}

wait_ldap_helen() {
  local i
  for i in $(seq 1 30); do
    if docker exec mnb-openldap ldapsearch -x -H ldap://127.0.0.1:389 \
        -b dc=meridiannb,dc=com -D cn=admin,dc=meridiannb,dc=com -w admin \
        '(uid=helen.ross)' dn 2>/dev/null | grep -F 'uid=helen.ross' >/dev/null; then
      echo "    OK  OpenLDAP seed (helen.ross)"
      return 0
    fi
    sleep 1
  done
  echo "    FAIL OpenLDAP seed missing helen.ross" >&2
  echo "         Tip: ./tools/lab/docker/down.sh && ./tools/lab/docker/up.sh --rebuild" >&2
  return 1
}

wait_mcp_to_iiq() {
  local i
  for i in $(seq 1 20); do
    if docker ps --format '{{.Names}}' | grep -qx 'mnb-iiq-mcp' \
      && docker exec mnb-iiq-mcp python3 -c \
        "import urllib.request; urllib.request.urlopen('http://identityiq:8080/identityiq/login.jsf', timeout=3)" \
        >/dev/null 2>&1; then
      echo "    OK  MCP can reach identityiq"
      return 0
    fi
    sleep 1
  done
  echo "    FAIL MCP cannot reach http://identityiq:8080 (DNS or IIQ down)" >&2
  return 1
}

post_ready_checks() {
  local failed=0
  info "Verifying endpoints (parallel)..."
  verify_identityiq_container || failed=1

  # Independent HTTP probes in parallel
  wait_http_parallel \
    "http://127.0.0.1:${IIQ_HTTP_PORT}/identityiq/login.jsf" "IIQ_login" 40 2 \
    "http://127.0.0.1:${MCP_PORT}/healthz" "MCP" 40 2 \
    "http://127.0.0.1:${API_DOCS_PORT}/swagger/" "OpenAPI" 40 2 \
    "http://127.0.0.1:${CHAT_PORT}/api/config" "Teller" 40 2 \
    "http://127.0.0.1:${ACADEMY_PORT}/" "Academy" 40 2 \
    || failed=1

  # LDAP + MCP DNS probes in parallel
  local p1 p2
  wait_ldap_helen &
  p1=$!
  wait_mcp_to_iiq &
  p2=$!
  wait "$p1" || failed=1
  wait "$p2" || failed=1

  if [[ "$failed" -ne 0 ]]; then
    cat >&2 <<EOF
ERROR: Startup verification failed - stack is not E2E-ready.
  ${COMPOSE[*]} ps
  ${COMPOSE[*]} logs --tail=100 identityiq iiq-mcp openldap
EOF
    exit 1
  fi
}

PLUGIN_PKG_PID=""
PLUGIN_PKG_LOG="/tmp/mnb-plugin-package.log"

start_plugin_package_bg() {
  if [[ "$DO_SEED" -ne 1 ]]; then
    return 0
  fi
  # Skip packaging if a zip already exists and looks fresh enough; still package when missing.
  if [[ -f "$ROOT/pluginsrc/mnb-iam-toolkit/dist/mnb_iam_toolkit-1.3.6.zip" ]]; then
    info "Plugin zip present - will install after IIQ is up (skip background package)"
    return 0
  fi
  info "Packaging plugin in background while stack starts..."
  (
    ./pluginsrc/mnb-iam-toolkit/package.sh
  ) >"$PLUGIN_PKG_LOG" 2>&1 &
  PLUGIN_PKG_PID=$!
}

await_plugin_package_bg() {
  if [[ -n "${PLUGIN_PKG_PID}" ]]; then
    if ! wait "$PLUGIN_PKG_PID"; then
      tail -40 "$PLUGIN_PKG_LOG" >&2 || true
      die "Background plugin package failed (see $PLUGIN_PKG_LOG)"
    fi
    PLUGIN_PKG_PID=""
  fi
}

ensure_plugin_ready() {
  local base="http://127.0.0.1:${IIQ_HTTP_PORT}/identityiq"
  local user="${IIQ_USER:-spadmin}"
  local pass="${IIQ_PASSWORD:-admin}"
  local ping_code

  info "Ensuring Meridian Custom APIs plugin is installed + flags enabled..."
  await_plugin_package_bg

  ping_code="$(curl -sS -o /tmp/mnb-up-ping.json -w '%{http_code}' -u "${user}:${pass}" \
    -H 'Accept: application/json' "${base}/plugin/rest/mnbToolkit/ping" || true)"

  if [[ "$ping_code" != "200" ]]; then
    info "Plugin not reachable (http=${ping_code}) - installing mnb_iam_toolkit..."
    if [[ ! -f "$ROOT/pluginsrc/mnb-iam-toolkit/dist/mnb_iam_toolkit-1.3.6.zip" ]]; then
      ./pluginsrc/mnb-iam-toolkit/package.sh
    fi
    local pid
    pid="$(curl -sS -u "${user}:${pass}" -H 'Accept: application/json' -H 'X-Requested-With: XMLHttpRequest' \
      "${base}/rest/plugins" 2>/dev/null | python3 -c '
import json,sys
try:
  d=json.load(sys.stdin)
except Exception:
  raise SystemExit(0)
for p in (d.get("objects") or []):
  if p.get("name")=="mnb_iam_toolkit":
    print(p.get("id") or ""); break
' || true)"
    if [[ -n "${pid}" ]]; then
      curl -sS -o /dev/null -u "${user}:${pass}" -H 'X-Requested-With: XMLHttpRequest' \
        -X DELETE "${base}/rest/plugins/${pid}" || true
    fi
    ./pluginsrc/mnb-iam-toolkit/install.sh
  fi

  IIQ_BASE_URL="$base" IIQ_USER="$user" IIQ_PASSWORD="$pass" \
    ./pluginsrc/mnb-iam-toolkit/enable-settings.sh

  ping_code="$(curl -sS -o /tmp/mnb-up-ping.json -w '%{http_code}' -u "${user}:${pass}" \
    -H 'Accept: application/json' "${base}/plugin/rest/mnbToolkit/ping" || true)"
  if [[ "$ping_code" != "200" ]]; then
    die "Plugin ping failed after install (http=${ping_code}). See /tmp/mnb-up-ping.json"
  fi
  if ! python3 -c 'import json; d=json.load(open("/tmp/mnb-up-ping.json")); raise SystemExit(0 if d.get("agentReady") else 1)' 2>/dev/null; then
    die "Plugin installed but agentReady=false - check enable-settings.sh output"
  fi
  echo "    OK  plugin agentReady"
}

seed_lab_data() {
  local key="${MCP_API_KEY:-mnb-lab-mcp-key}"
  info "Seeding MNB-HR + MNB-OpenLDAP via MCP..."
  export IIQ_MCP_URL="http://127.0.0.1:${MCP_PORT}/mcp"
  export MCP_API_KEY="$key"
  ./tools/lab/scripts/seed-mnb-lab-data.sh
}

print_ready() {
  local MCP_KEY="${MCP_API_KEY:-mnb-lab-mcp-key}"
  echo
  echo "Ready."
  echo "  Academy:  http://localhost:${ACADEMY_PORT}/"
  echo "  IIQ:      http://localhost:${IIQ_HTTP_PORT}/identityiq  (spadmin / admin)"
  echo "  OpenAPI:  http://localhost:${API_DOCS_PORT}/swagger/"
  echo "  MCP:      http://127.0.0.1:${MCP_PORT}/mcp"
  echo "            Authorization: Bearer ${MCP_KEY}"
  echo "  Teller:   http://localhost:${CHAT_PORT}/  (IIQ chatbot)"
  if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
    echo "            Tip: export OPENROUTER_API_KEY=... for free-text LLM chat"
  fi
  echo "  OpenLDAP: ldap://localhost:${LDAP_PORT}"
  echo "            bind cn=admin,dc=meridiannb,dc=com / admin"
  if [[ "$DO_SEED" -eq 1 ]]; then
    echo "  Seed:     MNB-HR + MNB-OpenLDAP (ran during up)"
  else
    echo
    echo "Next (seed skipped):"
    echo "  ./pluginsrc/mnb-iam-toolkit/enable-settings.sh"
    echo "  MCP_API_KEY=${MCP_KEY} ./tools/lab/scripts/seed-mnb-lab-data.sh"
  fi
  echo
  echo "Stop/wipe:  ./tools/lab/docker/down.sh"
  echo "Keep data:  ./tools/lab/docker/down.sh --keep-volumes"
}

# --- main ---
require_docker

if [[ -z "${IIQ_IMAGE:-}" ]]; then
  if docker image inspect mnb-identityiq:local >/dev/null 2>&1; then
    export IIQ_IMAGE=mnb-identityiq:local
  fi
fi

if [[ "$KILL_HOST_SIDECARS" -eq 1 ]]; then
  maybe_kill_host_sidecars
fi

preflight_ports

if [[ "$CHECK_ONLY" -eq 1 ]]; then
  echo "Preflight OK (ports free or owned by ${PROJECT_NAME})."
  exit 0
fi

# Overlap: package plugin while compose brings services up
start_plugin_package_bg

info "Starting Meridian stack (IIQ + OpenLDAP + Academy + MCP + OpenAPI + Teller)"
echo "    IIQ_IMAGE=${IIQ_IMAGE:-ghcr.io/beyond-boilerplate/identityiq:0.1.0}"
if need_image_build; then
  if [[ "$FORCE_REBUILD" -eq 1 ]]; then
    info "Building images (--rebuild)..."
  else
    info "Building missing local images..."
  fi
  "${COMPOSE[@]}" up -d --build
else
  info "Local images present - starting without rebuild (pass --rebuild to force)"
  "${COMPOSE[@]}" up -d
fi

info "Waiting for IdentityIQ login..."
# Poll IIQ while other services come up; full parallel verify follows bootstrap
if ! wait_http "http://127.0.0.1:${IIQ_HTTP_PORT}/identityiq/login.jsf" "IIQ login" 90 3; then
  await_plugin_package_bg || true
  cat >&2 <<EOF
ERROR: IIQ login page not up on :${IIQ_HTTP_PORT} after wait
  ${COMPOSE[*]} logs --tail=120 identityiq
EOF
  exit 1
fi
verify_identityiq_container

info "Bootstrapping IIQ (init + HelloWorld)..."
IIQ_BOOTSTRAP_SKIP_WAIT=1 ./tools/lab/docker/bootstrap.sh

post_ready_checks

if [[ "$DO_SEED" -eq 1 ]]; then
  ensure_plugin_ready
  seed_lab_data
fi

print_ready
