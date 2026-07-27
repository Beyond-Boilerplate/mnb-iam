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

- Inventory Meridian tasks and state their purpose
- Define a nightly runbook order with HR first
- Configure (then safely disable) a schedule on a refresh task
- Read a task result for start time, duration, counters, and errors
- Write a five-line on-call checklist for aggregation failure

## Why this matters

Banks run IAM as a factory. Task order and schedules are operational controls, not conveniences. If IT aggregation runs before HR, new joiners get uncorrelated accounts; if refresh overlaps itself, you get lock contention and opaque failures before the business day.

**Control / audit:** Ops must show a documented job sequence, schedules, monitoring of task results, and an incident response when aggregation fails. This lesson builds that muscle in the lab.

## Concepts

**Meridian nightly order (target):**

```text
  1. Aggregate MNB-HR
  2. Aggregate MNB-IT-Access          (Lesson 09+)
  3. Aggregate platform apps          (Lessons 11–16)
  4. Refresh MNB Identities           (population-scoped when possible)
  5. Policy scan / cert generation    (later lessons)
```

| Why this order | Reason |
| --- | --- |
| HR first | Creates/updates people before accounts try to correlate |
| Apps next | Attach entitlements to existing identities |
| Refresh after | Recalculate managers, roles, policies from new truth |
| Avoid overlap | Two refreshes at once → contention and partial state |

**Task result literacy:** Always read start/end time, host, success/fail, account/identity counters, and the first error stack—before re-running.

**SLA sketch:** Aggregation failures visible before start of banking day; on-call acknowledges within agreed minutes (define for your org—lab: “notice on next login”).

## How it works

IIQ **TaskDefinitions** encapsulate what to run (aggregation, refresh, …); **schedules** attach cron-like timing; **TaskResults** are the auditable proof. Meridian’s control narrative depends on ordered execution: HR → apps → refresh → policy/certs.

```text
Schedule / Run Now
        │
        ▼
TaskDefinition (Aggregate MNB-HR, Refresh MNB Identities, …)
        │
        ▼
TaskResult (counters, errors, host, duration)
        │
        └── Evidence binder + on-call triage
```

| Ops rule | Why |
| --- | --- |
| HR before targets | People must exist before correlation |
| Refresh after aggregates | Compile new truth |
| No overlapping refreshes | Avoid contention / partial state |
| Read TaskResult before re-run | Don’t mask root cause |

**Real-life Meridian example.** If `Aggregate MNB-IT-Access` runs before HR on a night when `nina.joiner` is added, her IT row may land uncorrelated. Ordering is a control, not a preference.

## Before you start

- [ ] `Aggregate MNB-HR` and `Refresh MNB Identities` exist
- [ ] Populations from Lesson 07 available (optional for scheduling)
- [ ] Evidence folder for today ready

## Lab procedure

### Task 1 — Task inventory

Before scheduling anything, inventory what already exists—orphan or misnamed tasks are how labs and production both accumulate silent failures.

1. Open **Tasks** in IIQ.
2. List every `MNB-*` task (and note stock tasks you must not schedule casually).
3. Build this table in your notebook:

| Task name | Type | Depends on | Schedule? |
| --- | --- | --- | --- |
| Aggregate MNB-HR | Account Aggregation | HR file path | Nightly |
| Refresh MNB Identities | Identity Refresh | HR aggregate | Nightly after apps |
| Aggregate MNB-IT-Access | Account Aggregation | Lesson 09 | Nightly after HR |

**Expected result:** Inventory table started; empty rows reserved for future apps.

### Task 2 — Write the runbook order

1. In `~/iiq-lab-notes/RUNBOOK-nightly.md` (or binder), write the sequence above.
2. Add a one-line rationale: “HR is authoritative; people must exist before IT entitlements correlate.”
3. Add failure policy: “Stop the chain on HR aggregate failure; do not refresh from stale partial loads without decision.”

**Expected result:** One-page runbook exists.

### Task 3 — Schedule UI practice

1. Open `Refresh MNB Identities` → schedule settings.
2. Set a daily time (e.g. 02:00 local).
3. Save. Screenshot the schedule.
4. **Disable** the schedule again unless you intentionally want overnight laptop runs.
5. Log in CHANGELOG: “Practiced schedule enable/disable on Refresh MNB Identities.”

**Expected result:** You can configure a schedule and prove you left it in a safe state for a personal lab.

**If it fails:** Some editions use cron expressions or separate Schedule objects—use the equivalent path and document it.

### Task 4 — Result literacy

1. Open the most recent successful `Aggregate MNB-HR` result.
2. Record: start time, end/duration, status, accounts created/updated/total, warnings.
3. Open a result that had warnings (if any) or re-run with a temporary bad path in a **copy** task to generate a failure—**prefer** reading an existing failure if available rather than breaking prod-like config.
4. Write which fields you read first when paged.

**Expected result:** Annotated screenshot or notes showing you can interpret a result without guessing.

### Task 5 — On-call checklist

Write a five-line checklist titled “Aggregation failed”:

