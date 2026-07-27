#!/usr/bin/env bash
# Assert Meridian academy objects exist in a running IIQ (console or kubectl exec).
# Usage:
#   Local (IIQ console on PATH / IIQ_HOME):
#     ./tools/iiq-verify/assert-mnb-objects.sh local
#   Homelab pod:
#     ./tools/iiq-verify/assert-mnb-objects.sh k8s
set -euo pipefail

MODE="${1:-local}"
NS="${NAMESPACE:-sailpoint}"
DEPLOY="${IIQ_DEPLOYMENT:-identityiq}"

# Object name | IIQ class simple name for console get
OBJECTS=(
  "MNB-Rule-Hello-World|Rule"
  "MNB-HR|Application"
  "MNB-IT-Access|Application"
  "MNB-CoreBanking|Application"
  "MNB-WirePortal|Application"
  "MNB-SAP-Finance|Application"
  "MNB-AWS-Cloud|Application"
  "Aggregate MNB-HR|TaskDefinition"
  "Refresh MNB Attributes|TaskDefinition"
  "Refresh MNB Managers|TaskDefinition"
  "Refresh MNB Roles|TaskDefinition"
  "Refresh MNB Policies|TaskDefinition"
  "Aggregate MNB-IT-Access|TaskDefinition"
  "MNB-HR EmployeeId Correlation|CorrelationConfig"
  "MNB-Rule-Correlation-EmployeeId|Rule"
  "MNB-Role-Birthright-Employee|Bundle"
  "MNB-Role-IT-Directory-User|Bundle"
  "MNB-Workflow-Joiner|Workflow"
  "MNB-Workflow-Leaver|Workflow"
  "MNB-EmailTemplate-Joiner-Notify|EmailTemplate"
  "MNB-SOD-Wire-Dual-Control|Policy"
)

run_console() {
  local cmd="$1"
  if [[ "$MODE" == "k8s" ]]; then
    local pod
    pod="$(kubectl -n "$NS" get pod -l "app.kubernetes.io/name=${DEPLOY}" -o jsonpath='{.items[0].metadata.name}')"
    kubectl -n "$NS" exec "$pod" -c identityiq -- sh -c "
      cd /usr/local/tomcat/webapps/identityiq/WEB-INF/bin
      chmod +x iiq 2>/dev/null || true
      ./iiq console iiqBeans -c \"$cmd\"
    "
  else
    local bin="${IIQ_HOME:-}/WEB-INF/bin/iiq"
    if [[ ! -x "$bin" ]]; then
      echo "ERROR: set IIQ_HOME to the exploded identityiq webapp (iiq console not found)" >&2
      exit 1
    fi
    ( cd "$(dirname "$bin")" && ./iiq console iiqBeans -c "$cmd" )
  fi
}

fail=0
echo "Asserting Meridian academy objects (mode=${MODE})…"
for row in "${OBJECTS[@]}"; do
  IFS='|' read -r name clazz <<<"$row"
  # Console: get <Class> <name> — empty/missing surfaces as error text
  out="$(run_console "get ${clazz} \"${name}\"" 2>&1 || true)"
  if echo "$out" | grep -qiE "no object|not found|could not|Unknown|ERROR"; then
    echo "FAIL: ${clazz} '${name}'"
    fail=1
  elif [[ -z "${out// }" ]]; then
    echo "FAIL: ${clazz} '${name}' (empty response)"
    fail=1
  else
    echo "OK:   ${clazz} '${name}'"
  fi
done

if [[ "$fail" -ne 0 ]]; then
  echo "One or more Meridian objects missing after import." >&2
  exit 1
fi
echo "All asserted Meridian academy objects present."
