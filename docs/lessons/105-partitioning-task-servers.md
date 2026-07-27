# Lesson 105 — Partitioning & Task Servers

**Level:** Intermediate  
**Track:** Enterprise Hardening & Mastery  
**Time:** 60–90 min  
**Prereq:** Lesson 104 — AuditConfig & SIEM; Task ops from Lesson 08 concepts  

**Lab data:**
- Meridian aggregation tasks
- Multi-host notes from HOMELAB-CD / SSD `servers.properties`

---

## Learning objectives

You will be able to:

- Explain **task server** hosts vs UI hosts in an IIQ cluster
- Configure or document **partitioning** for a large Account Aggregation
- Assign heavy Meridian aggregations to a task host (or single-host lab simulation)
- Prevent concurrent destructive dual-runs of the same aggregation
- List clock-sync and hostname mapping requirements for multi-node labs
- Fill a capacity planning worksheet with real Task Result numbers

---

## Why this matters

**Business.** Full AD or core-banking aggregations on the UI node freeze operators during business hours. When `marcus.approve` cannot open a certification because Account Aggregation for `MNB-ActiveDirectory` is hammering the only JVM, Meridian’s interactive control plane is offline — during the same window leavers may need disable. Partitioning and dedicated task servers keep Meridian interactive while inventory jobs scale.

**Control / audit.** Failed or overlapping aggregations create false orphans and missed leavers. Host assignment and schedules are operational controls with evidence in Task Results. When the examiner asks *"where do heavy aggregations run, and how do you prevent dual-runs,"* you show server inventory, schedule stagger table, and Task Result host/timing — not “we hope cron is fine.”

---

## Concepts

### Core terms

| Term | Meaning |
| --- | --- |
| **UI / Request host** | Serves browsers and lightweight work |
| **Task server** | Runs aggregations, refresh, certifications generation |
| **Partitioning** | Splits aggregation/request work across threads/hosts by partition keys |
| **Server** object | IIQ’s view of a JVM node and its roles |

### Meridian placement sketch

| Workload | Preferred host role |
| --- | --- |
| Interactive UI / LCM | UI servers |
| Account Aggregation (AD, Core, AWS) | Task servers |
| Identity Refresh large | Task servers |
| Report generation heavy | Task or reporting node |

**Lab reality:** Single-node Tomcat still teaches partitioning options and schedule hygiene; document “would pin to task host in prod.” Homelab may run single JVM; production blueprint (Lesson 110) must still show separate pools.

### Real-life Meridian example

HR, AD, and Identity Refresh all started at 02:00. The DB melted; morning joiners for `nina.joiner` had stale cubes. Stagger (HR → AD → refresh) restored freshness without new hardware. Partitioning helped AD; schedule hygiene helped everything.

### Wrong way vs Meridian way

| Wrong way | Why it fails | Meridian way |
| --- | --- | --- |
| All heavy jobs on UI node | Operator freezes | Pin aggregations to task hosts |
| Identical start times | DB/connector contention | Stagger schedules |
| Dual schedules for same agg | Duplicate links / orphans | One schedule; mutex discipline |
| Ignore NTP | SIEM/audit skew (Lesson 104) | Sync clocks before trusting correlations |

---

## How it works

```
  Schedule: Aggregate MNB-ActiveDirectory
        │
        ▼
  Task server host (not UI)
        │
        ├── Partition 0..N  ---> connector threads
        │
        ▼
  Task Result counters + errors (+ host name if shown)
```

| Dependency | Order rationale |
| --- | --- |
| `MNB-HR` aggregation | Authoritative identities first |
| Directory / target aggs (`MNB-ActiveDirectory`, …) | Correlate against existing cubes |
| Identity Refresh | Compute attributes / roles after accounts land |

IQService reachability must be tested from the **task** host network namespace (K8s/homelab gotcha).

---

## Real-world setup (topology before hero threads)

### Step 1 — Inventory servers

1. List Server objects / hosts with heartbeat.
2. Mark UI vs task roles in a 2-node design even if lab is 1-node.

### Step 2 — Partition large apps

1. Prefer connector partitioning / threads where supported.
2. Else document filter-based split (OU/host) for `MNB-ActiveDirectory`.

### Step 3 — Schedule stagger + collision control

1. No identical start stamps for heavy jobs.
2. Document restart behavior if task host dies mid-agg.

### Step 4 — Multi-host readiness

1. Unique server names, NTP, shared DB, sticky UI sessions, IQService from task hosts, AuditConfig clock alignment.

---

## Before you start

- [ ] List Meridian aggregation task names already in lab
- [ ] Access to Task Definition editor as `spadmin`
- [ ] Read `servers.properties` SPTARGET mapping (Lesson 101)
- [ ] Note whether cluster is single or multi JVM
- [ ] Binder: `ops/partitioning/`

