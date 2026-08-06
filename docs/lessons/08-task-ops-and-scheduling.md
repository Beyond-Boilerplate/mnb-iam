# Lesson 08 — Task Operations & Scheduling Discipline

| Field | Value |
| --- | --- |
| **Level** | Beginner |
| **Track** | Foundations |
| **Time** | 45–60 minutes |
| **Prereq** | Lesson 07 |
| **Lab data** | Existing `MNB-*` tasks; upcoming `Aggregate MNB-IT-Access` (Lesson 09) |

## Learning objectives

You will be able to:

- Inventory Meridian tasks and state each one's purpose
- Define a nightly runbook order with HR first, then purpose-built refreshes
- Configure — then safely disable — a schedule on an attribute refresh task
- Read a task result for start time, duration, counters, and errors
- Write a five-line on-call checklist for aggregation failure

## Why this matters

Banks run IAM as a factory, and task order is an operational control, not a convenience. If IT aggregation runs before HR, new joiners get accounts with no identity to correlate against. If two refreshes overlap, you get lock contention and an opaque failure right before the business day opens. This lesson builds the muscle memory an on-call IAM engineer needs before a real incident, not during one.

**Control / audit:** Ops must show a documented job sequence, active schedules, monitored task results, and a written response for when aggregation fails. Today's runbook is the artifact you'd hand to a new on-call engineer.

## Concepts

**Meridian nightly order (target):**

```text
  1. Aggregate MNB-HR
  2. Aggregate MNB-IT-Access          (Lesson 09+)
  3. Aggregate platform apps          (Lessons 11–16)
  4. Refresh MNB Attributes           (promote Link → Identity after HR/apps)
  5. Refresh MNB Managers             (hierarchy; can follow attrs same night)
  6. Refresh MNB Roles                (when role model exists)
  7. Refresh MNB Policies / certs     (later lessons; never overlap refreshes)
```

| Why this order | Reason |
| --- | --- |
| HR first | Creates/updates people before accounts try to correlate |
| Apps next | Attach entitlements to existing identities |
| Attributes refresh after | Promote HR (and other) Link fields onto cubes |
| Managers after attrs | Hierarchy resolution needs current identity attrs |
| Roles / policies last | Depend on promoted attrs and memberships |
| Avoid overlap | Two refreshes at once risks contention and partial state |
| Purpose-built refreshes | Failures stay diagnosable; runtime cost stays predictable |

A **TaskDefinition** is what to run (an aggregation, a refresh, …). A **schedule** attaches cron-like timing to it. A **TaskResult** is the auditable record of what actually happened. Always read start/end time, host, success/fail, account/identity counters, and the first error stack **before** you re-run anything — re-running blind can mask the real root cause.

> **Watch out:** A single Identity Refresh task with every option enabled looks efficient but is slow to run and impossible to diagnose when it fails. Meridian keeps refreshes purpose-built — attributes, managers, roles, policies — as separate tasks with separate blast radii.

## How it works

Meridian's control narrative depends on ordered execution: HR → apps → attribute refresh → managers → roles → policy/certs. Skipping the order, or collapsing it into one mega task, is how banks get silent joiner delays and unexplained cert gaps.

```text
Schedule / Run Now
        │
        ▼
TaskDefinition (Aggregate MNB-HR, Refresh MNB Attributes, Refresh MNB Managers, …)
        │
        ▼
TaskResult (counters, errors, host, duration)
        │
        └── Evidence binder + on-call triage
```

| Ops rule | Why |
| --- | --- |
| HR before targets | People must exist before correlation |
| `Refresh MNB Attributes` after aggregates | Promotes Link → Identity, required after every HR/app load |
| Separate manager/role/policy refreshes | Scopes cost and blast radius |
| No overlapping refreshes | Avoids contention / partial state |
| Read TaskResult before re-run | Preserves the root cause instead of masking it |

**Real-life Meridian example.** If `Aggregate MNB-IT-Access` ran before HR on the night `nina.joiner` is added, her IT row could land with no identity to correlate against — and if that IT app were wrongly marked authoritative, IIQ could mint an **orphan identity** for her. Ordering and create-identities discipline (Lesson 09) are both controls, working together.

## Before you start

- [ ] `Aggregate MNB-HR`, `Refresh MNB Attributes`, and `Refresh MNB Managers` exist
- [ ] Populations from Lesson 07 available (optional for scheduling)
- [ ] Evidence folder for today ready

