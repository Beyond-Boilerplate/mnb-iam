#!/usr/bin/env bash
# Wipe leftover Meridian academy objects/identities from a running IIQ
# (keeps spadmin + MNB-Rule-Hello-World). For UI-first clean lab.
# Usage:
#   ./tools/iiq-verify/wipe-mnb-leftovers.sh local
#   ./tools/iiq-verify/wipe-mnb-leftovers.sh k8s
set -euo pipefail

MODE="${1:-local}"
NS="${NAMESPACE:-sailpoint}"
DEPLOY="${IIQ_DEPLOYMENT:-identityiq}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RULE_XML="${ROOT}/tools/iiq-verify/MNB-Rule-E2E-WipeAcademy.xml"

if [[ ! -f "$RULE_XML" ]]; then
  echo "ERROR: missing ${RULE_XML}" >&2
  exit 1
fi

echo "Wiping Meridian academy leftovers (mode=${MODE})…"
echo "Keeps: spadmin, MNB-Rule-Hello-World"

if [[ "$MODE" == "k8s" ]]; then
  POD="$(kubectl -n "$NS" get pod -l "app.kubernetes.io/name=${DEPLOY}" -o jsonpath='{.items[0].metadata.name}')"
  if [[ -z "$POD" ]]; then
    echo "ERROR: no identityiq pod in ${NS}" >&2
    exit 1
  fi
  kubectl -n "$NS" cp "$RULE_XML" "${POD}:/tmp/MNB-Rule-E2E-WipeAcademy.xml" -c identityiq
  kubectl -n "$NS" exec "$POD" -c identityiq -- sh -c '
    cd /usr/local/tomcat/webapps/identityiq/WEB-INF/bin
    chmod +x iiq 2>/dev/null || true
    ./iiq console iiqBeans <<EOF
import /tmp/MNB-Rule-E2E-WipeAcademy.xml
rule MNB-Rule-E2E-WipeAcademy
EOF
  '
else
  bin="${IIQ_HOME:-}/WEB-INF/bin/iiq"
  if [[ ! -x "$bin" ]]; then
    echo "ERROR: set IIQ_HOME to exploded identityiq webapp" >&2
    exit 1
  fi
  (
    cd "$(dirname "$bin")"
    ./iiq console iiqBeans <<EOF
import ${RULE_XML}
rule MNB-Rule-E2E-WipeAcademy
EOF
  )
fi

echo "Wipe finished. Spot-check: only spadmin (+ HelloWorld) should remain from Meridian lab."
