# Enterprise Sandbox Path — Lessons 201–258

**Standalone** Meridian IdentityIQ curriculum on `--enterprise` Docker (directories, IdP, HCM, JDBC, Wire/CRM, Mailpit, Gitea, Employee Portal). Classic **01–110** is an optional archive once you finish this path — not a prerequisite.

| | |
| --- | --- |
| **Style** | [_SANDBOX_STYLE.md](_SANDBOX_STYLE.md) — exemplar [223](223-break-glass-live.md) |
| **Coverage map** | [_COVERAGE_01_110.md](_COVERAGE_01_110.md) (classic → sandbox absorption) |
| **Stack guide** | [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md) |
| **Start** | `./tools/lab/docker/up.sh --enterprise` then [201](201-boot-enterprise-stack.md); add `--with=ad|sso|pam` per lesson |
| **Finish live** | [250 Capstone](250-capstone-bank-day.md) then optional [251–255](251-workstation-grant-revoke.md) |
| **Theory** | [256–258](256-connector-registry-theory.md) (registry, IQService, LDIF) |

No worksheets. **Why** → **What this is** / **Know these** / **Do this** (Tasks with Why/Expect) / **If it fails** / **Feedback**.

---

## Arc

| Block | Lessons | Focus |
| --- | --- | --- |
| Boot & master | 201–202 | Stack + identity master (definitions only — **no** workforce cubes) |
| First cubes (HCM) | **207** | Aggregate `MNB-Workday` + refresh → Warehouse; HCM UI hire |
| Mail | 203 | Mailpit SMTP (no cubes required) |
| Directories & SSO | 204–206, 211–213 | OpenLDAP, Samba AD, pass-through (**after** 207), Keycloak, Portal, Gitea |
| Live apps | 208–210, 214–216 | JDBC, Wire WS, CRM SCIM, correlation, sync, birthright |
| JML | 217–220 | Joiner / mover / leaver / contractor-LOA → elevated access via **request catalog** (221+) |
| Requests & governance | 221–232 | Catalog → approvals → break-glass → SoD → certs → reports → templates |
| Connectors depth | 233–240 | Agg runbook, AD groups/OUs, LDAP/JDBC/WS/SCIM stretch, ITSM, logical |
| Build & operate | 241–249 | Rules, workflows, forms, QuickLinks, scopes, toolkit/REST, SSD, hardening |
| Capstone | 250 | Full bank day |
| v3 add-ons | 251–255 | Workstation, Entra-shaped, intranet SSO, password reset, Vault/PAM |
| **Theory** | **256–258** | Connector registry/selection, IQService architecture, LDIF offline evidence |

> **Path note:** After 202, do **207** before **204–206**. Mail (203) can slot anytime after 201. Theory **256** after you have built at least one live app; **257** after 205; **258** after 235.

---

## Catalog

