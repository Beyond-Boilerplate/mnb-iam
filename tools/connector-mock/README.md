# Meridian connector mock — Wire Portal, SCIM, HCM, CRM, ITSM

```bash
python3 tools/connector-mock/serve.py
# http://localhost:8091/health
# http://localhost:8091/users                  (Lesson 68 Wire)
# http://localhost:8091/scim/v2/Users          (Lesson 69 SCIM)
# http://localhost:8091/hcm/ui                 (MNB Workday helper UI — Lesson 207)
# http://localhost:8091/hcm/v1/workers         (Enterprise Workday-shaped HCM API)
# http://localhost:8091/crm/scim/v2/Users      (Enterprise CRM)
# http://localhost:8091/itsm/v1/catalog        (Enterprise ITSM)
```

**MNB Workday UI** (`/hcm/ui`) browses the same in-memory HCM feed IIQ aggregates: add workers (`POST`), edit fields (`PATCH`), terminate (`PATCH` `active: false`). No hard delete. Restarting `connector-mock` resets to `lab-data/connectors/hcm/workers.json`.

Docker (main stack): service `connector-mock` on host `:8091`  
From IIQ container: `http://connector-mock:8091`

Regenerate HCM/CRM fixtures from the identity master:

```bash
./tools/lab/enterprise/generate-identity-artifacts.py
```

See also:
- `lab-data/connectors/webservices/` — OpenAPI + fixture
- `lab-data/connectors/scim/Users.json` — SCIM ListResponse fixture
- `lab-data/connectors/hcm/workers.json` — HCM workers
- `docs/ENTERPRISE-LAB-V2.md`
