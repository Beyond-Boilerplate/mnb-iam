# Lesson 106 — Performance Tuning IIQ

**Level:** Advanced  
**Track:** Enterprise Hardening & Mastery  
**Time:** 75–90 min  
**Prereq:** Lesson 105 — Partitioning & Task Servers  

**Lab data:**
- Task Results from Lesson 105
- DB access per LOCAL_SETUP
- JVM notes from deploy docs / homelab Helm values

---

## Learning objectives

You will be able to:

- Build a Meridian performance baseline (UI login, identity search, one aggregation, one refresh)
- Identify tuning levers: JVM heap, DB indexes, IIQ caches, connector thread pools, partitioning
- Apply one safe lab tuning change and re-measure
- Recognize anti-patterns (debug logging in prod, unbounded searches, full agg hourly)
- Draft an SLO table for IAM operations with owners
- Publish operator search hygiene that protects warehouse performance

---

## Why this matters

**Business.** Slow identity search during an incident means leavers stay active longer. When SOC pages IAM about `jordan.reed` termination and `helen.ross` waits 40 seconds per cube open, disable SLA slips. Performance is a **control latency** problem, not only a comfort issue.

**Control / audit.** SLOs for aggregation freshness and LCM completion are exam-relevant for “timely revocation.” Tuning changes need tickets and before/after metrics. When the examiner asks *"what is your aggregation freshness SLO and how do you prove it,"* you show dated baselines and Task Result trends — not folklore about heap sizes.

---

## Concepts

### Tuning layers

| Layer | Levers |
| --- | --- |
| Browser / UI | Search limits, projection attributes, CDN/static caching |
| App JVM | Heap, GC, thread pools, connection pools |
| IIQ caches | Identity/ManagedAttribute caches — warm vs stale tradeoffs |
| Database | Indexes on identity/link tables, vacuum/stats, pool size |
| Connectors | Threads, deltas vs full, filters, IQService capacity |
| Topology | Task vs UI split (Lesson 105) |

### Meridian lab SLOs (starting point — adjust to bank)

| Metric | Lab target | Prod aspirational |
| --- | --- | --- |
| Login interactive | < 3s | < 2s |
| Identity warehouse search | < 5s typical | < 3s |
| HR aggregation freshness | ≤ 24h | ≤ 4–12h per policy |
| Leaver disable SLA | Same business day | Hours per playbook |

### Measure → hypothesize → one change → re-measure

```
  Measure baseline
       │
       ▼
  Hypothesize bottleneck (UI / DB / connector / JVM)
       │
       ▼
  One change + ticket
       │
       ▼
  Re-measure --> keep / revert
```

**Wrong way:** Change heap, threads, and schedules in one night — cannot attribute effect. **Meridian way:** one lever, dated before/after, revert if worse.

### Real-life Meridian example

Operators ran Advanced Analytics with empty search “export everything” every morning. Warehouse slowed; aggregations overlapped. A process control (require 2+ characters, ban empty exports on prod-like data) recovered more performance than a heroic heap bump.

### Aggregation hygiene checklist

- Prefer delta where connector supports and integrity allows
- Filters exclude deactivated OU/test trees when safe
- Thread count agreed with target system owners
- Schedules staggered (Lesson 105)
- Task Results retained long enough for trend charts
- Error thresholds alert IAM ops (`MNB-WG-IAM-Ops`)

---

## How it works

| Symptom pattern | Primary hypothesis | First lever |
| --- | --- | --- |
| UI slow; tasks fine | UI/cache/DB select | Search hygiene; indexes |
| Aggregation hours long | Connector/partition/IQService | Partition; delta; task host |
| Memory thrash | Heap / leak / too many threads | Topology before heroic heap |
| “Faster” but wrong counts | Delta misconfig | Validate vs source |

Owners: platform (`sofia.torres` lab), IAM (`helen.ross`). Capacity risks: AD size, cert explosion, report season.

---

## Real-world setup (performance as a control)

### Step 1 — Baseline with dates

1. Four metrics: login, search, agg duration, refresh duration.
2. File `MNB-Perf-Baseline-YYYY-MM-DD`.

### Step 2 — Inspection without reckless flips

1. Logging not TRACE/DEBUG globally.
2. Full vs delta; filters; JVM limits.

### Step 3 — One controlled tune + ticket

1. Change one lever; record before/after; revert if worse.

### Step 4 — SLO board + search education

1. Publish SLOs and operator search one-pager.
2. Increasing threads without memory headroom causes GC thrash — tune topology first.

---

## Before you start

- [ ] Stopwatch or browser network timing available
- [ ] Task Result history for one aggregation (Lesson 105)
- [ ] Ability to view logs (not DEBUG in shared prod-like env)
- [ ] Change note template ready
- [ ] Binder: `ops/performance/`

---

## Lab procedure

### Task 1 — Capture baseline

Without a baseline, every tune is storytelling.

1. Cold-ish login as `helen.ross`; record time to home.
2. Search Identity Warehouse for `priya.wire`; record time to open cube.
3. From latest Task Results, record duration for one Meridian aggregation and one refresh.
4. Store as `MNB-Perf-Baseline-YYYY-MM-DD`.

