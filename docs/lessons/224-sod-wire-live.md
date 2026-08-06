# Lesson 224 — SoD: Wire Dual Control Live

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~65 minutes  
**Prereq:** Lessons 216, 222  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 39–40

> **Why (1–2 lines):** One person who can both initiate and approve a wire is a critical ops finding on day one. SoD only matters when the policy references roles that actually exist and a scan produces a visible violation.

## What this is

`MNB-Policy-SOD-Wire-DualControl` is an `SOD` policy (`sailpoint.policy.SODPolicyExecutor`) with one constraint: left bundle set vs right bundle set — dual control. The shipped XML references `MNB-Role-WireInitiator` / `MNB-IT-WireInit` / `MNB-Role-WireApprover` / `MNB-IT-WireAppr` — **none exist in `config/Bundle/`**. Only `MNB-Bundle-Wire-Initiator` is real. Classic 39–40 taught SoD design; this lesson makes you repair dangling references (the kind SSD promote catches in 248) and prove a live violation on Marcus.

## Know these

```text
Left:  can initiate wire  (MNB-Bundle-Wire-Initiator → WIRE_INIT)
Right: can approve wire   (MNB-Bundle-Wire-Approver → WIRE_APPR)
Same identity holds both → Policy Violation on SoD scan
```

| Term | Meaning |
| --- | --- |
| SODConstraint | LeftBundles vs RightBundles — mutual exclusion |
| Detection | Policy scan / refresh with check policies |
| Enforcement | Reject second grant **or** mitigate with expiry (225) |

**Wrong way:** Importing the policy “green” while Bundle names don’t resolve — silent non-firing SoD is worse than a loud import error.

## Intent

- Discover dangling Bundle references in the shipped policy.
- Create `MNB-Bundle-Wire-Approver` mapped to `WIRE_APPR`.
- Repoint and activate the policy on real Bundles.
- Force a violation on one identity and resolve or mitigate.

## Before you start

- [ ] `MNB-Bundle-Wire-Initiator` works (Lesson 216)
- [ ] Marcus has Core Banking / wire data (Lesson 208)
- [ ] Read `config/Policy/MNB-Policy-SOD-Wire-Dual-Control.xml` once
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/224`

## Do this

1. Open the Policy XML; list Left/Right Bundle names; grep `config/Bundle/` for each.  
   **Expect:** Only `MNB-Bundle-Wire-Initiator` exists; the four shipped names do not.

2. Create `it` Bundle `MNB-Bundle-Wire-Approver`, `requestable=true`, mapped to `WIRE_APPR` on the **same** live app as Initiator (`MNB-WirePortal` or `MNB-CoreBanking`).  
   **Expect:** Role can provision/recognize `WIRE_APPR`.

3. Edit Policy: `LeftBundles` → `MNB-Bundle-Wire-Initiator`; `RightBundles` → `MNB-Bundle-Wire-Approver`. Keep `type="SOD"`, executor, `configPage="sodpolicy.xhtml"`.  
   **Expect:** No dangling names; capitalization exact.

4. Import/activate (`state="Active"`). Open **Setup → Policies → SOD Policies**.  
   **Expect:** Policy listed without unresolved-reference warnings.

5. Use `marcus.approve` (seeded `WIRE_APPR`). Also assign `MNB-Bundle-Wire-Initiator` (direct or via Lesson 222 request).  
   **Expect:** Marcus now holds both sides of dual control.

6. Run policy scan / Identity Refresh with **check policies** scoped to Marcus.  
   **Expect:** Policy Violation for `MNB-Policy-SOD-Wire-DualControl`.

7. Open the violation; confirm both Initiator and Approver sides named.  
   **Expect:** Correct attribution — not a generic “policy failed.”

8. Resolve: **reject** (remove Initiator, re-scan, violation clears) **or** **mitigate** with justification + expiry and carry into Lesson 225.  
   **Expect:** Either clear violation or an open mitigation record.

## If it fails

- **Import fails on unedited XML** — expected; fix references (steps 2–3).
- **Policy never fires** — scan/refresh lacks SoD/policy check flags.
- **Wrong bundles on violation** — stale Left/Right names; name-exact Bundle refs.
- **Unsure what Marcus already holds** —  
  `docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps -c "select username, entitlement from mnb_app_accounts where username='marcus.approve';"`
- **Violation won’t clear** — re-scan after removing conflict; violations clear on next evaluation.

## You are done when

Active SoD policy references two real Bundles; Marcus generates a correctly attributed violation when he holds both wire powers.

## Control note

- **Control:** Wire dual-control SoD.  
- **Owner:** Treasury Controls + IAM.  
- **SLA (lab):** Detect same session; production often continuous / daily scan.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/224/` — policy XML snippet (no secrets), violation id, resolve/mitigate choice.

## Quick check

1. What makes shipped SoD “importable but broken”? → Bundle names that don’t exist.  
2. Why must Initiator and Approver map to the same app family? → Constraint compares comparable powers.  
3. Detection without reject/mitigate proves what? → Only awareness — not enforcement.

## Navigate

- Previous: Lesson 223  
- Next: Lesson 225  
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
