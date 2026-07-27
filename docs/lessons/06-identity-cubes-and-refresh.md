# Lesson 06 — Identity Cubes & Refresh

| Field | Value |
| --- | --- |
| **Level** | Beginner |
| **Track** | Foundations |
| **Time** | 60–75 minutes |
| **Prereq** | Lesson 05 (HR schema mapped) |
| **Lab data** | `~/iiq-lab-data/HRApplications.txt` |

## Learning objectives

You will be able to:

- Inspect a full identity cube and inventory its major tabs
- Create Identity Refresh task `Refresh MNB Identities`
- Enable intentional refresh options (manager, roles, policy—as available)
- Run the pipeline Aggregate → Refresh and capture evidence
- Prove a file change (`onLeave`) appears on the cube after re-aggregate + refresh

## Why this matters

Aggregation loads accounts; refresh recalculates the person. Without refresh, managers, detected roles, and policy state lag HR reality—Meridian would walk into Monday’s ops meeting with stale cubes.

**Control / audit:** Task order is itself a control: HR aggregate then identity refresh. Examiners ask whether identity state is recalculated after HR loads and whether results are monitored. Your task results are the evidence.

## Concepts

| Process | Does | Does not |
| --- | --- | --- |
| **Account Aggregation** | Reads connector data into accounts/links | Fully recalculate role/policy/manager outcomes |
| **Identity Refresh** | Re-evaluates correlations, manager links, role assignment, optional policy checks | Replace the need to aggregate source apps |

```text
  Aggregate MNB-HR
        |
        v
  Accounts on cubes updated
        |
        v
  Refresh MNB Identities
        |
        v
  Manager links / attrs / roles / policies recalculated
```

**Production-like discipline:** Schedule refresh after aggregations. Too many refresh checkboxes on a large tenant = long runtimes—enable only what you need.

**SLA (lab):** Manual run after config changes. **SLA (prod target):** Nightly pipeline before business day (see Lesson 08).

## Before you start

- [ ] `Aggregate MNB-HR` succeeds
- [ ] Attribute maps from Lesson 05 saved
- [ ] Evidence folder ready
- [ ] Backup of `HRApplications.txt` before change-detect drill

## Lab procedure

### Task 1 — Cube deep-dive

1. Open identity `christopher.hayes` (MNB00002, Director of Technology).
2. Inventory tabs: attributes, accounts, roles/bundles, work items, risk/history (as present).
3. Note which attributes already show HR-sourced values vs still empty.
4. Optionally open `helen.ross` for a second leadership cube.

**Expected result:** Notebook checklist of cube tabs + which HR fields are visible pre-refresh.

### Task 2 — Create Refresh MNB Identities

1. **Tasks** → New Task → type **Identity Refresh** (or equivalent).
2. Name: `Refresh MNB Identities`.
3. Scope: if your UI supports filtering to identities that have an account on `MNB-HR`, use it; else refresh all (lab headcount is small).
4. Save.

**Expected result:** Task definition `Refresh MNB Identities` exists and is selectable under Tasks.

### Task 3 — Enable useful options

1. Edit `Refresh MNB Identities`.
2. Enable options you understand, for example (labels vary by version):
   - Refresh manager correlation / promote manager
   - Refresh assigned / detected roles (if present)
   - Refresh identity attributes from accounts
   - Check policies (optional in early labs—note cost)
3. Document every checkbox you enabled in the notebook.
4. Save.

**Expected result:** Written option list. No mystery toggles—“I don’t know what this does” stays unchecked.

### Task 4 — Run the pipeline

1. Run `Aggregate MNB-HR` → wait for Success.
2. Run `Refresh MNB Identities` → wait for Success.
3. Screenshot both task results into `~/iiq-lab-evidence/YYYY-MM-DD/`.
4. Re-open `priya.wire` and confirm manager/attributes look more complete than Task 1.

**Expected result:** Two successful task results; at least one identity shows improved manager or attribute promotion.

**If it fails:** Read refresh task errors first (rule exceptions, missing manager targets). Fix data/maps; do not blindly re-run in a loop without reading results.

### Task 5 — Change-detect drill

1. Backup:

```bash
cp ~/iiq-lab-data/HRApplications.txt ~/iiq-lab-data/HRApplications.txt.bak
```

