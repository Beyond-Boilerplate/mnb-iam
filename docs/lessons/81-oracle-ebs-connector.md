# Lesson 81 — Oracle E-Business Suite Connector

**Level:** Intermediate  
**Track:** Connectors — ERP / HR / Banking  
**Time:** 90–120 min  
**Prereq:** Lesson 80 — PeopleSoft HCM Connector; Lesson 12 (`MNB-SAP-Finance` SoD pattern) helpful  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv`
- Repo: `lab-data/connectors/features-string-glossary.md`
- Repo: `lab-data/apps/MNB-SAP-Finance.csv` (Lesson 12 SoD contrast)
- Runtime notes: `~/iiq-lab-data/connectors/`

---

## Learning objectives

You will be able to:

- Explain the Oracle E-Business Suite (EBS) security model — `FND_USER`, responsibilities, menus, and concurrent programs — and which of those become IIQ entitlements
- Distinguish the native Oracle E-Business connector from JDBC-to-FND-views and from Oracle Database Direct
- Perform the real-world setup: service account, least-privilege grants, JDBC/API connectivity, and network/TLS worksheet
- Create and configure **MNB-Oracle-EBS** field by field (schema, correlation, responsibility entitlements)
- Design create / disable / responsibility grant-revoke policies and a finance SoD pair in the Lesson 12 style
- Complete the lesson with or without a live EBS instance (mock fallback provided)

---

## Why this matters

**Business.** Meridian’s finance stack may run Oracle EBS for GL, AP, purchasing, and supplier master alongside the SAP Finance extract from Lesson 12. When `sofia.torres` still held `MNB_AP_CLERK` six months after moving to Marketing, she could still enter invoices — not because anyone intended it, but because EBS responsibilities are granted casually ("add her for month-end") and reviewed almost never. That is the same access-creep story as Google groups, except the blast radius is the general ledger.

**Control / audit.** Examiners do not ask whether “Oracle” appears in a spreadsheet. They ask who can post journals, approve invoices, change suppliers, and submit concurrent programs that rewrite master data — and they want aggregation Task Results, correlation evidence, and disablement proof. This lesson builds `MNB-Oracle-EBS` so those answers exist even when the bank rolls the connector out in phases.

---

## Concepts

### The EBS security object model

Before touching IIQ, understand what Oracle actually stores. EBS application security is **not** the same as Oracle Database roles. The objects that matter for governance:

| EBS object | What it is | Real-life example at Meridian |
| --- | --- | --- |
| **FND_USER** | The application user row (login identity for EBS forms/self-service) | `SOFIA.TORRES` linked to employee number `MNB00095` |
| **Responsibility** | A named bundle of menus + data groups + request groups — the primary grant | `MNB_AP_CLERK`, `MNB_GL_JOURNAL`, `MNB_PO_BUYER` |
| **Menu / function** | Navigation paths inside a responsibility | "Enter Invoices" under AP Clerk |
| **Data access set / security profile** | Row-level scope (which ledgers, orgs, inventory orgs) | Commercial Lending ledger only |
| **Concurrent program** | A batch job a user can submit (often more powerful than the UI) | Mass supplier update, GL post |

The critical distinction: **responsibilities grant access to do work; concurrent programs can rewrite the work at scale.** Teams that only certify responsibilities and ignore request-group / concurrent-program entitlements miss half the financial-control surface.

### Why responsibilities must be entitlements

In IIQ terms, an EBS responsibility membership behaves like an AD group or SAP role: discrete, grantable, revocable, and access-bearing. The connector should surface responsibilities as a **multi-valued entitlement attribute**, so each becomes a `ManagedAttribute` you can risk-rate, certify, put in SoD pairs, and revoke through a provisioning plan.

The naive alternative — treating "responsibilities" as a free-text attribute on the account — means no entitlement catalog, no certification line item, and no revoke button. When the examiner asks who reviewed `MNB_GL_JOURNAL` this year, you would have nothing.

### Concurrent programs are a residual risk unless modeled

Many EBS deployments expose concurrent programs only inside a responsibility’s request group. If your connector version can surface request-group / concurrent-program assignments as entitlements, do it for high-risk programs. If it cannot, document residual risk `RR-EBS-CP-01` and compensate with periodic DBA exports reviewed by Finance Ops — never pretend the responsibility cert alone covers mass-update jobs.

### EBS connector vs JDBC vs Oracle DB Direct

| Approach | What you see | When Meridian uses it |
| --- | --- | --- |
| **Oracle E-Business / ERP connector** | FND users, responsibilities, often enable/disable | Preferred — application security as first-class objects |
| **JDBC to FND views** | Whatever views/DBA expose | Alternate when native connector blocked; still model responsibilities as entitlements |
| **Oracle Database Direct** | RDBMS roles/privileges | Different control plane — DBAs, not AP clerks |

Saying “we have Oracle in IIQ” while only aggregating DB roles fails the finance exam. Application users live in `FND_USER`; database accounts are a separate story.

### Link to Lesson 12 finance SoD

Lesson 12 taught SoD on `MNB-SAP-Finance` (Jordan’s toxic pair). EBS needs the same discipline with different names: `MNB_AP_CLERK` vs supplier-master responsibility is the classic pair — enter invoices *and* create the payee. You will draft that pair in Task 8 using the same evidence mindset as Lesson 12.

---

## How it works

The SailPoint Oracle E-Business connector (or Meridian’s approved ERP template) typically reaches EBS through **JDBC to the apps schema / FND tables** and, in some deployments, through **Oracle APIs / concurrent-aware interfaces** for provisioning. Exact UI field labels vary by IIQ version — use your Application guide and say “or equivalent menu path.”

```
IdentityIQ (MNB-Oracle-EBS)
        │  JDBC URL + wallet/TLS + svc account
        │  (optional API / apps user for provisioning)
        ▼