## Lab procedure

### Task 1 — Task inventory

Before scheduling anything, inventory what already exists. Orphan or misnamed tasks are how labs and production both quietly accumulate silent failures — you can't monitor a task you didn't know existed.

1. Open **Tasks** in IIQ.
2. List every `MNB-*` task (and note stock tasks you must not schedule casually).
3. Build this table in your notebook:

| Task name | Type | Depends on | Schedule? |
| --- | --- | --- | --- |
| Aggregate MNB-HR | Account Aggregation | HR file path (CSV) | Nightly |
| Aggregate MNB-IT-Access | Account Aggregation | Lesson 09 | Nightly after HR |
| Refresh MNB Attributes | Identity Refresh | HR (and app) aggregates | Nightly after aggs |
| Refresh MNB Managers | Identity Refresh | After attrs; resolve `managersAssociateID` | Nightly after attrs |
| Refresh MNB Roles | Identity Refresh | Role model (later) | After role changes |
| Refresh MNB Policies | Identity Refresh | Policies (later) | After policy changes |

**Expected result:** Inventory table started, with rows reserved for apps you haven't onboarded yet.

### Task 2 — Write the runbook order

1. In `~/iiq-lab-notes/RUNBOOK-nightly.md` (or your binder), write the sequence from Concepts above.
2. Add a one-line rationale: "HR is authoritative; people must exist before IT entitlements correlate."
3. Add a failure policy: "Stop the chain on HR aggregate failure; do not refresh from a stale partial load without an explicit decision."

**Expected result:** A one-page runbook exists.

### Task 3 — Schedule UI practice

1. Open `Refresh MNB Attributes` → schedule settings.
2. Set a daily time (e.g. 02:00 local).
3. Save, then screenshot the schedule.
4. **Disable** the schedule again — unless you genuinely want overnight runs on your own machine.
5. Log in CHANGELOG: "Practiced schedule enable/disable on Refresh MNB Attributes."

**Expected result:** You can configure a schedule and prove you left it in a safe state for a personal lab.

**If it fails:** Some editions use cron expressions or separate Schedule objects — use the equivalent path and document it.

### Task 4 — Result literacy

1. Open the most recent successful `Aggregate MNB-HR` result.
2. Record: start time, end/duration, status, accounts created/updated/total, warnings.
3. If a result with warnings exists, open it. Otherwise, don't force a failure on the real task yet — Task 8 gives you a safe way to generate one.
4. Write which fields you read first when paged.

**Expected result:** Annotated screenshot or notes showing you can interpret a result without guessing.

### Task 5 — On-call checklist

Write a five-line checklist titled "Aggregation failed":

1. Open the task result → capture the error text and the result id.
2. Verify the file path exists and the Tomcat user can read it (`ls -l` the absolute path).
3. Validate the delimiter/header with `head` on the file.
4. Check disk space / DB connectivity if the connector error suggests infrastructure.
5. Re-run once after the fix; if it fails again, escalate with the evidence pack — don't loop blindly.

**Expected result:** A checklist saved in your notes/evidence, ready to paste into a real ops runbook later.

### Task 6 — Overlap risk note

1. Write one paragraph on the risk of overlapping two Identity Refresh runs (e.g. `Refresh MNB Attributes` and `Refresh MNB Managers` starting at the same second, or two attribute runs stacking).
2. Write the mitigation: schedules with buffer time, mutual exclusion, monitoring duration trends, and never scheduling a mega "all options" refresh on top of purpose-built tasks.

**Expected result:** An overlap-risk paragraph in the runbook.

### Task 7 — Result ID evidence habit

1. From a successful `Aggregate MNB-HR` result, copy the result id / name / timestamp into an evidence file `TASK-RESULTS.txt`.
2. Do the same for `Refresh MNB Attributes` (and optionally `Refresh MNB Managers`).
3. Add a binder rule: "Every production-like change cites at least one task result id."

**Expected result:** `TASK-RESULTS.txt` has at least two entries with timestamps.

### Task 8 — Dry-run failure (optional but recommended)

Reading someone else's failure screenshot is not the same as watching a task actually break. This task gives you a real, safe failure to triage without touching production config.