1. Open task result → capture error text and result id.
2. Verify file path exists and Tomcat user can read it (`ls -l` absolute path).
3. Validate delimiter/header with `head` on the file.
4. Check disk space / DB connectivity if connector errors suggest infrastructure.
5. Re-run once after fix; if fail again, escalate with evidence pack—do not loop blindly.

**Expected result:** Checklist saved in notes/evidence; suitable to paste into a real ops runbook later.

### Task 6 — Overlap risk note

1. Write one paragraph: risk of overlapping two `Refresh MNB Identities` runs.
2. Write mitigation: schedules with buffer; mutual exclusion; monitor duration trends.

**Expected result:** Overlap risk paragraph in the runbook.

### Task 7 — Result ID evidence habit

1. From a successful `Aggregate MNB-HR` result, copy the result id / name / timestamp into evidence `TASK-RESULTS.txt`.
2. From `Refresh MNB Identities`, do the same.
3. Add a binder rule: “Every production-like change cites at least one task result id.”

**Expected result:** `TASK-RESULTS.txt` has two entries with timestamps.

### Task 8 — Dry-run failure (optional but recommended)

1. Create a **copy** task `Aggregate MNB-HR-DRYRUN` pointing at a nonexistent path (do **not** alter the real `Aggregate MNB-HR`).
2. Run it; capture the failure result.
3. Delete or disable the dry-run task after filing evidence.
4. Walk your five-line on-call checklist against this failure.

**Expected result:** Failure evidence pack without damaging the real HR aggregation task.

## Acceptance criteria

- [ ] MNB task inventory table complete (with placeholders for IT)
- [ ] Nightly runbook order documented with HR-first rationale
- [ ] Schedule enable/disable practiced on refresh
- [ ] Task result fields annotated
- [ ] Five-line on-call checklist written
- [ ] Overlap risk noted
- [ ] Task result ids filed in evidence
- [ ] Optional dry-run failure practiced or explicitly deferred

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Schedule did not fire | Disabled / wrong timezone / scheduler down | Verify schedule enabled; check IIQ request processor |
| Task stuck Running | Host crash mid-job | Admin terminate/cleanup per IIQ ops guidance; fix root cause |
| Success but 0 accounts | Path regression after restart | Reconfirm absolute path; Lesson 03 hygiene |
| Cascading failures | Ran refresh after failed HR agg | Stop chain; fix HR first |
| Duplicate schedules | Copied tasks both enabled | Inventory and disable extras |

## Training binder evidence

- Task inventory table
- RUNBOOK-nightly.md
- Screenshot: schedule config (then disabled state)
- Annotated task result screenshot
- On-call checklist

**Examiner question:** “What is your job order for nightly IAM processing, and what do you do when HR aggregation fails?”

## Knowledge check

1. Why HR aggregate before IT aggregate?
2. What fields do you read on a task result first?
3. Name one risk of overlapping refreshes.
4. What should you do if HR aggregation fails before refresh?
5. Why disable lab schedules after practice?

### Answers

1. Identities must exist/update from authoritative HR before IT accounts correlate and entitlements attach.
2. Status/success, timestamps/duration, counters, and the first error message.
3. Lock contention, long runtimes, inconsistent intermediate identity state, noisy failures.
4. Stop the chain; fix HR path/data; do not refresh as if the load succeeded.
5. Avoid unexpected overnight load/failures on a personal laptop lab.

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “task schedule” and “Account Aggregation task” for scheduling and result interpretation.
- [SailPoint Community](https://community.sailpoint.com/) — search “nightly aggregation refresh order” for production sequencing war stories.
- [NIST SP 800-53 AU-6 / SI-2](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — reviewing automated processing logs and maintaining reliable batch controls.
- [FFIEC IT Examination Handbook — Architecture, Infrastructure, and Operations](https://ithandbook.ffiec.gov/it-booklets/architecture-infrastructure-and-operations.aspx) — job monitoring, failure handling, and operational resilience.
- [CIS Controls v8 — Control 8 (Audit Log Management)](https://www.cisecurity.org/controls/audit-log-management) — retaining and reviewing evidence of control activities like aggregations.

## Stretch lab

- Draft a “sequential composite” mindset doc: even if your edition uses separate schedules, document required gaps (e.g. HR 01:00, apps 01:20, refresh 02:00).
- Add duration baselines to the runbook after three manual runs.
- Create a fake failure evidence pack (bad path on a *copy* task named `Aggregate MNB-HR-DRYRUN`) and file it under evidence as training for incident response.
- Add a RACI line to the runbook: who acknowledges failed tasks (IAM Ops) vs who fixes HR file feeds (HRIS).

## Summary

- Meridian treats task order and schedules as controls.
- HR → apps → refresh is the factory sequence; results are monitored artifacts.
- On-call checklists turn aggregation failures into repeatable response.

---

**Previous:** [Lesson 07 — Populations & Identity Selectors](07-populations-and-selectors.md)  
**Next:** [Lesson 09 — Onboard IT Access Inventory App](09-it-access-inventory-app.md)
