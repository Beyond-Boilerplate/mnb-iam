# Lesson 208 — JDBC Core Banking Live

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~65 minutes  
**Prereq:** Lesson 202 (207 recommended — uses `e2e.sandbox` as orphan subject)  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 63–64

> **Why:** A huge share of real bank applications are just tables behind a login screen — JDBC is the honest connector for that. Get the governed attribute wrong on a flat-table app and every downstream cert/SoD review is reviewing the wrong column. Examiners ask how Core Banking entitlements are proven in the system of record (SQL), not only in the IIQ UI.

## What this is

`MNB-CoreBanking` is a **JDBC** connector against `jdbc-pg` (PostgreSQL). Seed usually imports the Application definition — this lesson still **verify-or-create** the app, then prove accounts and entitlements with SQL before and after aggregation.

| Setting | Value |
| --- | --- |
| JDBC URL (from IIQ) | `jdbc:postgresql://jdbc-pg:5432/mnb_apps` |
| Creds | `mnb` / `mnb` |
| Account query | `SELECT account_id, username, email, employee_id, status, entitlement FROM mnb_app_accounts` |

`entitlement` is the managed/entitled column (values like `WIRE_INIT`, `WIRE_APPR`, `SAP_FI`, `DWRP`). A companion `mnb_app_entitlements` lookup table carries `risk_tier`. Seeded at container init from `lab-data/connectors/jdbc/mnb_core_accounts.sql`.

## Know these

```text
psql ground truth (accounts + entitlement catalog)
  → Verify-or-create Application MNB-CoreBanking (JDBC)
  → Test Connection → Account Aggregation
  → Cube proof (priya.wire + WIRE_INIT) + SQL parity
  → Insert orphan row (bad employee_id) → re-agg → Uncorrelated
  → Fix key or manual correlate → SQL + cube agree
```

| Column | Role |
| --- | --- |
| `account_id` | `identityAttribute` (native key) |
| `username` | `displayAttribute` |
| `employee_id` | correlation key → identity `userId` |
| `status` | account-level lifecycle (`ACTIVE` / `DISABLED`) — **not** governed |
| `entitlement` | the governed/managed attribute — what certs and SoD (Lesson 224) actually review |

- **Wrong way:** Treating `status` as the attribute certifications should review.  
- **Wrong way:** Assuming `MNB-CoreBanking` exists after every wipe — **verify**, then create from the JDBC template if missing.  
- **Wrong way:** Declaring aggregation success without a matching `psql` row count / entitlement check.  
- **Wrong way:** Pointing IIQ at `localhost:5435` from inside the container — IIQ uses hostname `jdbc-pg`.

## Intent

- Query the live tables with `psql` before trusting IIQ.
- Verify-or-create `MNB-CoreBanking` with the correct schema and SQL.
- Aggregate and prove correlation + entitlement on a cube **and** in SQL.
- Insert a bad-key orphan, re-aggregate, and resolve it deliberately.
- Explain why `entitlement` (not `status`) is the managed/governed attribute.

## Before you start

- [ ] IIQ up as `spadmin` / `admin`
- [ ] JDBC container running:

```bash
docker ps --format '{{.Names}}' | grep -i jdbc
```

- [ ] Lesson 207’s `e2e.sandbox` joiner exists (orphan repair subject) — or another cube you will use for manual correlate
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/208
```

## Do this

### Task 1 — SQL ground truth: accounts

Ground truth before aggregation. Confirm container name with `docker ps` if yours differs (`mnb-jdbc-sample` is typical).

```bash
docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps -c \
  "select account_id, username, employee_id, status, entitlement from mnb_app_accounts order by username;"
```

Save the output under evidence.

- **Why:** if the table is wrong, IIQ can only amplify it.
- **Expect:** multiple rows; note `priya.wire` (or similar) with `WIRE_INIT`; `samir.hassan` shows `status = DISABLED` if seeded — baseline for “already disabled.”

### Task 2 — SQL ground truth: entitlement catalog

```bash
docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps -c \
  "select entitlement_code, display_name, risk_tier from mnb_app_entitlements order by entitlement_code;"
```

- **Why:** `WIRE_INIT` and `WIRE_APPR` are both `risk_tier = critical` — the same pair Lesson 224’s SoD policy cares about.
- **Expect:** both entitlements listed with `risk_tier` critical (or equivalent).

### Task 3 — Verify-or-create Application `MNB-CoreBanking`

Do not assume seed left the app intact.

1. **Applications → Application Definition** → search `MNB-CoreBanking`

#### 3a — If the app exists — verify these fields

Open the app and confirm:

| Area | Must be |
| --- | --- |
| Type / connector | **JDBC** |
| URL | `jdbc:postgresql://jdbc-pg:5432/mnb_apps` |
| User | `mnb` |
| SQL | `SELECT account_id, username, email, employee_id, status, entitlement FROM mnb_app_accounts` |
| Schema `identityAttribute` | `account_id` |
| Schema `displayAttribute` | `username` |
| Attribute `entitlement` | **entitlement=true**, **managed=true** |
| Correlation | `employee_id` → identity `userId` (or equivalent CorrelationConfig) |

