#!/usr/bin/env bash
# One command: Postgres + OpenLDAP + IdentityIQ + Academy + MCP + OpenAPI docs.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"
COMPOSE=(docker compose -f docker-compose.iiq.yml)

if [[ -z "${IIQ_IMAGE:-}" ]]; then
  if docker image inspect mnb-identityiq:local >/dev/null 2>&1; then
    export IIQ_IMAGE=mnb-identityiq:local
  fi
fi

# Free host ports if a previous host-path MCP / OpenAPI is still bound
for port in "${MCP_PORT:-8766}" "${API_DOCS_PORT:-8765}"; do
  pids="$(lsof -nP -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null || true)"
  if [[ -n "$pids" ]]; then
    # Only stop non-docker listeners (docker-proxy keeps the compose mapping)
    for pid in $pids; do
      cmd="$(ps -p "$pid" -o comm= 2>/dev/null || true)"
      if [[ "$cmd" == *docker* || "$cmd" == *com.docke* ]]; then
        continue
      fi
      echo "==> Stopping host process on :${port} (pid $pid, $cmd) so Compose can bind"
      kill "$pid" 2>/dev/null || true
    done
  fi
done

echo "==> Starting Meridian stack (IIQ + OpenLDAP + Academy + MCP + OpenAPI)"
echo "    IIQ_IMAGE=${IIQ_IMAGE:-ghcr.io/beyond-boilerplate/identityiq:0.1.0}"
"${COMPOSE[@]}" up -d --build

echo "==> Waiting for IdentityIQ login page…"
for _ in $(seq 1 90); do
  if curl -sf -o /dev/null "http://127.0.0.1:${IIQ_HTTP_PORT:-8080}/identityiq/login.jsf"; then
    break
  fi
  sleep 5
done

echo "==> Bootstrapping IIQ (init + HelloWorld)…"
./tools/lab/docker/bootstrap.sh

echo "==> Waiting for MCP + OpenAPI + Teller + OpenLDAP…"
for _ in $(seq 1 40); do
  mcp_ok=0
  docs_ok=0
  chat_ok=0
  ldap_ok=0
  curl -sf -o /dev/null "http://127.0.0.1:${MCP_PORT:-8766}/healthz" && mcp_ok=1 || true
  curl -sf -o /dev/null "http://127.0.0.1:${API_DOCS_PORT:-8765}/swagger/" && docs_ok=1 || true
  curl -sf -o /dev/null "http://127.0.0.1:${CHAT_PORT:-4180}/api/config" && chat_ok=1 || true
  if docker exec mnb-openldap ldapsearch -x -H ldap://127.0.0.1:389 \
      -b dc=meridiannb,dc=com -D cn=admin,dc=meridiannb,dc=com -w admin \
      '(uid=helen.ross)' dn 2>/dev/null | grep -q 'uid=helen.ross'; then
    ldap_ok=1
  fi
  if [[ "$mcp_ok" -eq 1 && "$docs_ok" -eq 1 && "$chat_ok" -eq 1 && "$ldap_ok" -eq 1 ]]; then
    break
  fi
  sleep 2
done

MCP_KEY="${MCP_API_KEY:-mnb-lab-mcp-key}"

echo
echo "Ready."
echo "  Academy:  http://localhost:${ACADEMY_PORT:-4173}/"
echo "  IIQ:      http://localhost:${IIQ_HTTP_PORT:-8080}/identityiq  (spadmin / admin)"
echo "  OpenAPI:  http://localhost:${API_DOCS_PORT:-8765}/swagger/"
echo "  MCP:      http://127.0.0.1:${MCP_PORT:-8766}/mcp"
echo "            Authorization: Bearer ${MCP_KEY}"
echo "  Teller:   http://localhost:${CHAT_PORT:-4180}/  (IIQ chatbot)"
if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
  echo "            Tip: export OPENROUTER_API_KEY=… for free-text LLM chat"
fi
echo "  OpenLDAP: ldap://localhost:${LDAP_PORT:-389}"
echo "            bind cn=admin,dc=meridiannb,dc=com / admin"
echo "            IIQ host from container network: openldap:389"
echo "            Seed: lab-data/connectors/ldap/ (see README)"
echo "  Lab data: /opt/iiq-lab-data inside IIQ (repo lab-data/)"
echo
echo "Cursor / Claude: register HTTP MCP → http://127.0.0.1:${MCP_PORT:-8766}/mcp"
echo "  (header Authorization: Bearer ${MCP_KEY})"
echo
echo "Open Academy → Lesson 01 → Lesson verify → Verify now"
echo "Stop:  ./tools/lab/docker/down.sh"
echo "Wipe:  ./tools/lab/docker/down.sh -v"
