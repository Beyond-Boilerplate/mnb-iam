# Lesson 63 — JDBC Connector Fundamentals

| Field | Value |
| --- | --- |
| **Level** | Intermediate |
| **Track** | Connectors — Databases |
| **Time** | 75–90 minutes |
| **Prereq** | Lesson 62; Core banking row in selection matrix |
| **Lab data** | `~/iiq-lab-data/connectors/jdbc/mnb_core_accounts.sql`; `jdbc/sample-rows.csv` |

## Learning objectives

You will be able to:

- Read Meridian JDBC SQL fixtures and sample account rows
- Create Application `MNB-CoreBanking-JDBC` with JDBC type
- Map `account_id` / `username` / `employee_id` / `entitlement` / `status`
- Complete lab-without-live-DB using CSV as schema and test data truth
- Define `Aggregate MNB-CoreBanking-JDBC` and correlation to HR

## Why this matters

Core banking and reporting databases hold crown-jewel entitlements (`WIRE_INIT`, `SAP_FI`). JDBC is Meridian’s preferred connector for Core banking DB (matrix). Mis-mapped `employee_id` breaks correlation; aggregating as authoritative invents bank staff from DB orphans.

**Control / audit:** SQL used for account query must be versioned. Examiners ask whether IIQ uses least-privilege DB accounts—not DDL admin.

## Concepts

| Table / column | Role |
| --- | --- |
| `mnb_app_accounts.account_id` | Native account key |
| `username` | Correlate to `userName` |
| `employee_id` | Correlate to `employeeId` (preferred) |
| `status` | ACTIVE/DISABLED → enable semantics |
| `entitlement` | Entitlement attribute |
| `mnb_app_entitlements` | Dictionary of codes / risk |

```text
  mnb_core_accounts.sql  →  optional Postgres/MySQL
  sample-rows.csv        →  offline truth / seed
           |
           v
  MNB-CoreBanking-JDBC
           |
           v
  Aggregate → correlate → cubes (priya.wire, marcus.approve, …)
```

Sample rows include `priya.wire` (WIRE_INIT), `marcus.approve` (WIRE_APPR), `jordan.reed` (SAP_FI), `samir.hassan` (DISABLED/DWRP).

## Before you start

- [ ] Copy JDBC fixtures under `~/iiq-lab-data/connectors/jdbc/`
- [ ] JDBC driver available in IIQ lab image (or document deferral)
- [ ] Optional DB via `docker-compose.connectors.yml`
- [ ] IIQ up

## Lab procedure

### Task 1 — Inspect SQL and CSV

1. Read schema:

```bash
cat ~/iiq-lab-data/connectors/jdbc/mnb_core_accounts.sql
```

2. Inspect seed:

```bash
cat ~/iiq-lab-data/connectors/jdbc/sample-rows.csv
```

3. Count ACTIVE vs DISABLED; note wire dual-control pair.

**Expected result:** Notebook shows 4 sample accounts; one DISABLED (`samir.hassan`).

**If it fails:** Re-copy from `lab-data/connectors/jdbc/`.

### Task 2 — Lab without live target — SQL map worksheet

1. Create `~/iiq-lab-data/connectors/jdbc/MNB-JDBC-maps-63.md` with:

| IIQ schema attr | SQL column |
| --- | --- |
| native identity | `account_id` |
| username | `username` |
| email | `email` |
| employee_id | `employee_id` |
| status | `status` |
| entitlement | `entitlement` |

2. Draft iterate/get SQL intent:

```sql
SELECT account_id, username, email, employee_id, status, entitlement, updated_at
FROM mnb_app_accounts;
```

3. Correlation: `employee_id`↔`employeeId`; create-identities **No**.
4. Expected result when live: 4 accounts; If it fails: driver/URL/SQL.

**Expected result:** Maps file with SQL and correlation; works fully offline.

### Task 3 — Create Application MNB-CoreBanking-JDBC

