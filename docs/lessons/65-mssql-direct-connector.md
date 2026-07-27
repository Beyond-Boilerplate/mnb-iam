# Lesson 65 — Microsoft SQL Server Direct Connector

| Field | Value |
| --- | --- |
| **Level** | Intermediate |
| **Track** | Connectors — Databases |
| **Time** | 60–90 minutes |
| **Prereq** | Lessons 63–64; matrix row SQL Server |
| **Lab data** | `jdbc/` fixtures (reuse schema concepts); selection matrix; feature glossary |

## Learning objectives

You will be able to:

- Select Microsoft SQL Server - Direct vs JDBC for Meridian reporting databases
- Create Application shell `MNB-MSSQL-Reporting`
- Document host, instance, auth mode, and role/login aggregation without a live SQL Server
- Compare Direct connector features to JDBC provisioning policies
- Define aggregate task and disable/login test cases with Expected result / If it fails

## Why this matters

Meridian reporting and some bank satellite DBs run on SQL Server. The matrix prefers **Microsoft SQL Server - Direct** with JDBC as alternate. Teams that only know JDBC miss Direct login/role semantics; teams that force Direct on non-MSSQL fail.

**Control / audit:** SQL Server logins and server/database roles are privileged. Aggregation scope and provisioning rights need DBA sign-off; sa-equivalent IIQ accounts are findings.

## Concepts

| Option | When Meridian uses it |
| --- | --- |
| Microsoft SQL Server - Direct | Native MSSQL logins/roles, Direct features |
| JDBC | Portable SQL against MSSQL or other RDBMS; Core Banking preferred JDBC in matrix |
| `MNB-CoreBanking-JDBC` | Already built—do not duplicate as MSSQL Direct without ADR |
| `MNB-MSSQL-Reporting` | Reporting DB Direct app |

```text
  connector-selection-matrix.csv
        |
        +-- Core banking DB → JDBC → MNB-CoreBanking-JDBC
        +-- SQL Server      → MSSQL Direct → MNB-MSSQL-Reporting
                                alternate: JDBC
```

Reuse account concepts from `sample-rows.csv` as **logical** test personas even if Direct schema differs (logins vs table rows)—document the mapping.

## Before you start

- [ ] Lesson 52 SQL Server row reviewed
- [ ] JDBC app exists so you can contrast—not replace—Core Banking
- [ ] No live SQL Server required
- [ ] IIQ up for shell if type present

## Lab procedure

### Task 1 — Selection justification

1. Write `~/iiq-lab-data/connectors/jdbc/MNB-MSSQL-selection-65.md`:

| Question | Answer |
| --- | --- |
| Why not use JDBC for this reporting DB? | Want Direct login/role model / features |
| Why not convert Core Banking to MSSQL Direct? | Matrix prefers JDBC + procs for core |
| Alternate if Direct type missing? | JDBC against MSSQL |

**Expected result:** Selection file with clear Core Banking vs Reporting split.

### Task 2 — Lab without live target — connection & scope worksheet

1. Complete fictional worksheet:

| Item | Lab value |
| --- | --- |
| Host | `mnb-mssql-reporting.lab` |
| Instance / port | `MSSQLSERVER` / 1433 |
| Auth | Windows integrated via service acct **or** SQL login (document choice) |
| IIQ DB account | `iiq_mssql_ro` aggregate; separate `iiq_mssql_prov` if provisioning |
| Databases in scope | `MNB_Reporting` only |
| Aggregate | SQL logins and/or DB users + roles |

2. Least privilege: no `sysadmin` for IIQ.
3. Expected result: worksheet complete without connecting. If it fails (unknown auth mode): mark TBD with DBA owner.

**Expected result:** Connection scope file section populated.

### Task 3 — Create Application MNB-MSSQL-Reporting

1. Applications → Add New → **Microsoft SQL Server - Direct** (or equivalent menu path).
2. Name: `MNB-MSSQL-Reporting`. Owner: Reporting / Technology (lab `spadmin`).
3. Enter placeholders from worksheet; skip live Test Connection.
4. Non-authoritative; create-identities **off**.
5. If type missing: notes shell + plan JDBC alternate app name `MNB-MSSQL-Reporting-JDBC`.

**Expected result:** Application or notes shell exists.

### Task 4 — Schema & correlation plan

