# Lesson 22 — Identity Attribute Sync Hygiene

**Level:** Intermediate  
**Track:** Correlation  
**Time:** 45–60 minutes  
**Prereq:** Lesson 21; MNB-HR authoritative; at least one IT target app aggregated (e.g. MNB-IT-Access, MNB-ActiveDirectory)  
**Lab data:** `~/iiq-lab-data/HRApplications.txt`, `~/iiq-lab-data/apps/MNB-IT-Access.csv`, identity cubes for `amelia.brooks` / `priya.wire`

---

## Learning objectives

You will be able to:

- Build a Meridian source-of-truth table for email, status, department, job, and manager
- Prove HR wins for identity attributes when an IT extract disagrees
- Confirm MNB-IT-Access (and similar inventory apps) are **not** authoritative for identity lifecycle fields
- Detect and document attribute flip-flop risk across aggregation order
- Define exception attributes that may legitimately originate on a target system

---

## Why this matters

Conflicting attribute sources create **flip-flops**: Monday HR says Teller; Tuesday an IT title overwrites the cube; Wednesday roles misfire. Business users lose trust; auditors see unstable identity truth.

**Control / audit:** Authoritative source designation is a control. Meridian’s stance: **HR owns identity truth** for email, employment status, department, job, manager, and worker type. IT apps own account/entitlement facts only. Examiners ask which system is system-of-record—your table is the answer.

---

## Concepts

During aggregation and refresh, IdentityIQ promotes account attributes onto the identity. **Authoritative applications** and attribute promotion / identity mapping rules decide winners.

```
                    ┌─────────────┐
                    │   Identity  │
                    │    Cube     │
                    └──────▲──────┘
           promote │       │ promote (must NOT win)
                   │       │
            ┌──────┴──┐ ┌──┴──────────┐
            │  MNB-HR │ │ MNB-IT-Access│
            │ author. │ │ non-author.  │
            └─────────┘ └─────────────┘
```

| Attribute | Authoritative source | IT apps may carry? | Identity owner |
| --- | --- | --- | --- |
| email | MNB-HR | Yes (copy only) | HR |
| status (active/inactive) | MNB-HR | Account status only | HR |
| departmentCode / jobCode | MNB-HR | Display title noise | HR |
| managerId / manager | MNB-HR | No | HR |
| workerType / onLeave | MNB-HR | No | HR |
| entitlements (WIRE_INIT, …) | Target apps | Yes | App owner |
| accountStatus on link | Target app | Yes | App |

**Flip-flopping:** Two sources alternately overwrite the same identity attribute depending on which aggregation ran last.

---

## Before you start

- [ ] IIQ at `http://localhost:8080/identityiq`
- [ ] MNB-HR marked authoritative (Lesson 04 pattern)
- [ ] MNB-IT-Access (or equivalent inventory) aggregated and correlated
- [ ] Lab files under `~/iiq-lab-data/`
- [ ] Lesson 21 manager chain still understood (manager is an HR-owned attribute)

---

## Lab procedure

### Task 1 — Draft the source-of-truth table

1. In your notebook, create table columns: Attribute | Source app | Authoritative? | Notes.
2. Fill rows for: email, first/last name, status, departmentCode, jobCode, jobTitle, manager, workerType, onLeave, locationCode.
3. Mark entitlement codes as **not** identity lifecycle attributes.

**Expected result:** Every lifecycle attribute lists **MNB-HR** as authoritative; entitlements list target apps.

**If it fails:** Start from Lesson 05 attribute dictionary and extend it—do not invent new HR columns.

### Task 2 — Trace email on a live cube

1. Open identity `amelia.brooks` (or `priya.wire`).
2. Note email = `*@meridiannb.com`.
3. Open the MNB-HR account link and confirm the same email.
4. Open an IT/AD account link if present; confirm email may match but is **not** the governance source.

**Expected result:** Cube email matches HR; documentation states “HR owns email; directory mirrors it.”

**If it fails:** If email differs, prefer HR and open a data-quality finding—do not “fix” by editing IIQ alone.

### Task 3 — Prove status ownership

1. Locate a terminated persona (e.g. `samir.hassan` from earlier lessons) and note identity status from HR.
2. Confirm any remaining app accounts may still show `active`/`disabled` inconsistently—that is **account** state, not HR status.
3. Write one sentence: “Identity status comes from HR; accountStatus is per application.”

**Expected result:** Clear separation of identity status vs account status in your notes.

**If it fails:** Re-read Lesson 20—orphans exist precisely when HR status and account presence disagree.

### Task 4 — Non-authoritative guardrail on IT inventory

