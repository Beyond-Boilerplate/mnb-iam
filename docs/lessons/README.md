# Meridian National Bank — IdentityIQ 50-Lesson Enterprise Bundle

Hands-on **SailPoint IdentityIQ 8.5** curriculum for enterprise IAM training, taught through realistic work at fictitious **Meridian National Bank (MNB)**.

| | |
| --- | --- |
| **Company** | Meridian National Bank |
| **Domain** | `meridiannb.com` |
| **Your role** | IAM Engineer, Identity Governance |
| **Platform** | Local IIQ 8.5 lab from this repo (or homelab) |
| **Learn site** | https://sailpoint.lmsapp.us/ |
| **Style guide** | [_STYLE.md](_STYLE.md) |

---

## Before you start

1. Complete [LOCAL_SETUP.md](../LOCAL_SETUP.md) until you can log in as `spadmin`.
2. Skim [INFRASTRUCTURE.md](../INFRASTRUCTURE.md) for vocabulary.
3. Copy lab fixtures:

```bash
mkdir -p ~/iiq-lab-data ~/iiq-lab-evidence/$(date +%F)
cp lab-data/HRApplications.txt lab-data/EmployeeData.txt ~/iiq-lab-data/
cp -R lab-data/apps lab-data/scenarios lab-data/reference lab-data/notifications ~/iiq-lab-data/
```

4. Keep a lab notebook / CHANGELOG with `MNB-` object names and dated evidence screenshots.

---

## How each lesson is structured

Every module follows the enterprise tutorial pattern in [_STYLE.md](_STYLE.md):

| Section | Purpose |
| --- | --- |
| Learning objectives | Measurable “you will be able to…” outcomes |
| Why this matters | Business + control/audit framing |
| Concepts | Tables, flows, IIQ vocabulary |
| Before you start | Prerequisites checklist |
| Lab procedure | Click-path tasks with **Expected result** / **If it fails** |
| Acceptance criteria | Definition of done |
| Troubleshooting | Common failures and fixes |
| Training binder evidence | What to keep for exam packs |
| Knowledge check | Questions **with answers** |
| Stretch lab | Optional harder practice |
| Summary | What you built |

---

## Tracks

- **Foundations:** 01–08 — UI, org model, HR authoritative source, refresh, populations, tasks
- **Applications:** 09–16 — IT inventory, entitlement catalog, Core/SAP/AWS/Wire/AD/CRM/digital, aggregation strategy
- **Correlation:** 17–22 — matching, orphans, dormant access, managers, attribute hygiene
- **Roles:** 23–28 — birthright, job roles, least privilege, privileged access
- **Lifecycle:** 29–34 — joiner / mover / leaver, contractors, leave, rapid offboard
- **Requests:** 35–38 — catalog, approvals, break-glass, IdentityRequest audit trail
- **Policies:** 39–42 — SoD, dual control, mitigation, risk scores
- **Certifications:** 43–46 — manager, owner, targeted campaigns, remediation evidence
- **Ops:** 47–49 — provisioning debug, assurance reports, email templates
- **Capstone:** 50 — exam readiness & go-live checklist

---

## Learning path (50 lessons)

