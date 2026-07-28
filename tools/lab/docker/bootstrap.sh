#!/usr/bin/env bash
# First-boot imports for Docker IIQ lab (init + LCM + HelloWorld smoke).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"
COMPOSE=(docker compose -f docker-compose.iiq.yml)

echo "Waiting for identityiq container healthy…"
for _ in $(seq 1 60); do
  st="$("${COMPOSE[@]}" ps --format json identityiq 2>/dev/null | head -1 || true)"
  if echo "$st" | grep -qi healthy; then
    break
  fi
  # fallback: HTTP login page
  if curl -sf -o /dev/null "http://127.0.0.1:${IIQ_HTTP_PORT:-8080}/identityiq/login.jsf"; then
    break
  fi
  sleep 5
done

echo "Importing stock init + LCM (idempotent-ish)…"
"${COMPOSE[@]}" exec -T identityiq sh -c '
  cd "$IIQ_HOME/WEB-INF/bin"
  chmod +x iiq 2>/dev/null || true
  ./iiq console iiqBeans <<EOF
import $IIQ_HOME/WEB-INF/config/init.xml
import $IIQ_HOME/WEB-INF/config/init-lcm.xml
EOF
' || echo "WARN: init import returned non-zero (may already be imported)"

if [[ -f "$ROOT/config/Rule/MNB-Rule-HelloWorld.xml" ]]; then
  echo "Importing Meridian HelloWorld smoke Rule…"
  "${COMPOSE[@]}" cp "$ROOT/config/Rule/MNB-Rule-HelloWorld.xml" identityiq:/tmp/MNB-Rule-HelloWorld.xml
  "${COMPOSE[@]}" exec -T identityiq sh -c '
    cd "$IIQ_HOME/WEB-INF/bin"
    ./iiq console iiqBeans <<EOF
import /tmp/MNB-Rule-HelloWorld.xml
EOF
  '
fi

echo "Bootstrap done. Login http://localhost:${IIQ_HTTP_PORT:-8080}/identityiq"
echo "Verify smoke: IIQ_BASE_URL=http://localhost:${IIQ_HTTP_PORT:-8080}/identityiq ./tools/iiq-verify/verify-lesson.sh 03"
