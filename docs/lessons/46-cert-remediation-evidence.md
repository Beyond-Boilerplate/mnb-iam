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
- Separate “phase complete” from “remediations open” in KPI language

---

## Why this matters

**Business.** A certification marked “complete” with open revokes is incomplete. When Rachel revokes leftover `AWS_ADMIN` on a report, the control is not the click — it is the removal (or documented exception) that follows. Without that chain, Meridian’s quarterly review is theater.

**Control / audit.** Internal audit and banking examiners sample both decision quality and remediation closure. Rubber-stamping (approve-all, sub-minute completes) destroys the control’s credibility even when completion % looks green. Control owner: IAM Ops chasing remediations; Risk tracking overdue KPI; managers owning decision quality.

---

## Concepts

### Remediation vs certification complete

**Remediation** is the downstream work created when a certifier revokes access: provisioning plan, access request, or manual ticket depending on connector and IIQ configuration.

**Certification phase complete** means managers finished deciding. **Control complete** means remediations closed (or exceptions documented). Examiners care about the second definition.

### Evidence binder (exam pack)

| Artifact | Proves |
| --- | --- |
| Campaign definition | Scope, period, cert type, owner |
| Population / inclusion logic | Who was in scope and why |
| Completion % + aging | Timeliness / late managers |
| Sample decisions | Thoughtful review vs rubber-stamp |
| Revoke → provisioning proof | Access actually removed |
| Notification sample | Users were informed (SLA start) |

### Rubber-stamp signals

- Entire campaign approved in minutes
- Zero revokes on high-risk apps (Wire/SAP/AWS in scope)
- Identical comments on every line
- Certifier never opened line-item detail
- Approve rate ~100% with known toxic pairs in scope (e.g. both `WIRE_INIT` and `WIRE_APPR` on one person)

### Meridian example — a revoke that “completed” but did nothing

Rachel revokes residual `AWS_ADMIN` on a report. Campaign shows 100% complete. Three weeks later aggregation still shows the entitlement — the remediation IdentityRequest failed on a bad file path (Lesson 47). Completion % was green; the control was red. Your binder must include the revoke *trace*, not only the decision screenshot.

The wrong way: hand Audit a green completion dashboard and no revoke traces. That fails sampling.

---

## How it works

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

| KPI | Good signal | Bad signal |
| --- | --- | --- |
| Completion % | High by due date | High with zero comments |
| Remediations open | Trend to zero by day +10 | Still open after “complete” |
| Revoke rate on critical ents | Non-zero when residuals exist | Always 0% |
| QA sample grade | Pass / Coach | Fail (rubber-stamp) |

Binder folder: `MNB-Exam-Binder-Certs/` — this lesson’s cover sheet feeds Capstone evidence packs.

Include artifacts from Lessons 43–45: manager campaign seed, owner cert decisions, micro-cert Risk one-pager with `FIND-IAM-45-001`. The cover checklist (Task 3) is how those pieces become one examiner pack.

---

## Before you start

- [ ] At least one campaign from Lessons 43–45 with ≥1 revoke decision
- [ ] Access to Task results, Identity Requests, and Work Items
- [ ] Ability to re-run Account Aggregation on affected apps
- [ ] Binder folder ready: `MNB-Exam-Binder-Certs/`
- [ ] Copy of `certification-sample.txt` available for notification evidence
- [ ] Note any open remediations from prior lessons so Task 1 has a live revoke to trace

---

## Lab procedure

### Task 1 — Trace one revoke end-to-end

Examiners pick one revoke and ask you to walk the chain. Practice that walk now. Prefer a high-risk entitlement (`WIRE_*`, `SAP_FI`, `AWS_ADMIN`) so the story matches Meridian’s scoped campaigns.

1. Open a completed (or in-progress) campaign; pick a **Revoke** line (identity + entitlement + app).
2. Navigate to related remediation: work item, IdentityRequest, or provisioning transaction (path varies by IIQ version).
3. Open the **provisioning plan** if present: Application, NativeIdentity, AttributeRequest/Operation.
4. Confirm target account/entitlement removed or disabled.
5. Run **Account Aggregation** for that app; open the identity cube; confirm absence.
6. Record IDs in the binder: campaign name, decision line, request/plan ID, aggregation Task Result time.

**Expected result:** Written trace: Decision ID/line → request/plan ID → cube proof. One revoke fully closed.

**If it fails:** If remediation stuck, capture error text and park for Lesson 47; still document the intended chain.

### Task 2 — Measure completion %

Separate phase complete from remediations open — two different KPIs. Green completion with red remediations is still a finding.

1. Open campaign dashboard / certification status.
2. Record: total certifiers, completed, open, % complete.
3. List late managers (past due date) if any.
4. Separate “phase complete” from “remediations open.”
5. If remediations open > 0, list each with owner and age in days.

