# Lesson 82 — Mainframe RACF for Banking

**Level:** Intermediate  
**Track:** Connectors — ERP / HR / Banking  
**Time:** 90–120 min  
**Prereq:** Lesson 81 — Oracle E-Business Suite Connector; Lesson 11 (`MNB-CoreBanking` CSV) for business context  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (row: Mainframe RACF)
- Repo: `lab-data/apps/MNB-CoreBanking.csv` (Lesson 11 business extract — contrast)
- Repo: `lab-data/connectors/features-string-glossary.md`
- Runtime: `~/iiq-lab-data/connectors/`

---

## Learning objectives

You will be able to:

- Explain why **RACF** is Meridian’s privileged control plane for mainframe / core banking security (USERID, GROUP, DATASET / FACILITY profiles)
- Select **RACF - Full** vs **RACF LDAP** per the connector matrix and defend the choice
- Contrast Lesson 11’s `MNB-CoreBanking` CSV (business context) with production reality: **RACF, not CSV**, gates CICS/DB2/batch
- Create **MNB-RACF-Core** with a defensible entitlement model and run Account Aggregation (live or mock)
- Design joiner / leaver expectations for core ops IDs, including SPECIAL / OPERATIONS as break-glass
- Answer the examiner question: *who can alter production CICS/DB2 security?*

---

## Why this matters

**Business.** Meridian’s deposit, loan, and settlement batches still depend on mainframe CICS regions and DB2 subsystems. In Lesson 11 you governed a `CORE` entitlement from a file extract — useful for teaching ownership and aggregation. Here is why that is not enough in production: the CSV does not decide whether `jordan.reed` can update a production CICS transaction or bind a DB2 plan. **RACF** does. Wrong permit = fraud window or settlement outage.

**Control / audit.** Regulators treat mainframe security as critical infrastructure. Saying “we have CoreBanking CSV in IIQ” fails when RACF groups that gate production regions are unmanaged. The examiner question is precise: *Who can alter production CICS/DB2 security, how do you inventory them continuously, and how do you prove a leaver’s USERID is REVOKEd?* This lesson connects IdentityIQ to that control plane — without requiring a live LPAR for the lab path.

---

## Concepts

### The RACF object model

Before touching IIQ, understand what RACF actually stores:

| RACF object | What it is | Governance treatment |
| --- | --- | --- |
| **USERID** | The mainframe identity (often ops-style, not always equal to Windows UPN) | The account IIQ aggregates |
| **GROUP** (connect group) | Named set of users sharing access; connect/remove is the common grant path | **Entitlement** (like an AD group) |
| **DATASET profile** | Access rules for datasets (HLQ, production libraries) | Entitlement or residual risk if not in connector scope |
| **FACILITY / other class profiles** | Resource rules (often CICS, DB2, started tasks) | Entitlement when modeled; else compensating review |
| **SPECIAL** | RACF attribute: user can administer security | Break-glass — never birthright |
| **OPERATIONS** | RACF attribute: bypasses many access checks | Break-glass — never birthright |
| **REVOKE** | User cannot enter the system | Leaver primitive |

Real-life anchor: when `jordan.reed` runs overnight batch under `MNB_BATCH_OPS`, that is **group connect**. When someone holds `SPECIAL`, they can change who else has that power — that is why SPECIAL is treated like a vaulted break-glass ID, not a role you request for a project.

### Lesson 11 CSV vs production RACF

```
Lesson 11 — MNB-CoreBanking (Delimited File)
   └── Business extract: who has "CORE" on the midrange narrative
         useful for ownership + cert practice
         NOT the security plane

Production — MNB-RACF-Core (RACF - Full)
   └── Security plane: USERID + groups + profiles
         gates CICS regions, DB2, batch
         continuous aggregation closes extract drift
```

Keep both objects during migration if needed, but never tell an examiner they are the same control. The CSV is business context; RACF is enforcement.

### RACF - Full vs RACF LDAP

| Connector | What it talks to | Meridian use |
| --- | --- | --- |
| **RACF - Full** | Native RACF administration interfaces / approved mainframe connector path | **Preferred** for banking core |
| **RACF LDAP** | LDAP projection of RACF identities/groups | Alternate only if directory projection is the *approved* integration and covers required attributes |

LDAP projections are convenient and often incomplete (missing attributes, delayed sync, no SPECIAL visibility). Default Meridian standard: **RACF - Full**; document LDAP as alternate with explicit coverage gaps.

### SPECIAL / OPERATIONS are break-glass

Treat SPECIAL and OPERATIONS like Lesson 37 break-glass: dual approval, short sunset, vaulted credentials, monthly privileged certification. Birthright roles must never assign them. Aggregation that shows SPECIAL on a standing ops ID is a finding, not a feature.

---

## How it works

