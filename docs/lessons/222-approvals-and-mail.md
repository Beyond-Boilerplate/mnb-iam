# Lesson 222 — Approvals With Mailpit Proof

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~80 minutes  
**Prereq:** Lessons 203, 221  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 36 / 38b

> **Why:** An approval nobody was emailed about isn’t governance — it’s a database row. And an approval routed to the requester themselves isn’t governance either.

## What this is

Lesson 221 left a pending Wire Initiator request from `priya.wire`. Now you make approvals **real**:

1. Fix the shipped approval workflow so Manager Approval goes to Priya’s **manager**, not to Priya  
2. Point **Lifecycle Manager** at that workflow (Request Access does **not** pick it automatically)  
3. Resubmit — old Lesson 221 cases still ran stock **`LCM Provisioning`**  
4. Approve as manager, then as app owner  
5. Watch **Mailpit** for notifications  
6. Confirm `WIRE_INIT` actually lands on the live app  

**`MNB-Workflow-Access-Approval`** is an `LCMProvisioning` workflow with two serial **Approval** steps (Manager → Owner), then `provisionProject`.

The Manager step ships with:

```text
owner="ref:launcher"
```

**`launcher`** = the person who submitted the request. So Priya currently approves her own request. The workflow Description even calls this an “approval skeleton… customize.” Fixing that owner reference is this lesson.

Editing the workflow alone is not enough. By default, Request Access still launches stock **`LCM Provisioning`** (`workflowLCMAccessRequest` / `workflowLCMRolesRequest`). Until you remapped those rows, Priya’s Wire request never entered `MNB-Workflow-Access-Approval` — which is why Sanjay never saw a Manager Approval work item.

Classic 36/38b taught approval chains and before/after rules; here you prove the chain against live Mailpit + a live Wire entitlement.

## Know these

```text
DEFAULT (broken for this lesson):
  Request Access → LCM Provisioning (approvalScheme often "owner" only)
    → Owner Approval for spadmin
    → Sanjay never gets a work item

THIS LESSON:
  Fix Manager owner on MNB-Workflow-Access-Approval
  → Gear → Lifecycle Manager → Business Processes
       Access Request / Roles Request → MNB-Workflow-Access-Approval
  → Resubmit Wire Initiator as priya.wire
  → Manager Approval (load identityName → getManager() → sanjay.kapoor) → Mailpit
  → Owner Approval (spadmin) → Mailpit / or note spadmin has no email
  → provisionProject → WIRE_INIT on live target
  → IdentityRequest trail shows both approvals + provision status
```

