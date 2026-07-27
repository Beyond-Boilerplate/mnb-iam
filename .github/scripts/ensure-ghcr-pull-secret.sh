#!/usr/bin/env bash
# Create or rotate the cluster's long-lived GHCR pull secret without a delete gap.
set -euo pipefail

NAMESPACE="${NAMESPACE:-sailpoint}"
SECRET_NAME="${GHCR_PULL_SECRET_NAME:-ghcr-pull}"
TOKEN="${GHCR_PULL_TOKEN:-${GHCR_READ_TOKEN:-}}"
USERNAME="${GHCR_USERNAME:-}"

kubectl get namespace "$NAMESPACE" >/dev/null 2>&1 || kubectl create namespace "$NAMESPACE"

if [[ -z "$TOKEN" ]]; then
  if kubectl -n "$NAMESPACE" get secret "$SECRET_NAME" >/dev/null 2>&1; then
    echo "No long-lived GHCR token supplied; preserving existing ${NAMESPACE}/${SECRET_NAME}."
    exit 0
  fi
  echo "::error::${NAMESPACE}/${SECRET_NAME} is missing and no GHCR_PULL_TOKEN or GHCR_READ_TOKEN was supplied."
  echo "Use a long-lived read:packages token; a job-scoped GITHUB_TOKEN expires after CI finishes."
  exit 1
fi

if [[ -z "$USERNAME" ]]; then
  echo "::error::GHCR_USERNAME is required when creating ${NAMESPACE}/${SECRET_NAME}."
  exit 1
fi

kubectl -n "$NAMESPACE" create secret docker-registry "$SECRET_NAME" \
  --docker-server=ghcr.io \
  --docker-username="$USERNAME" \
  --docker-password="$TOKEN" \
  --dry-run=client \
  --output=yaml \
  | kubectl apply -f -

echo "Ensured ${NAMESPACE}/${SECRET_NAME} without deleting the live secret."
