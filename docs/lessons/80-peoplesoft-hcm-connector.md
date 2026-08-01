# Lesson 80 — PeopleSoft HCM Connector

**Level:** Intermediate  
**Track:** Connectors — ERP / HR / Banking  
**Time:** 90–120 min  
**Prereq:** Lesson 79 — SAP Direct Security; Lesson 77 — Workday HCM (authoritative-candidate pattern)  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (PeopleSoft row)
- Repo: `lab-data/connectors/features-string-glossary.md`
- Repo: `lab-data/connectors/jdbc/` (DB alternate patterns)
- Contrast: DelimitedFile `MNB-HR` from foundations

---

## Learning objectives

You will be able to:

- Select **PeopleSoft HCM Database** vs **PeopleSoft Direct** using Meridian's connector matrix and defend the choice
- Explain PeopleSoft HCM building blocks — EMPLID, job data, effective dating — and how Component Interfaces / Integration Broker fit connectivity
- Create **MNB-PeopleSoft-HCM** as an authoritative **candidate** (same discipline as Workday: do not flip both authoritative)
- Map EMPLID, job, status, and department into IIQ identity attributes with a bridge to Meridian `userId`
- Complete the lesson with mock/JDBC fallback when no PeopleSoft environment is available, and hand off cleanly to Lesson 81 (Oracle EBS)

---

## Why this matters

**Business.** Legacy Meridian entities may still run PeopleSoft HCM for HR and payroll long after corporate moves toward Workday. Those workers have **EMPLIDs**, job effective dates, and department IDs that never touch the Workday tenant. If IAM ignores PeopleSoft, joiners in that entity never enter the birthright pipeline — or someone dumps a spreadsheet into `MNB-HR` and hopes the formats match.

**Control / audit.** Examiners ask *which HCM system is authoritative per legal entity*. "We have Workday" is not an answer if a thrift subsidiary still runs PeopleSoft. Matrix-driven connector choice plus dual-run evidence (Lesson 77 pattern) prevent silent identity splits when two HCM feeds overlap.

---

## Concepts

### EMPLID is the person key — not Meridian `userId`

PeopleSoft identifies a person with **EMPLID**. Meridian cubes key on `userId` (`MNB#####`). Same bridge problem as SAP PERNR (Lesson 78): without `userId` ↔ `psEmplId`, correlation fails. Keep the native EMPLID on the identity forever; do not overwrite Meridian IDs with raw EMPLIDs.

| PeopleSoft concept | What it is | IAM use |
| --- | --- | --- |
| **EMPLID** | Person identifier | Native key → `psEmplId` + bridge |
| **JOB / Job Data** | Employment rows: dept, job code, supervisor, status | Department, title, manager, active/inactive |
| **EFFDT** | Effective date of a job row | Must select *current* effective-dated row |
| **HR_STATUS / EMPL_STATUS** | Active, leave, terminated, etc. | Map carefully — leave ≠ terminate (Sofia pattern) |
| **OPRID / User Profile** | PeopleSoft *application* login | Often a **target** account — not the HCM worker feed |

### Effective dating — the bug factories love

PeopleSoft job data is **effective-dated**: multiple rows per EMPLID across time. Aggregate "all JOB rows" and you invent duplicate accounts or thrash department attributes every night. Production designs use a **current effective-dated view** (as-of today, highest EFFDT / EFFSEQ rules per your PS version). Document that view name in the binder.

### Component Interfaces and Integration Broker

Two common enterprise integration surfaces:

- **Component Interface (CI):** a PeopleTools API over a component (e.g. PERSON / JOB). Connectors or custom integrations invoke CIs to read/write structured HCM data with PeopleSoft's business rules.
- **Integration Broker:** PeopleSoft's messaging framework (async/sync services) for publishing HR events or exposing services to external systems.