**Expected result:** KPI line: `MNB-Cert-Completion — campaign — XX% — remediations open: N — date` plus aged open-item list if N > 0.

### Task 3 — Build evidence binder checklist

This checklist becomes the Capstone cover sheet. Build it once; reuse forever.

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

Sampling protects the control. Focus on high-risk maintains — birthright ELDAP approves teach little.

1. Randomly select five **Approve/Maintain** decisions on high-risk entitlements.
2. For each, answer: Does job title / dept support this access? Any SoD conflict (`WIRE_INIT`+`WIRE_APPR`, `SAP_FI`+`AWS_ADMIN`)?
3. Flag rubber-stamp symptoms (see Concepts).
4. Score campaign quality: Pass / Coach / Fail.

**Expected result:** QA sheet with five rows and overall quality grade.

**If it fails:** If campaign had fewer than five approves, sample all approves plus any maintains.

### Task 5 — Manager coaching note

Coaching prevents next quarter’s Fail grade. Keep it short enough to attach to launch mail.

Draft 5–8 lines to managers:

- What good looks like (spot-check, revoke residuals, comment on privileged keep)  
- What fails exam sampling (approve-all, no comments)  
- Reminder: completion ≠ control until revokes close  

**Expected result:** Coaching note ready to attach to next quarterly launch mail.

### Task 6 — Assemble the pack and self-audit

1. Place all checklist items into `MNB-Exam-Binder-Certs/` with a dated index.
2. Self-audit: can a stranger answer “show one revoke that actually removed access” in two minutes using only the pack?
3. If no, fix the missing revoke trace before Capstone.

**Expected result:** Indexed binder that passes the two-minute stranger test.

---

## Acceptance criteria

- [ ] One revoke traced to cube-confirmed removal (or documented blocker with Lesson 47 handoff)
- [ ] Completion % and open remediations recorded
- [ ] Evidence binder checklist created
- [ ] Five-decision QA sample completed with grade
- [ ] Manager coaching note drafted
- [ ] Assembled pack passes two-minute stranger test

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Revoke with no remediation | Continuous cert / read-only mode | Check cert configuration for remediation enabled |
| Plan success but cube still shows access | Aggregation not run | Aggregate; check correlation |
| 100% complete, 0% remediations closed | Process gap | Add remediation KPI to dashboard |
| Cannot find decision detail | Archived cert | Use reports / Debug Certification object |
| QA finds wire dual on one person | Real defect | Open SoD violation path (Lesson 41); revoke immediately |
| Binder fails stranger test | Missing revoke trace | Complete Task 1 before Capstone |

---

## Training binder evidence

- Revoke trace one-pager  
- Completion % screenshot  
- Binder checklist (this lesson’s cover sheet)  
- QA sample + coaching note  
- Indexed `MNB-Exam-Binder-Certs/` cover sheet with stranger-test note  

---

## Knowledge check

1. What proves a revoke actually happened?
2. List four binder artifacts examiners want.
3. Name three rubber-stamp signals.
4. Why is completion % alone insufficient?
5. Who owns chasing open remediations after cert end date?
6. What two KPIs must you report separately?

### Answers

1. Provisioning/remediation completion plus post-aggregate cube (or target system) confirmation.
2. Definition, population logic, completion/aging, decision sample, revoke proof, notifications (any four+).
3. Ultra-fast approve-all; zero revokes on high-risk scope; empty/identical comments.
4. Open remediations mean access may still exist.
5. IAM ops with certifier/manager escalation; Risk tracks overdue KPI.
6. Phase completion % and remediations still open.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “certification remediation” and “provisioning from certification.”
- [SailPoint Community](https://community.sailpoint.com/) — search “certification evidence” / remediation tracking.
- [NIST SP 800-53 AC-2 / CA-7](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) — account review and continuous monitoring evidence.
- [FFIEC Information Technology Examination Handbook](https://ithandbook.ffiec.gov/) — search audit evidence and access review expectations.
- [ISACA — Audit evidence / SOX ITGC primers](https://www.isaca.org/) — search “audit evidence” and “access certification” for binder structure.

---

## Stretch lab

Design a manager scorecard: on-time %, revoke rate on critical ents, comment rate on privileged maintains. Propose thresholds for “coach” vs “escalate to helen.ross.” Feed scorecard outputs into next quarter’s launch mail so coaching is continuous, not annual theater.

---

## Summary

- Certifications end when remediations close, not when managers click Done.
- Binders combine definition, sampling, and revoke proof.
- Rubber-stamp detection protects the control’s credibility.
- The two-minute stranger test is the pack quality gate before Capstone.

---

**Previous:** [Lesson 45 — Targeted Campaigns](45-targeted-campaigns.md)  
**Next:** [Lesson 47 — Provisioning Troubleshooting](47-provisioning-troubleshooting.md)