| # | Lesson | Track | Level | Time |
| ---: | --- | --- | --- | ---: |
| 01 | [Bank Briefing & UI Orientation](01-bank-briefing-and-ui.md) | Foundations | Beginner | 60–75 |
| 02 | [Meridian Org Model & Risk Language](02-meridian-org-model.md) | Foundations | Beginner | 60 |
| 03 | [Lab Hygiene, Naming & Evidence Habits](03-lab-hygiene-and-naming.md) | Foundations | Beginner | 45 |
| 04 | [Authoritative HR Source](04-authoritative-hr-source.md) | Foundations | Beginner | 75–90 |
| 05 | [HR Schema & Identity Attribute Design](05-hr-schema-and-identity-attrs.md) | Foundations | Beginner | 60–75 |
| 06 | [Identity Cubes & Refresh](06-identity-cubes-and-refresh.md) | Foundations | Beginner | 60–75 |
| 07 | [Populations & Identity Selectors](07-populations-and-selectors.md) | Foundations | Beginner | 60 |
| 08 | [Task Operations & Scheduling Discipline](08-task-ops-and-scheduling.md) | Foundations | Beginner | 45–60 |
| 09 | [Onboard IT Access Inventory App](09-it-access-inventory-app.md) | Applications | Beginner | 75–90 |
| 10 | [Entitlement Dictionary & Managed Attributes](10-entitlement-dictionary.md) | Applications | Beginner | 60 |
| 11 | [Onboard Core Banking Extract](11-onboard-core-banking.md) | Applications | Intermediate | 60–75 |
| 12 | [Onboard SAP Finance](12-onboard-sap-finance.md) | Applications | Intermediate | 60–75 |
| 13 | [Onboard AWS Cloud Admin](13-onboard-aws-cloud.md) | Applications | Intermediate | 60–75 |
| 14 | [Onboard Wire Portal (Dual Control)](14-onboard-wire-portal.md) | Applications | Intermediate | 75–90 |
| 15 | [Directory, CRM & Digital Channel Apps](15-onboard-directory-and-crm.md) | Applications | Intermediate | 75 |
| 16 | [Multi-App Aggregation Strategy](16-multi-app-aggregation-strategy.md) | Applications | Intermediate | 60–75 |
| 17 | [Account Correlation Basics](17-correlation-basics.md) | Correlation | Intermediate | 75 |
| 18 | [Correlation Rules & Edge Cases](18-correlation-rules-advanced.md) | Correlation | Intermediate | 75–90 |
| 19 | [Uncorrelated Account Remediation](19-uncorrelated-remediation.md) | Correlation | Intermediate | 60–75 |
| 20 | [Orphan & Dormant Access Hunting](20-orphan-dormant-hunting.md) | Correlation | Intermediate | 60–75 |
| 21 | [Manager Hierarchy & Reassignment](21-manager-hierarchy.md) | Correlation | Intermediate | 60 |
| 22 | [Identity Attribute Sync Hygiene](22-attribute-sync-hygiene.md) | Correlation | Intermediate | 60 |
| 23 | [Role Model Introduction](23-role-model-intro.md) | Roles | Intermediate | 60 |
| 24 | [Birthright Employee Role](24-birthright-employee-role.md) | Roles | Intermediate | 75–90 |
| 25 | [Department & Job-Based Roles](25-dept-job-roles.md) | Roles | Intermediate | 75–90 |
| 26 | [IT Role Packaging & Least Privilege](26-it-role-packaging.md) | Roles | Intermediate | 60–75 |
| 27 | [Role Detection vs Assignment](27-role-detection-vs-assignment.md) | Roles | Intermediate | 60 |
| 28 | [Privileged Access Role Design](28-privileged-access-roles.md) | Roles | Advanced | 75 |
| 29 | [Joiner Lifecycle](29-joiner-lifecycle.md) | Lifecycle | Intermediate | 75–90 |
| 30 | [Mover / Transfer Events](30-mover-transfers.md) | Lifecycle | Intermediate | 75–90 |
| 31 | [Leaver & Access Disablement](31-leaver-disablement.md) | Lifecycle | Intermediate | 75–90 |
| 32 | [Contractor & Contingent Worker Lifecycle](32-contractor-lifecycle.md) | Lifecycle | Intermediate | 60–75 |
| 33 | [Leave of Absence Controls](33-leave-of-absence.md) | Lifecycle | Intermediate | 60 |
| 34 | [Rapid Offboarding Incident Drill](34-rapid-offboarding-drill.md) | Lifecycle | Advanced | 75 |
| 35 | [Access Request Catalog](35-access-request-catalog.md) | Requests | Intermediate | 75–90 |
| 36 | [Approval Chains & Escalations](36-approval-chains.md) | Requests | Intermediate | 75 |
| 37 | [Emergency / Break-Glass Access](37-break-glass-access.md) | Requests | Advanced | 60–75 |
| 38 | [IdentityRequest Tracking & Auditing](38-identity-request-tracking.md) | Requests | Intermediate | 60 |
| 39 | [SoD Fundamentals for Banking](39-sod-fundamentals.md) | Policies | Intermediate | 60–75 |
| 40 | [Payment Dual-Control Policy Deep Dive](40-payment-dual-control-policy.md) | Policies | Advanced | 75 |
| 41 | [Policy Violations & Mitigation](41-policy-violations-mitigation.md) | Policies | Intermediate | 60–75 |
| 42 | [Risk Scores & Scoring Models](42-risk-scores.md) | Policies | Advanced | 60 |
| 43 | [Manager Access Certifications](43-manager-certifications.md) | Certifications | Intermediate | 90–120 |
| 44 | [Application Owner Certifications](44-app-owner-certifications.md) | Certifications | Intermediate | 75–90 |
| 45 | [Targeted & Focused Campaigns](45-targeted-campaigns.md) | Certifications | Advanced | 60–75 |
| 46 | [Certification Remediation & Evidence](46-cert-remediation-evidence.md) | Certifications | Intermediate | 60–75 |
| 47 | [Provisioning Plans & Troubleshooting](47-provisioning-troubleshooting.md) | Ops | Advanced | 90 |
| 48 | [Audit-Ready Reporting & Dashboards](48-audit-ready-reporting.md) | Ops | Intermediate | 75–90 |
| 49 | [Email Templates & Notifications](49-email-templates-notifications.md) | Ops | Intermediate | 60–75 |
| 50 | [Capstone: Exam Readiness & Go-Live Checklist](50-capstone-exam-readiness.md) | Capstone | Advanced | 90–120 |