The SailPoint **PeopleSoft Direct** path typically leans on application-level integration (CI / related APIs depending on version). The **PeopleSoft HCM Database** path reads HR tables/views via **JDBC** — faster to stand up for read-only identity feed if DB access is allowed, with the trade-off that you bypass some Component Interface validations and must own SQL/view correctness.

| Option (matrix) | Typical use | Trade-off |
| --- | --- | --- |
| **PeopleSoft HCM Database** (preferred at Meridian) | Read current HR views via JDBC | You own the view; no PS UI license needed for read |
| **PeopleSoft - Direct** (alternate) | Application connector / CI-style path | Closer to PS security model; licensing/version sensitive |

```
PeopleSoft HCM
   ├── Database views (current JOB + PERSONAL) ──► MNB-PeopleSoft-HCM (preferred lab path)
   └── Direct / CI / Broker path                 ──► same app name if chosen; document why
            │
            ▼
   Identity attributes (NON-authoritative in lab unless directed)
```

### Authoritative-candidate pattern (copy Workday discipline)

`MNB-HR` remains lab authoritative. `MNB-Workday-HCM` is a corporate candidate (Lesson 77). `MNB-PeopleSoft-HCM` is a **legal-entity candidate**. Never enable authoritative create on PeopleSoft *and* HR/Workday for the same humans. Segment by company/`SETID`/population rule, or dual-run then flip one.

### HCM is not PeopleSoft security

PeopleSoft also has roles, permission lists, and user profiles for the PS application itself. Those are **out of scope** for `MNB-PeopleSoft-HCM`. If Meridian later governs PS application security, that is a separate application object — same split as SAP HR vs SAP Direct.

---

## How it works

```
IdentityIQ (MNB-PeopleSoft-HCM)
        │
        ├── Path A (preferred): JDBC to PS HR views
        │         SELECT current EMPLID, JOB, status, dept, manager…
        │
        └── Path B (alternate): PeopleSoft Direct / CI / Integration Broker
                  read PERSON / JOB via connector configuration
        ▼
Account or identity aggregation rows
        │  correlate via employeeId bridge
        ▼
Existing cubes (MNB-HR / future Workday) — create-identities OFF in lab
```

| Operation | PeopleSoft behavior | IIQ behavior |
| --- | --- | --- |
| Aggregation | Current effective-dated worker query or CI read | One row per EMPLID in scope |
| Correlation | Bridge EMPLID ↔ `userId` | Match corporate cubes |
| Status map | HR_STATUS / EMPL_STATUS (+ leave) | Active/inactive; leave as attribute |
| Manager | Supervisor ID on JOB | Resolve via EMPLID → identity after bridge |

**Matrix reminder:** preferred **PeopleSoft HCM Database**; alternate **PeopleSoft - Direct**. Lab uses Database-style mapping via mock/JDBC patterns; choose Direct only if licensed and architecture prefers CI/Broker.

---

## Real-world setup (outside IIQ)

### Step 1 — Choose the path and get access

1. Architecture decision recorded: HCM Database vs Direct (Task 1 will formalize).
2. **Database path:** DBA creates read-only DB user `iiq_ps_hr_ro` on the HR reporting database; grant SELECT only on agreed views (not write to PSPROD casually).
3. **Direct / CI path:** PeopleSoft admin exposes required Component Interfaces / service operations; Integration Broker nodes and authentication configured; network allow-list from IIQ.

### Step 2 — Current-effective view contract

1. HRIS + DBA publish view `MNB_IIQ_PS_WORKERS_CUR` (name example) selecting current JOB + personal fields: EMPLID, names, email, HR status, leave indicators, DEPTID, JOBCODE, SUPERVISOR_ID, company/SETID.
2. Document EFFDT logic in one paragraph — this is what auditors ask when department thrash appears.

### Step 3 — EMPLID bridge

1. Agree bridge source: HRIS crosswalk table or attribute sync from corporate directory.
2. Owner: `sofia.torres` (HRIS proxy); IAM owner: `helen.ross`.

### Step 4 — Governance records

