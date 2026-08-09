# Lesson 224 — SoD: Wire Dual Control Live

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~75 minutes  
**Prereq:** Lessons 216, 222  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 39–40

> **Why:** One person who can both initiate and approve a wire is a critical ops finding on day one. SoD only matters when the policy references roles that actually exist and a scan produces a visible violation.

## What this is

**Segregation of Duties (SoD)** means splitting powers that are dangerous in one pair of hands. At Meridian’s wire desk:

| Power | Meaning | Should the same person hold both? |
| --- | --- | --- |
| **Initiate** | Create / send a wire instruction | — |
| **Approve** | Authorize that wire | **Never** with Initiate |

IIQ models this with an **SOD policy**: a constraint with a **Left** Bundle set and a **Right** Bundle set. If one identity holds something from Left **and** something from Right, a **Policy Violation** appears when you scan.

The shipped policy XML (`config/Policy/MNB-Policy-SOD-Wire-Dual-Control.xml`) references Bundle names like `MNB-Role-WireInitiator` / `MNB-IT-WireAppr` — **those Bundles do not exist** under `config/Bundle/`. Only `MNB-Bundle-Wire-Initiator` is real today. You will:

1. Discover the dangling references  
2. Create `MNB-Bundle-Wire-Approver` mapped to `WIRE_APPR`  
3. Repoint the policy to real Bundles  
4. Force a violation on Marcus  

Classic 39–40 taught SoD design; this lesson teaches the SSD-promote class of bug: importable XML that never fires.

## Know these

```text
Left:  MNB-Bundle-Wire-Initiator  → WIRE_INIT  (can start a wire)
Right: MNB-Bundle-Wire-Approver   → WIRE_APPR  (can approve a wire)

Same identity holds both
  → Identity Refresh / policy scan with check policies
  → Policy Violation (MNB-SOD-Wire-DualControl)
  → Lesson 225: mitigate or remediate
```

| Term | Plain English |
| --- | --- |
| **SoD / SOD** | Segregation of Duties — mutually exclusive powers |
| **SODConstraint** | LeftBundles vs RightBundles rule inside a Policy |
| **Detection** | Scan / refresh finds the conflict |
| **Enforcement** | Reject the second grant **or** mitigate with expiry (Lesson 225) |
| **Dangling reference** | Policy names a Bundle that doesn’t exist — silent non-fire |

| Policy file name (disk) | Object `name` attribute in XML |
| --- | --- |
| `MNB-Policy-SOD-Wire-Dual-Control.xml` | Often `MNB-SOD-Wire-DualControl` — use what Import shows |

- **Wrong way:** Importing the policy “green” while Bundle names don’t resolve — silent non-firing SoD is worse than a loud import error.
- **Wrong way:** Mapping Initiator and Approver to unrelated apps — the constraint must compare comparable powers on the same wire path.
- **Wrong way:** Stopping at “violation exists” without deciding reject vs mitigate — detection ≠ enforcement.

## Intent

- Discover dangling Bundle references in the shipped policy.
- Create `MNB-Bundle-Wire-Approver` mapped to `WIRE_APPR` on the same live app family as Initiator.
- Repoint and activate the policy on real Bundles.
- Force a correctly attributed violation on Marcus; resolve or carry mitigation into 225.

## Before you start

