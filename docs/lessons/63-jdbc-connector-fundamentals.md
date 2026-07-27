# Lesson 63 — JDBC Connector Fundamentals

**Level:** Intermediate  
**Track:** Connectors — Databases  
**Time:** 90–120 min  
**Prereq:** Lesson 62 — Directory Authoritative vs Target; Core banking row in selection matrix  

**Lab data:**
- Repo: `lab-data/connectors/jdbc/mnb_core_accounts.sql`
- Repo: `lab-data/connectors/jdbc/sample-rows.csv`
- Repo: `docker-compose.connectors.yml` — **live Postgres (`jdbc-pg`) on host port 5433; required for this lesson**
- Runtime: `~/iiq-lab-data/connectors/jdbc/`

---

## Learning objectives

You will be able to:

- Read Meridian’s JDBC SQL fixture and predict aggregation results from `sample-rows.csv` before connecting
- Start the live **jdbc-pg** Postgres container, verify with `psql`, and load seed rows
- Create and configure **MNB-CoreBanking-JDBC** with real JDBC URL, least-privilege lab credentials, and account SQL
- Run a real **Test Connection** and **Account Aggregation**, reconciling four accounts including `samir.hassan` DISABLED
- Correlate on `employee_id` with create-identities off so core banking never invents staff
- Diagnose driver, URL, SQL, and entitlement-mapping failures

---

## Why this matters

**Business.** Core banking and satellite app databases hold crown-jewel entitlements — `WIRE_INIT`, `WIRE_APPR`, `SAP_FI`. When `priya.wire` and `marcus.approve` hold dual-control roles in a database table rather than AD, the only honest inventory is a JDBC aggregation against that table. Teams that wait for a quarterly CSV from the DBA certify stale wire access.

**Control / audit.** Examiners ask: *“Show the SQL IdentityIQ uses to list core banking accounts and the DB login’s privilege level.”* Versioned iterate SQL plus a non-DDL service account is the answer. Aggregating as authoritative invents bank staff from DB orphans; using `sa` / superuser for IIQ is an automatic finding.

---

## Concepts

### Why JDBC for Core Banking

The connector selection matrix prefers **JDBC** for Core banking DB (alternate: Microsoft SQL Server - Direct). Meridian’s lab models application accounts in ordinary tables — not engine logins — so portable SQL is the right tool. Lessons 65–66 cover native Direct connectors when you govern **SQL Server / Oracle engine users and roles** instead.

| Table / column | Role |
| --- | --- |
| `mnb_app_accounts.account_id` | Native account key |
| `username` | Login-style name; secondary correlation |
| `employee_id` | Preferred correlation to identity `employeeId` |
| `status` | `ACTIVE` / `DISABLED` → enable semantics |
| `entitlement` | Entitlement attribute (certifiable) |
| `mnb_app_entitlements` | Dictionary of codes / risk tiers |
| `updated_at` | Delta / freshness candidate (Lesson 54) |

### Seed truth (memorize before you aggregate)

| account_id | username | employee_id | status | entitlement |
| --- | --- | --- | --- | --- |
| jdbc-001 | `priya.wire` | MNB00090 | ACTIVE | WIRE_INIT |
| jdbc-002 | `marcus.approve` | MNB00091 | ACTIVE | WIRE_APPR |
| jdbc-003 | `jordan.reed` | MNB00092 | ACTIVE | SAP_FI |
| jdbc-004 | `samir.hassan` | MNB00094 | DISABLED | DWRP |

Prediction before Task Connection: **4 accounts scanned; 1 DISABLED; wire dual-control pair present; zero identities created.**

### Authoritative flag (Lesson 62 carry-forward)

`MNB-CoreBanking-JDBC` is a **target**. Create-identities **OFF**. HR remains workforce truth. DB orphans become uncorrelated accounts, not cubes.

```
  docker jdbc-pg :5433  (db mnb_apps, user mnb)
        │  schema from mnb_core_accounts.sql
        │  rows from sample-rows.csv
        ▼
  MNB-CoreBanking-JDBC  (JDBC URL + iterate SQL)
        │
        ▼
  Account Aggregation → correlate employee_id → HR cubes
```

---

## How it works

The JDBC connector opens a JDBC connection from the IIQ server, runs configured SQL (iterate / get), and maps columns to account schema attributes. No IQService. Provisioning (Lesson 64) is separate SQL or stored procedures — this lesson is inventory first.

```
IdentityIQ (MNB-CoreBanking-JDBC)
        │  jdbc:postgresql://localhost:5433/mnb_apps
        │  user mnb / password mnb  (lab only)
        ▼
PostgreSQL 16 (jdbc-pg container)
        ├── SELECT … FROM mnb_app_accounts  → account aggregation
        └── entitlement column → ManagedAttribute / entitlement attr
```

