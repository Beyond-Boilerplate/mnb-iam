# Lesson 217 — Joiner LCM End-to-End

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~75 minutes  
**Prereq:** Lessons 207, 216  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 29–34b

> **Why:** A joiner only counts as done when the new hire has real accounts and can sign in — not when a cube merely exists. Capture timestamps from HR create → birthright → first login, or you can’t debug where the pipeline stalled.

## What this is

`MNB-IdentityTrigger-Joiner` (`type="create"`) launches `MNB-Workflow-Joiner` when a new cube is created. With `MNB-Workday` authoritative, that happens when a fresh HCM worker aggregates and refreshes.

The workflow logs, then `refreshIdentity` with `promoteAttributes`, `provision`, and `correlateEntitlements` — materializing Lesson 216 birthright onto live targets.

Classic 29 taught joiner on CSV; here the acceptance test is Employee Portal SSO. CRM/Wire stay request-only — birthright never auto-grants them.

## Know these

```text
HCM POST worker
  → Aggregate MNB-Workday → cube create
  → IdentityTrigger Joiner → MNB-Workflow-Joiner
  → refreshIdentity (provision + correlate)
  → birthright on LDAP / AD / …
  → Keycloak user + Portal SSO  ← done
```

| Day-one | Not day-one (request) |
| --- | --- |
| Cube + birthright (directory / IdP basics) | Wire Initiator, CRM elevated, BreakGlass |

- **Wrong way:** Hand-creating a cube in Debug without an HCM row — no authoritative trail, no trigger story, no ops timeline when joiners break.

## Intent

- Create a joiner via live HCM and watch the joiner trigger/workflow (or document manual fallback).
- Confirm birthright provisioned on a live target, not cube-only.
- Prove Portal SSO as the real acceptance test.
- Note Mailpit welcome mail presence or honest gap (Lesson 232).

## Before you start

- [ ] Lesson 216 birthright has a real OpenLDAP (or directory) profile
- [ ] HCM mock healthy: `curl -sf http://localhost:8091/health`
- [ ] Mailpit UI: [http://localhost:8025](http://localhost:8025)
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/217
```

## Do this

### Task 1 — Create the joiner in live HCM

```bash
./tools/lab/enterprise/hcm-scenario.sh joiner lab.joiner1 Lab Joiner \
  lab.joiner1@meridiannb.com 'Identity & Access'
```

- **Why:** production joiners arrive as HR API creates — not file edits or Debug cube inserts.
- **Expect:** script exits 0; worker id returned.

### Task 2 — Confirm the worker at the source

```bash
curl -s http://localhost:8091/hcm/v1/workers \
  | python3 -m json.tool | grep -A6 lab.joiner1
```

- **Why:** if the worker isn’t in HCM, aggregation cannot invent them.
- **Expect:** active worker with email and department populated.

### Task 3 — Aggregate Workday (cube create)

Run **Account Aggregation** on `MNB-Workday` (authoritative). Follow with Identity Refresh that creates identities if the cube isn’t created by agg alone (same pattern as Lesson 207).

- **Why:** the cube-create event is what the Joiner trigger listens for.
- **Expect:** new identity cube `lab.joiner1` in the Warehouse.

### Task 4 — Watch the joiner workflow

Check Task Results / process monitor for `MNB-Workflow-Joiner`, or:

```bash
docker logs mnb-identityiq 2>&1 | grep -i "MNB Joiner workflow"
```

- **Why:** automatic trigger is the production path — you need to know whether it fired.
- **Expect:** log line naming `lab.joiner1`, or a clear note that you’ll use manual launch (Task 5).

### Task 5 — Manual fallback if trigger didn’t fire

If the trigger didn’t fire, launch `MNB-Workflow-Joiner` with `identityName=lab.joiner1` (Workflow Launcher).

- **Why:** complete the LCM plan even if automatic trigger config needs a tweak — treat missing auto-fire as a finding, not a blocker.
- **Expect:** workflow completes.

### Task 6 — Confirm birthright on the cube

Open `lab.joiner1`:

- **Roles** tab shows `MNB-Bundle-Birthright-Employee`
- **Application Accounts** shows at least `MNB-OpenLDAP` if birthright maps there

- **Why:** role metadata alone is not day-one access — you need the live link.
- **Expect:** role + live account link.

### Task 7 — Re-aggregate provisioned targets

Re-aggregate `MNB-OpenLDAP` (and Samba if used) so links show current attributes / group membership.

- **Why:** provisioning may have completed; aggregation is how you see the result on the cube.
- **Expect:** correlated account with group membership from birthright.

### Task 8 — Ensure Keycloak login for the joiner

Admin console [http://localhost:8085/admin/](http://localhost:8085/admin/) → realm `meridian`:

1. User `lab.joiner1` exists (create if IIQ isn’t provisioning IdP yet)
2. Password `LabUser1!`
3. Attribute `employeeId` = HCM worker id
4. Groups: `mnb-employees` + `portal-users`

- **Why:** Portal SSO needs an IdP user — directory birthright alone doesn’t create Keycloak credentials in this estate.
- **Expect:** user enabled; attributes saved.

### Task 9 — Portal SSO acceptance test

Open [http://localhost:8092/](http://localhost:8092/) and sign in as `lab.joiner1` / `LabUser1!`.

- **Why:** this is the acceptance test a cube alone can’t prove.
- **Expect:** successful login. Screenshot under `~/iiq-lab-evidence/sandbox/217/` (no passwords).

### Task 10 — Check Mailpit for welcome mail

Open [http://localhost:8025](http://localhost:8025).

- **Why:** welcome mail may or may not be in `MNB-Workflow-Joiner` today — honest gap goes to Lesson 232.
- **Expect:** message present, **or** note “no email step in joiner workflow today.”

## If it fails

| Symptom | Fix |
| --- | --- |
| No cube after agg | Confirm `authoritative=true` on Workday; Identity Refresh create-identities after agg (Lesson 207) |
| No trigger, no logs | Refresh may need identity-trigger processing — use Task 5 fallback |
| Birthright never provisions | Lesson 216 profile missing |
| Keycloak login fails | `employeeId` not persisted, or user disabled |
| Portal up but authorization fails | Missing `portal-users` group |

## You are done when

- [ ] `lab.joiner1` cube sourced from live HCM POST
- [ ] Birthright provisioned on at least one live target
- [ ] Employee Portal SSO succeeds as the joiner

## Control note

- **Control:** Joiner LCM (HR → identity → birthright → usable access)
- **Owners:** HR Ops (source) + IAM Ops (trigger/workflow)
- **SLA (lab):** same session; production often ≤1 hour to identity, same-day birthright
- **Evidence:** `~/iiq-lab-evidence/sandbox/217/` — HCM curl snippet, workflow/Task Result, Portal login proof

## Quick check

1. What must never be birthright on day one? → Wire / CRM elevated / BreakGlass
2. What event fires `MNB-IdentityTrigger-Joiner`? → new identity cube create (auth Workday path)
3. Why is Portal SSO the done criteria? → proves IdP + groups, not only IIQ metadata

## Feedback

Could you hire another disposable joiner and get to Portal login without this lesson open? If the trigger didn’t fire, note whether Task 5 manual launch still completed birthright — auto vs manual is a finding worth keeping.

## Navigate

- Previous: [Lesson 216](216-birthright-roles-live.md)
- Next: [Lesson 218](218-mover-lcm-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
