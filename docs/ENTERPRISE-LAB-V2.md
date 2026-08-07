# Meridian Enterprise Lab v2 — operator guide

Production-like **local** IdentityIQ ecosystem. Design + implementation live in-repo; start with the enterprise Compose profile when you want the full bank simulation.

**ADR:** [`docs/adr/001-enterprise-lab-v2.md`](adr/001-enterprise-lab-v2.md)

## Decisions

| Decision | Choice |
| --- | --- |
| Infra | Fully local Docker (no SaaS tenants) |
| Pedagogy | Core Path stays CSV-first; v2 is opt-in |
| Connectors | WS/SCIM/LDAP for Workday-/Okta-/AD-shaped systems |
| IQService | Documented stretch only — not a v2 gate |

## Topology

| Service | Host port | Role |
| --- | --- | --- |
| **lab-hub** | 9000 | Static TOC of all local service URLs |
| **db-viewer** | 9001 | Adminer — IIQ Postgres + JDBC lab (baked-in Auto Sign-In) |
| IIQ + Postgres + Academy + MCP + Teller | 8080, 5433, 4173, 8766, 4180 | Core stack (always) |
| OpenLDAP + phpLDAPadmin | 389, 8090 | Corp directory |
| jdbc-pg | 5435 | Core banking JDBC |
| connector-mock | 8091 | Wire + SCIM + **HCM** + CRM + ITSM APIs; **MNB Workday** UI at `/hcm/ui` |
| **samba-ad** | 3890 (LDAP), 445 | Corporate AD (Samba DC) |
| **keycloak** | 8085 | Okta-shaped IdP (OIDC + SCIM) |
| **employee-portal** | 8092 | OIDC app for login proof |
| **mailpit** | 8025 (UI), host SMTP 1026→1025 | Catch-all email; IIQ uses `mailpit:1025` |
| **gitea** | 8093 | Second SSO app (OIDC via Keycloak) |
| **workstation-portal** | 8094 | Laptop login gate (`mnb-workstation-users`) |
| **hr-intranet** | 8095 | HR Self-Service SSO (`mnb-hr-intranet`) |
| **finance-portal** | 8096 | Finance Portal SSO (`mnb-finance-portal`) |
| **vault** | 8200 | HashiCorp Vault (secret store) |
| **pam-lab** | 8097 | CyberArk-shaped safes / checkout / sessions |

```text
HCM mock ──agg──► IIQ ──provision──► OpenLDAP / Samba / JDBC / Wire / CRM / Entra-mock
                         │
                         ├── SCIM ──► Keycloak (workforce IdP + groups)
                         ├── SMTP ──► Mailpit (notifications proof)
                         ├── BreakGlass ──► pam-lab safes ──► Vault KV (checkout)
                         └── login verify ──► Portal + Gitea + Workstation + HR + Finance
```

## Quick start

```bash
# Core (unchanged) — overlay seed; does not wipe MNB-* objects
./tools/lab/docker/up.sh

# Enterprise lite (Keycloak + Employee Portal + Mailpit) — default --enterprise
./tools/lab/docker/up.sh --enterprise

# Add packs only when the lesson needs them
./tools/lab/docker/up.sh --enterprise --with=ad          # Samba AD (Lessons 205/234)
./tools/lab/docker/up.sh --enterprise --with=sso         # Gitea + SSO gates
./tools/lab/docker/up.sh --enterprise --with=pam         # Vault + pam-lab
./tools/lab/docker/up.sh --enterprise-full               # all packs

# Destructive Meridian reset (backup → wipe → seed)
./tools/lab/docker/up.sh --enterprise --wipe
```

| Pack / profile | Services | When |
| --- | --- | --- |
| `enterprise` (lite) | Keycloak, Employee Portal, Mailpit | Default `--enterprise` — IdP / mail / portal |
| `enterprise-ad` | Samba AD DC (`linux/amd64`) | Lessons **205**, **234** — real AD-shaped LDAP |
| `enterprise-sso` | Gitea, Workstation, HR, Finance gates | Lessons **212–213+** |
| `enterprise-pam` | Vault, pam-lab | PAM / break-glass lessons |

**Samba AD value:** dedicated live path for AD aggregation/groups without IQService (`MNB-ActiveDirectory-Live`). Core Path lessons 56–57 use CSV stubs; Enterprise Sandbox proves the same skills against a real Samba DC. Opt-in because the image is **amd64** (QEMU on Apple Silicon) and slow to become healthy.

