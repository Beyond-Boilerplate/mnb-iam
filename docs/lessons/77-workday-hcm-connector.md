# Lesson 77 — Workday HCM Connector

**Level:** Intermediate  
**Track:** Connectors — ERP / HR / Banking  
**Time:** 75–90 min  
**Prereq:** Lesson 76 — AWS IAM; Lesson 04 authoritative HR concepts  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (Workday row)
- Repo: `lab-data/connectors/features-string-glossary.md`
- Contrast: existing DelimitedFile `MNB-HR` from foundations track

---

## Learning objectives

You will be able to:

- Design Workday as an **authoritative HR** pattern alternative/complement to file-based `MNB-HR`
- Create **MNB-Workday-HCM** application shell with SOAP/RaaS/OAuth placeholders as your build requires
- Map Worker attributes (employee id, manager, status, job) to IdentityIQ identity attributes
- Complete lab-without-live-target worker mock + aggregation checklist without a Workday tenant
- Document cutover risks from CSV HR to Workday authoritative aggregation

---

## Why this matters

**Business.** Meridian may replace batch HR files with Workday as the live HCM system. Joiner/mover/leaver accuracy depends on Worker status and supervisory org feeding IIQ quickly.

**Control / audit.** Examiners treat HR as the identity source of record. Switching connectors without dual-run evidence creates unexplained cube churn—control owners must show reconciliation.

---

## Concepts

**Workday connector.** Reads Workers (and related objects) for authoritative identity data; distinct from Workday Accounts (application accounts) depending on product packaging.

```
Workday HCM (Workers)
        │
        ▼
 MNB-Workday-HCM (authoritative)
        │
        ▼
 Identity cubes created/updated
        │
        ▼
 Downstream target apps (AD, Okta, AWS, …)
```

| Attribute (typical) | IIQ identity use |
| --- | --- |
| Employee_ID / Worker_ID | `employeeId` / name |
| Legal / preferred name | display attrs |
| Supervisory manager | manager |
| Active status / termination | inactive / leaver triggers |
| Job profile / org | department, title |

**Matrix:** Workday → Workday; Workday Accounts separate concern.

**Lab-without-live-target.** Do **not** flip production authoritative flag casually. Build shell + mock worker file + dual-run plan while `MNB-HR` remains authoritative in lab.

---

## Before you start

- [ ] IIQ up; `MNB-HR` exists from foundations
- [ ] Understand danger of two authoritative apps creating duplicate identities
- [ ] Persona `nina.joiner` for joiner scenarios; `helen.ross` as IAM owner

---

## Lab procedure

### Task 1 — Authoritative policy reminder

1. Write rule: *Only one authoritative application active for employees in a given population.*
2. Lab stance: keep `MNB-HR` authoritative; `MNB-Workday-HCM` built as future authoritative candidate (non-auth in lab unless instructor says otherwise).

**Expected result:** Policy reminder in binder.

### Task 2 — Create MNB-Workday-HCM

1. Applications → Add New → **Workday** (HCM).
2. Name: `MNB-Workday-HCM`. Owner: `helen.ross`; HRIS contact `sofia.torres`.
3. Tenant URL + ISU credentials placeholders via vault.
4. Save shell; skip live Test Connection if no tenant.

**Expected result:** Application object exists.

**If it fails:** Document Integration System User permissions needed; continue mock.

### Task 3 — Attribute map

1. Map Worker id → `employeeId` (`MNB#####` style).
2. Map email → `email`.
3. Map manager employee id → manager correlation.
4. Map termination date / active → IIQ inactive semantics.
5. Align with Lesson 05 HR schema naming where possible.

**Expected result:** Attribute map table.

### Task 4 — Mock workers (lab-without-live-target)

1. Create `~/iiq-lab-data/connectors/workday/MNB-Workday-HCM-mock.csv` with `workerId,userName,email,managerId,status,department,title`.
2. Include `nina.joiner` (active), `priya.wire`, terminated stub `ex.employee` with status=terminated.
3. Optional non-authoritative Shadow DelimitedFile for aggregation practice only.

**Expected result:** Mock file with active + terminated examples.

### Task 5 — Aggregation task (non-auth)

1. Create `MNB-Workday-HCM-Account-Aggregation` (or identity aggregation per Workday pattern in your version—document which).
2. Run against shadow/live; **do not** enable authoritative create if `MNB-HR` already owns cubes—unless in a disposable sandbox.

**Expected result:** Task Result with clear note “non-authoritative lab run.”

### Task 6 — Dual-run cutover plan

1. Phase 1: Workday agg parallel; reconcile employeeId sets vs `MNB-HR`.
2. Phase 2: Fix deltas; freeze CSV changes.
3. Phase 3: Flip authoritative with change ticket + rollback plan.
4. Evidence: reconcile spreadsheet sample (10 identities).

**Expected result:** Three-phase cutover page.

### Task 7 — Joiner/leaver trigger notes

1. Joiner: Workday active Worker → refresh → birthright.
2. Leaver: terminated Worker → disable targets within SLA.
3. Tie to Lessons 29–31 conceptually.

**Expected result:** Trigger notes page.

### Task 8 — Examiner Q&A

*What is Meridian’s identity source of record today vs target state?* Answer with current `MNB-HR` and planned `MNB-Workday-HCM`.

**Expected result:** Written answer.

---

## Acceptance criteria

- [ ] Single-authoritative-app policy reminder documented
- [ ] `MNB-Workday-HCM` shell + attribute map
- [ ] Mock workers include active and terminated
- [ ] Non-auth aggregation evidence captured
- [ ] Dual-run cutover plan + examiner answer complete

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Duplicate identities | Two authoritative apps | Disable auth on one immediately; merge/remediate |
| Manager blanks | Supervisory org not returned | Adjust Workday response group / field list |
| ISU permission errors | Security group missing | HRIS grants; Shadow path for class |
| Terminated still active in IIQ | Status mapping wrong | Fix termination mapping; re-agg; refresh |
| CSV and Workday drift | No reconcile job | Run dual-run spreadsheet daily in cutover |

---

## Training binder evidence

- Authoritative policy reminder
- App config redacted + attribute map
- Mock CSV + Task Result
- Dual-run cutover plan
- Examiner Q&A answer

---

## Knowledge check

1. What is the Meridian Workday application name?
2. Why keep `MNB-HR` authoritative during the lab build?
3. Which persona illustrates a joiner in the mock?
4. Name the three cutover phases at a high level.
5. What matrix connector is preferred for Workday?
6. Who is the HRIS contact proxy?

### Answers

1. `MNB-Workday-HCM`.
2. Avoid duplicate cube creation while validating maps.
3. `nina.joiner`.
4. Parallel reconcile → freeze/fix deltas → flip authoritative with rollback.
5. Workday.
6. `sofia.torres`.

---

## Stretch lab

Draft Workday Accounts (app accounts) vs HCM Worker split: when Meridian needs both connectors. One paragraph ADR seed.

---

## Summary

- Workday HCM is Meridian’s future authoritative Worker feed pattern.
- Lab-without-live-target builds maps and mocks without flipping authority prematurely.
- Dual-run reconciliation is mandatory evidence for HR connector cutover.

---

**Previous:** [Lesson 76 — AWS IAM Connector](76-aws-iam-connector.md)  
**Next:** [Lesson 78 — SAP HR/HCM Connector](78-sap-hr-hcm-connector.md)
