# Lesson 66 — Oracle Database Direct Connector

**Level:** Intermediate  
**Track:** Connectors — Databases  
**Time:** 75–90 min  
**Prereq:** Lesson 65 — Microsoft SQL Server Direct Connector; Lesson 63 JDBC fundamentals  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (Oracle DB row)
- Repo: `lab-data/connectors/features-string-glossary.md`
- Repo: `lab-data/connectors/jdbc/mnb_core_accounts.sql` (schema reference if JDBC fallback)
- Runtime: `~/iiq-lab-data/connectors/`
- Optional live: Oracle listener via `docker-compose.connectors.yml` (if present)

---

## Learning objectives

You will be able to:

- Select **Oracle Database - Direct** vs JDBC for Meridian Oracle role governance using the selection matrix
- Create application shell **MNB-Oracle-GL** with schema, correlation, and featuresString notes—even without a live TNS listener
- Map Oracle users / roles (or grants) to IIQ account and entitlement attributes
- Document Test Connection, Account Aggregation, and provisioning feature expectations for DBAs
- Complete the **lab-without-live-target** path: app XML checklist, mock account CSV, and examiner Q&A card

---

## Why this matters

**Business.** Meridian’s Oracle GL and reporting schemas hold DBA and application accounts that can alter financial postings. IAM must inventory who holds `CONNECT`/`RESOURCE`-style roles and custom bank roles without waiting for a CSV dump from every DBA team.

**Control / audit.** Examiners ask: *Which connector governs Oracle DB privileged users, who owns Test Connection evidence, and how do you disable a terminated DBA account?* Direct connector configuration plus aggregation Task Results answer ownership and SLA.

---

## Concepts

**Oracle Database - Direct** is the IdentityIQ connector specialized for Oracle RDBMS accounts and database roles/privileges. Prefer it over generic JDBC when Meridian needs fine-grained DB role aggregation and native Oracle operations.

**JDBC alternate.** Use JDBC when you only need custom SQL against application tables (see Lessons 63–64), not Oracle system catalog users.

| Decision | Prefer Oracle Direct | Prefer JDBC |
| --- | --- | --- |
| Target | Oracle users / DB roles | App tables (`mnb_app_accounts`) |
| Provisioning | Native Oracle grants/users | SQL / stored procs you write |
| Meridian systems | Oracle GL, warehouse schemas | Custom bank apps on any RDBMS |

```
IIQ Application MNB-Oracle-GL
        │
        ▼
 Oracle Database - Direct connector
        │
        ├── Test Connection (TNS / JDBC URL + service account)
        ├── Account Aggregation → DB users + role entitlements
        └── Provisioning (if features enable) → create/modify/disable
```

**featuresString (review in Debug → ConnectorRegistry):** expect `PROVISIONING`, `ENABLE`, `PASSWORD`, `SEARCH`, `DISCOVER_SCHEMA` where licensed—confirm before promising Risk enable/disable SLAs.

**Lab-without-live-target.** You still create the Application object, schema map, correlation to `employeeId`/`email`, owner assignment, and a mock extract (`MNB-Oracle-GL-mock.csv`) so training completes on a laptop.

---

## Before you start

- [ ] IIQ at `http://localhost:8080/identityiq` (homelab URL only as alternate)
- [ ] `spadmin` access; Debug → Applications / ConnectorRegistry readable
- [ ] Copied `lab-data/connectors/` → `~/iiq-lab-data/connectors/`
- [ ] Matrix CSV open; locate **Oracle DB** row
- [ ] Know Meridian personas: `helen.ross` (IAM lead), `samir.hassan` (potential DBA proxy)

---

## Lab procedure

### Task 1 — Confirm connector choice from the matrix

1. Open `~/iiq-lab-data/connectors/connector-selection-matrix.csv`.
2. Find row: `Oracle DB` → preferred `Oracle Database - Direct`, alternate `JDBC`.
3. Write one sentence for the binder: *MNB Oracle GL uses Direct for native DB roles; JDBC only for app-table extracts.*

**Expected result:** Documented decision matching the matrix—not an ad-hoc DelimitedFile.

**If it fails:** Re-copy matrix from repo `lab-data/connectors/`.

### Task 2 — Inspect featuresString expectations

1. Debug → search **ConnectorRegistry** (or Application templates) for Oracle Database / Oracle Direct.
2. Note advertised features; cross-check `features-string-glossary.md`.
3. Record which of ENABLE / PASSWORD / PROVISIONING you will claim in the control owner card.

**Expected result:** Binder table: Feature | Present? | Meridian SLA note.

**If it fails:** Use glossary + product docs offline; mark features “confirm at install” rather than inventing UI labels.

### Task 3 — Create application shell MNB-Oracle-GL (live or dry-run)

