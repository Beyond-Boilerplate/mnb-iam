# Lesson 64 — JDBC Provisioning Policies

**Level:** Intermediate  
**Track:** Connectors — Databases  
**Time:** 90–120 min  
**Prereq:** Lesson 63 — JDBC Connector Fundamentals; `MNB-CoreBanking-JDBC` against live jdbc-pg  

**Lab data:**
- Repo: `lab-data/connectors/jdbc/mnb_core_accounts.sql`
- Repo: `lab-data/connectors/jdbc/sample-rows.csv`
- Repo: `lab-data/connectors/features-string-glossary.md`
- Repo: `docker-compose.connectors.yml` — **live Postgres (`jdbc-pg`) on host port 5433; required**
- Runtime: `~/iiq-lab-data/connectors/jdbc/`

---

## Learning objectives

You will be able to:

- Design create / update / disable / soft-delete SQL for `mnb_app_accounts` and prefer DBA-owned stored procedures in production
- Configure JDBC provisioning policy attribute maps on **MNB-CoreBanking-JDBC** against live Postgres
- Execute disable and modify against jdbc-pg and verify with `psql` (not just Task Result green)
- Keep wire dual-control SoD intact when entitlement SQL would otherwise allow a toxic combo
- Write idempotent ENABLE semantics on `status` that examiners can quote

---

## Why this matters

**Business.** Aggregation (Lesson 63) only inventories. When `nina.joiner` needs a core-banking row, or `samir.hassan` must lose `ACTIVE` status within the leaver SLA, IdentityIQ must run controlled DML — not hope a DBA notices a ticket. Raw `DELETE FROM mnb_app_accounts` in a bank schema is how IAM becomes an unreviewed operational risk.

**Control / audit.** Examiners ask: *“Show the controlled statement that disables a core banking application account on termination.”* Versioned SQL or stored-proc names, plus a `psql` before/after, answer that. Ad-hoc UPDATE strings living only in an engineer’s head do not.

---

## Concepts

### Provisioning is not aggregation with a write flag

Lesson 63’s iterate SQL **reads**. Provisioning policies bind plan attributes to **write** statements (or callable procedures). The JDBC connector’s `PROVISIONING` / `ENABLE` features (Lesson 55) only matter if those statements exist and are correct.

| Operation | Meridian intent on `mnb_app_accounts` |
| --- | --- |
| Create | `INSERT` new row; `status='ACTIVE'` |
| Modify | `UPDATE` attributes / `entitlement` |
| Disable | `status='DISABLED'` (ENABLE feature) |
| Enable | `status='ACTIVE'` |
| Delete | Soft-disable preferred; hard `DELETE` only with DBA ADR |

### Why production prefers stored procedures

Inline SQL in the Application object works in the lab. In production Meridian Core Banking:

- DBAs own procedure source under CRQ; IAM calls `mnb_sp_set_status`, not freehand UPDATE.
- Least-privilege grants `EXECUTE` on procs — not `UPDATE` on every column.
- Auditing and bind validation live in one place.

Lab may use parameterized inline SQL against jdbc-pg; the binder must still name the production proc strategy.

### Seed truth you will mutate

| account_id | username | status (start) | entitlement |
| --- | --- | --- | --- |
| jdbc-001 | `priya.wire` | ACTIVE | WIRE_INIT |
| jdbc-002 | `marcus.approve` | ACTIVE | WIRE_APPR |
| jdbc-003 | `jordan.reed` | ACTIVE | SAP_FI |
| jdbc-004 | `samir.hassan` | DISABLED | DWRP |

Never grant both `WIRE_INIT` and `WIRE_APPR` to one identity — SoD (Lessons 40–41) still applies even if SQL would allow it.

```
  LCM / leaver plan
        │
        ▼
  JDBC provisioning policy (binds + SQL/proc)
        │
        ▼
  PostgreSQL jdbc-pg :5433 / mnb_apps
        │
        ▼
  mnb_app_accounts row change → next aggregation sees it
```

---

## How it works

IIQ builds a provisioning plan (create account, set attribute, disable). The JDBC connector substitutes plan values into configured SQL (or callable statement), executes on the same JDBC connection settings as aggregation, and returns success/failure to the IdentityRequest / provisioning engine.

