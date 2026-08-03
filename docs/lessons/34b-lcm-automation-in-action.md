# Lesson 34b — LCM Automation in Action

**Level:** Intermediate  
**Track:** Lifecycle  
**Time:** 75–90 minutes  
**Prereq:** Lessons 29–34 (JML control stories); Lesson 29b design cards helpful; **`init-lcm.xml` imported** ([LOCAL_SETUP.md](../LOCAL_SETUP.md))  
**Lab data:** Scenario runners under `lab-data/scenarios/`; personas `nina.joiner`, `priya.wire`, `jordan.reed`, `sofia.torres`, `raj.external`  
**Path:** Core (01–50) — practical LCM bridge before mid-34

---

> **Verify:** Lab lesson — configure Meridian `MNB-LE-*` lifecycle events, prove LCM workflows exist, fire at least one Joiner/Leaver path and capture evidence. Soft-fails until you finish Tasks 3–7.

## Learning objectives

You will be able to:

- Import / confirm Lifecycle Manager objects and locate OOTB JML workflows in IIQ
- Create **Meridian-named Lifecycle Events** (`IdentityTrigger`) for Joiner, Mover, Leaver, LoA, and contractor end
- Wire each event to the matching OOTB (or Rapid Setup) workflow — without editing OOTB in place
- Drive a real event: HR delta → Aggregate → Refresh → workflow / work item evidence
- Manually launch a JML workflow for testing (UI or toolkit) when you need a controlled dry run
- Keep **rapid offboard** (Lesson 34) as disable-first, then reconcile into the Leaver automation path

---

## Why this matters

**Business.** Lessons 29–34 proved the control story with file deltas and operator refresh. Production Meridian still needs **automation**: when HR creates Nina, when Priya’s jobCode flips, when Jordan terminates, when Sofia goes LOA — something must start without an engineer clicking Aggregate by hand every time. That “something” is Lifecycle Events + LCM workflows.

**Control / audit.** Examiners accept file+refresh labs for training, then ask: *Show the Joiner event, the workflow name, and a Task Result / WorkflowCase for a real hire.* This lesson is that demo — implement the cards from 29b, fire them, screenshot the trail.

---

## Concepts

### Two layers you already know — now connected

| Layer | What Lessons 29–34 taught | What this lesson adds |
| --- | --- | --- |
| **Business event** | HR row change via `apply-*.sh` | Same — HR remains authoritative |
| **Operator pipeline** | Aggregate MNB-HR → Refresh | Still required for attribute detection |
| **Automation** | Stretch / paper only (29b) | **Lifecycle Event → Workflow launch** |
| **Emergency** | Rapid offboard (34) | Still disable-first; then HR + Leaver event |

```
HR delta (authoritative)
        │
        ▼
Account Aggregation (MNB-HR)
        │
        ▼
Identity Refresh (attrs + roles)
        │
        ├── Attribute / create detection
        │         │
        │         ▼
        │   IdentityTrigger (MNB-LE-*)
        │         │
        │         ▼
        │   Workflow (Lifecycle Event - Joiner|Mover|Leaver|…)
        │         │
        │         ├── Work items / notifications
        │         └── Provisioning / disable subprocesses
        │
        └── Birthright / role assignment (still from Refresh rules)
```

### Lifecycle Event types you will build

| Meridian event | Trigger type | Typical attribute / signal | Persona | Workflow target (OOTB name) |
| --- | --- | --- | --- | --- |
| `MNB-LE-Joiner-HR` | Create | New identity / HR account create | `nina.joiner` | `Lifecycle Event - Joiner` or `RapidSetup - Joiner` |
| `MNB-LE-Mover-Job` | AttributeChange | `jobCode` (or `departmentName`) | `priya.wire` | `Lifecycle Event - Manager Transfer` / RapidSetup Mover |
| `MNB-LE-Leaver-Terminate` | AttributeChange | `inactive` false→true | `jordan.reed` | `Lifecycle Event - Leaver` |
| `MNB-LE-LoA-Freeze` | AttributeChange | `exceptions` → contains `LOA` | `sofia.torres` | Custom / Reinstate-style clone later; **not** Leaver |
| `MNB-LE-Contractor-End` | AttributeChange | end date / `inactive` for contractors | `raj.external` | Leaver (or dedicated contractor workflow) |

