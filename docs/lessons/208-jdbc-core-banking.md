# Lesson 208 — JDBC Core Banking Live

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~55 minutes  
**Prereq:** Lesson 202  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 63–64

> **Why (1–2 lines):** A huge share of real bank applications are just tables behind a login screen — JDBC is the honest connector for that. An examiner will ask which attribute is actually governed on a flat-table app; get the answer wrong and every downstream cert/SoD review is reviewing the wrong column.

## What this is

`MNB-CoreBanking` is a real `JDBC` connector application against `jdbc-pg` (PostgreSQL, `jdbc:postgresql://jdbc-pg:5432/mnb_apps`, credentials `mnb`/`mnb`). Its account query is `SELECT account_id, username, email, employee_id, status, entitlement FROM mnb_app_accounts` — a single flat table where `entitlement` is the managed/entitled column (values like `WIRE_INIT`, `WIRE_APPR`, `SAP_FI`, `DWRP`, defined in a companion `mnb_app_entitlements` lookup table with a `risk_tier`). This table is seeded once at container init from `lab-data/connectors/jdbc/mnb_core_accounts.sql` — rows for `priya.wire` (`WIRE_INIT`), `marcus.approve` (`WIRE_APPR`), `jordan.reed` (`SAP_FI`), `samir.hassan` (`DWRP`, status `DISABLED`), `helen.ross` and `christopher.hayes` (both `DWRP`). This is the connector you'll reach for whenever a "vendor" or in-house system doesn't have a real API — which, in banking, is often.

## Know these

| Column | Role |
| --- | --- |
| `account_id` | `identityAttribute` (native key) |
| `username` | `displayAttribute` |
| `employee_id` | correlation key → identity `userId` |
| `status` | account-level lifecycle (`ACTIVE`/`DISABLED`) — not governed |
| `entitlement` | the governed/managed attribute — what certs and SoD (Lesson 224) actually review |

**Wrong way:** Treating `status` as the attribute certifications should review — `status` is enable/disable plumbing; `entitlement` is what grants real capability inside Core Banking.

## Intent

- Query the live table with `psql` before touching IIQ, so you know the ground truth independent of aggregation.
- Aggregate `MNB-CoreBanking` and correlate `employee_id`→identity `userId`.
- Insert a brand-new row for a joiner by hand, re-aggregate, and pick it up as an uncorrelated account you then correlate deliberately.
- Explain why `entitlement` (not `status`) is the managed/governed attribute on this schema.

## Before you start

- [ ] `mnb-jdbc-sample` container running (`docker ps | grep jdbc-pg`)
- [ ] `MNB-CoreBanking` Application exists in IIQ (Lesson 202 seed)
- [ ] Lesson 207's `e2e.sandbox` joiner exists (used as the correlation-repair subject)
- [ ] Evidence dir: `mkdir -p ~/iiq-lab-evidence/sandbox/208`

## Do this

1. Query the table directly: `docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps -c "select account_id, username, status, entitlement from mnb_app_accounts;"`.  
   **Why:** ground truth before aggregation — confirm the container name with `docker ps | grep jdbc-pg` if yours differs.  
   **Expect:** `samir.hassan`'s row shows `status = DISABLED` — your baseline for the "already disabled" case.

2. Glance at the entitlement catalog table: `docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps -c "select * from mnb_app_entitlements;"`.  
   **Why:** `WIRE_INIT` and `WIRE_APPR` are both `risk_tier = critical` — the same pair Lesson 224's SoD policy cares about.  
   **Expect:** both entitlements listed with `risk_tier critical`.

3. In IIQ, open **Applications → Application Definition → MNB-CoreBanking**, **Test Connection**, then run **Account Aggregation**.  
   **Why:** schema's `identityAttribute` is `account_id`, `displayAttribute` is `username` — one account link per row.  
   **Expect:** aggregation Task Result succeeds.

4. Correlate `employee_id` (e.g. `MNB00090` for `priya.wire`) → identity `userId`. Open Priya's cube.  
   **Why:** confirms the correlation pattern shared by every live app in this path.  
   **Expect:** `MNB-CoreBanking` link with entitlement `WIRE_INIT` under Application Accounts/Entitlements.

5. Insert a new row for `e2e.sandbox` with a deliberately bad correlation key: `docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps -c "insert into mnb_app_accounts (account_id, username, email, employee_id, status, entitlement) values ('jdbc-e2e', 'e2e.sandbox', 'e2e.sandbox@meridiannb.com', 'MNB-E2E', 'ACTIVE', 'DWRP');"`.  
   **Why:** `MNB-E2E` is intentionally **not** the joiner's real HCM `id` from Lesson 207 — simulates a system that provisions out-of-band before IIQ catches up, a common real-world "shadow IT" pattern.  
   **Expect:** insert succeeds.

6. Re-run **Account Aggregation**.  
   **Why:** the row lands as an account link, but `employee_id` (`MNB-E2E`) doesn't match any real `userId`.  
   **Expect:** the new row aggregates as an **uncorrelated** account — the orphan pattern Lesson 214 formalizes a fix for.

7. Fix the orphan deliberately — either update `employee_id` to the joiner's real HCM `id` and re-aggregate, or manually correlate from IIQ's uncorrelated-accounts view.  
   **Why:** this is the exercise, not a shortcut to skip.  
   **Expect:** the link ends up on `e2e.sandbox`'s cube.

8. State why `entitlement`, not `status`, is the governed attribute.  
   **Why:** `status` is account-level lifecycle state; `entitlement` is what actually grants capability inside Core Banking and is what certifications and SoD policy review.  
   **Expect:** you can say this from memory.

## If it fails

- **`docker exec` container name wrong** — `docker ps --format '{{.Names}}'` and use whatever the `jdbc-pg` service actually resolved to.
- **`psql: FATAL: password authentication failed`** — credentials are `mnb`/`mnb` against database `mnb_apps`.
- **Test Connection fails from IIQ but `psql` works from your host** — IIQ connects via internal hostname `jdbc-pg:5432`, not the host-published port; confirm the Application XML's `url` wasn't edited to a host-facing address.
- **Insert succeeds but aggregation shows the old row count** — re-run aggregation; IIQ doesn't poll the database automatically.
- **Orphan never resolves after fixing `employee_id`** — you must re-run aggregation *and* a correlation-enabled refresh; fixing the source row alone doesn't retroactively fix an already-created uncorrelated link.

## You are done when

`MNB-CoreBanking` aggregates cleanly, `priya.wire` shows a correlated `WIRE_INIT` entitlement, and you've personally created and then resolved one uncorrelated account by hand.

## Control note

- **Control:** Entitlement governance on in-house/vendor database applications.
- **Owner:** Core Banking app owner + IAM Ops.
- **SLA (lab):** orphan correlation resolved same session; production target is same-day.
- **Evidence:** `~/iiq-lab-evidence/sandbox/208/` — `psql` query output, before/after uncorrelated-account screenshot.

## Quick check

1. Which column is governed for certs/SoD — `status` or `entitlement`? → `entitlement`.
2. What correlation key maps to identity `userId` on this app? → `employee_id`.
3. Why does the deliberately-bad `employee_id` insert create an orphan? → it doesn't match any real `userId`, so aggregation can't attach the link to an existing cube.

## Navigate

- Previous: Lesson 207
- Next: Lesson 209
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
