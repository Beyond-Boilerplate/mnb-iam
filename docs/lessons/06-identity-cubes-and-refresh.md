# Lesson 06 — Identity Cubes & Refresh

| Field | Value |
| --- | --- |
| **Level** | Beginner |
| **Track** | Foundations |
| **Time** | 75–90 minutes |
| **Prereq** | Lesson 05 (HR schema mapped) |
| **Lab data** | `~/iiq-lab-data/HRApplications.txt` |

## Learning objectives

You will be able to:

- Inspect a full identity cube and inventory its major tabs
- Explain each major **Identity Refresh** option and when Meridian turns it on
- Create **separate** purpose-built refresh tasks (attributes, managers, roles, optional policy)
- Run the pipeline `Aggregate MNB-HR` → `Refresh MNB Attributes` (and managers) to promote HR Link data onto cubes
- Prove a file change (`exceptions` (LOA)) appears on the cube after re-aggregate + attribute refresh

## Why this matters

Aggregation loads accounts; refresh recalculates the person. Without the right refresh after HR aggregation, identity attributes stay blank, managers stay unresolved, and roles/policies lag—Meridian would walk into Monday’s ops meeting with stale cubes.

**Control / audit:** Task order and *which* refresh options you enable are themselves controls. Examiners ask whether identity state is recalculated after HR loads, and whether you run one overloaded “refresh everything” job or purpose-scoped tasks that ops can schedule and debug. Your task results are the evidence.

## Concepts

| Process | Does | Does not |
| --- | --- | --- |
| **Account Aggregation** | Reads connector data into accounts/links; with authoritative `MNB-HR`, creates/updates identities | Fully promote attrs, resolve managers, assign roles, or check policies |
| **Identity Refresh** | Re-evaluates selected cube outcomes based on **options you enable** | Replace the need to aggregate source apps |

**Why separate refresh tasks?** One Identity Refresh definition with every checkbox enabled is slow, hard to schedule, and opaque when it fails. Meridian creates **purpose-built** tasks so each nightly (or on-demand) job has one job:

| Task name | Purpose | Typical options ON |
| --- | --- | --- |
| `Refresh MNB Attributes` | Promote/update identity attrs from HR Link after aggregation | Refresh identity attributes from accounts |
| `Refresh MNB Managers` | Resolve `managersAssociateID` → manager Identity | Refresh manager / manager correlation |
| `Refresh MNB Roles` | Recalculate assigned/detected roles (later lessons) | Refresh assigned / detected roles |
| `Refresh MNB Policies` *(optional early)* | Evaluate policy violations | Check active policies |

Keep a broad lab helper `Refresh MNB Identities` only if you want a “run all for demos” shortcut—**do not** schedule it as the only production-like pattern. Ops prefers the purpose-built set.

### Identity Refresh options (define before you click)

Labels vary slightly by IIQ version; meanings do not. Enable only options you can explain.

| Option (typical label) | What it does | When Meridian uses it | Cost |
| --- | --- | --- | --- |
| **Refresh identity attributes** / promote attributes from accounts | Copies mapped Link fields onto the Identity | **Always after `Aggregate MNB-HR`** (and after map changes) | Moderate |
| **Refresh manager** / manager correlation | Resolves manager references (`managersAssociateID` → manager cube) | After HR manager changes; hierarchy certs/approvals | Moderate |
| **Refresh assigned / detected roles** | Re-evaluates birthright and detection | After role model changes (Lessons 23+) | Higher |
| **Check active policies** / process policy violations | Evaluates SoD and other policies | After policy edits (Lessons 39+); not needed every early-lab run | Higher |
| **Refresh entitlements / needs refresh** *(if present)* | Marks or recalculates entitlement-related state | When entitlement catalogs or assignment flags change | Moderate–high |
| **Provision / synchronize attributes** *(if present)* | Pushes identity changes outbound | Only when attribute sync is designed (Lesson 22+)—leave off until then | High / side-effecting |
| **Filter / population scope** | Limits which identities the task touches | Prefer `MNB-Active-Employees` once Lesson 07 exists | Lowers cost |

