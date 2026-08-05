# Meridian National Bank — IdentityIQ Curriculum

**Classic track:** 110 lessons (01–110). **Enterprise Sandbox Path:** 50 practical lessons (201–250) on the production-like local estate.

One-stop **SailPoint IdentityIQ 8.5** curriculum for enterprise IAM engineers: governance basics **and** the full connector / customization surface (AD, LDAP, JDBC, Web Services, SCIM, SAP, Workday, mainframe, rules, workflows, plugins, SSB, hardening) — plus a live enterprise stack path after Capstone.

| | |
| --- | --- |
| **Company** | Meridian National Bank |
| **Domain** | `meridiannb.com` |
| **Your role** | IAM Engineer, Identity Governance |
| **Platform** | Local IIQ 8.5 lab (or homelab) |
| **Learn site** | https://sailpoint.lmsapp.us/ |
| **Style guide** | [_STYLE.md](_STYLE.md) |
| **Part II catalog** | [_CATALOG_51_110.md](_CATALOG_51_110.md) |
| **Sandbox Path (201–250)** | [_CATALOG_201_250.md](_CATALOG_201_250.md) · [_SANDBOX_STYLE.md](_SANDBOX_STYLE.md) |

---

## Before you start

Learner setup **is** the scoped bank setup: same SSB repo, same `config/` objects, same tokens—academy-sized Meridian, not HA prod.

1. Complete [LOCAL_SETUP.md](../LOCAL_SETUP.md) until you can log in as `spadmin` (or use the shared homelab URL).
2. Skim [INFRASTRUCTURE.md](../INFRASTRUCTURE.md), [SSD.md](../SSD.md), and [config/PACKS.md](../../config/PACKS.md) — CD ships **HelloWorld only**; you build the rest in lessons.
3. Lab CSV paths (Delimited File apps) — see [`lab-data/README.md`](../../lab-data/README.md):

| Lab mode | Path to paste into IIQ |
| --- | --- |
| Docker (`./tools/lab/docker/up.sh`) | `/opt/iiq-lab-data/HRApplications.txt` |
| Native Tomcat | `realpath ~/iiq-lab-data/HRApplications.txt` after copy below |

```bash
# Native Tomcat only (Docker already mounts repo lab-data/ → /opt/iiq-lab-data)
mkdir -p ~/iiq-lab-data ~/iiq-lab-evidence/$(date +%F)
cp lab-data/HRApplications.txt lab-data/EmployeeData.txt ~/iiq-lab-data/
cp -R lab-data/apps lab-data/scenarios lab-data/reference lab-data/notifications lab-data/connectors ~/iiq-lab-data/
realpath ~/iiq-lab-data/HRApplications.txt
# Skim bank-style HR columns:
# less lab-data/reference/hr-column-map.md
```

4. In Lesson 03, learn SSB layout / tokens. Set `%%MNB_*_FILE%%` when you **export** apps (usually Lesson 04+), not before you have Applications in git.
5. Homelab already imported HelloWorld via CD. On a laptop WAR, optional:

```bash
export SPTARGET=sandbox
./build.sh importdynamic   # smoke Rule only until you export your own objects
```

6. Live OpenLDAP, **jdbc-pg** (host **:5435**), and **connector-mock** (**:8091**) ship with `./tools/lab/docker/up.sh`. Standalone JDBC/mock if needed:

```bash
docker compose -f docker-compose.connectors.yml up -d jdbc-pg connector-mock
```

7. Keep a CHANGELOG of `MNB-*` objects you **create**, optional `config/` exports, and evidence screenshots.
8. After each lesson, run **Verify now** in the Academy (or the CLI) for **lab** lessons. Paperwork / design lessons disable live Verify — use **Mark binder complete** instead. Progress never comes from JSON paste.

```bash
./tools/lab/up.sh   # or ./tools/lab/docker/up.sh
# Open lesson → Lesson verify → Verify now

# CLI equivalent (writes evidence JSON only):
./tools/iiq-verify/verify-lesson.sh 04
```

See [LESSON_VERIFY.md](../LESSON_VERIFY.md). Specs cover lessons **01–110**.

---

## How each lesson is structured

See [_STYLE.md](_STYLE.md). Lessons are written as true tutorials: concepts and real-life context first, then guided setup, then verification — never a bare task list.