The SailPoint **RACF - Full** connector (labels vary by version — use your Application guide) inventories USERIDs and group connects, and may surface selected profile classes depending on configuration. IIQ does **not** replace the RACF administrator; it governs who holds what and drives joiner/leaver workflows against that inventory.

```
IdentityIQ (MNB-RACF-Core)
        │  connector credentials / secure channel to LPAR tooling
        ▼
RACF (production sysplex / LPAR scope)
        ├── LISTUSER / user inventory     → accounts (USERID)
        ├── group connects                → group entitlements
        ├── DATASET / FACILITY (if scoped)→ profile entitlements
        └── ALTUSER REVOKE / CONNECT      → leaver / entitlement change
                 │
                 ▼
        CICS / DB2 / batch (enforcement outside IIQ)
```

| Operation | RACF-side idea | IIQ behavior |
| --- | --- | --- |
| Account aggregation | Inventory USERIDs in scope | Account per USERID, native identity |
| Entitlement aggregation | Group connects (+ profiles if modeled) | Managed attributes on accounts |
| Joiner | Define user + default group + connects | Create + entitlement add |
| Leaver | REVOKE + remove production connects | Disable / modify plan |
| Break-glass | SPECIAL / OPERATIONS | Privileged request path only |

Authentication and network to the LPAR are bank-specific (TN3270 gateways, approved APIs, MQ, etc.). Lab never invents production hostnames or passwords — worksheet + mock only unless you have a sanctioned non-prod.

---

## Real-world setup (outside IIQ)

### Step 1 — Scope and owners

1. Name the LPAR / sysplex scope for production core (and separate nprod apps if needed).
2. Control owners: Mainframe Security (technical), Platform Ops (ops IDs), IAM (governance). Application owner on `MNB-RACF-Core` is Technology / Mainframe Security — not “whoever owns the CSV.”

### Step 2 — Connector principal

1. Create a dedicated connector USERID (or approved service identity) with **least privilege** to list users/groups and, for phase 2 only, CONNECT/REMOVE and REVOKE within scoped groups.
2. Deny the connector the ability to grant SPECIAL/OPERATIONS to itself (guardrail).
3. Vault credentials; rotate per mainframe standard; no shared human admin IDs.

### Step 3 — Network and change control

1. IIQ task servers → approved mainframe integration endpoint; firewall owned by Platform Ops.
2. All write operations go through change tickets for production until phase 2 is formally approved.
3. CloudTrail-equivalent on the mainframe side: SMF / RACF audit for connector activity — document who reviews it.

### Step 4 — Governance records