1. Account identity: SQL login name or DB user name—**document choice**.
2. Correlation: map to `userName` where login mirrors `priya.wire` style; else employee attribute table if exists.
3. Entitlements: server roles / database roles (e.g. `db_datareader`, custom `MNB_WIRE_REPORT`).
4. Disable: prefer disable login / revoke connect—map to ENABLE feature if declared.

**Expected result:** Schema plan in selection file.

### Task 5 — Test cases

| Test ID | Action | Expected result | If it fails |
| --- | --- | --- | --- |
| MSSQL-AGG-01 | Aggregate | Logins/roles appear | Auth/driver/network |
| MSSQL-EN-01 | Disable lab login | Login disabled / connect revoked | ENABLE feature / rights |
| MSSQL-COR-01 | Correlate `jordan.reed` | Link on cube | Naming mismatch |
| MSSQL-PRIV-01 | Review IIQ SQL account | Not sysadmin | Reduce privileges |

Include Expected result / If it fails on each; live run optional.

**Expected result:** Four tests documented.

### Task 6 — Contrast JDBC provisioning

1. One paragraph: JDBC Lesson 64 uses table SQL/procs on `mnb_app_accounts`; MSSQL Direct manages engine logins/roles.
2. Do not point both apps at the same core banking tables without Architecture approval.

**Expected result:** Contrast paragraph.

### Task 7 — Encryption & network controls

1. Require TLS to SQL Server for Meridian non-lab; document encrypt=true (or equivalent) connection property intent.
2. Firewall: IIQ hosts → MSSQL 1433/instance only.
3. Expected result: network/TLS bullets in worksheet. If it fails (cleartext SQL): block prod promotion.

**Expected result:** TLS + firewall notes added.

### Task 8 — Task naming + CHANGELOG

1. `Aggregate MNB-MSSQL-Reporting` named in runbook (ad-hoc or nightly per size).
2. CHANGELOG: “Lesson 65 MSSQL Direct shell for reporting DB.”
3. Next lesson preview: Oracle Database Direct (`66-oracle-db-direct-connector.md`).

**Expected result:** Runbook + CHANGELOG; navigation ready.

## Acceptance criteria

- [ ] Selection justification vs JDBC Core Banking written
- [ ] Lab-without-live-target connection/scope worksheet done
- [ ] `MNB-MSSQL-Reporting` shell or notes (+ alternate if needed)
- [ ] Schema/correlation/disable plan documented
- [ ] ≥4 tests with Expected result / If it fails
- [ ] TLS/firewall notes written
- [ ] JDBC contrast paragraph + CHANGELOG

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Type missing | IIQ edition | Use JDBC alternate; document |
| Login failed | Auth mode | Fix Windows vs SQL auth |
| Huge aggregate | Whole instance | Scope one database |
| sysadmin IIQ account | Over-privilege | Recreate least-priv logins |
| Duplicate of JDBC app | Scope creep | Keep Reporting vs Core split |

## Training binder evidence

- `MNB-MSSQL-selection-65.md` with worksheets
- Application screenshot or shell notes
- Privilege statement (not sysadmin)
- Test matrix

**Examiner question:** “Is the IdentityIQ SQL Server account a sysadmin? Show the role membership.”

## Knowledge check

1. Preferred connector for SQL Server in Meridian matrix?
2. Alternate connector?
3. What Application name does this lesson create?
4. Should this app replace `MNB-CoreBanking-JDBC`?
5. Can you complete acceptance without a live SQL Server?

### Answers

1. Microsoft SQL Server - Direct.
2. JDBC.
3. `MNB-MSSQL-Reporting`.
4. No—Core Banking stays JDBC per matrix unless Architecture changes it.
5. Yes—lab-without-live-target worksheets and shell/notes suffice.

## Stretch lab

- Map Direct role names to entitlement dictionary risk tiers.
- Draft Always Encrypted / TLS requirements for bank SQL Server.
- Premap Lesson 66 Oracle Direct differences (service name, roles).

## Summary

- `MNB-MSSQL-Reporting` is Meridian’s SQL Server Direct reporting target.
- JDBC remains correct for Core Banking; Direct serves MSSQL login/role models.
- Offline worksheets keep the database connector track moving without live servers.

---

**Previous:** [Lesson 64 — JDBC Provisioning Policies](64-jdbc-provisioning-policies.md)  
**Next:** [Lesson 66 — Oracle Database Direct Connector](66-oracle-db-direct-connector.md)