Oracle EBS apps tier / DB
        ├── FND_USER (+ employee link)     → account aggregation
        ├── FND_USER_RESP_GROUPS (etc.)    → responsibility entitlements
        ├── END_DATE / status updates      → disable / leaver
        └── responsibility assign/revoke   → entitlement add / remove
```

| Operation | Target behavior | IIQ behavior |
| --- | --- | --- |
| Account aggregation | Read FND users in scope | One account per `USER_NAME`, native identity |
| Entitlement aggregation | Responsibilities assigned to users | Managed attributes + memberships on accounts |
| Provision create | Insert / API create FND user | New hire with employee number link |
| Disable | Set `END_DATE` / inactive status | Disable / ENABLE feature |
| Responsibility grant/revoke | Assign or end-date responsibility | Entitlement add / remove in provisioning plan |

Connectivity note: Meridian prefers **TLS to the listener**, credentials in the vault (never in git), and a **dedicated apps-read / limited-write service account** — not a DBA’s personal account. The connector is exactly as powerful as the grants on that account.

---

## Real-world setup (outside IIQ)

Read this even if you use the mock fallback — the knowledge check and the examiner both assume you know it.

### Step 1 — Decide connector path

1. Confirm with Platform + Finance Ops: native **Oracle E-Business** connector (preferred) vs JDBC-to-approved FND views (alternate).
2. Record the decision on the matrix row: EBS application security ≠ Oracle Database Direct.

### Step 2 — Service account and least privilege

1. Create `SVC_IIQ_EBS` (or equivalent) in EBS / DB as directed by the DBA standard — not a named human.
2. Phase 1 (aggregation): read-only grants on the FND user / responsibility views your connector requires.
3. Phase 2 (provisioning): add only the write packages/tables needed for create, end-date, and responsibility assign — each grant security-reviewed.
4. Vault the password; set rotation ≤90 days; deny interactive Forms login where possible.

### Step 3 — Network and TLS

1. IIQ task servers → EBS DB listener (or mid-tier API host) on the approved port; firewall ticket owned by Platform Ops.
2. Prefer Oracle wallet / TLS; document cipher and cert trust store location.
3. No production TNS credentials on lab laptops — lab uses placeholders.

### Step 4 — Governance records

Document: instance name (prod/nprod), connector type, service account, grant package version, phase 1/2 status, application owner `rachel.evans` (Finance Ops), technical owner (EBS DBA).

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq` as `spadmin`; PeopleSoft shell patterns from Lesson 80 clear
- [ ] `~/iiq-lab-data/connectors/connector-selection-matrix.csv` present (copy from repo if needed)
- [ ] Skim Lesson 12 SoD mindset (`MNB-SAP-Finance`); optional `lab-data/apps/MNB-SAP-Finance.csv`
- [ ] Decide your path: live EBS non-prod **or** mock fallback in Task 4
- [ ] No production DB passwords on lab machines or in git