Tear down: `./tools/lab/docker/down.sh` (add `-v` to wipe volumes including Samba/Keycloak).

**RAM:** ≥10 GB Colima / ≥16 GB host recommended. Lite `--enterprise` is lighter than `--enterprise-full`.

## Identity correlation standard

| System | Native key | Login | Employee id |
| --- | --- | --- | --- |
| HR / HCM mock | `userId` (e.g. MNB00001) | `name` (helen.ross) | `userId` |
| OpenLDAP | `uid` | `uid` | `employeeNumber` |
| Samba AD | `sAMAccountName` | `sAMAccountName` | `employeeNumber` |
| Keycloak | `username` | `username` | attribute `employeeId` |
| JDBC Core | `username` | `username` | `employee_id` |

**Master file:** [`lab-data/enterprise/identity-master.json`](../lab-data/enterprise/identity-master.json)  
**Generator:** `./tools/lab/enterprise/generate-identity-artifacts.py`

## App estate

| Meridian name | Backend | IIQ connector type |
| --- | --- | --- |
| MNB-HR | DelimitedFile CSV (enterprise: **non-authoritative** contrast) | Core Path authoritative; Enterprise Sandbox does not mint cubes from it |
| MNB-Workday | connector-mock `/hcm/v1/*` (+ UI `:8091/hcm/ui`) | Web Services — **authoritative** HCM; cubes in Lesson 207 |
| MNB-OpenLDAP | OpenLDAP | OpenLDAP - Direct |
| MNB-ActiveDirectory | Samba LDAP `:3890` | LDAP / OpenLDAP - Direct (enterprise pack) |
| MNB-Okta | Keycloak SCIM | SCIM 2.0 |
| MNB-CoreBanking | jdbc-pg | JDBC |
| MNB-WirePortal | connector-mock | Web Services / SCIM |
| MNB-EmployeePortal | :8092 | Logical / access via IdP groups |
| Gitea (dev portal) | :8093 | OIDC app (Keycloak client `gitea`) |
| Workstation / HR / Finance | :8094–8096 | SSO gates (group membership) |
| Mailpit | :8025 / SMTP :1025 | Not an IIQ app — email sink |
| MNB-EntraID | connector-mock `/entra/*` | SCIM/Graph-shaped (not real Entra) |
| MNB-PAM-CyberArk | pam-lab `:8097` | CyberArk-shaped (Vault backend) |
| MNB-Salesforce-CRM | connector-mock `/crm/scim/v2/*` | SCIM 2.0 |
| MNB-ServiceNow | connector-mock `/itsm/v1/*` | Web Services |

## SSD packs

See [`config/PACKS.md`](../config/PACKS.md).

| Pack | Contents |
| --- | --- |
| **Academy (CD)** | HelloWorld smoke only |
| **Lab seed** | HR + OpenLDAP + CSV stubs (default `up.sh --seed`) |
| **Enterprise** | Live AD/LDAP app, Workday WS, Okta SCIM, JDBC Core, CRM SCIM, LCM triggers, approval QuickLinks, cert definitions under `config/` |

Import enterprise objects after stack is healthy:

```bash
./tools/lab/enterprise/seed-enterprise.sh
```

`./tools/lab/docker/up.sh --enterprise` already overlays definitions-only core apps (`MNB-HR` **non-authoritative**, `MNB-OpenLDAP` definition, no account aggregation)→this pack. Pass `--wipe` for backup→reset first. Samba seed runs only when `mnb-samba-ad` is up (`--with=ad`).

**Workforce cubes are not created at seed.** Learners create the first Identity Warehouse population in Lesson **207** by aggregating authoritative `MNB-Workday` and running Identity Refresh (create identities). Use **MNB Workday** UI at http://localhost:8091/hcm/ui to browse/hire/terminate against the same HCM feed.

## Success criteria (DoD)

