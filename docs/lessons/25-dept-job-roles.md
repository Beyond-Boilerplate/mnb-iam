# Lesson 25 — Department & Job-Based Roles

**Level:** Intermediate  
**Track:** Roles  
**Time:** 60–90 minutes  
**Prereq:** Lesson 24 (`MNB-Birthright-Employee`); entitlements DWRP, ODS, CRM, WIRE_INIT available  

**Lab data:**
- `~/iiq-lab-data/reference/job-codes.csv`
- Personas with DEV/RM/WIR01 jobs; dual-control pair `priya.wire` (WIR01) / `marcus.approve` (WIR02)
- Mover preview: `~/iiq-lab-data/scenarios/mover/hr-delta-priya-to-commercial.csv`

---

## Learning objectives

You will be able to:

- Create **`MNB-Role-Developer`** with DWRP + ODS for `DEV01` / `SRE01`
- Create **`MNB-Role-RelationshipManager`** with CRM for `RM01` / `LO01`
- Create **`MNB-Role-WireInitiator`** with WIRE_INIT for **`WIR01` only** (never `WIR02`)
- Assign via HR `jobCode` (and optionally `departmentCode`) and verify after refresh
- Preview why Priya’s mover delta will swap wire → RM packs in Lesson 30
- Prove `marcus.approve` never receives the initiator role (dual control)

---

## Why this matters

**Business.** Most access follows the desk you sit in. When `priya.wire` later moves to commercial banking, HR changes `jobCode` from `WIR01` to `RM01`—and refresh should re-evaluate packs. Job-coded roles beat one-off entitlement requests for movers: that is how Meridian prevents “Treasury forever” access after a commercial transfer.

**Control / audit.** Job→role mapping is an approved matrix. Dual-control jobs (`WIR01` vs `WIR02`) must never share a single initiate+approve role. Evidence = role definitions + mapping matrix + sample assignee cubes (`priya.wire`, `marcus.approve`, a developer, an RM such as `sofia.torres`).

---

## Concepts

### Job codes are the assignment key

HR `jobCode` (and sometimes `departmentCode`) drives who gets which business role. Birthright still applies underneath for employees; job packs layer on top.

```
HR jobCode ──► Assignment rule ──► Business role ──► Entitlements
   WIR01              │              WireInitiator         WIRE_INIT
   WIR02              │              WireApprover          WIRE_APPR  (separate role)
   RM01               │              RelationshipManager   CRM
   DEV01/SRE01        │              Developer             DWRP, ODS
```

| Role | Entitlements | Assignment rule (intent) |
| --- | --- | --- |
| `MNB-Role-Developer` | DWRP, ODS | jobCode in {DEV01, SRE01} |
| `MNB-Role-RelationshipManager` | CRM (+ ODS optional) | jobCode in {RM01, LO01} |
| `MNB-Role-WireInitiator` | WIRE_INIT | jobCode = WIR01 **only** |

### Dual control is a catalog fact

`priya.wire` initiates; `marcus.approve` approves. A rule keyed only on department `TRS` would give both people initiator access—destroying segregation. Key off `WIR01` explicitly. SoD Lessons 39–40 enforce conflicts; this lesson refuses to encode the conflict in a role.

### Mover preview (Lesson 30)

`hr-delta-priya-to-commercial.csv` sets Priya to `CML` / `RM01` / manager `MNB00006`. Wire initiator assignment should stop; RM path should start—**WIRE_INIT entitlement may residual** on the account until remediations. Roles fix intent; residual entitlement hygiene still matters.

### LoA nuance

`sofia.torres` may be `RM01` with `onLeave=true` (Lesson 33). Job roles may still assign while freeze disables interactive access. Do not “fix” leave by removing job packs blindly—freeze is lifecycle, not catalog redesign.

---

## How it works

Refresh re-evaluates every identity against every assignment rule. When HR attributes change, packs should follow—without a ticket for every entitlement.

```
Aggregate MNB-HR (jobCode, departmentCode, status)
        │
        ▼
Refresh MNB Identities (assign roles)
        │
        ├── TEL01  → birthright only
        ├── WIR01  → birthright + WireInitiator
        ├── WIR02  → birthright + WireApprover (not Initiator)
        ├── RM01   → birthright + RelationshipManager
        └── DEV01  → birthright + Developer
```

