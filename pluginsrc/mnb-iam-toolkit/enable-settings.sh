#!/usr/bin/env bash
# Enable Meridian Custom APIs plugin flags after install (install resets values to defaults).
set -euo pipefail
BASE="${IIQ_BASE_URL:-http://localhost:8080/identityiq}"
USER="${IIQ_USER:-spadmin}"
PASS="${IIQ_PASSWORD:-admin}"
PLUGIN="${PLUGIN_NAME:-mnb_iam_toolkit}"

SETTINGS_JSON="${SETTINGS_JSON:-$(cat <<'EOF'
{
  "settings": {
    "agentApiEnabled": "true",
    "taskRunEnabled": "true",
    "mutateGovernanceEnabled": "true",
    "passwordResetEnabled": "true",
    "advancedOpsEnabled": "true",
    "allowedTaskNames": "Account Aggregation*,Refresh Identity Cube*,Refresh*,Aggregate *,Identity Refresh*"
  }
}
EOF
)}"

echo "Updating $PLUGIN settings via Custom APIs…"
code=$(curl -sS -o /tmp/mnb-plugin-settings.json -w '%{http_code}' -u "$USER:$PASS" \
  -H 'Content-Type: application/json' -H 'Accept: application/json' \
  -X POST "$BASE/plugin/rest/mnbToolkit/agent/plugins/${PLUGIN}/settings" \
  -d "$SETTINGS_JSON" || true)
echo "http=$code"
python3 -m json.tool /tmp/mnb-plugin-settings.json 2>/dev/null | head -80 || head -c 800 /tmp/mnb-plugin-settings.json
echo
if [[ "$code" != "200" ]]; then
  echo "WARN: settings API failed (need mnb_iam_toolkit ≥1.3.2). Falling back to status dump…"
  curl -sS -u "$USER:$PASS" -H 'X-Requested-With: XMLHttpRequest' -H 'Accept: application/json' \
    "$BASE/rest/plugins" | python3 - <<'PY'
import json,sys
d=json.load(sys.stdin)
plug=next((p for p in (d.get("objects") or []) if p.get("name")=="mnb_iam_toolkit"), None)
if not plug:
  raise SystemExit("mnb_iam_toolkit not installed")
for s in plug.get("settings") or []:
  print(f"  {s['name']}: value={s.get('value')!r}")
print("Set flags in UI → Plugins → Meridian Custom APIs")
PY
  exit 1
fi

echo "--- ping ---"
curl -sS -u "$USER:$PASS" -H 'Accept: application/json' "$BASE/plugin/rest/mnbToolkit/ping" | python3 -m json.tool