- **UI-first bank craft:** You **build** Meridian objects in each lesson. Optional export to [`config/`](../../config/) practices promotion (Lesson 101+). CD does **not** pre-create `MNB-HR` or other academy packs.
- HR attributes follow [`lab-data/reference/hr-column-map.md`](../../lab-data/reference/hr-column-map.md) across lessons 01–110 (`userId`, `managersAssociateID`, `exceptions=LOA`, `employeeType`, …).
- Connector lessons (51+) teach the **native connector as the primary path**, including real-world setup outside IIQ. A **lab-without-live-target** fallback keeps laptop training runnable.
- Early application lessons (09–16) use Delimited File on purpose; each has a **Production reality** box linking to the Part II connector lesson.
- Intermediate+ lessons end with **Further reading**.
- Lesson **03** = SSB awareness; **101 / 108** = promotion / multi-env maturity after you have objects worth exporting.

---

## Tracks

### Core Path — entry-level (default in Academy TOC)

- **Foundations:** 01–08 → **[08b Ticket triage](08b-day-in-the-life-ticket-triage.md)**
- **Applications:** 09–16 → **[mid-16](mid-16-apps-capstone.md)** → **[16b Task Results](16b-reading-task-results.md)**
- **Correlation:** 17–19 → **[19b Dirty data war room](19b-dirty-data-war-room.md)** → 20–22
- **Roles:** 23–28
- **Lifecycle:** 29 → **[29b LCM design](29b-lifecycle-events-rapid-setup.md)** → 30–34 → **[34b LCM in action](34b-lcm-automation-in-action.md)** → **[mid-34](mid-34-jml-capstone.md)**
- **Requests:** 35–36 → **[36b Be the approver](36b-be-the-approver.md)** → 37–38 → **[38b Configure approval flows](38b-approval-flows-lab.md)**
- **Policies:** 39–42
- **Certifications:** 43–46 → **[mid-46](mid-46-certs-capstone.md)**
- **Ops:** 47–49
- **Capstone I:** 50 → **[50b Choose your stack](50b-choose-your-stack.md)**

**Start here:** [First 90 days as an IIQ engineer](first-90-days.md) · roadmap: [_CORE_PATH_ROADMAP.md](_CORE_PATH_ROADMAP.md)

JML / HR scenario runners (upsert by `userId` — see [`lab-data/scenarios/README.md`](../../lab-data/scenarios/README.md)):

```bash
./tools/lab/scripts/scenarios/apply-joiner.sh
./tools/lab/scripts/scenarios/apply-mover.sh
./tools/lab/scripts/scenarios/apply-leaver.sh
./tools/lab/scripts/scenarios/apply-loa.sh
./tools/lab/scripts/scenarios/apply-rehire.sh
./tools/lab/scripts/scenarios/apply-batch-hire.sh
./tools/lab/scripts/scenarios/apply-contractor-end.sh
./tools/lab/scripts/scenarios/apply-bad-row.sh   # diagnose only
```

### Part II — Specialist tracks (opt-in after Capstone 50; hidden by default in Academy)

- **Connectors:** 51–55
- **Connectors — Directory:** 56–62
- **Connectors — Databases:** 63–67
- **Connectors — Web APIs & SaaS:** 68–76
- **Connectors — ERP / HR / Banking:** 77–82
- **Connectors — Infra, Logical, PAM:** 83–88
- **Rules, Workflows, Forms:** 89–96
- **Plugins, APIs & SSD:** 97–103
- **Enterprise Hardening & Mastery:** 104–110

---

## Coverage map (one-stop shop)

| Domain | Lessons | What you get |
| --- | --- | --- |
| Delimited / file HR & apps | 04–16 | Authoritative HR, inventory, per-app files |
| Connector architecture | 51–55 | Registry, selection matrix, IQService, aggregation/provisioning features |
| Directories & IdP | 56–62 | AD, LDAP, Entra ID, LDIF, passwords, authoritative vs target |
| Databases | 63–67 | JDBC, MSSQL, Oracle DB, SQLLoader |
| APIs & SaaS | 68–76 | Web Services, SCIM, Salesforce, ServiceNow, Okta, Google, M365, AWS IAM |
| ERP / HR / core banking | 77–82 | Workday, SAP HR, SAP Direct, PeopleSoft, Oracle EBS, RACF |
| Infra / Logical / PAM | 83–88 | Linux, Windows Local, Logical apps, PAM/CyberArk, MFA, Cloud Gateway |
| Rules / workflows / UI | 89–96 | Rule catalog, BeanShell/Java, LCM workflows, forms, QuickLinks, scopes |
| Plugins / APIs / SSD | 97–103 | Plugins, console, IIQ REST/SCIM, SSB promotion, Java services, branding |
| Hardening & mastery | 104–110 | Audit/SIEM, partitioning, performance, DR, multi-env, admin hardening, blueprint |

