#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/charts/sailpoint"
helm dependency update
echo "helm deps updated for sailpoint"