| # | Lesson | Mins | Maps (classic) |
| --- | --- | --- | --- |
| 201 | [Boot the Enterprise Sandbox](201-boot-enterprise-stack.md) | 45 | N+4 infra / 103 cue |
| 202 | [Identity Master & Enterprise Seed](202-identity-master-and-seed.md) | 45 | Packs |
| **207** | [Authoritative HCM (Workday-Shaped)](207-hcm-workday-shaped.md) | 70 | 77 — **first cubes** |
| 203 | [Catch All Mail in Mailpit](203-mailpit-iiq-email.md) | 45 | 49 |
| 204 | [Operate Live OpenLDAP](204-openldap-live-ops.md) | 55 | 58 |
| 205 | [Operate Samba AD](205-samba-ad-live-ops.md) | 65 | 56–57 |
| 206 | [Pass-Through Login to IIQ](206-passthrough-iiq-login.md) | 40 | 61 / auth |
| 208 | [JDBC Core Banking Live](208-jdbc-core-banking.md) | 55 | 63–64 |
| 209 | [Wire Portal Web Services](209-wire-webservices.md) | 50 | 68 |
| 210 | [CRM via SCIM Mock](210-crm-scim.md) | 40 | 69–71 |
| 211 | [Keycloak as Workforce IdP](211-keycloak-okta-shaped.md) | 70 | 73 |
| 212 | [Employee Portal SSO Proof](212-employee-portal-sso.md) | 35 | DoD #3 |
| 213 | [Second App: Gitea via OIDC](213-gitea-sso-app.md) | 60 | 73 / SSO |
| 214 | [Nail Correlation Across Live Apps](214-correlation-standard-live.md) | 50 | 17–19 / 21 |
| 215 | [Attribute Sync on Live Targets](215-attribute-sync-live.md) | 50 | 20 / 30 |
| 216 | [Birthright Roles Against Live Apps](216-birthright-roles-live.md) | 60 | 23–28 |
| 217 | [Joiner LCM End-to-End](217-joiner-lcm-live.md) | 70 | 29–34b |
| 218 | [Mover LCM End-to-End](218-mover-lcm-live.md) | 70 | 30 |
| 219 | [Leaver LCM End-to-End](219-leaver-lcm-live.md) | 85 | 31 / 34 / 20 |
| 220 | [Contractor & LOA Controls Live](220-contractor-loa-live.md) | 70 | 32–33 |
| 221 | [Build a Live Request Catalog](221-access-catalog-live.md) | 70 | 35 / 10 |
| 222 | [Approvals With Mailpit Proof](222-approvals-and-mail.md) | 80 | 36 / 38b |
| 223 | [Break-Glass Access Drill](223-break-glass-live.md) | 90 | 37 |
| 224 | [SoD: Wire Dual Control Live](224-sod-wire-live.md) | 75 | 39–40 |
| 225 | [Work Violations & Mitigations](225-policy-violations-live.md) | 70 | 41–42 |
| 226 | [Manager Cert + Email](226-manager-cert-mail.md) | 90 | 43 / 21 |
| 227 | [App-Owner Certification Live](227-app-owner-cert-live.md) | 75 | 44 / 10 |
| 228 | [Targeted / Focused Campaign](228-targeted-cert-live.md) | 65 | 45 / 07 |
| 229 | [Certification Remediation Proof](229-cert-remediation-live.md) | 70 | 46 |
| 230 | [Troubleshoot a Failed Provision](230-provisioning-troubleshoot-live.md) | 80 | 47 / 55 |
| 231 | [Audit-Ready Reports Live](231-audit-reports-live.md) | 55 | 48 / 104 |
| 232 | [Tune Email Templates Live](232-email-templates-live.md) | 60 | 49 |
| 233 | [Live Aggregation Runbook](233-aggregation-strategy-live.md) | 50 | 16 / 08 / 54 |
| 234 | [AD Groups & OUs on Samba](234-ad-groups-ous-live.md) | 65 | 57 |
| 235 | [OpenLDAP Provision Stretch](235-ldap-provision-stretch.md) | 55 | 58 |
| 236 | [JDBC Create/Disable Policies](236-jdbc-provision-policies.md) | 80 | 64 |
| 237 | [Web Services Connector Depth](237-ws-connector-deep.md) | 70 | 68 |
| 238 | [SCIM Connector Depth](238-scim-connector-deep.md) | 65 | 69–70 |
| 239 | [ITSM Ticket Mock Fulfillment](239-itsm-ticket-mock.md) | 70 | 72 |
| 240 | [Logical Application Over Live Apps](240-logical-application-live.md) | 70 | 85 |
| 241 | [Before/After Provisioning Rules](241-rules-before-after-live.md) | 80 | 91 |
| 242 | [Customize an LCM Workflow](242-workflow-lcm-customize.md) | 85 | 93 |
| 243 | [Forms & Field Validation](243-forms-live.md) | 80 | 94 |
| 244 | [QuickLinks That Operators Use](244-quicklinks-live.md) | 75 | 95 |
| 245 | [Workgroups, Capabilities, Scopes](245-workgroups-scopes-live.md) | 90 | 96 / 07 |
| 246 | [Toolkit / MCP Operator APIs](246-toolkit-apis-live.md) | 85 | 97–100 |
| 247 | [IIQ REST & SCIM Live](247-iiq-rest-scim-live.md) | 80 | 100 |
| 248 | [SSD Export & Promote](248-ssd-promote-live.md) | 100 | 101 / 108 / 103 |
| 249 | [Hardening & Perf Lite](249-hardening-perf-lite.md) | 80 | 105–109 |
| 250 | [Capstone: Full Bank Day E2E](250-capstone-bank-day.md) | 110 | 50 / 110 / DoD |
| 251 | [Workstation Grant → Login → Revoke](251-workstation-grant-revoke.md) | 80 | 83–84 |
| 252 | [Entra-Shaped Lifecycle](252-entra-shaped-lifecycle.md) | 75 | 59 |
| 253 | [Intranet SSO Apps](253-intranet-sso-apps.md) | 70 | 73 |
| 254 | [Password Reset Live](254-password-reset-live.md) | 85 | 61–62 |
| 255 | [Privileged Vault Checkout](255-privileged-vault-checkout.md) | 95 | 86 |
| **256** | [Connector Registry & Selection (Theory)](256-connector-registry-theory.md) | 50 | **51–52 / 55** |
| **257** | [IQService Architecture (Theory)](257-iqservice-architecture-theory.md) | 45 | **53** |
| **258** | [LDIF Offline Directory Evidence (Theory)](258-ldif-offline-evidence-theory.md) | 45 | **60** |

**Total guided time:** ~40–50 hours (self-paced; theory + capstone included).

---

## vs Classic 01–110

| Classic | Sandbox |
| --- | --- |
| Required before enterprise | **Optional archive** — concepts absorbed into 2xx Know these + Theory 256–258 |
| CSV-first Core + worksheets | Live estate from lesson 201 |
| Capstones 50 & 110 | Capstone 250 = bank day on enterprise stack |

---

## Sunset note

When [_COVERAGE_01_110.md](_COVERAGE_01_110.md) marks a classic topic `strong`, `replaced-by-live`, or theory (**256–258**), Enterprise-only cohorts need not run the classic lesson. Keep classic files as reference until your program formally retires 01–110.