1. Applications → Add New → **JDBC**.
2. Name: `MNB-CoreBanking-JDBC`. Owner: Core Banking / Technology (lab `spadmin`).
3. JDBC URL / user / password: Docker values or placeholders; secrets in vault only.
4. Paste account SQL from worksheet into connector SQL fields (per UI: iterate/get).
5. Mark entitlement column; set status attribute.
6. Save.

**Expected result:** Application object exists.

**If it fails:** Notes shell documenting URL + SQL still counts; proceed.

### Task 4 — Optional live DB path

1. Apply `mnb_core_accounts.sql` to lab DB; load `sample-rows.csv` (INSERT or import).
2. Test Connection.
3. Create/run Account Aggregation `Aggregate MNB-CoreBanking-JDBC`.
4. Spot-check `priya.wire` / `marcus.approve` entitlements; `samir.hassan` DISABLED.

**Expected result:** Live: accounts=4 (or more). Offline: deferred note with maps complete.

**If it fails:** Fix driver class/URL; keep CSV as acceptance evidence for schema understanding.

### Task 5 — Offline CSV acceptance drill

1. Without DB, treat CSV as expected aggregate output table.
2. Write Expected result: after correlation, wire personas show WIRE_* entitlements on cubes.
3. If it fails (correlation): verify `employee_id` values match HR (`MNB00090`, etc.).

**Expected result:** Drill paragraph in maps file.

### Task 6 — Runbook + CHANGELOG

1. Add aggregate after HR; before Refresh.
2. CHANGELOG: “Lesson 63 JDBC fundamentals for MNB-CoreBanking-JDBC.”

**Expected result:** Runbook + CHANGELOG updated.

## Acceptance criteria

- [ ] SQL + CSV inspected; DISABLED persona noted
- [ ] Lab-without-live-target maps + SQL worksheet saved
- [ ] `MNB-CoreBanking-JDBC` created or notes shell
- [ ] Create-identities disabled documented
- [ ] Aggregate live optional; CSV drill done
- [ ] Runbook + CHANGELOG updated

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Driver not found | Missing JDBC jar | Install driver per IIQ docs |
| 0 rows | Wrong SQL/table | Match `mnb_app_accounts` |
| Orphans | Create-identities | Disable |
| Entitlements missing | Column not marked entitlement | Fix schema; re-agg |
| Password in XML export | Hygiene | Redact; use encrypted config |

## Training binder evidence

- `MNB-JDBC-maps-63.md`
- SQL fixture reference
- Application screenshot or shell notes
- Aggregate result **or** CSV expected-output drill

**Examiner question:** “Show the SQL IdentityIQ uses to list core banking accounts and the DB login’s privilege level.”

## Knowledge check

1. Preferred connector for Core banking DB in the matrix?
2. Which CSV user is DISABLED?
3. Preferred correlation attribute from the JDBC table?
4. Must a live database be running to finish this lesson?
5. Name the entitlement for `priya.wire` in sample rows.

### Answers

1. JDBC (alternate: Microsoft SQL Server - Direct).
2. `samir.hassan`.
3. `employee_id` → `employeeId`.
4. No—maps + CSV drill satisfy lab-without-live-target.
5. `WIRE_INIT`.

## Stretch lab

- Join `mnb_app_entitlements` for risk_tier in a richer SQL iterate statement.
- Time aggregate and propose delta on `updated_at` (Lesson 54).
- Premap stored-proc provisioning for Lesson 64.

## Summary

- `MNB-CoreBanking-JDBC` onboarded from Meridian SQL/CSV fixtures.
- Offline maps keep laptop training valid without Postgres.
- Correlation and non-authoritative flags protect HR truth.

---

**Previous:** [Lesson 62 — Directory Authoritative vs Target](62-directory-authoritative-vs-target.md)  
**Next:** [Lesson 64 — JDBC Provisioning Policies](64-jdbc-provisioning-policies.md)