Document: path choice, connect string location in vault (no secrets in binder), view name, bridge owner, authoritative stance (**candidate**), population (which company/SETID), residual risks.

---

## Before you start

- [ ] IIQ up; Workday dual-run / single-auth ideas from Lesson 77 fresh
- [ ] Matrix PeopleSoft row open; JDBC fixtures under `lab-data/connectors/jdbc/` available if using DB-style path
- [ ] Decide path: live PeopleSoft / JDBC lab DB, or mock CSV fallback
- [ ] Personas: `sofia.torres`, `kai.nguyen`, `nina.joiner`; owner `helen.ross`

---

## Lab procedure

### Task 1 — Matrix choice and naming

Every connector choice becomes tribal knowledge unless written down.

1. Record preferred: **PeopleSoft HCM Database**; alternate: **PeopleSoft Direct**.
2. Write Meridian decision: *Lab uses HCM Database-style mapping via mock/JDBC patterns; Direct only if the application connector is licensed and architecture prefers Component Interface / Integration Broker.*
3. Application name locked: `MNB-PeopleSoft-HCM`. Owner `helen.ross`; HR contact `sofia.torres`.

**Expected result:** Decision sentence + naming card in the binder.

### Task 2 — Create MNB-PeopleSoft-HCM

1. Applications → Add New → **PeopleSoft HCM Database** or **PeopleSoft** Direct per available template and Task 1 decision.
2. Connection placeholders:
   - Database path: JDBC URL, user `iiq_ps_hr_ro`, password `"in vault"`, schema/view hints
   - Direct path: PS connection / CI / Broker endpoints `"in vault"`
3. Save shell. Live path: **Test Connection**.

**Expected result:** Application object named `MNB-PeopleSoft-HCM`; live path shows Test Connection success.

**If it fails:** Wrong template (Direct vs DB) → revisit matrix and recreate from correct type. JDBC timeout → off-peak + filtered view. Build DelimitedFile/JDBC shadow labeled clearly for training if no PS environment.

### Task 3 — Schema map and bridge

1. `emplId` → `psEmplId` (always retain).
2. Bridge design: `userId,psEmplId` — same discipline as Workday Worker ID and SAP PERNR.
3. `userName` / OPRID strategy: document whether OPRID is correlated as an HCM attribute or deferred to a future PS **security** application (recommended: do not overload this HCM app with PS roles).
4. `hrStatus` / `emplStatus` → active/inactive; separate leave indicator if present.
5. `deptId`, `jobCode`, `managersAssociateID` (supervisor EMPLID) → identity attrs + manager resolution plan.
6. **Create identities: OFF** — authoritative candidate only.

**Expected result:** Schema/bridge map table; create-identities off; security scope boundary noted.

### Task 4 — Mock extract (fallback: no live PeopleSoft)

1. Create `~/iiq-lab-data/connectors/peoplesoft/MNB-PeopleSoft-HCM-mock.csv`:

```csv
emplId,userId,userName,email,hrStatus,exceptions (LOA),deptId,jobCode,managersAssociateID
PS10095,MNB00095,sofia.torres,sofia.torres@meridiannb.com,A,true,CML,RM01,PS10006
PS10096,MNB00096,kai.nguyen,kai.nguyen@meridiannb.com,A,false,IT,ENG01,PS10003
PS10120,MNB00120,nina.joiner,nina.joiner@meridiannb.com,A,false,RET,TEL01,PS10007
PS10999,MNB00999,ex.psworker,ex.psworker@meridiannb.com,I,false,RET,TEL01,PS10007
```

2. Optional: stage the same rows into a JDBC table using patterns under `lab-data/connectors/jdbc/` if your lab DB is up — still non-authoritative.
3. Read stories: Sofia active + on leave; Nina joiner; Kai IT; inactive row for leaver mapping tests.

**Expected result:** ≥3 active workers (+ inactive) ready to aggregate; leave vs terminate understood.

### Task 5 — Aggregation task (non-authoritative)