```
IdentityIQ (MNB-CoreBanking-JDBC)
        │  jdbc:postgresql://localhost:5433/mnb_apps
        │  provisioning SQL / CALL mnb_sp_*
        ▼
PostgreSQL 16 (jdbc-pg)
        ├── INSERT mnb_app_accounts     → create
        ├── UPDATE … entitlement         → modify
        └── UPDATE … status='DISABLED'   → disable (ENABLE)
```

| Plan operation | Lab SQL pattern | Verify with |
| --- | --- | --- |
| Create | `INSERT … VALUES (?,?,?,?, 'ACTIVE', ?)` | `psql` SELECT new `account_id` |
| Disable | `UPDATE … SET status='DISABLED' WHERE account_id=?` | status column |
| Modify entitlement | `UPDATE … SET entitlement=? WHERE account_id=?` | entitlement column |
| Soft delete | disable + clear entitlement | both columns |

Use **bind parameters** (`?`) — never string-concatenate usernames or entitlements (OWASP parameterization).

---

## Real-world setup (outside IIQ)

Live Postgres is **mandatory** for this lesson when Docker runs — same `jdbc-pg` as Lesson 63.

### Step 1 — Confirm jdbc-pg and seed data

```bash
docker compose -f docker-compose.connectors.yml up -d jdbc-pg
psql "postgresql://mnb:mnb@localhost:5433/mnb_apps" -c \
  "SELECT account_id, username, status, entitlement FROM mnb_app_accounts ORDER BY account_id;"
```

Expect four rows. If empty, re-run Lesson 63 seed INSERT block.

### Step 2 — Production privilege split (document even in lab)

| Account | Purpose | Grants |
| --- | --- | --- |
| `iiq_corebank_ro` | Aggregation | `SELECT` on account/dictionary tables |
| `iiq_corebank_prov` | Provisioning | `EXECUTE` on procs (or limited DML) |

Lab continues with `mnb`/`mnb` — label **lab-only**. Never use superuser in prod.

### Step 3 — Agree soft-delete ADR

With Core Banking DBA: leaver = `status='DISABLED'` (+ optional entitlement clear). Hard `DELETE` only with written ADR and retention rules.

### Step 4 — Version SQL/procs in git

Store procedure definitions next to schema fixtures. Examiners will ask for the exact disable statement — not a screenshot of a green Task Result alone.

---

## Before you start

- [ ] Lesson 63 complete: `MNB-CoreBanking-JDBC` Test Connection works to `:5433`
- [ ] `psql` available; four seed rows present
- [ ] Feature matrix: PROVISIONING/ENABLE for JDBC = Y (Lesson 55)
- [ ] IIQ at `http://localhost:8080/identityiq` as `spadmin`
- [ ] Fallback only if Docker impossible — Task 9; binder must say live path unavailable

---

## Lab procedure

### Task 1 — Choose SQL vs stored-proc strategy

Production Meridian Core Banking must not depend on ad-hoc SQL edited only in the IIQ UI.

1. Create `~/iiq-lab-data/connectors/jdbc/MNB-JDBC-provisioning-64.md` with:

> Lab uses parameterized inline SQL against jdbc-pg. Production Meridian Core Banking uses DBA-approved stored procedures for create/update/disable.

2. List proc names: `mnb_sp_create_account`, `mnb_sp_set_status`, `mnb_sp_set_entitlement`.

**Expected result:** Strategy paragraph + proc name list in the markdown file.

### Task 2 — Draft parameterized SQL (then prove on live DB)

Drafts without a live proof are incomplete when Postgres is available.

1. Draft create / disable / modify:

```sql
INSERT INTO mnb_app_accounts
  (account_id, username, email, employee_id, status, entitlement)
VALUES (?, ?, ?, ?, 'ACTIVE', ?);

UPDATE mnb_app_accounts
SET status = 'DISABLED', updated_at = CURRENT_TIMESTAMP
WHERE account_id = ?;

UPDATE mnb_app_accounts
SET entitlement = ?, updated_at = CURRENT_TIMESTAMP
WHERE account_id = ?;
```

2. Soft-delete policy: set DISABLED + clear entitlement; hard DELETE only with ADR.
3. Paste drafts into the provisioning file.

