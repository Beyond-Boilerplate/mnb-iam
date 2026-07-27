# Lesson 54 — Aggregation Patterns Advanced

**Level:** Intermediate  
**Track:** Connectors  
**Time:** 90–120 min  
**Prereq:** Lesson 53 — IQService Architecture; prior Account Aggregation experience (Lessons 08–09, 16)  

**Lab data:**
- Repo / homelab: `~/iiq-lab-data/connectors/`
- Existing tasks: `Aggregate MNB-HR`, `Aggregate MNB-IT-Access` (names may vary slightly — use your Lesson 09/16 task names)
- Cross-link: Lesson 16 multi-app runbook failure domains

---

## Learning objectives

You will be able to:

- Distinguish **full**, **delta**, **filtered**, **partitioned**, and **multi-host** aggregation patterns and when each is honest
- Choose a pattern per Meridian application SLA and target size without silently dropping wire initiators
- Configure or document filter strings and partition strategy without a live huge directory
- Tie aggregation schedules and failure domains to Lesson 16’s authoritative-first pipeline
- Use **Account Aggregation Task Results** as continuous control evidence (counters, duration, errors)
- Update the Meridian runbook with Pattern / Filter / Partition / Completeness-proof columns

---

## Why this matters

**Business.** Nightly full aggregates of multi-million-object directories blow SLAs. Delta and partition patterns keep Meridian’s cert and SoD data fresh without melting task servers. Wrong filters are worse than slow jobs: if an OU filter excludes the payments OU, `priya.wire` disappears from inventory and nobody certifies her Wire-adjacent AD groups.

**Control / audit.** Runbooks must state whether each `Aggregate MNB-*` is full or delta, and how completeness is proven after filter changes. Examiners ask: *If you only run delta on AD, how do you prove disabled accounts are still detected?* Task Results — accounts scanned, created, updated, failures — are the evidence, not a verbal assurance.

---

## Concepts

### Full vs delta — two different honesty models

| Pattern | Behavior | When Meridian uses it | Completeness risk |
| --- | --- | --- | --- |
| **Full** | Iterate/search entire configured scope | Small apps; nightly baseline; file feeds; quarterly AD reconcile | Slow on huge directories |
| **Delta** | Changes since watermark / USN / timestamp | Large AD / large DB when connector supports it | Watermark bugs can hide disables/orphans |

**Real-life Meridian example.** Ops enabled AD delta and celebrated 12-minute runtimes. Three months later a quarterly spot-check found disabled accounts that never appeared in IIQ — the watermark had advanced past a DC replication blip. The fix was not “trust delta harder”; it was **nightly delta + quarterly full reconcile**, with an alert when delta volume drops >80% vs baseline.

**File connectors caveat:** DelimitedFile usually means **full file replace** semantics. “Delta” for HR means the HRIS dropped a differential file — not AD-style USN. Do not pretend `MNB-HR` has directory watermarks.

### Filters — precision vs blind spots

Filters narrow LDAP/SQL/connector scope (OU, `status = 'ACTIVE'`, objectClass). They are powerful and dangerous:

| Filter intent | Good use | Failure mode |
| --- | --- | --- |
| Employee OU only | Separate employee vs contractor jobs | Contractor OU forgotten → `raj.external` invisible |
| `status = 'ACTIVE'` | Cert-facing inventory of live DB users | Leavers with DISABLED never show for evidence |
| Security groups only | Reduce entitlement noise | Missed nested/distribution groups that still gate access |

Rule: **every filter needs a completeness story** — what did you exclude, and how do you still see it when Risk asks?

### Partitioning and multi-host (preview)

| Pattern | Behavior | Meridian use |
| --- | --- | --- |
| **Partition** | Split account space across threads/workers | Huge directories when a single iterate misses SLA |
| **Multi-host** | Multiple aggregation hosts / task servers | Scale-out when concurrent AD + JDBC + Entra windows collide (Lesson 105) |

Partition keys must not overlap. Overlapping partitions create duplicate work and confusing counters; gapped partitions create silent holes. Document partition count as a design decision — confirm the connector’s partition UI on your IIQ version before go-live.

### Schedules and Lesson 16 failure domains

Aggregation patterns sit inside the pipeline you already designed:

```text
  [1] Aggregate MNB-HR            ── if FAIL → STOP pipeline (Lesson 16)
  [2] Aggregate MNB-IT-Access
  [3] Aggregate MNB-ActiveDirectory (delta nightly + quarterly full)
  [4] Aggregate platform apps     ── Core, SAP, AWS, Wire, …
  [5] Refresh MNB Identities      ── after aggregates
```