```text
  Aggregate MNB-HR
        |
        v
  Accounts / Links on cubes updated (raw HR truth)
        |
        +-----> Refresh MNB Attributes  --> identity attrs current
        +-----> Refresh MNB Managers    --> manager links resolved
        +-----> Refresh MNB Roles       --> (when roles exist)
        +-----> Refresh MNB Policies    --> (when policies exist)
```

**Production-like discipline:** Schedule attribute (and usually manager) refresh **immediately after** HR aggregation. Do not enable every checkbox on one task “just in case.”

**SLA (lab):** Manual run after config changes. **SLA (prod target):** Nightly pipeline before business day (see Lesson 08).

## How it works

**Account Aggregation** moves connector data onto Links. **Identity Refresh** recompiles only the cube-derived outcomes whose options are enabled. Running refresh without aggregating first recompiles stale inputs. Running aggregation without attribute refresh leaves promoted identity attributes stale even when the Link is correct.

```text
Aggregate MNB-HR  ──►  Links / raw attrs current
        │
        ▼
Refresh MNB Attributes (promote attrs from HR Link)
        │
        ▼
Refresh MNB Managers (optional same night / after hierarchy edits)
        │
        ├── Resolve manager references
        ├── (later) Refresh MNB Roles → assign/remove birthright
        └── (later) Refresh MNB Policies → SoD / policy flags
```

**Real-life Meridian example.** `priya.wire`’s `managersAssociateID` points at `rachel.evans`. Aggregation alone may leave department/`exceptions` (LOA) blank on the Identity and manager display unresolved. After `Refresh MNB Attributes`, org flags appear; after `Refresh MNB Managers`, Rachel appears as manager so wire certifications and approvals route correctly.

## Before you start

- [ ] `Aggregate MNB-HR` succeeds
- [ ] Attribute maps from Lesson 05 saved
- [ ] Evidence folder ready
- [ ] Backup of `HRApplications.txt` before change-detect drill

## Lab procedure

### Task 1 — Cube deep-dive

A cube is the examiner-facing unit of a person. Inventory one leadership cube end-to-end so you know which tabs prove attributes, accounts, and workflow state.

1. Open identity `christopher.hayes` (MNB00002, Director of Technology).
2. Inventory tabs: attributes, accounts, roles/bundles, work items, risk/history (as present).
3. Note which attributes already show HR-sourced values vs still empty (expected gaps before attribute refresh).
4. Optionally open `helen.ross` for a second leadership cube.

**Expected result:** Notebook checklist of cube tabs + which HR fields are visible pre-refresh.

### Task 2 — Option study (write before you click)

Before creating tasks, lock the meanings so you never enable mystery toggles.

1. Open any Identity Refresh task editor (or the new-task form) and list every option checkbox your version shows.
2. Map each checkbox to the definition table in Concepts. Mark unknowns as “leave OFF until documented.”
3. Decide Meridian’s purpose split:
   - Attributes → `Refresh MNB Attributes`
   - Managers → `Refresh MNB Managers`
   - Roles → `Refresh MNB Roles` (options off until roles exist—still create the shell)
   - Policies → `Refresh MNB Policies` (optional shell; leave schedule disabled)

**Expected result:** Written option dictionary in your notebook. No “I don’t know what this does” left checked.

### Task 3 — Create purpose-built refresh tasks (UI)

CD does not ship these. Create them now so every HR aggregate has a clear promote/manager path.

#### 3a — Refresh MNB Attributes *(required after every HR aggregate)*

1. **Tasks** → New Task → type **Identity Refresh**; name `Refresh MNB Attributes`.
2. Enable **only** refresh / promote identity attributes from accounts (manager/roles/policies/provisioning **off**).
3. Scope: all lab identities, or filter to identities with an account on `MNB-HR` if the UI allows.
4. Save. CHANGELOG: `created Refresh MNB Attributes`.

#### 3b — Refresh MNB Managers

1. Create `Refresh MNB Managers` with **only** manager correlation / refresh manager options.
2. Save. CHANGELOG: `created Refresh MNB Managers`.

#### 3c — Refresh MNB Roles *(shell for later)*

1. Create `Refresh MNB Roles` (assigned/detected role refresh when roles exist—Lesson 23+).
2. Leave unscheduled for early labs.

