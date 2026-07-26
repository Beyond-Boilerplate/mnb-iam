#!/usr/bin/env bash
# Publish base/ga/identityiq-8.5.zip to GHCR as an OCI artifact (run on a trusted machine).
# Usage:
#   echo "$GHCR_PAT" | docker login ghcr.io -u USER --password-stdin
#   ./.github/scripts/publish-ga-oci.sh [tag]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
TAG="${1:-8.5}"
ZIP_REL="base/ga/identityiq-8.5.zip"
OWNER="${GHCR_OWNER:-beyond-boilerplate}"
REF="ghcr.io/${OWNER}/mnb-iam-ga:${TAG}"

test -f "$ZIP_REL" || { echo "Missing $ROOT/$ZIP_REL" >&2; exit 1; }
command -v oras >/dev/null || { echo "Install oras: https://oras.land" >&2; exit 1; }

oras push "$REF" \
  --artifact-type application/vnd.sailpoint.iiq.ga.v1+zip \
  "${ZIP_REL}:application/zip"

echo "Published ${REF}"
