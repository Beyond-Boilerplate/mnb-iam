# Lesson 220 — Contractor & LOA Controls Live

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~55 minutes  
**Prereq:** Lesson 217  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 32–33

> **Why:** Non-employees and people on leave need different access rules than active employees — and both look almost identical to a role selector that only checks “active or not.”

## What this is

`employeeType` is either `Employee` or `Contractor`. Seeded active contractors:

| Persona | `userId` |
| --- | --- |
| `rachel.khatri` | `MNB00022` |
| `james.nguyen` | `MNB00023` |

From Lesson 216: `MNB-Bundle-Birthright-Employee` requires `employeeType=Employee`, so contractors are excluded by design.

**Leave of Absence has no dedicated field in this estate** — only `status: Active | Terminated`. You’ll simulate LOA by reusing the termination lever and reversing it, then name why that’s a worse tool than a real LOA state.

## Know these

| State | Field(s) | Native support |
| --- | --- | --- |
| Contractor | `employeeType=Contractor` | Yes — selector excludes from birthright |
| Termination | `active:false`, `status:Terminated` | Yes — leaver trigger fires |
| LOA | *none* | **No** — must reuse the leaver lever and reverse it |

```text
Contractor: selector excludes birthright natively — no simulation needed

LOA (no real field):
  leaver PATCH → access drops like termination
  → manual PATCH reverses
  → audit trail indistinguishable from real termination  ← the gap
```

- **Wrong way:** Treating LOA and termination as the same event because the lab reuses one lever — production needs a distinct state, not a shared trigger with a manual undo.

## Intent

- Confirm contractors get a smaller birthright outcome than employees under the same refresh.
- Prove Rachel’s non-birthright accounts still correlate, then decide what a contractor birthright *should* look like by inspecting her live links.
- Simulate LOA with the only lever HCM exposes, and name exactly what breaks.
- Reverse the simulation and confirm access restores.

## Before you start

- [ ] Lesson 216 birthright refresh run at least once
- [ ] `rachel.khatri` (`MNB00022`) exists as active Contractor (Workday cube from 207+)
- [ ] HCM mock healthy: `curl -sf http://localhost:8091/health`
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/220
```

## Do this

### Task 1 — Confirm contractor exclusion from birthright

Run Identity Refresh with role detection (same flags as Lesson 216), scoped to include `rachel.khatri`. Open her **Roles** tab.

- **Why:** proves the selector gate works for non-employees — not just that employees match.
- **Expect:** **no** `MNB-Bundle-Birthright-Employee` assigned.

Screenshot under `~/iiq-lab-evidence/sandbox/220/`.

### Task 2 — Inventory what Rachel still has

Open Rachel’s **Application Accounts**. List which live apps still correlate (Workday, LDAP, CRM, etc.) even without employee birthright.

- **Why:** a real bank rarely leaves contractors with zero access — you need to see what’s already linked before designing a narrower Bundle.
- **Expect:** Workday (and any other non-birthright links) present; birthright LDAP group from employee role **absent**.

### Task 3 — Sketch a contractor birthright (in IIQ, optional)

If you want a narrower day-one package for contractors, create (or open) a Bundle with selector `employeeType=Contractor` AND `inactive=false`, and attach a smaller OpenLDAP/IdP entitlement than `MNB-Employees`.

Skip the create if your session is short — but write one evidence line naming the entitlement you’d attach (e.g. `MNB-Contractors` or `portal-users` only).

- **Why:** observing exclusion without deciding the alternative is incomplete ops work.
- **Expect:** either a draft Bundle in IIQ, or a one-line policy note under evidence.

### Task 4 — Simulate LOA with the leaver lever

There is no separate LOA action — that’s the gap.

```bash
./tools/lab/enterprise/hcm-scenario.sh leaver MNB00022
```

- **Why:** the only HCM lever that drops access is termination-shaped.
- **Expect:** `active:false`, `status:"Terminated"` at the source.

Confirm:

```bash
curl -s http://localhost:8091/hcm/v1/workers/MNB00022 \
  | python3 -m json.tool | grep -E 'active|status|employeeType'
```

### Task 5 — Run leaver path on Rachel

Aggregate `MNB-Workday` and refresh with the Lesson 219 leaver trigger/workflow (auto or manual).

- **Why:** the system can’t tell LOA from termination — access reduces the same way.
- **Expect:** Rachel’s access reduces exactly like a real leaver’s.

### Task 6 — Reverse the LOA simulation

LOA should be temporary. Restore at the source:

```bash
curl -sf -X PATCH http://localhost:8091/hcm/v1/workers/MNB00022 \
  -H 'Content-Type: application/json' \
  -d '{"active":true,"status":"Active"}' \
  | python3 -m json.tool
```

- **Why:** proves reversibility — real termination should never get this undo path in production policy.
- **Expect:** worker flips back to Active at HCM.

### Task 7 — Aggregate and refresh to restore access

Aggregate `MNB-Workday` and refresh with provisioning enabled (re-enable / re-provision as needed).

- **Why:** a full disable plan (Lesson 219) may need an explicit enable pass — status flip alone may not re-open every hop.
- **Expect:** Rachel’s access restores to its pre-LOA state.

## If it fails

| Symptom | Fix |
| --- | --- |
| Contractor shows birthright anyway | Check `MNB-Bundle-Birthright-Employee` MatchExpression still requires `employeeType=Employee` |
| Reversal `PATCH` doesn’t stick | Confirm worker id `MNB00022`; `active` must be a boolean, not a string |
| Access doesn’t restore after reversal | Re-run refresh with provisioning; watch for an actual enable plan |
| Can’t tell contractor-exclusion from LOA-reduction in IIQ | Use HCM `employeeType` / `status` as ground truth — don’t infer from the Roles tab alone |

## You are done when

- [ ] Contractor correctly excluded from employee birthright
- [ ] Rachel’s non-birthright links inventoried (and optional contractor Bundle sketched)
- [ ] LOA simulated and reversed via leaver lever; access restored

## Control note

- **Control:** Non-employee access scoping + leave-of-absence handling
- **Owner:** HR Ops (source state) + IAM Ops (selector design)
- **SLA (lab):** same-session reversal; production LOA should never share termination’s trigger
- **Evidence:** `~/iiq-lab-evidence/sandbox/220/` — contractor exclusion proof, LOA PATCH pair, before/after access state

## Quick check

1. Which selector term excludes contractors from birthright? → `employeeType=Employee`
2. What lever does this estate reuse to simulate LOA? → the leaver (termination) `PATCH`
3. Why is that reuse a real finding? → indistinguishable audit trail between “left the bank” and “on leave”

## Feedback

Could you explain why LOA-via-terminate is unsafe for audit without opening this lesson? If access didn’t restore after Task 7, note whether you saw an enable plan — status flip without provisioning is the usual miss.

## Navigate

- Previous: [Lesson 219](219-leaver-lcm-live.md)
- Next: [Lesson 221](221-access-catalog-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
