# Lesson 81 — Oracle E-Business Suite Connector

**Level:** Intermediate  
**Track:** Connectors — ERP / HR / Banking  
**Time:** 60–90 min  
**Prereq:** Lesson 80 — PeopleSoft HCM Connector  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv`
- Repo: `lab-data/connectors/features-string-glossary.md`
- Runtime notes: `~/iiq-lab-data/connectors/`

---

## Learning objectives

You will be able to:

- Place **Oracle E-Business Suite (EBS)** on Meridian’s connector selection matrix vs JDBC-only approaches
- Create Application shell `MNB-Oracle-EBS` with schema maps for users, responsibilities, and key flex attributes
- Document provisioning policies for create / disable / responsibility grant-revoke without a live EBS instance
- Design correlation to HR `employeeId` / `userName` for Meridian personas
- Produce an examiner-ready ownership and evidence packet for GL / AP / AR security

---

## Why this matters

**Business.** Meridian’s finance stack may include Oracle EBS for GL, AP, and purchasing alongside SAP Finance extracts. Access to EBS responsibilities (e.g., payables clerk, GL journal entry) is a material financial control.

**Control / audit.** Examiners ask who can post journals, approve invoices, and change suppliers—not only whether “Oracle” appears in a spreadsheet. IIQ must show aggregation, correlation, requestability, and disablement evidence for EBS accounts even when the bank runs a phased connector rollout.

---

## Concepts

**Oracle EBS in IIQ** typically uses an Oracle E-Business / ERP-style connector (or JDBC when only tables/views are exposed). Prefer the native EBS path when responsibilities and concurrent programs must be first-class entitlements.

| Meridian concern | IIQ object / design |
| --- | --- |
| Who owns EBS | Application owner `rachel.evans` (Finance Ops) + IT DBA control owner |
| Account key | EBS `USER_NAME` ↔ IIQ `userName` / `employeeId` |
| Entitlements | Responsibilities, menus, data access sets |
| Leaver | Disable FND user; revoke standing responsibilities |
| Lab path | App shell + policy forms + worksheet (no live DB required) |

```
HR cube (employeeId)
        │
        ▼
 Correlation ──► MNB-Oracle-EBS account (USER_NAME)
        │
        ▼
 Responsibilities (entitlements) ──► certs / SoD / LCM
```

**Lab-without-live-target:** Complete Application XML/UI shell, attribute maps, provisioning policy forms, and a connection worksheet. Do not invent live TNS credentials in git.

---

## Before you start

- [ ] IIQ at `http://localhost:8080/identityiq` (or homelab URL) healthy
- [ ] `~/iiq-lab-data/connectors/connector-selection-matrix.csv` present (copy from repo if needed)
- [ ] Skim matrix row for Oracle / ERP systems; note EBS vs `Oracle Database - Direct`
- [ ] Lesson 80 PeopleSoft shell or notes available for ERP pattern comparison
- [ ] Binder section: `connectors/oracle-ebs/`

---

## Lab procedure

### Task 1 — Confirm connector choice on the matrix

1. Open `~/iiq-lab-data/connectors/connector-selection-matrix.csv` (or repo `lab-data/connectors/connector-selection-matrix.csv`).
2. Locate Oracle Database vs any ERP notes; add a binder line: **EBS application security ≠ Oracle DB Direct roles**.
3. Write: Preferred path = Oracle E-Business connector (or approved Meridian standard); Alternate = JDBC to FND views if native connector blocked.
4. Read `features-string-glossary.md`; list features you expect: `PROVISIONING`, `ENABLE`, possibly `PASSWORD`.

**Expected result:** One-page decision note: when to use EBS connector vs JDBC vs Delimited extract.

**If it fails:** Use matrix + glossary only; ask control owner which connector Meridian standardized.

---

### Task 2 — Create Application shell `MNB-Oracle-EBS`

1. Applications → Add New Application (or equivalent).
2. Select **Oracle E-Business** / EBS template if present; otherwise create placeholder Application named `MNB-Oracle-EBS` with connector type documented in Description.
3. Set Owner: `rachel.evans` (or `spadmin` temporarily with owner transfer note).
4. Mark **not authoritative**.
5. Save.

**Expected result:** Application `MNB-Oracle-EBS` listed; Description states lab-without-live-target.

**If it fails:** Naming must be exact `MNB-Oracle-EBS` for later lessons.

---

### Task 3 — Schema and entitlement model (offline)

1. Open Application → Schema (or Debug Application XML).
2. Define account attributes (document even if UI discovery fails):
   - `USER_NAME` (identity attribute / native identity)
   - `EMPLOYEE_NUMBER` / `EMAIL` if available
   - `START_DATE`, `END_DATE`, `STATUS`
3. Define entitlement type **Responsibility** (or group equivalent): name + description.
4. Map sample Meridian responsibilities for binder:
   - `MNB_AP_CLERK`
   - `MNB_GL_JOURNAL`
   - `MNB_PO_BUYER`
5. Document correlation: `EMPLOYEE_NUMBER` ↔ `employeeId`, fallback `USER_NAME` ↔ `userName`.

