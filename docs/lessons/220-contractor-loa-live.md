# Lesson 220 — Contractor & LOA Controls Live

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~70 minutes  
**Prereq:** Lessons 216–219  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 32–33

> **Why:** Non-employees and people on leave need different access rules than active employees — and both look almost identical to a role selector that only checks “active or not.”

## What this is

Not everyone in the Identity Warehouse is a full-time employee. Meridian also has **contractors** — temporary workers who should get a *smaller* day-one package (or none of the employee birthright).

Separately, an employee can go on **Leave of Absence (LOA)** — still employed, but access should drop until return. That is **not** the same as termination, even though both people may look “inactive” in a careless selector.

In this estate:

| Concept | Field(s) available? | What happens |
| --- | --- | --- |
| **Contractor** | Yes — `employeeType=Contractor` | Birthright selector requires `Employee` → contractors excluded |
| **Termination** | Yes — `active:false`, `status:Terminated` | Leaver trigger (Lesson 219) |
| **LOA** | **No dedicated field** | You simulate by reusing termination, then reversing — and name why that’s a control gap |

Seeded active contractors you will use:

| Persona | `userId` | Type |
| --- | --- | --- |
| `rachel.khatri` | `MNB00022` | Contractor |
| `james.nguyen` | `MNB00023` | Contractor |

From Lesson 216: `MNB-Bundle-Birthright-Employee` requires `employeeType=Employee`, so contractors are excluded by design — if you built the selector correctly.

## Know these

```text
Contractor path (native):
  employeeType=Contractor
    → birthright MatchTerm employeeType=Employee fails
    → no MNB-Bundle-Birthright-Employee
    → (optional) design a narrower contractor Bundle

LOA path (simulated — no real field):
  leaver PATCH → access drops like termination
    → manual PATCH reverses active/status
    → aggregate + provision refresh restores
    → audit trail looks like "terminated then rehired"  ← the gap
```

| Term | Plain English |
| --- | --- |
| **`employeeType`** | HR classification on the cube — Employee vs Contractor |
| **Birthright selector** | MatchExpression that decides who auto-gets a role |
| **LOA** | Temporary leave — should suspend access without “termination” semantics |
| **Mitigation vs design** | Reusing leaver for LOA “works” technically but fails audit meaning |

- **Wrong way:** Treating LOA and termination as the same event because the lab reuses one lever — production needs a distinct state, not a shared trigger with a manual undo.
- **Wrong way:** Assuming “contractor = no accounts at all” — Rachel may still correlate to Workday / CRM without employee birthright.
- **Wrong way:** Inferring contractor vs LOA from the Roles tab alone — use HCM `employeeType` / `status` as ground truth.

## Intent

- Confirm contractors are excluded from employee birthright under the same refresh employees use.
- Inventory what Rachel still has without birthright; sketch what a contractor package *should* include.
- Simulate LOA with the only HCM lever available; reverse it; confirm access restores.
- Name exactly why LOA-via-terminate is an audit finding.

## Before you start

- [ ] Lesson 216 birthright refresh run at least once (`MNB-Bundle-Birthright-Employee` exists with `employeeType=Employee`)
- [ ] `rachel.khatri` (`MNB00022`) exists as active Contractor (Workday cube from 207+)
- [ ] Lesson 219 leaver workflow/trigger available (you’ll reuse the path for LOA sim)
- [ ] HCM mock healthy:

```bash
curl -sf http://localhost:8091/health
```

- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/220
```

## Do this

### Task 1 — Confirm contractor exclusion from birthright

1. Run **Identity Refresh** with role detection (same flags as Lesson 216), scoped to include `rachel.khatri`
2. Open her cube → **Roles** tab

- **Why:** proves the selector gate works for non-employees — not just that employees match.
- **Expect:** **no** `MNB-Bundle-Birthright-Employee` assigned.

Screenshot under `~/iiq-lab-evidence/sandbox/220/`.

> **Tip:** Also open an employee (e.g. `helen.ross`) Roles tab for a side-by-side — same refresh, different outcome.

### Task 2 — Inventory what Rachel still has

Open Rachel’s **Application Accounts**. List which live apps still correlate even without employee birthright:

| App | Present? (Y/N) | Notes |
| --- | --- | --- |
| `MNB-Workday` | | Authoritative link expected |
| `MNB-OpenLDAP` | | Employee birthright LDAP group should be absent |
| `MNB-Salesforce-CRM-Live` | | May correlate without birthright |
| Other | | |

- **Why:** a real bank rarely leaves contractors with zero access — you need to see what’s already linked before designing a narrower Bundle.
- **Expect:** Workday (and any non-birthright links) present; birthright LDAP group from employee role **absent**.

Save the inventory as a short text file under evidence.

### Task 3 — Sketch a contractor birthright (optional create)

Decide what day-one access a contractor *should* get (example: Portal SSO only, no Wire, no employee LDAP group).

**Option A — Create a draft Bundle in IIQ**

1. **Setup → Roles → Create New → Role** (or IT / Business as your build prefers)
2. Name e.g. `MNB-Bundle-Birthright-Contractor`
3. Selector: `employeeType=Contractor` **AND** inactive/active filter for “currently engaged”
4. Attach a **smaller** entitlement than employee birthright (e.g. IdP `portal-users` only — not `all-employees` / Wire)

**Option B — Policy note only (if short on time)**

Write one evidence line:

```text
Contractor birthright candidate: portal-users only via MNB-Keycloak-IdP;
exclude Wire Initiator and employee OpenLDAP all-employees.
```

- **Why:** observing exclusion without deciding the alternative is incomplete ops work.
- **Expect:** either a draft Bundle in IIQ, or a one-line policy note under evidence.

### Task 4 — Simulate LOA with the leaver lever

There is no separate LOA action in this HCM mock — that’s the gap.

```bash
./tools/lab/enterprise/hcm-scenario.sh leaver MNB00022
```

Confirm at the source:

```bash
curl -s http://localhost:8091/hcm/v1/workers/MNB00022 \
  | python3 -m json.tool | grep -E 'active|status|employeeType|userName'
