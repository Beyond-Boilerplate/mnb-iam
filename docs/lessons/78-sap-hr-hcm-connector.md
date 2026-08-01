# Lesson 78 — SAP HR/HCM Connector

**Level:** Intermediate  
**Track:** Connectors — ERP / HR / Banking  
**Time:** 90–120 min  
**Prereq:** Lesson 77 — Workday HCM Connector; Lesson 04 (`MNB-HR`); Lesson 12 (`MNB-SAP-Finance`) helpful for contrast  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (SAP HR row)
- Repo: `lab-data/apps/MNB-SAP-Finance.csv` (finance **security extract** — wrong object for this lesson)
- Repo: `lab-data/HRApplications.txt` (CSV/TXT HR contrast from Lesson 04)
- Repo: `lab-data/connectors/features-string-glossary.md`

---

## Learning objectives

You will be able to:

- Distinguish **SAP HR/HCM** (who people are) from **SAP Direct** (what they can do in SAP) and from the Lesson 12 finance CSV
- Explain SAP HR building blocks — infotypes, personnel number (PERNR), org assignment — in IAM language
- Perform the real-world RFC/BAPI connectivity setup: least-privilege RFC user, gateway reachability, and what *not* to grant (`SAP_ALL`)
- Create **MNB-SAP-HR** with a defensible PERNR↔`userId` bridge and run a safe non-authoritative aggregation
- Document coexistence with `MNB-HR`, Workday, and SAP security apps without creating a second authoritative source by accident
- Complete the lesson with or without a live SAP HCM system (mock fallback provided)

---

## Why this matters

**Business.** Some Meridian legal entities still run SAP HCM for payroll and organizational management. Those workers never appear in a Workday tenant. If IAM only knows corporate `MNB-HR` CSV employees, subsidiary joiners never get birthright access and leavers never get a clean disable — or worse, someone "fixes" it by stuffing people into the finance role CSV from Lesson 12. When `amelia.brooks` moves org units inside SAP, infotype 0001 may update days before the corporate file; without a governed SAP HR feed, manager hierarchy and birthright selectors drift.

**Control / audit.** Examiners and SOX testers routinely confuse **SAP user security** with **HR master data**. Certifying `MNB-SAP-Finance` as if it were the employee roster — or aggregating ECC roles into an HR app — fails the control narrative. Separate applications: people in `MNB-SAP-HR`, roles in `MNB-SAP-Direct` (Lesson 79).

---

## Concepts

### Infotypes — SAP's way of storing people facts

SAP HCM does not store a single flat "employee row" the way `HRApplications.txt` does. It stores **infotypes**: numbered slices of HR data maintained with effective dates. The ones IAM cares about most:

| Infotype (common) | What it holds | IAM use |
| --- | --- | --- |
| **0000** Actions | Hire, terminate, status changes | Active / inactive triggers |
| **0001** Org Assignment | Position, org unit, cost center, administrator | Department, org, sometimes manager path |
| **0002** Personal Data | Name | Display attributes |
| **0006** Addresses | Address (sometimes email in custom setups) | Contact attrs if used |
| **0105** Communications | System user ID, email, phone | Correlation hints (`userName`, email) |

You do not need to become an HR configurator. You need to know that **the connector reads these slices** (via BAPIs / function modules), and a missing infotype authorization on the RFC user looks like "SAP has no email" when the data is actually there.

### Personnel number (PERNR) is not Meridian `userId`

Every SAP employee has a **personnel number (PERNR)** — the native key in HCM. Meridian cubes key on `userId` (`MNB#####`). Those numbers are rarely identical. Without an explicit **bridge** (`userId` ↔ `sapPernr`), correlation fails and you get uncorrelated Workers or — if someone panics and enables create-identities — a second identity for the same human.

Real-life anchor: `sofia.torres` is `MNB00095` in HR. In a subsidiary SAP HCM client she might be PERNR `00001234`. The bridge is a control, not a convenience.

### Org assignment feeds manager and department — carefully

Infotype 0001 / org management relationships can yield manager and org unit. Treat manager resolution like Workday supervisory org: resolve PERNR → identity after the bridge exists. Do not leave raw PERNRs as "manager" on the cube forever.

### Contrast with Lesson 04 CSV HR and Lesson 12 finance CSV