Fix any drift, **Save**, then continue.

#### 3b — If the app is missing — create from JDBC template

1. **Applications → Application Definition → Add New Application** (or Create New)
2. Type / template: **JDBC**
3. **Name:** `MNB-CoreBanking` (exact — later lessons search this name)
4. Set connection:

| Field | Value |
| --- | --- |
| JDBC URL | `jdbc:postgresql://jdbc-pg:5432/mnb_apps` |
| Driver | `org.postgresql.Driver` (if prompted) |
| User | `mnb` |
| Password | `mnb` |
| SQL | `SELECT account_id, username, email, employee_id, status, entitlement FROM mnb_app_accounts` |

5. **Schema** (account):

| Attribute | Notes |
| --- | --- |
| `account_id` | identityAttribute |
| `username` | displayAttribute |
| `email` | string |
| `employee_id` | correlation → `userId` |
| `status` | string — **not** managed entitlement |
| `entitlement` | **entitlement=true**, **managed=true** |

6. **Correlation:** account `employee_id` → Identity Attribute `userId`
7. Owner: `spadmin` · Description: Meridian Core Banking accounts (PostgreSQL)
8. **Save**

Optional durable path: Debug → Import `config/Application/MNB-Application-CoreBanking.xml` (password may need re-entry after import).

- **Why:** wipe/partial seed leaves operators staring at a missing app — verify-or-create is the ops habit.
- **Expect:** Application named exactly `MNB-CoreBanking` with managed `entitlement` and JDBC URL using host `jdbc-pg`.

### Task 4 — Test Connection and aggregate

1. On `MNB-CoreBanking` → **Test Connection**
2. **Setup → Tasks** → create **Account Aggregation** for `MNB-CoreBanking` if none exists (Applications = `MNB-CoreBanking` only)
3. **Save** → **Run Now**
4. Open the Task Result — confirm success / account counts

SQL parity check (row count):

```bash
docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps -c \
  "select count(*) as account_rows from mnb_app_accounts;"
```

- **Why:** one account link per row — operators own the first pull after seed.
- **Expect:** Test Connection succeeds; aggregation Task Result succeeds; IIQ account count is consistent with SQL `count(*)` (allow for previously deleted/orphan handling).

> **Watch out:** Test Connection fails from IIQ while host `psql` works → IIQ must use `jdbc-pg:5432`, not the host-published port.

### Task 5 — Prove correlation on Priya’s cube + SQL

Correlation key: JDBC `employee_id` → identity `userId` (e.g. `MNB00090` for `priya.wire`).

1. **Identities → Identity Warehouse → priya.wire**
2. Confirm `MNB-CoreBanking` link
3. Confirm entitlement `WIRE_INIT` under Application Accounts / Entitlements

SQL proof (same persona):

```bash
docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps -c \
  "select account_id, username, employee_id, status, entitlement from mnb_app_accounts where username='priya.wire';"
```

- **Why:** `status` is account-level lifecycle; `entitlement` is what grants capability and what certs/SoD review — UI and SQL must agree.
- **Expect:** correlated link with `WIRE_INIT` visible in IIQ **and** in the `psql` row.

> **Tip:** When you look at Samir later, `DISABLED` status and governed entitlement are different axes — don’t treat status as the entitlement.

### Task 6 — Insert an orphan on purpose (SQL write)

`MNB-E2E` is intentionally **not** the joiner’s real HCM `id` from Lesson 207 — simulates a system that provisions out-of-band before IIQ catches up.

```bash
docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps -c \
  "insert into mnb_app_accounts (account_id, username, email, employee_id, status, entitlement)
   values ('jdbc-e2e', 'e2e.sandbox', 'e2e.sandbox@meridiannb.com', 'MNB-E2E', 'ACTIVE', 'DWRP')
   on conflict do nothing;"
```

If `on conflict` fails (no constraint), run the insert without it; ignore “duplicate key” if you already inserted this lesson.

Verify the row:

```bash
docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps -c \
  "select account_id, username, employee_id, entitlement from mnb_app_accounts where account_id='jdbc-e2e';"
```