OOTB types from this repo’s `ConnectorRegistry` are mapped in `lab-data/connectors/connector-selection-matrix.csv`. Niche industry connectors (Epic, Meditech, Guidewire, …) reuse **Web Services / SCIM / JDBC / Logical** patterns taught in Part II.

---

## Learning path (110 lessons)

| # | Lesson | Track | Level | Time |
| ---: | --- | --- | --- | ---: |
| 01 | [Bank Briefing & UI Orientation](01-bank-briefing-and-ui.md) | Foundations | Beginner | 75–90 minutes |
| 02 | [Meridian Org Model & Risk Language](02-meridian-org-model.md) | Foundations | Beginner | 75–90 minutes |
| 03 | [Lab Hygiene, Naming & Evidence Habits](03-lab-hygiene-and-naming.md) | Foundations | Beginner | 45 minutes |
| 04 | [Authoritative HR Source](04-authoritative-hr-source.md) | Foundations | Beginner | 75–90 minutes |
| 05 | [HR Schema & Identity Attribute Design](05-hr-schema-and-identity-attrs.md) | Foundations | Beginner | 60–75 minutes |
| 06 | [Identity Cubes & Refresh](06-identity-cubes-and-refresh.md) | Foundations | Beginner | 60–75 minutes |
| 07 | [Populations & Identity Selectors](07-populations-and-selectors.md) | Foundations | Beginner | 60 minutes |
| 08 | [Task Operations & Scheduling Discipline](08-task-ops-and-scheduling.md) | Foundations | Beginner | 45–60 minutes |
| 09 | [Onboard IT Access Inventory App](09-it-access-inventory-app.md) | Applications | Beginner | 75–90 minutes |
| 10 | [Entitlement Dictionary & Managed Attributes](10-entitlement-dictionary.md) | Applications | Beginner | 60 minutes |
| 11 | [Onboard Core Banking Extract](11-onboard-core-banking.md) | Applications | Intermediate | 60–75 min |
| 12 | [Onboard SAP Finance](12-onboard-sap-finance.md) | Applications | Intermediate | 60–75 min |
| 13 | [Onboard AWS Cloud Admin](13-onboard-aws-cloud.md) | Applications | Intermediate | 60–75 min |
| 14 | [Onboard Wire Portal (Dual Control)](14-onboard-wire-portal.md) | Applications | Intermediate | 60–90 min |
| 15 | [Directory, CRM & Digital Channel Apps](15-onboard-directory-and-crm.md) | Applications | Intermediate | 75–90 min |
| 16 | [Multi-App Aggregation Strategy](16-multi-app-aggregation-strategy.md) | Applications | Intermediate | 60–75 min |
| 17 | [Account Correlation Basics](17-correlation-basics.md) | Correlation | Intermediate | 60–75 min |
| 18 | [Correlation Rules & Edge Cases](18-correlation-rules-advanced.md) | Correlation | Intermediate | 60–90 min |
| 19 | [Uncorrelated Account Remediation](19-uncorrelated-remediation.md) | Correlation | Intermediate | 60–75 min |
| 20 | [Orphan & Dormant Access Hunting](20-orphan-dormant-hunting.md) | Correlation | Intermediate | 60–75 min |
| 21 | [Manager Hierarchy & Reassignment](21-manager-hierarchy.md) | Correlation | Intermediate | 45–60 minutes |
| 22 | [Identity Attribute Sync Hygiene](22-attribute-sync-hygiene.md) | Correlation | Intermediate | 45–60 minutes |
| 23 | [Role Model Introduction](23-role-model-intro.md) | Roles | Intermediate | 45–60 minutes |
| 24 | [Birthright Employee Role](24-birthright-employee-role.md) | Roles | Intermediate | 60–90 minutes |
| 25 | [Department & Job-Based Roles](25-dept-job-roles.md) | Roles | Intermediate | 60–90 minutes |
| 26 | [IT Role Packaging & Least Privilege](26-it-role-packaging.md) | Roles | Intermediate | 45–60 minutes |
| 27 | [Role Detection vs Assignment](27-role-detection-vs-assignment.md) | Roles | Intermediate | 45–60 minutes |
| 28 | [Privileged Access Role Design](28-privileged-access-roles.md) | Roles | Advanced | 60–75 minutes |
| 29 | [Joiner Lifecycle](29-joiner-lifecycle.md) | Lifecycle | Intermediate | 60–90 minutes |
| 30 | [Mover / Transfer Events](30-mover-transfers.md) | Lifecycle | Intermediate | 60–90 minutes |
| 31 | [Leaver & Access Disablement](31-leaver-disablement.md) | Lifecycle | Intermediate | 60–90 minutes |
| 32 | [Contractor & Contingent Worker Lifecycle](32-contractor-lifecycle.md) | Lifecycle | Intermediate | 60–75 minutes |
| 33 | [Leave of Absence Controls](33-leave-of-absence.md) | Lifecycle | Intermediate | 45–60 minutes |
| 34 | [Rapid Offboarding Incident Drill](34-rapid-offboarding-drill.md) | Lifecycle | Advanced | 60–75 minutes |
| 34b | [LCM Automation in Action](34b-lcm-automation-in-action.md) | Lifecycle | Intermediate | 75–90 minutes |
| 35 | [Access Request Catalog](35-access-request-catalog.md) | Requests | Intermediate | 60–90 minutes |
| 36 | [Approval Chains & Escalations](36-approval-chains.md) | Requests | Intermediate | 60–75 minutes |
| 37 | [Emergency / Break-Glass Access](37-break-glass-access.md) | Requests | Advanced | 60–75 minutes |
| 38 | [IdentityRequest Tracking & Auditing](38-identity-request-tracking.md) | Requests | Intermediate | 45–60 minutes |
| 38b | [Configure Approval Flows in IdentityIQ](38b-approval-flows-lab.md) | Requests | Intermediate | 75–90 minutes |
| 39 | [SoD Fundamentals for Banking](39-sod-fundamentals.md) | Policies | Intermediate | 60–75 minutes |
| 40 | [Payment Dual-Control Policy Deep Dive](40-payment-dual-control-policy.md) | Policies | Advanced | 60–75 minutes |
| 41 | [Policy Violations & Mitigation](41-policy-violations-mitigation.md) | Policies | Intermediate | 60–75 |
| 42 | [Risk Scores & Scoring Models](42-risk-scores.md) | Policies | Advanced | 45–60 |
| 43 | [Manager Access Certifications](43-manager-certifications.md) | Certifications | Intermediate | 90–120 |
| 44 | [Application Owner Certifications](44-app-owner-certifications.md) | Certifications | Intermediate | 60–90 |
| 45 | [Targeted & Focused Campaigns](45-targeted-campaigns.md) | Certifications | Advanced | 45–60 |
| 46 | [Certification Remediation & Evidence](46-cert-remediation-evidence.md) | Certifications | Intermediate | 60–75 |
| 47 | [Provisioning Plans & Troubleshooting](47-provisioning-troubleshooting.md) | Ops | Advanced | 90 |
| 48 | [Audit-Ready Reporting & Dashboards](48-audit-ready-reporting.md) | Ops | Intermediate | 60–90 |
| 49 | [Email Templates & Notifications](49-email-templates-notifications.md) | Ops | Intermediate | 45–60 |
| 50 | [Capstone: Exam Readiness & Go-Live Checklist](50-capstone-exam-readiness.md) | Capstone | Advanced | 90–120 |
| 51 | [Connector Landscape & Registry](51-connector-landscape-and-registry.md) | Connectors | Intermediate | 60–75 minutes |
| 52 | [Connector Selection for Meridian](52-connector-selection-for-meridian.md) | Connectors | Intermediate | 60–75 minutes |
| 53 | [IQService Architecture](53-iqservice-architecture.md) | Connectors | Intermediate | 60–90 minutes |
| 54 | [Aggregation Patterns Advanced](54-aggregation-patterns-advanced.md) | Connectors | Intermediate | 60–90 minutes |
| 55 | [Provisioning Feature Matrix](55-provisioning-feature-matrix.md) | Connectors | Intermediate | 60–75 minutes |
| 56 | [Active Directory Connector](56-active-directory-connector.md) | Connectors — Directory | Intermediate | 75–90 minutes |
| 57 | [AD Groups, OUs & Exchange](57-ad-groups-ous-exchange.md) | Connectors — Directory | Intermediate | 60–90 minutes |
| 58 | [LDAP / OpenLDAP Connector](58-ldap-openldap-connector.md) | Connectors — Directory | Intermediate | 75–90 minutes |
| 59 | [Azure / Entra ID Connector](59-azure-entra-id-connector.md) | Connectors — Directory | Intermediate | 60–90 minutes |
| 60 | [LDIF Connector](60-ldif-connector.md) | Connectors — Directory | Intermediate | 60–75 minutes |
| 61 | [Password Management & Interceptor](61-password-management-interceptor.md) | Connectors — Directory | Intermediate | 60–90 minutes |
| 62 | [Directory Authoritative vs Target](62-directory-authoritative-vs-target.md) | Connectors — Directory | Intermediate | 60–75 minutes |
| 63 | [JDBC Connector Fundamentals](63-jdbc-connector-fundamentals.md) | Connectors — Databases | Intermediate | 75–90 minutes |
| 64 | [JDBC Provisioning Policies](64-jdbc-provisioning-policies.md) | Connectors — Databases | Intermediate | 75–90 minutes |
| 65 | [Microsoft SQL Server Direct Connector](65-mssql-direct-connector.md) | Connectors — Databases | Intermediate | 60–90 minutes |
| 66 | [Oracle Database Direct Connector](66-oracle-db-direct-connector.md) | Connectors — Databases | Intermediate | 75–90 min |
| 67 | [SQLLoader & Bulk Load Patterns](67-sqlloader-bulk-patterns.md) | Connectors — Databases | Intermediate | 60–75 min |
| 68 | [Web Services Connector](68-web-services-connector.md) | Connectors — Web APIs & SaaS | Intermediate | 75–90 min |
| 69 | [SCIM 2.0 Connector](69-scim2-connector.md) | Connectors — Web APIs & SaaS | Intermediate | 75–90 min |
| 70 | [SCIM Custom Schemas & Enterprise Attributes](70-scim-custom-schemas.md) | Connectors — Web APIs & SaaS | Intermediate | 60–75 min |
| 71 | [Salesforce Native Connector](71-salesforce-native-connector.md) | Connectors — Web APIs & SaaS | Intermediate | 75–90 min |
| 72 | [ServiceNow Connector](72-servicenow-connector.md) | Connectors — Web APIs & SaaS | Intermediate | 75–90 min |
| 73 | [Okta Workforce IdP Connector](73-okta-connector.md) | Connectors — Web APIs & SaaS | Intermediate | 75–90 min |
| 74 | [Google Workspace Connector](74-google-workspace-connector.md) | Connectors — Web APIs & SaaS | Intermediate | 75–90 min |
| 75 | [M365 & SharePoint Online Connectors](75-m365-sharepoint-online.md) | Connectors — Web APIs & SaaS | Intermediate | 75–90 min |
| 76 | [AWS IAM Connector](76-aws-iam-connector.md) | Connectors — Web APIs & SaaS | Intermediate | 75–90 min |
| 77 | [Workday HCM Connector](77-workday-hcm-connector.md) | Connectors — ERP / HR / Banking | Intermediate | 75–90 min |
| 78 | [SAP HR/HCM Connector](78-sap-hr-hcm-connector.md) | Connectors — ERP / HR / Banking | Intermediate | 75–90 min |
| 79 | [SAP Direct Security Connector](79-sap-direct-security.md) | Connectors — ERP / HR / Banking | Intermediate | 75–90 min |
| 80 | [PeopleSoft HCM Connector](80-peoplesoft-hcm-connector.md) | Connectors — ERP / HR / Banking | Intermediate | 75–90 min |
| 81 | [Oracle E-Business Suite Connector](81-oracle-ebs-connector.md) | Connectors — ERP / HR / Banking | Intermediate | 60–90 min |
| 82 | [Mainframe RACF for Banking](82-mainframe-racf-banking.md) | Connectors — ERP / HR / Banking | Intermediate | 60–90 min |
| 83 | [Linux / Unix Connector](83-linux-unix-connector.md) | Connectors — Infra, Logical, PAM | Intermediate | 60–90 min |
| 84 | [Windows Local Connector](84-windows-local-connector.md) | Connectors — Infra, Logical, PAM | Intermediate | 60–90 min |
| 85 | [Logical Applications](85-logical-applications.md) | Connectors — Infra, Logical, PAM | Intermediate | 60–90 min |
| 86 | [PAM / CyberArk Module](86-pam-cyberark-module.md) | Connectors — Infra, Logical, PAM | Advanced | 75–90 min |
| 87 | [Duo MFA Integration Patterns](87-duo-mfa-integration-patterns.md) | Connectors — Infra, Logical, PAM | Intermediate | 60–75 min |
| 88 | [Connector Gateway / Cloud Patterns](88-connector-gateway-cloud-patterns.md) | Connectors — Infra, Logical, PAM | Intermediate | 60–90 min |
| 89 | [Rule Types Catalog](89-rule-types-catalog.md) | Rules, Workflows, Forms | Intermediate | 60–90 min |
| 90 | [BeanShell vs Java Rules](90-beanshell-vs-java-rules.md) | Rules, Workflows, Forms | Intermediate | 60–75 min |
| 91 | [Before / After Provisioning Rules](91-before-after-provisioning-rules.md) | Rules, Workflows, Forms | Advanced | 75–90 min |
| 92 | [Identity Attribute Rules](92-identity-attribute-rules.md) | Rules, Workflows, Forms | Intermediate | 60–90 min |
| 93 | [LCM Workflow Customization](93-workflow-lcm-customization.md) | Rules, Workflows, Forms | Advanced | 75–90 min |
| 94 | [Forms and Field Validation](94-forms-and-field-validation.md) | Rules, Workflows, Forms | Intermediate | 60–90 min |
| 95 | [QuickLinks and Custom UI](95-quicklinks-custom-ui.md) | Rules, Workflows, Forms | Intermediate | 60–90 min |
| 96 | [Workgroups, Capabilities & Scopes](96-workgroups-capabilities-scopes.md) | Rules, Workflows, Forms | Intermediate | 60–75 minutes |
| 97 | [Plugin Framework Basics](97-plugin-framework-basics.md) | Plugins, APIs & SSD | Intermediate | 60–75 minutes |
| 98 | [Build Meridian Toolkit Plugin](98-build-meridian-toolkit-plugin.md) | Plugins, APIs & SSD | Advanced | 75–90 minutes |
| 99 | [IIQ Console & Automation](99-iiq-console-and-automation.md) | Plugins, APIs & SSD | Intermediate | 60–75 minutes |
| 100 | [IIQ REST & SCIM APIs](100-iiq-rest-scim-apis.md) | Plugins, APIs & SSD | Intermediate | 60–90 minutes |
| 101 | [SSB/SSD Promotion Discipline](101-ssb-ssd-promotion-discipline.md) | Plugins, APIs & SSD | Intermediate | 60–90 minutes |
| 102 | [Custom Java Services](102-custom-java-services.md) | Plugins, APIs & SSD | Advanced | 75–90 minutes |
| 103 | [UI Customization & Branding](103-ui-customization-branding.md) | Plugins, APIs & SSD | Intermediate | 60–75 minutes |
| 104 | [AuditConfig & SIEM](104-auditconfig-and-siem.md) | Enterprise Hardening & Mastery | Intermediate | 60–90 minutes |
| 105 | [Partitioning & Task Servers](105-partitioning-task-servers.md) | Enterprise Hardening & Mastery | Intermediate | 60–90 minutes |
| 106 | [Performance Tuning IIQ](106-performance-tuning-iiq.md) | Enterprise Hardening & Mastery | Advanced | 75–90 minutes |
| 107 | [Backup, DR & Object Recovery](107-backup-dr-object-recovery.md) | Enterprise Hardening & Mastery | Advanced | 75–90 minutes |
| 108 | [Multi-Environment Promotion](108-multi-env-promotion.md) | Enterprise Hardening & Mastery | Advanced | 75–90 minutes |
| 109 | [Hardening spadmin & Capabilities](109-hardening-spadmin-capabilities.md) | Enterprise Hardening & Mastery | Advanced | 75–90 minutes |
| 110 | [Ultimate Meridian Production Blueprint (Capstone)](110-ultimate-blueprint-capstone.md) | Enterprise Hardening & Mastery | Advanced (Capstone) | 120–150 minutes |