Lesson 04 taught governance mechanics on a flat file. That file is still Meridian's lab authoritative source — but it is not what a live SAP subsidiary looks like.

| Source | Shape | What it can feed | What it cannot |
| --- | --- | --- | --- |
| `MNB-HR` (Lesson 04) | Flat CSV | Corporate `userId`, manager, leave | Live SAP org events |
| `MNB-SAP-HR` (this lesson) | Infotype-backed RFC | PERNR, org assignment, SAP status | ECC posting roles |
| `MNB-SAP-Finance` (Lesson 12) | Entitlement extract | Coarse `SAP_FI` label | Hire date, org, leave, PERNR |

**Wrong way:** use `MNB-SAP-Finance.csv` as an HR source because "it has userId." That file is a **security entitlement** extract. It will never be a safe authoritative feed.

### Three Meridian SAP-shaped apps — do not mix them

| Connector / app | Governs | Meridian object |
| --- | --- | --- |
| DelimitedFile HR (Lesson 04) | Corporate employee roster | `MNB-HR` (authoritative in lab) |
| **SAP HR/HCM** (this lesson) | SAP-managed workforce master / org | **`MNB-SAP-HR`** |
| DelimitedFile finance (Lesson 12) | Coarse `SAP_FI` entitlement extract | `MNB-SAP-Finance` |
| SAP Direct (Lesson 79) | ECC users + roles/profiles | `MNB-SAP-Direct` |

```
Lesson 04 CSV HR  ──► MNB-HR          (who — corporate, auth in lab)
SAP HCM           ──► MNB-SAP-HR      (who — SAP entities; candidate / segmented)
Lesson 12 CSV     ──► MNB-SAP-Finance (what — stale SAP_FI code)
SAP ECC security  ──► MNB-SAP-Direct  (what — real roles; next lesson)
```

Same authoritative rule as Workday (Lesson 77): do **not** enable `MNB-SAP-HR` as authoritative while `MNB-HR` (or Workday) already creates cubes for the same population — unless you have an explicit multi-entity architecture with population filters.

---

## How it works

The SailPoint **SAP HR/HCM** connector reaches an SAP ABAP system over **RFC** (Remote Function Call), invoking **BAPIs** / HR function modules to read personnel and org data. This is not the same connector path as SAP Direct security (Lesson 79), even though both may share host/client/RFC plumbing concepts.

```
IdentityIQ (MNB-SAP-HR)
        │  RFC destination: host, system number, client, RFC user
        ▼
SAP Gateway / Message Server
        ▼
SAP HCM (ABAP)
        ├── BAPI / HR FM: personnel master   → Worker-like accounts / identity feed
        ├── Org assignment / OM relations    → department, manager refs
        └── Employment status / actions      → active / inactive
```

| Operation | SAP behavior | IIQ behavior |
| --- | --- | --- |
| Aggregation | RFC reads personnel + selected infotypes | One account (or identity row) per PERNR in scope |
| Correlation | Bridge PERNR ↔ `userId` | Match to existing `MNB-HR` / Workday cubes |
| Status | Actions / employment status | Inactive flag when mapped correctly |
| Manager | Org / chief relationships | Manager link after PERNR resolution |

**Matrix:** preferred **SAP HR/HCM**; alternate **DelimitedFile** (what Lesson 04 already taught — not a production substitute for live subsidiaries).

Authentication note: the **RFC user** must be a system user with HR read authorizations for the needed infotypes and org objects. Granting `SAP_ALL` "to make the connector work" is a finding — you have created a god credential that can also change security and finance. Least privilege is decided in SAP PFCG roles for that RFC user.

---

## Real-world setup (outside IIQ)

Read this even if you use the mock fallback — the knowledge check and the examiner both assume you know it.

### Step 1 — RFC connectivity

1. From BASIS, obtain: application server host (or message server + group), system number, client, and whether SNC/TLS is required.
2. Confirm IIQ (or IQService, if your deployment routes RFC there) can reach the gateway ports — firewall tickets before configuration day.
3. Non-prod first (DEV/QA client); never point lab at production.

### Step 2 — Least-privilege RFC user

