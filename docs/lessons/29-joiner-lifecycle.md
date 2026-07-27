# Lesson 29 — Joiner Lifecycle

**Level:** Intermediate  
**Track:** Lifecycle  
**Time:** 60–90 minutes  
**Prereq:** Lessons 24–28 (birthright + job/priv roles); MNB-HR aggregation path known  
**Lab data:** `~/iiq-lab-data/scenarios/joiner/hr-delta-new-hire.csv` → persona **`nina.joiner`** (`MNB00120`)

---

## Learning objectives

You will be able to:

- Apply the joiner HR delta for Nina Foster (`nina.joiner`) into the authoritative HR file safely
- Run Account Aggregation for MNB-HR and Refresh MNB Identities to materialize the cube
- Confirm birthright `MNB-Birthright-Employee` / ELDAP assignment intent for the new hire
- Distinguish automatic birthright from job-specific access still requiring requests
- Document Meridian joiner SLA and evidence for training/exam records

---

## Why this matters

Joiners stuck without access create shadow IT and bad first impressions. Automated birthright triggered from HR is Meridian’s first IAM promise: identity exists, directory baseline lands, tickets cover only non-birthright needs.

**Control / audit:** Joiner control = HR active row → aggregate → refresh → birthright within SLA. Evidence = HR delta file + task results + identity screenshots. Examiners ask how quickly a new teller gets baseline access and what is excluded from automation.

---

## Concepts

In full LCM, joiner **lifecycle events** fire workflows. In this file-based lab, **inserting an HR row** is the business event.

```
hr-delta-new-hire.csv
        │
        ▼
Append/merge into HRApplications.txt
        │
        ▼
Account Aggregation task (MNB-HR)
        │
        ▼
Refresh MNB Identities (assign roles)
        │
        ▼
Identity nina.joiner + MNB-Birthright-Employee
```

| Field (Nina) | Value |
| --- | --- |
| employeeId | MNB00120 |
| userName | nina.joiner |
| email | nina.joiner@meridiannb.com |
| managerId | MNB00007 (`emily.bennett`) |
| status | 1 (active) |
| departmentCode | RET |
| jobCode | TEL01 |
| jobTitle | Teller |
| workerType | Employee |
| hireDate | 2026-07-26 |

**Automatic:** birthright ELDAP. **Not automatic:** CRM, wire, cloud, privileged roles.

---

## Before you start

- [ ] IIQ at `http://localhost:8080/identityiq`
- [ ] Backup `~/iiq-lab-data/HRApplications.txt`
- [ ] Scenario file present: `~/iiq-lab-data/scenarios/joiner/hr-delta-new-hire.csv`
- [ ] `MNB-Birthright-Employee` assignment rule includes active Employees
- [ ] Confirm `nina.joiner` does **not** already exist (or plan to re-run cleanly)

---

## Lab procedure

### Task 1 — Read the joiner delta

1. Open `~/iiq-lab-data/scenarios/joiner/hr-delta-new-hire.csv`.
2. Verify header columns match `HRApplications.txt`.
3. Record Nina’s manager, job, dept, and hire date in your binder.

**Expected result:** Column counts match; you understand Nina is an active Retail teller under `MNB00007`.

**If it fails:** Fix header mismatch before merging—shifted columns corrupt managerId/status.

### Task 2 — Apply delta to HR file

1. Backup HR file: copy to `HRApplications.txt.bak-joiner`.
2. Append Nina’s data row to `~/iiq-lab-data/HRApplications.txt` (data only—do not duplicate header).
3. Confirm one new line for `MNB00120` / `nina.joiner`.
4. Confirm no accidental truncation of prior rows.

**Expected result:** HR file contains Nina exactly once with valid CSV/TXT field counts.

**If it fails:** Restore backup; re-append carefully; validate with `wc -l` / spreadsheet open.

### Task 3 — Aggregate MNB-HR

1. Tasks → run **Account Aggregation** for application **MNB-HR**.
2. Wait for success in task results.
3. Check for errors/warnings referencing MNB00120.

**Expected result:** Aggregation succeeds; new account link for Nina creatable on next identity view.

**If it fails:** Validate file path on the application; fix malformed row; re-run aggregation.

### Task 4 — Refresh identities (joiner materialization)

1. Run **Refresh MNB Identities** with identity attribute refresh + **role assignment** enabled.
2. Optionally filter to new identity / recent hires if supported.
3. Confirm task success.

**Expected result:** Identity cube `nina.joiner` exists with HR attributes and manager resolved toward Emily Bennett / `MNB00007`.

