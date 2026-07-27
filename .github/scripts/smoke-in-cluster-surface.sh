#!/usr/bin/env bash
# Verify path routing from inside the cluster and emit useful Kubernetes diagnostics.
set -euo pipefail

NAMESPACE="${NAMESPACE:-sailpoint}"
EDGE_URL="${EDGE_URL:-http://sailpoint-edge:8080}"
CURL_IMAGE="${CURL_IMAGE:-curlimages/curl:8.12.1}"
ACADEMY_PATTERN="${ACADEMY_PATTERN:-Meridian|IAM Academy|Curriculum}"
IIQ_ATTEMPTS="${IIQ_ATTEMPTS:-18}"
IIQ_INTERVAL_SECONDS="${IIQ_INTERVAL_SECONDS:-10}"
POD_NAME="surface-smoke-${GITHUB_RUN_ID:-local}-${GITHUB_RUN_ATTEMPT:-1}"
POD_NAME="${POD_NAME:0:63}"

cleanup() {
  kubectl -n "$NAMESPACE" delete pod "$POD_NAME" --ignore-not-found --wait=false >/dev/null 2>&1 || true
}

diagnose() {
  echo "---- in-cluster surface diagnostics ----"
  kubectl -n "$NAMESPACE" get deploy,pods,svc,endpoints -o wide 2>/dev/null || true
  kubectl -n "$NAMESPACE" describe pod -l app.kubernetes.io/name=identityiq 2>/dev/null || true
  kubectl -n "$NAMESPACE" logs deploy/sailpoint-edge --tail=100 2>/dev/null || true
  kubectl -n "$NAMESPACE" logs deploy/identityiq --tail=80 2>/dev/null || true
  echo "----------------------------------------"
}

trap cleanup EXIT
cleanup

kubectl -n "$NAMESPACE" run "$POD_NAME" \
  --restart=Never \
  --image="$CURL_IMAGE" \
  --command -- sleep 300
kubectl -n "$NAMESPACE" wait --for=condition=Ready "pod/${POD_NAME}" --timeout=60s

ACADEMY_BODY=$(kubectl -n "$NAMESPACE" exec "$POD_NAME" -- \
  curl --fail --silent --show-error --max-time 15 "${EDGE_URL}/") || {
  diagnose
  exit 1
}
if ! grep -qiE "$ACADEMY_PATTERN" <<<"$ACADEMY_BODY"; then
  echo "::error::sailpoint-edge / did not return academy content"
  diagnose
  exit 1
fi

IIQ_CODE="000"
for ((attempt = 1; attempt <= IIQ_ATTEMPTS; attempt++)); do
  IIQ_CODE=$(kubectl -n "$NAMESPACE" exec "$POD_NAME" -- \
    curl --silent --show-error --output /dev/null --write-out '%{http_code}' --max-time 30 \
    "${EDGE_URL}/identityiq/login.jsf") || IIQ_CODE="000"
  echo "IdentityIQ through edge attempt ${attempt}/${IIQ_ATTEMPTS}: HTTP ${IIQ_CODE}"
  if [[ "$IIQ_CODE" =~ ^(200|301|302|303)$ ]]; then
    echo "In-cluster academy and IdentityIQ path routing is healthy."
    exit 0
  fi
  if ((attempt < IIQ_ATTEMPTS)); then
    sleep "$IIQ_INTERVAL_SECONDS"
  fi
done

echo "::error::sailpoint-edge /identityiq returned HTTP ${IIQ_CODE} after ${IIQ_ATTEMPTS} attempts"
diagnose
exit 1
