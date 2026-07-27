# Lesson 38 — IdentityRequest Tracking & Auditing

**Level:** Intermediate  
**Track:** Requests  
**Time:** 45–60 minutes  
**Prereq:** Lessons 35–37 (at least one completed CRM, reject, or break-glass request)  

**Lab data:**
- Prior IdentityRequest ids from your notebook (CRM approve, `REJECT-TEST-L36`, `MNB-INC-####` break-glass)
- Optional: Audit configuration in IIQ (audit search / audit config)
- Evidence output: `~/iiq-lab-data/evidence/identityrequest-L38/`

---

## Learning objectives

You will be able to:

- Locate a completed or in-flight IdentityRequest by id, requester, or target identity
- Trace approval decisions (who, when, approve/reject) from work item / request history
- Determine provisioning status (executed, pending, failed, not applicable in file lab)
- Search audit events related to access requests when audit actions are enabled
- Assemble an **evidence pack** suitable for Internal Audit / examiners
- Explain which objects prove “who approved what when”

---

## Why this matters

**Business.** Disputes and fraud investigations need a single narrative: request → approval → provision → revoke. When someone asks whether `CRM` for a returning RM was approved—or whether `PRIV_BREAK` for `MNB-INC-1042` was Security-approved and removed—you need artifacts, not memory.

**Control / audit.** “We think the manager approved” fails exams. IdentityRequest + work items + provisioning transactions + audit logs are the answer. Control owner: IAM Ops; Audit may sample monthly. Examiner question: *Produce the evidence pack for request X end-to-end.*

---

## Concepts

### Evidence spine

```
IdentityRequest (header: who/what/when/state)
        │
        ├── Work items / approval history (decisions)
        ├── Comments / justifications / ticket ids
        ├── Provisioning plan / Project / Integration requests
        └── Audit events (if enabled)
```

### Pack contents (Meridian minimum)

| Artifact | Proves |
| --- | --- |
| IdentityRequest summary | What was asked for whom |
| Approval history | Who decided, timestamps |
| Reject/approve comments | Intent / ticket linkage |
| Provisioning status | Whether access changed |
| Identity entitlements before/after | Outcome on cube |
| Audit search export (optional) | Independent log trail |

### Three stories this pack should cover

| Story | Source lesson | What must appear |
| --- | --- | --- |
| Low-risk CRM approve | 35–36 | Manager approve + advanced state |
| Reject path | 36 | Reject comment; no provision |
| Break-glass | 37 | `MNB-INC-####`, Security approve, revoke evidence |

### The wrong way

Screenshots of the catalog alone, or “approver said OK in Slack.” Examiners want the IdentityRequest object lineage. Slack is not a control.

---

## How it works

Every LCM ask creates (or updates) an IdentityRequest. Approvals attach as work-item history; provisioning attaches as plans/transactions; AuditConfig may emit parallel events.

```
LCM submit
   └──► IdentityRequest (id, requester, target, items, state)
              │
              ├── Approval work items ──► decisions + comments
              ├── Provisioning engine ──► plan / Project status
              └── AuditConfig actions ──► searchable audit events
```

| Status class | Meaning | Lab honesty |
| --- | --- | --- |
| Finished / committed | Change applied | Ideal |
| Pending | Waiting connector / manual | Common in file lab |
| Failed | Error—needs Lesson 47 | Track owner |
| None / N/A | Rejected or stub lab | Still valid evidence |

**IIQ terms:** *IdentityRequest* is the LCM request object. *Provisioning plan* is the technical change set. *AuditConfig* controls which actions are logged—if off, turn on relevant actions in lab thoughtfully.

---

## Before you start

- [ ] At least one request from Lessons 35–37 exists (CRM approve, reject test, or break-glass)
- [ ] Admin rights to search IdentityRequests and work items
- [ ] Create evidence folder `~/iiq-lab-data/evidence/identityrequest-L38/`
- [ ] Note: file-mode labs may show provisioning as stubbed/pending—document honestly

---

## Lab procedure

### Task 1 — Locate the request

You cannot pack what you cannot find. Start with id and state.

1. Open Access Request search / **Identity Requests** (or Debug → IdentityRequest list).
2. Filter by target identity or date.
3. Open one CRM request and one privileged/reject example if available.
4. Record: request id, created date, requester, target, state, items.

**Expected result:** Notebook table with ≥1 IdentityRequest fully identified (prefer ≥2 story types).

**If it fails:** Use Debug to list recent IdentityRequest objects; copy name/id.

### Task 2 — Trace approvals

This is the “who approved what when” answer.

1. On the IdentityRequest, open approval / workflow history (or linked work items).
2. List each approver, decision (`Approved`/`Rejected`), timestamp, comments.
3. For break-glass, confirm Security approver (`helen.ross`) and `MNB-INC-` comment still visible.
4. For reject test, confirm reject comment from Lesson 36.

**Expected result:** Approval chronology you could read aloud on an exam call.

**If it fails:** Open Work Item archive/search by related identity; screenshot each decision.

### Task 3 — Provisioning status

