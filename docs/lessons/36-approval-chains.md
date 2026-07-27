# Lesson 36 — Approval Chains & Escalations

**Level:** Intermediate  
**Track:** Requests  
**Time:** 60–75 minutes  
**Prereq:** Lesson 35 (catalog + submitted request); LCM active (`init-lcm.xml`); manager hierarchy (Lesson 21)  

**Lab data:**
- Low-risk path: `CRM` → manager approval
- Privileged design: `AWS_ADMIN` → manager + Technology owner `christopher.hayes`
- Personas: RM managers e.g. `sanjay.kapoor`; cloud owner `christopher.hayes@meridiannb.com`

---

## Learning objectives

You will be able to:

1. Trace and complete a **manager-only** approval for a low-risk CRM request.
2. Design a **dual approval** chain for AWS/privileged access (manager + app/technology owner).
3. Execute a **reject** path and confirm no provisioning occurs.
4. Define escalation after N days (manager’s manager / Security).
5. Capture work-item history as approval evidence.
6. Explain serial vs parallel approval trade-offs for Meridian risk tiers.

---

## Why this matters

**Business:** Wrong approvers create rubber stamps (everything approved) or deadlock (nothing moves). CRM should be fast; AWS must be slow and dual-controlled.

**Control / audit:** Examiners sample closed requests: *Who approved, when, and what happens on reject?* Control owner: IAM Governance; app owners own privileged second votes. Escalation prevents silent queue death when managers are OOO.

---

## Concepts

### Meridian approval tiers

| Access | Approvers | Mode | Escalation |
| --- | --- | --- | --- |
| `CRM` / medium business | Manager only | Serial (single) | Day 3 → manager’s manager |
| `DWRP` | Manager | Serial | Day 3 → manager’s manager |
| `AWS_ADMIN` | Manager + `christopher.hayes` (Technology) | Serial or parallel dual | Day 2 → Security (`helen.ross` / SOC) |
| `PRIV_BREAK` | Security (Lesson 37) | Strict | Immediate page—not email-only |

### Flow

```text
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
```

**IIQ terms:** *Approval scheme* / LCM business process rules decide who gets work items. *Escalation* reassigns overdue work items. *Reject* must leave a forensic trail on the IdentityRequest.

---

## Before you start

- [ ] LCM Access Request UI works (Lesson 35).
- [ ] At least one pending or new CRM request available.
- [ ] Manager links populated on target identities.
- [ ] You can open **Work Items** inbox as approver (or use `spadmin` forward/act-as if lab limited).
- [ ] Decision recorded for AWS dual-approval design even if full rule config is partial in lab.

---

## Lab procedure

### Task 1 — Complete manager approval for CRM (low-risk)

1. Submit a fresh CRM request if none pending (Lesson 35 steps).
2. Identify the target’s manager (from identity cube).
3. Open the approval **Work Item** (manager inbox or administrator search).
4. Review requested item, justification, and SoD warnings if shown.
5. **Approve** the CRM request.
6. Return to IdentityRequest; confirm state advanced (Approved / Provisioning / Finished—depending on connectors).

**Expected result:** Work item history shows manager identity, approve decision, and timestamp. CRM path required only manager.

**If it fails:** As `spadmin`, use work item administration to open the item; verify manager attribute is set (Lesson 21).

---

### Task 2 — Design dual approval for AWS_ADMIN

1. Write the Meridian rule (binder):

```text
AWS_ADMIN / MNB-Role-CloudAdmin approval
1) Manager affirms business need and SOW/employment status
2) Technology owner christopher.hayes affirms least privilege and expiry
Neither approval alone is sufficient.
```

2. In LCM approval configuration (QuickLink policies, Approval schemes, or workflow—use your lab’s equivalent), configure or document dual approval: manager then owner, or parallel both-required.
3. Prefer **parallel** for speed only if both approvals are mandatory before provision; document choice.

**Expected result:** Design artifact naming both approvers; config screenshot if UI allows, else explicit “configured in prod / stubbed in lab” note with intended object names.

**If it fails:** Do not invent menu clicks—capture the design and map to IIQ approval scheme docs in product PDF.

---

### Task 3 — Test the reject path

1. Submit a disposable request (CRM or DWRP) with justification `REJECT-TEST-L36`.
2. Open the approval work item.
3. **Reject** with comment: `Business case insufficient — training reject path`.
4. Confirm IdentityRequest shows rejected/cancelled end state.
5. Confirm no new entitlement appeared on the identity after Refresh.

**Expected result:** Reject guarantees no provisioning for that request; comment retained for audit.

**If it fails:** If reject unavailable, cancel request as administrator and document equivalent control—but prefer true reject.

---

### Task 4 — Define escalation policy

1. Draft escalation:

| Tier | Overdue after | Escalate to |
| --- | --- | --- |
| CRM / DWRP | 3 business days | Manager’s manager |
| AWS dual | 2 business days | Security / `helen.ross` |
| Break-glass | 1 hour | SOC bridge |

2. If lab supports work item escalation settings, configure 3-day escalate for standard requests.
3. Note OOO coverage: managers must have delegates where possible.

**Expected result:** Escalation table approved for Meridian training binder; optional UI config screenshot.

**If it fails:** Policy-only is acceptable; mark config as follow-up.

---

### Task 5 — Evidence pack for approvals

1. Screenshot work item history for the approved CRM request.
2. Screenshot reject test IdentityRequest.
3. Save AWS dual-approval design page.
4. Store under `~/iiq-lab-data/evidence/approvals-L36/`.

**Expected result:** Examiner can see approve and reject examples without re-running the lab.

---

## Acceptance criteria

- [ ] CRM manager approval completed with history.
- [ ] Dual approval for AWS designed (manager + `christopher.hayes`).
- [ ] Reject path tested; no provision on reject.
- [ ] Escalation table written (3-day standard / faster for privileged).
- [ ] Screenshots filed in evidence folder.

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

1. Approved CRM work item history.
2. Rejected request with comment.
3. AWS dual-approval design text.
4. Escalation SLA table.
5. IdentityRequest before/after states.

---

## Knowledge check

1. Who approves CRM in the Meridian standard?
2. Who approves AWS_ADMIN?
3. What does reject guarantee?
4. What is the standard CRM escalation timer?
5. Why might parallel dual approval still be acceptable?

### Answers

1. The requestor’s manager only (for low-risk CRM).
2. Manager plus Technology owner `christopher.hayes` (dual).
3. No provisioning from that request; decision and comment retained.
4. Three business days to manager’s manager (lab standard).
5. If both approvals are still required before provision, parallel reduces latency without removing control.

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
