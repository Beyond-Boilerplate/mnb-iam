#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
FILE="${1:-$ROOT/lab-data/scenarios/bad-row/hr-delta-bad-row-diagnose.csv}"
exec "$ROOT/tools/lab/scripts/scenarios/apply-hr-delta.sh" --diagnose "$FILE"
