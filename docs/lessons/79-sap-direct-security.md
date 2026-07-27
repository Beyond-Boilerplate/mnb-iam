# Lesson 79 — SAP Direct Security Connector

**Level:** Intermediate  
**Track:** Connectors — ERP / HR / Banking  
**Time:** 90–120 min  
**Prereq:** Lesson 78 — SAP HR/HCM Connector; Lesson 12 — Onboard SAP Finance (`MNB-SAP-Finance` CSV)  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (SAP ECC security row)
- Repo: `lab-data/apps/MNB-SAP-Finance.csv` (legacy file extract for contrast)
- Repo: `lab-data/connectors/features-string-glossary.md`

---

## Learning objectives

You will be able to:

- Explain the SAP security object model (users, roles, profiles, composites) and why a role is an IIQ **entitlement**
- Perform the real-world setup: least-privilege RFC user for security aggregation — without granting the connector `SAP_ALL`
- Create **MNB-SAP-Direct** with a risk-tiered role dictionary including `SAP_ALL` and Meridian `Z*` roles
- Upgrade Meridian from the Lesson 12 CSV extract (`SAP_FI`) to native role aggregation, with a documented retirement plan (same pattern as Lesson 76 for AWS CSV)
- Surface the real toxic-pair story for `jordan.reed` — and design SoD / leaver evidence on native roles

---

## Why this matters

**Business.** In Lesson 12 you governed a single entitlement code `SAP_FI` from a file. Real SAP access is not one code — it is hundreds of roles and profiles: `SAP_ALL`, `Z_FI_POST`, `Z_FI_APPROVE`, Basis roles, security-admin roles. When `jordan.reed` holds both finance posting power and cloud admin (`AWS_ADMIN` from Lesson 13 / native AWS in Lesson 76), the SoD story only works if IIQ can see the **actual** SAP roles, not a quarterly spreadsheet that says "SAP_FI."

**Control / audit.** Examiners test whether toxic SAP combinations are detectable continuously. A CSV that refreshes monthly certifies fiction between extracts — the same failure mode Lesson 76 called out for AWS. Native SAP Direct aggregation feeds SoD engines (Lessons 39–41) with Task Results as evidence; stale `MNB-SAP-Finance` does not.

---

## Concepts

### Users, roles, profiles — what you are governing

SAP ABAP security for people looks like this:

| SAP object | What it is | Governance treatment |
| --- | --- | --- |
| **User (SU01)** | Dialog / system / service user in a client | The **account** IIQ aggregates |
| **Single role** | Bundle of authorization objects | **Entitlement** |
| **Composite role** | Role that contains other roles | **Entitlement** (often what humans are assigned) |
| **Profile** | Generated authorization set behind roles | Usually secondary; prefer role-level governance |
| **`SAP_ALL` / `SAP_NEW`** | Super-user profiles/roles | Critical — break-glass only, never standing |
| **Customer `Z*` / `Y*` roles** | Meridian-built finance/ops roles | The real SoD vocabulary |

Real-life anchor: Lesson 12's `SAP_FI` was a **label** standing in for "can post in finance." In production that label expands into roles such as `Z_FI_POST` and `Z_FI_APPROVE`. Dual control dies if one person holds both — exactly the SoD pair you will draft in Task 7.

### Role as entitlement — why not a string attribute

A SAP role assignment is discrete, grantable, revocable, and access-bearing. Model roles as a **multi-valued entitlement attribute** so each role becomes a `ManagedAttribute`: risk-rated, certifiable, removable via provisioning plan. Treat roles as a plain string and you get no catalog entry, no certification line item, and no revoke button — when the examiner asks who reviewed `Z_FI_APPROVE` this year, you have nothing.

### `SAP_ALL` is the finding, not the baseline

Well-run systems never leave `SAP_ALL` on dialog users. When the first native aggregation shows `SAP_ALL` (or a Basis god-role) on anyone other than a controlled break-glass ID, that row is the value of the connector. Your dictionary marks it **critical / non-requestable**.

### This is not SAP HR

