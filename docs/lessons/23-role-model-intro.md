# Lesson 23 — Role Model Introduction

**Level:** Intermediate  
**Track:** Roles  
**Time:** 45–60 minutes  
**Prereq:** Lesson 22; applications and entitlements from Lessons 09–16 available  
**Lab data:** `~/iiq-lab-data/reference/job-codes.csv`, `entitlement-dictionary.csv`, `sod-matrix.csv`

---

## Learning objectives

You will be able to:

- Distinguish **IT roles** vs **business roles** in IdentityIQ terms Meridian can defend to audit
- Sketch a starter role catalog using `MNB-Birthright-*` and `MNB-Role-*` naming
- Map department/job codes to candidate roles without exploding the catalog
- Mark which roles are birthright, assignment-rule driven, or request-only
- List stakeholders who must approve the catalog before go-live

---

## Why this matters

Without roles, every access request is a snowflake entitlement pick—slow for joiners, opaque for certifiers. Roles translate bank jobs into governed bundles managers understand: “Relationship Manager pack,” not fifteen raw codes.

**Control / audit:** Role composition is a change-controlled artifact. Examiners ask how birthright is bounded and how privileged access is excluded. Your catalog sketch is the design control; later lessons implement bundles in IIQ.

---

## Concepts

In IdentityIQ, roles are often **Bundles**. Two common modeling styles:

| Style | Speaks to | Contains | Meridian use |
| --- | --- | --- | --- |
| **IT role** | Technical packaging | Entitlements / accounts | Building blocks (e.g. directory + ODS) |
| **Business role** | Job / function | IT roles and/or entitlements | What HR and managers recognize |

```
Business role: MNB-Role-Developer
        │
        ├── IT entitlements: DWRP, ODS
        └── Assigned when jobCode in {DEV01, SRE01}

Birthright: MNB-Birthright-Employee
        │
        └── ELDAP only — active Employee workerType
```

**Starter catalog (sketch — implement in Lessons 24–28):**

| Role name | Type | Entitlements (intent) | Assignment posture |
| --- | --- | --- | --- |
| `MNB-Birthright-Employee` | Birthright | ELDAP | Auto: active Employee |
| `MNB-Role-Developer` | Job | DWRP, ODS | Auto: DEV01 / SRE01 |
| `MNB-Role-RelationshipManager` | Job | CRM (+ optional ODS) | Auto: RM01 / LO01 |
| `MNB-Role-WireInitiator` | Job | WIRE_INIT | Auto: WIR01 only |
| `MNB-Role-WireApprover` | Job | WIRE_APPR | Auto: WIR02 (separate forever) |
| `MNB-Role-CloudAdmin` | Privileged | AWS_ADMIN | Request-only |
| `MNB-Role-BreakGlass` | Privileged | PRIV_BREAK | Request-only |

**Anti-goals:** Never birthright CloudAdmin, WireApprover, BreakGlass, or SAP_FI.

---

## Before you start

- [ ] IIQ up; you can browse Applications and Entitlements
- [ ] Reference CSVs copied to `~/iiq-lab-data/reference/`
- [ ] Attribute hygiene understood (roles will key off HR codes)
- [ ] Notebook section titled `MNB-Role-Catalog-v0`

---

## Lab procedure

### Task 1 — Refresh Meridian job language

1. Open `~/iiq-lab-data/reference/job-codes.csv`.
2. Highlight: `TEL01`, `WIR01`, `WIR02`, `RM01`, `DEV01`, `SRE01`, `CLD01`.
3. Open `entitlement-dictionary.csv` and mark risk=critical codes.

**Expected result:** You can say aloud which jobs are retail baseline vs payments dual-control vs cloud privilege.

**If it fails:** Re-read Lesson 02 org model; do not invent job codes.

### Task 2 — Sketch IT vs business roles

1. Write two paragraphs:
   - IT roles = reusable entitlement packs for engineers
   - Business roles = “desk” language for HR/managers/certifiers
2. Decide Meridian’s v0 approach: **business roles that embed entitlements directly** (simpler for the lab) with optional future IT-role nesting.

**Expected result:** Explicit lab decision recorded (flat business roles OK for academy).

### Task 3 — Build catalog v0 table

1. Copy the starter catalog table into your binder.
2. Add columns: Owner, Risk tier, Requestable Y/N, Birthright Y/N.
3. Assign draft owners: e.g. Directory/IAM for birthright; Treasury (`rachel.evans`) for wire roles; Technology for CloudAdmin; Security for BreakGlass; Commercial manager for RM.

