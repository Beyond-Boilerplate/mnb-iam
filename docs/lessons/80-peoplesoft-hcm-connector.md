# Lesson 80 — PeopleSoft HCM Connector

**Level:** Intermediate  
**Track:** Connectors — ERP / HR / Banking  
**Time:** 75–90 min  
**Prereq:** Lesson 79 — SAP Direct Security; Lesson 77 Workday patterns  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (PeopleSoft row)
- Repo: `lab-data/connectors/features-string-glossary.md`
- Repo: `lab-data/connectors/jdbc/` (DB alternate patterns)

---

## Learning objectives

You will be able to:

- Select **PeopleSoft HCM Database** vs **PeopleSoft Direct** per Meridian matrix notes
- Create **MNB-PeopleSoft-HCM** application shell for worker/person data
- Map EmplID, job, status, and department fields into IIQ identity attributes
- Complete lab-without-live-target PS mock extract and aggregation checklist
- Document authoritative coexistence with Workday/SAP HR/CSV and handoff to Lesson 81 Oracle EBS

---

## Why this matters

**Business.** Legacy Meridian entities may still run PeopleSoft HCM for HR and payroll. IAM must ingest EmplID-based workers without treating PS security the same as HCM person data.

**Control / audit.** Examiners ask which HCM system is authoritative per legal entity. Matrix-driven connector choice plus dual-run evidence prevent silent identity splits.

---

## Concepts

**PeopleSoft options (matrix):** preferred **PeopleSoft HCM Database**; alternate **PeopleSoft - Direct**.

| Option | Typical use |
| --- | --- |
| PeopleSoft HCM Database | Read HR tables / views via DB connectivity |
| PeopleSoft Direct | Application-level PS connector path |

```
PeopleSoft HCM
        │
        ▼
 MNB-PeopleSoft-HCM
        │
        ▼
 Identity attributes (non-auth in lab unless directed)
```

**EmplID** is the PeopleSoft person key—bridge to `employeeId` like SAP PERNR.

**Lab-without-live-target.** Mock PS extract + maps + coexistence card; Next lesson moves to Oracle EBS.

---

## Before you start

- [ ] IIQ up; Workday/SAP HR coexistence ideas fresh
- [ ] Matrix PeopleSoft row open
- [ ] JDBC fixtures available if DB-style PS HCM path used

---

## Lab procedure

### Task 1 — Matrix choice

1. Record preferred: PeopleSoft HCM Database; alternate PeopleSoft Direct.
2. Write Meridian decision: *Lab uses HCM Database-style mapping via mock/JDBC patterns; Direct only if app connector licensed and preferred by architecture.*

**Expected result:** Decision sentence.

### Task 2 — Create MNB-PeopleSoft-HCM

1. Applications → Add New → **PeopleSoft HCM Database** or **PeopleSoft** Direct per available template.
2. Name: `MNB-PeopleSoft-HCM`. Owner: `helen.ross`; HR contact `sofia.torres`.
3. Connection placeholders (JDBC URL or PS conn)—vault only.
4. Save shell.

**Expected result:** Application object named correctly.

**If it fails:** Build DelimitedFile/JDBC shadow labeled clearly for training.

### Task 3 — Schema map

1. `emplId` → `psEmplId` + bridge to `employeeId`.
2. `userName` / opid → account or identity name strategy (document one).
3. `hrStatus` / `effStatus` → active/inactive.
4. `deptId`, `jobCode`, `managerId` → identity attrs.

**Expected result:** Schema map table.

### Task 4 — Mock extract (lab-without-live-target)

1. Create `~/iiq-lab-data/connectors/peoplesoft/MNB-PeopleSoft-HCM-mock.csv` with `emplId,employeeId,userName,email,hrStatus,deptId,jobCode,managerId`.
2. Include `sofia.torres`, `kai.nguyen`, `nina.joiner`.
3. Aggregate via Shadow DelimitedFile or JDBC staging loaded from mock.

**Expected result:** ≥3 workers in Task Result.

### Task 5 — Aggregation task

1. `MNB-PeopleSoft-HCM-Account-Aggregation`
2. Keep non-authoritative unless sandbox dedicated to PS-auth experiment.
3. Spot-check bridge fields on cubes after correlation refresh design.

**Expected result:** Task Result + non-auth note.

### Task 6 — Coexistence & cutover stub

1. Extend coexistence matrix from Lesson 78: add PeopleSoft legal entity column.
2. Dual-run sample vs `MNB-HR` for 5 EmplIDs.
3. Rollback: disable PS auth flag; revert to CSV/Workday.

**Expected result:** Updated coexistence matrix.

### Task 7 — Security vs HCM note

1. Clarify PS application security roles are out of scope for this HCM lesson (similar to SAP split).
2. If PS security needed later, separate application object—do not overload `MNB-PeopleSoft-HCM`.

**Expected result:** Scope boundary paragraph.

### Task 8 — Examiner Q&A + handoff

1. Answer: *Which connector inventories PeopleSoft workers?* → `MNB-PeopleSoft-HCM` per matrix.
2. Note Next: Oracle E-Business Suite connector (Lesson 81) for EBS responsibilities.

**Expected result:** Q&A + handoff sentence in binder.

---

## Acceptance criteria

- [ ] Matrix HCM Database vs Direct decision recorded
- [ ] `MNB-PeopleSoft-HCM` shell + schema/bridge map
- [ ] Mock extract aggregated (shadow/live/JDBC staging)
- [ ] Coexistence matrix updated; security scope boundary written
- [ ] Examiner Q&A and Lesson 81 handoff noted

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| EmplID collisions | Shared ids across entities | Namespace by company / setid in correlation |
| Effdt confusion | Multiple effective-dated rows | Use current effective-dated view |
| JDBC timeout | Heavy PS queries | Filter active employees; schedule off-peak |
| Authoritative duplicates | PS + HR both auth | Segment populations immediately |
| Wrong template chosen | Direct vs DB mismatch | Revisit matrix; recreate app from correct template |
| Security roles mixed in | Overloaded app | Split to future PS security app |

---

## Training binder evidence

- Matrix decision
- App config redacted + schema map
- Mock/Task Result
- Coexistence matrix update
- Examiner Q&A + Lesson 81 handoff

---

## Knowledge check

1. What preferred PeopleSoft connector does the matrix list?
2. What is the Meridian PeopleSoft HCM application name?
3. Why bridge EmplID to employeeId?
4. Should PS security roles live on the HCM app?
5. What lesson follows for Oracle E-Business?
6. Name one persona in the PS mock.

### Answers

1. PeopleSoft HCM Database (alternate PeopleSoft Direct).
2. `MNB-PeopleSoft-HCM`.
3. IIQ cubes and Meridian HR keys use `MNB#####` / employeeId, not raw EmplID alone.
4. No—keep security in a separate application object.
5. Lesson 81 — Oracle EBS Connector.
6. `sofia.torres`, `kai.nguyen`, or `nina.joiner`.

---

## Stretch lab

Design JDBC view SQL sketch selecting current effective-dated JOB and PERSONAL_DATA fields for Meridian lab schema naming. Do not run against production PS.

---

## Summary

- PeopleSoft HCM Database is Meridian’s preferred PS worker inventory path.
- Lab-without-live-target mocks and bridges keep authoritative cutovers safe.
- HCM scope stays separate from PS security; next stop is Oracle EBS.

---

**Previous:** [Lesson 79 — SAP Direct Security](79-sap-direct-security.md)  
**Next:** [Lesson 81 — Oracle EBS Connector](81-oracle-ebs-connector.md)
