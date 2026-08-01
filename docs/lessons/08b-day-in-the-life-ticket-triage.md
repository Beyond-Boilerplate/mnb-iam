# Lesson 08b — Day in the Life: Ticket Triage

**Level:** Beginner  
**Track:** Foundations  
**Time:** 45–60 minutes  
**Prereq:** Lesson 08 (task ops); `MNB-HR` aggregated (Lesson 04+)  
**Lab data:** `lab-data/scenarios/bad-row/*`; live Task Results in IIQ  
**Path:** Core (01–50)

---

## Learning objectives

You will be able to:

- Triage three junior-ticket shapes: unlock, failed aggregation, “user has no access”
- Read a Task Result for start time, counters, and the first actionable error line
- Diagnose a bad HR delta **without** corrupting the live feed (`apply-bad-row.sh`)
- Write a five-line on-call note with persona, evidence, and next owner
- Distinguish “IIQ problem” vs “HR data problem” vs “correlation / birthright not yet built”

---

## Why this matters

**Business.** Week-one IAM engineers do not design connectors—they clear queues. Meridian’s help desk opens tickets like “`amelia.brooks` locked out,” “HR aggregation failed overnight,” and “new teller can’t open CRM.” Wrong first moves (recreating cubes, enabling create-identities on IT apps, editing HR without a backup) create exam findings.

**Control / audit.** Every triage leaves evidence: Task Result ID, identity screenshot, delta diagnosis, and who owns the fix (IAM Ops vs HR Ops vs app owner). Examiners ask how you know the factory is healthy before the branch opens.

---

## Concepts

### Three tickets you will own constantly

| Ticket | Sounds like | First place to look | Wrong move |
| --- | --- | --- | --- |
| Unlock | “I can’t log in” | Identity → accounts / IIQ login capability | Reset HR `userId` |
| Failed aggregation | “Joiner missing” / overnight red | **Monitor → Task Results** | Re-run five tasks overlapping |
| No access | “I exist but can’t do my job” | Cube attrs, roles, Links, birthright | Hand-assign Wire/AWS “just for today” |

### Task Results are the black box recorder

A **Task Result** shows whether Aggregate / Refresh succeeded, how many accounts were scanned/created/updated, and the stack or message that failed. Lesson 08 introduced the UI; this lesson uses it under ticket pressure.

### Bad HR deltas are tickets too

HR sometimes sends a file with blank `userId`, contradictory `inactive`/`status`, or shifted columns. Applying that file is an outage. Meridian’s rule: **diagnose first**, apply second.

```
Ticket arrives
    │
    ├── Unlock? → identity + account state → unlock / password policy
    ├── Red task? → Task Result → fix path/schema → re-run single task
    └── No access? → attrs → roles → Links → request vs birthright gap
            │
            └── If HR-triggered: diagnose delta → apply-*.sh → Aggregate MNB-HR
```

---

## How it works

| Stage | Artifact | What “done” looks like |
| --- | --- | --- |
| Intake | Ticket one-liner + persona | Named identity (`amelia.brooks`, …) |
| Evidence | Task Result / cube / diagnose output | Screenshot or CLI paste |
| Fix or escalate | Single change + owner | IAM vs HR vs app owner |
| Close | Binder note | Residual risk if incomplete |

---

## Before you start

- [ ] IIQ at `http://localhost:8080/identityiq` as `spadmin`
- [ ] Lesson 08 complete; you can open Task Results
- [ ] `lab-data/scenarios/bad-row/` present
- [ ] Do **not** point `MNB-HR` at a bad-row file

---

## Lab procedure

### Task 1 — Ticket A: unlock / login hygiene

Help desk: *“`amelia.brooks` says she is locked out of IIQ / directory baseline.”*

1. Identity Warehouse → search `amelia.brooks`.
2. Note inactive/status flags and whether the cube looks Active.
3. Check Accounts tab for directory / IT inventory Links if already onboarded (Lesson 09+); if not yet, document “Links N/A — apps track incomplete.”
4. If your lab shows a lock/unlock action on the identity or account, practice **Unlock** (or document the menu path your build uses).
5. Binder one-liner: *Unlock ticket — Active cube? Y/N — action taken — residual.*

**Expected result:** You can explain whether this is identity inactive, missing Link, or account lock—not a mystery.

**If it fails:** Confirm you aggregated HR (Lesson 04/06) so Amelia exists.

### Task 2 — Ticket B: failed aggregation

Ops: *“Nightly Aggregate MNB-HR is red.”*

