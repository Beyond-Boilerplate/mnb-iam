# Lesson 66 — Oracle Database Direct Connector

**Level:** Intermediate  
**Track:** Connectors — Databases  
**Time:** 90–120 min  
**Prereq:** Lesson 65 — Microsoft SQL Server Direct Connector; Lesson 63 JDBC fundamentals  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (Oracle DB row)
- Repo: `lab-data/connectors/features-string-glossary.md`
- Repo: `lab-data/connectors/jdbc/sample-rows.csv` (persona patterns)
- Runtime: `~/iiq-lab-data/connectors/oracle/`

---

## Learning objectives

You will be able to:

- Select **Oracle Database - Direct** vs JDBC for Meridian Oracle GL role governance using the selection matrix
- Perform real-world TNS / service account / least-privilege setup steps a DBA would recognize
- Create application shell **MNB-Oracle-GL** with schema, correlation, and featuresString notes
- Map Oracle users and roles (or grants) to IIQ account and entitlement attributes
- Complete lab-without-live-target: mock CSV, optional Shadow app, aggregation task, and examiner control card

---

## Why this matters

**Business.** Meridian’s Oracle General Ledger holds accounts that can post or query financials. When a contractor like `raj.external` inherits an `ORA_GL_POST` grant from a shared DBA script, nobody sees it until quarter-end. IAM must inventory Oracle users and roles continuously — not wait for a CSV dump from every DBA team.

**Control / audit.** Examiners ask: *Which connector governs Oracle DB privileged users, who owns Test Connection evidence, and how do you disable a terminated DBA account?* Direct connector configuration, aggregation Task Results, and a disable storyboard answer ownership and SLA.

---

## Concepts

### Oracle Direct vs JDBC (again — different catalog)

| Decision | Prefer Oracle Direct | Prefer JDBC |
| --- | --- | --- |
| Target | Oracle **users** / **DB roles** / privileges | App tables (`mnb_app_accounts`) |
| Provisioning | Native Oracle user/grant operations | SQL / stored procs you write |
| Meridian systems | Oracle GL, warehouse schemas | Custom bank apps on any RDBMS |

Matrix row: **Oracle DB → Oracle Database - Direct**, alternate **JDBC**.

### Users, roles, and profiles

- **Database user** — the account IdentityIQ usually treats as the Link native identity (`USERNAME`).
- **Role** — grantable entitlement (`ORA_GL_READ`, `ORA_GL_POST`, `ORA_GL_DBA`).
- **Profile / account status** — OPEN, LOCKED, EXPIRED — maps to enable/disable semantics when the connector supports ENABLE.

Naive approach: dump `DBA_USERS` into a spreadsheet monthly. Under exam, that fails freshness and ownership tests. Direct aggregation with Task Results is the continuous control.

### Suspend pattern for databases

Banks rarely `DROP USER` on day one. Prefer **lock / expire / revoke sensitive roles**, then drop on a retention schedule after legal-hold check — same philosophy as Google suspend-first (Lesson 74), adapted to Oracle.

```
IIQ Application MNB-Oracle-GL
        │
        ▼
 Oracle Database - Direct
        │
        ├── Test Connection (service name + least-priv account)
        ├── Account Aggregation → DB users + role entitlements
        └── Provisioning → create / grant / lock (if features allow)
```

---

## How it works

The Oracle Database Direct connector uses Oracle connectivity (service name / TNS / JDBC URL form per build) and Oracle catalog semantics to iterate users and roles. It is not “JDBC with different branding” when you need native role operations — though JDBC remains the escape hatch for custom SQL extracts.

```
IdentityIQ (MNB-Oracle-GL)
        │  host:port / service name / wallet or user+pass
        ▼
Oracle Database - Direct connector
        ├── users.list-style iterate → accounts
        ├── role grants → entitlements
        ├── lock / alter user → ENABLE
        └── grants/revokes → entitlement provisioning
```

| Operation | Oracle-side idea | IIQ evidence |
| --- | --- | --- |
| Test Connection | Auth to service | Success screenshot |
| Account aggregation | Users in scope (non-Oracle-maintained filter as designed) | Task Result |
| Entitlements | Roles granted | ManagedAttributes |
| Disable | `ACCOUNT LOCK` / revoke CONNECT-equivalent | Plan + re-agg |

Confirm `featuresString` (`PROVISIONING`, `ENABLE`, `PASSWORD`, `SEARCH`, `DISCOVER_SCHEMA`) in ConnectorRegistry before Risk SLAs.

---

## Real-world setup (outside IIQ)

`docker-compose.connectors.yml` does **not** ship Oracle. Execute these steps with a DBA on a real/dev CDB/PDB — or document them fully for the lab-without-live-target path.

### Step 1 — Connectivity

1. Obtain host, port (often 1521), **service name** (prefer service over SID for modern Oracle).
2. Confirm network path from IIQ servers; open firewall only for that listener.
3. Prefer wallet / TLS (`TCPS`) for non-lab; document java truststore needs.

### Step 2 — Service account

