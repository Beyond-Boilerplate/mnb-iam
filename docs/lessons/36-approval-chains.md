# Lesson 36 — Approval Chains & Escalations

**Level:** Intermediate  
**Track:** Requests  
**Time:** 60–75 minutes  
**Prereq:** Lesson 35 (catalog + submitted request); LCM active (`init-lcm.xml`); manager hierarchy (Lesson 21)  

**Lab data:**
- Low-risk path: `CRM` → manager approval
- Privileged design: `AWS_ADMIN` → manager + Technology owner `christopher.hayes`
- Personas: RM managers e.g. `sanjay.kapoor`; cloud owner `christopher.hayes@meridiannb.com`; Security escalation `helen.ross`
- Dual-control reminder: wire approvals must not collapse initiate/approve into one vote

---

## Learning objectives

You will be able to:

- Trace and complete a **manager-only** approval for a low-risk CRM request
- Design a **dual approval** chain for AWS/privileged access (manager + app/technology owner)
- Execute a **reject** path and confirm no provisioning occurs
- Define escalation after N days (manager’s manager / Security)
- Capture work-item history as approval evidence
- Explain serial vs parallel approval trade-offs for Meridian risk tiers

---

## Why this matters

**Business.** Wrong approvers create rubber stamps (everything approved) or deadlock (nothing moves). CRM for a commercial RM should be fast—`sanjay.kapoor` can affirm business need. AWS for a contractor like `raj.external` must be slow and dual-controlled: manager affirms SOW need; `christopher.hayes` affirms least privilege and expiry.

**Control / audit.** Examiners sample closed requests: *Who approved, when, and what happens on reject?* Control owner: IAM Governance; app owners own privileged second votes. Escalation prevents silent queue death when managers are OOO (including when Sofia’s manager is covering LoA books).

---

## Concepts

### Meridian approval tiers

| Access | Approvers | Mode | Escalation |
| --- | --- | --- | --- |
| `CRM` / medium business | Manager only | Serial (single) | Day 3 → manager’s manager |
| `DWRP` | Manager | Serial | Day 3 → manager’s manager |
| `AWS_ADMIN` | Manager + `christopher.hayes` (Technology) | Serial or parallel dual | Day 2 → Security (`helen.ross` / SOC) |
| `PRIV_BREAK` | Security (Lesson 37) | Strict | Immediate page—not email-only |
| `WIRE_INIT` / `WIRE_APPR` | Manager + Treasury owner (`rachel.evans`) | Dual; never self-approve both sides | Day 2 → Payments Ops leadership |

### Dual control is not “two managers”

Payment segregation (`priya.wire` vs `marcus.approve`) is about **roles and entitlements**, not merely two approval clicks on one toxic pack. Approval chains reinforce ownership; they do not replace Lesson 25’s split roles.

### Reject is a control, not a failure

Rubber-stamp culture treats reject as awkward. Examiners want proof that reject leaves a forensic trail and **blocks provisioning**. Lesson 38 will package that evidence.

---

## How it works

IdentityRequest submission creates work items per the approval scheme. Decisions advance or cancel the request; escalation reassigns overdue items.

```
IdentityRequest submitted
        │
        ▼
Work item(s) to approver(s)
        │
   ┌────┴────┐
   ▼         ▼
Approve    Reject ──► Request cancelled; no provision
   │
   ▼
Next approver (if dual) or provisioning
        │
        ▼ (if overdue)
Escalation reassignment (manager’s manager / Security)
```

| Mode | Behavior | When Meridian uses it |
| --- | --- | --- |
| Serial dual | Approver 1 then Approver 2 | Clear ownership sequence |
| Parallel dual | Both required before provision | Speed without removing control |
| Manager-only | Single work item | Low-risk CRM/DWRP |

**IIQ terms:** *Approval scheme* / LCM business process rules decide who gets work items. *Escalation* reassigns overdue work items. *Reject* must leave a forensic trail on the IdentityRequest.

---

## Before you start

- [ ] LCM Access Request UI works (Lesson 35)
- [ ] At least one pending or new CRM request available
- [ ] Manager links populated on target identities (Lesson 21)
- [ ] You can open **Work Items** inbox as approver (or use `spadmin` forward/act-as if lab limited)
- [ ] Decision recorded for AWS dual-approval design even if full rule config is partial in lab

---

## Lab procedure

### Task 1 — Complete manager approval for CRM (low-risk)

Prove the happy path before designing privileged complexity.

1. Submit a fresh CRM request if none pending (Lesson 35 steps).
2. Identify the target’s manager (from identity cube).
3. Open the approval **Work Item** (manager inbox or administrator search).
4. Review requested item, justification, and SoD warnings if shown.
5. **Approve** the CRM request.
6. Return to IdentityRequest; confirm state advanced (Approved / Provisioning / Finished—depending on connectors).

**Expected result:** Work item history shows manager identity, approve decision, and timestamp. CRM path required only manager.

**If it fails:** As `spadmin`, use work item administration to open the item; verify manager attribute is set (Lesson 21).

### Task 2 — Design dual approval for AWS_ADMIN

Standing cloud admin needs two distinct votes—especially for contractors.

1. Write the Meridian rule (binder):

```text
AWS_ADMIN / MNB-Role-CloudAdmin approval
1) Manager affirms business need and SOW/employment status
2) Technology owner christopher.hayes affirms least privilege and expiry
Neither approval alone is sufficient.
```