1. Monitor → Task Results (or equivalent) → open the latest `Aggregate MNB-HR` (or your HR aggregate task).
2. Record: start/end, success/fail, accounts scanned/updated, first error line.
3. Write the five-line on-call checklist:

```text
1) Which task failed? (exact name)
2) First error line?
3) Did a prior task still run? (overlap)
4) Is the file path reachable? (HRApplications.txt)
5) Re-run ONE task after fix — do not stampede the runbook
```

4. If the last result is green, still open it and practice reading counters—green results teach the baseline.

**Expected result:** Binder has a Task Result reading with counters + next action.

**If it fails:** Use any recent Aggregate/Refresh result; note the lesson gap honestly.

### Task 3 — Ticket C: diagnose bad HR delta (do not apply)

HR drop: *“Please load this joiner file”* — but it is the bad-row pack.

```bash
./tools/lab/scripts/scenarios/apply-bad-row.sh
./tools/lab/scripts/scenarios/apply-hr-delta.sh --diagnose \
  lab-data/scenarios/bad-row/hr-delta-shifted-columns.csv
```

1. Read the FINDINGS list (blank `userId`, inactive/status contradiction, email collision, column shift).
2. Map each finding to an owner: HR Ops (data), IAM Ops (refuse apply), app owner (N/A).
3. Explicitly **do not** run a normal apply against this file.

**Expected result:** Diagnosis paste in binder + written “refuse upsert” decision.

**If it fails:** Open the CSV in a spreadsheet and mark the same issues by hand.

### Task 4 — Ticket D: “no access” triage tree

Business: *“`nina.joiner` (or Amelia) exists but has no CRM.”*

1. Open the cube → attributes (`employeeType`, `JobCode`, `inactive`).
2. Roles tab: birthright present? (Lesson 24+ — if not built yet, write “role track pending”).
3. Accounts: is there a CRM Link? If apps track incomplete, the answer is “not onboarded / not requested,” not “IIQ is broken.”
4. Decide: birthright gap vs missing request vs correlation miss vs app not aggregated.

**Expected result:** One sentence classification: *data / role / request / app inventory*.

---

## Acceptance criteria

- [ ] Unlock triage note for a named persona
- [ ] Task Result reading with counters + first error/success line
- [ ] Bad-row diagnose output captured; no bad upsert into live HR
- [ ] “No access” classification recorded

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No Task Results | Task never run | Run Aggregate MNB-HR once |
| Diagnose exits 0 | Wrong file | Use `bad-row` paths in README |
| Identity missing | HR not aggregated | Lesson 04/06 |
| Tempted to create-identities on IT | Panic move | Refuse; fix HR/correlation instead |

---

## Training binder evidence

1. Task Result screenshot  
2. `apply-bad-row.sh` terminal output  
3. Five-line on-call checklist  
4. One “no access” decision note  

**Control owner:** IAM Operations  
**Examiner question:** “Show how you handle a bad HR file without corrupting the workforce.”

---

## Knowledge check

1. Why diagnose before `apply-hr-delta.sh` on an untrusted file?  
2. What is the first screen for a red overnight job?  
3. Name two wrong moves when a joiner “has no access.”  
4. Who owns blank `userId` in a delta—IAM or HR?

### Answers

1. Blank/`userId` collisions and status contradictions corrupt authoritative HR and every downstream control.  
2. Task Results for that exact task name.  
3. Hand-creating a cube; enabling create-identities on a target app; granting Wire/AWS outside request.  
4. HR Ops owns the data fix; IAM owns refusing the apply and proving diagnosis.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “Task Results” and “Account Aggregation.”  
- Meridian column map: [`lab-data/reference/hr-column-map.md`](../../lab-data/reference/hr-column-map.md)  
- Scenario runners: [`lab-data/scenarios/README.md`](../../lab-data/scenarios/README.md)

---

## Stretch lab

Induce a safe failure: point a **non-HR** delimited app at a missing path, run Aggregate, capture the Task Result error, restore the path, re-run once (preview of Lesson 16b / 47).

---

## Summary

- Triage is a control habit: evidence first, then one fix.  
- Bad HR files are diagnosed, not “force loaded.”  
- “No access” is a tree—not a single button.

**Previous:** [Lesson 08 — Task Operations & Scheduling Discipline](08-task-ops-and-scheduling.md)  
**Next:** [Lesson 09 — Onboard IT Access Inventory App](09-it-access-inventory-app.md)
