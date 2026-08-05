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
  echo "==> Ensuring Core lab seed (HR + OpenLDAP) is present"
  "$ROOT/tools/lab/scripts/seed-mnb-lab-data.sh" || true
fi

echo "==> Importing enterprise XML via MCP"
python3 "$ROOT/tools/lab/enterprise/import-enterprise-xml.py" || true

if docker inspect mnb-samba-ad >/dev/null 2>&1; then
  echo "==> Seeding Samba (best-effort)"
  "$ROOT/tools/lab/enterprise/seed-samba.sh" || true
fi

echo "==> Enterprise seed complete"
echo "    Pass-through login: see lab-data/enterprise/PASS-THROUGH-AUTH.md"
echo "    Portal: http://localhost:8092/  Keycloak: http://localhost:8085/"
echo "    Workstation: http://localhost:8094/  HR: :8095  Finance: :8096"
echo "    Vault/PAM: http://localhost:8200/ui · http://localhost:8097/ (lab-data/enterprise/pam/README.md)"
echo "    Password path: lab-data/enterprise/password/README.md"
echo "    Toolkit: GET /plugin/rest/mnbToolkit/enterprise/status (after plugin rebuild)"
echo "    Note: Keycloak realm JSON imports only on empty volume — wipe mnb-keycloak-data to pick up new clients/groups"
