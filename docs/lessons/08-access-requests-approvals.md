# Lesson 08 — Access Requests & Approvals

**Level:** Intermediate  
**Prereq:** Lessons 06–07; LCM enabled  
**Meridian story:** A relationship manager needs Salesforce CRM. That must be requested, approved by a manager, and tracked—never quietly added in a spreadsheet.

---

## Story

You will make at least one role or entitlement **requestable**, submit an access request as an end user (or via Manage User Access), and complete the approval work item as a manager.

This is the happy path of Lifecycle Manager.

---

## How it works

```text
Requester → Access Request → Workflow → Approver work item → Approved
        → Provisioning plan → Connector (or manual work item) → Access granted
```

In a file-based lab, provisioning may be **manual** (work item to IT) unless you configure a writable target. That is still valuable: you learn the governance path even when the last mile is a ticket.

---

## Lesson goals

- [ ] Mark `MNB-Role-Developer` or entitlement `SalesForce` / `AWS` as requestable
- [ ] Submit a request for a Meridian user
- [ ] Approve/reject as manager
- [ ] Trace the request in the user’s history / access request UI

---

## Tasks

### Task 1 — Make something requestable

1. Open a role **or** entitlement that should not be birthright (`AWS` preferred for drama, `SalesForce` for business realism).  
2. Enable **requestable** / add to requestable roles catalog as your UI allows.  
3. Set owner / approval details if prompted.  
4. Save.

### Task 2 — Choose actors

| Actor | Lab approach |
| --- | --- |
| Requester | Identity with UI login capability, or admin using Manage Access for user |
| Approver | That user’s manager from HR hierarchy |

If managers cannot log in yet, approve as `spadmin` **and** note what production would require (passwords, SSO, workgroup inboxes).

### Task 3 — Submit request

1. Use **Manage User Access** / **Request Access** Quicklink.  
2. Select the target identity.  
3. Add the requestable role/entitlement.  
4. Submit with a business justification: “Needs CRM for commercial client portfolio.”

### Task 4 — Complete work item

1. Open approver inbox / work items.  
2. Open the access request approval.  
3. Approve with a comment.  
4. Confirm request moves forward.

### Task 5 — Observe provisioning outcome

1. Check whether a provisioning plan / pass was created.  
2. If manual work item appears for IT, complete it.  
3. Refresh identity; see if access shows as assigned/detected/pending.

---

## Tips & tricks

- Justifications matter in banking audits—practice writing real ones.  
- If no work item appears: workflow not launched, LCM not active, or approver resolution failed (manager blank).  
- Rejection path is as important as approval—do one reject test.  
- Duplicate requests / sticky entitlements: re-refresh and check request status before re-requesting.

---

## Checkpoint

1. What object does an approver receive?  
2. Why are privileged entitlements requestable instead of birthright?  
3. What still needs to happen after approval for access to appear in a target system?

---

## Stretch

Add a two-stage approval for `AWS`: manager then Cloud Security workgroup. Document the workflow change.

**Next:** [Lesson 09 — SoD policies for banking](09-sod-policies.md)
