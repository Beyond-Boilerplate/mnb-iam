#!/usr/bin/env bash
# Seed Samba AD users from generated CSV (best-effort; requires samba-ad healthy).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
CSV="${ROOT}/lab-data/enterprise/generated/samba-users.csv"
CONTAINER="${SAMBA_CONTAINER:-mnb-samba-ad}"
DOMAIN_DN="DC=meridiannb,DC=com"
ADMIN_PASS="${SAMBA_ADMIN_PASS:-Password1!}"

if [[ ! -f "$CSV" ]]; then
  echo "Missing $CSV — run generate-identity-artifacts.py first" >&2
  exit 1
fi

if ! docker inspect "$CONTAINER" >/dev/null 2>&1; then
  echo "Container $CONTAINER not running — start with ./tools/lab/docker/up.sh --enterprise" >&2
  exit 1
fi

echo "==> Seeding Samba users into $CONTAINER (best-effort)"

# IIQ OpenLDAP-Direct binds simple on ldap://samba-ad:389. Modern Samba defaults to
# "ldap server require strong auth = yes", which rejects that bind with LDAP 8
# ("Transport encryption required"). TLS certs in this image are often missing, so
# LDAPS/StartTLS is not a reliable lab path — allow cleartext binds for the sandbox.
docker exec "$CONTAINER" bash -lc '
CONF=/etc/samba/smb.conf
if grep -qi "ldap server require strong auth" "$CONF"; then
  sed -i "s/^[[:space:]]*ldap server require strong auth.*/\tldap server require strong auth = no/I" "$CONF"
else
  awk '\''BEGIN{d=0} /^\[global\]/{print; print "\tldap server require strong auth = no"; d=1; next} {print}'\'' "$CONF" > /tmp/smb.conf.new && mv /tmp/smb.conf.new "$CONF"
fi
smbcontrol all reload-config 2>/dev/null || true
if command -v supervisorctl >/dev/null 2>&1; then
  supervisorctl restart samba 2>/dev/null || true
fi
' || true

# Create OU for people if missing
docker exec "$CONTAINER" bash -lc "
set -e
samba-tool ou create 'OU=People' --description='Meridian workforce' 2>/dev/null || true
samba-tool group add 'MNB-Employees' 2>/dev/null || true
samba-tool group add 'MNB-Managers' 2>/dev/null || true
samba-tool group add 'Wire-Initiators' 2>/dev/null || true
samba-tool group add 'Wire-Approvers' 2>/dev/null || true
" || true

# Skip header; create users
tail -n +2 "$CSV" | while IFS=, read -r sam given sn mail emp dept title uac password; do
  [[ -z "$sam" ]] && continue
  echo "  user $sam"
  docker exec "$CONTAINER" bash -lc "
samba-tool user create '$sam' '$password' \
  --given-name='$given' --surname='$sn' --mail-address='$mail' \
  --job-title='$title' --department='$dept' \
  --userou='OU=People' 2>/dev/null || samba-tool user setpassword '$sam' --newpassword='$password' 2>/dev/null || true
" || true
done

echo "==> Samba seed finished (check docker logs $CONTAINER if users missing)"
