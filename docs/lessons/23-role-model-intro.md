# Lesson 23 — Role Model Introduction

**Level:** Intermediate  
**Track:** Roles  
**Time:** 45–60 minutes  
**Prereq:** Lesson 22; applications and entitlements from Lessons 09–16 available  

**Lab data:**
- Repo / home: `~/iiq-lab-data/reference/job-codes.csv`
- Repo / home: `~/iiq-lab-data/reference/entitlement-dictionary.csv`
- Repo / home: `~/iiq-lab-data/reference/sod-matrix.csv`

---

## Learning objectives

You will be able to:

- Distinguish **IT roles** vs **business roles** in IdentityIQ terms Meridian can defend to audit
- Sketch a starter role catalog using `MNB-Birthright-*` and `MNB-Role-*` naming
- Map department/job codes to candidate roles without exploding the catalog
- Mark which roles are birthright, assignment-rule driven, or request-only
- List stakeholders who must approve the catalog before go-live
- Explain why dual-control payment roles (`WIR01` / `WIR02`) must never share a single bundle

---

## Why this matters

**Business.** Without roles, every access request is a snowflake entitlement pick—slow for joiners, opaque for certifiers. When `amelia.brooks` joined as a teller, her manager should have seen “baseline employee pack,” not fifteen raw group codes. Roles translate bank jobs into governed bundles managers understand: “Relationship Manager pack,” not `CRM|ODS|ELDAP` soup.

**Control / audit.** Role composition is a change-controlled artifact. When the OCC examiner asks *"how is birthright bounded, and how is privileged access excluded?"* your answer is the catalog sketch plus the anti-goals (no birthright CloudAdmin, no initiate+approve wire pack). Later lessons implement the bundles in IIQ; this lesson freezes the design control.

---

## Concepts

### Bundles speak two languages

In IdentityIQ, roles are often **Bundles**. Two common modeling styles:

| Style | Speaks to | Contains | Meridian use |
| --- | --- | --- | --- |
| **IT role** | Technical packaging | Entitlements / accounts | Building blocks (e.g. directory + ODS) |
| **Business role** | Job / function | IT roles and/or entitlements | What HR and managers recognize |

The naive alternative is to skip roles and certify every entitlement forever. That fails at a bank under exam: managers cannot attest technical codes they do not understand, and joiner SLAs collapse under ticket volume.

### Starter catalog (sketch — implement in Lessons 24–28)

| Role name | Type | Entitlements (intent) | Assignment posture |
| --- | --- | --- | --- |
| `MNB-Birthright-Employee` | Birthright | ELDAP | Auto: active Employee |
| `MNB-Role-Developer` | Job | DWRP, ODS | Auto: DEV01 / SRE01 |
| `MNB-Role-RelationshipManager` | Job | CRM (+ optional ODS) | Auto: RM01 / LO01 |
| `MNB-Role-WireInitiator` | Job | WIRE_INIT | Auto: WIR01 only |
| `MNB-Role-WireApprover` | Job | WIRE_APPR | Auto: WIR02 (separate forever) |
| `MNB-Role-CloudAdmin` | Privileged | AWS_ADMIN | Request-only |
| `MNB-Role-BreakGlass` | Privileged | PRIV_BREAK | Request-only |

**Anti-goals:** Never birthright CloudAdmin, WireApprover, BreakGlass, or SAP_FI. Never merge `WIRE_INIT` and `WIRE_APPR` into one role—that destroys payment dual control.

### Why dual control shows up in the catalog, not later

`priya.wire` (`WIR01`) initiates; `marcus.approve` (`WIR02`) approves. If the catalog treats “Treasury wire access” as one pack, SoD policy later is theater—the conflict is already baked into the role. Catalog design is the first SoD control.

---

## How it works

Roles sit between HR attributes and entitlements. Refresh evaluates assignment rules; LCM later lets humans request privileged packs. Detection (Lesson 27) is analytical—do not confuse it with assignment.

```
HR identity attributes (jobCode, employeeType, status)
        │
        ▼
Assignment rules / selectors
        │
        ├──► MNB-Birthright-Employee  → ELDAP
        ├──► MNB-Role-* (job packs)   → app entitlements
        └──► (no rule) privileged     → request-only path (Lessons 28, 35–37)
        │
        ▼
Identity cube: Assigned roles ──► provisioning plan (when connectors live)
```

| Layer | Object | What it answers |
| --- | --- | --- |
| HR | `jobCode`, `employeeType`, `status` | Who is this person at Meridian? |
| Role (Bundle) | `MNB-Birthright-*` / `MNB-Role-*` | What pack should they have? |
| Entitlement | ELDAP, WIRE_INIT, AWS_ADMIN… | What access does the pack grant? |
| Request path | LCM catalog | What can they ask for that rules do not auto-grant? |