**If it fails:** Confirm manager `MNB00007` exists; fix manager correlation; re-refresh.

### Task 5 — Verify cube & birthright

1. Identity Warehouse → search `nina.joiner`.
2. Confirm attributes: email `@meridiannb.com`, TEL01, RET, Employee, active.
3. Confirm Manager resolves (Emily Bennett).
4. Roles: **`MNB-Birthright-Employee` assigned**.
5. Confirm **no** CloudAdmin, BreakGlass, WireInitiator, or RM roles.

**Expected result:** Birthright only among business packs; privileged roles absent.

**If it fails:** Re-check birthright rule; ensure refresh assigned roles; verify workerType=Employee on cube.

### Task 6 — Gap analysis (non-birthright)

1. List access Nina might still need for teller operations beyond ELDAP (core banking frontline, branch apps)—mark as **request / separate birthright** decisions.
2. Explicitly note CRM/Wire/Cloud are out of scope for TEL01 automation.
3. Open a training “ticket” note: optional follow-up request catalog items (Lesson 35).

**Expected result:** Gap list with “auto vs request” column; birthright alone not oversold.

### Task 7 — Joiner SLA statement

1. Write Meridian lab/prod target:
   - Identity visible ≤ 1 hour after HR marks active
   - Birthright assigned same refresh cycle
   - Non-birthright fulfilled per catalog SLAs
2. Name control `MNB-Ctrl-Joiner-SLA`.

**Expected result:** SLA paragraph with metrics and owners (HR data + IAM ops).

### Task 8 — Evidence pack

1. Capture screenshots: HR row, aggregation result, Nina cube attrs, birthright role.
2. Store delta file path and bak file name in binder index.

**Expected result:** Complete joiner evidence folder entry.

---

## Acceptance criteria

- [ ] Nina’s HR row applied without corrupting HR file
- [ ] MNB-HR aggregation and identity refresh succeeded
- [ ] `nina.joiner` cube exists with correct manager/job
- [ ] `MNB-Birthright-Employee` assigned; privileged roles not assigned
- [ ] Joiner SLA and gap analysis documented

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Nina missing after agg | Row not in file path IIQ reads | Confirm `~/iiq-lab-data` path on app |
| Identity created, no birthright | Assign roles off / rule exclude | Enable assign; fix workerType/status maps |
| Manager blank | MNB00007 missing or map fail | Ensure Emily exists; re-aggregate/refresh |
| Duplicate Nina | Delta applied twice | Dedupe HR file; re-aggregate |
| CSV column shift | Header appended or commas in fields | Restore bak; re-apply clean row |

---

## Training binder evidence

- Copy of joiner delta CSV + note of append time
- Task result screenshots (aggregate + refresh)
- `nina.joiner` attribute + roles screenshots
- Gap analysis table (auto vs request)
- `MNB-Ctrl-Joiner-SLA`

**Control owner:** HR Operations (trigger) + IAM Operations (pipeline)  
**Examiner question:** “Show a joiner from HR file to birthright assignment with timestamps.”

---

## Knowledge check

1. What triggers joiner in this lab?
2. What must Nina get automatically?
3. What is the joiner identity/birthright SLA target?
4. Who is Nina’s managerId?
5. Should Nina receive `MNB-Role-CloudAdmin` as a joiner?

### Answers

1. Inserting/merging the HR delta row for the new hire, then aggregating MNB-HR and refreshing identities.
2. Identity cube + `MNB-Birthright-Employee` (ELDAP baseline)—not privileged or wire packs.
3. Identity within ~1 hour of HR active; birthright same refresh cycle.
4. `MNB00007` (Emily Bennett).
5. No—privileged roles are request-only and never joiner birthright.

---

## Stretch lab

- If LCM Rapid Setup / Lifecycle Events are imported, configure a Joiner event on HR account create to create a work item “Verify birthright for nina.joiner.”
- Compare `amelia.brooks` and `nina.joiner`—both TEL01 tellers should converge on the same birthright composition.
- Measure wall-clock time from file save → birthright visible; record as lab KPI.

---

## Summary

- Joiner lab event = HR delta for `nina.joiner` → aggregate → refresh → birthright.
- Automatic access stays minimal; gaps become catalog requests.
- SLA and screenshots turn a demo into an auditable control.

---

**Previous:** [Lesson 28 — Privileged Access Role Design](28-privileged-access-roles.md)  
**Next:** [Lesson 30 — Mover / Transfer Events](30-mover-transfers.md)
