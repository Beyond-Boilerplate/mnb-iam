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
2. Attach that workflow to the Wire Bundle  
3. Approve as manager, then as app owner  
4. Watch **Mailpit** for notifications  
5. Confirm `WIRE_INIT` actually lands on the live app  

**`MNB-Workflow-Access-Approval`** is an `LCMProvisioning` workflow with two serial **Approval** steps (Manager → Owner), then `provisionProject`.

The Manager step ships with:

```text
owner="ref:launcher"
```

**`launcher`** = the person who submitted the request. So Priya currently approves her own request. The workflow Description even calls this an “approval skeleton… customize.” Fixing that owner reference is this lesson.

Classic 36/38b taught approval chains and before/after rules; here you prove the chain against live Mailpit + a live Wire entitlement.

## Know these

```text
Submit request (Lesson 221)
  → Manager Approval (owner="ref:launcher" — BROKEN, self-approves)
  → FIX: owner resolves identity.getManager() → sanjay.kapoor
  → Manager Approval (real) → Mailpit assignment mail
  → Owner Approval (spadmin stands in for app owner) → Mailpit
  → provisionProject → WIRE_INIT on live target
  → IdentityRequest trail shows both approvals + provision status
```

| Term | Plain English | Meridian example |
| --- | --- | --- |
| **Approval step** | Workflow pause until someone decides | Manager Approval, Owner Approval |
| **`owner` on Approval** | Who gets the work item | Must be manager — not `ref:launcher` |
| **`ref:launcher`** | The requester | Priya approving Priya = broken |
| **Serial approval** | Step 2 waits for step 1 | Manager then Owner |
| **`provisionProject`** | Execute the access plan after approvals | Creates/updates Wire account entitlement |
| **Mailpit** | Local catch-all mailbox | [http://localhost:8025](http://localhost:8025) |

- **Wrong way:** Leaving `ref:launcher` because “it technically has an approval step” — self-approval is not governance.
- **Wrong way:** Approving as `spadmin` only and calling the manager step done — no manager accountability trail.
- **Wrong way:** Stopping when the work item closes — entitlement must provision on the live target.

## Intent

- Fix Manager Approval so it routes to `identity.getManager()`.
- Attach the workflow to `MNB-Bundle-Wire-Initiator`.
- Approve Priya’s request as Sanjay (manager), then as owner (`spadmin`), watching Mailpit.
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

**Practical lab options (pick what your UI supports):**

- **Rule / script owner** that returns `identity.getManager()` (or manager name string) for the requesting identity  
- **Owner script** in the Approval step (same idea)  
- If your build uses a shipped rule name from classic 38b patterns, wire that rule here  

Leave **Owner Approval** as `owner="spadmin"` for now — it stands in for the Wire app owner.

Save; if you edit XML on disk, **Debug → Import** the updated workflow.

- **Why:** Manager Approval only means something if a real manager decides.
- **Expect:** corrected owner logic active before you submit anything new.

> **Watch out:** Test the rule against `priya.wire` — it must return `sanjay.kapoor`, not null. Null owner = stuck or auto-failing work item.

### Task 3 — Attach the workflow to Wire Initiator

Configure `MNB-Bundle-Wire-Initiator` (or LCM approval-workflow mapping) so access requests for that Bundle use `MNB-Workflow-Access-Approval`.

Exact clicks vary by IIQ screen (role approval process / provisioning policy / LCM config). Goal:

```text
Request Wire Initiator → Manager Approval → Owner Approval → Provision
```

- **Expect:** a new wire request routes Manager → Owner instead of auto-approving.

### Task 4 — Resubmit if the old request predates the fix

If Lesson 221’s request was created under the broken workflow:

1. Cancel / complete it harmlessly as needed  
2. As `priya.wire`: **Request Access** → Wire Initiator → justification → submit  
3. Note the **new** `IdentityRequest` id under evidence  

- **Why:** old cases may still carry `ref:launcher` routing.
- **Expect:** fresh request through the corrected workflow.

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

- **Why:** this trail — not the entitlement alone — answers “why was access granted?”
- **Expect:** full trail visible; screenshot under evidence.

## If it fails

| Symptom | Fix |
| --- | --- |
| Manager Approval has no valid owner after fix | Rule returns null — test against `priya.wire`; confirm manager correlation (Lesson 214) |
| Request auto-approves with zero work items | Bundle approval-workflow attachment didn’t take; re-check Task 3 |
| Mailpit empty | Confirm Lesson 203 SMTP (`mailpit:1025`); then check EmailTemplate for work-item assignment |
| Both approvals done, no entitlement | `provisionProject` stuck/errored — check Task Results / workflow case history |
| Can’t log in as Sanjay | Act from spadmin Manage Work Items filtered by owner |
| Still self-approving | Workflow edit didn’t import/save; re-open XML and confirm `ref:launcher` is gone |

## You are done when

- [ ] Manager Approval routes to Sanjay (not Priya)
- [ ] Both approvals have timestamps/comments
- [ ] At least one Mailpit-visible notification
- [ ] `WIRE_INIT` confirmed on the live app for this IdentityRequest

## Control note

- **Control:** Segregated approval routing (manager + owner) for access requests
- **Owner:** IAM Ops (workflow) + line manager + app owner (decisions)
- **SLA (lab):** Same session; production two-step approvals often target 24–72 hours
- **Evidence:** `~/iiq-lab-evidence/sandbox/222/` — fixed workflow, both approvals, Mailpit screenshots, provisioning proof

## Quick check

1. What did `owner="ref:launcher"` mean before the fix? → The requester approved their own request  
2. What two Mailpit moments should this lesson produce? → Manager assignment mail and completion/provisioning mail (or named gaps)  
3. What proves approval isn’t just paperwork? → The entitlement provisioning on the live target after both approvals  
4. Who stands in for Wire app owner here? → `spadmin` on the Owner Approval step  

## Feedback

Could you explain why `ref:launcher` fails a governance review in one sentence? If Mailpit stayed empty after a successful approval, note whether you checked SMTP *and* EmailTemplate — those are two different failure classes.

## Navigate

- Previous: [Lesson 221](221-access-catalog-live.md)
- Next: [Lesson 223](223-break-glass-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