---

## Lab procedure

### Task 1 — Inventory servers

You cannot pin work to a host you have not named.

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

**If it fails:** Connector lacks partition UI — document filter-based split strategy (OU/host) instead.

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
3. Homelab note: K8s replicas may blur UI/task — document how Meridian will separate pools in prod Helm values.

**Expected result:** Multi-host readiness checklist completed.

### Task 7 — Capacity planning worksheet + failure domain

Fill:

| App | Est. accounts | Full agg duration baseline | Partition plan | Task host |
| --- | --- | --- | --- | --- |
| MNB-ActiveDirectory | (lab count) | (min) | OU / threads | task-1 |
| MNB-CoreBanking | | | | task-1 |
| MNB-AWS-Cloud | | | | task-1 |
| MNB-HR | | | often lighter | ui or task |

Then write failure-domain notes:

1. If task host dies mid-aggregation, document restart behavior (resume vs restart full).
2. Ensure UI hosts can still process LCM approvals during agg outage.
3. IQService reachability must be tested from the task host network namespace.

**Expected result:** Worksheet with real Task Result numbers + failure-domain paragraph.

### Task 8 — Examiner question drill

*"Where do heavy aggregations run, and how do you prevent dual-runs?"*

Write the three-artifact answer: (1) server inventory with UI vs task roles, (2) schedule stagger table, (3) Task Result showing host/timing for `MNB-ActiveDirectory` (or largest app).

**Expected result:** Written proof steps in the binder.

---

## Acceptance criteria

- [ ] Server inventory captured
- [ ] Partitioning or split strategy documented for one large app
- [ ] Host pin or description intent set
- [ ] Staggered schedule table filed
- [ ] One Task Result evidenced
- [ ] Multi-host checklist complete
- [ ] Capacity worksheet + failure-domain notes filed
- [ ] Examiner proof steps drafted

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Task stuck Pending | Wrong host / host down | Check Server heartbeat; clear host pin |
| Duplicate aggregations | Two schedules | Disable duplicate; use mutex discipline |
| Partition errors | Uneven filters | Balance OU/host partitions |
| UI timeouts during agg | Agg on UI node | Move to task host |
| Clock skew across nodes | NTP missing | Sync time before trusting audits |
| IQService fails only on task pod | Network policy | Test from task namespace |

---

## Training binder evidence

- Server inventory
- Partitioning notes
- Schedule stagger table
- Task Result ID/screenshot
- Multi-host checklist
- Capacity worksheet + failure-domain notes
- Examiner proof steps

---

## Knowledge check

1. Why separate task servers from UI servers?
2. What does aggregation partitioning accomplish?
3. Name a safe Meridian schedule order for HR vs AD vs refresh.
4. Why does NTP matter for AuditConfig/SIEM?
5. What evidence proves a partitioned job ran?
6. Why must IQService be tested from the task host?

### Answers

1. Protect interactive latency; isolate heavy connector CPU/IO.
2. Parallelizes work across partitions/threads/hosts for throughput.
3. Authoritative HR first, then directories/targets, then identity refresh (adjust to your dependency graph).
4. Correlating events across nodes/SIEM requires aligned timestamps.
5. Task Result with timing/counters (and host name if shown).
6. AD/Windows ops often run where the aggregation runs — UI reachability is not enough.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “task servers,” “partitioning,” and “Server object” for cluster role configuration.
- [SailPoint Community / Compass](https://community.sailpoint.com/) — search “aggregation partitioning best practices” for OU-split patterns.
- [docs/SSD.md](../SSD.md) — `servers.properties` and SPTARGET mapping for multi-host builds.
- [NIST SP 800-53 Rev. 5 — CP / AU families](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — contingency planning for processing nodes and audit timestamp integrity.
- [FFIEC IT Handbook — Architecture, Infrastructure, and Operations](https://ithandbook.ffiec.gov/) — capacity and operational resilience expectations for critical bank platforms.

---

## Stretch lab

Design OU-based partitions for `MNB-ActiveDirectory` (e.g. by branch OU) with a rollback plan if a partition fails. Include how Task Results prove each partition completed.

---

## Summary

- Pin heavy Meridian jobs to task capacity; partition large aggregations.
- Stagger schedules; prove runs with Task Results.
- Multi-host readiness includes NTP, naming, IQService reachability, and role separation — even when lab is single-node.

---

**Previous:** [Lesson 104 — AuditConfig & SIEM](104-auditconfig-and-siem.md)  
**Next:** [Lesson 106 — Performance Tuning IIQ](106-performance-tuning-iiq.md)
