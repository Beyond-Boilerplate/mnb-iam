# Lesson 67 — SQLLoader Bulk Patterns

**Level:** Intermediate  
**Track:** Connectors — Databases  
**Time:** 75–90 min  
**Prereq:** Lesson 66 — Oracle Database Direct; Lesson 63 JDBC fundamentals  

**Lab data:**
- Repo: `lab-data/connectors/jdbc/sample-rows.csv`
- Repo: `lab-data/connectors/jdbc/mnb_core_accounts.sql`
- Repo: `lab-data/connectors/connector-selection-matrix.csv`
- Runtime: `~/iiq-lab-data/connectors/jdbc/`

---

## Learning objectives

You will be able to:

- Explain when Meridian uses **SQL*Loader / bulk ETL** patterns versus iterative JDBC or Direct connectors
- Design a bulk feed contract (columns, native identity, idempotency, tombstones, control file)
- Configure **MNB-SQLLoader-Bulk** against the lab fixture and reconcile Account Aggregation counts
- Run a partial-load failure drill with count gates that protect morning certifications
- Document SLA, control owners, and examiner evidence for bulk nights

---

## Why this matters

**Business.** Nightly warehouse and GL extracts can be hundreds of thousands of rows — too large or too locked for comfortable mid-day Direct aggregation. Meridian ops need a governed bulk path so inventories land predictably before manager certifications open.

**Control / audit.** Examiners ask whether bulk jobs are monitored, idempotent, and reconcilable to IdentityIQ — not whether someone “ran a script.” Task Results plus load control evidence and count gates close that gap. Certifying from a half-loaded night is how toxic access slips through.

---

## Concepts

### Bulk is an ops pattern, not a matrix connector type

The selection matrix names **JDBC**, **Oracle Direct**, **Web Services** — it does not list “SQLLoader” as a preferred connector. **SQL*Loader / COPY / ETL** is how data *lands*; IdentityIQ still aggregates via **JDBC** (staging table) or **DelimitedFile** (landed file).

| Pattern | Use when | Risk if misused |
| --- | --- | --- |
| Iterative Direct/JDBC | Moderate volumes; live provision | Timeout / lock contention |
| Bulk + aggregate | Large nightly inventories | Stale mid-day; partial loads |
| Delta file | Change-only feeds | Missed deletes without tombstones |

**Meridian rule:** Prefer bulk for *read inventory*; keep provisioning on Direct/JDBC with stored procs (Lesson 64). Do not enable `PROVISIONING` on inventory-only bulk apps.

### Idempotency and deletes

Full-replace feeds: same `account_id` upserts; absences mean gone **only if** you truncate-and-load or send explicit tombstones (`status=DELETED` / revoke file). Naive “file replaces yesterday” without a delete story leaves ghosts on cubes.

### Count gates

Before certifications: `|tonight − baseline| / baseline > 5%` → page and **block cert launch**. Partial-load drills prove the gate works.

```
Source system extract
        │
        ▼
 Bulk loader (SQL*Loader / ETL / COPY)  →  staging table or file
        │
        ▼
 IIQ Account Aggregation (JDBC or DelimitedFile)
        │
        ▼
 Correlation + Identity Refresh → certs only if counts pass
```

---

## How it works

Externally, Oracle SQL*Loader (or Postgres `COPY`, Informatica, etc.) writes a staging artifact. IdentityIQ does not replace the loader — it consumes the result on a schedule. Governance owns: contract, SLA, aggregation task, count reconcile, and “do not certify” break-glass.

```
04:30  file/table landed (ETL owner: samir.hassan)
        │
06:00  MNB-SQLLoader-Bulk-Account-Aggregation success
        │
        ├── count gate pass → refresh / certs OK
        └── count gate fail → page helen.ross; hold certs
```

| Artifact | Owner | Purpose |
| --- | --- | --- |
| Control file / job log | ETL/DBA | Proves load ran |
| Staging file/table | ETL | What IIQ reads |
| Aggregation Task Result | IAM | Proves IIQ consumed it |
| Count reconcile sheet | IAM | Examiner freshness proof |

---

## Real-world setup (outside IIQ)

### Step 1 — Agree the feed contract with ETL

1. Columns, delimiter, header, timezone, late-file handling.
2. Native identity key (`account_id` recommended).
3. Delete/tombstone semantics in writing.
4. Landing path or staging schema grants for the IIQ RO account.

### Step 2 — Schedule dependency chain

1. Source extract → loader → IIQ aggregation → Identity Refresh.
2. Do not schedule certs before aggregation SLA (06:00 lab example).
3. Page on loader failure **and** on count-gate failure (different runbooks).

