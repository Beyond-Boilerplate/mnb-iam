# Lesson 28 — Privileged Access Role Design

**Level:** Advanced  
**Track:** Roles  
**Time:** 60–75 minutes  
**Prereq:** Lesson 27; AWS_ADMIN and PRIV_BREAK entitlements exist in dictionary/apps  
**Lab data:** `entitlement-dictionary.csv` (AWS_ADMIN, PRIV_BREAK); cloud account extract; approval expectations for later LCM lessons

---

## Learning objectives

You will be able to:

- Create **`MNB-Role-CloudAdmin`** (AWS_ADMIN) and **`MNB-Role-BreakGlass`** (PRIV_BREAK) as request-only roles
- Prove neither role is granted by birthright or job assignment rules
- Define approval expectations (Technology Director + Security for break-glass)
- Place privileged roles on a **monthly** certification scope list
- Publish a privileged access runbook: joiners never auto-get; leavers revoke same day

---

## Why this matters

Privileged access needs time bounds, approvals, and monitoring. Standing cloud admin for convenience is a governance failure mode. Break-glass without logging and approval is theater.

**Control / audit:** Privileged roles are rare, owned, frequently certified, and excluded from birthright. Examiners ask for the privileged inventory, approval path, and revocation SLA. This lesson designs the IIQ role objects and control narrative; Lessons 35–37 wire request/approval flows.

---

## Concepts

```
Birthright / job rules ──✗──► CloudAdmin / BreakGlass
Access request (future) ──► approvals ──► assigned privileged role ──► entitlement
```

| Role | Entitlement | Requestable | Auto-assign | Cert frequency | Approvers (intent) |
| --- | --- | --- | --- | --- | --- |
| `MNB-Role-CloudAdmin` | AWS_ADMIN | Yes | No | Monthly | Manager + Technology / Cloud owner |
| `MNB-Role-BreakGlass` | PRIV_BREAK | Yes | No | Monthly (or per-use) | Technology Director + Security |

**Standing vs break-glass:** CloudAdmin may be standing but tightly controlled; BreakGlass is emergency, time-bounded, heavily logged (PAM integration noted even if not implemented in lab).

---

## Before you start

- [ ] Lesson 26 confirmed AWS_ADMIN not inside Developer/birthright
- [ ] AWS_ADMIN entitlement aggregatable from MNB-AWS-Cloud (or IT inventory)
- [ ] PRIV_BREAK present in dictionary (create managed attribute if missing)
- [ ] IIQ role editor available; catalog naming standard known

---

## Lab procedure

### Task 1 — Confirm privileged entitlements

1. Verify **AWS_ADMIN** managed attribute / entitlement (critical).
2. Verify or create **PRIV_BREAK** with display name “Break-Glass Admin” and risk critical.
3. Record application owners: cloud platform owner; Security for break-glass.

**Expected result:** Both entitlements visible with critical risk labeling.

**If it fails:** Aggregate cloud app; add managed attribute manually from dictionary—do not skip PRIV_BREAK.

### Task 2 — Create `MNB-Role-CloudAdmin`

1. Create role `MNB-Role-CloudAdmin`.
2. Description: “Standing AWS account administration. Not birthright. Requires approved access request and monthly review.”
3. Attach **AWS_ADMIN** only.
4. Mark **requestable = Yes**.
5. Ensure **no** identity assignment rule auto-grants by jobCode (including CLD01).
6. Owner: Technology / Cloud platform (document).

**Expected result:** Role exists; composition = AWS_ADMIN; no assignment rule firing on refresh for random identities.

**If it fails:** If a rule was added by mistake, delete it and re-refresh a CLD01 user to confirm no auto-assign.

### Task 3 — Create `MNB-Role-BreakGlass`

1. Create role `MNB-Role-BreakGlass`.
2. Description: “Emergency privileged access only. Dual approval Technology Director + Security. Time-bound. Full audit trail required.”
3. Attach **PRIV_BREAK** only.
4. Requestable = Yes; automatic assignment = No.
5. Owner: Security.

**Expected result:** BreakGlass role saved as request-only singleton entitlement pack.

### Task 4 — Birthright exclusion proof