**IIQ term:** An **IdentityTrigger** (Lifecycle Event) watches for Create, AttributeChange, ManagerTransfer, etc., and hands off to a **Workflow** via `WorkflowTriggerHandler`. Rapid Setup is SailPoint’s packaged UI over the same idea.

### Wrong way

1. Edit OOTB `Lifecycle Event - Joiner` in place (upgrade wipe — Lesson 93 deepens this).  
2. Point LoA at the Leaver workflow (Sofia gets terminated treatment).  
3. Skip HR and “just launch Joiner” forever — demos without authoritative signal fail exams.  
4. Wait for an access-request approval to stop Jordan or Marcus (Lessons 31/34).

---

## How it works

| Stage | Object / action | What you prove |
| --- | --- | --- |
| LCM present | `init-lcm.xml` imported | Workflows `Lifecycle Event - *` searchable |
| Event configured | `IdentityTrigger` named `MNB-LE-*` | Type + workflow name + attribute |
| Signal | Scenario runner + Aggregate + Refresh | Cube attrs match delta |
| Automation | WorkflowCase / Task Result | Launch id, status, work item |
| Evidence | Screenshots + binder | Examiner can replay the trail |

**Production reality:** Live banks often use Workday (or similar) → aggregation → triggers. This lab keeps delimited HR so you can *see* every column flip; the IdentityTrigger + Workflow pattern is what you keep when the connector changes (Lesson 77+).

---

## Before you start

- [ ] IIQ at `http://localhost:8080/identityiq` as `spadmin`
- [ ] **`init-lcm.xml` imported** (iiq console: `import init-lcm.xml`) — required for this lesson
- [ ] Lessons 29–34 personas available (or re-run scenario scripts)
- [ ] Backup `~/iiq-lab-data/HRApplications.txt` (or Docker `/opt/iiq-lab-data/…`)
- [ ] Lesson 29b event cards nearby (or use the tables in this lesson)
- [ ] Shared lab: create **disabled** drafts first; enable only when you are ready to fire one test

---

## Lab procedure

### Task 1 — Prove LCM workflows exist

Without workflows, events have nowhere to go. Inventory before you configure.

1. In IIQ, open **Debug** → **Object Browser** (or Setup → Lifecycle Events / Rapid Setup — labels vary).
2. Search Workflows for names containing `Lifecycle Event` or `RapidSetup`.
3. Record which of these exist in your lab:

| Expected name | Present? |
| --- | --- |
| `Lifecycle Event - Joiner` | |
| `Lifecycle Event - Leaver` | |
| `Lifecycle Event - Manager Transfer` (or Mover) | |
| `Lifecycle Event - Reinstate` | |
| `RapidSetup - Joiner` / `Leaver` / `Mover` | |

4. If **none** exist: stop and import `init-lcm.xml`, then restart / recheck. Do not invent workflow XML in a shared lab.

**Expected result:** At least Joiner + Leaver workflows listed. Binder note: “LCM present; workflow names = …”

**If it fails:** Re-run `import init-lcm.xml` via iiq console per [LOCAL_SETUP.md](../LOCAL_SETUP.md); confirm license/feature notes with instructor for non-lab installs.

### Task 2 — Inventory existing Lifecycle Events

1. Navigate to **Lifecycle Events** (or Debug → IdentityTrigger).
2. List any stock Joiner / Leaver / Reinstate triggers (often from `init-lcm.xml`).
3. Decide: you will **add Meridian `MNB-LE-*` triggers** rather than silently renaming OOTB. Leave OOTB as reference; disable overlapping stock events if they would double-fire in your personal lab.