#### 3d — Refresh MNB Policies *(optional shell)*

1. Optionally create `Refresh MNB Policies` with policy-check options prepared but **not** scheduled early (cost).
2. Document the choice.

**Expected result:** At least `Refresh MNB Attributes` and `Refresh MNB Managers` exist as separate TaskDefinitions. Option lists documented per task.

**If it fails:** Some editions nest options under “advanced”—expand panels before assuming a checkbox is missing.

### Task 4 — Optional demo umbrella (do not schedule as primary)

1. Optionally create `Refresh MNB Identities` that enables attributes + managers (still avoid policy/provisioning in early labs).
2. Label it in CHANGELOG as **lab demo only**—nightly discipline in Lesson 08 uses the purpose-built tasks.
3. Prefer running the purpose-built pair for the rest of this lesson.

**Expected result:** You can explain why Meridian does not rely on one “refresh everything” job in production-like ops.

### Task 5 — Run the pipeline (HR aggregate → attribute refresh → managers)

This is the control sequence after any HR feed change.

1. Run `Aggregate MNB-HR` → wait for Success.
2. Run **`Refresh MNB Attributes`** → wait for Success. This is the task that **promotes/updates identity attributes from the HR Link**.
3. Run **`Refresh MNB Managers`** → wait for Success.
4. Screenshot all three task results into `~/iiq-lab-evidence/YYYY-MM-DD/`.
5. Re-open `priya.wire` and confirm department/job/`exceptions` (LOA) (as mapped) and manager toward `rachel.evans`.

**Expected result:** Three successful task results; at least one identity shows promoted attributes and a resolved manager.

**If it fails:** Read the failing task’s errors first (rule exceptions, missing manager targets). Fix data/maps; do not blindly re-run in a loop without reading results.

### Task 6 — Change-detect drill

1. Backup:

```bash
cp ~/iiq-lab-data/HRApplications.txt ~/iiq-lab-data/HRApplications.txt.bak
```

2. Pick an active employee currently without LOA (e.g. `amelia.brooks` MNB00097). Set `exceptions` to `LOA` in the HR file (careful **CSV** edit—comma delimiter, preserve header; leave `inactive=false`).
3. Run `Aggregate MNB-HR`, then **`Refresh MNB Attributes`** (managers optional if hierarchy unchanged).
4. Open the cube; confirm `exceptions` (or mapped identity attribute) reflects `LOA`.
5. Restore from `.bak` and re-run aggregate + `Refresh MNB Attributes` so the rest of the curriculum stays clean.

**Expected result:** Before/after note + screenshots proving attribute refresh propagates HR changes. File restored.

### Task 7 — Scheduling awareness (no overnight requirement)

1. Open schedule settings on `Refresh MNB Attributes`.
2. Observe how daily/cron-style schedules are configured in your UI.
3. Optionally set a daily time, save, then **disable** the schedule again if you do not want laptop overnight runs.
4. Note: full scheduling discipline and the nightly order (HR → apps → attrs → managers → roles) is Lesson 08.

**Expected result:** You can explain where schedules live; lab schedule left disabled unless you intentionally keep it.

### Task 8 — Cube comparison after refresh

1. Compare three cubes side by side in notes:

| Identity | Focus after refresh |
| --- | --- |
| priya.wire | manager → rachel.evans; dept TRS |
| samir.hassan | inactive/terminated signals |
| sofia.torres | exceptions=LOA promoted |

2. Confirm leadership cubes (`helen.ross`, `christopher.hayes`) still look healthy (no accidental inactivation).
3. File a one-line SLA note: “After any HR file edit in lab, always Aggregate MNB-HR → Refresh MNB Attributes (→ Refresh MNB Managers when hierarchy matters) before trusting cube state.”

**Expected result:** Comparison table complete; no unexpected identity corruption; SLA note in CHANGELOG.

## Acceptance criteria