| Operation | JDBC behavior | IIQ behavior |
| --- | --- | --- |
| Test Connection | Driver connect + simple validation | Proves URL, creds, network |
| Account aggregation | Iterate SQL result set | One Link per `account_id` |
| Get Object | Get SQL by native identity | Single-account refresh |
| Entitlements | Column marked entitlement | Certifiable wire/SAP codes |
| Provisioning | Not yet | Lesson 64 |

---

## Real-world setup (outside IIQ)

Per the style contract, **the live Postgres path is mandatory** — `docker-compose.connectors.yml` ships `jdbc-pg`.

### Step 1 — Start Postgres

From the repo root:

```bash
docker compose -f docker-compose.connectors.yml up -d jdbc-pg
docker compose -f docker-compose.connectors.yml ps
```

Image `postgres:16-alpine` creates database `mnb_apps` with user/password `mnb`/`mnb` and applies `lab-data/connectors/jdbc/mnb_core_accounts.sql` on first init (tables `mnb_app_accounts`, `mnb_app_entitlements`). Host port **5433** maps to container 5432 (avoids clashing with a local Postgres on 5432).

### Step 2 — Verify with psql before IIQ

```bash
psql "postgresql://mnb:mnb@localhost:5433/mnb_apps" -c '\dt'
psql "postgresql://mnb:mnb@localhost:5433/mnb_apps" -c 'SELECT COUNT(*) FROM mnb_app_accounts;'
```

Expect tables present. Count may be **0** until you load seed data — schema init does not insert the CSV rows.

### Step 3 — Load seed rows

```bash
psql "postgresql://mnb:mnb@localhost:5433/mnb_apps" <<'SQL'
INSERT INTO mnb_app_accounts (account_id, username, email, employee_id, status, entitlement) VALUES
 ('jdbc-001','priya.wire','priya.wire@meridiannb.com','MNB00090','ACTIVE','WIRE_INIT'),
 ('jdbc-002','marcus.approve','marcus.approve@meridiannb.com','MNB00091','ACTIVE','WIRE_APPR'),
 ('jdbc-003','jordan.reed','jordan.reed@meridiannb.com','MNB00092','ACTIVE','SAP_FI'),
 ('jdbc-004','samir.hassan','samir.hassan@meridiannb.com','MNB00094','DISABLED','DWRP')
ON CONFLICT (account_id) DO UPDATE SET
  username=EXCLUDED.username, email=EXCLUDED.email, employee_id=EXCLUDED.employee_id,
  status=EXCLUDED.status, entitlement=EXCLUDED.entitlement, updated_at=CURRENT_TIMESTAMP;

INSERT INTO mnb_app_entitlements (entitlement_code, display_name, risk_tier) VALUES
 ('WIRE_INIT','Wire Initiate','critical'),
 ('WIRE_APPR','Wire Approve','critical'),
 ('SAP_FI','SAP Finance','high'),
 ('DWRP','Dormant / wrap-up','low')
ON CONFLICT (entitlement_code) DO NOTHING;

SELECT account_id, username, status, entitlement FROM mnb_app_accounts ORDER BY account_id;
SQL
```

### Step 4 — Production deltas (document in binder)

- Dedicated least-privilege DB user (`iiq_corebank_ro` for aggregate; separate prov user in Lesson 64) — **not** table owner / superuser.
- JDBC URL via secrets manager; TLS (`sslmode=require`) to Postgres.
- Iterate SQL versioned in git / CRQ; examiners will ask for the exact statement.
- Lab credentials `mnb`/`mnb` are disposable — label **lab-only**.

### Step 5 — JDBC driver on IIQ