1. Open `MNB-Birthright-Employee` composition—confirm no AWS_ADMIN / PRIV_BREAK.
2. Open Developer / RM / WireInitiator—confirm still clean.
3. Run Refresh MNB Identities on `amelia.brooks`—confirm she does **not** gain privileged roles.

**Expected result:** Documented proof screenshots: birthright unchanged; Amelia without CloudAdmin/BreakGlass.

### Task 5 — Approval expectations (design now, wire later)

1. Write approval matrix:

| Role | Approver 1 | Approver 2 | Notes |
| --- | --- | --- | --- |
| CloudAdmin | Line manager | Cloud/Tech owner | No self-approval |
| BreakGlass | Technology Director | Security | Emergency justification mandatory |

2. Note Lessons 36–37 will implement chains; this lesson freezes intent.

**Expected result:** Approval matrix in binder titled `MNB-Priv-Approval-Intent`.

### Task 6 — Certification frequency list

1. Add both roles to `MNB-Cert-Scope-Privileged-Monthly`.
2. Contrast: standard job roles quarterly (future campaigns).
3. Record owner of the monthly campaign (Security / IAM).

**Expected result:** Scope list artifact with two role names and frequency Monthly.

### Task 7 — Privileged runbook

1. Write runbook bullets:
   - Joiner: never auto-assigned CloudAdmin/BreakGlass
   - Mover: privileged access re-justified within 5 business days
   - Leaver: revoke same calendar day as HR termination (Lesson 31)
   - Break-glass: ticket ID + start/end time + MFA/PAM note
2. Store as `MNB-Runbook-Privileged-Access`.

**Expected result:** One-page runbook suitable for ops handoff.

### Task 8 — Optional detect-only profile note

1. Decide whether CloudAdmin has a detection profile (analytical) separate from assignment.
2. Prefer: detection helps find AWS_ADMIN holders; assignment only via request.

**Expected result:** Explicit detect-vs-assign note referencing Lesson 27.

---

## Acceptance criteria

- [ ] `MNB-Role-CloudAdmin` and `MNB-Role-BreakGlass` created request-only
- [ ] No birthright/job auto-assignment to privileged roles
- [ ] Approval intent matrix documented
- [ ] Monthly privileged cert scope list updated
- [ ] Privileged access runbook written

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| CLD01 users auto-get CloudAdmin | Accidental assignment rule | Remove rule; refresh; verify |
| PRIV_BREAK missing | Not in app extract | Create managed attribute / stub entitlement for role design |
| Managers can approve own CloudAdmin | Approval design gap | Ban self-approval in matrix; enforce in Lesson 36 |
| Break-glass standing forever | No time-bound process | Add expiry/SLA to runbook; later LCM sunset |

---

## Training binder evidence

- Screenshots: both privileged role definitions (requestable, compositions)
- Proof: Amelia / birthright without privileged roles
- `MNB-Priv-Approval-Intent` matrix
- `MNB-Cert-Scope-Privileged-Monthly` list
- `MNB-Runbook-Privileged-Access`

**Control owner:** Security (BreakGlass) + Technology (CloudAdmin) + IAM (IIQ objects)  
**SLA:** Leaver privileged revoke same day; break-glass dual approval before use

---

## Knowledge check

1. Who approves break-glass (intent)?
2. What is the cert frequency for privileged roles?
3. Are these roles birthright eligible?
4. Which entitlement maps to CloudAdmin?
5. What happens on joiner day regarding these roles?

### Answers

1. Technology Director **and** Security (dual approval).
2. Monthly (at minimum for standing privileged).
3. No.
4. AWS_ADMIN.
5. Joiners never auto-receive them—request/approval only when justified.

---

## Stretch lab

- Draft MFA / PAM requirement note attached to both roles (“IIQ role is necessary but not sufficient”).
- Propose automatic sunset: BreakGlass assignment expires in 8 hours unless extended.
- Build population of AWS_ADMIN account holders for the first monthly privileged campaign dry-run.

---

## Summary

- Privileged roles are request-only, narrowly composed, and frequently certified.
- CloudAdmin and BreakGlass stay out of birthright and job automation.
- Approval intent and same-day leaver revoke are control commitments—not optional polish.

---

**Previous:** [Lesson 27 — Role Detection vs Assignment](27-role-detection-vs-assignment.md)  
**Next:** [Lesson 29 — Joiner Lifecycle](29-joiner-lifecycle.md)