---

## Lab procedure

### Task 1 — Design decisions and naming

Every production connector starts with a design card — renaming after certifications reference it is painful.

1. Application name: `MNB-Oracle-EBS`. Owner: `rachel.evans`; technical contact: EBS DBA / Platform.
2. Scope: GL / AP / PO users in the corporate apps instance; contractors included if they hold EBS logins (excluding them is a classic blind spot).
3. Entitlement strategy: **responsibilities = entitlements**; concurrent programs = entitlements if connector supports, else `RR-EBS-CP-01`.
4. Sensitive list for risk-rating: `MNB_AP_CLERK`, `MNB_GL_JOURNAL`, `MNB_PO_BUYER`, plus any supplier-master responsibility Meridian uses.

**Expected result:** Design card covering name, owners, scope, entitlement strategy, and sensitive responsibilities.

### Task 2 — Create the application (native primary)

In production this is where Step 2–3 outputs (JDBC URL, wallet, service account) get consumed.

1. Applications → Add New → **Oracle E-Business** / EBS template (or equivalent menu path). If the template is missing, create Application `MNB-Oracle-EBS` and document the intended connector type in Description.
2. Fill the connection section (labels vary by version):
   - JDBC URL / TNS alias for the apps database (lab: placeholder noting “URL in vault / Config”)
   - Service user `SVC_IIQ_EBS` (lab: placeholder)
   - TLS / wallet path notes — never paste production secrets into exported XML in git
3. Owner `rachel.evans`. Mark **not authoritative**. Save.
4. Live non-prod: click **Test Connection** — success proves network + credentials + grants for a minimal handshake.

**Expected result:** Application object `MNB-Oracle-EBS` saved; live path shows Test Connection success.

**If it fails:** Listener / firewall first; then grants. Missing connector jar/license → document JDBC alternate and escalate to platform — do not invent credentials.

### Task 3 — Schema and correlation

The schema decides what governance can see. Missing status / end-date here means leaver evidence never materializes.

1. Open the account schema. Confirm/set: `USER_NAME` (native identity), `EMPLOYEE_NUMBER` (or equivalent), `EMAIL_ADDRESS`, `START_DATE`, `END_DATE` / status, and multi-valued **responsibilities** marked as the **entitlement attribute**.
2. Responsibility schema (if separate): responsibility key/name + description.
3. Correlation: `EMPLOYEE_NUMBER` ↔ identity `userId`, fallback `USER_NAME` ↔ `name`/`userName` (document case conventions — EBS often uppercases).
4. **Create identities: OFF.** EBS is a target; `MNB-HR` remains authoritative.

**Expected result:** Schema shows responsibilities as entitlement; employee number correlation documented; create-identities disabled.

### Task 4 — Mock inventory (fallback: no live EBS)

If you have no instance, simulate what aggregation *would* return so downstream steps still work. This is a fallback, not the lesson.

1. Create `~/iiq-lab-data/connectors/oracle-ebs/MNB-Oracle-EBS-mock.csv`:

```csv
USER_NAME,EMPLOYEE_NUMBER,EMAIL,responsibilities,status
HELEN.ROSS,MNB00091,helen.ross@meridiannb.com,MNB_GL_JOURNAL,ACTIVE
SOFIA.TORRES,MNB00095,sofia.torres@meridiannb.com,MNB_AP_CLERK|MNB_PO_BUYER,ACTIVE
SAMIR.HASSAN,MNB00094,samir.hassan@meridiannb.com,,INACTIVE
JORDAN.REED,MNB00092,jordan.reed@meridiannb.com,MNB_AP_CLERK|MNB_SUPPLIER_MASTER,ACTIVE
```