**Expected result:** Written inventory: stock vs planned `MNB-LE-*`.

### Task 3 — Build `MNB-LE-Joiner-HR` (Nina)

Wire the Lesson 29 joiner into real automation.

1. Create Lifecycle Event:
   - **Name:** `MNB-LE-Joiner-HR`
   - **Type:** Create (new identity / authoritative create — match your UI options)
   - **Workflow:** `Lifecycle Event - Joiner` or `RapidSetup - Joiner` (whichever Task 1 found)
   - **Description:** `Meridian joiner from MNB-HR; birthright via Refresh; no Wire/AWS`
2. Start **inactive / disabled** if the UI allows — enable only for the fire test.
3. Binder: paste the event card (name, type, workflow, non-actions).

**Expected result:** `MNB-LE-Joiner-HR` saved and visible in the event list.

**If it fails:** Use Debug to create IdentityTrigger; handler `sailpoint.api.WorkflowTriggerHandler`; handler parameter `workflow` = chosen workflow name.

### Task 4 — Build mover, leaver, LoA, contractor events

Implement the rest of the 29–34 story as triggers. Prefer AttributeChange with explicit attribute names from the bank HR map.

1. **`MNB-LE-Mover-Job`**
   - Type: AttributeChange  
   - Attribute: `jobCode` (or `departmentName` if your cube map uses that)  
   - Workflow: Mover / Manager Transfer workflow from Task 1  
   - Description: Priya-style residual review; do not grant Wire on RM  
2. **`MNB-LE-Leaver-Terminate`**
   - Type: AttributeChange  
   - Attribute: `inactive` (new value true / Terminated path per your map)  
   - Workflow: `Lifecycle Event - Leaver`  
   - Description: Jordan Sev-1; directory + privileged residuals  
3. **`MNB-LE-LoA-Freeze`**
   - Type: AttributeChange  
   - Attribute: `exceptions`  
   - Workflow: **Do not use Leaver.** If no freeze workflow exists, point to a **disabled** draft that creates a manager work item only, or document “custom workflow required — use Reinstate/custom later (Lesson 93).”  
   - Description: Sofia freeze ≠ terminate  
4. **`MNB-LE-Contractor-End`**
   - Type: AttributeChange on inactive/end for `employeeType=Contractor` (rule filter if UI supports; else document “population + leaver”)  
   - Workflow: Leaver (or note dedicated contractor path)  
   - Description: `raj.external` AWS_ADMIN same-day  

**Expected result:** Four additional `MNB-LE-*` objects (LoA may be design-only if no safe workflow — say so honestly in the binder).

**If it fails:** Create what the UI allows; remaining events as Debug IdentityTrigger XML export for Lesson 101 later.

### Task 5 — Fire Joiner end-to-end (see it work)

This is the money shot: delta → pipeline → event → evidence.

```bash
./tools/lab/scripts/scenarios/apply-joiner.sh
```

1. Enable `MNB-LE-Joiner-HR` if it was disabled.
2. Run **Account Aggregation** for **MNB-HR**.
3. Run **Refresh MNB Identities** (or Attributes + Roles split tasks) so create/attribute detection can run.
4. Open **Debug → WorkflowCase** / Task Results / IdentityRequest (labels vary). Search for launches tied to Nina or `Lifecycle Event - Joiner`.
5. Open `nina.joiner`: confirm birthright still correct (**no** Wire/AWS packs) — automation must not over-grant.
6. If a manager work item appeared for `emily.bennett`, screenshot it (Lesson 36b will deepen approver craft).

**Expected result:** Evidence pack: HR runner + aggregation Task Result + WorkflowCase/Task Result for Joiner + Nina roles screenshot.

