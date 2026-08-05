#!/usr/bin/env bash
# Drive HCM mock joiner/mover/leaver (Enterprise Lab) instead of only patching HR CSV.
set -euo pipefail
MOCK="${CONNECTOR_MOCK_URL:-http://127.0.0.1:8091}"
ACTION="${1:-}"
shift || true

usage() {
  cat <<EOF
Usage:
  $0 joiner <username> <first> <last> <email> [department]
  $0 leaver <username|workerId>
  $0 mover <username|workerId> <newDepartment> [newTitle]
  $0 list
EOF
  exit 2
}

case "$ACTION" in
  list)
    curl -sf "$MOCK/hcm/v1/workers" | python3 -m json.tool
    ;;
  joiner)
    [[ $# -ge 4 ]] || usage
    user="$1"; first="$2"; last="$3"; email="$4"; dept="${5:-Identity & Access}"
    curl -sf -X POST "$MOCK/hcm/v1/workers" -H 'Content-Type: application/json' \
      -d "{\"userName\":\"$user\",\"firstName\":\"$first\",\"lastName\":\"$last\",\"email\":\"$email\",\"department\":\"$dept\",\"active\":true,\"status\":\"Active\"}" \
      | python3 -m json.tool
    echo "Next: aggregate MNB-Workday (or MNB-HR) and refresh cubes in IIQ."
    ;;
  leaver)
    [[ $# -ge 1 ]] || usage
    id="$1"
    curl -sf -X PATCH "$MOCK/hcm/v1/workers/$id" -H 'Content-Type: application/json' \
      -d '{"active":false,"status":"Terminated"}' | python3 -m json.tool
    ;;
  mover)
    [[ $# -ge 2 ]] || usage
    id="$1"; dept="$2"; title="${3:-}"
    body="{\"department\":\"$dept\""
    [[ -n "$title" ]] && body+=",\"title\":\"$title\""
    body+="}"
    curl -sf -X PATCH "$MOCK/hcm/v1/workers/$id" -H 'Content-Type: application/json' \
      -d "$body" | python3 -m json.tool
    ;;
  *) usage ;;
esac
