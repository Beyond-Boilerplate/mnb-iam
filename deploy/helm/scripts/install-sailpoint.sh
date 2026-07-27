#!/usr/bin/env bash
# Install / upgrade the sailpoint umbrella into namespace `sailpoint`.
#
# Phased for first-boot speed & diagnosis:
#   1) data plane (CNPG + schema hook) with --wait
#   2) app (IdentityIQ) with --wait
# Progress dumps avoid silent 15m hangs.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VALUES="${1:-$ROOT/values/local-homelab.yaml}"
NS="${NAMESPACE:-sailpoint}"
RELEASE="${RELEASE_NAME:-sailpoint}"
PHASE="${INSTALL_PHASE:-all}" # all | data | app

kubectl get ns "$NS" >/dev/null 2>&1 || kubectl create namespace "$NS"

dump_status() {
  echo "---- cluster status ($NS) ----"
  kubectl -n "$NS" get pods,pvc,jobs,svc 2>/dev/null || true
  kubectl -n "$NS" get cluster 2>/dev/null || true
  kubectl -n "$NS" get events --sort-by=.lastTimestamp 2>/dev/null | tail -15 || true
  echo "------------------------------"
}

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

kubectl -n "$NS" delete job sailpoint-pg-schema-init --ignore-not-found --wait=false || true

"$ROOT/scripts/update-deps.sh"
shift || true

SECRETS_FILE="${VALUES%.yaml}.secrets.yaml"
HELM_BASE=(
  upgrade --install "$RELEASE" "$ROOT/charts/sailpoint"
  --namespace "$NS"
  --create-namespace
  -f "$VALUES"
)
if [[ -f "$SECRETS_FILE" ]]; then
  echo "Using secrets overlay: $SECRETS_FILE"
  HELM_BASE+=(-f "$SECRETS_FILE")
fi

# Pin app image when IMAGE_TAG is set (CI after Publish GHCR)
IMAGE_SETS=()
if [[ -n "${IMAGE_TAG:-}" ]]; then
  echo "Pinning identityiq.image.tag=${IMAGE_TAG}"
  IMAGE_SETS+=(--set-string "identityiq.image.tag=${IMAGE_TAG}")
  # Force pull so mutable tags (0.1.0/latest) and retagged SHAs never reuse a stale node cache.
  if [[ "${IMAGE_PULL_POLICY:-}" != "" ]]; then
    IMAGE_SETS+=(--set-string "identityiq.image.pullPolicy=${IMAGE_PULL_POLICY}")
  elif [[ "${GITHUB_ACTIONS:-}" == "true" ]]; then
    IMAGE_SETS+=(--set-string "identityiq.image.pullPolicy=Always")
  fi
  if [[ "${VERIFY_IMAGE_TAGS:-}" == "true" ]]; then
    OWNER="$(tr '[:upper:]' '[:lower:]' <<<"${GHCR_OWNER:-beyond-boilerplate}")"
    MANIFEST="ghcr.io/${OWNER}/identityiq:${IMAGE_TAG}"
    echo "Verifying GHCR manifest exists: ${MANIFEST}"
    if command -v docker >/dev/null 2>&1; then
      docker buildx imagetools inspect "$MANIFEST" >/dev/null
    elif command -v crane >/dev/null 2>&1; then
      crane manifest "$MANIFEST" >/dev/null
    else
      echo "ERROR: VERIFY_IMAGE_TAGS=true but neither docker nor crane is available" >&2
      exit 1
    fi
  fi
elif [[ "${GITHUB_ACTIONS:-}" == "true" ]]; then
  echo "ERROR: CI deploy requires IMAGE_TAG — refusing values-file default" >&2
  exit 1
fi

EXTRA_ARGS=()
if [[ "$#" -gt 0 ]]; then
  EXTRA_ARGS+=("$@")
fi

run_helm() {
  local label="$1"
  shift
  local timeout="${HELM_TIMEOUT:-8m}"
  echo "==> Helm phase: ${label} (timeout ${timeout})"
  # Background status ticker while helm blocks
  (
    while true; do
      sleep 30
      echo "… still waiting on ${label}"
      dump_status
    done
  ) &
  local ticker_pid=$!
  # shellcheck disable=SC2064
  trap "kill ${ticker_pid} 2>/dev/null || true" RETURN

  # "${arr[@]}" is unbound under `set -u` when empty — expand only if set/nonempty.
  if ! helm "${HELM_BASE[@]}" \
      --timeout "$timeout" \
      --wait \
      ${IMAGE_SETS[@]+"${IMAGE_SETS[@]}"} \
      "$@" \
      ${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}; then
    echo "ERROR: Helm phase ${label} failed"
    dump_status
    return 1
  fi
  kill "$ticker_pid" 2>/dev/null || true
  trap - RETURN
  echo "==> Helm phase ${label} OK"
  dump_status
}

# Phase 1: CNPG + schema hook only (avoid waiting on IIQ cold start in same --wait)
if [[ "$PHASE" == "all" || "$PHASE" == "data" ]]; then
  run_helm "data" \
    --set identityiq.enabled=false \
    --set identityiq-data.enabled=true
fi

# Phase 2: IdentityIQ (DB already up / schema applied)
if [[ "$PHASE" == "all" || "$PHASE" == "app" ]]; then
  # Give schema job a moment if it just finished as a hook
  if kubectl -n "$NS" get job sailpoint-pg-schema-init >/dev/null 2>&1; then
    echo "Waiting for schema init job (up to 5m)…"
    if ! kubectl -n "$NS" wait --for=condition=complete "job/sailpoint-pg-schema-init" --timeout=5m; then
      echo "ERROR: schema initialization did not complete"
      kubectl -n "$NS" logs job/sailpoint-pg-schema-init --all-containers --tail=200 || true
      dump_status
      exit 1
    fi
  fi
  run_helm "app" \
    --set identityiq.enabled=true \
    --set identityiq-data.enabled=true
fi

echo "Release ${RELEASE} installed in $NS"
dump_status