```

- **Why:** the only HCM lever that drops access is termination-shaped.
- **Expect:** `active:false`, `status:"Terminated"`, `employeeType` still `Contractor`.

> **Watch out:** Note `employeeType` stayed Contractor — you did **not** turn Rachel into an employee. You marked her Terminated, which is the wrong semantic for LOA.

### Task 5 — Run leaver path on Rachel

Aggregate `MNB-Workday` and refresh with **Process events** (Lesson 219 path — auto trigger or manual `MNB-Workflow-Leaver`).

- **Why:** the system can’t tell LOA from termination — access reduces the same way.
- **Expect:** Rachel’s access reduces exactly like a real leaver’s (accounts disabled / roles removed as your disable plan defines).

Screenshot after-state under evidence.

### Task 6 — Reverse the LOA simulation

LOA should be temporary. Restore at the source:

```bash
curl -sf -X PATCH http://localhost:8091/hcm/v1/workers/MNB00022 \
  -H 'Content-Type: application/json' \
  -d '{"active":true,"status":"Active"}' \
  | python3 -m json.tool
```

- **Why:** proves reversibility — real termination should never get this casual undo path in production policy.
- **Expect:** worker flips back to Active at HCM.

### Task 7 — Aggregate and refresh to restore access

1. Aggregate `MNB-Workday`
2. Refresh with provisioning enabled (re-enable / re-provision as needed)
3. Confirm Rachel’s Application Accounts / Portal access return to pre-LOA state

- **Why:** a full disable plan (Lesson 219) may need an explicit enable pass — status flip alone may not re-open every hop.
- **Expect:** Rachel’s access restores to its pre-LOA state.

### Task 8 — Name the control finding

Save under evidence:

```text
LOA simulated via termination PATCH. Audit trail indistinguishable from real
termination + rehire. Production needs distinct LOA status + LOA-specific
workflow (suspend without Terminated semantics).
```

- **Why:** the lesson outcome is the finding, not “Rachel works again.”
- **Expect:** written gap you could hand to HR/IAM design.

## If it fails

| Symptom | Fix |
| --- | --- |
| Contractor shows birthright anyway | Check `MNB-Bundle-Birthright-Employee` MatchExpression still requires `employeeType=Employee` |
| Reversal `PATCH` doesn’t stick | Confirm worker id `MNB00022`; `active` must be a boolean, not a string `"true"` |
| Access doesn’t restore after reversal | Re-run refresh with **provisioning**; watch for an actual enable plan |
| Can’t tell contractor-exclusion from LOA-reduction | Use HCM `employeeType` / `status` as ground truth — don’t infer from Roles alone |
| Rachel missing entirely | Re-aggregate Workday from Lesson 207; confirm she exists in HCM list |

## You are done when

- [ ] Contractor correctly excluded from employee birthright
- [ ] Rachel’s non-birthright links inventoried (and optional contractor Bundle sketched)
- [ ] LOA simulated and reversed via leaver lever; access restored
- [ ] Written finding: LOA-via-terminate is unsafe for audit semantics

## Control note

- **Control:** Non-employee access scoping + leave-of-absence handling
- **Owner:** HR Ops (source state) + IAM Ops (selector design)
- **SLA (lab):** same-session reversal; production LOA should never share termination’s trigger
- **Evidence:** `~/iiq-lab-evidence/sandbox/220/` — contractor exclusion proof, LOA PATCH pair, before/after access, finding note

## Quick check

1. Which selector term excludes contractors from birthright? → `employeeType=Employee` on the employee Bundle  
2. What lever does this estate reuse to simulate LOA? → The leaver (termination) `PATCH`  
3. Why is that reuse a real finding? → Indistinguishable audit trail between “left the bank” and “on leave”  
4. Does reversing LOA require provisioning? → **Usually yes** — status flip alone may not re-enable every app  

## Feedback

Could you explain why LOA-via-terminate is unsafe for audit without opening this lesson? If access didn’t restore after Task 7, note whether you saw an enable plan — status flip without provisioning is the usual miss.

## Navigate

- Previous: [Lesson 219](219-leaver-lcm-live.md)
- Next: [Lesson 221](221-access-catalog-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