2. Shadow-aggregate via DelimitedFile (pipe-split `responsibilities`), or attach the file if your build allows a file-based test mode. Description must say “proxy / mock for EBS training.”
3. Read the seeded stories: Sofia still holds AP after her move (creep); Jordan holds the Lesson 12-style toxic pair (`MNB_AP_CLERK` + `MNB_SUPPLIER_MASTER`); Samir demonstrates a completed disable.

**Expected result:** Four mock accounts ready; three findings written down.

### Task 5 — Account Aggregation

Aggregation is continuous inventory — the Task Result *is* audit evidence.

1. Tasks → New → Account Aggregation: `MNB-Oracle-EBS-Account-Aggregation`.
2. Run (live or against the shadow app). Record accounts scanned/created and errors.
3. Open `sofia.torres` — confirm EBS account + responsibilities; open `samir.hassan` — confirm inactive/end-dated visible; open `jordan.reed` — confirm both AP and supplier-master entitlements.
4. Propose schedule: nightly, after HR aggregation, so correlation targets exist first.

**Expected result:** Task Result success; Sofia/Jordan/Samir spot-checks match the stories.

**If it fails:** Live empty schema → grants or wrong apps schema. Shadow zero rows → path/delimiter/multi-valued split.

### Task 6 — Provisioning policies (create / disable / responsibility)

1. Open Provisioning Policies for Create, Enable/Disable, Modify (or equivalent menu path).
2. Create field stubs: `USER_NAME`, `EMAIL_ADDRESS`, `EMPLOYEE_NUMBER`, responsibility assignment.
3. Disable pattern Meridian will use: set `END_DATE` / inactive status on leaver — document it even if you do not execute against live EBS.
4. Phase plan: phase 1 aggregation + disable; phase 2 responsibility provisioning after security review of write grants.
5. Export Application XML to binder with secrets redacted (`***LAB***`).

**Expected result:** Create/Disable/Modify stubs saved; two-phase enablement note; redacted export.

### Task 7 — Leaver runbook for FND_USER

Walk the examiner story end-to-end.

1. Storyboard termination, in order:
   1. **Revoke standing responsibilities** (especially AP/GL/supplier) — kills capability even if later steps stall.
   2. **Disable FND_USER** (`END_DATE` / inactive) — blocks login.
   3. **Re-aggregate** — evidence: inactive + empty sensitive responsibilities.
2. Attach SLA: sensitive responsibilities within 4 hours of HR term event; FND disable within 1 business day (tighten if Finance Ops requires same-day).
3. Note: database accounts / concurrent request ownership clean-up may be a parallel DBA ticket — outside this connector’s SLA but inside the runbook.

**Expected result:** Three-step leaver card with SLAs and DBA footnote.

### Task 8 — Finance SoD pair (Lesson 12 style)

1. Draft SoD pair: `MNB_AP_CLERK` vs `MNB_SUPPLIER_MASTER` (or Meridian’s real supplier-master responsibility name).
2. Write the examiner one-liner: *enter invoices and create the payee = classic fraud path.*
3. Map to a `lab-data/reference/sod-matrix.csv`-style row for Capstone; owner `rachel.evans`.
4. Confirm Jordan’s mock row would violate the pair — that is the training signal, not a coincidence.

**Expected result:** SoD pair card with owner and Capstone mapping note.

### Task 9 — Residual risk and examiner drill

1. Record `RR-EBS-CP-01`: *High-risk concurrent programs not surfaced as entitlements need compensating DBA export review.* Owner: EBS DBA + `rachel.evans`.
2. Answer: *"Prove a terminated AP clerk lost invoice-entry access."* Three artifacts: (1) responsibility revoke plan/log, (2) post-term Task Result, (3) account detail showing inactive and `MNB_AP_CLERK` absent.

**Expected result:** RR logged; written proof steps in the binder.

---

## Acceptance criteria