Lesson 78's `MNB-SAP-HR` answers *who works here* (PERNR, org). This lesson's `MNB-SAP-Direct` answers *what they can do in ECC*. Mixing them produces certifications that confuse payroll attributes with posting authority — an examiner trap.

```
Human access to SAP at Meridian
   ├── Legacy CSV SAP_FI (Lesson 12)     → MNB-SAP-Finance (retire after dual-run)
   ├── Native roles/profiles (this lesson) → MNB-SAP-Direct aggregates them
   └── HR master data (Lesson 78)          → MNB-SAP-HR — not an entitlement source
```

### Jordan's toxic pair — upgraded

| Persona | employeeId | Lesson 12 CSV | Native Direct (this lesson) | Cloud side |
| --- | --- | --- | --- | --- |
| `jordan.reed` | MNB00092 | `SAP_FI` active | `Z_FI_POST` + residual risk of broader grants | `AWS_ADMIN` / IAM admin story |
| `marcus.approve` | (approver persona) | — | `Z_FI_APPROVE` only | — |
| `samir.hassan` | MNB00094 | `SAP_FI` disabled | locked / role residual teaching | — |
| `toxic.user` | lab-only | — | POST + APPROVE on one user | teaching SoD |

The CSV could only say Jordan had `SAP_FI`. Native aggregation tells you *which* finance powers — and whether he also collected `SAP_ALL` during an incident.

---

## How it works

The SailPoint **SAP Direct** (SAP — Direct) connector uses **RFC** to an ABAP system to read users and role assignments, and optionally to provision role assign/remove and user lock — gated by `featuresString` and the RFC user's authorizations.

```
IdentityIQ (MNB-SAP-Direct)
        │  RFC user (security-read / later provision)
        ▼
SAP ABAP (ECC / S/4)
        ├── User list + lock status          → accounts
        ├── Role / profile assignments       → entitlements
        └── (provisioning) role assign/remove, lock/unlock
```

| Operation | SAP / RFC behavior | IIQ behavior |
| --- | --- | --- |
| Account aggregation | List users in client | Account per SAP user; user id as native identity |
| Entitlement aggregation | Roles (and profiles per design) | ManagedAttributes; memberships on accounts |
| Role revoke | Remove role assignment | Entitlement remove in provisioning plan |
| Disable / lock | Lock user | ENABLE-style operation if featured |

**Matrix:** SAP ECC security → preferred **SAP - Direct**; do **not** use SAP HR/HCM for roles.

Authentication note: the connector RFC user for **aggregation** needs user/role display authorizations. For **provisioning**, it needs role-assignment and lock authorizations — still not `SAP_ALL`. A writable security connector is itself a privileged system; phase writes like Lesson 76 phased IAM policy.

---

## Real-world setup (outside IIQ)

### Step 1 — RFC destination for security

1. Obtain SID, client, host/message server, system number from BASIS (may share host with HR system or be a different client — document which).
2. Confirm network path from IIQ/IQService to the gateway.

### Step 2 — Least-privilege RFC user (security)

1. Create system user `RFC_IIQ_SEC` — separate from Lesson 78's `RFC_IIQ_HR` when possible (blast-radius separation).
2. Phase 1 role: display users, roles, profiles, assignments — enough to aggregate.
3. Phase 2 (provisioning): add role assign/remove and user lock — security-reviewed, named objects only.
4. **Never** assign `SAP_ALL` to the connector user. If someone suggests it "temporarily," that is the finding.

### Step 3 — Guardrails

1. Deny the RFC user the ability to modify its own roles or unlock break-glass admins without dual control (BASIS design).
2. Alert on RFC logons from unexpected hosts; rotate password/SNC credentials on schedule.

### Step 4 — Governance records

Document: client, RFC user, phase 1/2 status, role dictionary version, CSV coexistence plan, owners `helen.ross` (IAM) and `samir.hassan` (SAP security contact).

---

## Before you start

