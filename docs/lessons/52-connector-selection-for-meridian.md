# Lesson 52 — Connector Selection for Meridian

| Field | Value |
| --- | --- |
| **Level** | Intermediate |
| **Track** | Connectors |
| **Time** | 60–75 minutes |
| **Prereq** | Lesson 51; `features-string-glossary.md` reviewed |
| **Lab data** | `~/iiq-lab-data/connectors/connector-selection-matrix.csv` |

## Learning objectives

You will be able to:

- Read and extend Meridian’s connector selection matrix CSV
- Map every Meridian system in the matrix to preferred and alternate connectors
- Justify AD Direct vs LDAP, JDBC vs MSSQL Direct, SCIM vs Web Services
- Produce a signed selection record for Risk / Architecture without a live target
- Flag IQService and stored-proc dependencies early

## Why this matters

Banks fail connector projects when Architecture picks “LDAP for everything” or “REST for everything.” Meridian’s matrix is the single source of preferred connectors: Corporate AD → Active Directory Direct, Core banking DB → JDBC (or MSSQL Direct), Wire Portal → Web Services.

**Control / audit:** Examiners ask who approved the connector type and whether an alternate was considered. Your completed matrix row is that evidence.

## Concepts

| System (matrix) | Preferred | Alternate | Meridian note |
| --- | --- | --- | --- |
| Corporate AD | Active Directory - Direct | LDAP | IQService for password/enable/Exchange |
| Entra ID | Azure Active Directory | SCIM 2.0 | Cloud directory + SaaS SSO |
| OpenLDAP | OpenLDAP - Direct | LDAP | Lab directory |
| HRIS extract | DelimitedFile | JDBC | Authoritative file still valid |
| Core banking DB | JDBC | MSSQL Direct | Prefer stored-proc provisioning |
| Wire Portal API | Web Services | SCIM 2.0 | Custom bank REST |
| SQL Server | Microsoft SQL Server - Direct | JDBC | Reporting DBs |
| Oracle DB | Oracle Database - Direct | JDBC | Fine-grained DB roles |

```text
  Business system inventory
        |
        v
  connector-selection-matrix.csv
        |
        +-- preferredConnector (build this)
        +-- alternate (fallback / PoC)
        +-- notes (IQService, procs, SCIM)
        |
        v
  Architecture sign-off → MNB-* Application build
```

## Before you start

- [ ] Lesson 51 worksheet available
- [ ] `~/iiq-lab-data/connectors/connector-selection-matrix.csv` present
- [ ] CHANGELOG open for selection decisions
- [ ] Know owners: IAM operates; app owners vary (Technology, Payments, HR)

## Lab procedure

### Task 1 — Load and validate the matrix

1. Inspect the CSV:

```bash
head -30 ~/iiq-lab-data/connectors/connector-selection-matrix.csv
wc -l ~/iiq-lab-data/connectors/connector-selection-matrix.csv
```

2. Confirm columns: `system`, `preferredConnector`, `alternate`, `notes`.
3. Count rows (≥20 expected including header).

**Expected result:** Header valid; systems include Corporate AD, Entra ID, Core banking DB, Wire Portal, SQL Server, Oracle DB, RACF, Okta, AWS IAM.

**If it fails:** Copy from `lab-data/connectors/connector-selection-matrix.csv`.

### Task 2 — Map Meridian MNB object names

1. For each matrix system, assign the intended `MNB-*` application name (create if not built yet):

| Matrix system | Intended Application |
| --- | --- |
| Corporate AD | `MNB-ActiveDirectory` |
| Entra ID / Azure AD | `MNB-EntraID` |
| OpenLDAP / FreeIPA | `MNB-OpenLDAP` |
| Core banking DB | `MNB-CoreBanking-JDBC` |
| Wire Portal API | `MNB-WirePortal-WS` |
| SQL Server | `MNB-MSSQL-Reporting` |
| Oracle DB | `MNB-OracleDB` (Lesson 66) |
| HRIS extract | `MNB-HR` (exists) |

2. Add three more from earlier curriculum: `MNB-IT-Access`, `MNB-SAP-Finance`, `MNB-AWS-Cloud` → preferred DelimitedFile or later native types per track.

**Expected result:** Mapping table with ≥8 `MNB-*` names.

### Task 3 — Deep-read dependency notes

