#!/usr/bin/env bash
# Lab-only: allow HTTP for Keycloak admin console (master) and meridian realm.
# Keycloak defaults master to sslRequired=EXTERNAL → "HTTPS required" on http://localhost:8085
set -euo pipefail

SERVER="${KEYCLOAK_INTERNAL_URL:-http://keycloak:8080}"
ADMIN_USER="${KEYCLOAK_ADMIN:-admin}"
ADMIN_PASS="${KEYCLOAK_ADMIN_PASSWORD:-admin}"
KCADM=/opt/keycloak/bin/kcadm.sh

echo "==> Waiting for Keycloak at $SERVER"
for i in $(seq 1 60); do
  if curl -sf "$SERVER/realms/master" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

echo "==> kcadm login (master)"
"$KCADM" config credentials --server "$SERVER" --realm master --user "$ADMIN_USER" --password "$ADMIN_PASS"

echo "==> Set sslRequired=NONE on master (admin console over HTTP)"
"$KCADM" update realms/master -s sslRequired=NONE

if "$KCADM" get realms/meridian >/dev/null 2>&1; then
  echo "==> Set sslRequired=NONE on meridian"
  "$KCADM" update realms/meridian -s sslRequired=NONE || true
fi

echo "==> Done — open http://localhost:8085/admin/ (admin / admin)"
