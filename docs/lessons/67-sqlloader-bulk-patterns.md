# Lesson 67 — SQLLoader & Bulk Load Patterns

**Level:** Intermediate  
**Track:** Connectors — Databases  
**Time:** 60–75 min  
**Prereq:** Lesson 66 — Oracle Database Direct; Lesson 63 JDBC fundamentals  

**Lab data:**
- Repo: `lab-data/connectors/jdbc/sample-rows.csv`
- Repo: `lab-data/connectors/jdbc/mnb_core_accounts.sql`
- Runtime: `~/iiq-lab-data/connectors/jdbc/`

---

## Learning objectives

You will be able to:

- Explain when Meridian uses **SQLLoader / bulk** patterns versus iterative JDBC or Direct connectors
- Design a bulk feed contract (file layout, control file notes, idempotent load keys)
- Build `MNB-SQLLoader-Bulk` application or feed checklist without a live Oracle SQL*Loader job
- Define reconciliation: bulk load → Account Aggregation → cube verification
- Document failure modes (partial load, duplicate keys, late files) for ops SLAs

---

## Why this matters

**Business.** Nightly warehouse and GL extracts can exceed interactive aggregation comfort. Meridian ops need a governed bulk path so large account inventories land predictably before morning certifications.

**Control / audit.** Examiners ask whether bulk jobs are monitored, idempotent, and reconcilable to IdentityIQ—not whether someone ‘ran a script.’ Task Results plus load control evidence close that gap.

---

## Concepts

**SQLLoader / bulk pattern.** External process (Oracle SQL*Loader, `COPY`, ETL) lands rows into a staging table or file; IdentityIQ then aggregates via JDBC/DelimitedFile. IIQ is rarely the loader itself—governance wraps the feed.

```
Source system extract
        │
        ▼
 Bulk loader (SQL*Loader / ETL)  →  staging table or file
        │
        ▼
 IIQ Account Aggregation (JDBC or DelimitedFile)
        │
        ▼
 Correlation + Identity Refresh
```

| Pattern | Use when | Risk |
| --- | --- | --- |
| Iterative Direct/JDBC | Moderate volumes, need live provision | Timeout / lock contention |
| Bulk + aggregate | Large nightly inventories | Stale mid-day; partial loads |
| Delta file | Change-only feeds | Missed deletes if no tombstones |

**Meridian rule:** Prefer bulk for *read inventory*; keep provisioning on Direct/JDBC with stored procs where possible (Lesson 64).

---

## Before you start

- [ ] IIQ up; Lessons 63–66 concepts reviewed
- [ ] `~/iiq-lab-data/connectors/jdbc/sample-rows.csv` present
- [ ] Understand `mnb_app_accounts` schema from SQL fixture
- [ ] Notebook for `MNB-SQLLoader-Bulk` naming

---

## Lab procedure

### Task 1 — Classify Meridian feeds

1. List three Meridian sources: Oracle GL users, core banking extract, Wire Portal API.
2. Mark each: iterative connector vs bulk+aggregate.
3. Align with matrix: databases may still use Direct; bulk is an *ops pattern*, not a matrix connector name.

**Expected result:** Table Source | Pattern | Why.

**If it fails:** Start with: warehouse-sized Oracle extract = bulk; Wire Portal = Web Services (Lesson 68).

### Task 2 — Design the bulk contract

1. Using `sample-rows.csv` as a model, define required columns: `account_id`, `username`, `email`, `employee_id`, `status`, `entitlement`.
2. Specify native identity = `account_id` or `username` (pick one; document).
3. Write idempotency rule: same `account_id` upserts; missing rows with `status=DELETED` or separate revoke file.
4. Name control artifact: `MNB-SQLLoader-Bulk-Control-YYYYMMDD.ctl` (document fields even if file is stub).

**Expected result:** One-page feed contract in binder.

**If it fails:** Copy headers exactly from `sample-rows.csv` and annotate.

### Task 3 — Lab-without-live-target application

Use the **lab-without-live-target** path when Oracle SQL*Loader / live staging DB is unavailable: configure IIQ against the landed file fixture only.

