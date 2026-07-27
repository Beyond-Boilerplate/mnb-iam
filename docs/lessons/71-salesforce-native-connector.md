# Lesson 71 — Salesforce Native Connector

**Level:** Intermediate  
**Track:** Connectors — Web APIs & SaaS  
**Time:** 75–90 min  
**Prereq:** Lesson 70 — SCIM Custom Schemas; Lesson 52 selection matrix  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (Salesforce CRM row)
- Repo: `lab-data/connectors/features-string-glossary.md`
- Prior CSV app knowledge: `lab-data/apps/MNB-Ecommerce-Ops.csv` (contrast only)

---

## Learning objectives

You will be able to:

- Select **Salesforce** native connector over DelimitedFile/Web Services per matrix
- Create application **MNB-Salesforce-CRM** with OAuth/JWT placeholders and schema plan
- Map Salesforce User / Profile / PermissionSet concepts to IIQ accounts and entitlements
- Complete lab-without-live-target: entitlement dictionary + mock user inventory
- Define Account Aggregation task and leaver disable expectations

---

## Why this matters

**Business.** Meridian relationship managers live in Salesforce. Profile and Permission Set sprawl drives over-entitlement risk on customer PII and pipeline data.

**Control / audit.** Examiners ask how CRM privileged profiles are inventoried and revoked. Native connector aggregation + ownership beats stale CSV exports.

---

## Concepts

**Salesforce connector (native).** OOTB IdentityIQ connector for Salesforce.com users, profiles, permission sets, and related objects—not a CSV dump of CRM.

| Object / concept | IIQ treatment |
| --- | --- |
| User | Account |
| Profile | Entitlement (often) |
| PermissionSet | Entitlement |
| Active / IsActive | Enable/disable |

```
MNB-Salesforce-CRM
        │
        ▼
 Salesforce native connector (OAuth)
        │
        ├── Aggregate Users + Profiles / PermissionSets
        └── Provision create/update/disable (per features)
```

**Matrix:** Salesforce CRM → Salesforce; alternate Web Services.

**Lab-without-live-target.** No SFDC tenant required: build app shell, schema, mock `MNB-Salesforce-CRM-mock.csv`, ops/owner card.

---

## Before you start

- [ ] IIQ up; matrix CSV available
- [ ] Do **not** use production Salesforce credentials in lab
- [ ] Know personas `amelia.brooks`, `kai.nguyen` as potential CRM users

---

## Lab procedure

### Task 1 — Matrix and anti-pattern

1. Confirm matrix: Salesforce → native Salesforce connector.
2. Write anti-pattern: *Do not keep MNB CRM as DelimitedFile if native connector is licensed and reachable.*

**Expected result:** Decision + anti-pattern sentences.

### Task 2 — Create MNB-Salesforce-CRM shell

1. Applications → Add New → **Salesforce** (or Salesforce connector).
2. Name: `MNB-Salesforce-CRM`. Owner: `helen.ross`; business owner `amelia.brooks`.
3. Configure OAuth/Connected App placeholders (Consumer Key/Secret via vault).
4. Save without requiring live token if lab-without-live-target.

**Expected result:** Application object named correctly.

**If it fails:** Create from template; document required Connected App scopes offline.

### Task 3 — Schema & entitlement plan

1. Native identity: Salesforce Username or Federation ID (pick; document).
2. Entitlements: `Profile` + `PermissionSet` naming prefix `SFDC_`.
3. Draft dictionary entries: `SFDC_SYSADMIN`, `SFDC_RM_STANDARD`, `SFDC_CREDIT_VIEW`.

**Expected result:** Schema plan + three dictionary rows.

### Task 4 — Mock inventory (lab-without-live-target)

1. Create `~/iiq-lab-data/connectors/salesforce/MNB-Salesforce-CRM-mock.csv` with columns `userName,email,employeeId,profile,permissionSets,active`.
2. Add rows for `amelia.brooks`, `kai.nguyen`, `jordan.reed` with distinct profiles.
3. Optional Shadow DelimitedFile app for aggregation practice.

**Expected result:** Mock file with ≥3 users.

### Task 5 — Account Aggregation task

1. Create `MNB-Salesforce-CRM-Account-Aggregation`.
2. Run against live SFDC **or** Shadow.
3. Capture counts; spot-check one cube.

**Expected result:** Task Result Success evidence.

### Task 6 — Leaver disable card

1. Document: disable Salesforce user (`IsActive=false`) within Meridian leaver SLA.
2. List evidence: IdentityRequest → plan → Task Result → post-agg inactive.

**Expected result:** Leaver card for CRM.

---


### Task 7 — Correlation & ownership drill

1. Document correlation order: Federation ID → employeeId; else email `@meridiannb.com`.
2. Confirm application owner `amelia.brooks` appears in app-owner cert scope notes.
3. List IQService-unrelated note: Salesforce auth is OAuth to cloud—not AD IQService.

**Expected result:** Correlation + ownership + auth-boundary notes.

### Task 8 — Feature matrix row

1. Using `features-string-glossary.md`, mark expected PROVISIONING / ENABLE / PASSWORD for Salesforce.
2. Write “confirm in ConnectorRegistry” rather than guessing missing features.

**Expected result:** Feature checklist table in binder.


## Acceptance criteria

- [ ] Native Salesforce chosen over CSV for CRM governance design
- [ ] `MNB-Salesforce-CRM` shell + schema/entitlement plan
- [ ] Mock inventory and optional Shadow aggregation
- [ ] Account Aggregation task defined with evidence
- [ ] Leaver disable card completed; no secrets in git

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| OAuth fails | Wrong Connected App / IP restrict | Fix Connected App; use sandbox; or Shadow path |
| PermissionSets missing | Feature/schema not selected | Enable PermissionSet aggregation in connector config |
| Sysadmin undetected | Profile name filter | Remove overly tight filters; mark high risk |
| CSV still authoritative | Old app not retired | Plan decommission of file CRM app |
| Federation ID blank | SSO users only | Document correlation to employeeId/email |

---

## Training binder evidence

- Matrix decision
- App config redacted
- Mock CSV + dictionary rows
- Aggregation Task Result
- Leaver disable card

---

## Knowledge check

1. What preferred connector does the matrix list for Salesforce CRM?
2. Name the Meridian Salesforce application object.
3. Which Salesforce constructs typically become entitlements?
4. Why is DelimitedFile an anti-pattern when native is available?
5. What lab artifact substitutes for a missing SFDC tenant?

### Answers

1. Salesforce (alternate Web Services).
2. `MNB-Salesforce-CRM`.
3. Profiles and Permission Sets (as designed).
4. Stale exports miss privilege changes examiners care about.
5. Mock CSV + Shadow DelimitedFile + full schema/owner documentation.

---

## Stretch lab

Map a SoD draft: `SFDC_SYSADMIN` vs Wire `WIRE_INIT`. Do not activate without Risk approval.

---

## Summary

- Native Salesforce connector is Meridian’s CRM governance path.
- Lab-without-live-target still produces schema, mock inventory, and leaver evidence design.
- Profiles/PermissionSets must enter the entitlement dictionary with risk tiers.

---

**Previous:** [Lesson 70 — SCIM Custom Schemas](70-scim-custom-schemas.md)  
**Next:** [Lesson 72 — ServiceNow Connector](72-servicenow-connector.md)
