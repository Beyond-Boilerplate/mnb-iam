#!/usr/bin/env bash
# Bootstrap Gitea admin + print Keycloak OIDC source settings (Lesson 213).
set -euo pipefail
GITEA="${GITEA_URL:-http://127.0.0.1:8093}"
# Gitea fetches discovery from inside its container — localhost:8085 is Gitea itself.
KC_DISCOVERY="${KEYCLOAK_DISCOVERY_URL:-http://host.docker.internal:8085}"
REALM="${KEYCLOAK_REALM:-meridian}"
CLIENT_ID="${GITEA_OIDC_CLIENT_ID:-gitea}"
CLIENT_SECRET="${GITEA_OIDC_CLIENT_SECRET:-mnb-gitea-oidc-secret}"
ADMIN_USER="${GITEA_ADMIN_USER:-giteaadmin}"
ADMIN_PASS="${GITEA_ADMIN_PASS:-GiteaAdmin1!}"
ADMIN_EMAIL="${GITEA_ADMIN_EMAIL:-giteaadmin@meridiannb.com}"
CONTAINER="${GITEA_CONTAINER:-mnb-gitea}"

echo "==> Waiting for Gitea at $GITEA"
for _ in $(seq 1 60); do
  if curl -sf "$GITEA/api/v1/version" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

if ! curl -sf "$GITEA/api/v1/version" >/dev/null 2>&1; then
  echo "Gitea API not ready. If you see the Install page, recreate with INSTALL_LOCK:" >&2
  echo "  docker compose -f docker-compose.iiq.yml -f docker-compose.enterprise.yml --profile enterprise up -d --force-recreate gitea" >&2
  exit 1
fi

echo "==> Ensure local admin '$ADMIN_USER' exists (ignore if already present)"
docker exec -u git "$CONTAINER" gitea admin user create \
  --admin \
  --username "$ADMIN_USER" \
  --password "$ADMIN_PASS" \
  --email "$ADMIN_EMAIL" \
  --must-change-password=false >/dev/null 2>&1 || true

cat <<EOF

==> Add OAuth2 authentication source in Gitea UI
    Site Administration → Authentication Sources → Add Authentication Source → OAuth2

  Authentication Name: meridian
  OAuth2 Provider:     OpenID Connect
  Client ID:           $CLIENT_ID
  Client Secret:       $CLIENT_SECRET
  OpenID Connect Auto Discovery URL:
    $KC_DISCOVERY/realms/$REALM/.well-known/openid-configuration
  Scopes (optional):   openid profile email

  (Use host.docker.internal — not localhost — so Gitea's container can reach Keycloak.)

Then sign in via "meridian" with helen.ross / LabUser1!

Local admin (config only): $ADMIN_USER / $ADMIN_PASS
EOF
