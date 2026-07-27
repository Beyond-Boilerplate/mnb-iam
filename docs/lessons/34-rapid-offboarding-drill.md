# Lesson 34 — Rapid Offboarding Incident Drill

**Level:** Advanced  
**Track:** Lifecycle  
**Time:** 60–75 minutes  
**Prereq:** Lessons 31–33 (leaver, contractor, LoA); ability to disable accounts in lab  

**Lab data:**
- Drill target options: `marcus.approve` (`MNB00091`) wire approver, or a disposable copy identity
- Wire context: `lab-data/apps/MNB-WirePortal.csv` / initiators & approvers extracts
- Contrast: planned leaver (`jordan.reed`) vs emergency lockout (this drill)

---

## Learning objectives

You will be able to:

1. Write a Meridian **rapid offboarding runbook** with requester verification, system order, and evidence.
2. Execute an emergency disable path in the lab against a payments-relevant identity.
3. Capture a timestamped timeline suitable for Security incident records.
4. Schedule follow-up HR reconcile so authoritative status catches up to the emergency action.
5. Run a short tabletop + lab retro that lists control gaps (PAM, dual approval of disable, etc.).
6. State who may authorize rapid offboard and which systems are first.

---

## Why this matters

**Business.** Involuntary terminations, insider-risk tips, and compromised credentials do not wait for the nightly HR file. Payments users (`WIRE_APPR` / `WIRE_INIT`) can move money in minutes. Marcus Chen (`marcus.approve`) is a live wire approver — locking him out late is a money-movement incident, not an IAM backlog item.

**Control / audit.** A wiki page written during the incident fails exams. You need a drilled runbook with identity verification of the requester, ordered disable steps, and HR reconciliation. Control owner: Security Operations with IAM Ops; HR and Legal informed. Examiner question: *Show the last drill evidence and time-to-disable for a wire user.*

---

## Concepts

### Planned leaver vs rapid offboard

Lesson 31 starts from HR. This drill **disables first**, then aligns HR — opposite order for a reason.

| Aspect | Planned leaver (L31) | Rapid offboard (this lesson) |
| --- | --- | --- |
| Trigger | HR `status=0` | Security/HR/Legal urgent call |
| Order | HR → Aggregate → Refresh → residuals | **Disable first**, HR reconcile after |
| SLA | Same day / 1 hour directory | Minutes for directory + payments |
| Evidence | Lifecycle pack | Incident timeline + INC ticket |
| Example persona | `jordan.reed` | `marcus.approve` (wire) |

### Disable priority (Meridian payments user)

```text
1. Verify requester identity (callback / known roster)
2. Disable ELDAP / directory login
3. Disable Wire Portal (WIRE_INIT and/or WIRE_APPR)
4. Disable Core / ACH if held
5. Revoke roles / kill sessions (PAM if exists)
6. Snapshot entitlement inventory
7. Open INC ticket + notify manager/Legal
8. HR status reconcile within agreed window
9. Residual cert / orphan hunt next business day
```

### Authorized requesters (lab policy)

| Role | May authorize? | Notes |
| --- | --- | --- |
| Head of IAM (`helen.ross`) | Yes | IAM leadership |
| SOC / Security on-call | Yes | Insider risk / compromise |
| HR BP + manager jointly | Yes | Involuntary exit |
| Random manager Slack DM | No | Verify out-of-band |
| App owner alone | No | Escalate to Security/IAM |

**IIQ terms:** Emergency disable may use Manage Accounts, RapidSetup/LCM terminate workflows (if configured), or file disable + aggregation. *IdentityRequest* is not required for emergency lockout — do not wait on approvals to stop bleeding.

The wrong way: open an access-request catalog item and wait for manager approval while `WIRE_APPR` stays live.

---

## How it works

```text
SOC / Legal / HR urgent call
        │
        ▼
Verify requester (callback) + open INC
        │
        ▼
Snapshot entitlements (before)
        │
        ▼
Disable ELDAP ──► Disable WIRE_APPR / WIRE_INIT
        │
        ▼
Notify manager (rachel.evans) + Legal + HR
        │
        ▼
HR reconcile ticket (status=0 when confirmed)
        │
        ▼
Next-day residual hunt + restore if drill-only
```