### Step 3 — Inventory-only application hygiene

1. Disable provisioning features on the bulk inventory app.
2. Create-identities **OFF**; HR remains authoritative.
3. Name clearly: `MNB-SQLLoader-Bulk` — not confused with `MNB-CoreBanking-JDBC` live provision path.

### Step 4 — Evidence retention

Retain control logs + Task Results per bank retention (often ≥1 year for access reviews).

---

## Before you start

- [ ] IIQ up; Lessons 63–66 concepts reviewed
- [ ] `~/iiq-lab-data/connectors/jdbc/sample-rows.csv` and SQL fixture present
- [ ] Understand `mnb_app_accounts` columns from `mnb_core_accounts.sql`
- [ ] Binder page ready for feed contract + SLA

---

## Lab procedure

### Task 1 — Classify Meridian feeds

Bulk vs iterative is an architecture choice — write it down before configuring anything.

1. Classify:

| Source | Pattern | Why |
| --- | --- | --- |
| Oracle GL users (moderate) | Oracle Direct iterative | Native roles + provision |
| Warehouse-sized GL extract | Bulk + aggregate | Volume / lock windows |
| Core banking live table | JDBC iterative (+ procs) | Dual-control provision |
| Wire Portal API | Web Services (L68) | Real-time entitlements |

2. Note: bulk is an *ops pattern*, not a matrix connector name.

**Expected result:** Classification table in binder.

### Task 2 — Design the bulk contract

Using `sample-rows.csv` as the model feed.

1. Required columns: `account_id`, `username`, `email`, `employee_id`, `status`, `entitlement`.
2. Native identity = `account_id` (document; do not silently switch to username).
3. Idempotency: same `account_id` upserts; deletes via `status=DELETED` or separate revoke file — pick one and write it.
4. Control artifact name: `MNB-SQLLoader-Bulk-Control-YYYYMMDD.ctl` (stub fields: infile, table, errors, rows expected).

**Expected result:** One-page feed contract.

**If it fails:** Copy headers exactly from `sample-rows.csv` and annotate.

### Task 3 — Create MNB-SQLLoader-Bulk (lab-without-live SQL*Loader)

When Oracle SQL*Loader / staging DB is unavailable, configure IIQ against the landed file fixture — that is still the real aggregation half of the pattern.

1. Applications → Add New → **DelimitedFile** (or JDBC-to-staging if you have jdbc-pg staging — file path is the default lab).
2. Name: `MNB-SQLLoader-Bulk`. Owner: `helen.ross`; feed owner `samir.hassan`.
3. Point at `~/iiq-lab-data/connectors/jdbc/sample-rows.csv`.
4. Map schema; mark `entitlement` managed; create-identities **OFF**; no provisioning.
5. Save.

**Expected result:** App saves; schema shows expected attributes; inventory-only noted.

**If it fails:** Match Lesson 11 delimited patterns; check path/delimiter.

### Task 4 — Account Aggregation and reconcile

1. Create task `MNB-SQLLoader-Bulk-Account-Aggregation`.
2. Run **Account Aggregation**; record accounts scanned/created.
3. Compare to CSV: expect **4** accounts (`priya.wire`, `marcus.approve`, `jordan.reed`, `samir.hassan`); one DISABLED.
4. Document SLA: aggregation success by **06:00** local before manager certs.

**Expected result:** Counts match CSV; Task Result Success archived.

**If it fails:** Header/delimiter/path; fix and re-run.

### Task 5 — Partial-load failure drill

Count gates are useless if never tested.

1. Copy CSV to `~/iiq-lab-data/connectors/jdbc/sample-rows-partial.csv`; keep only two rows.
2. Point app at partial file; aggregate; record lower count (expect 2).
3. Confirm gate rule would fire: delta vs baseline 4 = 50% > 5%.
4. Restore full file path; re-aggregate; confirm recovery to 4.
5. Ops note: *Never certify from a partial bulk night without count gates.*

**Expected result:** Binder shows before/after counts and restore proof.

**If it fails:** Keep original path noted so restore is one edit.

### Task 6 — Control owner, SLA, examiner prep

1. Control owner IAM: `helen.ross`; feed owner ETL/DBA: `samir.hassan`.
2. SLA: bulk landed by **04:30**; Account Aggregation success by **06:00**; page on count delta **> 5%**.
3. Evidence list: control file stub name, Task Result, count reconcile sheet, partial-load drill notes.
4. CHANGELOG: “Lesson 67 SQLLoader bulk pattern for MNB-SQLLoader-Bulk.”

**Expected result:** Owner/SLA/evidence triple + CHANGELOG.

### Task 7 — Examiner question drill