Document: preferred connector **RACF - Full**, LDAP alternate rationale (if any), group catalog, SPECIAL inventory process, coexistence plan with `MNB-CoreBanking` CSV.

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq` as `spadmin`
- [ ] Matrix CSV available; skim `lab-data/apps/MNB-CoreBanking.csv` for Lesson 11 contrast
- [ ] Privileged-access / break-glass notes (Lessons 28 / 37) available for SPECIAL handling
- [ ] Decide path: sanctioned non-prod RACF **or** mock fallback in Task 4
- [ ] Binder: `connectors/racf/`

---

## Lab procedure

### Task 1 — Contrast: CSV business context vs RACF enforcement

Ground the upgrade before building it.

1. Open `~/iiq-lab-data/apps/MNB-CoreBanking.csv` (or repo copy). Note what it contains (business `CORE` holders) and what it structurally *cannot* contain: RACF GROUP connects, DATASET/FACILITY permits, SPECIAL/OPERATIONS, REVOKE state, anything newer than the last export.
2. Write the production-reality sentence: *Lesson 11 taught governance mechanics on a file; production core security is RACF.*
3. Coexistence: CSV app may remain for business certifications until RACF aggregation is trusted for two clean cycles — then retire or demote the CSV (Task 8).

**Expected result:** Contrast paragraph + coexistence stub in the binder.

### Task 2 — Create MNB-RACF-Core (native primary)

1. Applications → Add New → **RACF** / **RACF - Full** (or equivalent menu path). If missing: Application `MNB-RACF-Core` with connector type “RACF - Full (lab shell)” in Description.
2. Connection: LPAR/sysplex identifiers and connector credentials (lab: placeholders noting “in vault”).
3. Owner: Mainframe Security / Technology Director persona; secondary Platform Ops. **Not authoritative.**
4. Live non-prod: Test Connection if your build supports it.

**Expected result:** `MNB-RACF-Core` saved; decision note states RACF - Full preferred, RACF LDAP alternate only.

**If it fails:** License/pack missing → document LDAP alternate coverage gaps and escalate; do not force unsafe LPAR access from a laptop lab.

### Task 3 — Schema and entitlement taxonomy

1. Account attributes to confirm/document: `USERID` (native identity), `NAME`, `OWNER`, `DFLTGRP`, `SPECIAL`, `OPERATIONS`, `REVOKE` (status), password flags only — never store password values.
2. Entitlement families:
   - **Groups:** `MNB_CICS_PROD_RO`, `MNB_CICS_PROD_UPDATE`, `MNB_DB2_SETTLE`, `MNB_BATCH_OPS`
   - **Profiles (if in scope):** selected DATASET/FACILITY profiles that gate production CICS/DB2 admin — otherwise residual risk
3. Risk-rate: `MNB_CICS_PROD_UPDATE` and any SPECIAL-capable access = critical / non-requestable except break-glass; `MNB_CICS_PROD_RO` = high; batch ops = high with manager + ops approval.
4. Correlation: prefer dedicated identity attribute `mainframeId` ↔ `USERID`; fallback `USERID` ↔ `userName`. Ops IDs that are not HR usernames must not auto-create people.
5. **Create identities: OFF.**

**Expected result:** Schema + group catalog with privilege flags; correlation choice documented.

### Task 4 — Mock inventory (fallback: no LPAR)

1. Create `~/iiq-lab-data/connectors/racf/MNB-RACF-Core-mock.csv`:

```csv
USERID,employeeId,groups,SPECIAL,OPERATIONS,REVOKE
HELENR,MNB00091,MNB_CICS_PROD_RO,false,false,false
JORDANR,MNB00092,MNB_BATCH_OPS|MNB_CICS_PROD_UPDATE,false,false,false
KAINGU,MNB00096,MNB_CICS_PROD_RO,false,false,false
MFADMIN,,MNB_CICS_PROD_UPDATE,true,false,false
LEAVER1,MNB00094,,false,false,true
```

2. Shadow-aggregate via DelimitedFile (pipe-split groups). Description must say proxy/mock.
3. Analyst read: Jordan holds production CICS **UPDATE** (privileged); `MFADMIN` has SPECIAL with no employeeId (break-glass / shared admin — inventory, don’t certify as a normal human); `LEAVER1` already REVOKEd (leaver evidence pattern); Kai has RO only (expected for engineer without prod update birthright).

**Expected result:** Five mock accounts aggregated; findings written (Jordan UPDATE, MFADMIN SPECIAL, leaver REVOKE).

### Task 5 — Account Aggregation

1. Create `MNB-RACF-Core-Account-Aggregation`; run live or shadow.
2. Compare against Lesson 11 CORE roster where names overlap — deltas (in RACF not CSV / vice versa) are evidence of why CSV alone fails.
3. Flag any SPECIAL=true rows into a privileged population note.

**Expected result:** Task Result + written delta note vs `MNB-CoreBanking`.

### Task 6 — Joiner / leaver for core ops IDs

1. **Joiner (ops):** HR cube exists → request path for `MNB_BATCH_OPS` or RO groups → create/connect USERID → aggregate verify. Engineers (`kai.nguyen`) do **not** receive `MNB_CICS_PROD_UPDATE` by birthright.
2. **Leaver:**
   1. Remove production group connects (CICS UPDATE, DB2 settle, batch).
   2. Set **REVOKE** on USERID same day.
   3. If SPECIAL/OPERATIONS present: Mainframe Security ticket within **1 hour** SLA (break-glass kill switch).
   4. Re-aggregate — evidence: REVOKE=true, production groups empty.
3. Map personas: `jordan.reed` may need batch; `kai.nguyen` stays RO unless break-glass ticket.

**Expected result:** Joiner card + four-step leaver card with SPECIAL SLA highlighted.

### Task 7 — Examiner question drill

*"Who can alter production CICS/DB2 security?"*

Write the answer as an evidence chain:

1. Entitlement catalog / aggregation showing holders of `MNB_CICS_PROD_UPDATE`, `MNB_DB2_SETTLE`, and any FACILITY/DATASET admin profiles in scope.
2. SPECIAL/OPERATIONS inventory (privileged cert or break-glass log) — these users can *change the security definitions*, not only use the apps.
3. Latest `MNB-RACF-Core` Account Aggregation Task Result as continuous inventory proof.
4. Explicitly state what Lesson 11 CSV does **not** prove.

**Expected result:** Written four-point examiner answer in the binder.

### Task 8 — CSV retirement stub and residual risk

1. Retirement/coexistence plan for `MNB-CoreBanking`: after two clean RACF cycles, demote CSV to archival or keep only if business still needs a non-RACF “CORE” narrative — document the decision.
2. Record `RR-RACF-PROF-01`: *DATASET/FACILITY profiles not in connector scope need periodic Mainframe Security export review.* Owner: Mainframe Security.
3. Record `RR-RACF-LDAP-01` if anyone proposes LDAP-only: *LDAP projection may omit SPECIAL/OPERATIONS or profile depth — Full connector remains standard.*

**Expected result:** Retirement stub + residual risks with owners.

---

## Acceptance criteria

- [ ] Lesson 11 vs RACF contrast and coexistence/retirement stub written
- [ ] RACF - Full preferred (LDAP alternate documented); real-world setup understood
- [ ] `MNB-RACF-Core` created; groups (+ optional profiles) as entitlements; create-identities off
- [ ] Aggregation evidence (live or mock) with Jordan / MFADMIN / leaver findings identified
- [ ] Joiner + leaver cards with SPECIAL 1-hour SLA
- [ ] Examiner “who can alter production CICS/DB2 security?” answer + residual risks recorded

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Confusing CoreBanking CSV with RACF | Two different planes | Separate apps; use Task 1 diagram language |
| No RACF - Full licensed | Product pack missing | Document LDAP gaps; escalate — don’t pretend coverage |
| SPECIAL users in birthright roles | Role mistake | Move to break-glass request path (Lessons 28/37) |
| Correlation orphans | Dedicated ops USERIDs | `mainframeId` attribute + manual correlate; create-identities off |
| Live test blocked | Network / LPAR policy | Worksheet + mock path; never force unsafe access |
| “Engineer needs PROD UPDATE” standing grant | Birthright creep | Time-bound break-glass only; certify monthly |

---

## Training binder evidence

- CSV vs RACF contrast + architecture ASCII
- Connector decision (Full vs LDAP) + setup worksheet (no secrets)
- Aggregation Task Result + findings (Jordan UPDATE, MFADMIN SPECIAL, REVOKE row)
- Joiner/leaver cards with SPECIAL SLA
- Examiner Q&A + `RR-RACF-PROF-01` / LDAP residual if used

---

## Knowledge check

1. Why is `MNB-CoreBanking` CSV insufficient as Meridian’s mainframe security control?
2. Preferred vs alternate connector for Mainframe RACF per Meridian matrix?
3. Why are SPECIAL and OPERATIONS treated as break-glass?
4. What leaver actions are mandatory for a production USERID?
5. How do you answer “who can alter production CICS/DB2 security?” with evidence?
6. Why must create-identities stay off for `MNB-RACF-Core`?

### Answers

1. It models a business entitlement extract; RACF is the enforcement plane for CICS/DB2/batch — CSV cannot show groups, profiles, SPECIAL, or continuous REVOKE state.
2. Preferred: RACF - Full; alternate: RACF LDAP (only if approved and gaps documented).
3. They administer or bypass RACF access controls — standing grants are a critical finding; use dual approval, sunset, and privileged certification.
4. Remove production connects, set REVOKE same day, escalate SPECIAL/OPERATIONS within 1 hour, re-aggregate for evidence.
5. Aggregation of UPDATE/settle/admin entitlements + SPECIAL inventory + latest Task Result; state CSV does not answer this.
6. Unknown or shared mainframe IDs must surface as uncorrelated / non-human inventory, not become people cubes; HR remains authoritative.

---

## Further reading

- [IBM z/OS Security Server RACF documentation](https://www.ibm.com/docs/en/zos/2.5.0?topic=zos-racf) — authoritative USERID, group, profile, and REVOKE concepts; search your z/OS level for “RACF Security Administrator’s Guide.”
- [IBM: RACF general user commands / administration concepts](https://www.ibm.com/docs/en/zos) — use the Docs search for LISTUSER, CONNECT, and REVOKE to align provisioning vocabulary with operators.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “RACF connector” for RACF - Full vs LDAP application guides and featuresString notes.
- [FFIEC Information Security](https://www.ffiec.gov/press/pr090906a.htm) (current FFIEC IT Examination Handbook — Information Security) — examiner lens on privileged access and critical systems.
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks) — use platform benchmarks as hardening input alongside RACF policy; mainframe-specific controls still owned by Mainframe Security standards.

---

## Stretch lab

Map `MNB_CICS_PROD_UPDATE` and SPECIAL holders into a monthly privileged certification population (inclusion rule text only). Then draft the SMF/RACF audit review question Mainframe Security should answer quarterly: *did the IIQ connector USERID perform only approved CONNECT/REVOKE operations?*

---

## Summary

- Production core security is RACF — Lesson 11’s CSV is business context, not the control plane.
- Govern USERID + groups (and profiles where scoped); treat SPECIAL/OPERATIONS as break-glass with a hard leaver SLA.
- Continuous aggregation Task Results plus a clear examiner evidence chain answer who can alter production CICS/DB2 security.

---

**Previous:** [Lesson 81 — Oracle E-Business Suite Connector](81-oracle-ebs-connector.md)  
**Next:** [Lesson 83 — Linux / Unix Connector](83-linux-unix-connector.md)
