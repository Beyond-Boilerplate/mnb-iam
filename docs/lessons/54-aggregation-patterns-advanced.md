# Lesson 54 — Aggregation Patterns Advanced

| Field | Value |
| --- | --- |
| **Level** | Intermediate |
| **Track** | Connectors |
| **Time** | 60–90 minutes |
| **Prereq** | Lesson 53; prior Account Aggregation experience (Lessons 08–09) |
| **Lab data** | `~/iiq-lab-data/connectors/`; existing `Aggregate MNB-HR` / `Aggregate MNB-IT-Access` tasks |

## Learning objectives

You will be able to:

- Distinguish full, delta, filtered, partitioned, and multi-host aggregation patterns
- Choose a pattern per Meridian application SLA and target size
- Configure or document filter strings and partition strategy without a live huge directory
- Update the Meridian runbook with aggregation pattern columns
- Predict examiner questions about completeness vs performance

## Why this matters

Nightly full aggregates of multi-million-object directories blow SLAs. Delta and partition patterns keep Meridian’s Cert and SoD data fresh without melting the task servers. Wrong filters silently drop wire initiators—worse than slow jobs.

**Control / audit:** Runbooks must state whether each `Aggregate MNB-*` is full or delta, and how completeness is proven after filter changes.

## Concepts

| Pattern | Behavior | Meridian use |
| --- | --- | --- |
| Full | Iterate/search entire configured scope | Small apps; nightly baseline |
| Delta | Changes since watermark / USN / timestamp | Large AD / DB |
| Filter | LDAP/SQL/connector filter narrows scope | OU or status = ACTIVE |
| Partition | Split account space across threads/hosts | Huge directories |
| Multi-host | Multiple aggregation hosts / task servers | Scale-out (Lesson 105) |

```text
  Schedule
     |
     +-- Aggregate MNB-HR (full file — NO_RANDOM_ACCESS)
     +-- Aggregate MNB-ActiveDirectory (delta + OU filter)
     +-- Aggregate MNB-CoreBanking-JDBC (full or timestamp delta)
     |
     v
  Refresh MNB Identities
```

**File connectors:** Usually full file replace semantics; “delta” may mean differential file drops, not connector USN.

## Before you start

- [ ] IIQ up; can open existing aggregation tasks
- [ ] Runbook inventory from Lesson 08 available
- [ ] Know approximate sizes: HR file small; AD large; IT Access medium
- [ ] `features-string-glossary.md` recalled (`NO_RANDOM_ACCESS`, `SEARCH`)

## Lab procedure

### Task 1 — Classify existing Meridian aggregates

1. Open Tasks → find `Aggregate MNB-HR` and `Aggregate MNB-IT-Access`.
2. Record: application, schedule, last result duration/counters.
3. Classify each as full file aggregate (expected).
4. Note create-identities behavior already set in earlier lessons.

**Expected result:** Two-row classification table: both full-file style.

**If it fails:** Recreate task names per Lesson 09 if missing; classification still required.

### Task 2 — Design AD aggregation patterns (no live AD)

1. Using Lesson 53 OU notes, draft:

| Job | Pattern | Filter intent |
| --- | --- | --- |
| `Aggregate MNB-AD-Employees` | Delta nightly | Employee OU only |
| `Aggregate MNB-AD-Contractors` | Full weekly | Contractor OU |
| `Aggregate MNB-AD-Groups` | Full / delta | Security groups scope |

2. Write completeness control: quarterly full AD reconcile even if delta nightly.

**Expected result:** Design table saved `~/iiq-lab-data/connectors/ad/MNB-ad-agg-patterns-54.txt`.

### Task 3 — Lab without live target — filter & partition worksheet

1. For JDBC Core Banking (`mnb_app_accounts`), draft SQL filter intent: `status = 'ACTIVE'` for certification-facing aggregate vs full including DISABLED for leaver evidence.
2. For OpenLDAP, draft LDAP filter: `(objectClass=inetOrgPerson)` and group filter separately.
3. For partition: invent partition count 4 for AD users by hash/range—document “confirm connector partition UI on your version.”
4. Explicitly mark: **No live target required**—worksheet only.

**Expected result:** Worksheet with JDBC + LDAP filter strings and AD partition note.

**If it fails:** Use sample rows in `jdbc/sample-rows.csv` to justify ACTIVE vs DISABLED inclusion.

### Task 4 — Runbook column upgrade