| Artifact | Purpose |
| --- | --- |
| `RUNBOOK-MNB-rapid-offboard.md` | Pre-written order of operations |
| `timeline.txt` | T+ timestamps for incident record |
| `snapshot-before.txt` | What access existed at lockout |
| INC + HR tickets | Audit trail linking emergency to authoritative HR |
| Retro gap list | Continuous improvement for next drill |

SLA sketch: directory + wire within minutes of verified request; HR reconcile within ~4 business hours; residual review next business day.

---

## Before you start

- [ ] IIQ up; admin access to disable accounts.
- [ ] Choose drill identity: prefer **copy** of `marcus.approve` if you can clone; otherwise use lab marcus and restore afterward.
- [ ] Stopwatch or clock for timeline.
- [ ] Folder `~/iiq-lab-data/evidence/rapid-offboard-YYYYMMDD/` (create it).
- [ ] Do **not** disable shared `spadmin` or leadership identities.

---

## Lab procedure

### Task 1 — Tabletop: write the runbook before clicking

Runbooks written mid-incident are fiction. Write first, then execute.

1. In your evidence folder, create `RUNBOOK-MNB-rapid-offboard.md` (or `.txt`) with sections:
   - Purpose / Sev definition
   - Authorized requesters + verification steps
   - System disable order (directory → wire → core/ACH → cloud → other)
   - Snapshot / evidence checklist
   - Notification matrix (Security, IAM, manager, HR, Legal)
   - HR reconcile window (e.g. 4 business hours)
   - Post-incident residual certification
2. Hold a 10-minute tabletop: “SOC calls — Marcus may be insider risk. Lock wire approve now.”
3. Assign drill roles: Requester (Security), Executor (you/IAM), Scribe (timeline).

**Expected result:** Written runbook exists **before** lab execution. Tabletop notes list who verifies the call.

**If it fails:** Use the priority list in Concepts; fill Meridian names.

### Task 2 — Verify requester and open the incident

Attackers and confused deputies can request lockouts. Out-of-band verification is the first control, not bureaucracy.

1. Simulate inbound request: `SOC on-call` requests lockout of `marcus.approve` citing insider-risk tip.
2. Perform verification step (lab): record callback phrase / ticket `MNB-INC-34XX` and requester name in the timeline.
3. Refuse to proceed if requester is unverified — document that refusal path.

**Expected result:** Timeline line 0 = verified requester + INC id **before** first disable.

**If it fails:** Invent lab INC `MNB-INC-3401` and a named SOC analyst; still write verification.

### Task 3 — Execute emergency disable in lab

Directory before or with wire — never “wire only” while login still works.

1. Open identity `marcus.approve` (`MNB00091`). Confirm entitlements include `WIRE_APPR` and `ELDAP`.
2. Snapshot entitlements to `snapshot-before.txt` (copy from UI or IT access CSV lines).
3. Disable in order:
   - Directory / `ELDAP` account link
   - Wire / `WIRE_APPR` account or entitlement
4. Use available lab methods: Manage Accounts disable, mark `disabled` in delimited files + **Account Aggregation** tasks, or LCM terminate if configured.
5. Refresh identity; confirm disabled signals.
6. Record timestamps for each step in `timeline.txt`.

**Expected result:** Marcus cannot be treated as an active wire approver in IIQ after disable; timeline shows directory before or with wire, not “wire only.”

**If it fails:** File-based disable on `MNB-ActiveDirectory.csv` and `MNB-WirePortal-Approvers.csv` (or combined wire file) + aggregation is valid drill evidence — restore files after.

### Task 4 — Capture timeline and notifications

Timestamps are the drill’s primary learning artifact.

1. Complete `timeline.txt` example structure:

```text
T+0:00  Verified SOC requester; opened MNB-INC-3401
T+0:03  Snapshot entitlements saved
T+0:07  ELDAP disabled
T+0:12  WIRE_APPR disabled
T+0:15  Manager rachel.evans notified
T+0:20  HR reconcile ticket filed
```

2. Draft notification stubs to `rachel.evans@meridiannb.com` (manager), HR, Legal.
3. Store screenshots of identity accounts tab post-disable.

**Expected result:** Evidence folder contains snapshot, timeline, notifications, and UI proof.

**If it fails:** Write timeline from memory immediately — drills without timestamps teach little.

### Task 5 — HR reconcile and residual follow-up

Emergency disable without HR reconcile is “shadow HR” — overnight aggregates can resurrect access or leave two truths.

