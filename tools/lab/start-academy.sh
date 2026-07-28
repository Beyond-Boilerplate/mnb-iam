#!/usr/bin/env bash
# Deprecated entry: use ./tools/lab/up.sh
# Kept as a thin wrapper for docs/bookmarks.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$ROOT/up.sh" --academy-only "$@"