- [ ] `MNB-Bundle-Wire-Initiator` works (Lesson 216 / 222)
- [ ] Marcus (`marcus.approve`) has Core Banking / wire data (Lesson 208)
- [ ] Read `config/Policy/MNB-Policy-SOD-Wire-Dual-Control.xml` once
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/224
```

## Do this

### Task 1 — List Left/Right names and grep for Bundles

Open the Policy XML. Write down every Bundle name under `LeftBundles` and `RightBundles`.

From the repo root:

```bash
ls config/Bundle/
grep -n 'Wire' config/Bundle/*.xml config/Policy/MNB-Policy-SOD-Wire-Dual-Control.xml
```

- **Why:** you need proof the shipped names are fiction before editing.
- **Expect:** only `MNB-Bundle-Wire-Initiator` exists among the wire roles; the four shipped policy names do **not**.

Save the list under evidence.

### Task 2 — Create `MNB-Bundle-Wire-Approver`

1. **Setup → Roles → Create New** (IT / role as your build prefers)
2. Name: **`MNB-Bundle-Wire-Approver`** (exact spelling — policy will reference it)
3. `requestable=true` (optional but useful)
4. Map required entitlement **`WIRE_APPR`** on the **same** live app as Initiator (`MNB-WirePortal` or `MNB-CoreBanking`)
5. Save

- **Why:** dual control needs a real Approver pack, not a phantom XML name.
- **Expect:** role can provision / recognize `WIRE_APPR`.

> **Tip:** If `WIRE_APPR` isn’t in Entitlement Catalog yet, run Account Aggregation (and Group Aggregation if needed) on that app first — same catalog lesson as 216.

### Task 3 — Repoint the policy to real Bundles

Edit the Policy (Debug Import of corrected XML, or UI **Setup → Policies**):

| Side | Set to |
| --- | --- |
| LeftBundles | `MNB-Bundle-Wire-Initiator` |
| RightBundles | `MNB-Bundle-Wire-Approver` |

Keep:

- `type="SOD"`
- executor `sailpoint.policy.SODPolicyExecutor`
- `configPage="sodpolicy.xhtml"`
- `state="Active"`

Capitalization must be **exact**.

- **Expect:** no dangling names.

### Task 4 — Import / activate and open in UI

1. Import if you edited XML  
2. **Setup → Policies → SOD Policies** (or Policy list)  
3. Open your Wire dual-control policy  

- **Expect:** policy listed without unresolved-reference warnings; state Active.

### Task 5 — Give Marcus both sides

1. Confirm `marcus.approve` already holds Approver power (`WIRE_APPR` / Approver Bundle) — often seeded  
2. Also assign `MNB-Bundle-Wire-Initiator` (direct assign **or** via request/approval like Lesson 222)  

Optional JDBC ground truth:

```bash
docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps \
  -c "select username, entitlement from mnb_app_accounts where username='marcus.approve';"
```

- **Expect:** Marcus now holds **both** sides of dual control.

### Task 6 — Run policy scan / refresh with check policies

Run **Identity Refresh** (or your Policy scan task) scoped to Marcus with **check policies** / SoD evaluation enabled.

- **Why:** detection doesn’t run because the policy file exists — something must evaluate it.
- **Expect:** Policy Violation for the Wire dual-control policy.

### Task 7 — Open the violation and read both sides

Open the violation detail. Confirm it names:

- Initiator side (`MNB-Bundle-Wire-Initiator` / `WIRE_INIT`)  
- Approver side (`MNB-Bundle-Wire-Approver` / `WIRE_APPR`)  

- **Expect:** correct attribution — not a generic “policy failed.”

Screenshot / note violation id under evidence.

### Task 8 — Resolve or mitigate

Pick one:

| Choice | Action | Next |
| --- | --- | --- |
| **Reject / remediate** | Remove Initiator from Marcus; re-scan; violation clears | Done for 224 |
| **Mitigate** | Keep conflict temporarily with justification + expiry | Carry into Lesson 225 |

- **Expect:** either a clear violation **or** an open mitigation record for 225.

## If it fails

| Symptom | Fix |
| --- | --- |
| Import fails on unedited XML | Expected if names don’t resolve — fix references (Tasks 2–3) |
| Policy never fires | Scan/refresh lacks SoD / check-policies flags |
| Wrong bundles on violation | Stale Left/Right names — name-exact Bundle refs |
| Unsure what Marcus holds | Use the `psql` query above + IIQ Application Accounts |
| Violation won’t clear after remove | Re-scan after removing conflict — violations clear on next evaluation |
| `WIRE_APPR` missing from catalog | Aggregate the wire/core app before mapping the Approver Bundle |

## You are done when

- [ ] Active SoD policy references two **real** Bundles  
- [ ] Marcus generates a correctly attributed violation when he holds both wire powers  
- [ ] You chose reject **or** mitigate (and know which Lesson 225 needs)  

## Control note

- **Control:** Wire dual-control SoD  
- **Owner:** Treasury Controls + IAM  
- **SLA (lab):** Detect same session; production often continuous / daily scan  
- **Evidence:** `~/iiq-lab-evidence/sandbox/224/` — policy snippet (no secrets), violation id, resolve/mitigate choice  

## Quick check

1. What makes shipped SoD “importable but broken”? → Bundle names that don’t exist  
2. Why must Initiator and Approver map to the same app family? → Constraint compares comparable powers  
3. Detection without reject/mitigate proves what? → Only awareness — not enforcement  
4. Who is the dual-control persona in this lab? → `marcus.approve`  

## Feedback

Could you explain dangling Bundle references without opening the XML? If the policy never fired, note whether you enabled check-policies on refresh — existence of a Policy object is not detection.

Before Lesson 225: write whether you chose **reject** or **mitigate** — 225 needs an open violation (or a recreate path) either way.

## Navigate

- Previous: [Lesson 223](223-break-glass-live.md)
- Next: [Lesson 225](225-policy-violations-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
