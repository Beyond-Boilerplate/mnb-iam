#!/usr/bin/env bash
# First-boot imports for Docker IIQ lab (init + LCM + HelloWorld smoke).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"
COMPOSE=(docker compose -f docker-compose.iiq.yml)
PORT="${IIQ_HTTP_PORT:-8080}"

echo "Waiting for identityiq…"
if [[ "${IIQ_BOOTSTRAP_SKIP_WAIT:-}" == "1" ]] \
  && curl -sf -o /dev/null "http://127.0.0.1:${PORT}/identityiq/login.jsf"; then
  echo "Login already up — skipping wait loop."
else
  for _ in $(seq 1 90); do
    if curl -sf -o /dev/null "http://127.0.0.1:${PORT}/identityiq/login.jsf"; then
      break
    fi
    sleep 5
  done
fi

if ! curl -sf -o /dev/null "http://127.0.0.1:${PORT}/identityiq/login.jsf"; then
  echo "ERROR: IIQ login page not reachable on :${PORT}" >&2
  "${COMPOSE[@]}" ps || true
  exit 1
fi

echo "Importing stock init + LCM…"
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
  ' || echo "WARN: HelloWorld import failed"
fi

echo "Bootstrap done."
