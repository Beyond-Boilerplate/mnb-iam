#!/usr/bin/env bash
# Enterprise Lab smoke checks (services + HCM + portal + optional IIQ).
set -euo pipefail

pass=0
fail=0
check() {
  local name="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    echo "PASS  $name"
    pass=$((pass + 1))
  else
    echo "FAIL  $name"
    fail=$((fail + 1))
  fi
}

echo "==> Enterprise Lab e2e smoke"

check "connector-mock health" curl -sf "http://127.0.0.1:8091/health"
check "HCM workers" curl -sf "http://127.0.0.1:8091/hcm/v1/workers"
check "CRM SCIM" curl -sf "http://127.0.0.1:8091/crm/scim/v2/Users"
check "ITSM catalog" curl -sf "http://127.0.0.1:8091/itsm/v1/catalog"
check "OpenLDAP helen.ross" ldapsearch -x -H "ldap://127.0.0.1:${LDAP_PORT:-389}" -b "dc=meridiannb,dc=com" -D "cn=admin,dc=meridiannb,dc=com" -w admin "(uid=helen.ross)" dn

# Enterprise profile services (soft)
if curl -sf "http://127.0.0.1:${KEYCLOAK_PORT:-8085}/realms/meridian" >/dev/null 2>&1; then
  echo "PASS  keycloak meridian realm"
  pass=$((pass + 1))
else
  echo "SKIP  keycloak (start with --enterprise)"
fi

if curl -sf "http://127.0.0.1:${EMPLOYEE_PORTAL_PORT:-8092}/health" >/dev/null 2>&1; then
  echo "PASS  employee-portal health"
  pass=$((pass + 1))
else
  echo "SKIP  employee-portal (start with --enterprise)"
fi

if curl -sf "http://127.0.0.1:${MAILPIT_UI_PORT:-8025}/api/v1/info" >/dev/null 2>&1; then
  echo "PASS  mailpit UI"
  pass=$((pass + 1))
else
  echo "SKIP  mailpit (start with --enterprise)"
fi

if curl -sf "http://127.0.0.1:${GITEA_HTTP_PORT:-8093}/api/v1/version" >/dev/null 2>&1; then
  echo "PASS  gitea API"
  pass=$((pass + 1))
else
  echo "SKIP  gitea (start with --enterprise)"
fi

if curl -sf "http://127.0.0.1:${WORKSTATION_PORTAL_PORT:-8094}/health" >/dev/null 2>&1; then
  echo "PASS  workstation-portal health"
  pass=$((pass + 1))
else
  echo "SKIP  workstation-portal (start with --enterprise)"
fi

if curl -sf "http://127.0.0.1:${HR_INTRANET_PORT:-8095}/health" >/dev/null 2>&1; then
  echo "PASS  hr-intranet health"
  pass=$((pass + 1))
else
  echo "SKIP  hr-intranet (start with --enterprise)"
fi

if curl -sf "http://127.0.0.1:${FINANCE_PORTAL_PORT:-8096}/health" >/dev/null 2>&1; then
  echo "PASS  finance-portal health"
  pass=$((pass + 1))
else
  echo "SKIP  finance-portal (start with --enterprise)"
fi

if curl -sf "http://127.0.0.1:8091/entra/scim/v2/Users" >/dev/null 2>&1; then
  echo "PASS  entra-shaped SCIM"
  pass=$((pass + 1))
else
  echo "FAIL  entra-shaped SCIM"
  fail=$((fail + 1))
fi

if curl -sf "http://127.0.0.1:${VAULT_HTTP_PORT:-8200}/v1/sys/seal-status" >/dev/null 2>&1; then
  echo "PASS  vault seal-status"
  pass=$((pass + 1))
else
  echo "SKIP  vault (start with --enterprise)"
fi

if curl -sf "http://127.0.0.1:${PAM_LAB_PORT:-8097}/health" >/dev/null 2>&1; then
  echo "PASS  pam-lab health"
  pass=$((pass + 1))
else
  echo "SKIP  pam-lab (start with --enterprise)"
fi

if curl -sf -o /dev/null -u "spadmin:admin" "http://127.0.0.1:${IIQ_HTTP_PORT:-8080}/identityiq/login.jsf" 2>/dev/null \
  || curl -sf -o /dev/null "http://127.0.0.1:${IIQ_HTTP_PORT:-8080}/identityiq/" >/dev/null 2>&1; then
  echo "PASS  IIQ reachable"
  pass=$((pass + 1))
else
  echo "FAIL  IIQ reachable"
  fail=$((fail + 1))
fi

# HCM joiner POST roundtrip
joiner=$(curl -sf -X POST "http://127.0.0.1:8091/hcm/v1/workers" \
  -H "Content-Type: application/json" \
  -d '{"userName":"e2e.joiner","firstName":"E2E","lastName":"Joiner","email":"e2e.joiner@meridiannb.com","department":"Identity & Access","active":true}' \
  || true)
if echo "$joiner" | grep -q "e2e.joiner"; then
  echo "PASS  HCM joiner POST"
  pass=$((pass + 1))
else
  echo "FAIL  HCM joiner POST"
  fail=$((fail + 1))
fi

echo "==> Result: $pass passed, $fail failed"
[[ "$fail" -eq 0 ]]
