# Lesson 106 — Performance Tuning IIQ

| Field | Value |
| --- | --- |
| **Level** | Advanced |
| **Track** | Enterprise Hardening & Mastery |
| **Time** | 75–90 minutes |
| **Prereq** | [Lesson 105 — Partitioning & Task Servers](105-partitioning-task-servers.md) |
| **Lab data** | Task Results from Lesson 105; DB access per LOCAL_SETUP; JVM notes from deploy docs |

## Learning objectives

You will be able to:

- Build a Meridian performance baseline (UI login, identity search, one aggregation, one refresh)
- Identify tuning levers: JVM heap, DB indexes, IIQ caches, connector thread pools, partitioning
- Apply one safe lab tuning change and re-measure
- Recognize anti-patterns (debug logging in prod, unbounded searches, full agg hourly)
- Draft an SLO table for IAM operations

## Why this matters

Slow identity search during an incident means leavers stay active longer. Performance is a control latency problem, not only a comfort issue.

**Control / audit:** SLOs for aggregation freshness and LCM completion are exam-relevant for “timely revocation.” Tuning changes need tickets and before/after metrics.

## Concepts

| Layer | Levers |
| --- | --- |
| Browser / UI | Search limits, projection attributes, CDN/static caching |
| App JVM | Heap, GC, thread pools, connection pools |
| IIQ caches | Identity/ManagedAttribute caches—warm vs stale tradeoffs |
| Database | Indexes on identity/link tables, vacuum/stats, pool size |
| Connectors | Threads, deltas vs full, filters, IQService capacity |
| Topology | Task vs UI split (Lesson 105) |

```text
  Measure baseline
       |
       v
  Hypothesize bottleneck (UI / DB / connector / JVM)
       |
       v
  One change + ticket
       |
       v
  Re-measure --> keep / revert
```

**Meridian lab SLOs (starting point—adjust to bank)**

| Metric | Lab target | Prod aspirational |
| --- | --- | --- |
| Login interactive | < 3s | < 2s |
| Identity warehouse search | < 5s typical | < 3s |
| HR aggregation freshness | ≤ 24h | ≤ 4–12h per policy |
| Leaver disable SLA | Same business day | Hours per playbook |

## Before you start

- [ ] Stopwatch or browser network timing available
- [ ] Task Result history for one aggregation
- [ ] Ability to view logs (not DEBUG in shared prod-like env)
- [ ] Change note template ready

## Lab procedure

### Task 1 — Capture baseline

1. Cold-ish login as `helen.ross`; record time to home.
2. Search Identity Warehouse for `priya.wire`; record time to open cube.
3. From latest Task Results, record duration for one Meridian aggregation and one refresh.
4. Store as `MNB-Perf-Baseline-YYYY-MM-DD`.

**Expected result:** Four-metric baseline sheet.

**If it fails:** Use Task Result durations alone; still date the sheet.

### Task 2 — Bottleneck hypothesis

1. If UI slow but tasks fine → UI/cache/DB select hypothesis.
2. If aggregation hours long → connector/partition/IQService hypothesis.
3. Write one primary hypothesis; avoid multi-change experiments.

**Expected result:** Single written hypothesis.

### Task 3 — Safe inspection (no reckless flips)

1. Check logging levels—ensure not TRACE/DEBUG globally.
2. Review aggregation: full vs delta; filters present?
3. Review identity search: are operators using unbounded Advanced Analytics?
4. Note JVM max heap from startup scripts/container limits (homelab Helm values if used).

**Expected result:** Inspection checklist with findings.

### Task 4 — One controlled tune

1. Pick **one** change, examples:
   - Enable delta aggregation for a file/JDBC app if full runs too often
   - Reduce schedule frequency of a redundant full agg
   - Increase partition/threads modestly (Lesson 105)
   - Add search best-practice: require 2+ chars (process control)
2. Record before metric, change, after metric.
3. Revert if worse.

**Expected result:** Before/after pair for one lever.

**If it fails:** Paper-tune only with predicted impact—still complete SLO table.

### Task 5 — Cache / staleness note

1. Document which caches exist conceptually (identity cubes, entitlements).
2. Write Meridian rule: after emergency entitlement fix, know whether refresh/cache clear is required before cert.
3. Never “clear all caches hourly” as a lifestyle.

**Expected result:** Cache hygiene paragraph.

### Task 6 — SLO + capacity board

1. Finalize SLO table for Meridian IAM.
2. List top three capacity risks (AD size, cert explosion, report season).
3. Assign owners: platform (`sofia.torres` lab), IAM (`helen.ross`).

**Expected result:** SLO + risk board page.

## Acceptance criteria

- [ ] Dated performance baseline
- [ ] One bottleneck hypothesis
- [ ] Logging not left at DEBUG
- [ ] One measured tune or documented paper-tune
- [ ] Cache hygiene note
- [ ] SLO table with owners

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Slow search | Missing DB indexes / huge result | DBA review; narrow query |
| Agg regression after threads↑ | Target throttling | Back off threads; contact app owner |
| Memory thrash | Heap too small / leak | Heap dump discipline; size JVM |
| “Faster” but wrong data | Delta misconfig | Validate counts vs source |
| UI still slow on task host mix | Topology | Separate pools (Lesson 105) |

## Training binder evidence

- Baseline + after metrics  
- Change ticket / note  
- Inspection checklist  
- SLO table  

## Knowledge check

1. Why is IAM performance a control issue?
2. Name four tuning layers.
3. What is wrong with changing heap, threads, and schedules in one night?
4. When are full aggregations still required?
5. Who shares ownership of capacity risks?

### Answers

1. Slow revoke/search extends exposure windows.  
2. UI, JVM, caches, DB, connectors, topology.  
3. Cannot attribute effect; hard to revert safely.  
4. When deltas unsupported or integrity drift suspected—on a controlled cadence.  
5. Platform/infra and IAM (lab: sofia.torres / helen.ross).

## Stretch lab

Chart aggregation durations for one week of Task Results; flag variance > 2× median.

## Summary

- Baseline before tuning; change one lever; re-measure.
- Performance SLOs protect revocation and exam timelines.
- Topology + connector design beat random JVM folklore.

## Aggregation hygiene checklist

- [ ] Prefer delta where connector supports and integrity allows
- [ ] Filters exclude deactivated OU/test trees when safe
- [ ] Thread count agreed with target system owners
- [ ] Schedules staggered (Lesson 105)
- [ ] Task Results retained long enough for trend charts
- [ ] Error thresholds alert IAM ops (`MNB-WG-IAM-Ops`)

### Task 7 — Operator search education

1. Publish a one-pager: how to search identities without full-table scans (required fields, max results).
2. Ban “empty search export everything” on prod-like data.
3. File as process control supporting performance SLOs.

**Expected result:** Search hygiene one-pager.

### JVM / container limits (homelab)

Document current Helm/memory limits if running K8s. Increasing threads without memory headroom causes GC thrash—tune topology before heroic heap increases.

---

**Previous:** [Lesson 105 — Partitioning & Task Servers](105-partitioning-task-servers.md)  
**Next:** [Lesson 107 — Backup, DR & Object Recovery](107-backup-dr-object-recovery.md)
