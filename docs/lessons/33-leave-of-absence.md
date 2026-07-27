# Lesson 33 — Leave of Absence Controls

**Level:** Intermediate  
**Track:** Lifecycle  
**Time:** 45–60 minutes  
**Prereq:** Lesson 32 (contractor lifecycle); HR `onLeave` mapped (Lesson 05); CRM/directory apps onboarded  

**Lab data:**
- HR row: `sofia.torres` (`MNB00095`) — `onLeave=true`, `status=1`
- Access context: `lab-data/apps/MNB-Salesforce-CRM.csv`, `lab-data/apps/MNB-ActiveDirectory.csv`, `lab-data/apps/MNB-IT-Access.csv`
- Contrast: Lesson 31 leaver `jordan.reed` (`status=0`)

---

## Learning objectives

You will be able to:

1. Locate on-leave identities using HR `onLeave=true`, with `sofia.torres` as the primary case.
2. Explain **freeze vs terminate** in Meridian policy language (keep identity, pause interactive/privileged access).
3. Design a freeze package: disable directory login / revoke or suspend privileged entitlements; retain CRM ownership notes.
4. Specify manager notification / work-item expectations within 24 hours.
5. Document return-to-work re-enable with a mini certification.
6. Avoid running full leaver destruction when return is expected.

---

## Why this matters

**Business:** People on leave still have credentials. Quiet misuse of CRM or residual privilege during parental/medical leave creates fraud and privacy incidents without the “clean” story of a termination.

**Control / audit:** Examiners ask whether leave is monitored separately from termination. Control owner: IAM + HR Business Partner; manager `sanjay.kapoor` owns Sofia’s commercial banking access decisions. Leaving leave active with wire or cloud rights is unacceptable.

---

## Concepts

### Freeze vs terminate

| Dimension | Freeze (LoA) | Terminate (Leaver) |
| --- | --- | --- |
| HR signal | `onLeave=true`, usually `status=1` | `status=0` + `terminationDate` |
| Identity cube | Remains; expected return | Inactive; end of employment |
| Directory | Disable interactive login | Disable + long-term deprovision |
| Privileged ents | Suspend / revoke for duration | Revoke / disable same day |
| Business data | Retain ownership notes (CRM) | Reassign ownership |
| Return path | Controlled re-enable + mini cert | New joiner / rehire process |

### Sofia Torres lab profile

| Field | Value |
| --- | --- |
| userName | `sofia.torres` |
| employeeId | `MNB00095` |
| email | `sofia.torres@meridiannb.com` |
| manager | `sanjay.kapoor` (`MNB00006`) |
| dept / job | `CML` / `RM01` Relationship Manager |
| onLeave | `true` |
| Typical access | `ELDAP`, `CRM`, `ODS` |

### Freeze control flow

```text
HR onLeave=true
      │
      ▼
Aggregate MNB-HR → Refresh MNB Identities
      │
      ▼
Detect LoA population / lifecycle event (optional LCM)
      │
      ├──► Disable ELDAP (interactive)
      ├──► Suspend privileged ents if any (WIRE_*, AWS_ADMIN, CORE, …)
      ├──► Flag CRM: read-only or disable login; keep ownership note
      └──► Work item → manager within 24h
      │
      ▼
Return: onLeave=false → staged re-enable → mini cert
```

**IIQ terms:** *Lifecycle event* (LCM) can fire on attribute change—optional if `init-lcm.xml` imported. *Work item* is the human decision/inbox object. Freeze is an operational policy; it may be implemented via disable account, remove role, or temporary population-driven certification.

---

## Before you start

- [ ] IIQ available; `spadmin` login works.
- [ ] HR feed contains Sofia with `onLeave=true` (baseline lab data already does).
- [ ] You can open identity cubes and account links.
- [ ] Lesson 31 completed so you will not accidentally “terminate” Sofia.
- [ ] Optional LCM: note whether `init-lcm.xml` was imported—stretch only.

---

## Lab procedure

### Task 1 — Find on-leave users in HR and IIQ

1. In `~/iiq-lab-data/hr/MNB-HR-Employees.csv` (or live HR file), filter `onLeave` = `true`.
2. Confirm Sofia’s row: `MNB00095`, `status=1`, `onLeave=true`, manager `MNB00006`.
3. Note other on-leave rows if present (e.g. `chloe.joshi`, `samir.hughes`, `amelia.foster`, `deepa.khatri`, `rohan.price`) for population sizing.
4. In IIQ, search identity `sofia.torres` and confirm `onLeave` attribute is true after Aggregate + Refresh if you just remapped schema.

**Expected result:** List of on-leave identities with Sofia highlighted; clear proof she is **not** a leaver (`status` still active).

**If it fails:** Remap `onLeave` boolean on HR app; Aggregate MNB-HR; Refresh MNB Identities.

---

### Task 2 — Write the Meridian freeze policy

1. Draft freeze rules for Relationship Managers on leave:

```text
MNB Leave-of-Absence Freeze (RM example)
1. Keep identity cube and HR linkage (not a termination).
2. Disable interactive directory (ELDAP) within 24 hours of onLeave=true.
3. Disable or suspend CRM interactive access; record account ownership for coverage.
4. Immediately revoke/suspend any privileged entitlements if present
   (WIRE_INIT/APPR, AWS_ADMIN, CORE, SAP_FI, PRIV_BREAK).
5. ODS/analytics: disable if interactive; keep entitlements only if read-only and approved.
6. Do NOT run full leaver account destruction or mailbox wipe solely for LoA.
```

2. Explicitly write one anti-pattern: “Do not set `status=0` to ‘simulate’ leave.”