1. Create `IIQ_ORA_GL_RO` for aggregation with SELECT on the catalog views the connector requires (DBA documents the minimum — do not default to `DBA` role).
2. Separate `IIQ_ORA_GL_PROV` for provisioning with CREATE USER / GRANT privileges Risk approved.
3. Vault credentials; rotate on bank schedule; exclude from human cert campaigns (service inventory instead).

### Step 3 — Scope

1. PDB / schema scope: GL application users only — exclude `SYS`, `SYSTEM`, and Oracle-maintained noise unless Risk demands them in a separate privileged campaign.
2. Sensitive roles list: `ORA_GL_DBA`, `ORA_GL_POST`; read roles: `ORA_GL_READ`, `ORA_GL_QUERY`.

### Step 4 — Ownership

Application `MNB-Oracle-GL`; IAM owner `helen.ross`; technical contact `samir.hassan`.

---

## Before you start

- [ ] IIQ at `http://localhost:8080/identityiq` as `spadmin`; ConnectorRegistry readable
- [ ] Matrix CSV + glossary under `~/iiq-lab-data/connectors/`
- [ ] `mkdir -p ~/iiq-lab-data/connectors/oracle`
- [ ] Personas ready: `samir.hassan`, `priya.wire`, `helen.ross`
- [ ] Decide path: live Oracle listener **or** lab-without-live-target (Tasks 4–5)

---

## Lab procedure

### Task 1 — Confirm connector choice from the matrix

1. Open `~/iiq-lab-data/connectors/connector-selection-matrix.csv`.
2. Find: `Oracle DB` → preferred `Oracle Database - Direct`, alternate `JDBC`.
3. Binder sentence: *MNB Oracle GL uses Direct for native DB roles; JDBC only for app-table extracts.*

**Expected result:** Documented decision matching the matrix — not DelimitedFile-as-primary.

**If it fails:** Re-copy matrix from repo `lab-data/connectors/`.

### Task 2 — Inspect featuresString expectations

1. Debug → ConnectorRegistry / templates for Oracle Database Direct.
2. Cross-check `features-string-glossary.md`.
3. Build table: Feature | Present? | Meridian SLA note (especially ENABLE / PROVISIONING / PASSWORD).

**Expected result:** Feature table in binder; Unknown marked “confirm at install” if registry unavailable.

### Task 3 — Create application shell MNB-Oracle-GL

1. Applications → Add New → **Oracle Database - Direct** (or equivalent menu path).
2. Name: `MNB-Oracle-GL`. Owner: `helen.ross`; technical contact `samir.hassan`.
3. Enter connection placeholders: host/port/service name, service account (vault/env — never commit secrets).
4. Non-authoritative; create-identities **OFF**.
5. **Live:** Test Connection → Success before schema discovery. **No listener:** save placeholders; skip Test Connection; continue Task 4.

**Expected result:** Application object exists with Meridian naming and ownership.

**If it fails:** Application XML import from template if wizard missing in lab build.

### Task 4 — Lab-without-live-target: schema + mock accounts

Training still delivers aggregation muscle memory when TNS is dead.

1. Schema attributes: `username` (native identity), `email`, `userId`, `status`, entitlement `dbRole` (multi-valued if multiple roles).
2. Create `~/iiq-lab-data/connectors/oracle/MNB-Oracle-GL-mock.csv`:

```csv
username,email,employeeId,status,dbRole
samir.hassan,samir.hassan@meridiannb.com,MNB00094,ACTIVE,ORA_GL_READ
priya.wire,priya.wire@meridiannb.com,MNB00090,ACTIVE,ORA_GL_QUERY
jordan.reed,jordan.reed@meridiannb.com,MNB00092,LOCKED,ORA_GL_READ
raj.external,raj.external@meridiannb.com,MNB00093,ACTIVE,ORA_GL_POST
```

3. Optional Shadow DelimitedFile `MNB-Oracle-GL-Shadow` pointing at the CSV — training only.
4. Correlation: `employeeId` → Identity `employeeId`; fallback email `@meridiannb.com`.

**Expected result:** Mock file + schema map; clear “shadow for training only” note.

**If it fails:** Reuse patterns from `jdbc/sample-rows.csv`; rename entitlements to `ORA_*`.

### Task 5 — Account Aggregation task

1. Create **Account Aggregation** task `MNB-Oracle-GL-Account-Aggregation` targeting `MNB-Oracle-GL` or the Shadow app.
2. Run once if connectivity or shadow file exists; capture Task Result.
3. Spot-check: `raj.external` holds `ORA_GL_POST` (finding candidate); `jordan.reed` shows locked/disabled semantics if mapped.

**Expected result:** Task Result Success with account count ≥ 3 (live or shadow).

**If it fails:** Fix file path/delimiter; confirm application name on the task.

### Task 6 — Disable / lock storyboard

1. Sequence for terminated GL user: revoke `ORA_GL_POST` / `ORA_GL_DBA` → lock account → re-aggregate → evidence.
2. SLA: sensitive role revoke within 15 minutes of HR term (align Lesson 34); lock within 1 hour.
3. Drop user later per retention — outside immediate leaver SLA.