Access on the cube must match the request story—or you must explain the gap.

1. Find provisioning section / plan / “Expand” details on the request (labels vary).
2. Classify status:

| Status | Meaning | Your note |
| --- | --- | --- |
| Finished / committed | Change applied | |
| Pending | Waiting connector / manual | |
| Failed | Error—needs Lesson 47 | |
| None / N/A | Rejected or stub lab | |

3. Open the target identity entitlements; compare to request intent.

**Expected result:** Written provisioning verdict aligned with cube reality.

**If it fails:** If no connector, state “lab delimited—manual verify via re-aggregation / no auto provision.”

### Task 4 — Audit search (if enabled)

Independent logs corroborate the IdentityRequest—when configured.

1. Open **Intelligence / Audit** search (or equivalent Audit search UI).
2. Filter time window around your request; look for access request / approval / provisioning events.
3. If empty, open Audit Configuration and note which actions are disabled—enable access request related actions **in lab only**, re-test once.
4. Export or screenshot matching events.

**Expected result:** Either audit hits attached to the pack, or a documented gap: “Audit actions disabled—enabled X for lab.”

**If it fails:** Do not enable noisy global audit in shared prod-like envs; lab-only changes; revert if required.

### Task 5 — Assemble the evidence pack

The pack is the deliverable. Another engineer should review it without IIQ access.

1. Create `PACK-README.txt`:

```text
Meridian Evidence Pack — IdentityRequest
Request id:
Target:
Business purpose:
Approvals:
Provisioning:
Cube before/after:
Audit refs:
Assembler:
Date:
```

2. Add screenshots/PDFs/exports for each section.
3. Include at least one reject or break-glass story if available (dual-control / Security narrative).
4. Zip or keep folder ready for training records.

**Expected result:** Complete pack another engineer can review without IIQ access.

### Task 6 — Examiner rehearsal

Read the pack aloud against this question: *“Produce the evidence pack for request X end-to-end.”* Time yourself; note missing artifacts.

**Expected result:** Gap list (if any) with owners; pack marked ready or “needs Task N redo.”

---

## Acceptance criteria

- [ ] IdentityRequest located with id and state
- [ ] Approval chronology documented
- [ ] Provisioning status classified and checked against cube
- [ ] Audit search attempted; gaps noted if empty
- [ ] Evidence pack folder assembled with README

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Cannot find request | Wrong date filter / purged | Broaden search; Debug list |
| No approval history | Workflow bypassed | Check LCM process; use another request |
| Provisioning forever pending | No connector | Document stub; manual outcome |
| Audit empty | Actions off | Enable relevant audit actions in lab |
| Pack incomplete | Missing screenshots | Re-open request; capture now |

---

## Training binder evidence

1. IdentityRequest header screenshot
2. Approval history screenshot
3. Provisioning status notes
4. Identity entitlements after outcome
5. Audit export or gap statement
6. `PACK-README.txt`

**Control owner:** IAM Ops; Audit may sample monthly  
**Examiner question:** “Produce the evidence pack for request X end-to-end.”

---

## Knowledge check

1. Which object is the spine of access-request audit at Meridian?
2. What proves approval besides someone’s memory?
3. If provisioning is pending, is the control failed?
4. What belongs in a minimum evidence pack?
5. Why enable audit actions thoughtfully?
6. What three request stories should a complete training pack preferably include?

### Answers

1. The IdentityRequest (plus linked work items).
2. Work item / approval history with identity, decision, timestamps, comments.
3. Not necessarily—pending may be normal without connectors; it is a finding if SLA breached or stuck without owner.
4. Request summary, approvals, comments/tickets, provisioning status, before/after access, optional audit hits.
5. Over-broad audit creates noise and performance cost; under-broad leaves exam gaps—enable what examiners sample.
6. CRM approve (manager path), reject (no provision), and break-glass (Security + ticket + revoke).

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “IdentityRequest” and “AuditConfig” for request objects and auditable actions.
- [SailPoint Community](https://community.sailpoint.com/) — search “access request audit” / “work item history” for evidence-pack patterns.
- [NIST SP 800-53 AU-2](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — audit events; what to log for access administration.
- [NIST SP 800-53 AU-6](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — audit review; how evidence packs support investigations.
- [FFIEC IT Handbook — Information Security](https://ithandbook.ffiec.gov/) — audit and accountability expectations for access administration evidence.

---

## Stretch lab

1. Enable additional audit actions and re-run a small CRM request to prove new events.
2. Build a weekly report of open IdentityRequests older than 5 days.
3. Map pack fields to a formal Internal Audit PBC (Prepared By Client) list.

---

## Summary

- You traced IdentityRequests from submission through approvals and provisioning status.
- You attempted audit-log corroboration and documented gaps honestly.
- You assembled a reusable examiner-ready evidence pack.

---

**Previous:** [Lesson 37 — Emergency / Break-Glass Access](37-break-glass-access.md)  
**Next:** [Lesson 39 — SoD Fundamentals for Banking](39-sod-fundamentals.md)