- **Why:** you need a controlled orphan before Lesson 214 formalizes the fix pattern.
- **Expect:** SQL shows `employee_id = MNB-E2E`, entitlement `DWRP`.

### Task 7 — Re-aggregate and find the uncorrelated account

1. Re-run **Account Aggregation** for `MNB-CoreBanking`
2. Check **Identities → Uncorrelated Accounts** (or equivalent)

- **Why:** the row lands as an account link, but `employee_id` (`MNB-E2E`) doesn’t match any real `userId`.
- **Expect:** new row aggregates as an **uncorrelated** account.

Screenshot under evidence.

### Task 8 — Fix the orphan deliberately + SQL proof

This is the exercise — not a shortcut to skip.

Pick one:

**Option A — fix the source key (preferred ops path)**

```bash
# Replace MNB##### with e2e.sandbox's real cube userId from Identity Warehouse
docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps -c \
  "update mnb_app_accounts set employee_id='MNB#####' where account_id='jdbc-e2e';"
```

Re-run Account Aggregation (and a correlation-enabled Identity Refresh if the link stays stuck).

**Option B — manual correlate** from IIQ’s uncorrelated-accounts view onto `e2e.sandbox`.

Then prove SQL + cube:

```bash
docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps -c \
  "select account_id, username, employee_id, entitlement from mnb_app_accounts where account_id='jdbc-e2e';"
```

Open `e2e.sandbox` → Application Accounts → `MNB-CoreBanking` with `DWRP`.

- **Why:** ops triage is either fix the source key or attach the link by hand — both end in SQL/UI agreement.
- **Expect:** the link ends up on `e2e.sandbox`’s cube; SQL `employee_id` matches that cube’s `userId` if you used Option A.

### Task 9 — Close with asserts

```bash
./tools/lab/enterprise/verify-lesson.sh 208
```

- **Why:** hard checks catch a dead JDBC target or missing app.
- **Expect:** hard asserts PASS.

## If it fails

| Symptom | Fix |
| --- | --- |
| `docker exec` container name wrong | `docker ps --format '{{.Names}}'` and use whatever the `jdbc-pg` service resolved to |
| `psql: FATAL: password authentication failed` | Credentials are `mnb` / `mnb` against database `mnb_apps` |
| App missing after wipe | Task 3b — create JDBC app or Debug-import `MNB-Application-CoreBanking.xml` |
| Test Connection fails from IIQ but `psql` works from your host | IIQ connects via internal hostname `jdbc-pg:5432`, not the host-published port |
| Aggregation succeeds but no entitlements on cube | Confirm schema `entitlement` is managed+entitlement; re-agg; check SQL value isn’t null |
| Insert succeeds but aggregation shows the old row count | Re-run aggregation; IIQ doesn’t poll the database automatically |
| Orphan never resolves after fixing `employee_id` | Re-run aggregation *and* a correlation-enabled refresh; fixing the source row alone doesn’t retroactively fix an already-created uncorrelated link |

## You are done when

- [ ] `psql` account + entitlement catalog queries saved under evidence
- [ ] `MNB-CoreBanking` verified or created with managed `entitlement`
- [ ] Aggregation succeeds; `priya.wire` shows correlated `WIRE_INIT` in IIQ **and** SQL
- [ ] You’ve personally created and then resolved one uncorrelated account by hand
- [ ] `./tools/lab/enterprise/verify-lesson.sh 208` hard asserts PASS

## Control note

- **Control:** Entitlement governance on in-house / vendor database applications
- **Owner:** Core Banking app owner + IAM Ops
- **SLA (lab):** orphan correlation resolved same session; production target is same-day
- **Evidence:** `~/iiq-lab-evidence/sandbox/208/` — `psql` before/after, app verify notes, uncorrelated-account screenshot

## Quick check

1. Which column is governed for certs/SoD — `status` or `entitlement`? → `entitlement`  
2. What correlation key maps to identity `userId` on this app? → `employee_id`  
3. Why does the deliberately-bad `employee_id` insert create an orphan? → it doesn’t match any real `userId`, so aggregation can’t attach the link  
4. What JDBC hostname must IIQ use? → `jdbc-pg` (not host `localhost`)

## Feedback

Could you recreate `MNB-CoreBanking` from the JDBC template (or re-verify every field) and resolve another orphan without looking at the SQL in this file? If correlation stuck, note whether you re-aggregated **and** refreshed after fixing `employee_id`, and paste the `psql` row for `jdbc-e2e`.

## Navigate

- Previous: [Lesson 207](207-hcm-workday-shaped.md)
- Next: [Lesson 209](209-wire-webservices.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md) · Theory: [256 Connector Registry](256-connector-registry-theory.md)