**If it fails:**  
- Event never fired → confirm Create trigger fires on *new* identities; if Nina already existed, use a disposable hire (`apply-batch-hire.sh` → `leo.batch`) or delete/recreate carefully in a personal lab.  
- Workflow 404 → Task 1 names wrong; fix event workflow reference.  
- Double work items → disable stock Joiner trigger temporarily.

### Task 6 — Fire Leaver (or dry-run launch)

Prove Lesson 31 automation without waiting on an examiner tabletop.

**Path A — Attribute-driven (preferred):**

```bash
./tools/lab/scripts/scenarios/apply-leaver.sh
```

1. Aggregate MNB-HR → Refresh.  
2. Confirm `jordan.reed` inactive signals.  
3. Confirm `MNB-LE-Leaver-Terminate` produced a WorkflowCase / Task Result.  
4. Residual inventory still required (`SAP_FI`, `AWS_ADMIN`) — the event starts the process; you still prove disposition.

**Path B — Controlled manual launch (when you cannot re-terminate Jordan):**

1. Lifecycle Manager / Rapid Setup UI: launch Joiner/Leaver for a **test** identity, **or**  
2. Toolkit / MCP (if available in your lab): `run_jml_event` with `event=leaver`, `identity=…`, `dry_run=true` first, then live.  
3. Record launch id / status in the binder.

**Expected result:** One successful Leaver (or dry-run) launch artifact with timestamp.

**If it fails:** File-driven inactive on cube is still valid control evidence — note “trigger misconfigured; operator leaver path used” and fix the AttributeChange filters.

### Task 7 — Mover + LoA contrast drill (15 minutes)

Do not skip the distinction that fails exams.

1. Re-read Priya BEFORE/AFTER from Lesson 30. Ensure `MNB-LE-Mover-Job` would fire on `jobCode` change — fire only if you can restore HR from `.bak-*` afterward.  
2. For Sofia: confirm `exceptions=LOA` would **not** satisfy `MNB-LE-Leaver-Terminate`. Write one binder sentence: *“LoA must never share the Leaver workflow.”*  
3. Optional: `./tools/lab/scripts/scenarios/apply-loa.sh` + Refresh; prove freeze population / work item path without terminationDate.

**Expected result:** Side-by-side note: Mover residual hunt vs LoA freeze vs Leaver disable.

### Task 8 — Rapid offboard ↔ LCM reconcile map

Lesson 34 disables first. Automation must not become a bottleneck.

1. Draw the reconcile loop in your binder:

```text
SOC urgent disable (Marcus)
        │
        ▼
Directory + Wire dead (minutes)
        │
        ▼
HR reconcile ticket → inactive=true
        │
        ▼
Aggregate + Refresh → MNB-LE-Leaver-Terminate
        │
        ▼
Workflow completes residual / audit trail
```

2. State explicitly: **do not wait** for `MNB-LE-Leaver-Terminate` before emergency disable.

**Expected result:** One-page reconcile map linking Lesson 34 runbook to this lesson’s Leaver event.

### Task 9 — Evidence pack & optional export

1. Screenshots: event list (`MNB-LE-*`), one WorkflowCase, Nina/Jordan outcomes, LoA≠Leaver note.  
2. Optional bank craft: export IdentityTriggers to `config/IdentityTrigger/MNB-LE-*.xml` for Lesson 101 promotion practice.  
3. Disable noisy test events in shared labs before you leave.

**Expected result:** Examiner-ready automation evidence; shared lab left quiet.

---

## Acceptance criteria

