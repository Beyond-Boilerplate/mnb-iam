# Lesson 25 — Department & Job-Based Roles

**Level:** Intermediate  
**Track:** Roles  
**Time:** 60–90 minutes  
**Prereq:** Lesson 24 (`MNB-Birthright-Employee` + `MNB-IT-ELDAP`); entitlements DWRP, ODS, CRM, WIRE_INIT available  

**Lab data:**
- `~/iiq-lab-data/reference/job-codes.csv`
- Personas with DEV/RM/WIR01 jobs; dual-control pair `priya.wire` (WIR01) / `marcus.approve` (WIR02)
- Mover preview: `~/iiq-lab-data/scenarios/mover/hr-delta-priya-to-commercial.csv`

---

> **Verify:** Lab lesson — create IT packs + business roles (Developer, RM, WireInitiator). Academy **Verify now** checks those Bundles + wire personas.

## Learning objectives

You will be able to:

- Create IT packs and matching business roles for Developer, Relationship Manager, and Wire Initiator (same two-tier model as Lesson 24)
- Put entitlements only on type **it**; put `jobCode` Match Lists only on type **business**
- Restrict **`MNB-Role-WireInitiator`** to **`WIR01` only** (never `WIR02`)
- Verify assignment after refresh; prove `marcus.approve` never receives the initiator role
- Preview why Priya’s mover delta will swap wire → RM packs in Lesson 30

---

## Why this matters

**Business.** Most access follows the desk you sit in. When `priya.wire` later moves to commercial banking, HR changes `jobCode` from `WIR01` to `RM01`—and refresh should re-evaluate packs. Job-coded roles beat one-off entitlement requests for movers: that is how Meridian prevents “Treasury forever” access after a commercial transfer.

**Control / audit.** Job→role mapping is an approved matrix. Dual-control jobs (`WIR01` vs `WIR02`) must never share a single initiate+approve role. Evidence = IT compositions + business assignment rules + sample assignee cubes (`priya.wire`, `marcus.approve`, a developer, an RM such as `sofia.torres`).

---

## Concepts

### Same two-tier model as birthright

Lesson 24 already proved stock IIQ: type **business** does **not** support Entitlements (*“Entitlements section is not supported by the selected role type”*). Job packs use the same pattern:

```
HR jobCode ──► Business role (Match List) ──► Required Roles ──► IT role ──► Entitlements
   WIR01         MNB-Role-WireInitiator           │              MNB-IT-WireInit      WIRE_INIT
   WIR02         MNB-Role-WireApprover (sep.)     │              MNB-IT-WireAppr      WIRE_APPR
   RM01/LO01     MNB-Role-RelationshipManager     │              MNB-IT-CRM           CRM
   DEV01/SRE01   MNB-Role-Developer               │              MNB-IT-Developer     DWRP, ODS
```

| Business role (who) | Required IT pack (what) | Entitlements | Assignment (intent) |
| --- | --- | --- | --- |
| `MNB-Role-Developer` | `MNB-IT-Developer` | DWRP, ODS | jobCode in {DEV01, SRE01} |
| `MNB-Role-RelationshipManager` | `MNB-IT-CRM` | CRM (+ ODS optional — keep on IT pack) | jobCode in {RM01, LO01} |
| `MNB-Role-WireInitiator` | `MNB-IT-WireInit` | WIRE_INIT | jobCode = WIR01 **only** |

Birthright (`MNB-Birthright-Employee` → `MNB-IT-ELDAP`) still applies underneath for employees; job packs layer on top.

### Dual control is a catalog fact

`priya.wire` initiates; `marcus.approve` approves. A rule keyed only on department `TRS` would give both people initiator access—destroying segregation. Key off `WIR01` explicitly. SoD Lessons 39–40 enforce conflicts; this lesson refuses to encode the conflict in a role.

### Mover preview (Lesson 30)

`hr-delta-priya-to-commercial.csv` sets Priya to `CML` / `RM01` / manager `MNB00006`. Wire initiator assignment should stop; RM path should start—**WIRE_INIT entitlement may residual** on the account until remediations. Roles fix intent; residual entitlement hygiene still matters.

### LoA nuance

`sofia.torres` may be `RM01` with `exceptions=LOA` (Lesson 33). Job roles may still assign while freeze disables interactive access. Do not “fix” leave by removing job packs blindly—freeze is lifecycle, not catalog redesign.