- [ ] Design card: name, owners, scope, entitlement strategy, sensitive responsibilities
- [ ] Real-world setup understood: service account, least privilege, TLS/network
- [ ] `MNB-Oracle-EBS` created; responsibilities as entitlements; create-identities off
- [ ] Aggregation evidence (live or mock) with Sofia/Jordan/Samir spot-checks
- [ ] Provisioning stubs + three-step leaver card with SLAs
- [ ] Lesson 12-style SoD pair + `RR-EBS-CP-01` + examiner proof steps recorded

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No EBS connector in UI | License / version / missing jar | Document JDBC alternate; escalate to platform |
| Test Connection fails | Firewall, TNS, wallet, or bad password | Fix network/TLS first; then vault credential; never widen to DBA personal account |
| Schema discovery empty | Wrong schema/user or missing grants | Confirm apps-read grants on FND views your version needs |
| Correlation orphans | `USER_NAME` ≠ IIQ `userName` casing | Prefer `employeeId`; document uppercase convention |
| Password in exported XML | Unencrypted config | Re-encrypt; scrub binder exports |
| Finance thinks JDBC DB Direct = EBS | Wrong connector narrative | Re-brief with matrix row + Concepts table |

---

## Training binder evidence

- Design card (naming, owners, scope, responsibilities vs concurrent programs)
- Real-world setup worksheet (instance, svc account, grants phase — no passwords!)
- Aggregation Task Result + Sofia/Jordan/Samir cube screenshots
- Provisioning stubs (redacted) + leaver card with SLAs
- SoD pair card + `RR-EBS-CP-01` + examiner proof steps

---

## Knowledge check

1. Why must EBS responsibilities be modeled as entitlements rather than a plain account attribute?
2. How does Oracle EBS application security differ from Oracle Database Direct?
3. What leaver evidence should IIQ show for a terminated FND user?
4. Why is Jordan’s mock row an SoD finding, and which Lesson 12 idea does it reuse?
5. What does `RR-EBS-CP-01` cover that responsibility certification alone might miss?
6. Why is create-identities off for `MNB-Oracle-EBS`?

### Answers

1. Entitlements become ManagedAttributes — certifiable, risk-rated, SoD-eligible, revocable via provisioning plans; plain attributes get none of that.
2. EBS governs `FND_USER` / responsibilities (application security); DB Direct governs RDBMS roles/privileges — different people, different exam questions.
3. Post-leaver aggregation showing inactive/end-dated account and sensitive responsibilities removed, plus the revoke/disable Task or provisioning logs.
4. He holds `MNB_AP_CLERK` and `MNB_SUPPLIER_MASTER` together — enter invoices and create payees; same toxic-pair discipline as Lesson 12 SAP Finance SoD.
5. High-risk concurrent programs / request-group power that may not appear as responsibility entitlements.
6. EBS is a target system; only `MNB-HR` creates identity cubes — unknown EBS users must surface as uncorrelated accounts for investigation.

---

## Further reading

- [Oracle E-Business Suite documentation library](https://docs.oracle.com/en/applications/ebusiness/) — landing for security and system-administration guides; search your EBS version for “Oracle E-Business Suite Security Guide” and user/responsibility administration.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “Oracle E-Business” or “Oracle ERP connector” for the version-specific application guide and featuresString reference.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — real-world JDBC, responsibility aggregation, and provisioning threads for ERP connectors.
- [FFIEC Information Security booklet](https://www.ffiec.gov/press/pr090906a.htm) (and current FFIEC IT Examination Handbook — Information Security) — examiner expectations for access control and audit evidence around financial applications.
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks) — search Oracle / database benchmarks relevant to your stack; use as hardening input for the service account and listener posture, not as a substitute for EBS responsibility governance.

---

## Stretch lab

Expand the SoD matrix with a second pair (e.g. `MNB_GL_JOURNAL` vs GL period-close / post responsibility if Meridian separates them). Then draft a targeted certification population for holders of `MNB_AP_CLERK` and `MNB_SUPPLIER_MASTER`, owned by `rachel.evans`, using Lesson 45-style campaign notes.

---

## Summary

- EBS governance hinges on the object model: responsibilities are entitlements, `FND_USER` disable is the leaver primitive, and concurrent programs need explicit coverage or a residual risk.
- Prefer the native EBS connector over “just JDBC” narratives that confuse application security with Database Direct.
- Aggregation Task Results, SoD pairs in the Lesson 12 style, and a three-step leaver card are the examiner-ready evidence chain.

---

**Previous:** [Lesson 80 — PeopleSoft HCM Connector](80-peoplesoft-hcm-connector.md)  
**Next:** [Lesson 82 — Mainframe RACF for Banking](82-mainframe-racf-banking.md)
