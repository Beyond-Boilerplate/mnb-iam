# Lesson 105 — Partitioning & Task Servers

| Field | Value |
| --- | --- |
| **Level** | Intermediate |
| **Track** | Enterprise Hardening & Mastery |
| **Time** | 60–90 minutes |
| **Prereq** | [Lesson 104 — AuditConfig & SIEM](104-auditconfig-and-siem.md); Task ops from Lesson 08 concepts |
| **Lab data** | Meridian aggregation tasks; multi-host notes from HOMELAB-CD / SSD servers.properties |

## Learning objectives

You will be able to:

- Explain **task server** hosts vs UI hosts in an IIQ cluster
- Configure or document **partitioning** for a large Account Aggregation
- Assign heavy Meridian aggregations to a task host (or single-host lab simulation)
- Prevent concurrent destructive dual-runs of the same aggregation
- List clock-sync and hostname mapping requirements for multi-node labs

## Why this matters

Full AD or core-banking aggregations on the UI node freeze operators during business hours. Partitioning and dedicated task servers keep Meridian interactive while inventory jobs scale.

**Control / audit:** Failed or overlapping aggregations create false orphans and missed leavers. Host assignment and schedules are operational controls with evidence in Task Results.

## Concepts

| Term | Meaning |
| --- | --- |
| **UI / Request host** | Serves browsers and lightweight work |
| **Task server** | Runs aggregations, refresh, certifications generation |
| **Partitioning** | Splits aggregation/request work across threads/hosts by partition keys |
| **Server** object | IIQ’s view of a JVM node and its roles |

```text
  Schedule: Aggregate MNB-ActiveDirectory
        |
        v
  Task server host (not UI)
        |
        +-- Partition 0..N  ---> connector threads
        |
        v
  Task Result counters + errors
```

**Meridian placement sketch**

| Workload | Preferred host role |
| --- | --- |
| Interactive UI / LCM | UI servers |
| Account Aggregation (AD, Core, AWS) | Task servers |
| Identity Refresh large | Task servers |
| Report generation heavy | Task or reporting node |

**Lab reality:** Single-node Tomcat still teaches partitioning options and schedule hygiene; document “would pin to task host in prod.”

## Before you start

- [ ] List Meridian aggregation task names already in lab
- [ ] Access to Task Definition editor as `spadmin`
- [ ] Read `servers.properties` SPTARGET mapping (Lesson 101)
- [ ] Note whether cluster is single or multi JVM

## Lab procedure

### Task 1 — Inventory servers

1. Open **Gear** → **Administrator Console** → **Hosts** / **Servers** (or Debug list `Server`).
2. Record hostname, roles (if shown), last heartbeat.
3. Mark which host would be UI vs task in a 2-node design.

**Expected result:** Server inventory table (even if one row).

**If it fails:** Use OS hostname + Tomcat instance name as stand-in inventory.

### Task 2 — Review one aggregation for partitioning

1. Open Account Aggregation task for `MNB-ActiveDirectory` or largest Meridian app available.
2. Locate partitioning / concurrent / thread options (labels vary by connector and version).
3. Record current values; photograph or note defaults.
4. For lab, set a modest partition/thread increase **or** document recommended prod values without changing shared lab if risky.

**Expected result:** Partitioning notes for one Meridian aggregation.

**If it fails:** Connector lacks partition UI—document filter-based split strategy (OU/host) instead.

### Task 3 — Host assignment

1. On the task definition, set **run on** / host restriction to the task server identity if multi-host.
2. Single-host: add description `MNB: pin to task host when clustered`.
3. Save.

**Expected result:** Explicit host pin or documented intent.

### Task 4 — Schedule collision control

1. List schedules for AD aggregation, HR aggregation, and identity refresh.
2. Ensure heavy jobs do not all start at the same minute.
3. Stagger: HR → AD → refresh (example order).
4. Record schedule table with start times.