**Expected result:** Complete table with no privileged role marked birthright.

**If it fails:** If unsure of owner, mark “TBD — Risk approval required” rather than inventing.

### Task 4 — Map jobs → roles

1. Create mapping:

| jobCode | Expected roles |
| --- | --- |
| TEL01 | Birthright only |
| WIR01 | Birthright + WireInitiator |
| WIR02 | Birthright + WireApprover |
| RM01 | Birthright + RelationshipManager |
| DEV01 | Birthright + Developer |
| CLD01 | Birthright + (CloudAdmin **request**, not auto) |

2. Confirm WIR01 ≠ WIR02 in the mapping (dual control).

**Expected result:** Mapping shows tellers do not get wire or cloud packs.

### Task 5 — Naming standard lock-in

1. Confirm prefixes: `MNB-Birthright-*`, `MNB-Role-*`.
2. Reject names like `Role1`, `dev pack`, `AWS stuff`.
3. Add naming rule to Lesson 03 hygiene notes if missing.

**Expected result:** Catalog uses only MNB- prefixes.

### Task 6 — Stakeholder approval list

1. List required approvers for catalog go-live: HR, Risk/Compliance, IT/IAM, Treasury (payments), Commercial (CRM).
2. Write the exam sentence: “Role catalog changes require Risk + IAM dual control.”

**Expected result:** Named stakeholder list in binder (roles/titles, not only personal names).

### Task 7 — Anti-pattern park lot

1. List three role-model anti-patterns Meridian forbids:
   - Birthright including AWS_ADMIN
   - Single role with WIRE_INIT + WIRE_APPR
   - “Everything developers need” including production cloud admin
2. Park each for Lessons 26–28 enforcement.

**Expected result:** Anti-pattern list signed off in notebook.

---

## Acceptance criteria

- [ ] IT vs business role explanation written in Meridian language
- [ ] Catalog v0 table with MNB-Birthright-* and MNB-Role-* entries
- [ ] Job→role mapping includes WIR01-only initiator rule
- [ ] Privileged roles marked request-only
- [ ] Stakeholder approval list completed

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Catalog growing past ~15 roles already | Designing every entitlement as a role | Prefer job packs; leave rare ents requestable |
| Managers won’t understand IT role names | Too technical | Lead with business role names in certs |
| Wire initiate/approve merged “for convenience” | SoD violation by design | Split immediately; see Lesson 40 |
| Cloud auto-assigned to CLD01 | Confusing job with privilege | Job gets eligibility to **request**, not birthright |

---

## Training binder evidence

- `MNB-Role-Catalog-v0` table
- Job→role mapping sheet
- Stakeholder approval list
- Anti-pattern park lot (3 items)
- Decision note: flat business roles for lab vs nested IT roles later

**Control owner:** IAM Architecture (draft) + Risk (approve compositions)  
**Examiner question:** “Show me which roles are birthright and prove privileged access is excluded.”

---

## Knowledge check

1. What is the difference between an IT role and a business role?
2. Which naming prefixes does Meridian use?
3. Which roles in the starter catalog are request-only?
4. Why must Wire Approver never be birthright for all of Treasury?
5. Which jobCode should receive `MNB-Role-WireInitiator`?

### Answers

1. IT roles package technical entitlements; business roles express job/function language (may contain IT roles or entitlements).
2. `MNB-Birthright-*` and `MNB-Role-*`.
3. `MNB-Role-CloudAdmin` and `MNB-Role-BreakGlass` (at minimum).
4. Approval is dual-control privilege; automatic broad assignment destroys payment segregation.
5. `WIR01` only—not `WIR02`.

---

## Stretch lab

- Draft `MNB-Role-AML-Investigator` → `AML_CASE` for jobCode `AML01`; mark requestable or assignment-rule with Risk owner.
- Propose nested model: `MNB-IT-Directory-Baseline` (ELDAP) consumed by birthright and by contractor birthright variant.
- Estimate certification impact: role-level cert vs entitlement-level cert for retail vs treasury.

---

## Summary

- Roles convert entitlement soup into auditable business language.
- Meridian v0 catalog centers birthright ELDAP, job packs for Dev/RM/Wire, and request-only privilege.
- Naming, dual-control splits, and stakeholder approval are design controls—not paperwork afterthoughts.

---

**Previous:** [Lesson 22 — Identity Attribute Sync Hygiene](22-attribute-sync-hygiene.md)  
**Next:** [Lesson 24 — Birthright Employee Role](24-birthright-employee-role.md)
