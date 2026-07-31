#!/usr/bin/env bash
# Grant svc-iiq-provision write (implies read) via the database-wide ACL.
# Must be on the catch-all "to *" rule — rules after "by * none" never run.
# Runs once after OpenLDAP is healthy (compose openldap-provision-acl).
set -euo pipefail

HOST="${LDAP_HOST:-openldap}"
PORT="${LDAP_PORT:-389}"
ADMIN_DN="${LDAP_ADMIN_DN:-cn=admin,dc=meridiannb,dc=com}"
ADMIN_PW="${LDAP_ADMIN_PASSWORD:-admin}"
CONFIG_DN="${LDAP_CONFIG_DN:-cn=admin,cn=config}"
CONFIG_PW="${LDAP_CONFIG_PASSWORD:-config}"
PROV_DN="${LDAP_PROVISION_DN:-cn=svc-iiq-provision,ou=service,dc=meridiannb,dc=com}"
PROV_PW="${LDAP_PROVISION_PASSWORD:-Provision1!}"
READ_DN="${LDAP_READONLY_DN:-cn=svc-iiq-read,dc=meridiannb,dc=com}"
URI="ldap://${HOST}:${PORT}"

echo "==> Waiting for ${PROV_DN}…"
for _ in $(seq 1 60); do
  if ldapsearch -x -H "$URI" -D "$ADMIN_DN" -w "$ADMIN_PW" -b "$PROV_DN" -s base dn >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

if ! ldapsearch -x -H "$URI" -D "$ADMIN_DN" -w "$ADMIN_PW" -b "$PROV_DN" -s base dn >/dev/null 2>&1; then
  echo "ERROR: provision bind entry not found: ${PROV_DN}" >&2
  exit 1
fi

DB_DN="$(
  ldapsearch -x -H "$URI" -D "$CONFIG_DN" -w "$CONFIG_PW" -b cn=config \
    "(olcSuffix=dc=meridiannb,dc=com)" dn -LLL 2>/dev/null \
    | awk '/^dn:/{print substr($0,5); exit}'
)"

if [[ -z "$DB_DN" ]]; then
  echo "ERROR: could not find olcDatabase for dc=meridiannb,dc=com" >&2
  exit 1
fi

ACL_BLOB="$(
  ldapsearch -x -H "$URI" -D "$CONFIG_DN" -w "$CONFIG_PW" -b "$DB_DN" olcAccess -LLL 2>/dev/null || true
)"

if echo "$ACL_BLOB" | tr -d '\n' | grep -q "dn.exact=\"${PROV_DN}\".*write\|dn=\"${PROV_DN}\".*write\|${PROV_DN}\" write"; then
  if ldapsearch -x -H "$URI" -D "$PROV_DN" -w "$PROV_PW" \
      -b ou=people,dc=meridiannb,dc=com '(uid=helen.ross)' dn 2>/dev/null | grep -q 'uid=helen.ross'; then
    echo "==> Provision ACLs already present — skip"
    exit 0
  fi
fi

echo "==> Replacing catch-all ACL so ${PROV_DN} has write (before by * none)"
# osixia default {2}: to * by self read by admin write by readonly read by * none
# Insert provision write on that same rule so evaluation reaches it.
ldapmodify -x -H "$URI" -D "$CONFIG_DN" -w "$CONFIG_PW" <<EOF
dn: ${DB_DN}
changetype: modify
delete: olcAccess
olcAccess: {2}
-
add: olcAccess
olcAccess: {2}to * by self read by dn="${ADMIN_DN}" write by dn="${READ_DN}" read by dn.exact="${PROV_DN}" write by * none
EOF

# Drop any earlier failed append-only rules that sit after by * none (harmless if absent)
ldapmodify -x -H "$URI" -D "$CONFIG_DN" -w "$CONFIG_PW" <<'EOF' || true
dn: olcDatabase={1}mdb,cn=config
changetype: modify
delete: olcAccess
olcAccess: {4}
EOF
ldapmodify -x -H "$URI" -D "$CONFIG_DN" -w "$CONFIG_PW" <<'EOF' || true
dn: olcDatabase={1}mdb,cn=config
changetype: modify
delete: olcAccess
olcAccess: {3}
EOF

echo "==> Verifying provision bind can search…"
ldapsearch -x -H "$URI" -D "$PROV_DN" -w "$PROV_PW" \
  -b ou=people,dc=meridiannb,dc=com '(uid=helen.ross)' dn | grep -q 'uid=helen.ross'

echo "==> Verifying provision bind can modify…"
ldapmodify -x -H "$URI" -D "$PROV_DN" -w "$PROV_PW" <<EOF
dn: uid=helen.ross,ou=people,dc=meridiannb,dc=com
changetype: modify
replace: description
description: Active
EOF

echo "Ready: ${PROV_DN} has write (aggregate + provision bind for IIQ)"