| Failure mode | What goes wrong | Fix |
| --- | --- | --- |
| Department-only wire rule | Marcus gets WIRE_INIT | Key `jobCode == WIR01` |
| AWS inside Developer | Privilege smuggled | Lesson 26 packaging; Lesson 28 CloudAdmin |
| Mover HR not aggregated | Old packs stick | Aggregate HR then refresh |
| File lab no provisioning | Ents missing on account | Still verify **role assignment** on cube |

---

## Before you start

- [ ] Birthright role working (Lesson 24)
- [ ] Entitlements DWRP, ODS, CRM, WIRE_INIT exist on onboarded apps
- [ ] HR identity attributes `jobCode` and `departmentCode` populated on cubes
- [ ] Do **not** merge WIRE_APPR into the initiator role
- [ ] Notebook matrix ready for job→role

---

## Lab procedure

### Task 1 — Confirm target personas

Named personas make dual-control proof examiner-ready. Guessing job codes fails the lab.

1. From HR, identify at least one DEV01 or SRE01 identity (e.g. `diego.hayes` DEV01).
2. Identify an RM persona (e.g. `sofia.torres` RM01—note onLeave flag if present).
3. Confirm `priya.wire` is WIR01 in **baseline** HR (before mover).
4. Confirm `marcus.approve` is WIR02—must **not** get WireInitiator role.

**Expected result:** Four named test identities with known jobCodes.

**If it fails:** Use `HRApplications.txt` / HR CSV search; do not guess job codes.

### Task 2 — Create `MNB-Role-Developer`

1. Create role `MNB-Role-Developer`.
2. Description: “Application development and analytics read/write baseline for engineers.”
3. Add entitlements **DWRP** and **ODS**.
4. Assignment: `jobCode` in `DEV01`, `SRE01`; optionally require active Employee.
5. Owner: Technology / App Dev manager (document name/title).

**Expected result:** Role saved; composition = DWRP + ODS only (no AWS_ADMIN).

**If it fails:** If ODS missing, aggregate the app that carries ODS or defer ODS and note gap—do not substitute AWS_ADMIN.

### Task 3 — Create `MNB-Role-RelationshipManager`

1. Create role `MNB-Role-RelationshipManager`.
2. Description: “Commercial relationship management CRM access.”
3. Add **CRM**; optionally ODS if your catalog agreed in Lesson 23.
4. Assignment: `jobCode` in `RM01`, `LO01`.
5. Owner: Commercial Banking (e.g. manager of `sanjay.kapoor`’s org).

**Expected result:** CRM present; no WIRE_INIT in this role.

### Task 4 — Create `MNB-Role-WireInitiator`

This is the dual-control hinge. Description and rule must say “initiate only.”

1. Create role `MNB-Role-WireInitiator`.
2. Description: “Wire Portal initiate only. Dual control: approvers use a separate role.”
3. Add **WIRE_INIT** only.
4. Assignment rule: `jobCode == WIR01` (explicitly exclude WIR02).
5. Owner: Payments Operations (`rachel.evans` as control owner).

**Expected result:** WIR01-only rule documented; WIRE_APPR not included.

**If it fails:** If rule UI is limited, use department TRS **and** job WIR01—still exclude WIR02.

### Task 5 — Optional Wire Approver stub

1. Create or stub-name `MNB-Role-WireApprover` → WIRE_APPR for WIR02 (full build can be light if time-boxed).
2. Record that initiator and approver roles remain forever separate (SoD Lessons 39–40).

**Expected result:** Dual-control split acknowledged in catalog even if approver is stubbed.

### Task 6 — Refresh and verify assignment

1. Run **Refresh MNB Identities** with role assignment enabled.
2. Open developer persona → expect `MNB-Role-Developer` (+ birthright).
3. Open `priya.wire` (baseline) → expect `MNB-Role-WireInitiator` (+ birthright).
4. Open `marcus.approve` → expect **no** WireInitiator; approver path only.
5. Open RM persona → expect RelationshipManager if active and in scope.

**Expected result:** Job-based assignments match matrix; marcus does not have initiator role.

**If it fails:** Check jobCode on cube; fix HR map; re-aggregate HR; refresh again.