---

## How it works

Refresh re-evaluates every identity against every **business** assignment rule. Required IT packs supply the entitlements for provisioning / detection.

```
Aggregate MNB-HR (jobCode, departmentName, inactive)
        │
        ▼
Refresh MNB Roles (assign roles ON)
        │
        ├── TEL01  → birthright only
        ├── WIR01  → birthright + WireInitiator (→ MNB-IT-WireInit)
        ├── WIR02  → birthright + WireApprover (not Initiator)
        ├── RM01   → birthright + RelationshipManager (→ MNB-IT-CRM)
        └── DEV01  → birthright + Developer (→ MNB-IT-Developer)
```

| Failure mode | What goes wrong | Fix |
| --- | --- | --- |
| Entitlements on business role | UI warning; nothing sticks | Put ents on type **it**; link Required Roles |
| Department-only wire rule | Marcus gets WIRE_INIT | Key `jobCode == WIR01` |
| AWS inside Developer IT pack | Privilege smuggled | Lesson 26 packaging; Lesson 28 CloudAdmin |
| Mover HR not aggregated | Old packs stick | Aggregate HR then refresh |

---

## Before you start

- [ ] Lesson 24 complete: `MNB-IT-ELDAP` + `MNB-Birthright-Employee` working
- [ ] Entitlements DWRP, ODS, CRM, WIRE_INIT exist on onboarded apps
- [ ] HR attributes `jobCode` / `JobCode` and `departmentName` populated on cubes
- [ ] Do **not** merge WIRE_APPR into the initiator IT pack
- [ ] Notebook matrix ready for job→business→IT→entitlement

### UI recipe (same as Lesson 24 — skim, then use per task)

| Step | Path / choice |
| --- | --- |
| Open roles | **Setup → Roles** → **Role Viewer** |
| Create | **Add** / **Create New** → **Role** (skip Business/IT Role Mining and Entitlement Analysis) |
| IT pack | Type **it** → **Entitlements → Add** → Simple View (or **Advanced View**) → Submit |
| Business role | Type **business** → ignore Entitlements warning → **Modify Required Roles** → **Assignment Rule = Match List** → Submit |

**Match List tip:** Use the HR attribute name on the cube (`jobCode` or `JobCode`—match Lesson 05 mapping). For multiple codes, add one Match List row per value (OR within the attribute group if your UI offers it), or create separate criteria your version supports—document what you used.

---

## Lab procedure

### Task 1 — Confirm target personas

Named personas make dual-control proof examiner-ready. Guessing job codes fails the lab.

1. **Identities → Identity Warehouse** — find at least one DEV01 or SRE01 identity (e.g. `diego.hayes` DEV01).
2. Identify an RM persona (e.g. `sofia.torres` RM01—note `exceptions=LOA` if present).
3. Confirm `priya.wire` is WIR01 in **baseline** HR (before mover).
4. Confirm `marcus.approve` is WIR02—must **not** get WireInitiator.

**Expected result:** Four named test identities with known jobCodes.

**If it fails:** Search `HRApplications.txt` / HR CSV; do not guess job codes.

### Task 2 — Developer pack (`MNB-IT-Developer` + `MNB-Role-Developer`)

Engineers need app/analytics tools—not cloud admin.

**2a — IT pack**

1. **Setup → Roles** → **Create New → Role**.
2. Name `MNB-IT-Developer`, Type **it**, Owner `spadmin`.
3. Description: `IT pack: DWRP + ODS for application development. No AWS_ADMIN.`
4. **Entitlements → Add** → select **DWRP** and **ODS** only (Simple or Advanced View) → Submit profile → **Submit** role.

**2b — Business role**

1. **Create New → Role** → Name `MNB-Role-Developer`, Type **business**, Owner `spadmin` (lab; production: Technology / App Dev manager).
2. Description: `Application development and analytics baseline for engineers. Not cloud admin, not wire access.`
3. Ignore Entitlements warning. **Modify Required Roles** → add **`MNB-IT-Developer`** → Save.
4. **Assignment Rule → Match List**: `jobCode` / `JobCode` in `DEV01`, `SRE01`; optionally `employeeType=Employee` and `inactive=false`.
5. Requestable **off**. **Submit**.