- [ ] `init-lcm.xml` confirmed; Joiner + Leaver workflows found
- [ ] `MNB-LE-Joiner-HR` and `MNB-LE-Leaver-Terminate` created (mover/LoA/contractor created or honestly documented)
- [ ] At least one Joiner **or** Leaver path fired with WorkflowCase / Task Result evidence
- [ ] Nina (or batch hire) birthright still excludes Wire/AWS
- [ ] Written LoA ≠ Leaver and rapid-offboard reconcile map
- [ ] Shared-lab events disabled or scoped after testing

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No Lifecycle Event UI | LCM not imported | `import init-lcm.xml` |
| Event saved, never fires | Wrong type; identity already existed | Use Create on new hire; or AttributeChange with real attr flip |
| `workflow_not_found` on toolkit launch | RapidSetup names missing | Point event at `Lifecycle Event - *` names from Task 1 |
| Double workflows | Stock + MNB-LE both active | Disable one set |
| Sofia terminated | LoA pointed at Leaver | Retarget; restore HR from backup |
| Birthright missing after Joiner WF | Refresh roles not run | Run Refresh MNB Roles; event ≠ birthright engine |

---

## Training binder evidence

1. Workflow inventory table (Task 1)  
2. Screenshots of `MNB-LE-*` events  
3. Joiner and/or Leaver WorkflowCase / Task Result  
4. Persona screenshots (Nina birthright; Jordan inactive; Sofia LOA)  
5. Rapid offboard reconcile diagram  
6. Optional IdentityTrigger XML export paths  

**Control owner:** IAM Operations + IAM Governance  
**Examiner question:** “Show a hire where HR create triggered a Joiner workflow — and prove privileged access was still not automatic.”

---

## Knowledge check

1. What remains Meridian’s authoritative joiner signal even after you add Lifecycle Events?  
2. Why create `MNB-LE-*` instead of editing OOTB Joiner in place?  
3. Which attribute should drive `MNB-LE-Leaver-Terminate` in this lab?  
4. Why must LoA not use the Leaver workflow?  
5. In a rapid offboard, what happens before `MNB-LE-Leaver-Terminate`?  
6. Does a Joiner workflow replace birthright role assignment on Refresh?

### Answers

1. New/updated row on authoritative MNB-HR (scenario runner / HCM), then Aggregate.  
2. Upgrades overwrite OOTB; Meridian needs named, auditable clones/triggers.  
3. `inactive` (false→true) / terminated status — not `exceptions=LOA`.  
4. Employment continues; freeze keeps the cube and expects return — Leaver deprovisions.  
5. Emergency disable of directory/payments; HR reconcile later triggers the Leaver event.  
6. No — birthright still comes from role assignment on Refresh; the event orchestrates work items/provisioning around that control.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “Lifecycle Events” and “IdentityTrigger.”  
- [SailPoint Community](https://community.sailpoint.com/) — search “Rapid Setup Joiner” for packaged workflow names.  
- [Lesson 29b](29b-lifecycle-events-rapid-setup.md) — design cards this lesson implements.  
- [Lesson 93 — LCM Workflow Customization](93-workflow-lcm-customization.md) — clone/version workflows after Core Path.  
- [NIST SP 800-53 AC-2](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) — account management automation still needs authorized process + evidence.

---

## Stretch lab

- Enable mover event and re-apply Priya’s delta; capture residual `WIRE_INIT` work item automation.  
- Use toolkit `list_lifecycle_events` / `upsert_lifecycle_event` to show API parity with the UI.  
- Draft `MNB-WF-LoA-Freeze` clone requirements for Lesson 93 (disable ELDAP, notify `sanjay.kapoor`, no terminationDate).

---

## Summary

- You turned Lessons 29–34 from operator-driven demos into **configured Lifecycle Events** with real workflow launches.  
- HR deltas remain the source of truth; Aggregate → Refresh → IdentityTrigger is the automation path.  
- LoA, Leaver, and rapid offboard stay separate plays — automation serves them, it does not blur them.

---

**Previous:** [Lesson 34 — Rapid Offboarding Drill](34-rapid-offboarding-drill.md)  
**Next:** [Mid-capstone — JML](mid-34-jml-capstone.md) · [Lesson 35 — Access Request Catalog](35-access-request-catalog.md)