### Task 7 — Mover preview (read-only)

Do not apply the delta yet—predict the outcome so Lesson 30 has a baseline.

1. Open `~/iiq-lab-data/scenarios/mover/hr-delta-priya-to-commercial.csv`.
2. Note changes: dept `CML`, job `RM01`, manager `MNB00006`, title Relationship Manager.
3. Write predicted post-mover role state: lose WireInitiator assignment; gain RelationshipManager; birthright remains; **WIRE_INIT entitlement may residual** until remediations.

**Expected result:** Prediction paragraph stored for Lesson 30 comparison.

### Task 8 — Publish job→role matrix

1. Finalize matrix in binder with columns: jobCode, roles, entitlements, owner, SoD notes.
2. Mark WIR01/WIR02 dual-control note in red/critical.

**Expected result:** Approved-looking matrix ready for Risk sign-off line.

---

## Acceptance criteria

- [ ] Three roles created: Developer, RelationshipManager, WireInitiator
- [ ] WireInitiator restricted to WIR01
- [ ] Refresh assigns expected personas; marcus lacks initiator role
- [ ] No AWS_ADMIN inside Developer role
- [ ] Mover prediction documented for Priya

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Priya missing WireInitiator | Already moved to RM01 in HR file | Restore baseline WIR01 or use another WIR01 identity |
| Marcus got WireInitiator | Rule uses department TRS only | Key off WIR01 explicitly |
| Developer missing ODS | Entitlement not aggregated | Aggregate source app; attach managed attribute |
| RM role on LOA user | Rule ignores onLeave | Decide policy: assign but disable accounts later (Lesson 33) |
| Roles assign but ents not on account | File lab without provisioning | Verify **assignment** on cube; track entitlement via app account separately |

---

## Training binder evidence

- Screenshots of three role compositions
- Assignment rules for each
- Cube screenshots: developer, `priya.wire`, `marcus.approve`
- Job→role matrix
- Mover prediction note referencing the scenario CSV

**Control owner:** IAM + business owners per role  
**Examiner question:** “Show that wire initiate and approve are not one role.”

---

## Knowledge check

1. Which jobCode receives `MNB-Role-WireInitiator`?
2. What entitlements are in `MNB-Role-Developer`?
3. What makes movers work with these roles?
4. Why must WIR02 not match the initiator rule?
5. After Priya’s commercial mover, which new job role should assign?
6. Why might `sofia.torres` still show RelationshipManager while on leave?

### Answers

1. `WIR01` only.
2. DWRP and ODS.
3. Assignment keys off HR job/dept codes that change on transfer; refresh re-evaluates roles.
4. WIR02 is the approve side of dual control; combining initiate assignment would break segregation.
5. `MNB-Role-RelationshipManager` (job `RM01`).
6. Job assignment may remain while LoA freeze disables interactive access—leave is not the same as job change (Lesson 33).

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “role assignment rules” and “identity refresh” for job-attribute-driven packs.
- [SailPoint Community](https://community.sailpoint.com/) — search “mover access” / “role reassignment” for residual entitlement patterns after HR transfers.
- [NIST SP 800-53 AC-5](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — separation of duties; the control language behind WIR01/WIR02 split roles.
- [FFIEC IT Handbook — Information Security](https://ithandbook.ffiec.gov/) — access administration and dual control expectations for payment systems.
- [CIS Controls v8 — Control 6](https://www.cisecurity.org/controls/access-control-management) — least privilege and access review practices tied to job function.

---

## Stretch lab

- Add `MNB-Role-Operations-Core` for `OPS01` → CORE entitlement with critical risk labeling.
- Parameterize rules with a population “Active Employees” shared across job roles.
- Draft requestable add-on: optional ODS for RMs who lack it—separate from core RM role.

---

## Summary

- Job-coded roles encode Meridian desks: Developer, RM, Wire Initiator.
- WIR01-only initiator packaging preserves payment dual control (`priya.wire` vs `marcus.approve`).
- Mover success depends on HR codes + refresh—and still needs residual entitlement hygiene.

---

**Previous:** [Lesson 24 — Birthright Employee Role](24-birthright-employee-role.md)  
**Next:** [Lesson 26 — IT Role Packaging & Least Privilege](26-it-role-packaging.md)
