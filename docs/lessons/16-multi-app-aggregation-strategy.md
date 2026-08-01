# Lesson 16 — Multi-App Aggregation Strategy

**Level:** Intermediate  
**Track:** Applications  
**Time:** 60–75 min  
**Prereq:** Lessons 09–15 (HR + inventory + platform apps exist)  

**Lab data:** All `~/iiq-lab-data/` extracts already wired to Meridian applications. No new CSV required.

---

## Learning objectives

You will be able to:

- Write an enterprise **aggregation runbook** with explicit task order and stop/go rules
- Execute a full lab pipeline: authoritative HR → targets → identity refresh
- Record durations and task results as operational evidence
- Apply a failure triage matrix (HR fail = stop; single target fail = continue + ticket)
- Draft the ops communication you would send on partial failure

---

## Why this matters

**Business.** Connectors without a schedule produce “sometimes true” cubes. Managers certify yesterday’s access while HR already terminated someone. Meridian needs a boring, repeatable pipeline.

**Control / audit.** Examiners ask for the **order of operations**, RPO expectations, and what happens when a feed fails. “We click Aggregate sometimes” fails exams. A signed runbook with task names and evidence samples passes.

---

## Concepts

**Authoritative first.** Identities must exist before target correlation and entitlement attachment are meaningful.

**Refresh after batches.** Account Aggregation brings accounts/ents; **Identity Refresh** recomputes cube-derived state managers see (roles, needs refresh flags, etc., depending on your options).

**Failure domains.**

```
[1] Aggregate MNB-HR          ── if FAIL → STOP pipeline, page IAM
[2] Aggregate MNB-IT-Access
[3] Aggregate MNB-ActiveDirectory
[4] Aggregate platform apps   ── Core, SAP, AWS, Wire, CRM, IB, ECOM
[5] Refresh MNB Identities    ── if targets partial, still refresh; ticket gaps
```

| Stage | Tasks (lab names) | On failure |
| --- | --- | --- |
| A — Authoritative | `Aggregate MNB-HR` | **Stop.** Do not run targets blindly. |
| B — Inventory | `Aggregate MNB-IT-Access` | Continue others; Sev-2 ticket |
| C — Directory | `Aggregate MNB-ActiveDirectory` | Continue; Sev-2 |
| D — Business platforms | Core, SAP, AWS, Wire, CRM, IB, ECOM aggregates | Continue peers; ticket each fail |
| E — Cube compile | `Refresh MNB Identities` (or your Lesson 06/08 refresh task) | Re-run after fixes; note stale UI |

**RPO (recovery point) narrative for Meridian lab/prod intent:** HR daily before start of business; targets daily after extract drops; privileged apps (AWS, Wire, SAP, Core) monitored for same-day re-run on feed repair.

> **Production reality.** In production this pipeline aggregates native connectors, not files — which changes the failure modes: instead of "file missing / stale extract," you plan for API rate limits (Okta/Graph 429s), expired client secrets, and connector-account lockouts. The staging discipline (authoritative first, stop-vs-continue decisions, refresh last) is identical; only the troubleshooting table grows. Lessons 56–76 teach each connector's specific failure signatures.

---

## How it works

A **pipeline** is an ordered set of Account Aggregation tasks plus a trailing Identity Refresh, with explicit **stop-vs-continue** rules per failure domain. HR failure stops the night; a single platform extract failure tickets and continues peers.

```text
[1] Aggregate MNB-HR                 ── FAIL → STOP
[2] Aggregate MNB-IT-Access          ── FAIL → ticket, continue
[3] Aggregate MNB-ActiveDirectory    ── FAIL → ticket, continue
[4] Platform aggregates (Core…CRM)   ── FAIL → ticket each, continue
[5] Refresh MNB Identities           ── compile whatever landed
```

| Stage | On failure | Why |
| --- | --- | --- |
| Authoritative HR | Stop | No trustworthy people base |
| Inventory / platforms | Continue + ticket | Partial coverage better than zero |
| Refresh | Re-run after fixes | Cubes reflect last good inputs |

**Real-life Meridian example.** If Wire extract fails but HR and Core succeed, payments certs may be stale while retail joiners still process—ops must know which SLA broke.

## Before you start

- [ ] All Meridian apps from Lessons 04–15 exist
- [ ] Account Aggregation tasks named consistently (`Aggregate MNB-…`)
- [ ] Identity Refresh task exists from earlier lessons (create `Refresh MNB Identities` if missing)
- [ ] Notebook / binder section “Ops Runbook” ready
- [ ] IIQ Tasks UI open; do not run random system tasks

