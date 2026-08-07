#!/usr/bin/env bash
# Import Enterprise Lab durable objects into a running IIQ (via MCP when available).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

export MCP_API_KEY="${MCP_API_KEY:-mnb-lab-mcp-key}"
export IIQ_MCP_URL="${IIQ_MCP_URL:-http://127.0.0.1:8766/mcp}"

echo "==> Generating identity artifacts"
python3 "$ROOT/tools/lab/enterprise/generate-identity-artifacts.py"

if [[ -x "$ROOT/tools/lab/scripts/seed-mnb-lab-data.sh" ]]; then
  echo "==> Ensuring Core app definitions (MNB-HR non-authoritative + MNB-OpenLDAP; no cubes)"
  # Overlay by default. up.sh --wipe sets MNB_LAB_RESET_DONE after backup→reset.
  seed_args=(--definitions-only --hr-non-authoritative --keep-existing)
  if [[ "${MNB_LAB_WIPE:-}" == "1" ]]; then
    seed_args=(--definitions-only --hr-non-authoritative --wipe)
  fi
  "$ROOT/tools/lab/scripts/seed-mnb-lab-data.sh" "${seed_args[@]}" || true
fi

echo "==> Importing enterprise XML via MCP"
python3 "$ROOT/tools/lab/enterprise/import-enterprise-xml.py" || true

if docker inspect mnb-samba-ad >/dev/null 2>&1; then
  echo "==> Seeding Samba (best-effort)"
  "$ROOT/tools/lab/enterprise/seed-samba.sh" || true
fi

echo "==> Enabling Keycloak iiq-scim provisioner roles (best-effort)"
if [[ -x "$ROOT/tools/lab/enterprise/keycloak-enable-iiq-provisioner.sh" ]]; then
  "$ROOT/tools/lab/enterprise/keycloak-enable-iiq-provisioner.sh" || true
fi

echo "==> Enterprise seed complete"
echo "    Pass-through login: see lab-data/enterprise/PASS-THROUGH-AUTH.md"
echo "    Portal: http://localhost:8092/  Keycloak: http://localhost:8085/"
echo "    Workstation: http://localhost:8094/  HR: :8095  Finance: :8096"
echo "    Vault/PAM: http://localhost:8200/ui · http://localhost:8097/ (lab-data/enterprise/pam/README.md)"
echo "    Password path: lab-data/enterprise/password/README.md"
echo "    Toolkit: GET /plugin/rest/mnbToolkit/enterprise/status (after plugin rebuild)"
echo "    Note: Keycloak realm JSON imports only on empty volume — wipe mnb-keycloak-data to pick up new clients/groups"
echo "    IdP birthright: MNB-Keycloak-IdP → connector-mock /idp/scim (after mock rebuild + keycloak-enable-iiq-provisioner.sh)"
echo "    Cubes: none yet — Lesson 207 aggregates MNB-Workday (authoritative HCM)"
echo "    MNB Workday UI: http://localhost:8091/hcm/ui"