1. Add columns to runbook: `Pattern` (full/delta), `Filter`, `Partition`, `Completeness proof`.
2. Fill for `MNB-HR`, `MNB-IT-Access`, and planned `MNB-ActiveDirectory`.
3. SLA: AD delta must finish before Refresh; document order.

**Expected result:** Runbook rows updated (or draft runbook section in lab-data).

### Task 5 — Safe live practice on file apps

1. Run `Aggregate MNB-IT-Access` (full) Now if environment allows.
2. Compare account/entitlement counters to prior result.
3. Do **not** invent delta on DelimitedFile unless you have a true differential feed.

**Expected result:** Task result success; counters understood as full-file semantics.

**If it fails:** Fix path/delimiter per Lesson 09; still accept design worksheets as primary evidence.

### Task 6 — Multi-host readiness note

1. Document when Meridian needs multiple aggregation hosts: AD > SLA budget, or concurrent JDBC + AD + Entra windows collide.
2. Name future lesson: partitioning / task servers (Lesson 105)—do not configure cluster now.
3. Expected result: one paragraph “single-host OK until measured”; If it fails (missed SLA): escalate to multi-host design.

**Expected result:** Multi-host readiness note in runbook draft.

### Task 7 — Examiner completeness statement

1. Write: “Delta aggregation requires a documented quarterly full aggregation or reconcile report so disabled/orphaned accounts are not permanently invisible.”
2. Add metric: track `accounts scanned` vs prior full baseline; alert if delta volume drops >80% unexpectedly (possible watermark bug).

**Expected result:** Statement + metric idea in binder.

## Acceptance criteria

- [ ] Existing HR/IT aggregates classified
- [ ] AD pattern design file created
- [ ] Lab-without-live-target filter/partition worksheet done
- [ ] Runbook pattern columns drafted
- [ ] Multi-host readiness note written
- [ ] Completeness statement + delta anomaly metric idea written

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Delta not available on type | Connector limitation | Use full + filters; document |
| Filter drops personas | Too narrow OU/SQL | Widen scope; include `priya.wire` OU in tests |
| Partition errors | Misconfigured ranges | Reduce partitions; retest small |
| File “delta” confusion | Wrong mental model | Treat file as full replace unless feed is differential |
| Refresh before aggregate | Order bug | Fix schedule dependencies |
| Delta volume cliff | Bad watermark / empty change log | Compare to full baseline; reset watermark with change control |
| Multi-host duplicate accounts | Overlapping partitions | Fix partition key ranges; re-agg cleanly |

## Training binder evidence

- Task result screenshot for a full file aggregate
- `MNB-ad-agg-patterns-54.txt`
- Runbook snippet with Pattern column
- Completeness statement + multi-host readiness note
- Filter/partition worksheet (lab-without-live-target)

**Examiner question:** “If you only run delta on AD, how do you prove disabled accounts are still detected?”

## Knowledge check

1. Difference between full and delta aggregation?
2. Why partition large directories?
3. Do DelimitedFile apps typically use AD-style USN delta?
4. Give one Meridian filter example for JDBC accounts.
5. What completeness control accompanies nightly delta?
6. Why might an unexpectedly tiny delta volume be a control risk?

### Answers

1. Full reads entire configured scope; delta reads changes since a watermark/checkpoint.
2. Split work across threads/hosts to finish inside SLA.
3. No—usually full file (or a separately produced differential file).
4. e.g. only `status = 'ACTIVE'`, or include DISABLED for leaver evidence—document intent.
5. Periodic full aggregate or reconcile proving orphans/disabled are still visible.
6. Watermark/filter bugs can silently skip changes; compare to baseline and investigate drops.

## Stretch lab

- Time `Aggregate MNB-IT-Access` and estimate AD runtime if 100× larger; justify delta.
- Draft multi-host notes referencing Lesson 105 partitioning task servers.
- Propose separate group vs account aggregation jobs for `MNB-ActiveDirectory`.

## Summary

- Pattern choice is an SLA and completeness decision, not a checkbox.
- File apps and directories need different delta mental models.
- Filters and partitions are documented before go-live—even without live AD.
- Delta anomaly metrics and quarterly full reconciles protect examiner completeness questions.

---

**Previous:** [Lesson 53 — IQService Architecture](53-iqservice-architecture.md)  
**Next:** [Lesson 55 — Provisioning Feature Matrix](55-provisioning-feature-matrix.md)
