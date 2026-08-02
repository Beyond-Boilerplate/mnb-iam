# Lesson 55 — Provisioning Feature Matrix

**Level:** Intermediate  
**Track:** Connectors  
**Time:** 75–90 min  
**Prereq:** Lessons 51–54; `features-string-glossary.md` + selection matrix  

**Lab data:**
- Repo: `lab-data/connectors/features-string-glossary.md`
- Repo: `lab-data/connectors/connector-selection-matrix.csv`
- Runtime: `~/iiq-lab-data/connectors/`

---

> **Verify:** Paperwork — provisioning feature matrix and test cases. Academy **Verify now** is disabled; mark the binder complete when the matrix is signed off.

## Learning objectives

You will be able to:

- Read a connector’s `featuresString` and translate each flag into a concrete JML capability
- Build Meridian’s provisioning feature matrix for eight applications with evidence-backed Y / N / Unknown
- Write test cases (Expected result / If it fails) for ENABLE, PASSWORD, UNLOCK, and CRUD before any connector build
- Align leaver disable scope to apps where ENABLE is proven — not assumed
- Hand Risk a signed capability matrix that survives examiner comparison to IdentityRequest outcomes

---

## Why this matters

**Business.** Last year Meridian’s joiner playbook promised “disable every account within one hour of termination.” The Wire Portal SCIM path could flip `active=false`, but the helpdesk catalog still offered **Unlock** for a SaaS product that never declared `UNLOCK`. When `samir.hassan` left Commercial Lending, ops burned ninety minutes retrying unlocks that could never succeed — and meanwhile his wire entitlements stayed live until someone noticed. Impossible promises are worse than honest gaps.

**Control / audit.** Examiners compare the leaver control statement to what IdentityIQ can actually do. The feature matrix is the contract: *these apps have ENABLE; those are inventory-only.* Without it, every failed IdentityRequest looks like a connector bug when it is often a configuration lie.

---

## Concepts

### What `featuresString` actually means

IdentityIQ connectors advertise capabilities as a space-delimited **`featuresString`** on the connector registry entry (Debug → `ConnectorRegistry`). The glossary in `features-string-glossary.md` is your dictionary; the registry is the source of truth for *this* build.

| Feature | Plain English | JML / ops use at Meridian |
| --- | --- | --- |
| `PROVISIONING` | Connector can create / modify / delete accounts | Joiner create, entitlement grant/revoke |
| `SYNC_PROVISIONING` | Plan can execute synchronously | Wire apps when Risk wants immediate confirm |
| `ENABLE` | Enable / disable account | Leaver disable SLA |
| `PASSWORD` | Password set / change | Helpdesk reset (AD needs IQService) |
| `UNLOCK` | Unlock locked accounts | Helpdesk unlock catalog |
| `CURRENT_PASSWORD` | Change requires old password | Self-service policy constraint |
| `SEARCH` | Random-access get by native id | Single-account refresh |
| `NO_RANDOM_ACCESS` | Iterate-only | Typical delimited / bulk inventory |

The naive mistake: marking every cell **Y** because “IIQ provisions everything.” At a bank under exam, a false Y becomes a finding the moment disable fails and your matrix said it should work.

### Features vs policies vs promises

Three different layers get confused:

1. **Feature** — the connector *can* do the operation (registry).
2. **Policy** — you *configured* create/disable SQL, AD enable, SCIM PATCH, etc.
3. **Promise** — Risk / runbooks *obligate* Meridian to do it within an SLA.

All three must align. Feature without policy = green Test Connection, red IdentityRequest. Policy without feature = you wrote SQL the connector never calls. Promise without either = examiner finding.

### Meridian application set (this lesson)

| Application | Type (matrix / track) | Why it is on the matrix |
| --- | --- | --- |
| `MNB-HR` | DelimitedFile (authoritative) | Inbound truth — not a disable target |
| `MNB-IT-Access` | DelimitedFile | Inventory / birthright evidence |
| `MNB-ActiveDirectory` | AD Direct | Primary ENABLE / PASSWORD / UNLOCK |
| `MNB-OpenLDAP` | OpenLDAP Direct | Directory alternate |
| `MNB-CoreBanking-JDBC` | JDBC | Status-based ENABLE via SQL/procs |
| `MNB-WirePortal-WS` | Web Services | API-dependent features |
| `MNB-EntraID` | Azure AD | Cloud directory disable |
| `MNB-MSSQL-Reporting` | MSSQL Direct | Login disable / roles |