- [ ] IIQ up; `lab-data/apps/MNB-SAP-Finance.csv` inspected; Lesson 12 Jordan toxic-pair context fresh
- [ ] Lessons 39–40 SoD concepts remembered (design only here unless instructed)
- [ ] Decide path: live SAP sandbox or mock fallback
- [ ] No standing `SAP_ALL` promises in lab without break-glass controls
- [ ] Personas: `jordan.reed`, `amelia.brooks`, `marcus.approve`, `samir.hassan`

---

## Lab procedure

### Task 1 — Contrast: what the CSV can never tell you

Ground the upgrade in specifics — same teaching move as Lesson 76 Task 1 for AWS.

1. Open `~/iiq-lab-data/apps/MNB-SAP-Finance.csv`. List what it contains: `userName`, `email`, `employeeId`, single `entitlement` (`SAP_FI`), `accountStatus` — **8** data rows including `jordan.reed` active and `samir.hassan` disabled.
2. List what it structurally *cannot* contain: distinct roles (`Z_FI_POST` vs `Z_FI_APPROVE`), composites, `SAP_ALL`, profiles, anything newer than the last export.
3. Write the upgrade rationale: native aggregation closes the stale-extract gap and makes SoD evaluable on real roles.
4. Coexistence plan: CSV app stays until two clean native aggregation cycles, then retire (Task 8).

**Expected result:** Upgrade rationale paragraph + coexistence plan in the binder.

### Task 2 — Create MNB-SAP-Direct

1. Applications → Add New → **SAP** / **SAP Direct** (or equivalent menu path).
2. Connection: system id / client / RFC user `RFC_IIQ_SEC` / password `"in vault"`.
3. Name: `MNB-SAP-Direct`. Owner: `helen.ross`; SAP security contact: `samir.hassan`.
4. Live sandbox: **Test Connection**.

**Expected result:** Application saved; live path shows Test Connection success.

**If it fails:** Auth object errors → extend phase-1 role with named objects. Wrong client → you may be reading a system without dialog users. Continue mock if no system.

### Task 3 — Schema and role dictionary

1. Account schema: SAP user id (native identity), email/employeeId if available, lock/valid-to flags, multi-valued **roles** marked as the **entitlement attribute** (profiles optional second family if your design requires them).
2. Correlation: prefer `employeeId` when present on the SAP user; fallback `userName` ↔ identity `userName`. Unknown users → uncorrelated (Lesson 19), **create-identities OFF**.
3. Build the Meridian role dictionary:

| Role | Risk | Requestable? | SoD notes |
| --- | --- | --- | --- |
| `SAP_ALL` | critical | No | Break-glass only |
| `SAP_BASIS_ADMIN` | critical | No | Privileged packaging later |
| `SAP_SECURITY_ADMIN` | critical | No | Dual control for grants |
| `Z_FI_POST` | high | Controlled | Toxic with APPROVE |
| `Z_FI_APPROVE` | high | Controlled | Toxic with POST |
| `SAP_FI_POST` / `SAP_FI_APPROVE` | high | Controlled | Align names with older CSV vocabulary if still referenced |
| `SAP_DISPLAY_ONLY` | low | Yes | Read-only |

4. Map Lesson 12's coarse `SAP_FI` → "any of POST family" for retirement messaging — do not pretend one CSV code equals one role.

**Expected result:** Schema with roles as entitlements; dictionary table with SoD pair flagged; create-identities off.

### Task 4 — Mock inventory (fallback: no live SAP)

1. Create `~/iiq-lab-data/connectors/sap/MNB-SAP-Direct-mock.csv`:

```csv
sapUser,email,employeeId,roles,locked
jordan.reed,jordan.reed@meridiannb.com,MNB00092,Z_FI_POST|SAP_DISPLAY_ONLY,false
amelia.brooks,amelia.brooks@meridiannb.com,MNB00098,Z_FI_POST,false
marcus.approve,marcus.approve@meridiannb.com,MNB00007,Z_FI_APPROVE,false
samir.hassan,samir.hassan@meridiannb.com,MNB00094,Z_FI_POST,true
toxic.user,toxic.user@meridiannb.com,MNB00997,Z_FI_POST|Z_FI_APPROVE,false
basis.breakglass,basis.breakglass@meridiannb.com,,SAP_ALL|SAP_BASIS_ADMIN,false
```

