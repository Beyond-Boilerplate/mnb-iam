#!/usr/bin/env bash
# Deploy Meridian IAM Academy + path-split edge for sailpoint.lmsapp.us
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
NS="${NAMESPACE:-sailpoint}"
LEARN_TAG="${LEARN_IMAGE_TAG:-latest}"
IMAGE="ghcr.io/beyond-boilerplate/mnb-iam-learn:${LEARN_TAG}"

kubectl get ns "$NS" >/dev/null 2>&1 || kubectl create namespace "$NS"

echo "Applying mnb-learn (${IMAGE}) + sailpoint-edge…"
kubectl -n "$NS" apply -f "$ROOT/learn/k8s/learn-static.yaml"
kubectl -n "$NS" apply -f "$ROOT/learn/k8s/edge-gateway.yaml"

# Pin image tag when CI provides LEARN_IMAGE_TAG / sha
kubectl -n "$NS" set image deploy/mnb-learn "nginx=${IMAGE}"
kubectl -n "$NS" rollout status deploy/mnb-learn --timeout=5m
kubectl -n "$NS" rollout status deploy/sailpoint-edge --timeout=3m

echo "Public surface ready."
echo "  Academy:     https://sailpoint.lmsapp.us/"
echo "  IdentityIQ:  https://sailpoint.lmsapp.us/identityiq/login.jsf"
echo "Cloudflare Tunnel URL must be: sailpoint-edge.sailpoint.svc.cluster.local:8080"
