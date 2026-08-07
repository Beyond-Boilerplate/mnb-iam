#!/usr/bin/env bash
# Grant Keycloak realm-management roles to the iiq-scim service account so
# connector-mock /idp/scim can create users and assign groups for birthright.
set -euo pipefail

KC_URL="${KEYCLOAK_URL:-http://127.0.0.1:8085}"
ADMIN_USER="${KEYCLOAK_ADMIN:-admin}"
ADMIN_PASS="${KEYCLOAK_ADMIN_PASSWORD:-admin}"
REALM="${KEYCLOAK_REALM:-meridian}"
CLIENT_ID="${KEYCLOAK_IIQ_CLIENT_ID:-iiq-scim}"
CLIENT_SECRET="${KEYCLOAK_IIQ_CLIENT_SECRET:-mnb-iiq-scim-secret}"

echo "==> Keycloak enable IIQ provisioner ($CLIENT_ID @ $REALM)"

TOKEN=$(curl -sf -X POST "$KC_URL/realms/master/protocol/openid-connect/token" \
  -d "client_id=admin-cli" \
  -d "username=$ADMIN_USER" \
  -d "password=$ADMIN_PASS" \
  -d "grant_type=password" | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

auth=(-H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json")

CLIENT_UUID=$(curl -sf "${auth[@]}" \
  "$KC_URL/admin/realms/$REALM/clients?clientId=$CLIENT_ID" \
  | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d[0]["id"] if d else "")')
if [[ -z "$CLIENT_UUID" ]]; then
  echo "ERROR: client $CLIENT_ID not found in realm $REALM" >&2
  exit 1
fi

SA_USER=$(curl -sf "${auth[@]}" \
  "$KC_URL/admin/realms/$REALM/clients/$CLIENT_UUID/service-account-user" \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')

RM_UUID=$(curl -sf "${auth[@]}" \
  "$KC_URL/admin/realms/$REALM/clients?clientId=realm-management" \
  | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d[0]["id"] if d else "")')

curl -sf "${auth[@]}" \
  "$KC_URL/admin/realms/$REALM/clients/$RM_UUID/roles" \
  | python3 -c '
import json,sys
wanted={"manage-users","view-users","query-users","view-groups","query-groups","view-realm"}
roles=json.load(sys.stdin)
out=[r for r in roles if r.get("name") in wanted]
print(json.dumps(out))
print("Selected:", ", ".join(sorted(r["name"] for r in out)), file=sys.stderr)
' > /tmp/mnb-iiq-scim-roles.json

curl -sf -X POST "${auth[@]}" \
  "$KC_URL/admin/realms/$REALM/users/$SA_USER/role-mappings/clients/$RM_UUID" \
  --data-binary @/tmp/mnb-iiq-scim-roles.json >/dev/null

SA_TOKEN=$(curl -sf -X POST "$KC_URL/realms/$REALM/protocol/openid-connect/token" \
  -d "grant_type=client_credentials" \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET" \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

CODE=$(curl -s -o /tmp/mnb-kc-users.json -w '%{http_code}' \
  -H "Authorization: Bearer $SA_TOKEN" \
  "$KC_URL/admin/realms/$REALM/users?max=1")
if [[ "$CODE" != "200" ]]; then
  echo "ERROR: service account still cannot list users (HTTP $CODE)" >&2
  cat /tmp/mnb-kc-users.json >&2 || true
  exit 1
fi

echo "==> Done — iiq-scim can manage users/groups in $REALM"
