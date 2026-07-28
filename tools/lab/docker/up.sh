#!/usr/bin/env bash
# One command: Postgres + IdentityIQ + Academy (lessons + Verify now).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"
COMPOSE=(docker compose -f docker-compose.iiq.yml)

if [[ -z "${IIQ_IMAGE:-}" ]]; then
  if docker image inspect mnb-identityiq:local >/dev/null 2>&1; then
    export IIQ_IMAGE=mnb-identityiq:local
  fi
fi

echo "==> Starting Meridian stack (IIQ + Academy)"
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

echo
echo "Ready."
echo "  Academy:  http://localhost:${ACADEMY_PORT:-4173}/"
echo "  IIQ:      http://localhost:${IIQ_HTTP_PORT:-8080}/identityiq  (spadmin / admin)"
echo "  Lab data: /opt/iiq-lab-data inside IIQ (repo lab-data/)"
echo
echo "Open Academy → Lesson 01 → Lesson verify → Verify now"
echo "Stop:  ./tools/lab/docker/down.sh"
echo "Wipe:  ./tools/lab/docker/down.sh -v"