*“Prove last night’s warehouse entitlement inventory was complete before certifications opened.”*

Answer: control log (rows loaded) + aggregation Task Result (accounts scanned) + reconcile sheet within gate + timestamp before cert launch.

**Expected result:** Written three-artifact answer.

### Task 8 — Residual risk

Record `RR-BULK-STALE-01`: *Mid-day joiner/mover entitlements on bulk-only sources are stale until next load — sensitive systems need Direct/WS/JDBC iterative paths or intraday deltas.*

**Expected result:** RR with owner `helen.ross`.

### Task 9 — Optional jdbc-pg staging path

If Lesson 63’s Postgres is up, demonstrate the “loader lands in a table” half of the pattern without Oracle SQL*Loader.

1. Confirm `jdbc-pg` on port **5433** (`docker compose -f docker-compose.connectors.yml ps`).
2. Note: production bulk would `COPY` or SQL*Loader into staging; lab already has `mnb_app_accounts` seeded.
3. Document: *IIQ may aggregate staging via JDBC (`MNB-CoreBanking-JDBC`) or the file via `MNB-SQLLoader-Bulk` — pick one consumer per feed to avoid double Links.*
4. Do **not** point both apps at the same rows for certifications.

**Expected result:** Staging-vs-file decision sentence in the feed contract.

---

## Acceptance criteria

- [ ] Feed contract (columns, native id, idempotency, deletes) documented
- [ ] `MNB-SQLLoader-Bulk` configured against lab fixture; provisioning off
- [ ] Account Aggregation Task Result with count reconciliation (4 rows)
- [ ] Partial-load drill completed and restored
- [ ] SLA / count-gate / owners / examiner answer / `RR-BULK-STALE-01`

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Count mismatch | Header/duplicates/filter | Diff CSV vs Task Result |
| Stale cubes | Aggregation not scheduled | Schedule; document timezone |
| Deletes not reflected | No tombstone/status | Add DELETED or full-replace semantics |
| Loader OK, IIQ empty | Wrong path/staging | Verify IIQ reads same artifact |
| Accidental provisioning | Features left on | Disable PROVISIONING on inventory app |

---

## Training binder evidence

- Feed contract page
- App config screenshot (path visible)
- Aggregation Task Result + counts
- Partial-load drill notes
- SLA count-gate + examiner answer + RR

**Examiner question:** *“Prove last night’s bulk inventory was complete before certifications opened.”*

---

## Knowledge check

1. Is SQLLoader typically an IIQ connector type or an external bulk pattern?
2. What Meridian app name did you use for the bulk inventory?
3. Why run a partial-load drill?
4. What should happen before morning certifications after a bulk night?
5. Name one idempotency key approach from this lab.
6. Should `PROVISIONING` be enabled on `MNB-SQLLoader-Bulk`?

### Answers

1. External bulk/ETL pattern; IIQ aggregates via JDBC or DelimitedFile.
2. `MNB-SQLLoader-Bulk`.
3. To prove count gates catch incomplete feeds before certs.
4. Successful Account Aggregation with reconciled counts (and refresh as designed).
5. `account_id` upsert with explicit delete/tombstone handling.
6. No — inventory-only.

---

## Further reading

- [Oracle SQL*Loader Concepts](https://docs.oracle.com/en/database/oracle/oracle-database/19/sutil/oracle-sql-loader-concepts.html) — how control files and loads work upstream of IIQ.
- [PostgreSQL COPY](https://www.postgresql.org/docs/current/sql-copy.html) — bulk land pattern if staging is Postgres (jdbc-pg).
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “Account Aggregation” scheduling and Task Results for evidence design.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — large aggregation / delimited performance threads (ties to Lesson 54).
- [NIST SP 800-53 AU-6 / AU-12](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) — audit record review mindset for load + aggregation evidence chains.

---

## Stretch lab

Sketch partitioned aggregation for >100k rows (filters by `entitlement` or hash ranges) using Lesson 54 ideas. Prototype count-gate as a script that compares `wc -l` on the CSV to Task Result accounts scanned. Wire jdbc-pg: `COPY mnb_app_accounts FROM …` then JDBC-aggregate staging instead of DelimitedFile.

---

## Summary

- Bulk patterns land large inventories; IIQ still needs aggregation, reconciliation, and count gates.
- `MNB-SQLLoader-Bulk` demonstrates governed inventory without live SQL*Loader.
- Partial-load drills and SLAs protect certification integrity — and examiner trust.

---

**Previous:** [Lesson 66 — Oracle Database Direct Connector](66-oracle-db-direct-connector.md)  
**Next:** [Lesson 68 — Web Services Connector](68-web-services-connector.md)
