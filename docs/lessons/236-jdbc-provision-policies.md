# Lesson 236 — JDBC Create/Disable Policies

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~60 minutes  
**Prereq:** Lesson 208  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 64

> **Why:** Policies turn plans into SQL. Keep the core banking row on leaver — deleting it destroys the audit trail and breaks rehire/reconciliation when you need the row later.

## What this is

`MNB-CoreBanking` is a `JDBCConnector` reading `mnb_app_accounts` (`account_id, username, email, employee_id, status, entitlement`) with `featuresString="PROVISIONING, SYNC_PROVISIONING, ENABLE"` — the plumbing already supports writes, but nothing tells IIQ **what SQL to run** for Create/Enable/Disable. That's the connector's Provisioning Policy tab: it maps `AttributeRequest` operations to parameterized SQL against this exact schema. You define Create and Disable policies, exercise both from real joiner/leaver events, and confirm with `psql`.

## Know these

| Policy | Maps to | Column effect |
| --- | --- | --- |
| Create | `username`, `email`, `employee_id`, `status` | Inserts a new row |
| Disable | `Disable` operation | Flips `status` → `DISABLED`, row intact |
| (not built) | `Delete` | Would drop the row — wrong default for a bank |

**Wrong way:** Mapping Disable to a hard `DELETE` — it loses the audit trail and breaks re-correlation if the same employee ID returns (rehire).

## Intent

- Define a Create policy that inserts a new row into `mnb_app_accounts`.
- Define a Disable policy that flips `status` rather than deleting the row.
- Fire a real joiner and watch a JDBC account get created from the plan.
- Fire a real leaver and watch `status` flip to disabled, not the row vanish.

## Before you start

- [ ] Lesson 208 `MNB-CoreBanking` aggregating cleanly
- [ ] `psql` reachable at host port `5435`
- [ ] `hcm-scenario.sh joiner`/`leaver` scripts available
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/236`

## Do this

1. **Applications → Application Definition → MNB-CoreBanking → Provisioning Policies**. Add a **Create** policy: `username` ← `$identity.name`, `email` ← `$identity.email`, `employee_id` ← `$identity.employeeNumber`, `status` ← literal `ACTIVE`, `entitlement` ← default/blank.  
   **Expect:** Only these columns are exposed — anything else silently no-ops.
2. Add a **Disable** policy mapped to the `Disable` operation: `status` ← literal `DISABLED`. Do **not** map a Delete operation.  
   **Expect:** Policy saves with no Delete mapping present.
3. Run a joiner: `./tools/lab/enterprise/hcm-scenario.sh joiner lab.jdbctest JDBC Test lab.jdbctest@meridiannb.com`, aggregate `MNB-Workday`, refresh, and let the birthright provisioning include a CoreBanking account (or request one manually).  
   **Expect:** Provisioning transaction completes.
4. Confirm: `psql -h localhost -p 5435 -U mnb -d mnb_apps -c "select account_id, username, email, employee_id, status from mnb_app_accounts where username='lab.jdbctest';"`.  
   **Expect:** `status = ACTIVE`.
5. Run a leaver against the same identity (219's flow, or `./tools/lab/enterprise/hcm-scenario.sh leaver lab.jdbctest`), aggregate HR, let the leaver workflow disable the CoreBanking account.  
   **Expect:** Leaver workflow completes.
6. Re-run the same `psql` query.  
   **Expect:** `status = DISABLED`, row still exists with all original columns intact.
7. Write one line explaining why Disable is a status flip, not a Delete — the row is ops/reconciliation evidence; deleting it breaks re-correlation on rehire.  
   **Expect:** Note saved with your evidence.
8. Save the two `psql` outputs (post-create, post-disable) and your note under `~/iiq-lab-evidence/sandbox/236/`.

## If it fails

- **Create policy saves but no row appears** — confirm the joiner's plan actually included `MNB-CoreBanking` as a target app; birthright roles may not have it in their provisioning policy yet.
- **`psql` connection refused** — confirm host-mapped port `5435`, not the in-container `5432`.
- **Disable ran but row shows `ACTIVE` still** — some leaver workflows generate a full `Delete` AttributeRequest instead of `Disable`; check the workflow step and adjust the mapped operation.

## You are done when

A JDBC account was created from a live joiner and disabled (status flipped, row intact) from a live leaver, both confirmed with `psql`.

## Control note

- **Control:** Core banking account lifecycle without evidence loss.  
- **Owner:** IAM Engineering / Core Banking App Owner.  
- **SLA (lab):** Disable same cycle as leaver event; no hard deletes.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/236/` — `psql` post-create/post-disable, rationale note.

## Quick check

1. Why flip `status` instead of deleting the row on leaver? → Preserves audit trail; supports rehire re-correlation.  
2. Which port does the Mac host use for `psql`? → `5435`.  
3. What columns does the schema actually expose for mapping? → `username, email, employee_id, status, entitlement`.

## Navigate

- Previous: Lesson 235
- Next: Lesson 237
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
