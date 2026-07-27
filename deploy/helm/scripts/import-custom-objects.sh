#!/usr/bin/env bash
# Import SSB custom objects (WEB-INF/config/sp.init-custom.xml) into a running IIQ pod.
# XML in the image filesystem does NOT become Debug objects until imported into the DB.
set -euo pipefail
NS="${NAMESPACE:-sailpoint}"
DEPLOY="${IIQ_DEPLOYMENT:-identityiq}"

POD="$(kubectl -n "$NS" get pod -l "app.kubernetes.io/name=${DEPLOY}" -o jsonpath='{.items[0].metadata.name}')"
if [[ -z "$POD" ]]; then
  echo "ERROR: no IdentityIQ pod in ${NS}" >&2
  exit 1
fi

echo "Waiting for IdentityIQ HTTP on ${POD}…"
for _ in $(seq 1 60); do
  if kubectl -n "$NS" exec "$POD" -c identityiq -- \
    sh -c 'wget -q -O /dev/null --timeout=3 http://127.0.0.1:8080/identityiq/login.jsf' 2>/dev/null; then
    break
  fi
  sleep 5
done

INIT_XML="/usr/local/tomcat/webapps/identityiq/WEB-INF/config/sp.init-custom.xml"
RULE_CHECK="/usr/local/tomcat/webapps/identityiq/WEB-INF/config/custom/Rule"

echo "Custom Rule files in image:"
kubectl -n "$NS" exec "$POD" -c identityiq -- sh -c "ls -la ${RULE_CHECK} 2>/dev/null || echo '(none yet)'"

echo "Importing ${INIT_XML} via iiq console (iiqBeans)…"
kubectl -n "$NS" exec "$POD" -c identityiq -- sh -c "
  set -e
  cd /usr/local/tomcat/webapps/identityiq/WEB-INF/bin
  chmod +x iiq 2>/dev/null || true
  ./iiq console iiqBeans -c \"import '${INIT_XML}'\"
"

echo "Custom object import finished."