```
  ConnectorRegistry featuresString
        │
        ▼
  Meridian capability matrix (this lesson)
        │
        ├── provisioning policies (Lessons 64+)
        ├── helpdesk catalog (PASSWORD / UNLOCK only where Y)
        └── leaver SLA scope (ENABLE only where Y)
```

---

## How it works

When a provisioning plan includes Disable, IIQ checks whether the Application’s connector supports `ENABLE`, then routes through the connector’s enable/disable implementation (AD attribute, JDBC status SQL, SCIM `active`, etc.). If the feature is absent, the plan fails or no-ops depending on configuration — either way, your matrix should have predicted it.

```
IdentityRequest / LCM plan
        │  operation: Disable / Password / Unlock
        ▼
Application (features from connector type)
        │
        ├── feature present? ──No──► configuration defect (wrong promise)
        │
        └── Yes → connector adapter → target system
                      │
                      └── success/fail → Task Result / IdentityRequest
```

| Matrix cell | Meaning for Meridian |
| --- | --- |
| **Y** | Registry (or proven API) supports it; policy will be built |
| **N** | Do not promise; remove from helpdesk / leaver scope |
| **Unknown** | Confirm in build lesson; do not sign as Y yet |

---

## Real-world setup (outside IIQ)

This lesson produces a governance artifact, not a live connector. Still, production teams do the following before signing the matrix.

### Step 1 — Pull registry evidence

1. In each non-prod IIQ, open Debug → `ConnectorRegistry` (or Application template) for every type on the selection matrix.
2. Copy the literal `featuresString` into a worksheet — do not rely on memory from a different version.

### Step 2 — Confirm target-side prerequisites

1. AD `PASSWORD` / `UNLOCK` / `ENABLE` require IQService, TLS, and a service account with rights (Lesson 53).
2. JDBC `ENABLE` requires DBA-owned disable SQL or stored proc (Lesson 64) — the feature alone is not enough.
3. Web Services / SCIM features are only as real as the OpenAPI / SCIM `active` support — read the contract first (Lessons 68–69).

### Step 3 — Risk workshop

1. Walk the matrix with Risk and app owners: every Y becomes an SLA candidate; every N gets an alternate control (ticket, vault, manual).
2. Record decisions under change control — the matrix is a controlled document, not a wiki scratchpad.

### Step 4 — Publish to ops