---

## Suggested pace (Core Path first)

| Block | Lessons | Focus |
| --- | --- | --- |
| Weeks 1–2 | 01–08b, 09–16, mid-16, 16b | Foundations, ticket triage, file apps, Task Results |
| Weeks 3–4 | 17–19b–22, 23–28, 29–29b–34–34b, mid-34 | Correlation war room, roles, JML (+ practical LCM events) |
| Weeks 5–6 | 35–36b–38–38b, 39–46, mid-46, 47–50 | Approver chair, configure IIQ approval schemes, SoD, certs, ops, Capstone I |
| Weeks 7+ | Specialist opt-in | Pick Directory/JDBC or SaaS/ERP after Capstone 50 |

Full catalog (if you unlock specialist tracks):

| Block | Lessons | Focus |
| --- | --- | --- |
| Weeks 7–9 | 51–76 | Connector architecture → SaaS |
| Weeks 10–11 | 77–88 | ERP, mainframe, PAM |
| Weeks 12–13 | 89–103 | Rules, plugins, SSD |
| Week 14 | 104–110 | Hardening + ultimate blueprint |

Self-paced: ~45–60 lab hours for Core Path; ~90–120 for the full 110.

---

## Enterprise Sandbox Path (lessons 201–250)

**After** the classic 110-lesson bundle: a production-like local estate with Mailpit, Samba AD, Keycloak, Employee Portal, Gitea, HCM/CRM/ITSM mocks, and live JDBC/LDAP — practical instructions only (no worksheets).