1. Open application **MNB-IT-Access** (Setup/Define Applications or equivalent).
2. Confirm it is **not** set as an authoritative identity source.
3. Spot-check that schema maps do not promote `status`/`department` onto the identity in a way that overrides HR.
4. Repeat the mental check for MNB-ActiveDirectory: directory is high volume, still **not** HR.

**Expected result:** Notebook checkbox: “MNB-IT-Access non-authoritative — verified.”

**If it fails:** Clear authoritative flag / remove identity attribute mappings that fight HR; re-aggregate and refresh.

### Task 5 — Controlled disagreement test

1. **Backup** `~/iiq-lab-data/apps/MNB-IT-Access.csv` (or the file your app reads).
2. For `amelia.brooks`, temporarily change **only** the job title string in the IT file to something absurd (e.g. `Interim CIO`).
3. Run Account Aggregation for MNB-IT-Access.
4. Run Refresh MNB Identities.
5. Open `amelia.brooks`—identity jobTitle / jobCode from HR should still reflect Teller / `TEL01`, not Interim CIO.
6. Restore the IT file and re-aggregate.

**Expected result:** Identity title/dept/status unchanged by IT title edit; only the IT account attribute (if shown on the link) reflects the joke title.

**If it fails:** You have a promotion path from IT → identity. Remove/remap that attribute and retest—this is a Sev-2 config defect.

### Task 6 — Aggregation order note

1. Document Meridian’s preferred nightly order: **HR first**, then target apps, then identity refresh.
2. Explain why HR-last aggregation of a mis-mapped IT source is dangerous.

**Expected result:** One-page ops note: order + owner + “no silent overwrites.”

### Task 7 — Exception register

1. List any attribute that **must** come from a target (examples: last login, mailbox quota, AWS account alias).
2. Mark them as account-level or extended attributes—not HR replacements.

**Expected result:** Exception register with ≤5 rows; none override status/email/dept/manager.

---

## Acceptance criteria

- [ ] Source-of-truth table completed for core identity attributes
- [ ] Email and status traced to MNB-HR on at least one cube
- [ ] MNB-IT-Access confirmed non-authoritative
- [ ] Disagreement test shows HR wins (or defect logged with remediation)
- [ ] Aggregation order + exception register documented

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Identity title flips after IT agg | IT attribute mapped to identity | Unmap; keep on Link only |
| Email domain wrong | Bad HR row or manual edit | Fix HR file; re-aggregate HR |
| Status active but HR terminated | Refresh not run / wrong status map | Fix status mapping; refresh |
| Two emails on cube | Multiple promotion sources | Single authoritative email map from HR |
| “Nothing changed” in disagreement test | App not reading the file you edited | Verify application file path vs `~/iiq-lab-data/` |

---

## Training binder evidence

- Source-of-truth table (print or PNG)
- Screenshot: application config showing MNB-IT-Access not authoritative
- Screenshot: `amelia.brooks` identity attributes after disagreement test
- Ops note: aggregation order (HR → apps → refresh)
- Exception register (even if empty except “none”)

**Control owner:** IAM Engineering (mappings) + HR (data) + App owners (account attributes)  
**SLA:** Attribute mapping defects that can overwrite status/email: fix within 2 business days

---

## Knowledge check

1. Which application owns employment status at Meridian?
2. Why are IT job titles untrustworthy for roles?
3. What is attribute flip-flopping?
4. Should MNB-IT-Access be authoritative?
5. Name two attributes that may legitimately stay on the account link only.

### Answers

1. MNB-HR (authoritative HR source).
2. Inventory/title fields are often stale, free-text, or role-inflated; roles must key off HR `jobCode`/`departmentCode`.
3. Two sources alternately overwriting the same identity attribute based on last aggregation/refresh.
4. No—non-authoritative inventory/correlation aid only.
5. Examples: entitlement membership, accountStatus, lastLogin, AWS-specific aliases (any account-scoped tech attribute).

---

## Stretch lab

- Add `locationCode` and `costCenter` to the source-of-truth table with HR as owner.
- Propose a monitoring report: identities whose email domain ≠ `@meridiannb.com` excluding known contractors (`raj.external` pattern).
- Sketch a change ticket template for “new identity attribute mapping” requiring dual approval (IAM + data owner).

---

## Summary

- HR owns email, status, dept, job, manager, worker type; IT apps must not clobber them.
- Non-authoritative inventory apps are correlation aids, not identity systems of record.
- Disagreement tests and aggregation order prevent silent flip-flops before roles and JML depend on clean attributes.

---

**Previous:** [Lesson 21 — Manager Hierarchy & Reassignment](21-manager-hierarchy.md)  
**Next:** [Lesson 23 — Role Model Introduction](23-role-model-intro.md)