**Expected result:** Four-beat storyboard (revoke → lock → re-agg → retain/drop) in binder.

### Task 7 — Examiner Q&A control card

Draft `MNB-Oracle-GL-Control-Card`:

1. Why Direct vs JDBC for Oracle GL?
2. Who owns credential rotation (`helen.ross` / DBA / vault)?
3. What evidence shows a leaver’s Oracle account was locked and sensitive roles removed?

**Expected result:** One-page control card; no secrets in git.

### Task 8 — Residual risk and CHANGELOG

1. Record `RR-ORA-SYS-01`: *Oracle-maintained and shared schema accounts may need a separate privileged-access process outside standard user aggregation.*
2. CHANGELOG: “Lesson 66 Oracle Direct shell MNB-Oracle-GL.”

**Expected result:** RR logged + CHANGELOG.

### Task 9 — Contrast card vs MSSQL Direct (Lesson 65)

Write a five-row comparison so DBAs and IAM share vocabulary:

| Topic | `MNB-MSSQL-Reporting` | `MNB-Oracle-GL` |
| --- | --- | --- |
| Matrix preferred | SQL Server Direct | Oracle Database Direct |
| Native identity | Login / DB user | Oracle username |
| Entitlements | Server/DB roles | DB roles / grants |
| Disable primitive | Disable login / revoke CONNECT | LOCK / revoke roles |
| Lab live backend | None in compose | None in compose |

**Expected result:** Contrast card in binder; both apps remain non-authoritative.

---

## Acceptance criteria

- [ ] Matrix decision recorded for Oracle DB → Oracle Direct
- [ ] Real-world setup steps understood (service name, RO/prov split, TLS)
- [ ] `MNB-Oracle-GL` shell with owner and schema map
- [ ] Mock CSV (+ optional Shadow) and aggregation Task Result if runnable
- [ ] Lock storyboard + examiner control card + `RR-ORA-SYS-01`

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Test Connection fails | Wrong service name / TNS / firewall | Validate with sqlplus; use Shadow for training |
| Zero accounts | Filter too tight / grants missing | Widen filter; confirm SELECT grants |
| Roles missing as entitlements | Entitlement attr not managed | Mark `dbRole`; re-aggregate |
| Shadow vs Direct confusion | Two apps | Suffix `-Shadow`; retire before prod |
| Password ops fail | Feature / policy gap | Confirm featuresString; Oracle ≠ AD IQService |

---

## Training binder evidence

- Matrix row + decision sentence
- Application config (redact secrets)
- Mock CSV path + sample rows
- Aggregation Task Result
- Control card + lock storyboard + RR

---

## Knowledge check

1. When does Meridian prefer Oracle Database Direct over JDBC?
2. What Meridian application name did you create for Oracle GL?
3. What is the lab-without-live-target substitute for a dead listener?
4. Which features should you verify before promising disable SLA?
5. Who is a reasonable technical contact for Oracle GL in this lab?
6. Why revoke sensitive roles before locking?

### Answers

1. When governing Oracle DB users/roles natively rather than custom application tables.
2. `MNB-Oracle-GL`.
3. Schema map + mock CSV and optional DelimitedFile Shadow app.
4. `ENABLE` / `PROVISIONING` via featuresString — not assumptions.
5. `samir.hassan` (IAM owner `helen.ross`).
6. Defense in depth — role revoke kills powerful grants even if lock stalls; separate evidence.

---

## Further reading

- [Oracle — Creating a Database User](https://docs.oracle.com/en/database/oracle/oracle-database/19/dbseg/configuring-authentication.html) — user/auth concepts behind Direct accounts (version-adjust as needed).
- [Oracle — Configuring Privilege and Role Authorization](https://docs.oracle.com/en/database/oracle/oracle-database/19/dbseg/configuring-privilege-and-role-authorization.html) — roles as entitlements.
- [Oracle Net Services / easy connect](https://docs.oracle.com/en/database/oracle/oracle-database/19/netag/configuring-naming-methods.html) — service name vs SID for connection worksheets.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “Oracle Database Direct connector.”
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — Oracle Direct connection and role aggregation threads.

---

## Stretch lab

Add entitlement risk tiers for `ORA_GL_DBA` vs `ORA_GL_READ` in the dictionary. Draft an SoD pair: `ORA_GL_POST` vs Wire initiator roles for a future policy lesson — do not activate SoD in production without Risk sign-off. Compare MSSQL Lesson 65 disable (login disable) vs Oracle lock in a one-page table.

---

## Summary

- Oracle Direct is Meridian’s preferred connector for native Oracle DB role governance; JDBC stays for app-table SQL.
- Lab-without-live-target still delivers app shell, mock aggregation, lock storyboard, and control evidence.
- `MNB-Oracle-GL` ownership and Task Results are examiner-facing artifacts — not optional homework.

---

**Previous:** [Lesson 65 — Microsoft SQL Server Direct Connector](65-mssql-direct-connector.md)  
**Next:** [Lesson 67 — SQLLoader Bulk Patterns](67-sqlloader-bulk-patterns.md)
