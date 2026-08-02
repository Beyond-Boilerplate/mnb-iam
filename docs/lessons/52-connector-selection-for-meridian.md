# Lesson 52 — Connector Selection for Meridian

**Level:** Intermediate  
**Track:** Connectors  
**Time:** 75–90 min  
**Prereq:** Lesson 51 — Connector Landscape & Registry; `features-string-glossary.md` reviewed  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv`
- Repo: `lab-data/connectors/features-string-glossary.md`
- Homelab copy: `~/iiq-lab-data/connectors/`

---

> **Verify:** Paperwork — connector selection matrix and decision records. Academy **Verify now** is disabled; mark the binder complete when Risk Q&A and CHANGELOG are done.

## Learning objectives

You will be able to:

- Read and extend Meridian’s connector selection matrix CSV as an Architecture contract
- Apply decision criteria: authoritative vs target, `featuresString`, network path, IQService dependency
- Map every priority Meridian system to preferred and alternate connectors with reject reasons
- Justify AD Direct vs LDAP, JDBC vs MSSQL Direct, SCIM vs Web Services
- Produce signed selection records for Risk / Architecture without a live target
- Flag IQService and stored-proc dependencies early so Lesson 53–56 builds do not surprise ops

---

## Why this matters

**Business.** Banks fail connector projects when Architecture picks “LDAP for everything” or “REST for everything.” Meridian’s matrix is the single source of preferred connectors: Corporate AD → Active Directory Direct, Core banking DB → JDBC (or MSSQL Direct), Wire Portal → Web Services. When `jordan.reed`’s team onboarded a new payments API last year using a generic LDAP assumption, password and disable never worked — three weeks of rework before `helen.ross` could sign the go-live.

**Control / audit.** Examiners ask who approved the connector type and whether an alternate was considered. Your completed matrix row plus a selection record (preferred, alternate, reject reason, owner, SLA) is that evidence. “We used what the implementer liked” fails the conversation.

---

## Concepts

### Decision criteria Meridian actually uses

Selection is not a popularity contest. Walk every system through the same criteria:

| Criterion | Question | Meridian implication |
| --- | --- | --- |
| **Authoritative vs target** | Does this system *create* identities or *receive* accounts? | Only `MNB-HR` (and SAP HR / Workday if used) is authoritative; everything else has create-identities **OFF** |
| **`featuresString`** | Do we need ENABLE / PASSWORD / UNLOCK / PROVISIONING? | If yes, DelimitedFile is almost never enough |
| **Network path** | Can IIQ reach the API/DB/directory from the IIQ tier? | Wire Portal and cloud SaaS need egress + secrets; AD Direct needs IQService near DCs |
| **IQService** | Is this Windows/AD/Exchange ops? | Corporate AD → plan Windows host, TLS, least-privilege account (Lesson 53) |
| **Native vs generic** | Is there an OOTB Direct/SaaS connector? | Prefer Salesforce / Okta / AWS IAM native over generic Web Services when available |
| **Provisioning shape** | Stored-proc, SCIM, or raw REST/SQL? | Core banking prefers stored-proc — raw UPDATE is an examiner finding waiting to happen |

**Real-life Meridian example.** Core Banking was almost wired with ad-hoc JDBC `UPDATE mnb_app_accounts SET status=…`. Payments risk (`marcus.approve`’s org) rejected it: account state changes must go through the bank’s stored procedures so audit triggers fire. Preferred connector stayed **JDBC**; the *provisioning pattern* became “call proc,” not “run naked SQL.” That decision belongs in the selection record, not in a forgotten Slack thread.

### Authoritative vs target — the create-identities trap

| Role | Meridian apps | create-identities | Why |
| --- | --- | --- | --- |
| **Authoritative** | `MNB-HR` (HRIS extract); future SAP HR / Workday | ON (or HR-only pipeline) | Identities are born here |
| **Target** | AD, Entra, Core Banking, Wire Portal, AWS, Google, SAP security | **OFF** | Accounts correlate to existing cubes; never spawn duplicate people |

The wrong way: turn create-identities on for AD because “we saw empty cubes.” That creates shadow identities on every uncorrelated account and poisons certifications. Fix correlation (Lessons 17–19); do not invent people from targets.

### Preferred vs alternate — always document the reject

Every matrix row has a preferred and an alternate. Selection records must say **why the alternate lost**:

| System | Preferred | Alternate | Typical reject reason |
| --- | --- | --- | --- |
| Corporate AD | Active Directory - Direct | LDAP | LDAP lacks first-class IQService password / Exchange patterns Meridian requires |
| Core banking DB | JDBC | Microsoft SQL Server - Direct | Either can work; Meridian standardizes on JDBC + stored-proc unless MSSQL Direct is mandated |
| Wire Portal API | Web Services | SCIM 2.0 | Portal is custom REST today; SCIM wins if vendor later ships standards-compliant SCIM |
| SCIM-compliant SaaS | SCIM 2.0 | Web Services | Prefer SCIM when vendor supports it — less mapping debt |
| OpenLDAP | OpenLDAP - Direct | LDAP | Lab/generic RFC directory — Direct type when available |

### Meridian portfolio snapshot (from the matrix)

| System (matrix) | Preferred | Alternate | Meridian note |
| --- | --- | --- | --- |
| Corporate AD | Active Directory - Direct | LDAP | Requires IQService for password/enable/Exchange |
| Entra ID / Azure AD | Azure Active Directory | SCIM 2.0 | Cloud directory + SaaS SSO |
| OpenLDAP / FreeIPA | OpenLDAP - Direct | LDAP | Lab directory |
| HRIS extract | DelimitedFile | JDBC | Authoritative file still valid |
| Core banking DB | JDBC | Microsoft SQL Server - Direct | Prefer stored-proc provisioning |
| Wire Portal API | Web Services | SCIM 2.0 | Custom bank REST |
| Salesforce CRM | Salesforce | Web Services | Native SFDC connector |
| SAP ECC security | SAP - Direct | SAP HR/HCM | App security vs HR authoritative |
| Okta | Okta | SCIM 2.0 | Workforce IdP |
| AWS IAM | AWS IAM | AWS | Cloud IAM roles/users |
| Office 365 | Microsoft Office365 | Azure Active Directory | Mailbox / M365 |
| Mainframe RACF | RACF - Full | RACF LDAP | Banking core security |

---

## How it works

```text
  Business system inventory (owners, SLAs, auth vs target)
        │
        ▼
  connector-selection-matrix.csv
        ├── preferredConnector  (build this)
        ├── alternate           (fallback / PoC)
        └── notes               (IQService, procs, SCIM, network)
        │
        ▼
  Selection record (this lesson)
        ├── features required (from Lesson 51)
        ├── network / IQService flags
        └── Risk + Architecture sign-off
        │
        ▼
  MNB-* Application build (Lessons 56+)