| Term | Plain English | Meridian example |
| --- | --- | --- |
| **Approval step** | Workflow pause until someone decides | Manager Approval, Owner Approval |
| **`owner` on Approval** | Who gets the work item | Must be manager — not `ref:launcher` |
| **`ref:launcher`** | The requester | Priya approving Priya = broken |
| **LCM Business Processes map** | Which workflow Request Access launches | Must name `MNB-Workflow-Access-Approval`, not stock `LCM Provisioning` |
| **`workflowLCMRolesRequest`** | SystemConfiguration key for role requests | Wire Initiator Bundle uses this path |
| **Serial approval** | Step 2 waits for step 1 | Manager then Owner |
| **`provisionProject`** | Execute the access plan after approvals | Creates/updates Wire account entitlement |
| **Mailpit** | Local catch-all mailbox | [http://localhost:8025](http://localhost:8025) |

- **Wrong way:** Leaving `ref:launcher` because “it technically has an approval step” — self-approval is not governance.
- **Wrong way:** Fixing the custom workflow but leaving Lifecycle Manager on `LCM Provisioning` — Sanjay never sees the request.
- **Wrong way:** Approving as `spadmin` only and calling the manager step done — no manager accountability trail.
- **Wrong way:** Stopping when the work item closes — entitlement must provision on the live target.

## Intent

- Fix Manager Approval so it loads the cube by `identityName` and routes to `getManager()`.
- Remap Lifecycle Manager Access Request / Roles Request to `MNB-Workflow-Access-Approval`.
- Approve Priya’s **new** request as Sanjay (manager), then as owner (`spadmin`), watching Mailpit.
- Confirm `WIRE_INIT` provisions and the IdentityRequest trail is complete.

## Before you start

- [ ] Lesson 221’s pending `IdentityRequest` id for `priya.wire` in hand (or plan to resubmit)
- [ ] Mailpit UI: [http://localhost:8025](http://localhost:8025)
- [ ] Lesson 203 SMTP pointing at Mailpit (`mailpit:1025`)
- [ ] Sanjay Kapoor (`MNB00006` / `sanjay.kapoor`) is Priya’s manager on the cube
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/222
```

## Do this

### Task 1 — Find the broken Manager Approval owner

1. Open `config/Workflow/MNB-Workflow-Access-Approval.xml` **or** IIQ **Setup → Business Processes → MNB-Workflow-Access-Approval**
2. Locate step **Manager Approval**
3. Confirm `owner="ref:launcher"`

- **Why:** you must see the defect before changing it — so you can explain the before/after to an auditor.
- **Expect:** owner attribute located and confirmed broken.

### Task 2 — Fix Manager Approval to resolve the real manager

Change Manager Approval so the owner is Priya’s manager.

In **Setup → Business Processes → MNB-Workflow-Access-Approval** → step **Manager Approval** → Approval details:

1. **Owner** → select **Script**
2. Paste this exact script (do **not** use bare `identity.getManager()` — `identity` is **not** in scope on this Approval step):

```java
import sailpoint.object.Identity;
Identity id = context.getObjectByName(Identity.class, identityName);
return (id != null) ? id.getManager() : null;
```

Leave **Owner Approval** as `owner="spadmin"` for now — it stands in for the Wire app owner.

**Save** the approval, then **Save** the business process. If you edit XML on disk instead, **Debug → Import** `config/Workflow/MNB-Workflow-Access-Approval.xml`.

- **Why:** Manager Approval only means something if a real manager decides.
- **Expect:** corrected owner logic saved on `MNB-Workflow-Access-Approval` before Task 3.

> **Watch out:** Error `getManager() on undefined variable … identity` means you used `identity` instead of loading from `identityName`. Against `priya.wire` the manager must resolve to `sanjay.kapoor`, not null.

### Task 3 — Point Request Access at `MNB-Workflow-Access-Approval`

Request Access does **not** read a workflow name off the Wire Bundle. It uses the global Lifecycle Manager map. Until you change that map, every Wire request still runs stock **`LCM Provisioning`**.

1. As `spadmin`, open the **gear** → **Lifecycle Manager**
2. Open the **Business Processes** tab
3. Change these rows from **`LCM Provisioning`** → **`MNB-Workflow-Access-Approval`**:

| Lifecycle Manager row | SystemConfiguration key | Why |
| --- | --- | --- |
| **Access Request** | `workflowLCMAccessRequest` | General access-request entry |
| **Roles Request** | `workflowLCMRolesRequest` | `MNB-Bundle-Wire-Initiator` is a role request |

4. **Save**
5. Re-open the tab and confirm both rows still show `MNB-Workflow-Access-Approval`

- **Why:** fixing Manager Approval on a workflow that never launches does nothing for Sanjay’s inbox.
- **Expect:** Lifecycle Manager shows your custom process for Access Request and Roles Request.

> **Watch out:** There is no “attach workflow to Bundle” click for this lab path. If you only edited the role and left Lifecycle Manager alone, you are still on stock LCM.

**If the Lifecycle Manager UI won’t edit:** Debug → **Configuration** → `SystemConfiguration` → set the same two keys to `MNB-Workflow-Access-Approval` → save.

**Fallback (OOTB LCM only):** If the custom skeleton fails on submit, put both rows back to `LCM Provisioning`, then **Setup → Business Processes → LCM Provisioning → Process Variables** and set `approvalScheme=manager,owner` and `approvalMode=serial`. That is dual approval without the custom workflow — document which path you used.

### Task 4 — Resubmit (old requests will not re-route)

Lesson 221’s pending item already started under stock **`LCM Provisioning`**. Changing the map does **not** rewrite open work items.

How to tell which process ran:

| Work item description | Process that ran |
| --- | --- |
| `Owner Approval - Account Changes for User: Priya Mehta` | Stock `LCM Provisioning` |
| `Manager approval for priya.wire` | `MNB-Workflow-Access-Approval` |

1. Cancel / complete the old Owner-only item harmlessly as needed  
2. As `priya.wire` / `LabUser1!`: **Request Access** → Wire Initiator → justification → submit  
3. Note the **new** `IdentityRequest` id under evidence  

- **Why:** only a **new** submit uses the Lifecycle Manager mapping from Task 3.
- **Expect:** a Manager Approval work item for `sanjay.kapoor`, description like `Manager approval for priya.wire`.

### Task 5 — Open Manager Approval as Sanjay

Log in as `sanjay.kapoor` / `LabUser1!`  
**Or** as `spadmin`: **Manage Work Items** filtered to Sanjay’s queue.

Find the Manager Approval item for Priya’s Wire request.

- **Expect:** work item addressed to the **real manager**, not Priya.

Screenshot under evidence.

### Task 6 — Check Mailpit before approving

Open [http://localhost:8025](http://localhost:8025). Search for Sanjay / approval / Wire.

- **Why:** assignment mail proves notification path, separate from “work item exists.”
- **Expect:** message present — **or** flag a gap (assignment email needs an `EmailTemplate`; missing template ≠ broken SMTP from Lesson 203).

### Task 7 — Approve Manager step

Approve with a comment, e.g.:

```text
Approved — Q3 wire desk rotation confirmed
```

- **Expect:** request transitions to **Owner Approval**; new work item for `spadmin`.

### Task 8 — Approve Owner step as spadmin

As `spadmin`, approve Owner Approval with a short comment.

- **Expect:** workflow enters `provisionProject`.

### Task 9 — Prove live entitlement + Mailpit completion

1. Check Mailpit again for completion / provisioning notification  
2. Re-aggregate `MNB-WirePortal` and/or `MNB-CoreBanking`  
3. Confirm `priya.wire` has `WIRE_INIT` correlated to **this** request  

Optional SQL if Core Banking is the target:

```bash
psql -h localhost -p 5435 -U mnb -d mnb_apps \
  -c "select username, entitlement, status from mnb_app_accounts where username='priya.wire';"
```

- **Expect:** entitlement live, tied to this IdentityRequest — not leftover seed data.

### Task 10 — Read the IdentityRequest trail

Open the IdentityRequest detail. Confirm you can see in one place:

- Requester  
- Manager approval timestamp + comment  
- Owner approval timestamp + comment  
- Provisioning status  

- **Why:** this trail — not the entitlement alone — answers “why was access granted?” Lesson 231 will export the same story as a report row; learn to read it here first.
- **Expect:** full trail visible; screenshot under evidence.

Write one evidence line you’ll reuse in 231:

```text
IdentityRequest id: ________  →  WIRE_INIT for priya.wire  →  manager+owner approved
```

## If it fails

| Symptom | Fix |
| --- | --- |
| Sanjay has no work item; only Owner Approval for `spadmin` | Lifecycle Manager still on `LCM Provisioning` — redo Task 3; then **resubmit** (Task 4) |
| Work item text is `Owner Approval - Account Changes…` | Stock LCM ran — custom workflow was never launched |
| `getManager() on undefined variable … identity` | `identity` is not in scope — use the Task 2 script that loads via `identityName` |
| Manager Approval has no valid owner after fix | Script returns null — confirm `priya.wire` manager is `sanjay.kapoor` (Lesson 214) |
| Request auto-approves with zero work items | Mapping didn’t save, or scheme is `none` — re-check Task 3 / Process Variables |
| Mailpit empty + Owner WI for `spadmin` | IIQ logs `Unable to notify, no email address for: spadmin` — expected for admin; Sanjay’s assignment mail is the Mailpit proof |
| Mailpit empty after Sanjay WI exists | Confirm Lesson 203 SMTP (`defaultEmailHost=mailpit:1025`); template `Work Item Assignment` exists |
| Both approvals done, no entitlement | `provisionProject` stuck/errored — check Task Results / workflow case history |
| Can’t log in as Sanjay | Act from spadmin Manage Work Items filtered by owner |
| Still self-approving | Workflow edit didn’t import/save; re-open and confirm `ref:launcher` is gone |
| Custom workflow submit errors / stalls | Fall back to Task 3 OOTB path (`approvalScheme=manager,owner`) and document it |

## You are done when

- [ ] Lifecycle Manager Access Request + Roles Request point at `MNB-Workflow-Access-Approval` (or documented OOTB `manager,owner` fallback)
- [ ] Manager Approval routes to Sanjay (not Priya)
- [ ] Both approvals have timestamps/comments
- [ ] At least one Mailpit-visible notification (Sanjay assignment — not only an `spadmin` attempt)
- [ ] `WIRE_INIT` confirmed on the live app for this IdentityRequest

## Control note

- **Control:** Segregated approval routing (manager + owner) for access requests
- **Owner:** IAM Ops (workflow) + line manager + app owner (decisions)
- **SLA (lab):** Same session; production two-step approvals often target 24–72 hours
- **Evidence:** `~/iiq-lab-evidence/sandbox/222/` — fixed workflow, both approvals, Mailpit screenshots, provisioning proof

## Quick check

1. What did `owner="ref:launcher"` mean before the fix? → The requester approved their own request  
2. Where do you tell Request Access to run `MNB-Workflow-Access-Approval` instead of `LCM Provisioning`? → Gear → Lifecycle Manager → Business Processes (Access Request + Roles Request)  
3. Why doesn’t editing the Wire Bundle alone change which workflow runs? → Request Access uses the global LCM map, not a per-role workflow field  
4. What two Mailpit moments should this lesson produce? → Manager assignment mail and completion/provisioning mail (or named gaps)  
5. What proves approval isn’t just paperwork? → The entitlement provisioning on the live target after both approvals  
6. Who stands in for Wire app owner here? → `spadmin` on the Owner Approval step  

## Feedback

Could you explain why fixing `ref:launcher` alone still left Sanjay’s inbox empty? If Mailpit stayed empty, note whether the open work item was for Sanjay or only for `spadmin` — those are different failure classes.

## Navigate

- Previous: [Lesson 221](221-access-catalog-live.md)
- Next: [Lesson 223](223-break-glass-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md) · Theory: [256 Connector Registry](256-connector-registry-theory.md) (Wire/Core Banking feature strings behind the request)
