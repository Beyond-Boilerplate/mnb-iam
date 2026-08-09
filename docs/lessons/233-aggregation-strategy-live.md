# Lesson 233 — Live Aggregation Runbook

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~50 minutes  
**Prereq:** Lessons 207–210, 214, 216  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 16 / 54 / 08

> **Why:** Aggregate targets before HR and you correlate accounts to identities that don’t exist yet — orphan links break leavers (219) and correlation (214). Document the sequence before calling refresh done.

## What this is

By now you have multiple live apps. A bank ops team does **not** run them ad hoc. They run a fixed sequence:

1. **Authoritative HR** (`MNB-Workday`)  
2. **Refresh Identity Cubes** (promote keys managers/targets correlate on)  
3. **Downstream targets** (directories, JDBC, Wire, CRM, IdP)  
4. **Refresh again** (promote newly linked entitlements)

You will write that as a runbook, execute it clean, schedule what’s still manual, then **break the order on purpose** to see an orphan — then fix it.

**IdP note:** Birthright Portal groups use `MNB-Keycloak-IdP` (Lessons 216–217). Seed may also include `MNB-Okta` as a SCIM-shaped app — include whichever IdP app you actually aggregate in this estate; don’t invent a third.

Classic 16/54 taught multi-app aggregation; here order is a **control**, not a convenience.

## Know these

| Step | Why it’s ordered here |
| --- | --- |
| 1. Aggregate `MNB-Workday` | HCM is authoritative for identity existence |
| 2. Refresh Identity Cubes | Promotes HR attrs (`employeeNumber`, manager, `employeeType`) |
| 3. Aggregate directories + JDBC + Wire/CRM + IdP | Each depends on the cube already having the correlation key |
| 4. Refresh Identity Cubes again | Promotes newly linked entitlements onto the cube |

```text
HCM (Workday) → Refresh
  → OpenLDAP / Samba AD
  → Core Banking → Wire → CRM
  → Keycloak-IdP (and/or Okta if present)
  → Refresh
```

| Term | Plain English |
| --- | --- |
| **Authoritative source** | System that creates/ends workforce cubes (Workday here) |
| **Orphan / uncorrelated** | Native account with no linked Identity |
| **TaskDefinition** | What to run (aggregate, refresh, …) |
| **Task Schedule** | Cron-like timing attached to a TaskDefinition |
| **TaskResult** | Auditable record: start/end, host, counters, first error — read **before** re-run |
| **Correlation key** | Attribute both sides share (often `employeeNumber` / `userId`) |
| **Purpose-built refresh** | Separate Identity Refresh tasks (attrs / managers / roles / policies) — not one mega-refresh |
| **Full aggregation** | Iterate entire configured scope — baseline / small apps / file feeds |
| **Delta aggregation** | Changes since watermark / USN / timestamp — large directories when connector supports it |
| **Partition** | Split account space across workers — huge directories; partitions must not overlap or gap |

```text
TaskDefinition → Schedule / Run Now → TaskResult (counters, errors, duration)
  Read TaskResult before any re-run — blind re-run masks root cause
```

| Pattern (classic 54) | When Meridian uses it | Completeness risk |
| --- | --- | --- |
| **Full** | Workday / JDBC / Wire / CRM nightly; quarterly AD reconcile | Slow on huge directories |
| **Delta** | Large AD when connector supports USN/watermark | Watermark bugs can hide disables |
| **Partition** | Directory too big for one iterate | Overlap = duplicate work; gap = silent holes |

**Ops discipline (classic 08):**

- Purpose-built refreshes (attrs → managers → roles) beat one Identity Refresh with every checkbox on
- **No overlapping refreshes** — lock contention and partial state
- Stop the chain on Workday aggregate failure; don’t refresh from a stale partial load

- **Wrong way:** Aggregating targets before HR “to save time” — silent orphans until a cert.
- **Wrong way:** Parallelizing “because the lab is small” — order is a correctness rule.
- **Wrong way:** Listing `MNB-Okta` when your Portal path is only `MNB-Keycloak-IdP` — runbook must match the live estate.
- **Wrong way:** Re-running a failed task without reading the TaskResult stack — you erase the evidence.
- **Wrong way:** Trusting delta forever with no full reconcile — examiners ask how disables still surface.

## Intent

- Write a runbook: HR → Refresh → directories → apps → IdP → Refresh, with Full/Delta notes.
- Execute it once end-to-end with TaskResult discipline and zero orphaned accounts on a spot-check identity.
- Schedule any app still manual-only without overlapping refreshes.
- Break the order once; capture the orphan; fix by aggregating HR first.

## Before you start

