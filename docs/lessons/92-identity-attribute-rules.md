# Lesson 92 — Identity Attribute Rules

**Level:** Intermediate  
**Track:** Rules, Workflows, Forms  
**Time:** 60–90 min  
**Prereq:** Lesson 91 — Before / After Provisioning Rules  

**Lab data:**
- Repo: `lab-data/connectors/rules/README.md`
- Repo: `lab-data/hr/MNB-HR-Employees.csv`
- Runtime: `~/iiq-lab-data/connectors/rules/`, `~/iiq-lab-data/hr/`

---

## Learning objectives

You will be able to:

- Explain when **IdentityAttribute** rules run and how they differ from account-attribute mapping
- Configure `MNB-Rule-IdentityAttribute-DisplayName` for Meridian's deterministic naming contract
- Use IdentityAttribute patterns as helpers for **derived attributes** and manager-correlation context
- Map the rule into Identity Mappings / refresh options and verify on named personas
- Document performance constraints so full refresh stays within SLA
- Promote rule XML together with Identity Mapping changes via SSD

---

## Why this matters

**Business.** Certifications, approval emails, and manager UX all show `displayName`. When `priya.wire` appeared as `priya.wire` in one campaign and `Priya Wire` in another, managers filed helpdesk tickets and skipped reviews. Consistent derived attributes are how Meridian makes cubes human-readable and populations stable.

**Control / audit.** Computed attributes used in populations, SoD, and manager correlation must be **deterministic and documented**. Examiners may ask: *"How is displayName derived? Can a rule call AD during refresh? Who owns the mapping?"* A named rule, a written contract, and refresh Task Results are the evidence chain.

---

## Concepts

### What an IdentityAttribute rule is

An **IdentityAttribute** rule runs during identity refresh / attribute promotion to compute a **target identity attribute** from sources already on the cube (HR-sourced attrs, other identity fields, sometimes link summaries). It does **not** replace aggregation — it shapes the identity after authoritative data lands.

Contrast:

| Mechanism | Operates on | Typical use |
| --- | --- | --- |
| Application account attribute mapping | Account / link | Copy `sAMAccountName` → identity `adAccount` |
| **IdentityAttribute rule** | Identity cube | Derive `displayName`, risk flags, normalized manager key |
| Correlation rule | Account → Identity match | Find which cube an account belongs to |

### Derived attributes at Meridian

Meridian standardizes a small set of derived fields rather than a zoo of one-off scripts:

| Attribute | Meridian pattern (lab) | Why |
| --- | --- | --- |
| `displayName` | `Last, First (employeeId)` | Cert UX, email headers, search |
| Optional email | From HR — do **not** override unless CAB-approved | Authoritative mailbox identity |
| Optional `mnbMfaRequired` | Boolean from department / privileged entitlements (stretch) | Population for MFA policy |

Stub: `MNB-Rule-IdentityAttribute-DisplayName`.

Examples:

- `helen.ross` → `Ross, Helen (MNB00001)` (ids vary by your HR file — use actual `employeeId`)
- `priya.wire` → `Wire, Priya (…)`
- `sofia.torres` → `Torres, Sofia (…)`

Null policy: if `lastname` missing, fall back to `name` / `uid` / `userName` — never throw during refresh.

### Manager correlation helpers

IdentityAttribute rules sometimes compute a **normalized manager key** (e.g. manager employeeId trimmed/uppercased) that Correlation or manager-assignment logic consumes. The rule itself should stay O(1) attribute reads — it prepares clean fields so Correlation stays simple equality (Lesson 89/90 preference for light BeanShell Correlation).

Wrong way: IdentityAttribute opens AD to "look up the manager's DN every refresh." That couples refresh to directory availability and destroys performance. Right way: HR feeds `managerEmployeeId`; IdentityAttribute normalizes it; Correlation / manager pointer uses the clean value.

### Wrong way vs Meridian way

| Wrong way | Why it fails | Meridian way |
| --- | --- | --- |
| Remote API inside IdentityAttribute | Refresh timeouts; rate limits | Local attrs only; I/O elsewhere |
| Override email without CAB | Breaks SSO / mailbox correlation | HR remains authoritative for email |
| Non-deterministic `new Date()` in displayName | Cubes churn every refresh; noisy audits | Pure function of source attrs |
| Different formats per app owner | Cert confusion | One Meridian contract, one rule |

```
HR attrs (firstname, lastname, employeeId)
        │
        ▼
 IdentityAttribute rule (DisplayName)
        │
        ▼
 identity.displayName = "Wire, Priya (MNB00xxx)"
        │
        ▼
 Certs / forms / populations consume stable displayName
```

