# Lesson 77 — Workday HCM Connector

**Level:** Intermediate  
**Track:** Connectors — ERP / HR / Banking  
**Time:** 90–120 min  
**Prereq:** Lesson 76 — AWS IAM Connector; Lesson 04 authoritative HR concepts (`MNB-HR`)  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (Workday row)
- Repo: `lab-data/connectors/features-string-glossary.md`
- Contrast: DelimitedFile `MNB-HR` from foundations (`lab-data/hr/MNB-HR-Employees.csv`)

---

## Learning objectives

You will be able to:

- Explain the Workday HCM object model (Workers, supervisory org, contingent workers, leave status) and how each maps into IdentityIQ identity attributes
- Perform the real-world Workday setup: Integration System User (ISU), ISU security groups, and RaaS / SOAP / OAuth connectivity choices
- Create and configure **MNB-Workday-HCM** field by field without flipping it authoritative while `MNB-HR` still owns cubes
- Design a dual-run cutover plan that an examiner would accept — and articulate why two authoritative apps is a bank-grade incident
- Complete the lesson with or without a live Workday tenant (mock fallback provided)

---

## Why this matters

**Business.** Meridian's joiner/mover/leaver accuracy today depends on nightly CSV drops into `MNB-HR`. When `nina.joiner` is hired into Retail, her AD account, Okta groups, and birthright roles appear only after the file lands and Identity Refresh runs. Workday as a live HCM feed collapses that lag: Worker status, supervisory manager, and contingent-worker flags update as HR events happen. That is the business case for this connector — not "Workday is modern," but "joiner SLA becomes hours, not overnight."

**Control / audit.** Examiners treat HR as the identity source of record. The question is never "do you have Workday?" — it is *"which system creates and inactivates cubes, and can you prove a cutover did not invent duplicates?"* Flipping two apps to authoritative at once (`MNB-HR` and `MNB-Workday-HCM`) is how banks invent ghost identities and fail reconciliation. This lesson builds the dual-run evidence chain *before* anyone touches the authoritative flag.

---

## Concepts

### Workers, not "users"

Workday HCM stores people as **Workers**. A Worker is keyed by a Worker ID / Employee ID and carries employment facts: legal name, preferred name, email, hire/termination dates, and — critically for IAM — **active vs terminated** status. Contiguous with that is the **supervisory organization**: the manager relationship and org tree HR actually uses for approvals. In IIQ terms, Workers become identity cubes (when the app is authoritative) or account rows correlated to cubes (when it is a candidate, as in this lab).

| Workday object | What it is | Meridian example |
| --- | --- | --- |
| **Worker (Employee)** | Regular employee record | `helen.ross` — Head of IAM, `MNB00001` |
| **Contingent Worker** | Contractor / temp with a Worker ID | Future contractor feed — treat like `raj.external` today |
| **Supervisory Org** | Manager + org tree for approvals | Sofia's manager chain under Commercial Lending |
| **Leave / Absence** | On-leave flag without termination | `sofia.torres` with `onLeave=true` in HR — mailbox stays, sensitive access may pause |
| **Job Profile / Position** | Title, job family, often department | Feeds `department`, `title`, birthright role selectors |

### Contingent workers are not optional scope

The naive cutover says "employees only — contractors stay in a spreadsheet." That is how contractor access escapes governance. Contingent Workers hold badges, VPN, and sometimes Shared Drive groups. Meridian's rule: if Workday has the Worker, IIQ aggregates it; population filters decide certification *scope*, not whether the person exists.

### Leave is not termination

`sofia.torres` is active (`status=1`) but `onLeave=true` in the HR file. Workday surfaces similar leave states. Mapping leave to "inactive identity" would fire the leaver workflow and destroy her accounts — wrong. Leave is an **identity attribute** that may drive temporary entitlement suspension; termination is the leaver event. Confusing them is a classic HR-connector defect under exam.

### Authoritative means "creates people"

In IIQ, an **authoritative** application creates and updates identity cubes from aggregation. `MNB-HR` is Meridian's lab authoritative source today. `MNB-Workday-HCM` is built here as an **authoritative candidate**: same attribute ambition, create-identities **off**, dual-run reconciliation required before any flip. Two authoritative apps for the same population = duplicate cubes, split managers, and certifications that cannot be explained.