- [ ] Apps from 207–210 aggregate successfully standalone
- [ ] `./tools/lab/enterprise/hcm-scenario.sh` available
- [ ] Know which IdP app you use (`MNB-Keycloak-IdP` and/or `MNB-Okta`)
- [ ] Spot-check identity ready (`helen.ross` or a recent joiner)
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/233
```

## Do this

### Task 1 — Write the runbook

Under evidence, write your estate’s sequence (adjust IdP line to match reality). Include **pattern** notes (classic 54):

```text
1) Aggregate MNB-Workday              [FULL — authoritative; FAIL → STOP]
2) Refresh attrs (promote)            [purpose-built; wait for Complete]
3) Aggregate MNB-OpenLDAP             [FULL]
4) Aggregate MNB-ActiveDirectory-Live [DELTA nightly + FULL quarterly if --with=ad]
5) Aggregate MNB-CoreBanking          [FULL]
6) Aggregate MNB-WirePortal + CRM     [FULL]
7) Aggregate MNB-Keycloak-IdP (+ Okta if present) [FULL]
8) Refresh again (managers / entitlements) — separate from step 2; do NOT overlap
```

- **Why:** tribal memory fails the night you’re out; pattern + stop-on-HR-fail is the control artifact.
- **Expect:** a checklist anyone on the team could run, with Full/Delta called out.

### Task 2 — Execute clean, in order (TaskResult discipline)

Run via **Monitor → Tasks** or **Applications → Aggregate**.

Wait for each **TaskResult** to show **Complete** before starting the next — **no parallel** and **no overlapping refreshes** for this drill.

For each step, open the TaskResult and note (even roughly):

| Field | Why it matters |
| --- | --- |
| Start / end / duration | SLA + capacity |
| Accounts scanned / created / updated | Completeness vs prior baseline |
| Failures / first error stack | Partial success is still a control event |

- **Why:** TaskResult is continuous control evidence (classic 08/54) — re-running blind masks the root cause.
- **Expect:** every step Complete; you can name one counter you checked on at least one aggregation.

### Task 3 — Spot-check correlation

Open **Identities → Identity Warehouse** → `helen.ross` (or recent joiner) → Application Accounts.

- **Expect:** expected links correlated (OpenLDAP, AD if present, Core Banking, Wire, CRM, IdP) — none orphaned on this identity.

Screenshot under evidence.

### Task 4 — Schedule what’s still manual (no overlap)

**Monitor → Tasks → Task Schedule** (or create **New Task → Account Aggregation** then schedule).

Add a nightly (or lab-friendly) schedule for any app you still only run by hand.

Stagger so aggregation finishes **before** attribute refresh, and attribute refresh finishes **before** manager/role refresh — never two Identity Refresh jobs at once.

- **Why:** the runbook must survive without you; overlapping refreshes risk contention and partial state (classic 08).
- **Expect:** recurring schedules exist for the sequence’s apps; refresh windows do not collide.

### Task 5 — Break the order on purpose

1. Create a fresh HCM worker you have **not** pulled into IIQ yet:

```bash
./tools/lab/enterprise/hcm-scenario.sh joiner lab.orphan1 Lab Orphan \
  lab.orphan1@meridiannb.com 'Bank Operations'
```

2. Ensure a matching row exists (or can be inserted) on a **target** — e.g. seed Core Banking / CRM for `lab.orphan1` if your lab tools support it, **or** temporarily create a native account the connector will see  
3. Aggregate that **target** (`MNB-CoreBanking` or `MNB-Salesforce-CRM-Live`) **before** aggregating `MNB-Workday` for this worker  

- **Expect:** target aggregation completes **without error** — the trap is that it looks fine.

> **Tip:** If you can’t seed a target row easily, document the intended break and use an existing uncorrelated account from an earlier lesson as the orphan specimen — still prove “uncorrelated” in Task 6.

### Task 6 — See the orphan

**Applications → Application Definition → \<target\> → Accounts** (or Uncorrelated Accounts view).

Find the native account for the new worker.

- **Expect:** **uncorrelated** — no linked Identity. That is the orphan symptom.

Screenshot under evidence.

### Task 7 — Fix with HR-first order

1. Aggregate `MNB-Workday`  
2. Refresh Identity Cubes  
3. Re-aggregate the target  

- **Expect:** account correlates on the next pass — proof the fix is “aggregate HR first,” not “wait longer.”

### Task 8 — Bag evidence

Save under `~/iiq-lab-evidence/sandbox/233/`:

- Runbook text  
- Clean-run Task Result list / screenshot  
- Orphan before + correlated after  

## If it fails

| Symptom | Fix |
| --- | --- |
| Orphan never correlates after HR | Correlation rule (214) key missing — check `employeeNumber` / `userId` both sides |
| Task Schedule missing | App was only aggregated ad hoc — create Account Aggregation task, then schedule |
| Parallel “works fine” | Lab data is small; still treat order as a correctness rule |
| Wrong IdP in runbook | Match `MNB-Keycloak-IdP` vs `MNB-Okta` to what Lessons 216–217 actually use |
| Re-ran failed job; error “gone” | You masked it — open prior TaskResult / host logs before re-run |
| Delta “fast” but disables missing | Schedule a periodic **full** reconcile; don’t trust watermark alone |

## You are done when

- [ ] Runbook executed clean once  
- [ ] Orphan reproduced and fixed by HR-first order  
- [ ] Recurring schedules exist for apps that were manual-only  

## Control note

- **Control:** Aggregation sequencing / orphan-account prevention  
- **Owner:** IAM Operations  
- **SLA (lab):** Nightly sequence via Task Schedule, not tribal memory  
- **Evidence:** `~/iiq-lab-evidence/sandbox/233/` — runbook, clean-run proof, orphan before/after  

## Quick check

1. What must aggregate before any target? → HCM (`MNB-Workday`)  
2. What does an orphan look like? → Native account, uncorrelated, no linked Identity  
3. Why refresh twice? → Promote HR attrs before correlation; promote entitlements after  
4. Which IdP app belongs in *your* runbook? → The one birthright/Portal actually uses (`MNB-Keycloak-IdP` and/or `MNB-Okta`)  
5. Full vs delta — what’s the completeness trap on delta? → Watermark can hide disables; need periodic full reconcile  
6. What do you read before re-running a failed task? → TaskResult (counters + first error stack)  

## Feedback

Could you recite the runbook from memory in under 30 seconds? If the orphan never appeared, note whether a target native account existed before Workday — without a target row, Task 5 can’t teach the symptom. If two refreshes overlapped and “mostly worked,” note it — classic 08 still forbids that in prod.

## Navigate

- Previous: [Lesson 232](232-email-templates-live.md)
- Next: [Lesson 234](234-ad-groups-ous-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