| | |
| --- | --- |
| **Catalog** | [_CATALOG_201_250.md](_CATALOG_201_250.md) |
| **Style** | [_SANDBOX_STYLE.md](_SANDBOX_STYLE.md) |
| **Stack** | [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md) · `./tools/lab/docker/up.sh --enterprise` |
| **Start → finish** | [201 Boot](201-boot-enterprise-stack.md) → [250 Capstone: Full Bank Day](250-capstone-bank-day.md) |

Covers the governance + connector surface from 01–110 **hands-on on the live stack**, plus advanced drills the CSV Core path cannot (SSO proof apps, catch-all mail, HCM API joiners, dual SSO apps).

| Block | Lessons | Focus |
| --- | --- | --- |
| Boot & mail | 201–203 | Enterprise up, seed, Mailpit |
| Directories & SSO | 204–213 | LDAP/AD, pass-through, HCM/JDBC/WS/SCIM, Keycloak, Portal, Gitea |
| Birthright & JML | 214–220 | Correlation, sync, roles, joiner/mover/leaver/contractor |
| Requests & certs | 221–232 | Approvals+mail, SoD, certs, remediation, reports, templates |
| Depth & build | 233–249 | Connector stretch, rules/workflows/forms/QL, APIs, SSD, hardening |
| Capstone | 250 | Full bank day + Enterprise Lab DoD |
| v3 add-ons | 251–255 | Workstation, Entra, intranet SSO, password reset, PAM vault |