1. Log into IIQ as a directory user (OpenLDAP or Samba pass-through).
2. Joiner from HCM mock → accounts on AD + LDAP + IdP + JDBC + Wire.
3. User SSO into Employee Portal **and Gitea** via Keycloak; Wire access when entitled. Workstation/HR/Finance gates honor group grant/revoke.
4. Access request → multi-step approval (Mailpit proof) → provision → portal/app access gains.
5. Leaver → accounts disabled; SSO fails; cert/remediation for residuals.
6. Manager + app-owner certs: decide, sign-off, remediation visible.
7. SSD change → `./build.sh` / import → intentional impact; pack roll-forward.
8. Toolkit REST + MCP smoke against the live estate.
9. **Password (v3):** LCM/helpdesk reset updates OpenLDAP and/or Keycloak; old password fails SSO; new succeeds. Interceptor = Out of scope ([password/README.md](../lab-data/enterprise/password/README.md)).

## Enterprise Sandbox add-ons (251–254)

| Lesson | Focus |
| --- | --- |
| [251](lessons/251-workstation-grant-revoke.md) | Workstation grant → login → revoke lockout |
| [252](lessons/252-entra-shaped-lifecycle.md) | Entra-shaped mock agg/disable |
| [253](lessons/253-intranet-sso-apps.md) | HR + Finance independent gates |
| [254](lessons/254-password-reset-live.md) | Password reset proof (Lesson 61 live) |
| [255](lessons/255-privileged-vault-checkout.md) | PAM vault checkout (Lesson 86 live) |

Automated checks:

```bash
./tools/lab/enterprise/e2e-smoke.sh
./tools/lab/enterprise/contract-tests.sh
# Per-lesson PASS/FAIL asserts (SMTP config, apps, identities, …)
./tools/lab/enterprise/verify-lesson.sh 203
./tools/lab/enterprise/verify-lesson.sh --all
```

Assert specs: [`tools/lab/enterprise/lesson-asserts/`](../tools/lab/enterprise/lesson-asserts/).

## Feasibility boundaries

| In scope | Out of scope |
| --- | --- |
| Samba users/groups, LDAP bind, agg/provision attributes | IQService password/Exchange |
| Workday-**shaped** HCM API + WS connector | Native Workday connector against mock |
| Keycloak as Okta-**shaped** IdP | Native Okta connector / real Okta tenant |
| 200–2k identities | 50k+ production scale |
| SAP/RACF worksheets | Full local emulators |
| CyberArk-**shaped** PAM (Vault + pam-lab) | Licensed CyberArk PVWA / PSM video |

## Day-2 ops

| Task | Command / note |
| --- | --- |
| Re-seed identities | `./tools/lab/enterprise/generate-identity-artifacts.py && ./tools/lab/enterprise/seed-enterprise.sh` |
| Backup IIQ DB | `docker exec` pg_dump on `postgres` (see [`docs/enterprise/RUNBOOK.md`](enterprise/RUNBOOK.md)) |
| Reset Samba | `docker compose … down -v` then `--enterprise` up (LDIF bootstrap) |
| Promote pack | Export changed XML → `config/` → `./build.sh` → importdynamic (Lesson 101/108) |

## Curriculum cross-links

Classic **01–110** stays CSV-first pedagogy. After that track (or Capstone 50 + connectors), run the **Enterprise Sandbox Path**:

| | |
| --- | --- |
| Catalog | [`docs/lessons/_CATALOG_201_250.md`](lessons/_CATALOG_201_250.md) (includes 251–254 add-ons) |
| Style | [`docs/lessons/_SANDBOX_STYLE.md`](lessons/_SANDBOX_STYLE.md) |
| Lessons | [`201`](lessons/201-boot-enterprise-stack.md) → [`250`](lessons/250-capstone-bank-day.md) |

Mail: [`lab-data/enterprise/mail/README.md`](../lab-data/enterprise/mail/README.md) · Gitea OIDC: `./tools/lab/enterprise/configure-gitea-oidc.sh`

## File map

| Path | Purpose |
| --- | --- |
| `docker-compose.enterprise.yml` | Samba, Keycloak, portal, Mailpit, Gitea |
| `lab-data/enterprise/` | Identity master, Keycloak realm, Samba seed, mail notes |
| `tools/lab/enterprise/` | Generators, seed, e2e, Gitea OIDC helper |
| `tools/employee-portal/` | OIDC login proof app |
| `config/**/MNB-*` | Enterprise durable objects (plus Core) |
| `docs/enterprise/RUNBOOK.md` | Ops runbook |
| `docs/lessons/201-*.md` … `250-*.md` | Enterprise Sandbox Path |