2. In LCM approval configuration (QuickLink policies, Approval schemes, or workflow—use your lab’s equivalent), configure or document dual approval: manager then owner, or parallel both-required.
3. Prefer **parallel** for speed only if both approvals are mandatory before provision; document choice.
4. Note: `raj.external` manager `christopher.hayes` may be both tech owner and manager—document compensating control (second Security vote) if that conflict appears.

**Expected result:** Design artifact naming both approvers; config screenshot if UI allows, else explicit “configured in prod / stubbed in lab” note with intended object names.

**If it fails:** Do not invent menu clicks—capture the design and map to IIQ approval scheme docs in product PDF.

### Task 3 — Test the reject path

1. Submit a disposable request (CRM or DWRP) with justification `REJECT-TEST-L36`.
2. Open the approval work item.
3. **Reject** with comment: `Business case insufficient — training reject path`.
4. Confirm IdentityRequest shows rejected/cancelled end state.
5. Confirm no new entitlement appeared on the identity after Refresh.

**Expected result:** Reject guarantees no provisioning for that request; comment retained for audit.

**If it fails:** If reject unavailable, cancel request as administrator and document equivalent control—but prefer true reject.

### Task 4 — Define escalation policy

Queues die when managers are OOO. Escalation is the anti-deadlock control.

1. Draft escalation:

| Tier | Overdue after | Escalate to |
| --- | --- | --- |
| CRM / DWRP | 3 business days | Manager’s manager |
| AWS dual | 2 business days | Security / `helen.ross` |
| Break-glass | 1 hour | SOC bridge |

2. If lab supports work item escalation settings, configure 3-day escalate for standard requests.
3. Note OOO coverage: managers must have delegates where possible (e.g. covering Sofia’s book during LoA).

**Expected result:** Escalation table approved for Meridian training binder; optional UI config screenshot.

**If it fails:** Policy-only is acceptable; mark config as follow-up.

### Task 5 — Evidence pack for approvals

1. Screenshot work item history for the approved CRM request.
2. Screenshot reject test IdentityRequest.
3. Save AWS dual-approval design page.
4. Store under `~/iiq-lab-data/evidence/approvals-L36/`.

**Expected result:** Examiner can see approve and reject examples without re-running the lab.

### Task 6 — Self-approval ban

1. Write: no identity may approve their own CloudAdmin or BreakGlass request.
2. Note how manager-equals-requester cases escalate to Security.

**Expected result:** Self-approval ban line in the approval matrix.

---

## Acceptance criteria

- [ ] CRM manager approval completed with history
- [ ] Dual approval for AWS designed (manager + `christopher.hayes`)
- [ ] Reject path tested; no provision on reject
- [ ] Escalation table written (3-day standard / faster for privileged)
- [ ] Screenshots filed in evidence folder

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Work item to wrong person | Manager attribute wrong | Fix HR managerId; Refresh |
| Stuck Pending | Approver inactive / no escalation | Reassign; add escalation |
| Dual not enforced | Scheme still manager-only | Update approval scheme / workflow |
| Reject still provisioned | Bug or manual grant | Revoke; file defect; check plan |
| Cannot act as manager | Auth limits | Use work item admin / test manager login |

---

## Training binder evidence

1. Approved CRM work item history
2. Rejected request with comment
3. AWS dual-approval design text
4. Escalation SLA table
5. IdentityRequest before/after states

**Control owner:** IAM Governance; app owners own privileged second votes  
**Examiner question:** “Who approved, when, and what happens on reject?”

---

## Knowledge check

1. Who approves CRM in the Meridian standard?
2. Who approves AWS_ADMIN?
3. What does reject guarantee?
4. What is the standard CRM escalation timer?
5. Why might parallel dual approval still be acceptable?
6. Why is dual approval not a substitute for split wire roles?

### Answers

1. The requestor’s manager only (for low-risk CRM).
2. Manager plus Technology owner `christopher.hayes` (dual).
3. No provisioning from that request; decision and comment retained.
4. Three business days to manager’s manager (lab standard).
5. If both approvals are still required before provision, parallel reduces latency without removing control.
6. Approvals affirm a request; role design prevents initiate+approve from being one entitlement pack—SoD starts in the catalog (Lessons 25/40).

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “approval schemes” and “work item escalation” for LCM configuration.
- [SailPoint Community](https://community.sailpoint.com/) — search “dual approval” / “parallel approval” for serial vs parallel trade-offs.
- [NIST SP 800-53 AC-5](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — separation of duties; dual approval as a compensating control pattern.
- [NIST SP 800-53 AC-2](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — account management; authorization of access requests.
- [FFIEC IT Handbook — Information Security](https://ithandbook.ffiec.gov/) — dual control and approval expectations for privileged and payment access.

---

## Stretch lab

1. Add Risk approval for any entitlement appearing in `sod-matrix.csv`.
2. Configure delegated approvers for `rachel.evans` OOO scenario.
3. Require MFA / electronic signature comment templates for privileged approvals.

---

## Summary

- You completed manager approval for CRM and designed dual control for AWS.
- You proved reject blocks provisioning and documented escalation SLAs.
- You captured work-item history as the core approval evidence artifact.

---

**Previous:** [Lesson 35 — Access Request Catalog](35-access-request-catalog.md)  
**Next:** [Lesson 37 — Emergency / Break-Glass Access](37-break-glass-access.md)