1. Create fictional HR ticket: “Set `marcus.approve` status=0 / terminationDate when involuntary exit confirmed; until then keep emergency disable.”
2. Schedule residual review next business day: orphan hunt, AWS/SAP check (Marcus may not have them — still run the checklist).
3. If this was a pure drill, **restore** Marcus’s lab access and note restore time in timeline (avoid leaving shared lab broken).

**Expected result:** Documented reconcile path so emergency disable is not “shadow HR.” Restore note if drill-only.

**If it fails:** At minimum write the HR ticket text and restore steps even if you did not flip HR yet.

### Task 6 — Retro: list gaps

Honest drills end with gaps, not victory slides.

1. Facilitate 5-minute retro. Capture gaps such as:
   - No PAM / no session kill API
   - No dual-control on emergency disable
   - No SMS/out-of-band approve for executor
   - Aggregation delay if file-only lab
   - Missing break-glass logging (Lesson 37 related)
2. Assign one improvement for the next drill.

**Expected result:** Gap list with at least three items and one named follow-up.

---

## Acceptance criteria

- [ ] Runbook written before execution.
- [ ] Requester verification recorded with INC id.
- [ ] Emergency disable executed (directory + wire) with timestamps.
- [ ] Evidence folder populated (snapshot, timeline, screenshots).
- [ ] HR reconcile ticket / plan documented.
- [ ] Retro gaps listed; lab restored if drill-only.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Waiting on access request approval | Wrong pattern | Emergency disable ≠ LCM catalog request |
| Disabled wrong user | Poor identity search | Confirm employeeId `MNB00091` |
| Wire still active in file | Forgot re-aggregate | Run Account Aggregation on wire app |
| Shared lab broken | Forgot restore | Re-copy lab-data apps files |
| No timestamps | Scribe missing | Reconstruct ASAP; rerun drill |

---

## Training binder evidence

1. Runbook document.
2. Tabletop attendance / role notes.
3. `timeline.txt` with T+ timestamps.
4. Before/after entitlement snapshot.
5. INC + HR reconcile ticket texts.
6. Retro gap list.

---

## Knowledge check

1. Who may authorize rapid offboard at Meridian (name at least two roles)?
2. Which systems are first for a payments user?
3. Why must HR reconcile after emergency disable?
4. Why is requester verification mandatory?
5. How does this differ from Lesson 31’s planned leaver flow?
6. Why is Marcus a better drill target than a teller-only identity?

### Answers

1. Examples: SOC/Security on-call, Head of IAM (`helen.ross`), HR+manager for involuntary exit — not an unverified Slack DM.
2. Directory/ELDAP, then Wire Portal entitlements; then core/ACH/cloud as held.
3. Authoritative HR must match reality so overnight aggregates do not resurrect access and audit has a single truth.
4. Attackers and confused deputies can request lockouts or avoid them; out-of-band verify prevents abuse.
5. Planned leaver starts from HR status; rapid offboard disables first, then aligns HR.
6. He holds `WIRE_APPR` — payments blast radius makes minute-level SLA meaningful.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “emergency termination” and “manage accounts disable.”
- [NIST SP 800-61 Rev. 2 — Computer Security Incident Handling Guide](https://csrc.nist.gov/pubs/sp/800/61/r2/final) — incident timeline, containment, and evidence discipline that map to this drill.
- [NIST SP 800-53 IR / AC families](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) — incident response and account disablement controls.
- [FFIEC Information Technology Examination Handbook](https://ithandbook.ffiec.gov/) — search incident response and access revocation expectations.
- [ISACA — Incident Management primers](https://www.isaca.org/) — search “incident response” for runbook and evidence expectations useful in exams.

---

## Stretch lab

1. Add Legal/HR communications templates (no privileged details in email subject).
2. Script a checklist CSV for system owners’ call tree.
3. Link drill output to Lesson 37 break-glass (emergency *grant* vs emergency *remove*).

---

## Summary

- You wrote and tabletop-tested a Meridian rapid offboarding runbook.
- You executed a timed emergency disable on a wire-relevant lab identity and captured evidence.
- You closed the loop with HR reconcile planning and a gap retro.

---

**Previous:** [Lesson 33 — Leave of Absence Controls](33-leave-of-absence.md)  
**Next:** [Lesson 35 — Access Request Catalog](35-access-request-catalog.md)