---

## Lab procedure

### Task 1 — Inventory your task catalog

A pipeline is only as good as its inventory—list every Meridian aggregate and refresh before you write order and failure rules.

1. Open **Tasks**. List every `Aggregate MNB-*` and your refresh task.
2. Build a checklist table in your binder with columns: Order, Task name, App, Last result, Duration, Owner on-call.
3. Confirm naming uses `MNB-` prefix—fix typos now.

**Expected result:** Complete inventory of pipeline tasks before execution.

**If it fails:** Create any missing Aggregate task from the application object rather than skipping silently.

---

### Task 2 — Write the runbook (before you click Run)

1. In your binder, write the canonical order:

```text
MNB Aggregation Runbook (lab)
1. Aggregate MNB-HR
2. Aggregate MNB-IT-Access
3. Aggregate MNB-ActiveDirectory
4. Aggregate MNB-CoreBanking
5. Aggregate MNB-SAP-Finance
6. Aggregate MNB-AWS-Cloud
7. Aggregate MNB-WirePortal
8. Aggregate MNB-Salesforce-CRM
9. Aggregate MNB-InternetBanking
10. Aggregate MNB-Ecommerce-Ops
11. Refresh MNB Identities
```

2. Add stop/go rules from the Concepts table.
3. Add SLA intents: HR fail → page within 15 minutes; privileged target fail → ticket within 1 hour; uncorrelated AWS_ADMIN → Lesson 19 SLA.

**Expected result:** Written runbook exists **before** the full run—process evidence, not after-the-fact notes.

---

### Task 3 — Execute Stage A (HR) with gate

1. Run `Aggregate MNB-HR`.
2. Open task result. Confirm success and non-zero accounts.
3. Spot-check `helen.ross` and `samir.hassan` still present.
4. **Gate:** Only proceed if HR succeeded.

**Expected result:** Authoritative stage green; pipeline continues.

**If it fails:** Stop. Fix HR path/schema. Do not “push through” target aggregates for this lesson’s graded path.

---

### Task 4 — Execute Stages B–D (targets)

> **Pipeline vs correlation.** Stage B–D success means each target Task Result is green and **Application → Accounts** counts look sane. HR cubes may still lack target links until Lessons 17–18—that is **not** a pipeline failure. Never enable create-identities on targets to “clear” uncorrelated lists or empty Accounts tabs on cubes.

1. Run inventory, AD, then each platform Aggregate task in runbook order.
2. After each task, jot duration (even if 1–2 seconds) and success/fail; spot-check that app’s Accounts count (not only persona cubes).
3. If any **single** target fails: note it, continue the remaining targets, open a pretend ticket ID `MNB-LAB-AGG-###`.
4. Do not enable create-identities on any target while “fixing” failures.

**Expected result:** Full target suite attempted; any failures logged with ticket IDs; most succeed. Uncorrelated accounts and incomplete cube links are expected until correlation.

**If it fails:** Use Lesson 11–15 troubleshooting tables per app.

---

### Task 5 — Execute Stage E (Refresh)

1. Run `Refresh MNB Identities` (or equivalent Identity Refresh filtered to Meridian population if you created one).
2. Record duration and result.
3. Open `priya.wire` and `jordan.reed` cubes—confirm accounts/ents still visible post-refresh.

**Expected result:** Refresh completes; cubes look coherent for correlated accounts.

**If it fails:** Refresh errors often trace to rule/option misconfig—run with conservative options used in Lesson 06.

---

### Task 6 — Timing & RPO evidence sheet

1. Create a simple evidence table:

| Task | Start | End | Duration | Result |
| --- | --- | --- | --- | --- |
| Aggregate MNB-HR | | | | |
| … | | | | |

2. Write RPO statement:

```text
Prod intent: HR extract aggregated by 06:00 local; targets by 07:00;
Refresh by 07:30. Privileged app failures page on-call IAM.
```

**Expected result:** Timing sheet filled—even lab seconds count as evidence practice.

---

### Task 7 — Partial failure communications drill

1. Draft an ops message (Slack/email tone):

```text
Subject: MNB IIQ aggregation partial failure — AWS
HR/AD/Wire/SAP OK. Aggregate MNB-AWS-Cloud failed (file permission).
Ticket MNB-LAB-AGG-104. Cloud admin certs may be stale until re-run 10:30.
No identity create changes made.
```

