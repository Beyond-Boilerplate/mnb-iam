#!/usr/bin/env bash
# Deploy Meridian IAM Academy + path-split edge for sailpoint.lmsapp.us
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
NS="${NAMESPACE:-sailpoint}"
if [[ "${GITHUB_ACTIONS:-}" == "true" && -z "${LEARN_IMAGE_TAG:-}" ]]; then
  echo "ERROR: CI must provide an immutable LEARN_IMAGE_TAG" >&2
  exit 1
fi
LEARN_TAG="${LEARN_IMAGE_TAG:-latest}"
OWNER="$(tr '[:upper:]' '[:lower:]' <<<"${GHCR_OWNER:-beyond-boilerplate}")"
IMAGE="ghcr.io/${OWNER}/mnb-iam-learn:${LEARN_TAG}"

kubectl get ns "$NS" >/dev/null 2>&1 || kubectl create namespace "$NS"

echo "Applying mnb-learn (${IMAGE}) + sailpoint-edge…"
# Render the selected image into the manifest before apply. Applying :latest and
# immediately changing it caused an unnecessary intermediate rollout.
PULL_POLICY="IfNotPresent"
[[ "$LEARN_TAG" == "latest" ]] && PULL_POLICY="Always"
sed \
  -e "s#image: ghcr.io/beyond-boilerplate/mnb-iam-learn:latest#image: ${IMAGE}#" \
  -e "s#imagePullPolicy: Always#imagePullPolicy: ${PULL_POLICY}#" \
  "$ROOT/learn/k8s/learn-static.yaml" \
  | kubectl -n "$NS" apply -f -
kubectl -n "$NS" apply -f "$ROOT/learn/k8s/edge-gateway.yaml"

# ConfigMap volumes update eventually, but nginx does not reload itself. Roll
# the edge only when its checked-in configuration changes.
if command -v sha256sum >/dev/null 2>&1; then
  EDGE_CONFIG_HASH="$(sha256sum "$ROOT/learn/k8s/edge-gateway.yaml" | awk '{print $1}')"
else
  EDGE_CONFIG_HASH="$(shasum -a 256 "$ROOT/learn/k8s/edge-gateway.yaml" | awk '{print $1}')"
fi
kubectl -n "$NS" patch deployment sailpoint-edge --type=merge \
  --patch "{\"spec\":{\"template\":{\"metadata\":{\"annotations\":{\"academy.meridiannb.com/edge-config\":\"${EDGE_CONFIG_HASH}\"}}}}}"

if ! kubectl -n "$NS" rollout status deploy/mnb-learn --timeout=5m; then
  kubectl -n "$NS" get pods,deploy,svc -o wide || true
  kubectl -n "$NS" describe deploy/mnb-learn || true
  exit 1
fi
if ! kubectl -n "$NS" rollout status deploy/sailpoint-edge --timeout=3m; then
  kubectl -n "$NS" get pods,deploy,svc -o wide || true
  kubectl -n "$NS" describe deploy/sailpoint-edge || true
  exit 1
fi

echo "Public surface ready."
echo "  Academy:     https://sailpoint.lmsapp.us/"
echo "  IdentityIQ:  https://sailpoint.lmsapp.us/identityiq/login.jsf"
echo "Cloudflare Tunnel URL must be: sailpoint-edge.sailpoint.svc.cluster.local:8080"