Ensure the PostgreSQL JDBC driver jar is available to your IIQ lab image (or document install per SailPoint docs). Without the driver, Test Connection fails before SQL runs.

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq` as `spadmin`; `MNB-HR` cubes exist for correlation
- [ ] Docker running; copy JDBC fixtures to `~/iiq-lab-data/connectors/jdbc/`
- [ ] `psql` client available (Homebrew `libpq`, Postgres.app, or `docker exec` into `jdbc-pg`)
- [ ] Lesson 52 matrix: Core banking DB → **JDBC**
- [ ] Fallback only if Docker is impossible — see Task 9; binder must say live path unavailable

---

## Lab procedure

### Task 1 — Inspect SQL and CSV; write the prediction

Auditable aggregation starts with a written prediction.

1. Read schema and seed:

```bash
cat ~/iiq-lab-data/connectors/jdbc/mnb_core_accounts.sql
cat ~/iiq-lab-data/connectors/jdbc/sample-rows.csv
```

2. Count ACTIVE vs DISABLED; note wire dual-control pair (`priya.wire` / `marcus.approve`).
3. Create `~/iiq-lab-data/connectors/jdbc/MNB-JDBC-maps-63.md` with prediction: **4 accounts, 1 DISABLED (`samir.hassan`), entitlements WIRE_INIT / WIRE_APPR / SAP_FI / DWRP.**

**Expected result:** Prediction card in maps file before any IIQ click.

**If it fails:** Re-copy from `lab-data/connectors/jdbc/`.

### Task 2 — Start live Postgres and load data

1. `docker compose -f docker-compose.connectors.yml up -d jdbc-pg`
2. Run Step 2–3 `psql` verification and INSERT block.
3. Confirm `SELECT COUNT(*) FROM mnb_app_accounts;` returns **4**.

**Expected result:** Live DB with four rows matching the CSV.

**If it fails:** `connection refused` → container not up or wrong port (5433); auth fail → user/password `mnb`/`mnb`; empty tables after INSERT → connected to wrong database.

### Task 3 — SQL map worksheet

1. Add to the maps file:

| IIQ schema attr | SQL column |
| --- | --- |
| native identity | `account_id` |
| username | `username` |
| email | `email` |
| employee_id | `employee_id` |
| status | `status` |
| entitlement | `entitlement` |

2. Draft iterate SQL:

```sql
SELECT account_id, username, email, employee_id, status, entitlement, updated_at
FROM mnb_app_accounts;
```

3. Correlation: `employee_id` ↔ `employeeId`; create-identities **No**.

**Expected result:** Maps file with SQL and correlation decision.

### Task 4 — Create Application MNB-CoreBanking-JDBC

1. Applications → Add New → **JDBC** (or equivalent menu path).
2. Name: `MNB-CoreBanking-JDBC`. Owner: Core Banking / Technology (lab `spadmin`); IAM contact `helen.ross`.
3. Connection:
   - **URL:** `jdbc:postgresql://localhost:5433/mnb_apps`  
     (if IIQ is in Docker: `host.docker.internal` or compose network hostname — classic trap)
   - **User / password:** `mnb` / `mnb` — annotate *lab-only; production uses vaulted `iiq_corebank_ro`*
   - **Driver class:** PostgreSQL driver per your build
4. Paste iterate / get SQL from the worksheet; mark `entitlement` as entitlement attribute; map `status` for enable semantics.
5. Non-authoritative; create-identities **OFF**. Save.

**Expected result:** Application saved with live connection values, not placeholders.

### Task 5 — Test Connection

1. Click **Test Connection** on `MNB-CoreBanking-JDBC`.
2. If it fails, reproduce with `psql` to split driver/IIQ issues from database issues.

**Expected result:** Success. Failure with working `psql` means URL/driver/user fields differ from the working connection string — compare character by character.

**If it fails:** Driver not found → install PostgreSQL JDBC jar; `Connection refused` → port/host; auth → credentials.

### Task 6 — Account Aggregation with predicted counts

1. Tasks → New → Account Aggregation: `Aggregate MNB-CoreBanking-JDBC` (alias `MNB-CoreBanking-JDBC-Account-Aggregation`).
2. Run. Record accounts scanned/created/updated.
3. Reconcile to prediction: **4 accounts**. Open cubes:
   - `priya.wire` — WIRE_INIT
   - `marcus.approve` — WIRE_APPR
   - `jordan.reed` — SAP_FI
   - `samir.hassan` — DISABLED + DWRP
4. Confirm zero identities created; all correlated via `employee_id`.
5. Schedule note: nightly after `MNB-HR` aggregation.

**Expected result:** Task Result success with exactly 4 accounts; Samir shows disabled semantics; wire pair visible.

**If it fails:** 0 rows → SQL/table/schema; entitlements missing → column not marked entitlement; uncorrelated → employee_id/HR mismatch.

### Task 7 — Examiner SQL evidence card

1. Paste the exact iterate SQL into the maps file under “Examiner evidence.”
2. Privilege statement: *Lab used table-owner `mnb`; production design is read-only `iiq_corebank_ro` with SELECT only on `mnb_app_accounts` / dictionary tables.*
3. Note `mnb_app_entitlements` exists for risk-tier joins in stretch / Lesson 64+.

**Expected result:** SQL + privilege paragraph ready for exam Q&A.

### Task 8 — Runbook + CHANGELOG