---

## How it works

```
MNB-HR Account Aggregation
        │
        ▼
 Correlation (employeeId) ──► Identity cube
        │
        ▼
 Refresh Identity Cubes / Refresh MNB Identities
        │  options: process identity attributes / promote
        ▼
 Identity Mapping: displayName ← MNB-Rule-IdentityAttribute-DisplayName
        │
        ▼
 Cube header + populations + cert line items updated
```

| Step | Object | Meridian owner |
| --- | --- | --- |
| Source attrs | `MNB-HR` schema / cube fields | HRIS + IAM |
| Rule | `MNB-Rule-IdentityAttribute-DisplayName` | IAM Ops (`helen.ross`) |
| Mapping | Global Identity Mappings | IAM Ops |
| Verification | Refresh Task Result + cube screenshots | Training binder / CAB evidence |

Performance: IdentityAttribute runs **broadly** (often every identity in a refresh population). Keep logic under ~20 lines, O(1) gets, no connector calls, no full link iteration unless strictly necessary and documented.

---

## Real-world setup (mapping + promotion)

### Step 1 — Write the computation contract

1. Inputs: `firstname` / `lastname` / `employeeId` (exact IIQ attribute names in your build).
2. Output: `displayName` string.
3. Null / fallback policy and two worked examples (`helen.ross`, `priya.wire`).
4. CAB note if any attribute besides displayName will be rule-driven.

### Step 2 — Implement and map in lower env

1. Implement rule body; attach under Identity Mappings for `displayName` (Advanced / rule value source — labels vary).
2. Refresh a small population first; then widen.

### Step 3 — Promote via SSD as a bundle

1. Rule XML + Identity Mapping XML/changes **together**.
2. Never promote mapping without the rule (or cubes go blank / stale).
3. Peer review: still light BeanShell, but mapping impact is enterprise-wide — treat as medium risk.

### Step 4 — Population and cert impact check

1. Populations filtering on `displayName` contains … must still match.
2. Notify cert owners (`MNB-WG-Cert-Approvers`) that labels change once — expected one-time churn.

---

## Before you start

- [ ] IIQ up; identities aggregated from HR (`MNB-HR` / `MNB-HR-Employees.csv`)
- [ ] Stub `MNB-Rule-IdentityAttribute-DisplayName` exists (Lesson 89)
- [ ] Know Global Settings → Identity Mappings (or equivalent) path
- [ ] Binder: `rules/identity-attribute/`

---

## Lab procedure

### Task 1 — Choose computation contract

Derived attributes without a contract become tribal formats. Freeze the contract before coding.

1. Write contract: inputs `firstname`, `lastname`, `employeeId` (adjust to your lab attribute names); output `displayName`.
2. Null policy: if lastname missing, fall back to `userName` / `name`.
3. Worked examples:
   - `helen.ross` → `Ross, Helen (<employeeId>)`
   - `priya.wire` → `Wire, Priya (<employeeId>)`
4. Explicit non-goals: do not recompute email; do not call connectors.

**Expected result:** Contract page with two examples and non-goals.

### Task 2 — Implement the IdentityAttribute rule

1. Debug → open `MNB-Rule-IdentityAttribute-DisplayName`.
2. Confirm type **IdentityAttribute**.
3. Implement BeanShell that:
   - Reads identity attributes safely (null checks)
   - Builds `Last, First (employeeId)`
   - Returns the string
4. Keep logic under ~20 lines; no remote calls; no `new Date()` in the value.
5. Save.

**Expected result:** Rule returns displayName string without errors on save.

**If it fails:** Temporarily return existing displayName / name passthrough until syntax is fixed — then iterate toward the contract.

### Task 3 — Map into Identity Attribute definition

1. Open Identity Mappings / Identity Attributes advanced config (path varies by version).
2. Locate **displayName** (or create advanced attribute mapping).
3. Attach rule `MNB-Rule-IdentityAttribute-DisplayName` as value source / Advanced rule.
4. Save.
5. Screenshot the mapping.

**Expected result:** Mapping references the Meridian rule.

**If it fails:** Document exact clicks for your version; use the application-independent identity attribute editor under Global Settings.

### Task 4 — Refresh and verify

Aggregation without refresh leaves derived attrs stale — verification means Task Result + cube UI.

1. Run **Refresh MNB Identities** (or Refresh Identity Cubes) for a population including `helen.ross`, `priya.wire`, `sofia.torres`.
2. Enable options that process identity attributes / promote attributes as required in your build.
3. Open each cube; record displayName before/after.
4. Confirm email domain remains `@meridiannb.com` where applicable (rule must not have overridden email).