2. Save draft in binder under Comms.

**Expected result:** You practice transparent partial-failure communication—silent gaps fail exams.

---

### Task 8 — Pipeline acceptance sign-off

1. Checkmark the runbook steps you executed.
2. List known gaps (uncorrelated accounts, missing target links on HR cubes, login-named orphans from earlier create-identities mistakes—all expected or deferred until Lessons 17–19).
3. Sign/date the binder page (lab training record).

**Expected result:** One complete pipeline execution with documented outcomes—including what you are **not** fixing yet (correlation).

---

## Acceptance criteria

- [ ] **Bank craft exit:** Nightly order documents seeded TaskDefinitions (`Aggregate MNB-*`, `Refresh MNB Attributes` / Managers) under `config/TaskDefinition/`

- [ ] Written runbook with ordered task names and stop/go rules
- [ ] Full pipeline executed at least once (HR → targets → refresh)
- [ ] Durations and results recorded
- [ ] Failure matrix understood; sample ticket + comms draft produced
- [ ] RPO narrative written for Meridian

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Targets “succeed” but cubes empty of people | HR skipped/failed | Re-run HR; restart pipeline |
| Targets succeed; HR cubes missing app links | Correlation not configured | **Expected** — prove under Application → Accounts; Lessons 17–18 |
| New orphan / login-named cubes after targets | Create-identities ON on a target | Disable on all non-HR apps; leave or clean (Lesson 19); do not re-enable |
| Refresh takes forever | Full population + heavy options | Narrow filter; disable unneeded refresh options |
| Task name chaos | Inconsistent naming | Rename to `Aggregate MNB-*` |
| Two HR aggregates conflicting | Duplicate apps | One authoritative `MNB-HR` only |
| Operator ran apps alphabetically putting AWS before HR | No runbook discipline | Enforce Stage A gate |

---

## Training binder evidence

1. Runbook page (order + stop/go)
2. Completed timing/results table
3. Screenshot collage of key task results (HR + one privileged + refresh)
4. Partial-failure comms draft
5. RPO statement

Examiner question: *“What do you do if Wire aggregation fails at 06:40?”* → Continue other targets, ticket, re-run Wire, communicate stale payment access data, still refresh after successful peers.

---

## Knowledge check

1. What runs first and why?
2. If Wire aggregate fails, do you stop SAP and AWS?
3. Where does Identity Refresh sit in the pipeline?
4. What is the correct response to HR aggregation failure?
5. Why record durations even when they are seconds in lab?

### Answers

1. `Aggregate MNB-HR` — identities must exist before target attachment/correlation is meaningful.
2. No — continue other targets; ticket Wire; communicate partial staleness.
3. After account aggregations (Stage E), to compile cube state.
4. **Stop** the pipeline; fix HR; page IAM; do not pretend targets can invent truth.
5. Builds the evidence habit and estimates for prod capacity/SLA discussions.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “task schedule” and “Account Aggregation” for chaining aggregations and refresh.
- [SailPoint Community](https://community.sailpoint.com/) — search “aggregation failure pipeline” for stop-vs-continue runbook patterns.
- [NIST SP 800-53 AU-6 / CP-2](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — reviewing processing outcomes and contingency for batch controls.
- [FFIEC IT Examination Handbook — Architecture, Infrastructure, and Operations](https://ithandbook.ffiec.gov/it-booklets/architecture-infrastructure-and-operations.aspx) — operational monitoring and resilience for scheduled jobs.
- [CIS Controls v8 — Control 8](https://www.cisecurity.org/controls/audit-log-management) — retaining task-result evidence for control activities.


## Stretch lab

- Schedule the pipeline conceptually on a weekly calendar (Mon–Fri 06:00 HR, 06:15 targets, 07:00 refresh).
- Add a “privileged re-run” mini-runbook for AWS/Wire/SAP/Core only.
- Propose monitoring: alert if any Aggregate MNB-* task result = Error.

---

## Summary

- Aggregation order is a **control**, not a convenience.
- You executed and documented a full Meridian pipeline with failure triage and comms.
- Applications track closes; Correlation track begins next.

---

**Previous:** [Lesson 15 — Directory, CRM & Digital](15-onboard-directory-and-crm.md)  
**Next:** [Mid-capstone — Apps](mid-16-apps-capstone.md) · [Lesson 16b — Reading Task Results](16b-reading-task-results.md) · [Lesson 17 — Account Correlation Basics](17-correlation-basics.md)