**Expected result:** Staggered schedule table with no identical start stamps for heavy jobs.

**If it fails:** Disable one lab schedule temporarily and note conflict.

### Task 5 — Controlled run + Task Result

1. Run the partitioned (or documented) aggregation once.
2. Open Task Result: duration, accounts scanned, errors.
3. Confirm UI remains responsive during run (subjective lab check).
4. Save result ID in binder.

**Expected result:** Successful Task Result with timing notes.

**If it fails:** Revert thread settings; run sequentially; capture error for Lesson 106 tuning.

### Task 6 — Multi-host readiness checklist

1. Checklist: unique server names, NTP sync, shared DB, sticky sessions for UI if needed, IQService reachability from task hosts, AuditConfig clocks aligned (Lesson 104).
2. Map `servers.properties` hostnames to roles.
3. Homelab note: K8s replicas may blur UI/task—document how Meridian will separate pools in prod Helm values.

**Expected result:** Multi-host readiness checklist completed.

## Acceptance criteria

- [ ] Server inventory captured
- [ ] Partitioning or split strategy documented for one large app
- [ ] Host pin or description intent set
- [ ] Staggered schedule table filed
- [ ] One Task Result evidenced
- [ ] Multi-host checklist complete

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Task stuck Pending | Wrong host / host down | Check Server heartbeat; clear host pin |
| Duplicate aggregations | Two schedules | Disable duplicate; use mutex discipline |
| Partition errors | Uneven filters | Balance OU/host partitions |
| UI timeouts during agg | Agg on UI node | Move to task host |
| Clock skew across nodes | NTP missing | Sync time before trusting audits |

## Training binder evidence

- Server inventory  
- Partitioning notes  
- Schedule stagger table  
- Task Result ID/screenshot  
- Multi-host checklist  

## Knowledge check

1. Why separate task servers from UI servers?
2. What does aggregation partitioning accomplish?
3. Name a safe Meridian schedule order for HR vs AD vs refresh.
4. Why does NTP matter for AuditConfig/SIEM?
5. What evidence proves a partitioned job ran?

### Answers

1. Protect interactive latency; isolate heavy connector CPU/IO.  
2. Parallelizes work across partitions/threads/hosts for throughput.  
3. Authoritative HR first, then directories/targets, then identity refresh (adjust to your dependency graph).  
4. Correlating events across nodes/SIEM requires aligned timestamps.  
5. Task Result with timing/counters (and host name if shown).

## Stretch lab

Design OU-based partitions for `MNB-ActiveDirectory` (e.g., by branch OU) with a rollback plan if a partition fails.

## Summary

- Pin heavy Meridian jobs to task capacity; partition large aggregations.
- Stagger schedules; prove runs with Task Results.
- Multi-host readiness includes NTP, naming, and role separation.

## Capacity planning worksheet

| App | Est. accounts | Full agg duration baseline | Partition plan | Task host |
| --- | --- | --- | --- | --- |
| MNB-ActiveDirectory | (lab count) | (min) | OU / threads | task-1 |
| MNB-CoreBanking | | | | task-1 |
| MNB-AWS-Cloud | | | | task-1 |
| MNB-HR | | | often lighter | ui or task |

Fill with real Task Result numbers from your lab.

### Task 7 — Failure domain notes

1. If task host dies mid-aggregation, document restart behavior (resume vs restart full).
2. Ensure UI hosts can still process LCM approvals during agg outage.
3. IQService reachability must be tested from the task host network namespace (K8s/homelab gotcha).

**Expected result:** Failure-domain paragraph for Meridian.

### Homelab vs prod topology

Homelab may run single JVM; production blueprint (Lesson 110) must still show separate pools even if lab cannot.

---

**Previous:** [Lesson 104 — AuditConfig & SIEM](104-auditconfig-and-siem.md)  
**Next:** [Lesson 106 — Performance Tuning IIQ](106-performance-tuning-iiq.md)