**Expected result:** Four-metric baseline sheet.

**If it fails:** Use Task Result durations alone; still date the sheet.

### Task 2 — Bottleneck hypothesis

1. If UI slow but tasks fine → UI/cache/DB select hypothesis.
2. If aggregation hours long → connector/partition/IQService hypothesis.
3. Write **one** primary hypothesis; avoid multi-change experiments.

**Expected result:** Single written hypothesis.

### Task 3 — Safe inspection (no reckless flips)

1. Check logging levels — ensure not TRACE/DEBUG globally.
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
2. Record before metric, change, after metric, ticket id `LAB-PERF-106`.
3. Revert if worse.

**Expected result:** Before/after pair for one lever.

**If it fails:** Paper-tune only with predicted impact — still complete SLO table.

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

### Task 7 — Operator search education

1. Publish a one-pager: how to search identities without full-table scans (required fields, max results).
2. Ban “empty search export everything” on prod-like data.
3. File as process control supporting performance SLOs.

**Expected result:** Search hygiene one-pager.

### Task 8 — Examiner question drill

*"What is your aggregation freshness SLO and how do you prove it?"*

Write the three-artifact answer: (1) SLO table with HR/AD freshness targets, (2) dated baseline + Task Result durations, (3) schedule stagger from Lesson 105 showing jobs can complete inside the SLO window.

**Expected result:** Written proof steps in the binder.

---

## Acceptance criteria

- [ ] Dated performance baseline
- [ ] One bottleneck hypothesis
- [ ] Logging not left at DEBUG
- [ ] One measured tune or documented paper-tune
- [ ] Cache hygiene note
- [ ] SLO table with owners
- [ ] Search hygiene one-pager
- [ ] Examiner proof steps drafted

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Slow search | Missing DB indexes / huge result | DBA review; narrow query |
| Agg regression after threads↑ | Target throttling | Back off threads; contact app owner |
| Memory thrash | Heap too small / leak / too many threads | Topology first; heap dump discipline |
| “Faster” but wrong data | Delta misconfig | Validate counts vs source |
| UI still slow on task host mix | Topology | Separate pools (Lesson 105) |
| No attribution | Multi-change night | Revert; redo one lever |

---

## Training binder evidence

- Baseline + after metrics
- Change ticket / note `LAB-PERF-106`
- Inspection checklist
- SLO table + capacity risks
- Search hygiene one-pager
- Examiner proof steps

---

## Knowledge check

1. Why is IAM performance a control issue?
2. Name four tuning layers.
3. What is wrong with changing heap, threads, and schedules in one night?
4. When are full aggregations still required?
5. Who shares ownership of capacity risks?
6. What operator behavior often hurts warehouse performance more than JVM size?

### Answers

1. Slow revoke/search extends exposure windows.
2. UI, JVM, caches, DB, connectors, topology (any four+).
3. Cannot attribute effect; hard to revert safely.
4. When deltas unsupported or integrity drift suspected — on a controlled cadence.
5. Platform/infra and IAM (lab: `sofia.torres` / `helen.ross`).
6. Unbounded empty searches / full exports.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “performance,” “caching,” and “aggregation best practices” for version-specific levers.
- [SailPoint Community / Compass](https://community.sailpoint.com/) — search “IdentityIQ performance tuning” for DB index and thread discussions.
- [NIST SP 800-53 Rev. 5 — SI-2 / CP-2](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — flaw remediation / capacity planning mindset for platform performance.
- [FFIEC IT Handbook — Architecture, Infrastructure, and Operations](https://ithandbook.ffiec.gov/) — capacity management and operational monitoring for critical systems.
- [OWASP Performance Testing guidance (project hub)](https://owasp.org/www-project-web-security-testing-guide/) — testing discipline: measure, change one variable, retest (adapt mindset to IAM platforms).

---

## Stretch lab

Chart aggregation durations for one week of Task Results; flag variance > 2× median. Document JVM/container memory limits if running K8s and relate them to thread settings from Lesson 105. Rule of thumb: raise connector threads only after confirming heap and DB pool headroom with platform (`sofia.torres`) — topology (Lesson 105) before heroic JVM flag changes.

---

## Capacity board agenda (optional paste into binder)

| Risk | Owner | Trigger |
| --- | --- | --- |
| AD account growth | IAM + AD ops | Full agg duration > 2× baseline |
| Cert campaign explosion | IAM + Risk | Generation task exceeds overnight window |
| Report season load | Platform | UI login SLO breached during month-end |

---

## Summary

- Baseline before tuning; change one lever; re-measure.
- Performance SLOs protect revocation and exam timelines.
- Topology + connector design + search hygiene beat random JVM folklore.

---

**Previous:** [Lesson 105 — Partitioning & Task Servers](105-partitioning-task-servers.md)  
**Next:** [Lesson 107 — Backup, DR & Object Recovery](107-backup-dr-object-recovery.md)