- [ ] Cube deep-dive notes for `christopher.hayes` complete
- [ ] Identity Refresh options defined in notebook (table mapped to your UI labels)
- [ ] Separate tasks present: `Refresh MNB Attributes`, `Refresh MNB Managers` (plus roles/policy shells) — works in IIQ; optional UI+export to `config/TaskDefinition/`
- [ ] Aggregate → Attributes → Managers pipeline run with evidence screenshots
- [ ] Change-detect drill completed and HR file restored
- [ ] Three-persona comparison table complete
- [ ] CHANGELOG updated

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Refresh success but attrs stale | Attribute option off / wrong task | Run `Refresh MNB Attributes` with promote-attrs enabled |
| Manager still blank | Ran attrs-only; manager task not run | Run `Refresh MNB Managers`; confirm managersAssociateID exists as userId |
| Refresh very slow | Too many options on one task | Split tasks; disable policy check for early labs |
| Change not visible | Edited wrong file copy | Confirm IIQ path matches edited absolute path |
| Restore forgotten | Skipped bak restore | Restore `.bak` immediately; re-aggregate + attrs refresh |
| Mystery checkbox enabled | Skipped Task 2 | Disable unknown options; re-document |

## Training binder evidence

- Screenshots: Aggregate + `Refresh MNB Attributes` + `Refresh MNB Managers` task results
- Screenshot: `priya.wire` manager/attributes after refresh
- Before/after `exceptions` (LOA) screenshots (then restored)
- Option checklist per purpose-built task (not one mega-list)

**Examiner question:** “Show the job that recalculates identity attributes after HR aggregation and its last success—and explain why manager refresh is a separate task.”

## Knowledge check

1. Aggregation vs refresh in one sentence each?
2. Which Meridian task must run after HR aggregation to promote identity attributes from the HR Link?
3. Why create separate Identity Refresh tasks instead of one with all options?
4. Name two Identity Refresh options and what each does.
5. Why restore the HR file after the exceptions (LOA) drill?

### Answers

1. Aggregation reads accounts from connectors onto Links; refresh recalculates selected identity-level outcomes (attrs, manager, roles, policies) based on enabled options.
2. `Refresh MNB Attributes` (Identity Refresh with attribute promotion from accounts).
3. Faster scoped runs, clearer failures, safer scheduling, and no accidental policy/provisioning side effects on every HR load.
4. Examples: refresh identity attributes = promote Link fields to Identity; refresh manager = resolve manager references; check policies = evaluate SoD/policy state; refresh roles = re-evaluate assigned/detected roles.
5. So later lessons see the intended baseline personas (amelia not stuck on leave).

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “Identity Refresh” and “refresh identity attributes” for option meanings and performance guidance.
- [SailPoint Community](https://community.sailpoint.com/) — search “refresh vs aggregation” for ops patterns that avoid overlapping nightly jobs.
- [NIST SP 800-53 AC-2 / AU-6](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — maintaining current account state and reviewing automated processing outcomes.
- [FFIEC IT Examination Handbook — Architecture, Infrastructure, and Operations](https://ithandbook.ffiec.gov/it-booklets/architecture-infrastructure-and-operations.aspx) — batch job reliability and sequencing expectations for bank platforms.
- [CIS Controls v8 — Control 5 (Account Management)](https://www.cisecurity.org/controls/account-management) — keeping account inventories and ownership current.

## Stretch lab

- Schedule `Refresh MNB Attributes` daily at 02:00, verify the schedule object, then disable it.
- Compare task duration: attrs-only vs attrs+managers+policies on one combined run.
- From Debug, note `lastRefresh` (or equivalent) timestamps on an Identity XML.
- Point `Refresh MNB Attributes` at population `MNB-Active-Employees` after Lesson 07 and document the scope change.

## Summary

- Cubes are the operational person record; Identity Refresh options are the calculation knobs—define them before enabling them.
- Meridian uses purpose-built tasks you create in Lesson 06: after `Aggregate MNB-HR`, run **`Refresh MNB Attributes`**, then **`Refresh MNB Managers`**.
- Change-detect drills prove evidence that ops and examiners expect; bank craft exit is TaskDefinition XML under `config/`.

---

**Previous:** [Lesson 05 — HR Schema & Identity Attribute Design](05-hr-schema-and-identity-attrs.md)  
**Next:** [Lesson 07 — Populations & Identity Selectors](07-populations-and-selectors.md)