1. Applications → Add New → **Oracle Database - Direct** (or equivalent menu path).
2. Name: `MNB-Oracle-GL`. Owner: `helen.ross` (IAM) with technical contact `samir.hassan`.
3. Enter connection placeholders: host/port/service name, service account (use vault/env—never commit secrets).
4. If **no live Oracle**: save with placeholders; do **not** run Test Connection yet—proceed to Task 4 lab-without-live-target.
5. If live: **Test Connection** → Success before schema discovery.

**Expected result:** Application object `MNB-Oracle-GL` exists with Meridian naming and ownership.

**If it fails:** Create from template Application XML export/import if wizard missing in lab build.

### Task 4 — Lab-without-live-target: schema + mock accounts

1. Define schema attributes (even if manually): `username` (native identity), `email`, `employeeId`, `status`, entitlement attr `dbRole`.
2. Create `~/iiq-lab-data/connectors/oracle/MNB-Oracle-GL-mock.csv` with headers and at least three rows, including `samir.hassan` / `samir.hassan@meridiannb.com` with role `ORA_GL_READ` and `priya.wire` with `ORA_GL_QUERY`.
3. Optionally attach a temporary DelimitedFile **shadow** app `MNB-Oracle-GL-Shadow` pointing at the mock CSV for aggregation practice when Direct cannot connect.
4. Document correlation: `employeeId` → Identity `employeeId`; fallback email `@meridiannb.com`.

**Expected result:** Mock file + schema map in binder; clear note “shadow app for training only.”

**If it fails:** Reuse column patterns from `jdbc/sample-rows.csv` and rename entitlements to `ORA_*`.

### Task 5 — Aggregation task definition

1. Create **Account Aggregation** task `MNB-Oracle-GL-Account-Aggregation` targeting `MNB-Oracle-GL` (or the Shadow app).
2. Run once if connectivity or shadow file exists; capture Task Result screenshot.
3. Spot-check cubes for linked accounts after correlation refresh.

**Expected result:** Task Result Success (live or shadow) with account count ≥ 3.

**If it fails:** Fix file path / filter; confirm application name on the task.

### Task 6 — Examiner Q&A card

Draft answers for:

1. Why Direct vs JDBC for Oracle GL?
2. Who owns connection credentials rotation?
3. What evidence shows a leaver’s Oracle account was disabled?

**Expected result:** One-page `MNB-Oracle-GL-Control-Card` in training binder.

---

## Acceptance criteria

- [ ] Matrix decision recorded for Oracle DB → Oracle Direct
- [ ] `MNB-Oracle-GL` application shell created with owner and schema map
- [ ] Lab-without-live-target mock CSV (and optional Shadow app) documented
- [ ] Account Aggregation task defined; Task Result captured if runnable
- [ ] Examiner Q&A control card complete; no secrets in git

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Test Connection fails | Wrong service name / TNS / firewall | Validate with DBA sqlplus; check listener; use Shadow path for training |
| Zero accounts | Filter too tight / wrong schema owner | Widen iterate SQL/filter; confirm service account SELECT grants |
| Roles missing as entitlements | Entitlement attribute not marked managed | Mark dbRole (or roles) as entitlement; re-aggregate |
| Shadow vs Direct confusion | Two apps without naming discipline | Suffix `-Shadow`; retire shadow before prod promotion |
| Password ops fail | PASSWORD feature / IQService not applicable | Oracle Direct password path differs from AD—confirm featuresString |

---

## Training binder evidence

- Matrix row screenshot + decision sentence
- Application `MNB-Oracle-GL` config (redact secrets)
- Mock CSV path + sample rows
- Account Aggregation Task Result
- `MNB-Oracle-GL-Control-Card` examiner answers

---

## Knowledge check

1. When does Meridian prefer Oracle Database Direct over JDBC?
2. What Meridian application name did you create for Oracle GL?
3. What is the lab-without-live-target substitute for a dead TNS listener?
4. Which glossary features should you verify before promising disable SLA?
5. Who is a reasonable technical contact for Oracle GL in this lab?

### Answers

1. When governing Oracle DB users/roles natively rather than custom application tables.
2. `MNB-Oracle-GL`.
3. Schema map + mock CSV and optional DelimitedFile Shadow app for aggregation practice.
4. `ENABLE` / `PROVISIONING` (and related) via featuresString / ConnectorRegistry—not assumptions.
5. `samir.hassan` (with IAM owner `helen.ross`).

---

## Stretch lab

Add entitlement risk tiers for `ORA_GL_DBA` vs `ORA_GL_READ` in the dictionary; draft an SoD pair with Wire initiator roles for a future policy lesson. Do not activate SoD in production without Risk sign-off.

---

## Summary

- Oracle Direct is Meridian’s preferred connector for native Oracle DB role governance.
- Lab-without-live-target still delivers app shell, schema, mock aggregation, and control evidence.
- `MNB-Oracle-GL` ownership and aggregation Task Results are examiner-facing artifacts.

---

**Previous:** [Lesson 65 — Microsoft SQL Server Direct Connector](65-mssql-direct-connector.md)  
**Next:** [Lesson 67 — SQLLoader Bulk Patterns](67-sqlloader-bulk-patterns.md)
