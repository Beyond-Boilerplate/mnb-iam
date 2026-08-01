# Lesson 36b — Be the Approver

**Level:** Intermediate  
**Track:** Requests  
**Time:** 45–60 minutes  
**Prereq:** Lesson 36 (approval chains designed); Lesson 35 (catalog + a request submitted); manager hierarchy (21)  
**Lab data:** Work items for managers (`emily.bennett`, `sanjay.kapoor`, `rachel.evans`, `christopher.hayes`)  
**Path:** Core (01–50)

---

## Learning objectives

You will be able to:

- Log in (or proxy) as a **manager approver** and complete Approve / Reject paths
- Read a work item like Emily Bennett or Sanjay Kapoor—not like `spadmin`
- Capture approval history as examiner evidence
- Practice an escalation note when the manager is OOO / on leave
- Explain why Wire dual-control must not collapse into one approver identity

---

## Why this matters

**Business.** Juniors build request catalogs, then wonder why nothing provisions. Often the work item is sitting in a manager inbox unread. Sitting in Emily’s chair teaches the other half of the control.

**Control / audit.** Sampling closed requests means reading **who** clicked Approve and whether Reject blocked provisioning. Spadmin-only demos fail that interview question.

---

## Concepts

### Approver personas at Meridian

| Persona | Approves | Notes |
| --- | --- | --- |
| `emily.bennett` | Retail teller / Nina’s manager | Low-risk CRM / birthright questions |
| `sanjay.kapoor` | Commercial / Sofia’s manager | CRM for RMs; LoA coverage complexity |
| `rachel.evans` | Treasury / wire ownership | Dual-control second vote |
| `christopher.hayes` | Technology / AWS | Privileged second vote |

### Work item literacy

A **work item** is the human decision object in an inbox. States typically include Open → Approved / Rejected / Expired. History must show actor + timestamp.

### Wrong way

Approve everything as `spadmin`, or approve both Wire initiate and Wire approve requests as the same human “to finish the lab.” That destroys the dual-control story (Lessons 14/40).

```
Requester submits (Lesson 35/36)
        │
        ▼
Work item → manager inbox
        │
        ├── Approve → provisioning may proceed
        ├── Reject  → no provision + forensic trail
        └── Escalate → manager’s manager / Security
```

---

## How it works

| Step | Actor | Evidence |
| --- | --- | --- |
| Submit request | Requester / spadmin lab helper | IdentityRequest id |
| Decision | Manager persona | Work item history |
| Outcome | Provisioner | Task Result / plan (Lessons 16b/47) |

---

## Before you start

- [ ] At least one open access request work item exists (Lesson 35/36). If none, submit a low-risk CRM request for `amelia.brooks` or `nina.joiner` as setup.  
- [ ] Know how your lab handles manager login: real passwords for manager cubes, or **Work Item forwarding / admin open**, or Capability to work as… (document which).  
- [ ] Do not use Wire initiate+approve as a single-approver shortcut.

---

## Lab procedure

### Task 1 — Inventory the open inbox

1. As `spadmin`, open Work Items / Approvals (menu labels vary).  
2. Find an open request tied to a Meridian persona.  
3. Note: requester, requested access, current owner/approver, age.

**Expected result:** One open work item identified with owner name.

**If it fails:** Submit a new CRM request for `nina.joiner` or `amelia.brooks` targeting manager `emily.bennett` / `MNB00007`, then refresh the inbox.

### Task 2 — Sit in the approver chair

1. Switch to the approver context your lab supports (login as manager, or open work item via admin “view” that still records the approval actor—document the method).  
2. Read the request as the manager: business need? SoD risk? Contractor?  
3. For a low-risk CRM-style request: **Approve** once.  
4. Capture work item history showing actor + timestamp.

**Expected result:** Approved work item with non-ambiguous history.

**If it fails:** If manager login is unavailable, perform approval as admin but write a gap: “Lab limitation — production would be manager login; actor should be emily.bennett.” Still capture history.

### Task 3 — Reject path (control proof)

1. Submit (or reuse) a request you are willing to reject—e.g. overly broad access for a teller.  
2. As approver, **Reject** with a reason (“least privilege — use job pack / ticket”).  
3. Confirm the IdentityRequest shows rejected / not provisioned.  
4. Binder: reject is a successful control outcome.

**Expected result:** Reject evidence with reason text.

### Task 4 — Escalation drill (paper + optional UI)

Scenario: `sanjay.kapoor` is covering Sofia’s book while she is `exceptions=LOA`, and a CRM request ages past SLA.

1. Write the escalation note:

```text
Day 3: no manager action on request <id>
Escalate to: manager’s manager / Helen Ross (Security) per Lesson 36 tier table
Reason: OOO / LoA coverage
```

2. If your approval scheme supports escalate/forward, exercise it once; otherwise paper is enough.

**Expected result:** Escalation note tied to Lesson 36 SLA table.

### Task 5 — Dual-control reminder (Wire)

1. Write three bullets: why `rachel.evans` (or Treasury owner) must remain in the Wire approve chain; why `priya.wire` must not approve her own initiate pack; why spadmin approval is lab-only.  
2. Do **not** collapse Wire dual-control in this exercise.

**Expected result:** Dual-control reminder in binder.

---

## Acceptance criteria

- [ ] One Approve with history evidence  
- [ ] One Reject with reason + no-provision proof  
- [ ] Escalation note written  
- [ ] Dual-control reminder recorded  

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Empty inbox | No request submitted | Lesson 35 submit |
| Manager cannot log in | Password/capability | Admin path + gap note |
| Request stuck | Wrong owner | Check manager on cube (Lesson 21) |

---

## Training binder evidence

1. Approve history screenshot  
2. Reject history screenshot  
3. Escalation note  
4. Dual-control reminder  

**Control owner:** IAM Governance + line managers  
**Examiner question:** “Show a reject that prevented provisioning.”

---

## Knowledge check

1. Why is spadmin-only approval weak evidence?  
2. What must a reject prove?  
3. Who is a sensible escalation target when Sanjay is overloaded?  
4. Why avoid approving both Wire initiate and approve as one person?

### Answers

1. Production decisions are made by managers/owners; actor identity matters.  
2. Access was not provisioned and a forensic reason exists.  
3. Manager’s manager or Security per tier table (Helen / SOC for privileged).  
4. Breaks payment dual-control and SoD narrative.

---

## Further reading

- Lesson 36 approval tiers; Lesson 38 IdentityRequest auditing  
- [SailPoint docs](https://documentation.sailpoint.com/) — search “work items” and “approvals”

---

## Stretch lab

Approve a dual chain for `AWS_ADMIN` (manager + `christopher.hayes`) end-to-end and attach both history entries.

---

## Summary

- Approvals are lived in manager inboxes, not only designed on paper.  
- Reject is a control success.  
- Dual-control stays sacred for Wire.

**Previous:** [Lesson 36 — Approval Chains & Escalations](36-approval-chains.md)  
**Next:** [Lesson 37 — Emergency / Break-Glass Access](37-break-glass-access.md)