1. Create `MNB-PeopleSoft-HCM-Account-Aggregation`.
2. Run against live DB/Direct, JDBC staging, or DelimitedFile shadow.
3. Binder banner: **non-authoritative lab run — do not flip with MNB-HR / Workday both auth.**
4. Spot-check bridge fields on design: after correlation refresh, `psEmplId` should sit on cubes without creating duplicates.

**Expected result:** Task Result + non-auth note; Nina/Sofia/Kai spot-checks planned.

**If it fails:** Duplicate identities → authoritative flag mistake. EFFDT duplicates → view not current-only. EmplID collisions across entities → namespace by company/SETID in correlation.

### Task 6 — Coexistence and dual-run stub (Workday pattern)

Extend the Lesson 78 coexistence matrix:

| Source | Population | Authoritative? |
| --- | --- | --- |
| `MNB-HR` | Corporate lab | Yes (lab today) |
| `MNB-Workday-HCM` | Future corporate HCM | Candidate |
| `MNB-SAP-HR` | SAP HCM entities | Segmented / candidate |
| `MNB-PeopleSoft-HCM` | PeopleSoft legal entity | **Candidate — this lesson** |

1. Dual-run sample: reconcile 5 EMPLID/`userId` pairs vs `MNB-HR` (include `nina.joiner`, `sofia.torres`).
2. Cutover stub: Phase 1 parallel → Phase 2 fix deltas → Phase 3 flip **only** the PeopleSoft population's authoritative flag with rollback (disable PS auth; revert to CSV/HR).
3. Explicit warning: **do not flip PeopleSoft and Workday authoritative for overlapping people.**

**Expected result:** Updated coexistence matrix + dual-run stub with rollback.

### Task 7 — Security vs HCM scope boundary

1. Write: *PeopleSoft application security (roles, permission lists, OPRID entitlements) is out of scope for `MNB-PeopleSoft-HCM`. A future `MNB-PeopleSoft-Security` (name TBD) would own that — same pattern as Lessons 78–79.*
2. If mock data tempted you to add a `roles` column on this app, remove it — wrong object model.

**Expected result:** Scope boundary paragraph in the binder.

### Task 8 — Examiner Q&A and Lesson 81 handoff

1. Answer: *Which connector inventories PeopleSoft workers?* → `MNB-PeopleSoft-HCM`, preferred path PeopleSoft HCM Database per matrix.
2. Answer: *How do you avoid duplicate cubes during HCM modernization?* → single authoritative per population; dual-run; create-identities off on candidates.
3. Handoff: Next lesson moves to **Oracle E-Business Suite** responsibilities/security (`Lesson 81`) — another ERP target, not another HR authoritative feed unless explicitly designed.

**Expected result:** Q&A + handoff sentence in the binder.

### Task 9 — Residual risk

Record `RR-PS-EFFDT-01`: *Incorrect effective-date filtering duplicates workers or oscillates department/manager attributes. Compensating control: certified current-effective view owned by HRIS/DBA; aggregation tests on EFFDT boundaries.* Owner: `sofia.torres`.

Record `RR-PS-AUTH-01`: *Enabling authoritative on PeopleSoft while MNB-HR or Workday still authoritative for the same EMPLID/`userId` creates duplicate cubes. Compensating control: population segmentation + dual-run gate.* Owner: `helen.ross`.

**Expected result:** Both RRs logged with owners.

---

## Acceptance criteria

