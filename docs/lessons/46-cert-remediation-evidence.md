# Lesson 46 — Certification Remediation & Evidence

**Level:** Intermediate  
**Track:** Certifications  
**Time:** 60–75  
**Prereq:** Lesson 45 — Targeted Campaigns  

**Lab data:** Prior campaign artifacts from Lessons 43–45; `notifications/certification-sample.txt`

---

## Learning objectives

You will be able to:

- Trace a certification **revoke** from decision → remediation work item / provisioning plan → account outcome
- Measure campaign **completion %** and list late certifiers
- Assemble an examiner-ready **evidence binder** checklist for Meridian certs
- Sample five approve decisions for rubber-stamp signals
- Propose a short manager coaching note based on QA findings

---

## Why this matters

A certification marked “complete” with open revokes is incomplete. The control is not the click—it is the removal (or documented exception) that follows. Internal audit and banking examiners sample both decision quality and remediation closure.

Rubber-stamping (approve-all, sub-minute completes) destroys the control’s credibility even when completion % looks green.

---

## Concepts

**Remediation** is the downstream work created when a certifier revokes access: provisioning plan, access request, or manual ticket depending on connector and IIQ configuration.

**Evidence binder** (exam pack) typically includes:

| Artifact | Proves |
| --- | --- |
| Campaign definition | Scope, period, cert type, owner |
| Population / inclusion logic | Who was in scope and why |
| Completion % + aging | Timeliness / late managers |
| Sample decisions | Thoughtful review vs rubber-stamp |
| Revoke → provisioning proof | Access actually removed |
| Notification sample | Users were informed (SLA start) |

```
Cert decision: Revoke
        │
        ▼
 Remediation item / IdentityRequest / plan
        │
        ▼
 Connector / file update / disable
        │
        ▼
 Re-aggregate + confirm cube clean
        │
        ▼
 Binder: before/after screenshots + ticket IDs
```

**Rubber-stamp signals:** entire campaign approved in minutes; zero revokes on high-risk apps; identical comments; certifier never opened line-item detail; approve rate ~100% with known toxic pairs in scope.

---

## Before you start

- [ ] At least one campaign from Lessons 43–45 with ≥1 revoke decision
- [ ] Access to Task results, Identity Requests, and Work Items
- [ ] Ability to re-run Account Aggregation on affected apps
- [ ] Binder folder ready: `MNB-Exam-Binder-Certs/`

---

## Lab procedure

### Task 1 — Trace one revoke end-to-end

1. Open a completed (or in-progress) campaign; pick a **Revoke** line (identity + entitlement + app).
2. Navigate to related remediation: work item, IdentityRequest, or provisioning transaction (path varies by IIQ version).
3. Open the **provisioning plan** if present: Application, NativeIdentity, AttributeRequest/Operation.
4. Confirm target account/entitlement removed or disabled.
5. Run **Account Aggregation** for that app; open the identity cube; confirm absence.

**Expected result:** Written trace: Decision ID/line → request/plan ID → cube proof. One revoke fully closed.

**If it fails:** If remediation stuck, capture error text and park for Lesson 47; still document the intended chain.

### Task 2 — Measure completion %

1. Open campaign dashboard / certification status.
2. Record: total certifiers, completed, open, % complete.
3. List late managers (past due date) if any.
4. Separate “phase complete” from “remediations open.”

**Expected result:** KPI line: `MNB-Cert-Completion — campaign — XX% — remediations open: N — date`.

### Task 3 — Build evidence binder checklist

Create a checklist file (markdown or paper) with:

- [ ] Campaign definition screenshot  
- [ ] Population logic  
- [ ] Notification sample (`certification-sample.txt` or IIQ mail)  
- [ ] Completion % report  
- [ ] Five-decision QA sample  
- [ ] Revoke trace (Task 1)  
- [ ] Residual open items with owners  

**Expected result:** Checklist used as cover sheet for Capstone.

### Task 4 — QA sample five approves

1. Randomly select five **Approve/Maintain** decisions on high-risk entitlements.
2. For each, answer: Does job title / dept support this access? Any SoD conflict?
3. Flag rubber-stamp symptoms (see Concepts).
4. Score campaign quality: Pass / Coach / Fail.

**Expected result:** QA sheet with five rows and overall quality grade.

**If it fails:** If campaign had fewer than five approves, sample all approves plus any maintains.

### Task 5 — Manager coaching note

Draft 5–8 lines to managers:

- What good looks like (spot-check, revoke residuals, comment on privileged keep)  
- What fails exam sampling (approve-all, no comments)  
- Reminder: completion ≠ control until revokes close  

**Expected result:** Coaching note ready to attach to next quarterly launch mail.

---

## Acceptance criteria

- [ ] One revoke traced to cube-confirmed removal (or documented blocker with Lesson 47 handoff)
- [ ] Completion % and open remediations recorded
- [ ] Evidence binder checklist created
- [ ] Five-decision QA sample completed with grade
- [ ] Manager coaching note drafted

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Revoke with no remediation | Continuous cert / read-only mode | Check cert configuration for remediation enabled |
| Plan success but cube still shows access | Aggregation not run | Aggregate; check correlation |
| 100% complete, 0% remediations closed | Process gap | Add remediation KPI to dashboard |
| Cannot find decision detail | Archived cert | Use reports / Debug Certification object |
| QA finds wire dual on one person | Real defect | Open SoD violation path (Lesson 41); revoke immediately |

---

## Training binder evidence

- Revoke trace one-pager  
- Completion % screenshot  
- Binder checklist (this lesson’s cover sheet)  
- QA sample + coaching note  

---

## Knowledge check

1. What proves a revoke actually happened?
2. List four binder artifacts examiners want.
3. Name three rubber-stamp signals.
4. Why is completion % alone insufficient?
5. Who owns chasing open remediations after cert end date?

### Answers

1. Provisioning/remediation completion plus post-aggregate cube (or target system) confirmation.  
2. Definition, population logic, completion/aging, decision sample, revoke proof, notifications.  
3. Ultra-fast approve-all; zero revokes on high-risk scope; empty/identical comments.  
4. Open remediations mean access may still exist.  
5. IAM ops with certifier/manager escalation; Risk tracks overdue KPI.

---

## Stretch lab

Design a manager scorecard: on-time %, revoke rate on critical ents, comment rate on privileged maintains. Propose thresholds for “coach” vs “escalate to helen.ross.”

---

## Summary

- Certifications end when remediations close, not when managers click Done.
- Binders combine definition, sampling, and revoke proof.
- Rubber-stamp detection protects the control’s credibility.

---

**Previous:** [Lesson 45 — Targeted Campaigns](45-targeted-campaigns.md)  
**Next:** [Lesson 47 — Provisioning Troubleshooting](47-provisioning-troubleshooting.md)