1. Create a **copy** task `Aggregate MNB-HR-DRYRUN` pointing at a nonexistent path. Do **not** alter the real `Aggregate MNB-HR`.
2. Run it and capture the failure result.
3. Delete or disable the dry-run task once you've filed the evidence.
4. Walk your five-line on-call checklist against this failure.

**Expected result:** A failure evidence pack, produced without damaging the real HR aggregation task.

## Acceptance criteria

- [ ] MNB task inventory table complete (with placeholders for IT)
- [ ] Nightly runbook order documented with HR-first rationale
- [ ] Schedule enable/disable practiced on refresh
- [ ] Task result fields annotated
- [ ] Five-line on-call checklist written
- [ ] Overlap risk noted
- [ ] Task result ids filed in evidence
- [ ] Dry-run failure practiced (or explicitly deferred with a reason)

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Schedule did not fire | Disabled / wrong timezone / scheduler down | Verify schedule enabled; check IIQ request processor |
| Task stuck Running | Host crash mid-job | Admin terminate/cleanup per IIQ ops guidance; fix root cause |
| Success but 0 accounts | Path regression after restart | Reconfirm absolute path; Lesson 03 hygiene |
| Cascading failures | Ran refresh after failed HR agg | Stop the chain; fix HR first |
| Duplicate schedules | Copied tasks both left enabled | Inventory and disable extras |

## Training binder evidence

- Task inventory table
- `RUNBOOK-nightly.md`
- Screenshot: schedule config (then disabled state)
- Annotated task result screenshot
- On-call checklist

**Ops note:** This runbook is what you hand to whoever takes the on-call pager next — it should stand alone without you in the room.

## Knowledge check

1. Why does HR aggregate run before IT aggregate?
2. What fields do you read on a task result first?
3. Name one risk of overlapping refreshes.
4. What should you do if HR aggregation fails, before running refresh?
5. Why disable lab schedules after practice?
6. After aggregations, which Meridian refresh task promotes identity attributes from Links?

### Answers

1. Identities must exist/update from authoritative HR before IT accounts correlate and entitlements attach.
2. Status/success, timestamps/duration, counters, and the first error message.
3. Lock contention, long runtimes, inconsistent intermediate identity state, and noisy failures.
4. Stop the chain; fix the HR path/data; don't refresh as if the load succeeded.
5. To avoid unexpected overnight load/failures on a personal laptop lab.
6. `Refresh MNB Attributes`.

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search "task schedule" and "Account Aggregation task" for scheduling and result interpretation.
- [SailPoint Community](https://community.sailpoint.com/) — search "nightly aggregation refresh order" for production sequencing war stories.
- [NIST SP 800-53 AU-6 / SI-2](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — reviewing automated processing logs and maintaining reliable batch controls.
- [FFIEC IT Examination Handbook — Architecture, Infrastructure, and Operations](https://ithandbook.ffiec.gov/it-booklets/architecture-infrastructure-and-operations.aspx) — job monitoring, failure handling, and operational resilience.
- [CIS Controls v8 — Control 8 (Audit Log Management)](https://www.cisecurity.org/controls/audit-log-management) — retaining and reviewing evidence of control activities like aggregations.

## Stretch lab

- Draft a "sequential composite" mindset doc: even if your edition uses separate schedules, document required gaps (e.g. HR 01:00, apps 01:20, attrs 02:00, managers 02:20).
- Add duration baselines to the runbook after three manual runs.
- Add a RACI line to the runbook: who acknowledges failed tasks (IAM Ops) vs. who fixes HR file feeds (HRIS).

## Summary

- Meridian treats task order and schedules as controls, not conveniences.
- HR → apps → `Refresh MNB Attributes` → managers → roles/policies is the factory sequence; task results are monitored artifacts, not fire-and-forget logs.
- On-call checklists and a safe dry-run habit turn aggregation failures into a repeatable response instead of a scramble.

## Feedback

Could you recite the nightly order and the five-line aggregation-failure checklist from memory? If a dry-run or schedule step confused you, note the **task name**, what you expected in TaskResult, and what you saw — that signal keeps the runbook honest.

---

**Previous:** [Lesson 07 — Populations & Identity Selectors](07-populations-and-selectors.md)  
**Next:** [Lesson 08b — Day in the Life: Ticket Triage](08b-day-in-the-life-ticket-triage.md) · [Lesson 09 — Onboard IT Access Inventory App](09-it-access-inventory-app.md)
