# Lesson 65 — Microsoft SQL Server Direct Connector

**Level:** Intermediate  
**Track:** Connectors — Databases  
**Time:** 90–120 min  
**Prereq:** Lessons 63–64; selection matrix row **SQL Server**  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv`
- Repo: `lab-data/connectors/features-string-glossary.md`
- Repo: `lab-data/connectors/jdbc/sample-rows.csv` (persona reuse)
- Runtime: `~/iiq-lab-data/connectors/mssql/`

---

## Learning objectives

You will be able to:

- Select **Microsoft SQL Server - Direct** vs JDBC for Meridian reporting databases using the matrix
- Create application shell **MNB-MSSQL-Reporting** with host, auth mode, scope, and least-privilege design
- Map SQL logins / database roles to IIQ accounts and entitlements without confusing them with JDBC table rows
- Document Test Connection, Account Aggregation, and disable expectations for DBAs
- Contrast Direct login governance with `MNB-CoreBanking-JDBC` so the two apps never collide

---

## Why this matters

**Business.** Meridian’s regulatory reporting warehouse runs on SQL Server. Logins holding `db_datawriter` or custom `MNB_WIRE_REPORT` can alter or exfiltrate filings. Waiting for a quarterly DBA spreadsheet means `jordan.reed` keeps warehouse rights months after moving off the reporting team.

**Control / audit.** Examiners ask: *“Is the IdentityIQ SQL Server account a sysadmin? Show the role membership.”* Direct connector scope plus a non-sysadmin service login is the answer. Pointing a second app at core banking tables “because it’s also SQL” is an architecture defect.

---

## Concepts

### Direct vs JDBC — different objects

| Approach | What you govern | Meridian use |
| --- | --- | --- |
| **Microsoft SQL Server - Direct** | Engine **logins**, DB users, server/database **roles** | Reporting / satellite MSSQL |
| **JDBC** | Rows returned by **your SQL** (app tables) | Core banking `mnb_app_accounts` (Lessons 63–64) |

The matrix says: **SQL Server → Microsoft SQL Server - Direct** (alternate JDBC). **Core banking DB → JDBC** (alternate MSSQL Direct). Do not collapse these without an ADR.

### Logins, users, and roles

- A **login** authenticates to the instance.
- A **database user** maps that login into one database.
- **Roles** (`db_datareader`, `MNB_WIRE_REPORT`, server roles) are the entitlement-shaped grants.

Naive teams aggregate “everything on the instance” and drown certifications in noise. Scope **one database** (`MNB_Reporting`) unless Risk explicitly expands.

### Personas as logical test keys

Reuse Lesson 63 usernames as **expected login names** in worksheets even when no live SQL Server exists: `priya.wire`, `marcus.approve`, `jordan.reed`, `samir.hassan`. Document that Direct schema ≠ `mnb_app_accounts` columns.

```
  connector-selection-matrix.csv
        │
        ├── Core banking DB → JDBC → MNB-CoreBanking-JDBC
        └── SQL Server → MSSQL Direct → MNB-MSSQL-Reporting
                              alternate: JDBC against MSSQL
```

---

## How it works

The SQL Server Direct connector talks to the instance (often via JDBC driver under the hood, but with **native login/role semantics** and connector operations — not your iterate SQL). Aggregation enumerates logins/users/roles per configuration; provisioning can create logins, alter roles, and disable/revoke connect when features allow.

```
IdentityIQ (MNB-MSSQL-Reporting)
        │  host / instance / auth / TLS
        ▼
Microsoft SQL Server - Direct
        ├── Test Connection
        ├── Account Aggregation → logins / DB users
        ├── Entitlement aggregation → roles
        └── Provisioning → create / role grant / disable login
```

| Operation | Typical Direct behavior | Examiner evidence |
| --- | --- | --- |
| Test Connection | Auth + network | Screenshot success |
| Account aggregation | Logins/users in scope | Task Result counts |
| Entitlements | Server/DB roles | ManagedAttributes |
| Disable | Disable login / revoke CONNECT | ENABLE feature + post-agg |

Review `featuresString` in ConnectorRegistry before promising PASSWORD/ENABLE SLAs (Lesson 55).

---

## Real-world setup (outside IIQ)

No live SQL Server is shipped in `docker-compose.connectors.yml`. Complete this checklist as if DBA were on the call — the lab shell consumes these decisions.

### Step 1 — Instance and scope

1. Identify host (`mnb-mssql-reporting.meridiannb.com`), instance (`MSSQLSERVER` or named), port **1433** (or dynamic).
2. Agree databases in scope: **`MNB_Reporting` only** for phase 1.
3. Decide auth: Windows service account (preferred in domain) vs SQL login — document one.

### Step 2 — Least-privilege IIQ accounts

1. Create `iiq_mssql_ro` for aggregation: view definitions / security catalog as required by the connector guide — **not** `sysadmin`.
2. Create separate `iiq_mssql_prov` if provisioning — grant only create-login / alter-role rights Risk approved.
3. Vault passwords; never commit them.

### Step 3 — Network and TLS

1. Firewall: IIQ hosts → MSSQL port only.
2. Require encryption (`encrypt=true` / Force Encryption on server) for non-lab.
3. Document certificate trust path for the Java truststore on the IIQ server.

### Step 4 — Naming and ownership

1. Application: `MNB-MSSQL-Reporting`. IAM owner `helen.ross`; DBA contact `samir.hassan`.
2. Explicitly record: this app does **not** replace `MNB-CoreBanking-JDBC`.

---

## Before you start

- [ ] IIQ at `http://localhost:8080/identityiq` as `spadmin`
- [ ] Lesson 52 SQL Server row + Lesson 55 matrix open
- [ ] `MNB-CoreBanking-JDBC` exists so you can contrast — not replace
- [ ] Copy worksheets path: `mkdir -p ~/iiq-lab-data/connectors/mssql`
- [ ] Live SQL Server optional; worksheets + shell are the primary path

