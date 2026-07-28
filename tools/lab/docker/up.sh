#!/usr/bin/env bash
# Start local IIQ via Docker Compose (alternative to tools/lab Tomcat path).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

if [[ -z "${IIQ_IMAGE:-}" ]]; then
  if docker image inspect mnb-identityiq:local >/dev/null 2>&1; then
    export IIQ_IMAGE=mnb-identityiq:local
  fi
fi

echo "Using IIQ_IMAGE=${IIQ_IMAGE:-ghcr.io/beyond-boilerplate/identityiq:0.1.0}"
echo "Lab CSV mount: ${ROOT}/lab-data → /opt/iiq-lab-data"
docker compose -f docker-compose.iiq.yml up -d
echo
echo "Wait for health, then run: ./tools/lab/docker/bootstrap.sh"
echo "UI: http://localhost:${IIQ_HTTP_PORT:-8080}/identityiq  (spadmin / admin)"