**Expected result:** Three cubes show computed displayName per contract; email untouched.

**If it fails:** Refresh single identity from UI; check Task Result for BeanShell stack traces.

### Task 5 — Population and manager UX check

1. Find any population using displayName contains filters — confirm still works or update the filter deliberately.
2. Note: manager certifications will show the new displayName — screenshot one identity header (`priya.wire` or `helen.ross`).
3. Optional: document a manager-key helper attribute you would add later (normalize `managerEmployeeId`) — design only unless stretch.

**Expected result:** Note + optional screenshot; manager-helper design one-liner.

### Task 6 — Performance and promotion notes

Write three bullets:

1. IdentityAttribute rules run broadly — keep O(1) attribute reads.
2. Do not call connectors or HTTP inside IdentityAttribute.
3. Promote rule XML via SSD **with** Identity Mapping changes together.

**Expected result:** Three-bullet ops note in binder.

### Task 7 — Examiner question drill

*"How is displayName set for employees, and how do you know it did not drift?"*

Answer with: (1) contract page, (2) rule + mapping screenshots, (3) refresh Task Result + three persona cube proofs.

**Expected result:** Written proof steps in binder.

---

## Acceptance criteria

- [ ] Computation contract documented (examples + non-goals)
- [ ] Rule implemented and saved (no remote calls)
- [ ] Identity mapping attached
- [ ] Refresh verified on `helen.ross`, `priya.wire`, `sofia.torres`
- [ ] Performance/promotion notes written
- [ ] Examiner proof steps drafted

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| NullPointer during refresh | Missing attr | Null-safe fallback to userName |
| No change after refresh | Mapping not attached / option off | Re-check mapping; enable attribute promote option |
| Wrong order `First Last` | Contract drift | Match Meridian `Last, First (employeeId)` |
| Slow refresh | Heavy rule / API calls | Remove loops and remote I/O immediately |
| Email changed unexpectedly | Rule overwrote email | Remove that logic; restore from HR aggregation |
| Garbled Unicode | Encoding | Stick to ASCII lab names for this exercise |

---

## Training binder evidence

- Contract page (inputs, output, null policy, examples)
- Rule source screenshot
- Identity mapping screenshot
- Three cube displayName proofs
- Ops performance / promotion note
- Examiner proof steps

---

## Knowledge check

1. When do IdentityAttribute rules typically run?
2. Name the Meridian displayName rule.
3. What is the Meridian displayName pattern in this lab?
4. May the rule call AD or ServiceNow during refresh?
5. Name three verification personas.
6. Why promote Identity Mapping changes in the same SSD bundle as the rule?

### Answers

1. During identity refresh / attribute promotion.
2. `MNB-Rule-IdentityAttribute-DisplayName`.
3. `Last, First (employeeId)` with userName fallback.
4. No — local attribute reads only.
5. `helen.ross`, `priya.wire`, `sofia.torres`.
6. So environments never get a mapping pointing at a missing rule (or a rule with no mapping) — avoids blank/stale cubes.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search "Identity Attribute rules" and "Identity Mappings" for attachment UI and refresh options by version.
- [SailPoint Community / Compass](https://community.sailpoint.com/) — search "IdentityAttribute rule performance" for refresh SLA war stories.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — patterns for derived attributes vs application mapping.
- [OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html) — mindset if derived attrs later feed filters or exports.
- [NIST SP 800-63A](https://pages.nist.gov/800-63-3/sp800-63a.html) — identity proofing / attribute quality background useful when defending authoritative vs derived attributes to examiners.

---

## Stretch lab

Add optional attribute `mnbMfaRequired` via a second IdentityAttribute rule: `true` when the identity has Wire Portal entitlements or privileged roles (read links carefully; keep logic light; still no remote calls). Document the population that would consume it. Optionally design (do not heavy-implement) a normalized `managerKey` helper for manager correlation.

---

## Summary

- IdentityAttribute rules compute deterministic cube fields for UX, populations, and control evidence.
- Meridian standardizes displayName via a named rule, a written contract, and refresh verification on real personas.
- Keep computations local and fast; promote rules with their Identity Mapping changes; never use refresh as a connector client.

---

**Previous:** [Lesson 91 — Before / After Provisioning Rules](91-before-after-provisioning-rules.md)  
**Next:** [Lesson 93 — LCM Workflow Customization](93-workflow-lcm-customization.md)