1. For Corporate AD row, expand notes into a design bullet list: IQService host, TLS, password, Exchange yes/no.
2. For Core banking DB: document “prefer stored-proc provisioning” and why raw UPDATE is risky for bank DBs.
3. For Wire Portal: note OpenAPI fixture path `webservices/wire-portal-openapi.yaml` for later lessons.
4. For Privileged vault: CyberArk / PAM—flag as Advanced track (Lesson 86), not this sprint.

**Expected result:** Four annotated note blocks in notebook.

### Task 4 — Lab without live target — selection decision record

1. Create `~/iiq-lab-data/connectors/MNB-connector-selection-record-52.md` with:

```text
System: Corporate AD
Preferred: Active Directory - Direct
Alternate: LDAP
Rejected alternate because: LDAP lacks first-class IQService password/Exchange patterns Meridian requires
Owner: Technology / IAM operate
SLA: Disable within 4h of leaver HR event
Live target available now: NO
Build path: Application shell + checklist (Lesson 56)
```

2. Repeat for Core banking DB and Wire Portal API (three records minimum).
3. Mark `Live target available now: NO` where true—training still valid.

**Expected result:** Three decision records on disk; each names preferred, alternate, reject reason, SLA.

**If it fails:** Use CSV notes column as reject/accept rationale.

### Task 5 — Risk sign-off simulation

1. Role-play: Risk asks “Why not LDAP for AD?”
2. Answer from matrix + Lesson 51 features (PASSWORD/ENABLE via IQService path).
3. Record the Q&A in the binder as examiner rehearsal.

**Expected result:** One written Q&A paragraph.

### Task 6 — Update CHANGELOG

1. Add entry: “Lesson 52: Meridian connector selection matrix reviewed; MNB app name map created.”
2. Do not create live Application objects yet unless already exist.

**Expected result:** CHANGELOG line dated today.

## Acceptance criteria

- [ ] Matrix CSV validated (columns + key systems)
- [ ] ≥8 systems mapped to `MNB-*` names
- [ ] AD, Core banking, Wire Portal notes expanded
- [ ] Three lab-without-live-target decision records written
- [ ] Risk Q&A + CHANGELOG updated

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| CSV truncated | Bad copy | Re-copy from repo `lab-data/connectors/` |
| Duplicate MNB names | Naming collision | Follow Lesson 03; suffix `-JDBC` vs `-Direct` |
| Prefer SCIM vs WS unclear | Vendor capability unknown | Prefer SCIM when vendor supports; else Web Services |
| Skipping alternate column | Incomplete ADR | Always document alternate + reject reason |
| Building apps early | Scope creep | Shells start Lesson 56+; this lesson is selection only |

## Training binder evidence

- Printed or screenshot of matrix header + AD/Core banking/Wire rows
- `MNB-connector-selection-record-52.md`
- MNB name mapping table

**Examiner question:** “Show the approved connector type for Core Banking and the alternate you rejected.”

## Knowledge check

1. Preferred connector for Corporate AD at Meridian?
2. Why does the matrix list IQService in AD notes?
3. Preferred vs alternate for Core banking DB?
4. When do you prefer SCIM 2.0 over Web Services?
5. Is live AD required to complete this lesson’s acceptance criteria?

### Answers

1. Active Directory - Direct.
2. Password, enable/disable, and often Exchange mailbox ops depend on IQService near the domain.
3. Preferred JDBC; alternate Microsoft SQL Server - Direct; prefer stored-proc provisioning.
4. When the vendor exposes standards-compliant SCIM; otherwise map REST with Web Services.
5. No—lab-without-live-target decision records are sufficient.

## Stretch lab

- Add a matrix row for a fictional `MNB-MobileBanking` API and choose Web Services vs SCIM with justification.
- Cross-check every matrix preferred type against Lesson 51 feature promises for ENABLE/PASSWORD.
- Draft an Architecture Decision Record (ADR) one-pager referencing the CSV path.

## Summary

- Meridian’s `connector-selection-matrix.csv` is the system→connector contract.
- Every selection needs preferred, alternate, reject reason, owner, and SLA.
- Live targets are optional; decision records unlock later connector labs.

---

**Previous:** [Lesson 51 — Connector Landscape & Registry](51-connector-landscape-and-registry.md)  
**Next:** [Lesson 53 — IQService Architecture](53-iqservice-architecture.md)