2. Shadow **Account Aggregation** via DelimitedFile (pipe-split `roles`).
3. Read findings like an analyst: Jordan holds POST (finance SoR) — pairs with his AWS admin story; Marcus is clean approver-only; toxic.user demonstrates POST+APPROVE; break-glass holds `SAP_ALL` (must not appear in standing manager certs without privileged process); Samir locked with lingering role (leaver residual).

**Expected result:** Six mock accounts aggregated; findings written down.

### Task 5 — Account Aggregation and CSV delta

1. Create `MNB-SAP-Direct-Account-Aggregation`; run live or shadow.
2. Compare entitlement vocabulary vs `MNB-SAP-Finance` — the delta (roles that never existed in the CSV; users present in one side only) is evidence of the drift problem.
3. Spot-check `jordan.reed` cube: native roles visible; note how SoD will evaluate `Z_FI_POST` rather than the blob `SAP_FI`.

**Expected result:** Task Result + written delta note vs the CSV app.

### Task 6 — Provisioning and leaver storyboard

1. Check `features-string-glossary.md` / connector registry: expect `PROVISIONING` and often `ENABLE` (lock) — confirm for your version.
2. Storyboard termination / toxic remediation for a finance user, in order:
   1. **Remove toxic / sensitive roles** (`Z_FI_POST`, `Z_FI_APPROVE`, anything critical) — access gone even if lock stalls.
   2. **Lock the SAP user** — dialog logon dead.
   3. **Re-aggregate** — evidence: roles absent, locked=true.
3. Tie to Lesson 47 evidence chain: provisioning plan + Task Result + account detail.

**Expected result:** Leaver/remediation storyboard with lock step explicit.

### Task 7 — SoD design touchpoint

1. Draft policy name `MNB-SOD-SAP-FI-POST-APPROVE` (do **not** activate unless instructed).
2. Entitlements: `Z_FI_POST` vs `Z_FI_APPROVE` (and legacy aliases if still in dictionary).
3. Owner `helen.ross`; severity high; compensating detection path uses native aggregation.
4. Note Jordan's cross-app toxic pair (`Z_FI_POST` + AWS admin) is a *separate* policy family — same person, two rails (Lessons 13/76).

**Expected result:** Draft SoD policy card + cross-app note.

### Task 8 — CSV retirement plan and residual risk