| Stage | Pattern note | On failure |
| --- | --- | --- |
| Authoritative HR | Full file | **Stop** — do not run targets blindly |
| Inventory / platforms | Full or delta per app | Continue peers; ticket (Sev-2) |
| Directory AD | Delta nightly; full quarterly | Continue; Sev-2; watch watermark metrics |
| Refresh | After aggregates | Re-run after fixes; note stale UI |

RPO narrative: HR before start of business; targets after extracts/API windows; AD delta must finish **before** Refresh so cubes see current links.

### Task Results as evidence

An Account Aggregation Task Result is not a vanity metric. Record:

| Counter / field | Why examiners care |
| --- | --- |
| Accounts scanned | Completeness vs prior baseline |
| Accounts created / updated / deleted (or equivalent) | Change volume sanity |
| Failures / warnings | Partial success is still a control event |
| Duration | SLA evidence; capacity planning for partition/multi-host |
| Application name + task name | Traceability in the runbook |

Unexpected **tiny** delta volume is a control risk — investigate before celebrating speed.

**How an auditor reads a Task Result.** They do not stop at green/red. They ask: (1) Was this the *scheduled* job or a manual Now? (2) Do scanned counts sit within ±N% of last week’s full or delta baseline? (3) Are failures attributed (connection, filter, schema) or silently zero? (4) Did Refresh run after this aggregate? Your binder should answer those four without hunting.

### Watermark and failure-domain interplay

Delta is not only a performance knob — it changes your **failure domain**:

| Event | Full-pattern impact | Delta-pattern impact |
| --- | --- | --- |
| IQService / DC outage mid-job | Partial iterate; re-run full when healthy | Watermark may advance incorrectly — **change-control** before reset |
| Bad OU filter deployed | Missing OU until fixed + re-agg | Missing OU *and* false confidence from “fast green” deltas |
| HR feed fail (Lesson 16) | Stop targets | Stop targets — delta on AD does not excuse running without identities |
| Task server capacity cliff | Miss SLA → partition / multi-host | Same; delta buys time but does not remove Lesson 105 scale-out |

Meridian rule: **never reset an AD watermark in production without a ticket, a full reconcile plan, and a recorded before/after scanned count.**

---

## How it works

```text
  Schedule (cron / sequential runbook)
     │
     ├── Aggregate MNB-HR (full file — NO_RANDOM_ACCESS)
     ├── Aggregate MNB-IT-Access (full file)
     ├── Aggregate MNB-ActiveDirectory (delta + OU filter; quarterly full)
     ├── Aggregate MNB-CoreBanking-JDBC (full or timestamp delta)
     │
     ▼
  Task Result (counters, errors, duration) ──► binder / SIEM / ops ticket
     │
     ▼
  Refresh MNB Identities
```

