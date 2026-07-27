# Lesson 64 — JDBC Provisioning Policies

| Field | Value |
| --- | --- |
| **Level** | Intermediate |
| **Track** | Connectors — Databases |
| **Time** | 75–90 minutes |
| **Prereq** | Lesson 63; `MNB-CoreBanking-JDBC` shell/maps exist |
| **Lab data** | `jdbc/mnb_core_accounts.sql`; `jdbc/sample-rows.csv`; feature matrix |

## Learning objectives

You will be able to:

- Design create / update / delete / disable SQL (or stored-proc) provisioning for Meridian JDBC
- Prefer stored procedures for Core Banking over ad-hoc UPDATEs
- Build provisioning policy attribute maps for `mnb_app_accounts`
- Write lab-without-live-DB test cases with Expected result / If it fails
- Align ENABLE/DISABLE to `status` column semantics

## Why this matters

Raw `DELETE FROM` in bank core schemas is dangerous. Meridian’s matrix note says prefer stored-proc provisioning. IIQ provisioning policies must call controlled SQL that Core Banking DBA owns—otherwise IAM becomes an unreviewed DDL threat.

**Control / audit:** Provisioning SQL/procs are change-controlled artifacts. Examiners compare leaver disable SQL to the feature matrix ENABLE row.

## Concepts

| Operation | Meridian JDBC intent |
| --- | --- |
| Create | INSERT account (+ optional entitlement) |
| Modify | UPDATE attributes / entitlement |
| Delete | Soft-delete or controlled proc—not casual DELETE |
| Disable | `status='DISABLED'` (ENABLE feature) |
| Enable | `status='ACTIVE'` |

```text
  LCM / leaver plan
        |
        v
  Provisioning policy (JDBC)
        |
        +-- Create SQL / proc
        +-- Update SQL / proc
        +-- Delete SQL / proc
        +-- Enable/Disable via status
        |
        v
  mnb_app_accounts
```

## Before you start

- [ ] Lesson 63 maps file available
- [ ] DBA contact named for prod proc ownership (lab: yourself)
- [ ] Feature matrix: PROVISIONING/ENABLE for JDBC = Y design
- [ ] Sample personas ready for test case IDs

## Lab procedure

### Task 1 — Choose SQL vs stored-proc strategy

1. Write in `~/iiq-lab-data/connectors/jdbc/MNB-JDBC-provisioning-64.md`:

> Lab may use inline SQL. Production Meridian Core Banking must use DBA-approved stored procedures for create/update/disable.

2. List proc names (fictional OK): `mnb_sp_create_account`, `mnb_sp_set_status`, `mnb_sp_set_entitlement`.

**Expected result:** Strategy paragraph + proc name list.

### Task 2 — Lab without live target — draft SQL statements

1. Draft create:

```sql
INSERT INTO mnb_app_accounts
  (account_id, username, email, employee_id, status, entitlement)
VALUES
  (?, ?, ?, ?, 'ACTIVE', ?);
```

2. Draft disable:

```sql
UPDATE mnb_app_accounts SET status = 'DISABLED', updated_at = CURRENT_TIMESTAMP
WHERE account_id = ?;
```

3. Draft entitlement modify:

```sql
UPDATE mnb_app_accounts SET entitlement = ?, updated_at = CURRENT_TIMESTAMP
WHERE account_id = ?;
```

4. Draft delete policy: soft-delete preferred—set DISABLED + clear entitlement; hard DELETE only with DBA ADR.

**Expected result:** SQL drafts in provisioning file (not executed required).

**If it fails:** Keep drafts as strings even if IIQ UI fields differ—map later.

### Task 3 — Provisioning policy in IIQ (or notes)

1. Open `MNB-CoreBanking-JDBC` → provisioning policy / create policy forms (or equivalent menu path).
2. Map plan attributes to SQL bind parameters: `account_id`, `username`, `email`, `employee_id`, `entitlement`, `status`.
3. Ensure disable uses status UPDATE, not missing op.
4. If UI unavailable: paste policy field table into the markdown file—lab-without-live-target complete.