---

## Lab procedure

### Task 1 — Selection justification

Architecture reviews fail when Core Banking and Reporting share one connector story.

1. Write `~/iiq-lab-data/connectors/mssql/MNB-MSSQL-selection-65.md`:

| Question | Answer |
| --- | --- |
| Why Direct for reporting? | Native login/role model and Direct features |
| Why not convert Core Banking to MSSQL Direct? | Matrix prefers JDBC + procs for core app tables |
| Alternate if Direct type missing? | JDBC app `MNB-MSSQL-Reporting-JDBC` |

**Expected result:** Selection file with clear Core vs Reporting split.

### Task 2 — Connection and scope worksheet (lab-without-live-target)

You can finish enterprise design without connecting — production still needs every field below.

1. Complete:

| Item | Lab value |
| --- | --- |
| Host | `mnb-mssql-reporting.lab` |
| Instance / port | `MSSQLSERVER` / 1433 |
| Auth | Windows integrated **or** SQL login (pick one; note owner) |
| Aggregate account | `iiq_mssql_ro` |
| Provision account | `iiq_mssql_prov` (if ENABLE/PROVISIONING) |
| Databases in scope | `MNB_Reporting` only |
| Aggregate | SQL logins and/or DB users + roles |

2. Least privilege: **no sysadmin** for IIQ.
3. TLS + firewall bullets from Real-world setup.

**Expected result:** Worksheet section complete without a live connection.

**If it fails:** Mark auth mode TBD with DBA owner — do not invent domain details.

### Task 3 — Create Application MNB-MSSQL-Reporting

1. Applications → Add New → **Microsoft SQL Server - Direct** (or equivalent menu path).
2. Name: `MNB-MSSQL-Reporting`. Owner: Reporting / Technology (lab `spadmin`); IAM contact `helen.ross`.
3. Enter placeholders from the worksheet; skip live Test Connection if no instance.
4. Non-authoritative; create-identities **OFF**.
5. If type missing: notes shell + alternate JDBC app name `MNB-MSSQL-Reporting-JDBC`.

**Expected result:** Application or notes shell exists with Meridian naming.

### Task 4 — Schema, correlation, and disable plan

1. Native identity: SQL login name **or** DB user — **document the choice**.
2. Correlation: where login mirrors `jordan.reed`, map to `userName`; else use an extended property / employee table if DBA provides one.
3. Entitlements: database roles (e.g. `db_datareader`, `MNB_WIRE_REPORT`) marked managed.
4. Disable: disable login / revoke CONNECT — map to ENABLE if featuresString declares it.
5. Optional mock: `MNB-MSSQL-Reporting-mock.csv` with login,employeeId,roles,disabled for shadow aggregation practice.

**Expected result:** Schema plan in the selection file; mock optional but recommended.

### Task 5 — featuresString and test cases

1. Check ConnectorRegistry / glossary for PROVISIONING, ENABLE, PASSWORD, SEARCH.
2. Document tests:

| Test ID | Action | Expected result | If it fails |
| --- | --- | --- | --- |
| MSSQL-AGG-01 | Aggregate | Logins/roles in scope | Auth/driver/network |
| MSSQL-EN-01 | Disable lab login | Login disabled | ENABLE / rights |
| MSSQL-COR-01 | Correlate `jordan.reed` | Link on cube | Naming mismatch |
| MSSQL-PRIV-01 | Review IIQ SQL account | Not sysadmin | Reduce roles |
| MSSQL-TLS-01 | Connection encrypt | Encrypted session | Fix TLS before prod |

**Expected result:** ≥4 tests with Expected result / If it fails.

### Task 6 — Contrast paragraph vs JDBC provisioning

1. Write one paragraph: JDBC Lesson 64 updates `mnb_app_accounts` via SQL/procs; MSSQL Direct manages engine logins/roles. Both must not target the same core banking tables without Architecture approval.
2. Add residual risk `RR-MSSQL-SCOPE-01`: *Instance-wide aggregation would certify unrelated app logins — mitigate by database scope.*

**Expected result:** Contrast + residual risk in binder.