**Expected result:** SQL drafts saved with bind placeholders.

### Task 3 — Live dry-run of disable with psql

Before wiring IIQ, prove the disable statement against `samir.hassan`’s row (already DISABLED — re-run must be idempotent).

```bash
psql "postgresql://mnb:mnb@localhost:5433/mnb_apps" <<'SQL'
UPDATE mnb_app_accounts
SET status = 'DISABLED', updated_at = CURRENT_TIMESTAMP
WHERE account_id = 'jdbc-004';
SELECT account_id, username, status FROM mnb_app_accounts WHERE account_id = 'jdbc-004';
SQL
```

**Expected result:** One row, `status=DISABLED`; no error on re-run.

**If it fails:** Wrong database/port; fix connection before touching IIQ policies.

### Task 4 — Live create + cleanup for nina.joiner

Joiner create must be reversible in the lab so you do not pollute the four-row baseline permanently.

1. Insert a lab account:

```bash
psql "postgresql://mnb:mnb@localhost:5433/mnb_apps" <<'SQL'
INSERT INTO mnb_app_accounts
  (account_id, username, email, employee_id, status, entitlement)
VALUES
  ('jdbc-lab-nina','nina.joiner','nina.joiner@meridiannb.com','MNB-LAB-NINA','ACTIVE',NULL)
ON CONFLICT (account_id) DO NOTHING;
SELECT * FROM mnb_app_accounts WHERE account_id = 'jdbc-lab-nina';
SQL
```

2. Disable it with the disable SQL; confirm `DISABLED`.
3. Soft-delete cleanup: keep DISABLED or `DELETE` only the lab row when finished.

**Expected result:** Create → disable cycle proven in `psql` with screenshots/output in binder.

### Task 5 — Provisioning policy in IIQ

This is where Lesson 63’s application grows write capability.

1. Open `MNB-CoreBanking-JDBC` → provisioning policy / create policy forms (or equivalent menu path).
2. Map plan attributes to binds: `account_id`, `username`, `email`, `employee_id`, `entitlement`, `status`.
3. Configure disable to use status UPDATE (ENABLE), not a missing operation.
4. Prefer the same JDBC URL as aggregation: `jdbc:postgresql://localhost:5433/mnb_apps` (or `host.docker.internal` if IIQ is containerized).
5. Save. If UI fields differ by version, paste a field→SQL table into the markdown — still complete the live `psql` proofs.

**Expected result:** Policy configured in IIQ **and** live SQL proofs attached.

**If it fails:** Bind mismatch → align names to Lesson 63 schema map.

### Task 6 — Optional IIQ plan execution + re-aggregate

If your lab build can run a provisioning plan / IdentityRequest against JDBC:

1. Disable or modify a lab-only account via IIQ; then `psql` to confirm the row.
2. Run Account Aggregation `Aggregate MNB-CoreBanking-JDBC`; confirm cube shows DISABLED / new entitlement.
3. If plan UI is unavailable: document “SQL proven via psql; IIQ plan deferred” with dated note — still require Tasks 3–4 live proofs.

**Expected result:** Either IIQ+psql evidence or dated deferral **with** psql proofs already done.

### Task 7 — Test matrix and wire SoD safety

| Test ID | Op | Data | Expected result | If it fails |
| --- | --- | --- | --- | --- |
| JDBC-CR-01 | Create | `nina.joiner` lab | New ACTIVE row | binds / PROVISIONING |
| JDBC-EN-01 | Disable | `jdbc-004` / lab row | `status=DISABLED` | ENABLE SQL |
| JDBC-MD-01 | Modify | `jordan.reed` entitlement | column updated | Update SQL |
| JDBC-DL-01 | Soft delete | lab only | DISABLED + cleared ent | block hard delete |
| JDBC-SOD-01 | Refuse dual wire | — | SoD blocks INIT+APPR | policy not SQL-only |

Add SoD note: provisioning must not grant both `WIRE_INIT` and `WIRE_APPR` to one user.

**Expected result:** Five tests documented; SOD note present.

### Task 8 — Idempotency, runbook, CHANGELOG

