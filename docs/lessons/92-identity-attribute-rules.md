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

- Configure an **IdentityAttribute** rule for computed cube attributes
- Implement `MNB-Rule-IdentityAttribute-DisplayName` for Meridian naming
- Map the rule into Identity Mapping / refresh options
- Verify computed values on personas (`helen.ross`, `priya.wire`, `sofia.torres`)
- Document performance constraints for refresh-time rules

---

## Why this matters

**Business.** Consistent display names and risk flags drive certifications, emails, and manager UX. Garbage attributes create helpdesk noise.

**Control / audit.** Computed attributes used in populations and SoD must be deterministic and documented. Examiners may ask how `displayName` or custom risk flags are derived.

---

## Concepts

**IdentityAttribute rule:** runs during identity refresh / attribute promotion to compute a target identity attribute from sources (HR attrs, links, other identity fields).

```
HR attrs (firstname, lastname, employeeId)
        │
        ▼
 IdentityAttribute rule (DisplayName)
        │
        ▼
 identity.displayName = "Ross, Helen (MNB00001)"  // example pattern
```

| Attribute | Meridian pattern (lab) |
| --- | --- |
| displayName | `Last, First (employeeId)` |
| Optional email | already from HR—do not override unless approved |
| Optional `mnbMfaRequired` | boolean from department/entitlements (stretch) |

Stub: `MNB-Rule-IdentityAttribute-DisplayName`.

---

## Before you start

- [ ] IIQ up; identities aggregated from HR
- [ ] Stub rule exists (Lesson 89)
- [ ] Know Global Settings → Identity Mappings (or equivalent) path
- [ ] Binder: `rules/identity-attribute/`

---

## Lab procedure

### Task 1 — Choose computation contract

1. Write contract: inputs `firstname`, `lastname`, `employeeId` (or IIQ attribute names in your lab); output `displayName`.
2. Null policy: if lastname missing, fall back to `userName`.
3. Examples:
   - helen.ross → `Ross, Helen (…id…)`
   - priya.wire → `Wire, Priya (…)`

**Expected result:** Contract page with two examples.

---

### Task 2 — Implement the IdentityAttribute rule

1. Debug → open `MNB-Rule-IdentityAttribute-DisplayName`.
2. Set type IdentityAttribute if not already.
3. Implement BeanShell that:
   - Reads identity attributes safely
   - Builds `Last, First (employeeId)`
   - Returns the string
4. Keep logic under ~20 lines; no remote calls.
5. Save.

**Expected result:** Rule returns displayName string without errors on save.

**If it fails:** Use comments + return `identity.getAttribute("displayname")` passthrough until syntax fixed—then iterate.

---

### Task 3 — Map into Identity Attribute definition

1. Open Identity Mappings / Identity Attributes advanced config (path varies by version).
2. Locate **displayName** (or create advanced attribute mapping).
3. Attach rule `MNB-Rule-IdentityAttribute-DisplayName` as value source / Advanced rule.
4. Save.
5. Screenshot mapping.

**Expected result:** Mapping references the Meridian rule.

**If it fails:** Document exact clicks for your version; use Application-independent identity attribute editor under Global Settings.

---

### Task 4 — Refresh and verify

1. Run **Refresh MNB Identities** (or Refresh Identity Cubes) for a population including `helen.ross`, `priya.wire`, `sofia.torres`.
2. Enable options that process identity attributes / promote attributes as required in your build.
3. Open each cube; record displayName before/after.
4. Confirm email domain remains `@meridiannb.com` where applicable.

**Expected result:** Three cubes show computed displayName per contract.

**If it fails:** Refresh single identity from UI; check Task Result for BeanShell errors.

---

### Task 5 — Population dependency check

1. Find any population using displayName contains filters—confirm still works.
2. Note: manager certifications show the new displayName—screenshot one identity header.

**Expected result:** Note + optional screenshot.

---

### Task 6 — Performance & promotion notes

Write:

1. IdentityAttribute rules run broadly—keep O(1) attribute reads.
2. Do not call connectors inside IdentityAttribute.
3. Promote rule XML via SSD with Identity Mapping changes together.

**Expected result:** Three-bullet ops note.

---

## Acceptance criteria

- [ ] Computation contract documented
- [ ] Rule implemented and saved
- [ ] Identity mapping attached
- [ ] Refresh verified on three personas
- [ ] Performance/promotion notes written
- [ ] No remote calls inside the rule

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| NullPointer | Missing attr | Null-safe fallback to userName |
| No change after refresh | Mapping not attached / option off | Re-check mapping; attribute promote option |
| Wrong order First Last | Contract drift | Match Meridian `Last, First` |
| Slow refresh | Heavy rule | Remove loops/API calls |
| Garbled Unicode | Encoding | Stick to ASCII lab names |

---

## Training binder evidence

- Contract page
- Rule source screenshot
- Identity mapping screenshot
- Three cube displayName proofs
- Ops performance note

---

## Knowledge check

1. When do IdentityAttribute rules typically run?
2. Name the Meridian displayName rule.
3. What is the Meridian displayName pattern in this lab?
4. May the rule call AD during refresh?
5. Name three verification personas.

### Answers

1. During identity refresh / attribute promotion.  
2. `MNB-Rule-IdentityAttribute-DisplayName`.  
3. `Last, First (employeeId)` with userName fallback.  
4. No.  
5. `helen.ross`, `priya.wire`, `sofia.torres`.

---

## Stretch lab

Add optional attribute `mnbMfaRequired` IdentityAttribute rule: true when identity has Wire Portal entitlements or privileged roles (read links carefully; keep logic light).

---

## Summary

- IdentityAttribute rules compute deterministic cube fields for UX and controls.
- Meridian standardizes displayName via a named rule and refresh verification.
- Keep computations local, fast, and promoted with mappings.

---

**Previous:** [Lesson 91 — Before / After Provisioning Rules](91-before-after-provisioning-rules.md)  
**Next:** [Lesson 93 — LCM Workflow Customization](93-workflow-lcm-customization.md)