```

| Artifact | Owner | Purpose |
| --- | --- | --- |
| `connector-selection-matrix.csv` | Architecture / IAM | System → connector contract |
| Selection record (`MNB-connector-selection-record-52.md`) | IAM lead (`helen.ross`) | Preferred, alternate, reject, SLA, live-target flag |
| Lesson 51 features worksheet | IAM engineer | Capability ceiling per type |
| Application object | IAM build | Implements the signed choice |

---

## Before you start

- [ ] Lesson 51 worksheet (`MNB-features-worksheet-51.txt`) available
- [ ] `~/iiq-lab-data/connectors/connector-selection-matrix.csv` present
- [ ] CHANGELOG (or training binder log) open for selection decisions
- [ ] Know owners: IAM operates; app owners vary (Technology, Payments, HR)
- [ ] Personas in mind: `helen.ross` (IAM), `marcus.approve` (approvals/risk), `priya.wire` (wire access)

---

## Lab procedure

### Task 1 — Load and validate the matrix

Treat the CSV as a controlled document. If columns drift, every downstream lesson drifts with them.

1. Inspect the CSV:

```bash
head -30 ~/iiq-lab-data/connectors/connector-selection-matrix.csv
wc -l ~/iiq-lab-data/connectors/connector-selection-matrix.csv
```

2. Confirm columns: `system`, `preferredConnector`, `alternate`, `notes`.
3. Count rows (≥20 expected including header). Spot-check: Corporate AD, Entra ID, Core banking DB, Wire Portal, SQL Server, Oracle DB, RACF, Okta, AWS IAM.

**Expected result:** Header valid; key banking systems present; notes column mentions IQService on Corporate AD.

**If it fails:** Copy from `lab-data/connectors/connector-selection-matrix.csv`.

### Task 2 — Map Meridian MNB object names

Selection without naming creates duplicate apps later. Assign intended Application names now — even if the object does not exist yet.

1. Complete:

| Matrix system | Intended Application | Auth vs target |
| --- | --- | --- |
| Corporate AD | `MNB-ActiveDirectory` | Target |
| Entra ID / Azure AD | `MNB-EntraID` | Target |
| OpenLDAP / FreeIPA | `MNB-OpenLDAP` | Target (lab) |
| Core banking DB | `MNB-CoreBanking-JDBC` | Target |
| Wire Portal API | `MNB-WirePortal-WS` | Target |
| SQL Server | `MNB-MSSQL-Reporting` | Target |
| Oracle DB | `MNB-OracleDB` | Target |
| HRIS extract | `MNB-HR` (exists) | **Authoritative** |
| AWS IAM | `MNB-AWS-Cloud` | Target |
| Okta | `MNB-Okta` | Target (IdP) |
| SAP ECC security | `MNB-SAP-Finance` | Target |

2. Add curriculum bridges: `MNB-IT-Access` → DelimitedFile inventory (not a long-term Direct path).

**Expected result:** Mapping table with ≥10 `MNB-*` names and auth/target flags.

### Task 3 — Apply the decision worksheet (criteria pass)

For three priority systems, force every criterion into writing. This is the heart of the lesson.

1. For **Corporate AD**, **Core banking DB**, and **Wire Portal API**, fill:

| Field | AD | Core Banking | Wire Portal |
| --- | --- | --- | --- |
| Auth vs target | | | |
| Required features | | | |
| Network path | | | |
| IQService? | | | |
| Preferred / alternate | | | |
| Reject reason | | | |
| Owner / SLA | | | |

2. Expand AD notes into design bullets: IQService host, TLS, password, Exchange yes/no.
3. For Core banking: document “prefer stored-proc provisioning” and why raw UPDATE is risky.
4. For Wire Portal: note OpenAPI fixture path `webservices/wire-portal-openapi.yaml` for later lessons.
5. Flag Privileged vault (CyberArk) as Advanced track (Lesson 86) — not this sprint.

**Expected result:** Three completed criteria worksheets; AD IQService dependency explicit; Core Banking proc note; Wire OpenAPI path recorded.

### Task 4 — Lab without live target — selection decision records

Produce the artifact Architecture would file. Live target availability is a field on the record — not a blocker for training.

1. Create `~/iiq-lab-data/connectors/MNB-connector-selection-record-52.md` with at least three records in this shape:

```text
System: Corporate AD
Preferred: Active Directory - Direct
Alternate: LDAP
Rejected alternate because: LDAP lacks first-class IQService password/Exchange patterns Meridian requires
Required features: PROVISIONING, ENABLE, PASSWORD, UNLOCK
IQService: YES — Windows host near DCs, TLS (Lesson 53)
Owner: Technology / IAM operate (helen.ross)
SLA: Disable within 4h of leaver HR event
Live target available now: NO
Build path: Application shell + checklist (Lesson 56)
```

2. Repeat for Core banking DB and Wire Portal API.
3. Optionally add AWS IAM or Okta as a fourth record using the matrix.

**Expected result:** ≥3 decision records on disk; each names preferred, alternate, reject reason, features, SLA, live-target flag.

**If it fails:** Use CSV notes column as reject/accept rationale; still write full records.

### Task 5 — Risk sign-off simulation

Practice the examiner / Risk conversation before you build.

1. Role-play: Risk (`marcus.approve` persona) asks “Why not LDAP for AD?”
2. Answer from matrix + Lesson 51 features (PASSWORD/ENABLE via IQService path).
3. Second challenge: “Why not DelimitedFile for Wire Portal?” — answer with leaver disable SLA and API reality.
4. Record both Q&As in the binder as examiner rehearsal.

**Expected result:** Two written Q&A paragraphs.

### Task 6 — Update CHANGELOG / binder log

Selection without a paper trail is not selection.

1. Add entry: “Lesson 52: Meridian connector selection matrix reviewed; MNB app name map + selection records created.”
2. Do **not** create live Application objects yet unless they already exist — this lesson is selection only.

**Expected result:** CHANGELOG / binder line dated today; no scope creep into Lesson 56 builds.

### Task 7 — Residual selection risks

Honest programs record what the matrix does not solve.

1. Log at least two residual risks, e.g.:
   - `RR-CONN-SEL-01`: Wire Portal SCIM alternate remains aspirational until vendor ships SCIM — Web Services mapping debt accepted.
   - `RR-CONN-SEL-02`: Core Banking stored-proc ownership sits with DBA team; IAM blocked if procs are not ready before ENABLE go-live.
2. Owner each risk (`helen.ross` or app owner).

**Expected result:** Residual risks logged with owners.

---

## Acceptance criteria

- [ ] Matrix CSV validated (columns + key systems)
- [ ] ≥10 systems mapped to `MNB-*` names with auth/target flags
- [ ] Criteria worksheets for AD, Core banking, Wire Portal complete
- [ ] ≥3 lab-without-live-target decision records written
- [ ] Risk Q&A (two challenges) + CHANGELOG updated
- [ ] Residual selection risks logged

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| CSV truncated | Bad copy | Re-copy from repo `lab-data/connectors/` |
| Duplicate MNB names | Naming collision | Follow Lesson 03; suffix `-JDBC` vs `-Direct` |
| Prefer SCIM vs WS unclear | Vendor capability unknown | Prefer SCIM when vendor supports; else Web Services; mark Unknown |
| Skipping alternate column | Incomplete ADR | Always document alternate + reject reason |
| Building apps early | Scope creep | Shells start Lesson 56+; this lesson is selection only |
| create-identities ON for AD | Auth vs target confusion | Targets stay OFF; fix correlation instead |

---

## Training binder evidence

- Printed or screenshot of matrix header + AD / Core banking / Wire rows
- `MNB-connector-selection-record-52.md`
- MNB name mapping table (auth vs target)
- Risk Q&A rehearsal + residual risks

**Examiner question:** “Show the approved connector type for Core Banking and the alternate you rejected.”

---

## Knowledge check

1. Preferred connector for Corporate AD at Meridian?
2. Why does the matrix list IQService in AD notes?
3. Preferred vs alternate for Core banking DB, and what provisioning shape does Meridian prefer?
4. When do you prefer SCIM 2.0 over Web Services?
5. Is live AD required to complete this lesson’s acceptance criteria?
6. Why must create-identities stay OFF for `MNB-ActiveDirectory`?

### Answers

1. Active Directory - Direct.
2. Password, enable/disable, and often Exchange mailbox ops depend on IQService near the domain.
3. Preferred JDBC; alternate Microsoft SQL Server - Direct; prefer stored-proc provisioning over raw UPDATE.
4. When the vendor exposes standards-compliant SCIM; otherwise map REST with Web Services.
5. No — lab-without-live-target decision records are sufficient.
6. AD is a target; identities are born from authoritative HR. Creating identities from AD produces uncorrelated/shadow cubes.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search your version’s connector guides for Active Directory Direct, JDBC, Web Services, and SCIM; use them to validate preferred types before signing records.
- [SailPoint Community (Compass)](https://community.sailpoint.com/) — search “Active Directory vs LDAP connector” and “IQService” for field experience on when LDAP is insufficient.
- [SCIM 2.0 overview (RFC 7644)](https://datatracker.ietf.org/doc/html/rfc7644) — why Meridian prefers SCIM when a SaaS vendor supports it.
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/) — relevant when selecting Web Services for Wire Portal (auth, object-level authz, excessive data exposure).
- [NIST SP 800-53 Rev. 5](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — AC-2 / AC-3 framing for why connector selection is an access-control design decision, not only an integration convenience.

---

## Stretch lab

- Add a matrix row for a fictional `MNB-MobileBanking` API and choose Web Services vs SCIM with justification.
- Cross-check every matrix preferred type against Lesson 51 feature promises for ENABLE/PASSWORD.
- Draft an Architecture Decision Record (ADR) one-pager referencing the CSV path and the three selection records.

---

## Summary

- Meridian’s `connector-selection-matrix.csv` is the system→connector contract; selection records add reject reasons, features, SLAs, and IQService flags.
- Decision criteria (auth vs target, featuresString, network, IQService) prevent “LDAP for everything” failures.
- Live targets are optional; signed records unlock later connector labs without promising impossible controls.

---

**Previous:** [Lesson 51 — Connector Landscape & Registry](51-connector-landscape-and-registry.md)  
**Next:** [Lesson 53 — IQService Architecture](53-iqservice-architecture.md)
