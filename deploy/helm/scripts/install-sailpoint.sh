#!/usr/bin/env bash
# Install / upgrade the sailpoint umbrella into namespace `sailpoint`.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VALUES="${1:-$ROOT/values/local-homelab.yaml}"
NS="${NAMESPACE:-sailpoint}"
RELEASE="${RELEASE_NAME:-sailpoint}"

kubectl get ns "$NS" >/dev/null 2>&1 || kubectl create namespace "$NS"

if helm -n "$NS" status "$RELEASE" >/dev/null 2>&1; then
  REL_STATUS="$(helm -n "$NS" status "$RELEASE" -o json | jq -r '.info.status // empty')"
  echo "Current Helm release status: ${REL_STATUS:-unknown}"
  case "$REL_STATUS" in
    pending-install|pending-upgrade|pending-rollback)
      echo "Clearing stuck Helm operation (${REL_STATUS})…"
      kubectl -n "$NS" get secrets -l "owner=helm,name=${RELEASE}" -o json \
        | jq -r --arg st "$REL_STATUS" \
          '.items[] | select(.metadata.labels.status==$st) | .metadata.name' \
        | while read -r sec; do
            [[ -n "$sec" ]] && kubectl -n "$NS" delete secret "$sec" --wait=true
          done
      ;;
  esac
fi

# Clear failed schema hook jobs that can block upgrades
kubectl -n "$NS" delete job sailpoint-pg-schema-init --ignore-not-found --wait=false || true

"$ROOT/scripts/update-deps.sh"

shift || true

HELM_ARGS=(
  upgrade --install "$RELEASE" "$ROOT/charts/sailpoint"
  --namespace "$NS"
  --create-namespace
  -f "$VALUES"
  --timeout "${HELM_TIMEOUT:-15m}"
  --wait
)
if [[ "${HELM_ATOMIC:-false}" == "true" ]]; then
  HELM_ARGS+=(--atomic)
fi

SECRETS_FILE="${VALUES%.yaml}.secrets.yaml"
if [[ -f "$SECRETS_FILE" ]]; then
  echo "Using secrets overlay: $SECRETS_FILE"
  HELM_ARGS+=(-f "$SECRETS_FILE")
fi

# Pin app image when IMAGE_TAG is set (CI after Publish GHCR)
if [[ -n "${IMAGE_TAG:-}" ]]; then
  echo "Pinning identityiq.image.tag=${IMAGE_TAG}"
  HELM_ARGS+=(--set-string "identityiq.image.tag=${IMAGE_TAG}")
  if [[ "${VERIFY_IMAGE_TAGS:-}" == "true" ]]; then
    OWNER="${GHCR_OWNER:-beyond-boilerplate}"
    MANIFEST="ghcr.io/${OWNER}/identityiq:${IMAGE_TAG}"
    echo "Verifying GHCR manifest exists: ${MANIFEST}"
    if command -v docker >/dev/null 2>&1; then
      docker buildx imagetools inspect "$MANIFEST" >/dev/null
    elif command -v crane >/dev/null 2>&1; then
      crane manifest "$MANIFEST" >/dev/null
    else
      echo "WARNING: neither docker nor crane available — skipping manifest verify" >&2
    fi
  fi
elif [[ "${GITHUB_ACTIONS:-}" == "true" ]]; then
  echo "ERROR: CI deploy requires IMAGE_TAG — refusing values-file default" >&2
  exit 1
fi

if [[ "$#" -gt 0 ]]; then
  HELM_ARGS+=("$@")
fi

helm "${HELM_ARGS[@]}"

echo "Release ${RELEASE} installed in $NS"
kubectl -n "$NS" get pods,svc,jobs,cluster 2>/dev/null || kubectl -n "$NS" get pods,svc,jobs