### Task 7 — Aggregation task naming and examiner card

1. Name task `Aggregate MNB-MSSQL-Reporting` (or `MNB-MSSQL-Reporting-Account-Aggregation`) in the runbook — nightly or weekly per size.
2. Examiner card answers: sysadmin? (No — show role list); Direct vs JDBC reason; disable evidence (plan + post-agg).
3. CHANGELOG: “Lesson 65 MSSQL Direct shell for reporting DB.”

**Expected result:** Runbook task name + examiner card + CHANGELOG.

### Task 8 — Peer challenge

Have a peer ask: *“Could we just point Core Banking JDBC at SQL Server and skip Direct?”* Answer using the matrix and object-model table from Concepts.

**Expected result:** Written Q&A in the selection file.

### Task 9 — Mock login inventory (optional Shadow)

When no SQL Server exists, still practice aggregation counts with a file that *looks* like Direct output.

1. Create `~/iiq-lab-data/connectors/mssql/MNB-MSSQL-Reporting-mock.csv`:

```csv
loginName,employeeId,email,dbRole,disabled
jordan.reed,MNB00092,jordan.reed@meridiannb.com,MNB_WIRE_REPORT,false
priya.wire,MNB00090,priya.wire@meridiannb.com,db_datareader,false
samir.hassan,MNB00094,samir.hassan@meridiannb.com,db_datareader,true
```

2. Optional Shadow DelimitedFile `MNB-MSSQL-Reporting-Shadow`; aggregate; label training-only.
3. Spot-check: Jordan holds reporting entitlement; Samir demonstrates disabled login semantics.

**Expected result:** Three-row mock ready; Shadow optional but documented if used.

---

## Acceptance criteria

- [ ] Selection justification vs JDBC Core Banking written
- [ ] Connection/scope/TLS/least-privilege worksheet done
- [ ] `MNB-MSSQL-Reporting` shell or notes (+ alternate if needed)
- [ ] Schema/correlation/disable plan + ≥4 tests
- [ ] JDBC contrast + `RR-MSSQL-SCOPE-01`
- [ ] Examiner card + CHANGELOG

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Type missing | IIQ edition/plugins | Use JDBC alternate; document |
| Login failed | Auth mode mismatch | Fix Windows vs SQL auth |
| Huge aggregate | Whole instance | Scope one database |
| sysadmin IIQ account | Over-privilege | Recreate least-priv logins |
| Duplicate of JDBC app | Scope creep | Keep Reporting vs Core split |
| Cleartext SQL | TLS not forced | Block prod promotion |

---

## Training binder evidence

- `MNB-MSSQL-selection-65.md` (worksheets, contrast, RR, examiner card)
- Application screenshot or shell notes (secrets redacted)
- Privilege statement (not sysadmin)
- Test matrix

**Examiner question:** *“Is the IdentityIQ SQL Server account a sysadmin? Show the role membership.”*

---

## Knowledge check

1. Preferred connector for SQL Server in the Meridian matrix?
2. Alternate connector?
3. What Application name does this lesson create?
4. Should this app replace `MNB-CoreBanking-JDBC`?
5. Can you complete acceptance without a live SQL Server?
6. What is the phase-1 database scope?

### Answers

1. Microsoft SQL Server - Direct.
2. JDBC.
3. `MNB-MSSQL-Reporting`.
4. No — Core Banking stays JDBC unless Architecture changes it.
5. Yes — worksheets and shell/notes suffice.
6. `MNB_Reporting` only.

---

## Further reading

- [Microsoft — Create a login](https://learn.microsoft.com/en-us/sql/relational-databases/security/authentication-access/create-a-login) — login vs user fundamentals for your schema plan.
- [Microsoft — Database-level roles](https://learn.microsoft.com/en-us/sql/relational-databases/security/authentication-access/database-level-roles) — what becomes entitlements.
- [Microsoft — Connect to SQL Server with encryption](https://learn.microsoft.com/en-us/sql/database-engine/configure-windows/configure-sql-server-encryption) — TLS expectations for bank networks.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “Microsoft SQL Server Direct” for connection and feature fields.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — MSSQL Direct aggregation and privilege troubleshooting.

---

## Stretch lab

Map Direct role names to entitlement dictionary risk tiers (`MNB_WIRE_REPORT` = critical). Draft Always Encrypted / column encryption notes for PII reporting columns. Premap Lesson 66 Oracle Direct differences (service name, Oracle roles vs MSSQL roles).

---

## Summary

- `MNB-MSSQL-Reporting` governs MSSQL logins/roles; JDBC remains correct for Core Banking app tables.
- Least privilege (no sysadmin), database scope, and TLS are examiner-facing design — not optional polish.
- Offline worksheets keep the database track moving when no SQL Server is in the lab.

---

**Previous:** [Lesson 64 — JDBC Provisioning Policies](64-jdbc-provisioning-policies.md)  
**Next:** [Lesson 66 — Oracle Database Direct Connector](66-oracle-db-direct-connector.md)
