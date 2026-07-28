#!/usr/bin/env bash
# Verify a Meridian lesson against local (default), Docker, or CD IIQ.
# Usage:
#   ./tools/iiq-verify/verify-lesson.sh 04
#   IIQ_BASE_URL=https://sailpoint.lmsapp.us/identityiq IIQ_VERIFY_MODE=k8s ./tools/iiq-verify/verify-lesson.sh 04
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LESSON="${1:-}"
if [[ -z "$LESSON" ]]; then
  echo "Usage: $0 <lesson-number-or-stem>" >&2
  echo "Specs: $ROOT/tools/iiq-verify/lesson-specs/" >&2
  exit 2
fi
shift || true
export IIQ_BASE_URL="${IIQ_BASE_URL:-http://localhost:8080/identityiq}"
export IIQ_USER="${IIQ_USER:-spadmin}"
export IIQ_PASSWORD="${IIQ_PASSWORD:-admin}"
exec python3 "$ROOT/tools/iiq-verify/verify_lesson.py" --lesson "$LESSON" "$@"