- [ ] Matrix HCM Database vs Direct decision recorded
- [ ] Real-world CI/Broker or JDBC setup understood; current-effective view contract noted
- [ ] `MNB-PeopleSoft-HCM` shell + schema/bridge map; create-identities off
- [ ] Mock (or live/JDBC) aggregation evidence with Sofia/Kai/Nina stories
- [ ] Coexistence matrix + dual-run stub; security scope boundary written
- [ ] Examiner Q&A, Lesson 81 handoff, `RR-PS-EFFDT-01` + `RR-PS-AUTH-01`

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| EMPLID collisions | Shared IDs across companies/SETIDs | Namespace correlation by company; segment populations |
| Department / manager thrash nightly | Multiple effective-dated JOB rows aggregated | Use current-effective view only (`RR-PS-EFFDT-01`) |
| JDBC timeout | Heavy PS queries / full history | Filter active employees; schedule off-peak; index views |
| Authoritative duplicates | PS + HR/Workday both auth | Segment or disable one auth flag immediately (`RR-PS-AUTH-01`) |
| Wrong template chosen | Direct vs Database mismatch | Revisit matrix; recreate app from correct connector type |
| Security roles mixed into HCM app | Overloaded object model | Split to future PS security application; remove role entitlements here |

---

## Training binder evidence

- Matrix decision + naming card
- Connection worksheet (path, view/CI — no secrets)
- Schema/bridge map + mock/live Task Result
- Coexistence matrix + dual-run stub with rollback
- Security scope boundary, examiner Q&A, Lesson 81 handoff, both RRs

---

## Knowledge check

1. What preferred PeopleSoft connector does the Meridian matrix list?
2. What is the Meridian PeopleSoft HCM application name?
3. Why bridge EMPLID to `userId`?
4. Should PeopleSoft security roles live on the HCM application?
5. Why must you not flip PeopleSoft and Workday authoritative together for the same people?
6. What lesson follows for Oracle E-Business Suite?

### Answers

1. PeopleSoft HCM Database (alternate PeopleSoft Direct).
2. `MNB-PeopleSoft-HCM`.
3. IIQ cubes and Meridian HR keys use `MNB#####` / `userId`; EMPLID is the PeopleSoft native key and must be bridged.
4. No — keep HCM worker data separate from PS application security (future separate app).
5. Two authoritative sources for one population create duplicate cubes and unexplained churn — use dual-run and population segmentation (Workday pattern).
6. Lesson 81 — Oracle EBS Connector.

---

## Further reading

- [Oracle PeopleSoft documentation](https://docs.oracle.com/en/applications/peoplesoft/) — landing page; search your Tools/HCM version for "Component Interface" and "Integration Broker" administration guides.
- [Oracle PeopleSoft HCM documentation](https://docs.oracle.com/en/applications/peoplesoft/) — search "job data" and "effective date" for the EFFDT behavior behind `RR-PS-EFFDT-01`.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search "PeopleSoft" for HCM Database vs Direct application guides and featuresString notes.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — JDBC view and PeopleSoft connector troubleshooting threads.
- [NIST SP 800-53 — AC-2 / IA-2](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — account management and identification controls that multi-HCM coexistence must still satisfy.
- [FFIEC IT Examination Handbook](https://ithandbook.ffiec.gov/) — search access control / information security for examiner expectations on authoritative identity sources.

---

## Stretch lab

Design a JDBC view SQL sketch (do **not** run against production PS) selecting current effective-dated JOB and PERSONAL_DATA-style fields aligned to Meridian lab schema naming (`userId`, `psEmplId`, `hrStatus`, `exceptions` (LOA), `deptId`, `jobCode`, `managersAssociateID`). Then add a SETID/company column to the coexistence matrix and propose the population rule that would allow PeopleSoft to become authoritative *only* for that entity while Workday owns corporate.

---

## Summary

- PeopleSoft HCM Database is Meridian's preferred worker inventory path; Direct/CI/Broker is the documented alternate — EMPLID, job data, and effective dating drive the schema.
- `MNB-PeopleSoft-HCM` is an authoritative candidate under the same dual-run discipline as Workday; never flip overlapping HCM feeds together.
- Keep PS application security out of this app; next stop is Oracle EBS (Lesson 81).

---

**Previous:** [Lesson 79 — SAP Direct Security](79-sap-direct-security.md)  
**Next:** [Lesson 81 — Oracle EBS Connector](81-oracle-ebs-connector.md)
