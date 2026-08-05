#!/usr/bin/env bash
# Install mnb-iam-toolkit into a running IIQ via POST /rest/plugins
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ZIP="${1:-$ROOT/pluginsrc/mnb-iam-toolkit/dist/mnb_iam_toolkit-1.3.17.zip}"
BASE="${IIQ_BASE_URL:-http://localhost:8080/identityiq}"
USER="${IIQ_USER:-spadmin}"
PASS="${IIQ_PASSWORD:-admin}"

if [[ ! -f "$ZIP" ]]; then
  echo "Building ZIP first…"
  "$ROOT/pluginsrc/mnb-iam-toolkit/package.sh"
  ZIP="$ROOT/pluginsrc/mnb-iam-toolkit/dist/mnb_iam_toolkit-1.3.17.zip"
fi

echo "Installing $ZIP → $BASE/rest/plugins as $USER"
# Jersey FormDataParam names: file, fileName
code=$(curl -sS -o /tmp/mnb-plugin-install.json -w '%{http_code}' -u "$USER:$PASS" \
  -H 'X-Requested-With: XMLHttpRequest' \
  -H 'Accept: application/json' \
  -F "file=@${ZIP};type=application/zip" \
  -F "fileName=$(basename "$ZIP")" \
  "$BASE/rest/plugins" || true)
echo "http=$code"
python3 -m json.tool /tmp/mnb-plugin-install.json 2>/dev/null | head -40 || cat /tmp/mnb-plugin-install.json
echo
if [[ "$code" != "200" ]] || grep -qi 'does not meet\|error\|cannot' /tmp/mnb-plugin-install.json 2>/dev/null; then
  # Empty body on success is OK; message body with failure is not
  if [[ "$code" != "200" ]] || python3 -c 'import json; d=json.load(open("/tmp/mnb-plugin-install.json")); raise SystemExit(1 if d.get("message") else 0)' 2>/dev/null; then
    echo "ERROR: plugin install failed (http=$code). Uninstall existing plugin first if upgrading same/older version."
    exit 1
  fi
fi
echo "--- verify plugins list ---"
curl -sS -u "$USER:$PASS" -H 'Accept: application/json' -H 'X-Requested-With: XMLHttpRequest' \
  "$BASE/rest/plugins" | python3 -m json.tool | head -60
echo "--- smoke ping (may 403 until rights granted) ---"
curl -sS -o /tmp/mnb-ping.json -w "http=%{http_code}\n" -u "$USER:$PASS" -H 'Accept: application/json' \
  "$BASE/plugin/rest/mnbToolkit/ping" || true
head -c 400 /tmp/mnb-ping.json; echo

echo
echo "NOTE: Reinstall resets plugin setting *values* to defaults (agentApiEnabled=false)."
echo "Re-enable in UI (Plugins → Meridian Custom APIs) or run:"
echo "  IIQ_BASE_URL=$BASE IIQ_USER=$USER IIQ_PASSWORD=… $ROOT/pluginsrc/mnb-iam-toolkit/enable-settings.sh"
echo "Required: agentApiEnabled, taskRunEnabled + allowedTaskNames, mutateGovernanceEnabled, advancedOpsEnabled."