1. Re-running disable on already-DISABLED must succeed or no-op — not error spam (you proved this in Task 3).
2. Runbook: *Leaver disable = `mnb_sp_set_status` / status UPDATE; verify with aggregation + optional psql.*
3. CHANGELOG: “Lesson 64 JDBC provisioning policies against live jdbc-pg.”

**Expected result:** Idempotency paragraph + runbook + CHANGELOG.

### Task 9 — Fallback (only if Docker cannot run)

Secondary path — binder must say live path was **unavailable**.

1. Complete strategy, SQL drafts, policy field table, test matrix, SoD, idempotency on paper.
2. Do **not** claim live disable evidence.
3. Resume Tasks 3–6 when jdbc-pg is available.

**Expected result:** Design artifacts complete; dated deferral.

---

## Acceptance criteria

- [ ] SQL vs proc strategy written (prod = procs)
- [ ] Create/disable/modify SQL drafted with binds
- [ ] Live `psql` disable (+ create cycle) against jdbc-pg **or** dated Docker deferral
- [ ] Policy mapped in IIQ or notes table tied to live URL
- [ ] ≥4 tests + wire SoD safety + idempotency notes
- [ ] Runbook + CHANGELOG updated

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Create succeeds, disable no-op | No ENABLE SQL | Add status UPDATE |
| Hard deletes in prod plan | Missing ADR | Soft-disable proc only |
| Bind mismatch | Wrong attribute names | Align to Lesson 63 maps |
| SoD bypass | Direct SQL grant | Keep IIQ + SoD checks |
| Connection refused | jdbc-pg down / wrong port | Host port **5433**; compose ps |
| IIQ in Docker cannot reach DB | `localhost` is the container | `host.docker.internal` or `jdbc-pg` |

---

## Training binder evidence

- `MNB-JDBC-provisioning-64.md` (strategy, SQL, procs, SoD, idempotency)
- `psql` before/after for disable and lab create
- Policy screenshot or notes table (password masked)
- Test matrix + CHANGELOG

**Examiner question:** *“Show the controlled statement that disables a core banking application account on termination.”*

---

## Knowledge check

1. Why prefer stored procedures for Meridian Core Banking in production?
2. How is disable modeled on `mnb_app_accounts`?
3. Is hard DELETE the default leaver action?
4. Can provisioning ignore SoD for wire entitlements?
5. What host port does live jdbc-pg use?
6. Why use bind parameters instead of string concatenation?

### Answers

1. DBA-owned, audited, least-privilege `EXECUTE` vs ad-hoc SQL from IAM.
2. `status='DISABLED'` (ENABLE semantics).
3. No — prefer soft-disable / controlled proc.
4. No — SoD still applies.
5. **5433** (container 5432).
6. Prevent SQL injection and broken quoting; OWASP parameterization.

---

## Further reading

- [OWASP Query Parameterization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Query_Parameterization_Cheat_Sheet.html) — mandatory mindset for JDBC binds.
- [PostgreSQL CREATE PROCEDURE](https://www.postgresql.org/docs/current/sql-createprocedure.html) — model `mnb_sp_set_status` for production.
- [PostgreSQL privileges](https://www.postgresql.org/docs/current/ddl-priv.html) — split `iiq_corebank_ro` vs `iiq_corebank_prov`.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “JDBC provisioning” / provisioning policies for SQL statement fields.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — JDBC enable/disable and bind troubleshooting threads.

---

## Stretch lab

Implement stub procedure signatures in Postgres (`CREATE PROCEDURE mnb_sp_set_status…`) and point IIQ at `CALL` statements. Add a before-provisioning rule stub name for Lesson 91. Negative test: refuse create without `employee_id`. Join `mnb_app_entitlements.risk_tier` in post-provision verification queries.

---

## Summary

- JDBC provisioning is policy-driven SQL/procs on live `mnb_app_accounts`, verified with `psql` — not freehand DML.
- Disable maps to `status`; production prefers stored procedures and split RO/prov accounts.
- Wire SoD and idempotent disable are part of the control, not optional footnotes.

---

**Previous:** [Lesson 63 — JDBC Connector Fundamentals](63-jdbc-connector-fundamentals.md)  
**Next:** [Lesson 65 — Microsoft SQL Server Direct Connector](65-mssql-direct-connector.md)