**Expected result:** Policy configured in IIQ **or** full field table in notes.

### Task 4 — Test matrix

| Test ID | Op | Persona / data | Expected result | If it fails |
| --- | --- | --- | --- | --- |
| JDBC-CR-01 | Create | `nina.joiner` lab account | New row ACTIVE | SQL binds / PROVISIONING |
| JDBC-EN-01 | Disable | `samir.hassan` | `status=DISABLED` | ENABLE mapping |
| JDBC-MD-01 | Modify entitlement | `jordan.reed` | entitlement updated | Update SQL |
| JDBC-DL-01 | Delete/soft | lab only | Soft-disable per policy | Block hard delete if ADR forbids |

**Expected result:** Four tests documented; execute only if live DB present.

### Task 5 — Wire dual-control safety note

1. Write: provisioning must not grant both `WIRE_INIT` and `WIRE_APPR` to one user—SoD policies still apply (Lessons 40–41).
2. Expected result: SoD still blocks toxic combo even if SQL would allow.

**Expected result:** Safety note in file.

### Task 6 — Idempotency expectation

1. Re-running disable for already-DISABLED `samir.hassan` must succeed or no-op cleanly—not error spam.
2. Document idempotent UPDATE expectation for procs.
3. Expected result: idempotency note. If it fails (unique constraint on re-create): use upsert/proc guards.

**Expected result:** Idempotency paragraph in provisioning file.

### Task 7 — CHANGELOG + runbook

1. CHANGELOG: “Lesson 64 JDBC provisioning SQL/proc policies drafted.”
2. Runbook: note “disable via status UPDATE / proc `mnb_sp_set_status`.”

**Expected result:** Docs updated.

## Acceptance criteria

- [ ] SQL vs proc strategy written (prod = procs)
- [ ] Create/disable/modify SQL drafted (lab-without-live-target)
- [ ] Policy mapped in IIQ or notes table
- [ ] ≥4 tests with Expected result / If it fails
- [ ] Wire SoD safety note included
- [ ] Idempotency expectation documented
- [ ] CHANGELOG + runbook touched

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Create succeeds, disable no-op | No ENABLE SQL | Add status UPDATE |
| Hard deletes in prod | Missing ADR | Switch to soft-delete proc |
| Bind mismatch | Wrong attribute names | Align to schema maps |
| SoD bypass | Direct SQL grant | Keep IIQ policy + SoD checks |
| Live test blocked | No DB | Accept design drafts |

## Training binder evidence

- `MNB-JDBC-provisioning-64.md` with SQL/procs
- Policy screenshot or notes table
- Test matrix
- Prod proc preference statement

**Examiner question:** “Show the controlled statement that disables a core banking application account on termination.”

## Knowledge check

1. Why prefer stored procedures for Meridian Core Banking?
2. How is disable modeled on `mnb_app_accounts`?
3. Is hard DELETE the default leaver action?
4. Can provisioning ignore SoD for wire entitlements?
5. Is a live DB required for acceptance?

### Answers

1. DBA-owned, audited, least-privilege operations vs ad-hoc SQL from IAM.
2. `status='DISABLED'` (ENABLE semantics).
3. No—prefer soft-disable / controlled proc.
4. No—SoD policies still apply.
5. No—SQL drafts and policy maps satisfy lab-without-live-target.

## Stretch lab

- Implement fictional proc signatures and IIQ callable statements.
- Add before-provisioning rule stub name for Lesson 91.
- Create negative test: refuse create without `employee_id`.

## Summary

- JDBC provisioning is policy-driven SQL/procs, not freehand DML.
- Disable maps to `status`; prod prefers stored procedures.
- Offline drafts unlock training without a database.

---

**Previous:** [Lesson 63 — JDBC Connector Fundamentals](63-jdbc-connector-fundamentals.md)  
**Next:** [Lesson 65 — Microsoft SQL Server Direct Connector](65-mssql-direct-connector.md)