1. Runbook: aggregate after HR; before Identity Refresh where correlation depends on refresh.
2. CHANGELOG: “Lesson 63 JDBC fundamentals for MNB-CoreBanking-JDBC against live jdbc-pg.”

**Expected result:** Runbook + CHANGELOG updated.

### Task 9 — Fallback (only if Docker cannot run)

Secondary path — binder must say live path was **unavailable**, not skipped.

1. Complete Tasks 1, 3, 4 (placeholder URL), 7, 8 using CSV as expected-output truth.
2. Mark Test Connection and Task 6 deferred with dated note.
3. Do **not** claim live aggregation evidence.

**Expected result:** Design artifacts complete; deferred-live note dated.

---

## Acceptance criteria

- [ ] Prediction card written before aggregation (4 accounts / 1 DISABLED / wire pair)
- [ ] `jdbc-pg` up; `psql` shows 4 seeded rows (or dated deferral if Docker impossible)
- [ ] `MNB-CoreBanking-JDBC` created with live URL; create-identities off
- [ ] Test Connection passed (live path)
- [ ] Aggregation Task Result matches prediction; Priya/Marcus/Jordan/Samir spot-checks done
- [ ] Examiner SQL + least-privilege note recorded; CHANGELOG updated

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Driver not found | Missing PostgreSQL JDBC jar | Install driver per IIQ docs; restart app server if required |
| Connection refused | Container down or wrong port | `docker compose … ps`; use host port **5433** |
| 0 rows, task green | Wrong SQL/table or empty DB | Re-run seed INSERT; match `mnb_app_accounts` |
| Orphan cubes | Create-identities on | Disable; Lesson 62 remediation |
| Entitlements missing | Column not marked entitlement | Fix schema; re-aggregate |
| Password in XML export | Hygiene | Redact; use encrypted config / vault |
| IIQ in Docker cannot reach DB | `localhost` is the container itself | Use `host.docker.internal` or compose service name `jdbc-pg` |

---

## Training binder evidence

- `MNB-JDBC-maps-63.md` (prediction, schema map, SQL, privilege note)
- `psql` output showing 4 rows
- Application screenshot (URL visible, password masked) + Test Connection success
- Aggregation Task Result reconciled to prediction; cube spot-checks

**Examiner question:** *“Show the SQL IdentityIQ uses to list core banking accounts and the DB login’s privilege level.”*

---

## Knowledge check

1. Preferred connector for Core banking DB in the matrix?
2. Which CSV/DB user is DISABLED?
3. Preferred correlation attribute from the JDBC table?
4. What host port does `jdbc-pg` expose, and which database/user?
5. Name the entitlement for `priya.wire` in sample rows.
6. Must create-identities be enabled on `MNB-CoreBanking-JDBC`?

### Answers

1. JDBC (alternate: Microsoft SQL Server - Direct).
2. `samir.hassan`.
3. `employee_id` → `employeeId`.
4. Port **5433**; database `mnb_apps`; user `mnb` (lab).
5. `WIRE_INIT`.
6. No — it is a non-authoritative target.

---

## Further reading

- [PostgreSQL JDBC Driver documentation](https://jdbc.postgresql.org/documentation/use/) — URL parameters (`sslmode`, ports) you will use beyond the lab.
- [PostgreSQL — CREATE ROLE / least privilege](https://www.postgresql.org/docs/current/user-manag.html) — model production `iiq_corebank_ro` properly.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “JDBC connector” for iterate/get SQL fields and driver installation.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — JDBC aggregation and driver-class troubleshooting threads.
- [OWASP — Query Parameterization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Query_Parameterization_Cheat_Sheet.html) — mindset for Lesson 64 bind parameters (never string-concat passwords or IDs).

---

## Stretch lab

Join `mnb_app_entitlements` in iterate SQL to surface `risk_tier`. Time aggregation and propose a delta on `updated_at` (Lesson 54). Premap stored-proc provisioning names for Lesson 64. Recreate the container after editing SQL (`down` then `up -d`) and re-seed — init scripts run only on first volume create.

---

## Summary

- `MNB-CoreBanking-JDBC` is onboarded against **live** Postgres (`jdbc-pg` :5433) with predicted counts from Meridian fixtures.
- Test Connection + aggregation Task Results, not CSV wishful thinking, are the examiner evidence for core banking inventory.
- Correlation on `employee_id` and create-identities off protect HR truth while wire dual-control entitlements become certifiable.

---

**Previous:** [Lesson 62 — Directory Authoritative vs Target](62-directory-authoritative-vs-target.md)  
**Next:** [Lesson 64 — JDBC Provisioning Policies](64-jdbc-provisioning-policies.md)
