# Lesson 222 — Approvals With Mailpit Proof

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~65 minutes  
**Prereq:** Lessons 203, 221  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 36 / 38b

> **Why (1–2 lines):** An approval nobody was emailed about isn't governance — it's a database row. And an approval routed to the requester themselves isn't governance either.

## What this is

`MNB-Workflow-Access-Approval` is an `LCMProvisioning` Workflow with two serial `Approval` steps — Manager, then Owner — followed by `provisionProject`. Its Manager Approval step ships with `owner="ref:launcher"`, a **placeholder** the Workflow's own `<Description>` calls an "approval skeleton... customize." That means the requester currently approves their own request. Fixing that owner reference — mirroring classic 38b's before/after rule pattern, but against the live Mailpit path — is this lesson.

## Know these

```text
Submit request → Manager Approval (owner="ref:launcher" — BROKEN, self-approves)
  → fix: owner rule resolves identity.getManager()
  → Manager Approval (real) → Mailpit mail → Owner Approval (spadmin) → Mailpit mail
  → provisionProject → entitlement lands on live target
```

**Wrong way:** Leaving `ref:launcher` in place "because it technically has an approval step" — self-approval is not governance regardless of workflow shape.

## Intent

- Fix the workflow skeleton so Manager Approval routes to the requester's real manager.
- Attach the corrected workflow to `MNB-Bundle-Wire-Initiator` so Lesson 221's pending request routes through it.
- Approve Priya's request as her manager, then as the Wire app owner, watching Mailpit at each step.
- Confirm the entitlement actually provisions after the second approval.

## Before you start

- [ ] Lesson 221's pending `IdentityRequest` id for `priya.wire` in hand
- [ ] Mailpit UI: `http://localhost:8025`
- [ ] Sanjay Kapoor (`MNB00006`) exists as Priya's manager in the identity master
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/222`

## Do this

1. Open `MNB-Workflow-Access-Approval`; find "Manager Approval"'s `owner="ref:launcher"`.  
   **Why:** This currently makes the requester their own approver — defeats the step's purpose.  
   **Expect:** Owner attribute located and confirmed broken.

2. Change it to an owner Rule resolving `identity.getManager()` off the requesting identity. Leave "Owner Approval"'s hardcoded `owner="spadmin"` as-is (stands in for the Wire app owner). Save; re-import via SSD if your build requires it.  
   **Expect:** Corrected owner logic active before you submit anything new.

3. Attach this workflow as the approval process for `MNB-Bundle-Wire-Initiator` (role's provisioning/approval configuration or LCM approval-workflow mapping).  
   **Expect:** A wire-initiator request now routes Manager → Owner instead of auto-approving.

4. If Priya's Lesson 221 request predates this fix, cancel and resubmit as `priya.wire`: **Request Access** → wire initiate → justification → submit. Note the new `IdentityRequest` id.  
   **Expect:** Fresh request routes through the corrected workflow.

5. Log in as `sanjay.kapoor` (or use spadmin's **Manage Work Items** scoped to his queue) and find the pending Manager Approval item.  
   **Expect:** Work item addressed to the real manager, not Priya.

6. Before approving, check Mailpit for the approval-assignment notification.  
   **Expect:** Message present, or a flagged gap (approval-assignment email is a separate `EmailTemplate` config from the approval step itself).

7. Approve Manager Approval with a comment.  
   **Expect:** Request transitions to Owner Approval; new work item appears for `spadmin`.

8. As `spadmin`, approve Owner Approval too.  
   **Expect:** Workflow transitions into `provisionProject`.

9. Check Mailpit again for a completion notification, then re-aggregate `MNB-WirePortal`/`MNB-CoreBanking` and confirm `priya.wire`'s `WIRE_INIT` is present and correlated to this specific request.  
   **Expect:** Entitlement live, tied to this `IdentityRequest`, not leftover seed data.

10. Open the `IdentityRequest` detail and confirm the full trail — requester, manager approval timestamp/comment, owner approval timestamp/comment, provisioning status — is visible in one place.  
    **Expect:** This trail, not the entitlement alone, is what ops needs when someone later asks why access was granted.

## If it fails

- **Manager Approval has no valid owner after the fix** — test the rule in isolation (Debug Page / rule tester) against `priya.wire`; it must return `sanjay.kapoor`, not null.
- **Request auto-approves with zero work items** — step 3's attachment didn't take; re-check the Bundle's approval-workflow wiring versus a "no approval required" default.
- **Mailpit never shows anything for either step** — confirm Lesson 203's SMTP settings (`mailpit:1025`), then confirm an `EmailTemplate` is actually configured for the work-item-assignment event — routed-with-no-template is a distinct failure from broken SMTP.
- **Approved through both steps but entitlement never provisions** — check `provisionProject` actually ran (Task Results/workflow case history) for a stuck or errored step.
- **Can't log in as `sanjay.kapoor` directly** — use spadmin's **Manage Work Items** filtered by owner; act there if his login isn't set up.

## You are done when

Priya's wire-initiator request has a complete, visible Manager → Owner approval trail with real timestamps, at least one Mailpit-visible notification, and `WIRE_INIT` confirmed provisioned on the live app.

## Control note

- **Control:** Segregated approval routing (manager + owner) for access requests.  
- **Owner:** IAM Ops (workflow) + line manager + app owner (decisions).  
- **SLA (lab):** Same session; production two-step approvals often target 24–72 hours.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/222/` — fixed workflow XML/rule, both approval timestamps, Mailpit screenshots, provisioning proof.

## Quick check

1. What did `owner="ref:launcher"` actually mean before the fix? → The requester approved their own request.  
2. What two Mailpit moments should this lesson produce? → Manager approval-assignment mail and completion/provisioning mail.  
3. What proves approval isn't just paperwork? → The entitlement actually provisioning on the live target after both approvals.

## Navigate

- Previous: Lesson 221  
- Next: Lesson 223  
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