```
Wrong (exam failure):
  MNB-HR (auth) ──► cubes
  MNB-Workday-HCM (auth) ──► MORE cubes for same people

Right (this lesson):
  MNB-HR (auth) ──► cubes
  MNB-Workday-HCM (non-auth candidate) ──► reconcile Worker IDs vs employeeId
  Flip only after dual-run evidence + change ticket
```

---

## How it works

The SailPoint Workday connector reads Worker and related data from a Workday tenant using an **Integration System User (ISU)** authenticated via SOAP (classic), **RaaS** (Report-as-a-Service custom reports), and/or **OAuth** depending on your IIQ/connector version and tenant policy. Unpack the pieces:

- An **ISU** is a non-human Workday account dedicated to integrations. It is not a person's login.
- **ISU security groups** grant that account domain permissions (Worker data, org data, custom reports). Too narrow → empty aggregations; too wide → a privileged HR credential.
- **RaaS** exposes a custom report as a web service — useful when the stock Worker response groups lack a field Meridian needs (e.g. a custom `employeeId` format).
- **OAuth** (where supported) replaces long-lived ISU passwords with token-based auth — prefer it in production when your build allows.

```
IdentityIQ (MNB-Workday-HCM)
        │  ISU + tenant URL  (SOAP / RaaS / OAuth per build)
        ▼
Workday Web Services / RaaS
        ├── Get_Workers / Worker reports     → identity / account aggregation
        ├── Supervisory Org / manager refs   → manager correlation
        ├── Contingent Worker endpoints      → contractor population
        └── (optional) Workday Accounts path → app accounts, NOT this lesson's HCM feed
```

| Operation | Workday behavior | IIQ behavior |
| --- | --- | --- |
| Worker aggregation | Paged Worker retrieve / RaaS report | One row per Worker; Worker/Employee ID as key |
| Manager resolution | Supervisory org manager Worker ID | Identity `manager` link after correlation |
| Status / term | Active, Terminated, dates | Active/inactive + leaver triggers when authoritative |
| Leave indicators | Leave / absence fields | Attribute — do **not** map to terminated |
| Contingent workers | Contingent Worker type | Same cube pipeline; filter populations later |

**Matrix reminder:** preferred connector is **Workday** (HCM Workers). **Workday Accounts** is a separate concern (application accounts inside Workday) — do not overload `MNB-Workday-HCM` with both without an ADR.

One consequence: the connector is exactly as powerful as the ISU security groups. Least privilege is decided in Workday, not in IIQ.

---

## Real-world setup (outside IIQ)

Read this even if you use the mock fallback — the knowledge check and the examiner both assume you know it.

### Step 1 — Integration System User

1. In Workday, create ISU `ISU_IdentityIQ` (or Meridian naming `ISU_MNB_IIQ`). No UI sessions for humans; exclude from people certifications.
2. Set a strong password (or prepare OAuth client credentials if your connector version uses OAuth). Vault it — never commit tenant secrets.

### Step 2 — ISU security groups

1. Create or assign an Integration System Security Group that can read Worker, Job, Organization, and Contingent Worker data required by the connector guide for your IIQ version.
2. Start **read-only**. Do not grant business-process initiation rights "just in case."
3. If using RaaS, share the custom report with the ISU and confirm the report runs as that security context.

### Step 3 — Connectivity choice