2. Pick an active employee currently `onLeave=false` (e.g. `amelia.brooks` MNB00097). Flip `onLeave` to `true` in the HR file (careful CSV edit).
3. Run `Aggregate MNB-HR`, then `Refresh MNB Identities`.
4. Open the cube; confirm `onLeave` (or mapped identity attribute) reflects `true`.
5. Restore from `.bak` and re-run aggregate + refresh so the rest of the curriculum stays clean.

**Expected result:** Before/after note + screenshots proving refresh propagates HR changes. File restored.

### Task 6 — Scheduling awareness (no overnight requirement)

1. Open schedule settings on `Refresh MNB Identities`.
2. Observe how daily/cron-style schedules are configured in your UI.
3. Optionally set a daily time, save, then **disable** the schedule again if you do not want laptop overnight runs.
4. Note: full scheduling discipline is Lesson 08.

**Expected result:** You can explain where schedules live; lab schedule left disabled unless you intentionally keep it.

### Task 7 — Cube comparison after refresh

1. Compare three cubes side by side in notes:

| Identity | Focus after refresh |
| --- | --- |
| priya.wire | manager → rachel.evans; dept TRS |
| samir.hassan | inactive/terminated signals |
| sofia.torres | onLeave promoted |

2. Confirm leadership cubes (`helen.ross`, `christopher.hayes`) still look healthy (no accidental inactivation).
3. File a one-line SLA note: “After any HR file edit in lab, always Aggregate MNB-HR then Refresh MNB Identities before trusting cube state.”

**Expected result:** Comparison table complete; no unexpected identity corruption; SLA note in CHANGELOG.

## Acceptance criteria

- [ ] Cube deep-dive notes for `christopher.hayes` complete
- [ ] `Refresh MNB Identities` created
- [ ] Refresh options documented
- [ ] Aggregate → Refresh pipeline run with evidence screenshots
- [ ] Change-detect drill completed and HR file restored
- [ ] Three-persona comparison table complete
- [ ] CHANGELOG updated

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Refresh success but attrs stale | Options not enabled / wrong filter | Enable attribute refresh; widen scope |
| Manager still blank | Manager identity missing or id mismatch | Confirm managerId exists as employeeId in HR |
| Refresh very slow | Too many options / full pop | Disable policy check for early labs |
| Change not visible | Edited wrong file copy | Confirm IIQ path matches edited absolute path |
| Restore forgotten | Skipped bak restore | Restore `.bak` immediately; re-aggregate |

## Training binder evidence

- Screenshots: Aggregate + Refresh task results
- Screenshot: `priya.wire` manager/attributes after refresh
- Before/after `onLeave` screenshots (then restored)
- Option checklist for `Refresh MNB Identities`

**Examiner question:** “Show the job that recalculates identities after HR aggregation and its last success.”

## Knowledge check

1. Aggregation vs refresh in one sentence each?
2. Why run refresh after HR aggregate?
3. What is dangerous about refreshing “everything” with all options in prod?
4. What task name does this curriculum use for refresh?
5. Why restore the HR file after the onLeave drill?

### Answers

1. Aggregation reads accounts from connectors; refresh recalculates identity-level outcomes (manager, roles, policies, promoted attrs).
2. New/updated HR accounts must be recalculated into person state before roles/certs trust the cube.
3. Long runtimes, lock contention, overlapping jobs, unexpected policy storms—scope and options must be intentional.
4. `Refresh MNB Identities`.
5. So later lessons see the intended baseline personas (amelia not stuck on leave).

## Stretch lab

- Schedule `Refresh MNB Identities` daily at 02:00, verify the schedule object, then disable it.
- Compare task duration with policy checking on vs off.
- From Debug, note `lastRefresh` (or equivalent) timestamps on an Identity XML.

## Summary

- Cubes are the operational person record; refresh is the calculation engine.
- Meridian pipeline pattern: `Aggregate MNB-HR` then `Refresh MNB Identities`.
- Change-detect drills prove evidence that ops and examiners expect.

---

**Previous:** [Lesson 05 — HR Schema & Identity Attribute Design](05-hr-schema-and-identity-attrs.md)  
**Next:** [Lesson 07 — Populations & Identity Selectors](07-populations-and-selectors.md)