1. Create DelimitedFile (or JDBC-to-staging) application `MNB-SQLLoader-Bulk`.
2. Point file path to `~/iiq-lab-data/connectors/jdbc/sample-rows.csv` (or a copied bulk file).
3. Map schema; mark entitlement column managed.
4. Owner: `helen.ross`; note “bulk inventory only—no provisioning” unless you add policies later.

**Expected result:** App saves; schema shows expected attributes.

**If it fails:** Use DelimitedFile wizard; match Lesson 11 patterns.

### Task 4 — Account Aggregation and reconcile

1. Create task `MNB-SQLLoader-Bulk-Account-Aggregation`.
2. Run **Account Aggregation**; record counts.
3. Compare row count in CSV vs aggregated accounts (spot-check `priya.wire` / fixture usernames if present).
4. Document SLA: aggregation must complete by 06:00 local before manager certs.

**Expected result:** Counts match; Task Result Success archived.

**If it fails:** Check delimiter/header; fix path; re-run.

### Task 5 — Partial-load failure drill (safe)

1. Copy CSV to `sample-rows-partial.csv`; delete half the rows.
2. Point app at partial file; aggregate; note lower count.
3. Restore full file; re-aggregate; confirm recovery.
4. Write ops note: *Never certify from a partial bulk night without count gates.*

**Expected result:** Binder shows before/after counts and restore proof.

**If it fails:** Keep original path noted so you can restore quickly.

---


### Task 6 — Control owner & examiner prep

1. Assign control owner: IAM Lead `helen.ross`; feed owner (DBA/ETL) `samir.hassan`.
2. Write SLA: bulk file landed by 04:30; Account Aggregation success by 06:00; page on count delta > 5%.
3. List evidence examiners will request: control file stub name, Task Result, count reconcile sheet.

**Expected result:** Owner/SLA/evidence triple on one binder page.

**If it fails:** Use Meridian naming `MNB-SQLLoader-Bulk-*` for all artifacts.


---

## Acceptance criteria

- [ ] Feed contract (columns, native id, idempotency) documented
- [ ] `MNB-SQLLoader-Bulk` app configured against lab fixture
- [ ] Account Aggregation Task Result with count reconciliation
- [ ] Partial-load drill completed and restored
- [ ] SLA / count-gate note written for examiners
- [ ] Control owner and examiner evidence list documented

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Count mismatch | Header/duplicate keys / filter | Diff CSV vs aggregation report; fix schema |
| Stale cubes | Aggregation not scheduled | Schedule task; document timezone |
| Deletes not reflected | No tombstone/status | Add status=DELETED or full replace semantics |
| Loader succeeded, IIQ empty | Wrong path / staging table | Verify IIQ reads same artifact loader wrote |
| Accidental provisioning | PROVISIONING enabled on bulk app | Disable provisioning features on inventory-only apps |

---

## Training binder evidence

- Feed contract page
- App config screenshot (path visible)
- Aggregation Task Result + counts
- Partial-load drill notes
- SLA count-gate statement

---

## Knowledge check

1. Is SQLLoader typically an IIQ connector type or an external bulk pattern?
2. What Meridian app name did you use for the bulk inventory?
3. Why run a partial-load drill?
4. What should happen before morning certifications after a bulk night?
5. Name one idempotency key approach from this lab.

### Answers

1. External bulk/ETL pattern; IIQ aggregates the landed data via JDBC or DelimitedFile.
2. `MNB-SQLLoader-Bulk`.
3. To prove count gates catch incomplete feeds before certs.
4. Successful Account Aggregation with reconciled counts (and correlation/refresh as designed).
5. `account_id` upsert (or documented username key) with explicit delete/tombstone handling.

---

## Stretch lab

Sketch a partitioned aggregation plan for >100k rows (filters by `entitlement` or hash ranges). Reference Lesson 54 concepts without requiring multi-host lab.

---

## Summary

- Bulk patterns land large inventories; IIQ still needs aggregation and reconciliation evidence.
- `MNB-SQLLoader-Bulk` demonstrates governed inventory without live SQL*Loader.
- Count gates and partial-load drills protect certification integrity.

---

**Previous:** [Lesson 66 — Oracle Database Direct Connector](66-oracle-db-direct-connector.md)  
**Next:** [Lesson 68 — Web Services Connector](68-web-services-connector.md)
