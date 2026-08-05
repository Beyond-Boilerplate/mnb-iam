# Lesson 217 — Joiner LCM End-to-End

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~75 minutes  
**Prereq:** Lessons 207, 216  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 29–34b

> **Why (1–2 lines):** A joiner only counts as done when the new hire has real accounts and can sign in — not when a cube merely exists. Examiners want timestamps from HR create → birthright provision → first successful login.

## What this is

`MNB-IdentityTrigger-Joiner` (`type="create"`, `WorkflowTriggerHandler`) launches `MNB-Workflow-Joiner` when a new cube is created. With `MNB-Workday` authoritative, that happens when a fresh HCM worker aggregates and refreshes. The workflow logs, then `refreshIdentity` with `promoteAttributes`, `provision`, and `correlateEntitlements` — materializing Lesson 216 birthright onto live targets. Classic 29 taught joiner as control story on CSV; here the acceptance test is Employee Portal SSO. CRM/Wire stay request-only — birthright never auto-grants them.

## Know these

```text
HCM POST worker → Aggregate MNB-Workday → cube create
  → IdentityTrigger Joiner → MNB-Workflow-Joiner
  → refreshIdentity (provision + correlate)
  → birthright entitlements on LDAP/AD/…
  → Keycloak user + Portal SSO  ← done
```

| Day-one | Not day-one (request) |
| --- | --- |
| Cube + birthright (directory/IdP basics) | Wire Initiator, CRM elevated, BreakGlass |

**Wrong way:** Hand-creating a cube in Debug without an HCM row — no authoritative trail, no trigger story, no examiner timeline.

## Intent

- Create a joiner via live HCM and watch the joiner trigger/workflow (or document manual fallback).
- Confirm birthright provisioned on a live target, not cube-only.
- Prove Portal SSO as the real acceptance test.
- Note Mailpit welcome mail presence or honest gap → Lesson 232.

## Before you start

- [ ] Lesson 216 birthright has a real OpenLDAP (or directory) profile
- [ ] HCM mock healthy: `curl -sf http://localhost:8091/health`
- [ ] Mailpit UI: `http://localhost:8025`
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/217`

## Do this

1. Create joiner via API (not a file edit):  
   `./tools/lab/enterprise/hcm-scenario.sh joiner lab.joiner1 Lab Joiner lab.joiner1@meridiannb.com 'Identity & Access'`  
   **Expect:** Script exits 0; worker id returned.

2. Confirm source: `curl -s http://localhost:8091/hcm/v1/workers | python3 -m json.tool | grep -A6 lab.joiner1`.  
   **Expect:** Active worker with email and department populated.

3. Run **Account Aggregation** on `MNB-Workday` (authoritative).  
   **Expect:** New identity cube `lab.joiner1`; this create event is what the Joiner trigger listens for.

4. Watch trigger/workflow: Task Results / process monitor for `MNB-Workflow-Joiner`, or  
   `docker logs mnb-identityiq 2>&1 | grep -i "MNB Joiner workflow"`.  
   **Expect:** Log line naming `lab.joiner1`, or a clear note that you’ll use manual launch (step 5).

5. If trigger didn’t fire, launch `MNB-Workflow-Joiner` with `identityName=lab.joiner1` (Workflow Launcher).  
   **Why:** Complete the LCM plan even if automatic trigger config needs a refresh-option tweak.  
   **Expect:** Workflow completes; treat missing auto-fire as a finding, not a blocker.

6. Confirm `refreshIdentity` effects: Roles tab shows `MNB-Bundle-Birthright-Employee`; Application Accounts shows at least `MNB-OpenLDAP` if birthright maps there.  
   **Expect:** Role + live link — not birthright metadata alone.

7. Re-aggregate provisioned targets (`MNB-OpenLDAP`, Samba if used) so links show current attributes.  
   **Expect:** Correlated account with group membership from birthright.

8. Ensure Keycloak login: Admin `http://localhost:8085/admin/` realm `meridian` — user `lab.joiner1`, password `LabUser1!`, attribute `employeeId` = HCM worker id, groups `mnb-employees` + `portal-users`.  
   **Expect:** User enabled; attributes saved after refresh if UI requires it.

9. SSO into Employee Portal `http://localhost:8092/` as `lab.joiner1` / `LabUser1!`.  
   **Expect:** Successful login — this is the acceptance test a cube alone can’t prove.

10. Check Mailpit for welcome/notification mail.  
    **Expect:** Message present, **or** honest note “no email step in MNB-Workflow-Joiner today” for Lesson 232.

## If it fails

- **No cube after agg** — `authoritative=true` on Workday; Identity Refresh create-identities after agg (Lesson 207).
- **No trigger, no logs** — refresh may need identity-trigger processing; use step 5 fallback.
- **Birthright never provisions** — Lesson 216 profile missing.
- **Keycloak login fails** — `employeeId` not persisted; user disabled.
- **Portal up but no gated content** — missing `portal-users` group.

## You are done when

`lab.joiner1` is cube-sourced from live HCM POST, holds provisioned birthright on at least one live target, and SSO into Employee Portal succeeds.

## Control note

- **Control:** Joiner LCM (HR → identity → birthright → usable access).  
- **Owners:** HR Ops (source) + IAM Ops (trigger/workflow).  
- **SLA (lab):** Same session; production often ≤1 hour to identity, same-day birthright.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/217/` — HCM curl snippet, workflow/Task Result, Portal login proof (no passwords).

## Quick check

1. What must never be birthright on day one? → Wire / CRM elevated / BreakGlass.  
2. What event fires `MNB-IdentityTrigger-Joiner`? → New identity cube create (auth HCM path).  
3. Why is Portal SSO the done criteria? → Proves IdP + groups, not only IIQ metadata.

## Navigate

- Previous: Lesson 216  
- Next: Lesson 218  
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