| Application | Typical pattern | Filter intent | Completeness proof |
| --- | --- | --- | --- |
| `MNB-HR` | Full file | N/A (whole extract) | Row count vs HR drop control totals |
| `MNB-IT-Access` | Full file | N/A | Compare to prior Task Result |
| `MNB-ActiveDirectory` | Delta nightly | Employee / contractor OU jobs | Quarterly full + delta volume alert |
| `MNB-CoreBanking-JDBC` | Full or timestamp delta | ACTIVE for certs; include DISABLED for leaver evidence (document which job) | Reconcile to DB count |
| `MNB-OpenLDAP` | Full (lab size) | `(objectClass=inetOrgPerson)` | Lab persona spot-check |

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq`; can open existing aggregation tasks
- [ ] Lesson 16 runbook inventory available (authoritative first, stop/go rules)
- [ ] Know approximate sizes: HR file small; AD large; IT Access medium
- [ ] `features-string-glossary.md` recalled (`NO_RANDOM_ACCESS`, `SEARCH`)
- [ ] Lesson 53 OU / IQService notes available for AD design

---

## Lab procedure

### Task 1 — Classify existing Meridian aggregates

Start from what already runs. Pattern literacy begins with your live Task Results, not a whiteboard fantasy.

1. Open Tasks → find `Aggregate MNB-HR` and `Aggregate MNB-IT-Access` (or your Lesson 09/16 names).
2. Record: application, schedule, last result duration, accounts scanned / created / updated, errors.
3. Classify each as **full file** aggregate (expected for DelimitedFile).
4. Note create-identities behavior already set in earlier lessons.

**Expected result:** Two-row classification table: both full-file style; Task Result counters captured as evidence.

**If it fails:** Recreate task names per Lesson 09 if missing; classification still required from design.

### Task 2 — Design AD aggregation patterns (no live AD)

AD is where full vs delta vs filter decisions pay rent. Use Lesson 53 OU notes.

1. Draft and save `~/iiq-lab-data/connectors/ad/MNB-ad-agg-patterns-54.txt`:

| Job | Pattern | Filter intent |
| --- | --- | --- |
| `Aggregate MNB-AD-Employees` | Delta nightly | Employee OU only |
| `Aggregate MNB-AD-Contractors` | Full weekly (or delta if supported) | Contractor OU — do not drop `raj.external` |
| `Aggregate MNB-AD-Groups` | Full / delta | Security groups scope |
| `Aggregate MNB-AD-FullReconcile` | Full quarterly | Entire in-scope directory |

2. Write completeness control: quarterly full AD reconcile even if delta nightly.
3. Write anomaly metric: alert if nightly delta volume drops >80% vs 30-day baseline.

**Expected result:** Design table + completeness + anomaly metric in the AD patterns file.

### Task 3 — Lab without live target — filter & partition worksheet

Document filters before anyone types them into production.

1. For JDBC Core Banking (`mnb_app_accounts`), draft SQL filter intent:
   - Cert-facing job: `status = 'ACTIVE'`
   - Leaver-evidence job: include `DISABLED` (separate task or wider filter — pick one and document)
2. For OpenLDAP, draft LDAP filter: `(objectClass=inetOrgPerson)` and a separate group filter.
3. For partition: invent partition count **4** for AD users by hash/range — document “confirm connector partition UI on your version.”
4. Explicitly mark: **No live target required** — worksheet only.
5. Save under `~/iiq-lab-data/connectors/MNB-agg-filter-partition-54.txt`.

**Expected result:** Worksheet with JDBC + LDAP filter strings, AD partition note, and ACTIVE vs DISABLED intent explained.

**If it fails:** Use sample rows in `jdbc/sample-rows.csv` to justify ACTIVE vs DISABLED inclusion.

### Task 4 — Schedules and Lesson 16 failure-domain tie-in

Patterns without schedule order recreate the “sometimes true cubes” problem Lesson 16 fixed.

1. Write the Meridian nightly order into your runbook draft:
   1. `Aggregate MNB-HR` (full) — **stop on fail**
   2. Inventory / platform aggregates (continue on single fail + ticket)
   3. `Aggregate MNB-ActiveDirectory` delta (continue on fail + ticket)
   4. `Refresh MNB Identities`
2. Add SLA: AD delta must finish before Refresh; document dependency.
3. Reference Lesson 16 failure domains explicitly in a one-paragraph ops note.

**Expected result:** Schedule + stop/go paragraph linked to Lesson 16.

### Task 5 — Runbook column upgrade

Make pattern choices visible to the next on-call engineer.

1. Add columns to runbook: `Pattern` (full/delta), `Filter`, `Partition`, `Completeness proof`.
2. Fill for `MNB-HR`, `MNB-IT-Access`, and planned `MNB-ActiveDirectory`.
3. Optional: add `MNB-CoreBanking-JDBC` with ACTIVE vs DISABLED job names.

**Expected result:** Runbook rows updated (or draft runbook section in lab-data / binder).

### Task 6 — Safe live practice on file apps + Task Result evidence

Prove you can read Task Results as evidence, not wallpaper.

1. Run `Aggregate MNB-IT-Access` (full) **Now** if environment allows.
2. Open the Task Result: capture accounts scanned, duration, errors — screenshot for binder.
3. Compare counters to the prior result; explain any delta in counts (file change vs failure).
4. Do **not** invent connector USN delta on DelimitedFile unless you have a true differential feed.

**Expected result:** Task Result success (or documented failure with fix); counters understood as full-file semantics; screenshot saved.

**If it fails:** Fix path/delimiter per Lesson 09; design worksheets remain primary evidence for AD/JDBC patterns.

### Task 7 — Multi-host readiness note

Know when to escalate from “one task server” without building a cluster tonight.

1. Document when Meridian needs multiple aggregation hosts: AD > SLA budget, or concurrent JDBC + AD + Entra windows collide.
2. Name future lesson: partitioning / task servers (Lesson 105) — do not configure cluster now.
3. Write: “Single-host OK until measured; miss SLA → escalate to multi-host design.”

**Expected result:** Multi-host readiness paragraph in runbook draft.

### Task 8 — Examiner completeness statement

Close with the sentence examiners want on letterhead.

1. Write: “Delta aggregation requires a documented quarterly full aggregation or reconcile report so disabled/orphaned accounts are not permanently invisible.”
2. Attach the delta anomaly metric from Task 2.
3. List three Task Result fields you would show as proof of last night’s AD (or file) run.

**Expected result:** Completeness statement + metric + Task Result field list in binder.

---

## Acceptance criteria

- [ ] Existing HR/IT aggregates classified with Task Result counters
- [ ] AD pattern design file created (delta + quarterly full + anomaly metric)
- [ ] Lab-without-live-target filter/partition worksheet done
- [ ] Schedule / Lesson 16 failure-domain tie-in written
- [ ] Runbook pattern columns drafted
- [ ] Multi-host readiness note written
- [ ] Completeness statement + Task Result evidence captured

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Delta not available on type | Connector limitation | Use full + filters; document |
| Filter drops personas | Too narrow OU/SQL | Widen scope; include contractor / `priya.wire` OU in tests |
| Partition errors | Misconfigured ranges | Reduce partitions; retest small; fix gaps/overlaps |
| File “delta” confusion | Wrong mental model | Treat file as full replace unless feed is differential |
| Refresh before aggregate | Order bug | Fix schedule dependencies (Lesson 16) |
| Delta volume cliff | Bad watermark / empty change log | Compare to full baseline; reset watermark with change control |
| Multi-host duplicate accounts | Overlapping partitions | Fix partition key ranges; re-agg cleanly |
| Task Result “success” but 0 scanned | Path/filter/connection | Treat as failure; do not trust green alone |

---

## Training binder evidence

- Task Result screenshot for a full file aggregate (counters visible)
- `MNB-ad-agg-patterns-54.txt`
- `MNB-agg-filter-partition-54.txt`
- Runbook snippet with Pattern / Filter / Partition / Completeness columns
- Completeness statement + multi-host readiness note + Lesson 16 tie-in

**Examiner question:** “If you only run delta on AD, how do you prove disabled accounts are still detected?”

---

## Knowledge check

1. Difference between full and delta aggregation?
2. Why partition large directories?
3. Do DelimitedFile apps typically use AD-style USN delta?
4. Give one Meridian filter example for JDBC accounts, and state the completeness tradeoff.
5. What completeness control accompanies nightly delta?
6. Why might an unexpectedly tiny delta volume be a control risk?
7. Where do aggregation patterns sit relative to Lesson 16’s HR-first stop rule?

### Answers

1. Full reads entire configured scope; delta reads changes since a watermark/checkpoint.
2. Split work across threads/hosts to finish inside SLA.
3. No — usually full file (or a separately produced differential file).
4. e.g. `status = 'ACTIVE'` for certs — but DISABLED leavers may vanish unless a separate evidence job includes them.
5. Periodic full aggregate or reconcile proving orphans/disabled are still visible.
6. Watermark/filter bugs can silently skip changes; compare to baseline and investigate drops.
7. After authoritative HR succeeds (stop on HR fail); AD/platform patterns run in the target stages before Refresh.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “Account Aggregation” and “delta aggregation” / “partitioned aggregation” for your version’s task options and connector support matrix.
- [SailPoint Community (Compass)](https://community.sailpoint.com/) — search “delta aggregation USN” and “aggregation task result” for watermark failure war stories.
- [Microsoft: Active Directory USN and replication basics](https://learn.microsoft.com/en-us/windows/win32/ad/update-sequence-numbers) — background on why AD delta depends on directory change tracking.
- [NIST SP 800-53 Rev. 5 — AU / SI families](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — why monitoring Task Result anomalies (unexpected drop in volume) is an audit/system-integrity concern.
- [FFIEC Information Security booklet](https://www.ffiec.gov/) — search current IS booklet for inventory completeness and monitoring expectations in banking exams.

---

## Stretch lab

- Time `Aggregate MNB-IT-Access` and estimate AD runtime if 100× larger; justify delta + quarterly full.
- Draft multi-host notes referencing Lesson 105 partitioning task servers with a sketched partition key.
- Propose separate group vs account aggregation jobs for `MNB-ActiveDirectory` and show how both appear in the Lesson 16 pipeline table.

---

## Summary

- Pattern choice is an SLA and completeness decision — full, delta, filter, partition, and multi-host each have failure modes.
- File apps and directories need different delta mental models; Task Results are the evidence examiners want.
- Schedules still obey Lesson 16: authoritative HR first, stop/go by failure domain, Refresh last; quarterly full reconciles protect delta honesty.

---

**Previous:** [Lesson 53 — IQService Architecture](53-iqservice-architecture.md)  
**Next:** [Lesson 55 — Provisioning Feature Matrix](55-provisioning-feature-matrix.md)