One consequence: **catalog size is a control.** Fifteen thoughtful job packs beat two hundred entitlement-named “roles.” Rare access stays requestable, not auto-assigned.

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq`; you can browse Applications and Entitlements
- [ ] Reference CSVs copied to `~/iiq-lab-data/reference/`
- [ ] Attribute hygiene from Lesson 22 understood (roles will key off HR codes)
- [ ] Notebook section titled `MNB-Role-Catalog-v0`

---

## Lab procedure

### Task 1 — Refresh Meridian job language

Before naming roles, speak Meridian’s desk language. Wrong job codes in the sketch become wrong assignment rules later.

1. Open `~/iiq-lab-data/reference/job-codes.csv`.
2. Highlight: `TEL01`, `WIR01`, `WIR02`, `RM01`, `DEV01`, `SRE01`, `CLD01`.
3. Open `entitlement-dictionary.csv` and mark risk=critical codes (`WIRE_*`, `AWS_ADMIN`, `SAP_FI`, `PRIV_BREAK`, `CORE`).

**Expected result:** You can say aloud which jobs are retail baseline vs payments dual-control vs cloud privilege.

**If it fails:** Re-read Lesson 02 org model; do not invent job codes.

### Task 2 — Sketch IT vs business roles

Enterprises argue endlessly about flat vs nested role models. Decide now for the academy so Lessons 24–28 stay consistent with stock IIQ.

1. Write two paragraphs:
   - IT roles = reusable entitlement packs for engineers
   - Business roles = “desk” language for HR/managers/certifiers
2. Decide Meridian’s v0 approach: **two-tier** — **business** roles for “who” (assignment rules) + **IT** roles for “what” (entitlements), linked by **Required Roles**. Stock IIQ business types do **not** support the Entitlements panel (`noProfiles`); Lesson 24 hits that warning on purpose.

**Expected result:** Explicit lab decision recorded (business + required IT packs for the academy).

### Task 3 — Build catalog v0 table

The table is the design control. Renaming after certifications reference a role is painful—treat names as permanent.

1. Copy the starter catalog table into your binder.
2. Add columns: Owner, Risk tier, Requestable Y/N, Birthright Y/N.
3. Assign draft owners: Directory/IAM for birthright; Treasury (`rachel.evans`) for wire roles; Technology for CloudAdmin; Security for BreakGlass; Commercial for RM.

**Expected result:** Complete table with no privileged role marked birthright.

**If it fails:** If unsure of owner, mark “TBD — Risk approval required” rather than inventing.

### Task 4 — Map jobs → roles

Assignment rules will copy this matrix. Dual control lives in the mapping rows.

1. Create mapping:

| jobCode | Expected roles |
| --- | --- |
| TEL01 | Birthright only |
| WIR01 | Birthright + WireInitiator |
| WIR02 | Birthright + WireApprover |
| RM01 | Birthright + RelationshipManager |
| DEV01 | Birthright + Developer |
| CLD01 | Birthright + (CloudAdmin **request**, not auto) |

2. Confirm WIR01 ≠ WIR02 in the mapping (dual control). Tellers (`amelia.brooks` / TEL01) get no wire or cloud packs.

**Expected result:** Mapping shows tellers do not get wire or cloud packs; CLD01 does not auto-get AWS_ADMIN.

### Task 5 — Naming standard lock-in

1. Confirm prefixes: `MNB-Birthright-*`, `MNB-Role-*`.
2. Reject names like `Role1`, `dev pack`, `AWS stuff`.
3. Add naming rule to Lesson 03 hygiene notes if missing.

**Expected result:** Catalog uses only MNB- prefixes.

### Task 6 — Stakeholder approval list

Catalog go-live is dual-controlled design, not an IAM-only publish.

1. List required approvers: HR, Risk/Compliance, IT/IAM, Treasury (payments), Commercial (CRM).
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

- [ ] **Bank craft exit:** Role model notes cite seeded `MNB-Role-Birthright-Employee` / `MNB-Role-IT-Directory-User` under `config/Bundle/`

- [ ] IT vs business role explanation written in Meridian language
- [ ] Catalog v0 table with MNB-Birthright-* and MNB-Role-* entries
- [ ] Job→role mapping includes WIR01-only initiator rule
- [ ] Privileged roles marked request-only
- [ ] Stakeholder approval list completed
- [ ] Dual-control anti-pattern (initiate+approve) parked for enforcement

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
- Decision note: two-tier business + required IT packs (stock IIQ; Entitlements not on business)

**Control owner:** IAM Architecture (draft) + Risk (approve compositions)  
**Examiner question:** “Show me which roles are birthright and prove privileged access is excluded.”

---

## Knowledge check

1. What is the difference between an IT role and a business role?
2. Which naming prefixes does Meridian use?
3. Which roles in the starter catalog are request-only?
4. Why must Wire Approver never be birthright for all of Treasury?
5. Which jobCode should receive `MNB-Role-WireInitiator`?
6. Why is catalog size itself a control?

### Answers

1. IT roles package technical entitlements; business roles express job/function language (may contain IT roles or entitlements).
2. `MNB-Birthright-*` and `MNB-Role-*`.
3. `MNB-Role-CloudAdmin` and `MNB-Role-BreakGlass` (at minimum).
4. Approval is dual-control privilege; automatic broad assignment destroys payment segregation.
5. `WIR01` only—not `WIR02`.
6. Too many roles recreate entitlement soup; too few smuggle privilege—thoughtful job packs plus requestable rares keep certs and joiners workable.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “Business Roles” and “IT Roles” for Bundle modeling and assignment vs detection.
- [SailPoint Community / Compass](https://community.sailpoint.com/) — search “role model design” for real-world birthright vs requestable patterns.
- [NIST SP 800-53 AC-2 / AC-6](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — account management and least privilege; the control language behind birthright boundaries.
- [FFIEC Information Security booklet](https://www.ffiec.gov/press/pr110723.htm) — banking examiner expectations for access administration (use current FFIEC IT Handbook portal if the press link redirects).
- [CIS Controls v8 — Control 6](https://www.cisecurity.org/controls/access-control-management) — access control management practices that map cleanly to role catalogs.

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