1. Create system user `RFC_IIQ_HR` (Meridian naming) — no dialog login for humans.
2. Assign a custom role with **display/read** for required HR infotypes and org management objects per the SailPoint SAP HR connector guide for your version.
3. Explicitly **do not** assign `SAP_ALL`, `SAP_NEW`, or broad Basis roles. If aggregation fails with auth errors, add the *named* missing object — resist the temptation to escalate.
4. Password/SNC credentials in vault; rotate on schedule.

### Step 3 — Scope filters and field contract with HR

1. Agree which personnel areas / employee groups / subsidiaries are in scope for `MNB-SAP-HR`.
2. Agree the PERNR↔`userId` bridge source of truth (HRIS table, IdM attribute, or controlled CSV maintained by `sofia.torres`'s team).
3. Align field list with Lesson 05 HR schema naming where possible (`department`, `title`, `exceptions` (LOA), `employeeType`).

### Step 4 — Governance records

Document: SID/client, RFC user (no password), role name, SNC flag, population scope, authoritative stance (usually **off** while `MNB-HR` or Workday owns corporate), owner `helen.ross`, HR contact `sofia.torres`, and Basis contact for RFC.

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq` as `spadmin`; Lessons 04, 12, and 77 concepts reviewed
- [ ] `lab-data/apps/MNB-SAP-Finance.csv` and `lab-data/HRApplications.txt` readable for contrast
- [ ] Decide path: live SAP HCM sandbox or mock fallback
- [ ] Know PERNR may differ from `MNB#####` — bridge is mandatory
- [ ] Personas: `sofia.torres`, `samir.hassan`, `amelia.brooks`; IAM owner `helen.ross`

---

## Lab procedure

### Task 1 — Separation statement and CSV contrasts

Ground the architecture in writing before clicking Create Application.

1. Write and paste into the binder: *SAP HR feeds who people are; SAP Direct feeds what they can do in SAP; Lesson 12 `MNB-SAP-Finance` is a legacy entitlement extract, not an HR system.*
2. Open `~/iiq-lab-data/HRApplications.txt` (or repo `lab-data/HRApplications.txt`). Note flat columns: `userId`, `managersAssociateID`, `exceptions` (LOA), `employeeType` — the shape IIQ already understands from Lesson 04.
3. Open `~/iiq-lab-data/apps/MNB-SAP-Finance.csv`. Note it only has `userName`, `email`, `employeeId`, `entitlement` (`SAP_FI`), `accountStatus` — **no org assignment, no PERNR, no hire date**.
4. Write one sentence: why neither file replaces a live SAP HCM feed for a subsidiary — and why the finance file must never become authoritative HR.

**Expected result:** Separation statement + two-file contrast paragraph in the binder.

### Task 2 — Create MNB-SAP-HR

In production this consumes the RFC destination and least-privilege role from Steps 1–2. The connector form asks for exactly those artifacts.

1. Applications → Add New → **SAP HR/HCM** (or equivalent menu path).
2. Connection placeholders: host/message server, system number, client, RFC user `RFC_IIQ_HR`, password `"in vault"`.
3. Name: `MNB-SAP-HR`. Owner: `helen.ross`; HR contact: `sofia.torres`.
4. Live sandbox: **Test Connection** — proves RFC logon and basic reachability (not full infotype authorization).

**Expected result:** Application object saved; live path shows Test Connection success.

**If it fails:** Network/gateway issues → BASIS. Auth failures naming authorization objects → extend the RFC role with those objects only. Continue mock if no system.

### Task 3 — Attribute map and PERNR bridge

The bridge decides whether SAP Workers attach to Meridian cubes or become orphan noise.

1. Map SAP personnel number → secondary identity attribute `sapPernr` (always retain native key).
2. Design bridge table/file: `userId,sapPernr` maintained by HRIS — example rows for lab personas.
3. Map email / system user (infotype 0105 style) → `email` / `userName` correlation fallbacks.
4. Map employment status / actions → inactive semantics.
5. Map org unit / department; manager PERNR → resolution plan *after* bridge load.
6. Map leave if available — do **not** equate leave to terminated (Sofia pattern from Lesson 77).
7. **Create identities: OFF** unless you are in a disposable sandbox dedicated to SAP-authoritative experiments with a segmented population.

**Expected result:** Bridge design page + attribute map; create-identities off.

### Task 4 — Mock extract (fallback: no live SAP)

If you have no SAP system, simulate what personnel aggregation *would* return. This is a fallback, not the lesson.

1. Create `~/iiq-lab-data/connectors/sap/MNB-SAP-HR-mock.csv`:

```csv
sapPernr,userId,userName,email,status,orgUnit,managerPernr,exceptions
00001001,MNB00095,sofia.torres,sofia.torres@meridiannb.com,active,CML,00001000,true
00001002,MNB00094,samir.hassan,samir.hassan@meridiannb.com,inactive,IT,00001000,false
00001003,MNB00098,amelia.brooks,amelia.brooks@meridiannb.com,active,CML,00001000,false
00001000,MNB00006,mgr.commercial,mgr.commercial@meridiannb.com,active,CML,,false
```

2. Create companion bridge stub `~/iiq-lab-data/connectors/sap/MNB-SAP-PERNR-bridge.csv` with the same `userId,sapPernr` pairs.
3. Shadow-aggregate via DelimitedFile labeled **non-authoritative training**. Read the stories: Sofia on leave but active; Samir inactive (leaver residual); Amelia active RM.

**Expected result:** Mock + bridge files; three persona stories understood.

### Task 5 — Aggregation task (safe)

Aggregation is continuous inventory. For an HR candidate, the Task Result proves the feed works *without* creating people.

1. Create `MNB-SAP-HR-Account-Aggregation` (or identity aggregation per your connector version — document which).
2. Run live or shadow. Confirm no unintended identity creates.
3. Spot-check: correlated personas show `sapPernr` populated when bridge + correlation rule/design are applied (even if the rule is design-only in lab).
4. Binder cover note: **non-authoritative lab run — MNB-HR still owns cubes.**

**Expected result:** Task Result + non-auth note; no cube duplication.

**If it fails:** Uncorrelated rows → bridge missing or PERNR formatting (leading zeros). Wrong people in a finance cert → you pointed a certification at the wrong app (Task 1 failure mode).

### Task 6 — Coexistence matrix

Build the examiner-ready population table:

| Source | Population | Authoritative? | Notes |
| --- | --- | --- | --- |
| `MNB-HR` | Corporate lab employees | **Yes** (lab today) | Lesson 04 CSV |
| `MNB-Workday-HCM` | Future corporate HCM | Candidate (Lesson 77) | Dual-run before flip |
| `MNB-SAP-HR` | SAP HCM legal entities | No / segmented only | This lesson |
| `MNB-SAP-Finance` | Finance entitlement holders | No | Legacy; not HR |
| `MNB-SAP-Direct` | ECC role holders | No | Lesson 79 |

Mark any overlapping population with both auth flags as a residual risk (next task).

**Expected result:** Coexistence matrix in the binder.

### Task 7 — Examiner Q&A

*"Show you are not certifying SAP HR as finance roles."*

Answer: `MNB-SAP-HR` carries personnel/org attributes only; finance posting access is `SAP_FI` on `MNB-SAP-Finance` today and real roles on `MNB-SAP-Direct` tomorrow (Lesson 79). Certifications for SoD use the security apps, not the HR connector. Point to separate application objects as evidence.

**Expected result:** Written distinction answer.

### Task 8 — Residual risk

Record `RR-SAP-PERNR-01`: *PERNR↔userId bridge errors cause uncorrelated SAP Workers or duplicate identities if create-identities is enabled. Compensating controls: bridge owned by sofia.torres, create-identities off, weekly uncorrelated account review (Lesson 19 pattern).* Owner: `sofia.torres`.

**Expected result:** RR with owner.

### Task 9 — Binder packaging

Assemble `MNB-SAP-HR-Binder-YYYY-MM-DD` with: separation statement, contrast paragraph, app redacted config, bridge design, mock Task Result, coexistence matrix, examiner answer, `RR-SAP-PERNR-01`.

**Expected result:** Dated binder index with eight artifacts checked off.

---

## Acceptance criteria

- [ ] HR vs security vs Lesson 12 CSV separation documented
- [ ] Real-world RFC/BAPI least-privilege setup understood
- [ ] `MNB-SAP-HR` shell + PERNR bridge design; create-identities off
- [ ] Mock (or live) aggregation evidence with Sofia/Samir/Amelia stories
- [ ] Coexistence matrix + examiner distinction answer
- [ ] `RR-SAP-PERNR-01` + dated binder index packaged

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Wrong people in a finance certification | Cert scope points at HR or uses finance CSV as "people" | Repoint certs to security apps; keep `MNB-SAP-HR` out of role SoD |
| Uncorrelated cubes / accounts | PERNR bridge missing or zero-padding mismatch | Load bridge; normalize PERNR format; correlation rule |
| Authoritative clash | SAP HR + `MNB-HR` / Workday both auth for same humans | Segment populations or disable one auth flag immediately |
| RFC failures / dumps | Network, client, or missing auth objects | BASIS connectivity; add named objects — never `SAP_ALL` for convenience |
| Org unit / manager churn noise | Full aggregation too frequent or OM history included | Filter current assignment; schedule off-peak; use delta if supported |
| Email blank after agg | Infotype 0105 (or equivalent) not authorized / not in field map | Extend RFC role; add communication fields to schema |

---

## Training binder evidence

- Separation statement + Lesson 04 / 12 contrast notes
- RFC setup worksheet (user, role, client — no passwords)
- Attribute map + PERNR bridge design
- Mock/live Task Result
- Coexistence matrix, examiner answer, `RR-SAP-PERNR-01`, dated binder index

---

## Knowledge check

1. What does `MNB-SAP-HR` govern versus `MNB-SAP-Direct`?
2. Why maintain a `userId`↔PERNR bridge?
3. Why is Lesson 12's `MNB-SAP-Finance` CSV the wrong stand-in for SAP HR?
4. What matrix preferred connector applies to SAP HR, and what is the alternate?
5. Why is granting `SAP_ALL` to the RFC user unacceptable?
6. What residual risk id covers bridge errors, and who owns it?

### Answers

1. People / HR master and org data vs SAP application security roles and profiles.
2. Meridian cubes key on `MNB#####` while SAP HCM keys on PERNR — without a bridge, correlation fails.
3. It is an entitlement extract (`SAP_FI`) without org/hire/leave master data — and it is not an HR system of record.
4. Preferred **SAP HR/HCM**; alternate **DelimitedFile**.
5. It creates a god-level credential far beyond HR read — a security finding and an audit failure.
6. `RR-SAP-PERNR-01`, owned by `sofia.torres`.

---

## Further reading

- [SAP Help Portal](https://help.sap.com/) — search "Personnel Administration infotypes" and "RFC" for the HR data model and connectivity concepts behind this connector.
- [SAP Help Portal — Authorizations](https://help.sap.com/) — search "PFCG" and "authorization objects" for how to build the least-privilege RFC role instead of `SAP_ALL`.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search "SAP HR" or "SAP HCM connector" for version-specific field maps and aggregation behavior.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — RFC authorization and PERNR correlation troubleshooting threads.
- [NIST SP 800-53 — AC-2 Account Management](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — why workforce source-of-record accuracy matters for account lifecycle.
- [FFIEC IT Examination Handbook — Information Security](https://ithandbook.ffiec.gov/) — examiner framing for access control and systems of record when multiple HCM feeds coexist.

---

## Stretch lab

Sketch a population selector for certifications: `identity.sapPernr != null` limits a campaign to SAP-HCM-backed subsidiary workers. Then draft a one-page note comparing attribute richness: Lesson 04 CSV vs Workday (Lesson 77) vs SAP HR infotypes — what each can and cannot feed into birthright selectors. Optionally draft a multi-entity matrix: Entity A (corporate) authoritative = Workday; Entity B (acquired thrift) authoritative = `MNB-SAP-HR` with population filter on company code.

---

## Summary

- SAP HR/HCM is people and org data — never a substitute for ECC role governance or for Lesson 12's finance entitlement CSV.
- RFC/BAPI connectivity with a least-privilege RFC user and a PERNR bridge are the production prerequisites; `SAP_ALL` is not a shortcut.
- Coexistence with `MNB-HR` / Workday requires explicit authoritative segmentation; `RR-SAP-PERNR-01` owns the bridge failure mode.

---

**Previous:** [Lesson 77 — Workday HCM Connector](77-workday-hcm-connector.md)  
**Next:** [Lesson 79 — SAP Direct Security](79-sap-direct-security.md)