**Expected result:** Freeze policy page distinguishing Sofia’s case from Jordan’s leaver case.

**If it fails:** Use the table in Concepts; fill Meridian names only.

---

### Task 3 — Execute freeze actions available in lab

1. On Sofia’s cube, inventory current accounts/entitlements (`ELDAP`, `CRM`, `ODS`).
2. Practice disable of `ELDAP` (Manage Accounts / mark disabled in AD CSV + Aggregate—per lab capability).
3. For CRM: either disable the account link or document “CRM freeze ticket” to app owner `sanjay.kapoor` / CRM owner.
4. Confirm no wire/cloud entitlements; if a future LoA user has them, mark Sev-1 freeze.

**Expected result:** Notebook shows before/after for directory (and CRM plan). Privileged entitlement check = none for Sofia, with rule recorded for others.

**If it fails:** File-level disable + re-aggregation is acceptable evidence in this delimited lab.

---

### Task 4 — Manager notification within 24 hours

1. Identify manager: `sanjay.kapoor@meridiannb.com`.
2. Create (or simulate) a work item / ticket:

```text
Subject: LoA freeze review — sofia.torres (MNB00095)
Due: 24 hours from onLeave detection
Ask: Confirm coverage for CRM book; acknowledge freeze; list any access that must remain
```

3. Record SLA: detection → manager work item ≤ 24h; privileged freeze ≤ 4h if entitlements exist.

**Expected result:** Notification artifact with owner, SLA, and identity identifiers.

**If it fails:** Email/ticket template in binder is enough when LCM work items are unavailable.

---

### Task 5 — Return-to-work re-enable control

1. Write return procedure:

```text
Return-to-work (onLeave false → true clear)
1. HR clears onLeave; Aggregate + Refresh.
2. Re-enable ELDAP only after manager confirmation.
3. Re-enable CRM after mini certification (manager attests still needed).
4. Privileged access: never auto-restore; new request (Lessons 35–37).
5. Evidence: HR delta, re-enable timestamps, mini-cert id.
```

2. Optionally flip Sofia’s `onLeave` to `false` in a **sandbox copy** of the HR file, aggregate/refresh, then restore `true` so shared labs stay consistent.

**Expected result:** Written return control that forbids silent full restore of privilege.

**If it fails:** Keep Sofia `onLeave=true` in shared lab; document procedure only.

---

### Task 6 — Optional LCM hook (if available)

1. If `init-lcm.xml` was imported, inspect Lifecycle Manager events / business processes for attribute change triggers (or equivalent menu).
2. Design (do not break prod): event on `onLeave` changing to `true` → workflow that creates manager work item + disable plan.
3. Screenshot or note object names for the binder.

**Expected result:** Either a config note “LCM event designed” or “LCM not active—manual freeze SOP applies.”

---

## Acceptance criteria

- [ ] On-leave users identified; Sofia confirmed `onLeave=true`, `status=1`.
- [ ] Freeze vs terminate comparison written.
- [ ] Freeze actions for ELDAP/CRM practiced or ticketed.
- [ ] Manager 24h notification artifact created.
- [ ] Return-to-work + mini-cert procedure documented.
- [ ] No accidental termination of Sofia.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Sofia looks terminated | Wrong lesson applied / status flipped | Restore `status=1`, `onLeave=true` |
| onLeave not on cube | Schema mapping missing | Map boolean; Aggregate; Refresh |
| Tempted to delete CRM | Over-applying leaver SOP | Freeze retains ownership notes |
| Manager unclear | Hierarchy not refreshed | Lesson 21 manager mapping |
| Privileged still live on other LoA user | No LoA+priv detection | Add population/policy in Stretch |

---

## Training binder evidence

1. HR filter screenshot showing Sofia `onLeave=true`.
2. Identity cube attribute screenshot.
3. Freeze policy text (freeze vs terminate).
4. Disable/ticket evidence for ELDAP/CRM.
5. Manager notification / work-item text with 24h SLA.
6. Return-to-work procedure page.

---

## Knowledge check

1. How does leave differ from terminate in Meridian HR attributes?
2. What must happen to privileged entitlements when `onLeave=true`?
3. What is the manager notification SLA for LoA detection?
4. On return, may privileged access auto-restore with directory?
5. Who is Sofia’s manager in the lab?

### Answers

1. Leave: `onLeave=true` with employment usually still active (`status=1`). Terminate: `status=0` and `terminationDate` set.
2. Suspend or revoke immediately—do not leave WIRE_*, AWS_ADMIN, CORE, etc. usable during leave.
3. Manager work item / notification within 24 hours (faster for privileged).
4. No—privileged access requires a new request; only approved baseline may return after mini cert.
5. `sanjay.kapoor` (`MNB00006`).

---

## Stretch lab

1. Create population `MNB-OnLeave` (`onLeave == true`) and a policy or report flagging on-leave + (`WIRE_*` OR `AWS_ADMIN`).
2. Configure LCM lifecycle event on `onLeave` if licensed/imported.
3. Write Legal/HR communications snippet for privacy-sensitive leave without disclosing reason in IAM tickets.

---

## Summary

- You treated `sofia.torres` as a freeze case, not a leaver.
- You defined disable/suspend behavior that preserves identity and CRM ownership context.
- You documented 24h manager review and controlled return-to-work re-enable.

---

**Previous:** [Lesson 32 — Contractor & Contingent Worker Lifecycle](32-contractor-lifecycle.md)  
**Next:** [Lesson 34 — Rapid Offboarding Incident Drill](34-rapid-offboarding-drill.md)