**Expected result:** Schema worksheet with account + responsibility attributes and correlation keys.

**If it fails:** Capture attributes in binder table; import later when schema discovery works.

---

### Task 4 — Provisioning policies (forms only)

1. Open Provisioning Policies for Create, Enable/Disable, Modify.
2. Create field stubs: `USER_NAME`, `EMAIL_ADDRESS`, `EMPLOYEE_NUMBER`, responsibility assignment field.
3. For Disable: document `END_DATE` / status inactive pattern Meridian will use on leaver.
4. Do **not** store real DB passwords in Application config in git-backed exports—use encrypted IIQ secrets or placeholder `***LAB***`.
5. Save policies; export Application XML to binder (redact secrets).

**Expected result:** Create/Disable/Modify policy forms saved; secrets redacted in evidence.

**If it fails:** Use Debug to attach empty Provisioning Policy objects named `MNB-Oracle-EBS-Create`, etc.

---

### Task 5 — Lab aggregation evidence path

1. If no live EBS: create Delimited File **proxy** extract `~/iiq-lab-data/apps/MNB-Oracle-EBS-proxy.csv` with columns `userName,employeeId,responsibility,status` and 3–5 rows (`helen.ross`, `samir.hassan`, `sofia.torres`).
2. Optionally create temporary Delimited app `MNB-Oracle-EBS-Proxy` **only** to practice Account Aggregation and correlation—label Description “proxy for EBS training.”
3. Run **Account Aggregation** on the proxy (or skip with written “blocked pending network” if policy forbids proxy apps).
4. Refresh identities if you aggregated; verify accounts on cubes.

**Expected result:** Either successful proxy aggregation evidence **or** signed blocker note with owner and date.

**If it fails:** Aggregation optional; Tasks 1–4 are mandatory for lesson completion.

---

### Task 6 — Control owner interview card

1. Draft five examiner questions:
   - Who approves EBS responsibility grants?
   - How is leaver disable proven?
   - Are DBAs using personal EBS apps accounts?
   - SoD: AP clerk vs supplier master?
   - Where is connection TLS / wallet documented?
2. Assign owners and SLA (e.g., grant approval 2 business days).

**Expected result:** Interview card in binder under `connectors/oracle-ebs/`.

---

## Acceptance criteria

- [ ] Matrix decision note distinguishes EBS vs Oracle DB Direct
- [ ] Application `MNB-Oracle-EBS` shell exists with owner and non-authoritative flag
- [ ] Schema + responsibility model documented
- [ ] Create/Disable provisioning policy stubs saved
- [ ] Lab-without-live-target path completed (proxy aggregate **or** blocker note)
- [ ] Control owner interview card written

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No EBS connector in UI | License / version / missing jar | Document alternate JDBC; escalate to platform team |
| Schema discovery empty | No live DB / wrong JDBC URL | Use offline schema worksheet |
| Correlation orphans | USER_NAME ≠ IIQ userName | Align to employeeId; BuildMap if extract dirty |
| Password in exported XML | Unencrypted config | Re-encrypt; scrub binder exports |
| Finance thinks JDBC = EBS | Wrong connector narrative | Re-brief with matrix row + this lesson |

---

## Training binder evidence

- Connector decision note (EBS vs JDBC vs extract)
- Application summary screenshot `MNB-Oracle-EBS`
- Schema / responsibility worksheet
- Redacted provisioning policy screenshots
- Proxy aggregation Task Result **or** blocker note
- Examiner interview card

---

## Knowledge check

1. Why is Oracle EBS not the same control surface as Oracle Database Direct?
2. What should be the primary correlation key for Meridian EBS users?
3. Name three sample Meridian responsibilities used in this lab.
4. What is the mandatory lab path when EBS is unreachable?
5. Who is the suggested application owner for `MNB-Oracle-EBS`?

### Answers

1. EBS governs application users/responsibilities; DB Direct governs database roles/privileges inside the RDBMS.  
2. `employeeId` / employee number, with `userName` as fallback.  
3. `MNB_AP_CLERK`, `MNB_GL_JOURNAL`, `MNB_PO_BUYER`.  
4. Complete app shell, schema maps, provisioning policy forms, and worksheet (optional CSV proxy).  
5. `rachel.evans` (Finance Ops), with IT/DBA as technical control owner.

---

## Stretch lab

Draft an SoD pair: `MNB_AP_CLERK` vs supplier master responsibility; map to `lab-data/reference/sod-matrix.csv` style row for Capstone.

---

## Summary

- EBS is an ERP application-security connector problem, not “just another database.”
- Meridian standardizes on named app `MNB-Oracle-EBS`, responsibility entitlements, and employeeId correlation.
- Training completes without live EBS via shell + policies + evidence worksheet.

---

**Previous:** [Lesson 80 — PeopleSoft HCM Connector](80-peoplesoft-hcm-connector.md)  
**Next:** [Lesson 82 — Mainframe RACF for Banking](82-mainframe-racf-banking.md)
