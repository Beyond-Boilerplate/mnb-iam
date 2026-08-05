# Lesson 220 — Contractor & LOA Controls Live

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~55 minutes  
**Prereq:** Lesson 217  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 32–33

> **Why (1–2 lines):** Non-employees and people on leave need different access rules than active employees — and both look almost identical to a role selector that only checks "active or not."

## What this is

`employeeType` is either `Employee` or `Contractor` — `rachel.khatri` (`MNB00022`) and `james.nguyen` (`MNB00023`) are seeded as active Contractors. Recall from Lesson 216: `MNB-Bundle-Birthright-Employee`'s selector explicitly requires `employeeType=Employee`, excluding contractors by design. **Leave of Absence has no dedicated field in this estate** — only `status: active|terminated`. That's an honest gap: you'll simulate LOA by reusing the termination lever and reversing it, then name why that's a worse tool than a real LOA state.

## Know these

| State | Field(s) | Native support |
| --- | --- | --- |
| Contractor | `employeeType=Contractor` | Yes — selector excludes from birthright |
| Termination | `active:false, status:Terminated` | Yes — leaver trigger fires |
| LOA | *none* | **No** — must reuse the leaver lever and reverse it |

```text
Contractor: selector excludes birthright natively — no simulation needed
LOA (no real field): leaver PATCH → access drops like termination → manual PATCH reverses
  → indistinguishable audit trail from real termination — that's the gap
```

**Wrong way:** Treating LOA and termination as the same event because the lab has to reuse one lever — production needs a distinct state, not a shared trigger with a manual undo.

## Intent

- Confirm contractors get a smaller birthright outcome than employees under the same refresh.
- Decide and document what contractors *should* get instead of zero access.
- Simulate LOA using the only lever this estate has, and name exactly what breaks.
- Reverse the LOA simulation and confirm access restores — proving it's reversible, unlike termination.

## Before you start

- [ ] Lesson 216 birthright refresh run at least once
- [ ] `rachel.khatri` (`MNB00022`) exists as active Contractor
- [ ] HCM mock healthy: `curl -sf http://localhost:8091/health`
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/220`

## Do this

1. Run the same role-detection refresh from Lesson 216/218 scoped to include `rachel.khatri`.  
   **Expect:** Roles tab shows **no** `MNB-Bundle-Birthright-Employee` — selector correctly excludes `Contractor`.

2. Decide what contractors should get instead of nothing — a narrower Bundle scoped to `employeeType=Contractor`, or confirm her live app accounts still aggregate/correlate correctly without birthright.  
   **Why:** A real bank rarely leaves contractors with zero access; document the policy, don't just observe the absence.  
   **Expect:** A written decision, plus evidence her non-birthright accounts still correlate.

3. Attempt the "real" LOA event through the only lever HCM exposes: `./tools/lab/enterprise/hcm-scenario.sh leaver MNB00022`.  
   **Why:** There is no separate LOA action — that's the gap itself, not a typo.  
   **Expect:** `active:false, status:"Terminated"` set at the source.

4. Aggregate `MNB-Workday` and refresh with the Lesson 219 leaver trigger/workflow.  
   **Expect:** Rachel's access reduces exactly like a real leaver's — the system can't tell LOA from termination.

5. Reverse it — LOA should be temporary. Direct `PATCH` to restore: `curl -sf -X PATCH http://localhost:8091/hcm/v1/workers/MNB00022 -H 'Content-Type: application/json' -d '{"active":true,"status":"Active"}' | python3 -m json.tool`.  
   **Expect:** Worker flips back to Active at the source.

6. Aggregate and refresh again.  
   **Expect:** Rachel's access restores to its pre-LOA state — a reversal real termination should never allow.

## If it fails

- **Contractor shows birthright assigned anyway** — check `MNB-Bundle-Birthright-Employee`'s `MatchExpression` still requires `employeeType=Employee`.
- **Reversal `PATCH` doesn't stick** — confirm you targeted the right worker id (`MNB00022`) and `active` is a real boolean, not a string.
- **Access doesn't restore after reversal + refresh** — a full disable plan (Lesson 219's leaver workflow) may need an explicit re-enable/re-provision pass; re-run refresh with provisioning enabled, watching for an actual enable plan.
- **Can't tell contractor-exclusion from LOA-reduction in the UI** — expected; use HCM's own `employeeType`/`status` fields as ground truth instead of inferring from IIQ's role list.

## You are done when

A contractor is correctly excluded from birthright with a documented alternative-access decision, and you've simulated and reversed an LOA event using the leaver lever, restoring access fully.

## Control note

- **Control:** Non-employee access scoping + leave-of-absence handling.  
- **Owner:** HR Ops (source state) + IAM Ops (selector design).  
- **SLA (lab):** Same session reversal; production LOA should never share termination's trigger.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/220/` — contractor exclusion proof, LOA PATCH pair, before/after access state.

## Quick check

1. Which selector term excludes contractors from birthright? → `employeeType=Employee`.  
2. What lever does this estate reuse to simulate LOA? → The leaver (termination) `PATCH`.  
3. Why is that reuse a real finding, not just a lab shortcut? → Indistinguishable audit trail between "left the bank" and "on leave."

## Navigate

- Previous: Lesson 219  
- Next: Lesson 221  
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
