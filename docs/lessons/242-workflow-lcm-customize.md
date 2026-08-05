# Lesson 242 — Customize an LCM Workflow

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~80 minutes  
**Prereq:** Lesson 217  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 93

> **Why:** Stock LCM rarely matches bank approvals. A joiner process with no human checkpoint means birthright access provisions before anyone with authority confirmed it's right.

## What this is

`MNB-Workflow-Joiner` (`type="IdentityLifecycle"`) currently does the minimum: log the joiner, then call `refreshIdentity` with `provision=true` and `correlateEntitlements=true` — no approval gate, no notification. You add a real manager-approval `<Step>` and an email step, fire a live joiner through the modified process, and watch the new step actually execute in a live workflow case.

## Know these

| Step | Purpose |
| --- | --- |
| `Log Joiner` | Existing first step |
| `Manager Approval` (new) | Gate on `identity.manager` before provisioning |
| `Refresh` | Existing — now happens only after approval completes |
| `Transition` | The rewire that makes the gate real, not a parallel no-op |

**Wrong way:** Adding an approval step without rewiring the `Transition` — the case sails past it and looks correct in the designer while doing nothing live.

## Intent

- Add an Approval step to `MNB-Workflow-Joiner` gating provisioning on manager sign-off.
- Add an email step so the manager gets a real Mailpit notification when approval is pending.
- Fire a live joiner and watch the new steps execute in the workflow case monitor.
- Confirm provisioning is genuinely held until the approval completes.
- Export the modified workflow to `config/Workflow/` for promotion.

## Before you start

- [ ] Lesson 217 joiner flow working end-to-end
- [ ] Mailpit proven (203)
- [ ] Know a manager identity you control (Helen or Christopher's org)
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/242`

## Do this

1. Open **Setup → Business Processes → MNB-Workflow-Joiner** in the Workflow Designer (or edit XML and `importdynamic`).  
   **Expect:** Existing steps `Log Joiner` → `Refresh` visible.
2. Insert a new **Step** named `Manager Approval` between `Log Joiner` and `Refresh`, `action="call:openWorkItem"` or an `Approval` generator, `owner` resolved from `identity.manager`, `workItemType="Approval"`, description `Confirm birthright access for $identityName`.  
   **Expect:** Step saves with owner expression referencing manager.
3. Rewire the `Transition` on `Log Joiner` to point at `Manager Approval` instead of `Refresh`, and set `Manager Approval`'s completion transition to `Refresh`.  
   **Expect:** This is what makes the approval a real gate, not a parallel branch.
4. Add a step sending an email (reuse 241's After-rule pattern or an `<EmailTemplateRef>` action) to the manager announcing the pending approval.  
   **Expect:** Email step wired before or alongside the approval.
5. Save/import. Fire a live joiner: `./tools/lab/enterprise/hcm-scenario.sh joiner lab.wftest WF Test lab.wftest@meridiannb.com` with department correlating to a manager you control, then aggregate `MNB-Workday` and let `MNB-IdentityTrigger-Joiner` fire.  
   **Expect:** Workflow case launches.
6. **Monitor → Processes → Workflows**, find the case for `lab.wftest`.  
   **Expect:** Case is paused at `Manager Approval`, not already past `Refresh` — proof the gate is real.
7. Check Mailpit for the pending-approval notification.  
   **Expect:** Manager's mail present.
8. Log in as the manager, complete the work item (**My Work Items**).  
   **Expect:** Case advances to `Refresh` and completes; joiner's birthright access appears only afterward.
9. Export the modified workflow to `config/Workflow/MNB-Workflow-Joiner.xml`, overwriting the shipped version per `config/README.md`.  
   **Expect:** File re-importable.
10. Save the paused-case screenshot, Mailpit notification, and post-approval provisioning proof under `~/iiq-lab-evidence/sandbox/242/`.

## If it fails

- **Case skips straight past your new step** — the `Transition` rewire didn't take; re-check `Log Joiner`'s `<Transition to="...">` target.
- **Approval has no owner / work item never appears** — manager attribute wasn't set before the trigger fired; run Refresh Identity Cubes first, or fix the HCM manager mapping (214/217).
- **Case stuck permanently at approval** — check the work item was actually created (Monitor → Work Items) and the manager identity has an active capability to see it.
- **Re-import fails with schema errors** — validate against `sailpoint.dtd`; a missing `Transition` or malformed `Approval` block is the usual cause.

## You are done when

A live joiner's workflow case pauses at your new manager-approval step, sends real mail, and only provisions birthright access after the manager completes the work item.

## Control note

- **Control:** Human checkpoint before birthright provisioning (joiner process).  
- **Owner:** IAM Engineering + HR/Manager population.  
- **SLA (lab):** Provisioning held until approval work item completes.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/242/` + `config/Workflow/MNB-Workflow-Joiner.xml`.

## Quick check

1. What makes an approval step a real gate vs decorative? → The `Transition` rewire pointing to it.  
2. What resolves the approval's owner? → `identity.manager`.  
3. Where do you confirm the case is genuinely paused? → Monitor → Processes → Workflows.

## Navigate

- Previous: Lesson 241
- Next: Lesson 243
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