**Expected result:** Business role requires `MNB-IT-Developer`; IT pack = DWRP + ODS only (no AWS_ADMIN).

**If it fails:** ODS missing → aggregate the ODS app or defer and note gap—do **not** substitute AWS_ADMIN.

### Task 3 — Relationship Manager pack (`MNB-IT-CRM` + `MNB-Role-RelationshipManager`)

**3a — IT pack**

1. **Create New → Role** → `MNB-IT-CRM`, Type **it**.
2. Entitlements: **CRM** only (add ODS here only if Lesson 23 catalog agreed—and never WIRE_INIT).
3. **Submit**.

**3b — Business role**

1. **Create New → Role** → `MNB-Role-RelationshipManager`, Type **business**.
2. Description: `Commercial relationship management CRM access.`
3. **Required Roles** → `MNB-IT-CRM`.
4. Match List: `jobCode` in `RM01`, `LO01` (optionally active Employee).
5. Owner note: Commercial Banking. **Submit**.

**Expected result:** CRM on the IT pack; no WIRE_INIT; business rule keys RM/LO jobs.

### Task 4 — Wire Initiator pack (`MNB-IT-WireInit` + `MNB-Role-WireInitiator`)

This is the dual-control hinge. Description and rule must say “initiate only.”

**4a — IT pack**

1. **Create New → Role** → `MNB-IT-WireInit`, Type **it**.
2. Entitlements: **WIRE_INIT** only — never `WIRE_APPR`.
3. **Submit**.

**4b — Business role**

1. **Create New → Role** → `MNB-Role-WireInitiator`, Type **business**.
2. Description: `Wire Portal initiate only. Dual control: approvers use a separate role.`
3. **Required Roles** → `MNB-IT-WireInit`.
4. Match List: `jobCode` / `JobCode` **equals `WIR01`** only (do **not** use department TRS alone).
5. Owner: Payments Operations (`rachel.evans` as control owner). **Submit**.

**Expected result:** WIR01-only assignment; IT pack has WIRE_INIT only.

**If it fails:** Rule UI limited → department TRS **and** job WIR01—still exclude WIR02.

### Task 5 — Optional Wire Approver stub

1. If time allows: IT `MNB-IT-WireAppr` → **WIRE_APPR** only; business `MNB-Role-WireApprover` → Required that IT pack; Match List `jobCode=WIR02`.
2. If time-boxed: stub-name both in the binder matrix without full UI build.
3. Record: initiator and approver remain forever separate (SoD Lessons 39–40).

**Expected result:** Dual-control split acknowledged in catalog even if approver is stubbed.

### Task 6 — Refresh and verify assignment

1. **Setup → Tasks** → open **`Refresh MNB Roles`** (or **`Refresh MNB Identities`**).
2. Enable **Refresh assigned, detected roles…** and **Provision assigned roles** if present → **Run Now**.
3. Identity Warehouse checks:
   - Developer persona → **Assigned:** `MNB-Role-Developer` (+ birthright).
   - `priya.wire` (baseline WIR01) → **Assigned:** `MNB-Role-WireInitiator` (+ birthright).
   - `marcus.approve` (WIR02) → **no** WireInitiator.
   - RM persona → RelationshipManager if active and in scope.

**Expected result:** Job-based assignments match matrix; marcus does not have initiator role.

**If it fails:** Check `jobCode` on cube; fix HR map; re-aggregate HR; confirm Required Role links; refresh again.

### Task 7 — Mover preview (read-only)

Do not apply the delta yet—predict the outcome so Lesson 30 has a baseline.

1. Open `~/iiq-lab-data/scenarios/mover/hr-delta-priya-to-commercial.csv`.
2. Note changes: dept `CML`, job `RM01`, manager `MNB00006`, title Relationship Manager.
3. Write predicted post-mover role state: lose WireInitiator assignment; gain RelationshipManager; birthright remains; **WIRE_INIT entitlement may residual** until remediations.

**Expected result:** Prediction paragraph stored for Lesson 30 comparison.

### Task 8 — Publish job→role matrix

1. Finalize matrix: jobCode | business role | required IT role | entitlements | owner | SoD notes.
2. Mark WIR01/WIR02 dual-control note in red/critical.

**Expected result:** Approved-looking matrix ready for Risk sign-off line.