1. Helpdesk catalog lists PASSWORD/UNLOCK only where Y.
2. Leaver runbook lists ENABLE targets only where Y.
3. Triage rule: failed disable → check matrix before filing a connector defect.

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq` as `spadmin` (Debug access helpful)
- [ ] Glossary + selection matrix copied to `~/iiq-lab-data/connectors/`
- [ ] Lesson 51–52 worksheets available; personas `priya.wire`, `marcus.approve`, `samir.hassan` known
- [ ] Binder folder ready for CSV + test markdown

---

## Lab procedure

### Task 1 — Build the empty Meridian feature matrix

Every production connector program starts with an empty contract so optimism cannot invent capabilities mid-build.

1. Create `~/iiq-lab-data/connectors/MNB-provisioning-feature-matrix-55.csv` with header:

```text
application,type,PROVISIONING,ENABLE,PASSWORD,UNLOCK,SYNC_PROVISIONING,notes
```

2. Add rows for: `MNB-HR`, `MNB-IT-Access`, `MNB-ActiveDirectory`, `MNB-OpenLDAP`, `MNB-CoreBanking-JDBC`, `MNB-WirePortal-WS`, `MNB-EntraID`, `MNB-MSSQL-Reporting`.

**Expected result:** CSV with eight application rows; values still blank.

**If it fails:** Re-copy glossary/matrix from `lab-data/connectors/`.

### Task 2 — Fill from registry and glossary (evidence, not hope)

You are building the contract Risk will sign. False Y cells become future findings.

1. For each row, mark `Y` / `N` / `Unknown` using the glossary, Lesson 51 notes, and ConnectorRegistry when available.
2. Use these training defaults (adjust if your registry differs):

| Application | PROVISIONING | ENABLE | PASSWORD | UNLOCK | Notes |
| --- | --- | --- | --- | --- | --- |
| `MNB-HR` | N | N | N | N | Authoritative inbound |
| `MNB-IT-Access` | Limited/file | N | N | N | Inventory |
| `MNB-ActiveDirectory` | Y | Y | Y | Y | PASSWORD/UNLOCK need IQService |
| `MNB-OpenLDAP` | Y typical | Y typical | Sometimes | Rare | Confirm registry |
| `MNB-CoreBanking-JDBC` | Y | Y via status | Rare | Rare | Lesson 64 procs |
| `MNB-WirePortal-WS` | If API | If API `active` | If API | If API | Confirm OpenAPI in L68 |
| `MNB-EntraID` | Y | Y | IdP-dependent | Rare | Cloud disable |
| `MNB-MSSQL-Reporting` | Y | Y login disable | Sometimes | Rare | Not sysadmin account |

3. Leave **Unknown** where API/OpenAPI is unread — Lesson 68 refines Wire Portal.

**Expected result:** Matrix filled; every Unknown has note “confirm in build.”

**If it fails:** Prefer Unknown over inventing Y.

### Task 3 — Write test cases with Expected result / If it fails

These cases become the QA script for connector build lessons. Design-only is fine when the target is not live yet.

1. For `MNB-ActiveDirectory`:

| Test ID | Operation | Persona | Expected result | If it fails |
| --- | --- | --- | --- | --- |
| AD-EN-01 | Disable | `samir.hassan` | Account disabled / plan success | IQService + ENABLE feature |
| AD-PW-01 | Password set | lab only | Password op succeeds | TLS / IQService / rights |
| AD-UN-01 | Unlock | lab only | Unlock succeeds | Feature missing → remove from helpdesk |

2. For `MNB-CoreBanking-JDBC`:

| Test ID | Operation | Expected result | If it fails |
| --- | --- | --- | --- |
| JDBC-EN-01 | Set status DISABLED | Row status updated | Fix ENABLE SQL/proc (L64) |
| JDBC-CR-01 | Create account | New `mnb_app_accounts` row | PROVISIONING + URL/SQL |

3. Store as `~/iiq-lab-data/connectors/MNB-feature-tests-55.md` (≥5 cases).

**Expected result:** Test file with Expected result and If it fails on every row.

### Task 4 — Align leaver control to the matrix

Leaver SLAs only bind where ENABLE is Y. Everything else needs an alternate control.

1. Draft:

> Meridian leaver disable is mandatory on applications where ENABLE=Y. File inventory apps are evidence sources, not disable targets.

2. Split apps into **in scope** (e.g. AD, Entra, Core Banking JDBC, MSSQL Reporting when ENABLE=Y) vs **out of scope** (HR, IT-Access file inventory).
3. For out-of-scope apps, name the alternate (ticket to app owner, vault disable, etc.).

**Expected result:** Two lists + alternate-control notes in the binder.

### Task 5 — SYNC_PROVISIONING decision

Synchronous provisioning is a product feature and an operational choice — not automatically “better.”

1. For each Y on `SYNC_PROVISIONING`, note whether Meridian *requires* sync (wire dual-control apps may; large AD often uses async + retry).
2. Default policy paragraph: *async + retry unless Risk requires sync for that application.*

**Expected result:** One-paragraph sync policy in the tests file.

### Task 6 — Map features to IdentityRequest triage

When disable fails at 02:00, the first question is not “restart IQService” — it is “did we promise ENABLE?”

1. Write triage rule: *Failed disable IdentityRequest → open matrix row → if ENABLE≠Y, close as configuration defect (wrong promise), not connector bug.*
2. Add: if ENABLE=Y, proceed to Lesson 47-style connector troubleshooting.

**Expected result:** Triage rule written and peer-readable.

### Task 7 — Risk review simulation and CHANGELOG

1. Present the matrix to a peer (or rigorous self-review). Challenge any Y without registry/API evidence — downgrade to Unknown.
2. Sign-off line: reviewer, date, “fit for connector build planning.”
3. CHANGELOG: “Lesson 55 provisioning feature matrix drafted for Meridian app set.”

**Expected result:** Sign-off + CHANGELOG entry.

### Task 8 — Examiner question drill

*“Which applications are you obligated to disable on termination, and what feature proves IIQ can do it?”*

Write the answer: point to ENABLE=Y rows, cite glossary definition of ENABLE, and attach one sample test ID (e.g. AD-EN-01 / JDBC-EN-01).

**Expected result:** Written examiner answer in the binder.

---

## Acceptance criteria

- [ ] Feature matrix CSV created for ≥8 apps
- [ ] Values justified from glossary/registry (Unknown OK; false Y not OK)
- [ ] ≥5 test cases with Expected result / If it fails
- [ ] Leaver in-scope / out-of-scope lists + alternate controls
- [ ] Sync policy paragraph + IdentityRequest triage rule
- [ ] Risk sign-off simulation + CHANGELOG + examiner answer

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Everything marked Y | Optimism | Re-read glossary; downgrade |
| File app PASSWORD=Y | Misunderstanding | Set N |
| No IQService note on AD PASSWORD | Incomplete | Add dependency in notes column |
| Tests require live AD | Scope creep | Design-only tests accepted this lesson |
| Matrix diverges from Lesson 52 | Drift | Align types to selection records |
| Wire Portal all Y | OpenAPI unread | Mark Unknown until Lesson 68 |

---

## Training binder evidence

- `MNB-provisioning-feature-matrix-55.csv`
- `MNB-feature-tests-55.md` (tests, sync policy, triage rule)
- Leaver in-scope / out-of-scope lists
- Risk sign-off line + examiner answer

**Examiner question:** *“Which applications are you obligated to disable on termination, and what feature proves IIQ can do it?”*

---

## Knowledge check

1. Which feature supports account disable on leaver?
2. Why is `MNB-HR` typically not a PASSWORD target?
3. What must accompany every PASSWORD=Y for Active Directory?
4. What does `SYNC_PROVISIONING` imply?
5. Is Unknown acceptable in the matrix?
6. If disable fails and ENABLE=N on the matrix, is that a connector bug?

### Answers

1. `ENABLE` (with a configured provisioning path).
2. HR is authoritative inbound identity truth, not a password-management target.
3. IQService architecture (TLS, rights) per Lesson 53.
4. The connector can execute provisioning synchronously when the plan runs.
5. Yes — prefer Unknown over a false Y until registry/API confirms.
6. No — it is a configuration / promise defect; fix the matrix and runbook first.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “connector features” / Application configuration for version-specific `featuresString` behavior.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — real threads on ENABLE/PASSWORD failures vs missing features.
- Repo glossary: `lab-data/connectors/features-string-glossary.md` — Meridian’s quick reference for matrix cells.
- [NIST SP 800-53 AC-2 (Account Management)](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) — control language examiners map to joiner/leaver disable evidence.
- [FFIEC Information Security booklet](https://www.ffiec.gov/press/pr110625.htm) — search current FFIEC IT Handbook “Information Security” for access termination expectations (use the live FFIEC handbook index if the press URL moves).

---

## Stretch lab

Add an `AUTHENTICATE` column and mark pass-through candidates. Cross-walk the matrix to Lesson 47’s provisioning troubleshooting playbook. Build a helpdesk catalog CSV that lists UNLOCK only where UNLOCK=Y — then delete any unlock runbook steps for Wire Portal until Lesson 68 proves the API.

---

## Summary

- Feature matrices prevent impossible JML promises; every Y needs registry or API evidence.
- ENABLE scope drives leaver SLAs; PASSWORD/UNLOCK drive helpdesk catalogs; Unknown is honest.
- Test cases with Expected result / If it fails become the build QA script for Lessons 56+.

---

**Previous:** [Lesson 54 — Aggregation Patterns Advanced](54-aggregation-patterns-advanced.md)  
**Next:** [Lesson 56 — Active Directory Connector](56-active-directory-connector.md)