Work **in order**. Later modules assume `MNB-*` objects and data from earlier ones.

---

## Meridian lab data map

| Signal | File |
| --- | --- |
| Authoritative HR | `HRApplications.txt` / `hr/MNB-HR-Employees.csv` |
| Entitlement dump | `EmployeeData.txt` / `apps/MNB-IT-Access.csv` |
| Per-app extracts | `apps/MNB-*.csv` |
| SoD pairs | `reference/sod-matrix.csv` |
| Dictionaries | `reference/entitlement-dictionary.csv`, `job-codes.csv`, `departments.csv` |
| JML deltas | `scenarios/joiner\|mover\|leaver/` |
| Cert email tone | `notifications/certification-sample.txt` |

**Scripted personas:** `priya.wire` / `marcus.approve` (wire dual control), `jordan.reed` (SAP+AWS SoD), `raj.external` (orphan email), `samir.hassan` (terminated residual), `sofia.torres` (on leave), `kai.nguyen` (digital dual), `amelia.brooks` / `nina.joiner` (joiners).

Regenerate **lab data only** (does not overwrite enterprise lessons):

```bash
python3 tools/generate-mnb-curriculum.py
```

---

## Suggested pace (enterprise cohort)

| Block | Lessons | Calendar |
| --- | --- | --- |
| Week 1 | 01–08 Foundations | Classroom + lab |
| Week 2 | 09–16 Applications | Lab-heavy |
| Week 3 | 17–22 Correlation | Lab + office hours |
| Week 4 | 23–28 Roles | Design reviews |
| Week 5 | 29–34 Lifecycle | Scenario drills |
| Week 6 | 35–42 Requests + Policies | LCM + SoD |
| Week 7 | 43–49 Certs + Ops | Campaign week |
| Week 8 | 50 Capstone | Mock exam / go-live pack |

Self-paced solo: ~40–55 lab hours plus reading.

---

## Need help?

- Setup → [LOCAL_SETUP.md](../LOCAL_SETUP.md)
- Concepts → [INFRASTRUCTURE.md](../INFRASTRUCTURE.md)
- Homelab / learn hosting → [HOMELAB-CD.md](../HOMELAB-CD.md), [LEARN-SITE.md](../LEARN-SITE.md)
- Product depth → PDFs in `identityiq-8.5/doc/`
