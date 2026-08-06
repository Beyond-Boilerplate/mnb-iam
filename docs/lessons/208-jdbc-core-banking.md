# Lesson 208 — JDBC Core Banking Live

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~55 minutes  
**Prereq:** Lesson 202 (207 recommended — uses `e2e.sandbox` as orphan subject)  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 63–64

> **Why:** A huge share of real bank applications are just tables behind a login screen — JDBC is the honest connector for that. Get the governed attribute wrong on a flat-table app and every downstream cert/SoD review is reviewing the wrong column.

## What this is

`MNB-CoreBanking` is a real **JDBC** connector against `jdbc-pg` (PostgreSQL):

| Setting | Value |
| --- | --- |
| JDBC URL (from IIQ) | `jdbc:postgresql://jdbc-pg:5432/mnb_apps` |
| Creds | `mnb` / `mnb` |
| Account query | `SELECT account_id, username, email, employee_id, status, entitlement FROM mnb_app_accounts` |

`entitlement` is the managed/entitled column (values like `WIRE_INIT`, `WIRE_APPR`, `SAP_FI`, `DWRP`). A companion `mnb_app_entitlements` lookup table carries `risk_tier`. Seeded at container init from `lab-data/connectors/jdbc/mnb_core_accounts.sql`.

This is the connector you reach for whenever a vendor or in-house system doesn’t have a real API — which, in banking, is often.

## Know these

| Column | Role |
| --- | --- |
| `account_id` | `identityAttribute` (native key) |
| `username` | `displayAttribute` |
| `employee_id` | correlation key → identity `userId` |
| `status` | account-level lifecycle (`ACTIVE` / `DISABLED`) — **not** governed |
| `entitlement` | the governed/managed attribute — what certs and SoD (Lesson 224) actually review |

**Wrong way:** Treating `status` as the attribute certifications should review — `status` is enable/disable plumbing; `entitlement` is what grants real capability inside Core Banking.

## Intent

- Query the live table with `psql` before touching IIQ.
- Aggregate `MNB-CoreBanking` and correlate `employee_id` → identity `userId`.
- Insert a brand-new row for a joiner with a bad correlation key, re-aggregate, and resolve the orphan deliberately.
- Explain why `entitlement` (not `status`) is the managed/governed attribute.

## Before you start

- [ ] JDBC container running (`docker ps | grep jdbc`)
- [ ] `MNB-CoreBanking` Application exists in IIQ (Lesson 202 seed)
- [ ] Lesson 207’s `e2e.sandbox` joiner exists (used as the correlation-repair subject)
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/208
```

## Do this

### Task 1 — Query accounts in Postgres

Ground truth before aggregation. Confirm container name with `docker ps | grep jdbc` if yours differs.

```bash
docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps -c "select account_id, username, status, entitlement from mnb_app_accounts;"
```

- **Why:** if the table is wrong, IIQ can only amplify it.
- **Expect:** `samir.hassan`’s row shows `status = DISABLED` — baseline for the “already disabled” case.

### Task 2 — Glance at the entitlement catalog table

```bash
docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps -c "select * from mnb_app_entitlements;"
```

- **Why:** `WIRE_INIT` and `WIRE_APPR` are both `risk_tier = critical` — the same pair Lesson 224’s SoD policy cares about.
- **Expect:** both entitlements listed with `risk_tier critical`.

### Task 3 — Test Connection and aggregate MNB-CoreBanking

1. **Applications → Application Definition → MNB-CoreBanking**
2. Confirm schema at a glance:
   - `identityAttribute` = `account_id`
   - `displayAttribute` = `username`
3. **Test Connection**
4. Run **Account Aggregation** (**Setup → Tasks** → create the task if needed)

- **Why:** one account link per row — operators own the first pull after seed.
- **Expect:** aggregation Task Result succeeds.

### Task 4 — Prove correlation on Priya’s cube

Correlation key: JDBC `employee_id` → identity `userId` (e.g. `MNB00090` for `priya.wire`).

1. **Identities → Identity Warehouse → priya.wire**
2. Confirm `MNB-CoreBanking` link
3. Confirm entitlement `WIRE_INIT` under Application Accounts / Entitlements

- **Why:** `status` is account-level lifecycle; `entitlement` is what grants capability and what certs/SoD review.
- **Expect:** correlated link with `WIRE_INIT` visible.

> **Tip:** When you look at Samir later, `DISABLED` status and governed entitlement are different axes — don’t treat status as the entitlement.

### Task 5 — Insert an orphan on purpose

`MNB-E2E` is intentionally **not** the joiner’s real HCM `id` from Lesson 207 — simulates a system that provisions out-of-band before IIQ catches up.

```bash
docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps -c "insert into mnb_app_accounts (account_id, username, email, employee_id, status, entitlement) values ('jdbc-e2e', 'e2e.sandbox', 'e2e.sandbox@meridiannb.com', 'MNB-E2E', 'ACTIVE', 'DWRP');"
```

- **Why:** you need a controlled orphan before Lesson 214 formalizes the fix pattern.
- **Expect:** insert succeeds.

### Task 6 — Re-aggregate and find the uncorrelated account

1. Re-run **Account Aggregation** for `MNB-CoreBanking`
2. Check **Identities → Uncorrelated Accounts** (or equivalent)

- **Why:** the row lands as an account link, but `employee_id` (`MNB-E2E`) doesn’t match any real `userId`.
- **Expect:** new row aggregates as an **uncorrelated** account.

### Task 7 — Fix the orphan deliberately

This is the exercise — not a shortcut to skip.

Pick one:

- Update `employee_id` to the joiner’s real HCM `id` and re-aggregate, **or**
- Manually correlate from IIQ’s uncorrelated-accounts view

- **Why:** ops triage is either fix the source key or attach the link by hand.
- **Expect:** the link ends up on `e2e.sandbox`’s cube.

### Task 8 — Close with asserts

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
| Test Connection fails from IIQ but `psql` works from your host | IIQ connects via internal hostname `jdbc-pg:5432`, not the host-published port |
| Insert succeeds but aggregation shows the old row count | Re-run aggregation; IIQ doesn’t poll the database automatically |
| Orphan never resolves after fixing `employee_id` | Re-run aggregation *and* a correlation-enabled refresh; fixing the source row alone doesn’t retroactively fix an already-created uncorrelated link |

## You are done when

- [ ] `MNB-CoreBanking` aggregates cleanly
- [ ] `priya.wire` shows a correlated `WIRE_INIT` entitlement
- [ ] You’ve personally created and then resolved one uncorrelated account by hand
- [ ] `./tools/lab/enterprise/verify-lesson.sh 208` hard asserts PASS

## Control note

- **Control:** Entitlement governance on in-house / vendor database applications
- **Owner:** Core Banking app owner + IAM Ops
- **SLA (lab):** orphan correlation resolved same session; production target is same-day
- **Evidence:** `~/iiq-lab-evidence/sandbox/208/` — `psql` query output, before/after uncorrelated-account screenshot

## Quick check

1. Which column is governed for certs/SoD — `status` or `entitlement`? → `entitlement`
2. What correlation key maps to identity `userId` on this app? → `employee_id`
3. Why does the deliberately-bad `employee_id` insert create an orphan? → it doesn’t match any real `userId`, so aggregation can’t attach the link to an existing cube

## Feedback

Could you insert another orphan row and resolve it without looking at the SQL? If correlation stuck, note whether you re-aggregated **and** refreshed after fixing `employee_id`.

## Navigate

- Previous: [Lesson 207](207-hcm-workday-shaped.md)
- Next: [Lesson 209](209-wire-webservices.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
