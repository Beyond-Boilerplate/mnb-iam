#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
exec "$ROOT/tools/lab/scripts/scenarios/apply-hr-delta.sh" on-leave "$@"
