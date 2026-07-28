#!/usr/bin/env bash
# Assert CD smoke objects exist (HelloWorld only). Learners build the rest in lessons.
# Usage:
#   ./tools/iiq-verify/assert-mnb-objects.sh local
#   ./tools/iiq-verify/assert-mnb-objects.sh k8s
set -euo pipefail

MODE="${1:-local}"
NS="${NAMESPACE:-sailpoint}"
DEPLOY="${IIQ_DEPLOYMENT:-identityiq}"

OBJECTS=(
  "MNB-Rule-Hello-World|Rule"
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
echo "Asserting Meridian CD smoke objects (mode=${MODE})…"
for row in "${OBJECTS[@]}"; do
  IFS='|' read -r name clazz <<<"$row"
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
  echo "CD smoke object(s) missing after import." >&2
  exit 1
fi
echo "CD smoke assert passed (HelloWorld). Academy apps/tasks are learner-built."
