#!/usr/bin/env bash
# Import + run MNB-Rule-Send-Test-Email inside the IIQ container (Mailpit proof).
# Optional shortcut — Lesson 203 teaches creating/running the rule in the IIQ UI.
# Prereq: Notification Settings SMTP = mailpit:1025 (Lesson 203).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
CONTAINER="${IIQ_DOCKER_CONTAINER:-mnb-identityiq}"
TPL="$ROOT/config/EmailTemplate/MNB-EmailTemplate-Lab-Test.xml"
RULE="$ROOT/config/Rule/MNB-Rule-Send-Test-Email.xml"

if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "ERROR: container ${CONTAINER} is not running" >&2
  exit 1
fi
[[ -f "$TPL" && -f "$RULE" ]] || { echo "ERROR: missing template/rule XML under config/" >&2; exit 1; }

echo "==> Importing EmailTemplate + Rule into ${CONTAINER}"
docker cp "$TPL" "${CONTAINER}:/tmp/MNB-EmailTemplate-Lab-Test.xml"
docker cp "$RULE" "${CONTAINER}:/tmp/MNB-Rule-Send-Test-Email.xml"
docker exec "$CONTAINER" sh -c '
  cd /usr/local/tomcat/webapps/identityiq/WEB-INF/bin
  chmod +x iiq 2>/dev/null || true
  ./iiq console iiqBeans <<EOF
import /tmp/MNB-EmailTemplate-Lab-Test.xml
import /tmp/MNB-Rule-Send-Test-Email.xml
rule MNB-Rule-Send-Test-Email
EOF
'
echo "==> Done. Refresh http://localhost:8025/ — expect subject \"Meridian lab SMTP test\" to lab-test@meridiannb.com"
