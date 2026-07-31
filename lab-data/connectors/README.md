# Meridian connector & customization lab fixtures

Use these when lessons move beyond Delimited File. Optional Docker targets are documented in `docker-compose.connectors.yml` at repo root (learn track).

| Path | Purpose |
| --- | --- |
| `connector-selection-matrix.csv` | Meridian system → recommended IIQ connector |
| `features-string-glossary.md` | PROVISIONING, ENABLE, PASSWORD, … meanings |
| `jdbc/mnb_core_accounts.sql` | Sample schema for JDBC lab |
| `jdbc/sample-rows.csv` | Seed data if DB unavailable |
| `ldap/mnb-openldap.ldif` | Enterprise-shaped inetOrgPerson + groups + svc binds (baked into OpenLDAP image) |
| `ldap/README.md` | OpenLDAP connection sheet for IIQ onboarding |
| `webservices/wire-portal-openapi.yaml` | Stub OpenAPI for Web Services connector |
| `webservices/sample-users.json` | Mock GET /users payload |
| `scim/Users.json` | SCIM 2.0 ListResponse sample |
| `ad/iqservice-checklist.md` | AD + IQService enterprise checklist |
| `rules/README.md` | Rule type cheat sheet + stub names |
| `plugins/README.md` | Plugin packaging notes for Meridian |

OpenLDAP starts with the main Docker lab (`./tools/lab/docker/up.sh`). Sample JDBC is optional via `docker-compose.connectors.yml`. Every connector lesson still includes a **lab-without-live-target** path so training completes without Docker backends.