---

## Acceptance criteria

- [ ] IT packs created: `MNB-IT-Developer`, `MNB-IT-CRM`, `MNB-IT-WireInit` (ents only on type **it**)
- [ ] Business roles created: Developer, RelationshipManager, WireInitiator (Required Roles + Match List; no direct Entitlements)
- [ ] WireInitiator restricted to WIR01
- [ ] Refresh assigns expected personas; marcus lacks initiator role
- [ ] No AWS_ADMIN inside Developer IT pack
- [ ] Mover prediction documented for Priya

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| *Entitlements not supported* on job role | Type = business (expected) | Put ents on IT pack; use Required Roles |
| Priya missing WireInitiator | Already moved to RM01 in HR file | Restore baseline WIR01 or use another WIR01 identity |
| Marcus got WireInitiator | Rule uses department TRS only | Key off WIR01 explicitly |
| Developer missing ODS | Entitlement not aggregated | Aggregate source app; attach on **IT** pack |
| Business role assigns but no ents expected | Required Role empty | Link `MNB-IT-*` under Required Roles |
| RM role on LOA user | Rule ignores exceptions (LOA) | Assign but disable accounts later (Lesson 33) |
| Roles assign but ents not on account | File lab without provisioning | Verify **assignment** on cube |

---

## Training binder evidence

- Screenshots: each IT pack Entitlements list
- Screenshots: each business role Required Roles + Match List
- Cube screenshots: developer, `priya.wire`, `marcus.approve`
- Job→business→IT→entitlement matrix
- Mover prediction note referencing the scenario CSV

**Control owner:** IAM + business owners per role  
**Examiner question:** “Show that wire initiate and approve are not one role.”

---

## Knowledge check

1. Which jobCode receives `MNB-Role-WireInitiator`?
2. Where do DWRP and ODS live—on the business role or on `MNB-IT-Developer`?
3. What makes movers work with these roles?
4. Why must WIR02 not match the initiator rule?
5. After Priya’s commercial mover, which new **business** role should assign?
6. Why might `sofia.torres` still show RelationshipManager while on leave?

### Answers

1. `WIR01` only.
2. On the **IT** pack `MNB-IT-Developer` (business role only Requires it + Match List).
3. Assignment keys off HR job/dept codes that change on transfer; refresh re-evaluates business roles.
4. WIR02 is the approve side of dual control; combining initiate assignment would break segregation.
5. `MNB-Role-RelationshipManager` (job `RM01`) → Required `MNB-IT-CRM`.
6. Job assignment may remain while LoA freeze disables interactive access—leave is not the same as job change (Lesson 33).

---

## Further reading

- [SailPoint IdentityIQ — Role Modeling](https://documentation.sailpoint.com/identityiq/help/roles_groups_and_populations/roles/role_modeling/index.html) — business vs IT types, Required Roles, Assignment Rule.
- [SailPoint Community](https://community.sailpoint.com/) — search “mover access” / “role reassignment” for residual entitlement patterns after HR transfers.
- [NIST SP 800-53 AC-5](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — separation of duties; the control language behind WIR01/WIR02 split roles.
- [FFIEC IT Handbook — Information Security](https://ithandbook.ffiec.gov/) — access administration and dual control expectations for payment systems.
- [CIS Controls v8 — Control 6](https://www.cisecurity.org/controls/access-control-management) — least privilege and access review practices tied to job function.

---

## Stretch lab

- Fully build Wire Approver: `MNB-IT-WireAppr` + `MNB-Role-WireApprover` for WIR02.
- Add `MNB-IT-Core` / `MNB-Role-Operations-Core` for `OPS01` → CORE with critical risk labeling.
- Draft requestable add-on: optional ODS IT pack for RMs who lack it—separate from core RM Required Role.

---

## Summary

- Job packs follow Lesson 24’s two-tier model: IT = entitlements, business = who (Match List) + Required Roles.
- WIR01-only initiator packaging preserves payment dual control (`priya.wire` vs `marcus.approve`).
- Mover success depends on HR codes + refresh—and still needs residual entitlement hygiene.

---

**Previous:** [Lesson 24 — Birthright Employee Role](24-birthright-employee-role.md)  
**Next:** [Lesson 26 — IT Role Packaging & Least Privilege](26-it-role-packaging.md)