1. Retirement plan for `MNB-SAP-Finance` (mirror Lesson 76's AWS CSV retirement): after two clean native cycles, mark CSV app inactive, migrate certifications to `MNB-SAP-Direct`, archive final CSV Task Result, delete the export cron.
2. Record `RR-SAP-COMPOSITE-01`: *If aggregation includes only single roles and Meridian assigns composites, effective access may be under-reported. Compensating control: include composite roles in scope or explode composites in a controlled report.* Owner: `samir.hassan`.
3. Record `RR-SAP-ALL-01`: *Holders of `SAP_ALL` can alter security between aggregations. Compensating controls: break-glass process, critical-tier cert, BASIS audit-log review.* Owner: `samir.hassan`.

**Expected result:** Retirement plan + both RRs logged.

### Task 9 — Examiner drill

*"Show toxic SAP access detection path."*

Write end-to-end: Direct aggregation → role entitlements on cube → SoD policy `MNB-SOD-SAP-FI-POST-APPROVE` → violation work item → remediation (role remove) → re-agg evidence. For Jordan, add the cross-system sentence: finance role on `MNB-SAP-Direct` plus cloud admin on AWS must both clear.

**Expected result:** Path written end-to-end in the binder.

---

## Acceptance criteria

- [ ] Upgrade rationale and CSV coexistence/retirement plan written (Lesson 12 → Direct)
- [ ] Real-world RFC least-privilege setup understood (no `SAP_ALL` on connector user)
- [ ] `MNB-SAP-Direct` created; roles as entitlements; dictionary with SoD pair and `SAP_ALL`
- [ ] Aggregation evidence (live or mock) with Jordan / toxic / break-glass findings
- [ ] Leaver storyboard + draft SoD card + examiner path
- [ ] `RR-SAP-COMPOSITE-01` and `RR-SAP-ALL-01` recorded

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Roles missing / only singles | Composites not in aggregation scope | Include composite roles or explode per design (`RR-SAP-COMPOSITE-01`) |
| RFC user locked | Failed logons / password policy | Coordinate with BASIS; use Shadow path for class |
| Toxic combo not detected | SoD policy not built/active or wrong entitlement names | Align dictionary names; activate per Lesson 39 patterns when ready |
| CSV still certified | Campaign still scoped to `MNB-SAP-Finance` | Repoint certs to `MNB-SAP-Direct`; finish retirement |
| User lock not working | ENABLE / lock feature absent or RFC lacks auth | Confirm featuresString; role remove + manual lock with RR |
| Connector "needs SAP_ALL" | Lazy BASIS response | Push back; add named auth objects only — document the refusal |

---

## Training binder evidence

- Upgrade rationale + delta note vs `MNB-SAP-Finance`
- RFC setup worksheet (phase 1/2 — no passwords)
- Role dictionary + aggregation Task Result + findings write-up
- Leaver storyboard, SoD draft, examiner path
- CSV retirement plan + `RR-SAP-COMPOSITE-01` + `RR-SAP-ALL-01`

---

## Knowledge check

1. What Meridian application name governs SAP security roles?
2. Why must SAP roles be entitlements rather than a plain attribute?
3. Which two Meridian roles form the dual-control SoD pair in this lab?
4. What made the Lesson 12 CSV unacceptable as a long-term control, in one sentence?
5. Why is SAP HR the wrong connector for ECC roles?
6. Why must the connector RFC user not receive `SAP_ALL`?

### Answers

1. `MNB-SAP-Direct`.
2. Entitlements become ManagedAttributes — certifiable, risk-rated, revocable; plain attributes get none of that.
3. `Z_FI_POST` vs `Z_FI_APPROVE` (aliases `SAP_FI_POST` / `SAP_FI_APPROVE` if used).
4. It collapses real roles into one stale `SAP_FI` label and drifts between extracts — SoD and certs review a fiction.
5. HR/HCM governs people/org master data, not ABAP role assignments.
6. It would make the connector a god credential; least privilege uses named auth objects in phased roles.

---

## Further reading

- [SAP Help Portal — User and Role Administration](https://help.sap.com/) — search "SU01" and "PFCG" for the security model behind users, roles, and profiles.
- [SAP Help Portal — Authorization concept](https://help.sap.com/) — search "authorization objects" and "SAP_ALL" for why super-user access is an audit flashpoint.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search "SAP Direct connector" for aggregation, provisioning, and featuresString details.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — RFC authorization and role-aggregation troubleshooting.
- [ISACA / SOX ITGC literature on SoD](https://www.isaca.org/) — search "segregation of duties SAP" for examiner-oriented framing of POST vs APPROVE style conflicts.
- [FFIEC IT Examination Handbook — Information Security](https://ithandbook.ffiec.gov/) — access control and audit expectations for privileged application roles.

---

## Stretch lab

Map `SAP_BASIS_ADMIN` into privileged access role packaging (Lesson 28) with mandatory manager + security approval and a 24-hour expiry pattern (Lesson 37 break-glass). Then cross-walk `jordan.reed`: list every entitlement on `MNB-SAP-Direct` mock plus his AWS admin story, and draft one combined remediation ticket that clears both rails.

---

## Summary

- `MNB-SAP-Direct` replaces Lesson 12's coarse `SAP_FI` extract with continuous role/profile inventory — including `SAP_ALL` and Meridian `Z*` roles as first-class entitlements.
- The connector RFC user is a security design: least privilege, phased writes, never `SAP_ALL`.
- Jordan's toxic-pair narrative becomes examiner-ready only when native roles feed SoD and the CSV is retired after dual-run evidence.

---

**Previous:** [Lesson 78 — SAP HR/HCM Connector](78-sap-hr-hcm-connector.md)  
**Next:** [Lesson 80 — PeopleSoft HCM Connector](80-peoplesoft-hcm-connector.md)
