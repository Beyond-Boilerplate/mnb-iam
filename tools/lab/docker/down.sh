#!/usr/bin/env bash
# Tear down the Meridian Docker lab stack.
#
# Default: remove containers AND volumes (Postgres, OpenLDAP, MCP audit).
# Keep data: ./tools/lab/docker/down.sh --keep-volumes
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

KEEP_VOLUMES=0
PASSTHRU=()
for arg in "$@"; do
  case "$arg" in
    --keep-volumes) KEEP_VOLUMES=1 ;;
    -h|--help)
      cat <<'EOF'
Usage: ./tools/lab/docker/down.sh [--keep-volumes] [docker compose down args...]

  (default)          Stop stack and DELETE volumes (full wipe)
  --keep-volumes     Stop stack but keep Postgres / OpenLDAP / MCP volumes
EOF
      exit 0
      ;;
    *) PASSTHRU+=("$arg") ;;
  esac
done

if [[ "$KEEP_VOLUMES" -eq 1 ]]; then
  echo "==> Stopping Meridian stack (keeping volumes)"
  docker compose -f docker-compose.iiq.yml down --remove-orphans "${PASSTHRU[@]+"${PASSTHRU[@]}"}"
else
  echo "==> Stopping Meridian stack and deleting volumes (full wipe)"
  docker compose -f docker-compose.iiq.yml down -v --remove-orphans "${PASSTHRU[@]+"${PASSTHRU[@]}"}"
fi
echo "Done."