1. Confirm tenant host (e.g. `wd2-impl-services1.workday.com` style — your tenant's actual host from Workday admin docs).
2. Decide SOAP response groups vs RaaS field list vs OAuth token endpoint — document the choice; do not mix undocumented hybrids.
3. Network: IIQ hosts need outbound HTTPS to Workday; no inbound from Workday required for aggregation-only.

### Step 4 — Field contract with HRIS

Before configuration, HRIS (`sofia.torres` as proxy owner in lab) and IAM (`helen.ross`) agree in writing: Worker ID format (`MNB#####` or bridge), contingent-worker inclusion, leave-field semantics, and which supervisory org levels feed manager. You will capture this in Task 1.

### Step 5 — Governance records

Document: tenant name, ISU name, security group list (no passwords), auth method, phase (aggregation-only vs future provisioning), and the dual-run owner.

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq` as `spadmin`; `MNB-HR` exists and is authoritative
- [ ] Decide your path: live Workday sandbox tenant or the mock fallback in Task 4
- [ ] Never put production ISU passwords on lab machines — placeholders or disposable sandbox only
- [ ] Personas: `nina.joiner` (joiner), `helen.ross` (IAM owner), `sofia.torres` (HRIS contact, on leave in HR data)

---

## Lab procedure

### Task 1 — Design decisions and single-authoritative rule

Every HR connector starts with a design card, because flipping authority after certifications and birthright roles reference cubes is painful. Decide now.

1. Application name: `MNB-Workday-HCM`. Owner: `helen.ross`; HRIS business contact: `sofia.torres`.
2. Write the non-negotiable rule: *Only one authoritative application active for a given employee population.*
3. Lab stance: **`MNB-HR` remains authoritative**; `MNB-Workday-HCM` is a future authoritative candidate (create-identities off).
4. Scope: employees + contingent workers; leave as attribute; termination as inactive/leaver trigger only when authoritative.

**Expected result:** Design card covering name, owners, single-auth rule, lab stance, and Worker scope.

### Task 2 — Create MNB-Workday-HCM

In production this consumes the ISU, tenant URL, and security-group outcomes from Steps 1–3. The connector form asks for exactly those artifacts.

1. Applications → Add New → **Workday** (HCM / Workers — or equivalent menu path).
2. Fill connection placeholders:
   - **Tenant / endpoint URL**: lab note `"Workday sandbox host — value in vault"`
   - **ISU username**: `ISU_MNB_IIQ`
   - **Password / OAuth client**: placeholder `"secret in vault"` — never a real password in the binder
   - Auth method note: SOAP, RaaS, or OAuth per your build
3. Owner `helen.ross`. Save.
4. Live sandbox: click **Test Connection** — success proves ISU auth + network + basic security-group reachability.

**Expected result:** Application object saved; live path shows Test Connection success.

**If it fails:** SOAP/auth faults usually mean wrong tenant host, ISU locked, or security group missing Worker domains — fix in Workday, not by widening IIQ blindly. Continue with mock if no tenant.

### Task 3 — Schema and correlation map

The schema decides whether leave, manager, and contingent flags become usable governance signals.

1. Map Worker / Employee ID → identity `employeeId` (`MNB#####` style where possible).
2. Map email → `email`; legal/preferred name → display attributes.
3. Map supervisory manager Worker ID → manager correlation (resolve to identity, not raw ID forever).
4. Map active/terminated (+ termination date) → IIQ inactive semantics for *future* authoritative use.
5. Map leave / absence → `onLeave` (or equivalent) — **do not** equate to terminated. Anchor with `sofia.torres`.
6. Map contingent vs employee → `workerType` (align with Lesson 05 HR naming where possible).
7. **Create identities: OFF.** Document that this remains true until cutover Phase 3.

**Expected result:** Attribute map table; create-identities disabled; leave ≠ terminate called out.

### Task 4 — Mock workers (fallback: no live tenant)

If you have no tenant, simulate what Worker aggregation *would* return. This is a fallback, not the lesson.

1. Create `~/iiq-lab-data/connectors/workday/MNB-Workday-HCM-mock.csv`:

```csv
workerId,userName,email,managerId,status,workerType,onLeave,department,title
MNB00120,nina.joiner,nina.joiner@meridiannb.com,MNB00007,active,Employee,false,RET,Teller
MNB00001,helen.ross,helen.ross@meridiannb.com,,active,Employee,false,SEC,Head of Identity & Access
MNB00095,sofia.torres,sofia.torres@meridiannb.com,MNB00006,active,Employee,true,CML,Relationship Manager
MNB00999,ex.employee,ex.employee@meridiannb.com,MNB00007,terminated,Employee,false,RET,Former Teller
MNB00888,raj.contingent,raj.contingent@meridiannb.com,MNB00003,active,Contingent,false,IT,Contractor Analyst
```

2. Create a shadow DelimitedFile app pointing at it for aggregation practice only, or attach the file if your build allows a file-based test mode — label the shadow clearly as **non-authoritative training**.
3. Read the seeded stories: Nina = joiner; Sofia = on leave but active; `ex.employee` = terminated; contingent row = must not be excluded from inventory.

**Expected result:** Five mock Workers ready; four stories understood.

### Task 5 — Account / identity aggregation (non-authoritative)

Aggregation is continuous inventory. For an HR candidate, the Task Result proves the feed works *without* creating people.

1. Tasks → New → Account Aggregation (or the Workday identity-aggregation pattern your version documents): `MNB-Workday-HCM-Account-Aggregation`.
2. Run live or against the shadow app. Record scanned/created counts and errors.
3. On the binder cover sheet write in large letters: **non-authoritative lab run — MNB-HR still owns cubes.**
4. Propose schedule for dual-run: after `MNB-HR` aggregation nightly, so reconcile has both sides.

**Expected result:** Task Result success + explicit non-auth note; no unexpected cube explosion.

**If it fails:** Live empty Workers → ISU security groups / response groups / RaaS share. Shadow zero rows → path/delimiter. Duplicate cubes → you accidentally enabled authoritative create — disable immediately and remediate.

### Task 6 — Dual-run cutover plan

This is the examiner-facing artifact. Dual-run means both feeds produce comparable ID sets before anyone flips authority.

1. **Phase 1 — Parallel:** Nightly Workday aggregation (non-auth) + `MNB-HR`; reconcile `workerId`/`employeeId` sets; log deltas (in Workday not HR, in HR not Workday, attribute mismatches on manager/status/leave).
2. **Phase 2 — Freeze and fix:** Freeze CSV schema changes; HRIS fixes Workday data quality; IAM fixes maps; sample reconcile of ≥10 identities including `nina.joiner` and `sofia.torres`.
3. **Phase 3 — Flip with rollback:** Change ticket; disable authoritative on `MNB-HR` (or segment populations); enable authoritative on `MNB-Workday-HCM`; Identity Refresh; rollback = reverse the flags and restore last-known-good HR file path.
4. Evidence pack: reconcile spreadsheet sample, Task Results from both apps, change ticket ID, rollback owner (`helen.ross`).

**Expected result:** Three-phase cutover page with evidence list and rollback.

### Task 7 — Joiner / leave / leaver trigger notes

Connect the feed to lifecycle conceptually (Lessons 29–31, 34).

1. **Joiner:** Workday active Worker for `nina.joiner` → (when authoritative) cube create → birthright — SLA clock starts at Worker active, not at CSV drop.
2. **Leave:** `sofia.torres` onLeave → temporary access policy; accounts stay; do not run full leaver.
3. **Leaver:** terminated Worker → disable targets within SLA; re-aggregate shows inactive — evidence.
4. Note contingent joiners need the same clock; excluding them recreates the contractor blind spot.

**Expected result:** Trigger notes page covering joiner, leave, leaver, contingent.

### Task 8 — Examiner question drill

*"What is Meridian's identity source of record today, and what is the target state?"*

Write the answer: today `MNB-HR` (Delimited File); target `MNB-Workday-HCM` after dual-run; never both authoritative for the same population. Attach the Phase 1–3 page as evidence of control over the cutover.

**Expected result:** Written answer in the binder.

### Task 9 — Residual risk

Record `RR-WD-DUAL-01`: *During dual-run, attribute drift between CSV and Workday can drive conflicting manager or status if anyone enables both as authoritative prematurely. Compensating control: create-identities off on Workday until Phase 3; daily reconcile owned by helen.ross / sofia.torres.*

**Expected result:** RR logged with owners.

---

## Acceptance criteria

- [ ] Design card: name, owners, single-auth rule, lab stance, Worker scope
- [ ] Real-world setup understood: ISU, security groups, SOAP/RaaS/OAuth choice
- [ ] `MNB-Workday-HCM` created; schema maps leave ≠ terminate; create-identities off
- [ ] Aggregation evidence (live or mock) with Nina / Sofia / terminated / contingent stories
- [ ] Three-phase dual-run cutover + examiner answer
- [ ] `RR-WD-DUAL-01` recorded

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Duplicate identity cubes | Two authoritative apps for same population | Disable auth on one immediately; merge/remediate; reopen dual-run |
| Manager attribute blank | Supervisory org / manager not in response group or RaaS | Expand Workday field list; re-agg; fix manager correlation |
| ISU authentication / permission errors | Security group missing Worker domains, or ISU locked | HRIS grants least-privilege domains; unlock ISU; Shadow path for class |
| Terminated Worker still active in IIQ | Status / termination mapping wrong | Fix map; re-agg; Identity Refresh; verify inactive |
| On-leave Worker fully deprovisioned | Leave mapped as terminated | Remap leave to attribute; restore accounts; update runbook |
| CSV and Workday ID sets drift | No reconcile job during cutover | Daily dual-run spreadsheet; block Phase 3 until deltas closed |

---

## Training binder evidence

- Design card (naming, owners, single-auth rule, scope)
- Real-world setup worksheet (ISU name, security groups, auth method — no secrets)
- Attribute map + mock CSV + non-auth Task Result
- Three-phase dual-run cutover with rollback
- Examiner answer + `RR-WD-DUAL-01`

---

## Knowledge check

1. Why must Meridian keep `MNB-HR` authoritative while building `MNB-Workday-HCM` in lab?
2. What is an Integration System User, and where is its power actually constrained?
3. Why is `sofia.torres` on leave a different event from a terminated Worker?
4. Name the three dual-run cutover phases at a high level.
5. Why include contingent workers in aggregation scope?
6. What residual risk does `RR-WD-DUAL-01` capture?

### Answers

1. Two authoritative apps for the same population create duplicate cubes and unexplained churn; the lab validates maps under a single source of record.
2. A non-human Workday integration account; its power is constrained by ISU security groups (and report shares), decided in Workday.
3. Leave keeps the Worker active and usually keeps accounts; termination is the leaver trigger. Mapping leave to inactive fires the wrong workflow.
4. Parallel reconcile → freeze/fix deltas → flip authoritative with change ticket and rollback.
5. Contractors hold real access; excluding them from inventory recreates the classic governance blind spot.
6. Attribute/ID drift (or premature dual authority) during cutover — compensated by create-identities off and owned daily reconcile.

---

## Further reading

- [Workday Community](https://community.workday.com/) — search "Integration System User" and "ISU security groups" for the tenant-side setup that Step 1–2 describe (login required; standard for Workday customers).
- [Workday Community — Report-as-a-Service (RaaS)](https://community.workday.com/) — search "RaaS" for custom-report web service patterns when stock Worker responses lack a field.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search "Workday connector" for the version-specific application guide, auth options, and featuresString reference.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — real-world ISU permission and aggregation troubleshooting threads.
- [FFIEC Information Security booklet](https://www.ffiec.gov/press/pr090996a.htm) — framing for examiners on information security; use alongside your institution's HR source-of-record control narrative (search current FFIEC IT handbooks for "information security").
- [NIST SP 800-53 — AC / IA control families](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — identity lifecycle and account management controls that HR authoritative feeds support.

---

## Stretch lab

Draft a one-paragraph ADR seed: when Meridian also needs **Workday Accounts** (application accounts inside Workday) vs HCM Worker feed — two application objects, two owners, never one overloaded app. Then extend the dual-run spreadsheet with a leave-state column and show how `sofia.torres` would look wrong if leave were mapped to inactive.

---

## Summary

- Workday HCM is Meridian's future authoritative Worker feed; Workers, supervisory org, contingent workers, and leave each map differently into IIQ.
- ISU + security groups (+ SOAP/RaaS/OAuth) decide what the connector can see — least privilege lives in Workday.
- Dual-run with `MNB-HR` still authoritative is mandatory evidence; flipping both authoritative is an exam failure, not a shortcut.

---

**Previous:** [Lesson 76 — AWS IAM Connector](76-aws-iam-connector.md)  
**Next:** [Lesson 78 — SAP HR/HCM Connector](78-sap-hr-hcm-connector.md)