| # | Title | Time |
| --- | --- | --- |
| 201 | [Boot the Enterprise Sandbox](201-boot-enterprise-stack.md) | ~25 min |
| 202 | [Identity Master & Enterprise Seed](202-identity-master-and-seed.md) | ~30 min |
| 203 | [Catch All Mail in Mailpit](203-mailpit-iiq-email.md) | ~20 min |
| 204 | [Operate Live OpenLDAP](204-openldap-live-ops.md) | ~35 min |
| 205 | [Operate Samba AD](205-samba-ad-live-ops.md) | ~40 min |
| 206 | [Pass-Through Login to IIQ](206-passthrough-iiq-login.md) | ~25 min |
| 207 | [Authoritative HCM (Workday-Shaped)](207-hcm-workday-shaped.md) | ~35 min |
| 208 | [JDBC Core Banking Live](208-jdbc-core-banking.md) | ~35 min |
| 209 | [Wire Portal Web Services](209-wire-webservices.md) | ~30 min |
| 210 | [CRM via SCIM Mock](210-crm-scim.md) | ~25 min |
| 211 | [Keycloak as Workforce IdP](211-keycloak-okta-shaped.md) | ~30 min |
| 212 | [Employee Portal SSO Proof](212-employee-portal-sso.md) | ~20 min |
| 213 | [Second App: Gitea via OIDC](213-gitea-sso-app.md) | ~35 min |
| 214 | [Nail Correlation Across Live Apps](214-correlation-standard-live.md) | ~30 min |
| 215 | [Attribute Sync on Live Targets](215-attribute-sync-live.md) | ~30 min |
| 216 | [Birthright Roles Against Live Apps](216-birthright-roles-live.md) | ~35 min |
| 217 | [Joiner LCM End-to-End](217-joiner-lcm-live.md) | ~45 min |
| 218 | [Mover LCM End-to-End](218-mover-lcm-live.md) | ~35 min |
| 219 | [Leaver LCM End-to-End](219-leaver-lcm-live.md) | ~40 min |
| 220 | [Contractor & LOA Controls Live](220-contractor-loa-live.md) | ~35 min |
| 221 | [Build a Live Request Catalog](221-access-catalog-live.md) | ~35 min |
| 222 | [Approvals With Mailpit Proof](222-approvals-and-mail.md) | ~40 min |
| 223 | [Break-Glass Access Drill](223-break-glass-live.md) | ~30 min |
| 224 | [SoD: Wire Dual Control Live](224-sod-wire-live.md) | ~35 min |
| 225 | [Work Violations & Mitigations](225-policy-violations-live.md) | ~30 min |
| 226 | [Manager Cert + Email](226-manager-cert-mail.md) | ~45 min |
| 227 | [App-Owner Certification Live](227-app-owner-cert-live.md) | ~40 min |
| 228 | [Targeted / Focused Campaign](228-targeted-cert-live.md) | ~30 min |
| 229 | [Certification Remediation Proof](229-cert-remediation-live.md) | ~35 min |
| 230 | [Troubleshoot a Failed Provision](230-provisioning-troubleshoot-live.md) | ~40 min |
| 231 | [Audit-Ready Reports Live](231-audit-reports-live.md) | ~30 min |
| 232 | [Tune Email Templates Live](232-email-templates-live.md) | ~30 min |
| 233 | [Live Aggregation Runbook](233-aggregation-strategy-live.md) | ~25 min |
| 234 | [AD Groups & OUs on Samba](234-ad-groups-ous-live.md) | ~35 min |
| 235 | [OpenLDAP Provision Stretch](235-ldap-provision-stretch.md) | ~30 min |
| 236 | [JDBC Create/Disable Policies](236-jdbc-provision-policies.md) | ~35 min |
| 237 | [Web Services Connector Depth](237-ws-connector-deep.md) | ~35 min |
| 238 | [SCIM Connector Depth](238-scim-connector-deep.md) | ~30 min |
| 239 | [ITSM Ticket Mock Fulfillment](239-itsm-ticket-mock.md) | ~30 min |
| 240 | [Logical Application Over Live Apps](240-logical-application-live.md) | ~30 min |
| 241 | [Before/After Provisioning Rules](241-rules-before-after-live.md) | ~40 min |
| 242 | [Customize an LCM Workflow](242-workflow-lcm-customize.md) | ~45 min |
| 243 | [Forms & Field Validation](243-forms-live.md) | ~30 min |
| 244 | [QuickLinks That Operators Use](244-quicklinks-live.md) | ~25 min |
| 245 | [Workgroups, Capabilities, Scopes](245-workgroups-scopes-live.md) | ~35 min |
| 246 | [Toolkit / MCP Operator APIs](246-toolkit-apis-live.md) | ~35 min |
| 247 | [IIQ REST & SCIM Live](247-iiq-rest-scim-live.md) | ~35 min |
| 248 | [SSD Export & Promote](248-ssd-promote-live.md) | ~40 min |
| 249 | [Hardening & Perf Lite](249-hardening-perf-lite.md) | ~35 min |
| 250 | [Capstone: Full Bank Day E2E](250-capstone-bank-day.md) | ~60 min |

---

## Need help?

- Setup → [LOCAL_SETUP.md](../LOCAL_SETUP.md)
- Homelab / public site → [HOMELAB-CD.md](../HOMELAB-CD.md), [LEARN-SITE.md](../LEARN-SITE.md)
- SSD build → [SSD.md](../SSD.md)
- Connector fixtures → [../../lab-data/connectors/README.md](../../lab-data/connectors/README.md)
- Enterprise sandbox → [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md) · [_CATALOG_201_250.md](_CATALOG_201_250.md)
