# Lesson 89 — Rule Types Catalog

**Level:** Intermediate  
**Track:** Rules, Workflows, Forms  
**Time:** 60–90 min  
**Prereq:** Lesson 88 — Connector Gateway / Cloud Patterns  

**Lab data:**
- Repo: `lab-data/connectors/rules/README.md`
- Runtime: `~/iiq-lab-data/connectors/rules/`

---

## Learning objectives

You will be able to:

- List major IdentityIQ **rule types** and when Meridian uses each
- Create Debug stub rules matching the Meridian naming standard (`MNB-Rule-*`)
- Map rule types to connectors, LCM, certifications, and policies
- State change-control expectations for rule promotion
- Build a personal cheat sheet from the lab README

---

## Why this matters

**Business.** Custom logic fills gaps connectors and out-of-box workflows cannot—correlation, plan mutation, computed attributes, cert exclusions.

**Control / audit.** Untracked BeanShell in production is an audit finding waiting to happen. Meridian requires named stubs, owners, and promotion discipline before any rule runs in prod-like environments.

---

## Concepts

From `lab-data/connectors/rules/README.md`:

| Rule type | When used |
| --- | --- |
| BuildMap | Delimited/JDBC row → resource object map |
| Correlation | Account → Identity matching |
| IdentityCreation | New identity defaults |
| IdentityAttribute | Computed identity attributes |
| FieldValue | Form field defaults |
| Provisioning | Customize provisioning plan |
| BeforeProvisioning / AfterProvisioning | Plan mutate / post actions |
| ResourceObjectCustomization | Tweak aggregated objects |
| Policy | Custom policy logic |
| Workflow | Workflow step logic |
| CertificationExclusion | Remove items from certs |
| Report | Custom report data |
| Listener | Lifecycle event hooks |

```
Aggregation ──► BuildMap / ResourceObjectCustomization
        │
        ▼
 Correlation rule ──► Identity cube
        │
        ▼
 IdentityAttribute / IdentityCreation
        │
        ▼
 LCM / request ──► BeforeProv ──► connector ──► AfterProv
```

Stub names (empty body OK until later lessons):

- `MNB-Rule-BuildMap-HR`
- `MNB-Rule-Correlation-EmployeeId`
- `MNB-Rule-BeforeProv-AD`
- `MNB-Rule-AfterProv-Ticket`
- `MNB-Rule-IdentityAttribute-DisplayName`

---

## Before you start

- [ ] IIQ up; Debug → Rules access
- [ ] Copy `lab-data/connectors/rules/README.md` to `~/iiq-lab-data/connectors/rules/`
- [ ] Binder: `rules/catalog/`

---

## Lab procedure

### Task 1 — Study the cheat sheet

1. Open `~/iiq-lab-data/connectors/rules/README.md`.
2. Copy the table into binder; add a column **Meridian example**.
3. Fill examples (e.g., Correlation → employeeId; BeforeProv-AD → OU on leaver).

**Expected result:** Annotated cheat sheet with Meridian examples column.

**If it fails:** Use repo path directly under `lab-data/connectors/rules/README.md`.

---

### Task 2 — Create five stub rules in Debug

1. Debug → Rules → Add New (or equivalent).
2. For each stub name above:
   - Name exact
   - Type matching purpose (Correlation, BuildMap, BeforeProvisioning, AfterProvisioning, IdentityAttribute)
   - Source: comment only `// Meridian stub — Lesson 89`
   - Owner / description: control owner IAM Academy
3. Save each.

**Expected result:** Five Rules listed with `MNB-Rule-` prefix.

**If it fails:** Create XML import stubs; names must still match README.

---

### Task 3 — Trace map: rule → object

Build table:

| Stub | Attaches to | Lesson that fills body |
| --- | --- | --- |
| BuildMap-HR | HR Delimited app | Earlier HR lessons / refresh |
| Correlation-EmployeeId | Apps needing employeeId match | Correlation track |
| BeforeProv-AD | `MNB-ActiveDirectory` | Lesson 91 |
| AfterProv-Ticket | Critical apps | Lesson 91 |
| IdentityAttribute-DisplayName | Identity mappings | Lesson 92 |

**Expected result:** Trace map in binder.

---

### Task 4 — Change control card

Write Meridian rules:

1. No direct prod edit—SSD/SSB promotion (preview Lesson 101).
2. Peer review for Before/After Provisioning.
3. Unit test notes for Correlation (known personas).
4. Logging must avoid PII (no full SSN in logs).

**Expected result:** One-page change control card.

---

### Task 5 — Negative catalog (what not to use)

List three anti-patterns:

- Business SoD only in opaque Workflow rules with no Policy object
- Correlation that always returns first identity
- AfterProvisioning that calls external HTTP without timeout/idempotency

**Expected result:** Anti-pattern list initialed.

---

### Task 6 — Registry of existing rules

1. Debug → search Rules with `MNB-`.
2. Export name list to binder `MNB-Rule-Inventory-YYYY-MM-DD.txt`.
3. Flag any non-stub custom rules for review.

**Expected result:** Inventory file saved.

---

## Acceptance criteria

- [ ] Annotated cheat sheet complete
- [ ] Five named stubs created
- [ ] Trace map links stubs to future lessons
- [ ] Change control card written
- [ ] Anti-patterns listed
- [ ] Inventory export saved

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Wrong rule type | Mis-click in UI | Recreate with correct type |
| Name collision | Prior lab | Rename old or reuse stub |
| Cannot save BeanShell | Syntax | Comment-only body |
| Missing type in dropdown | Version | Closest type + Description note |
| Too many orphan rules | No inventory | Run Task 6 monthly |

---

## Training binder evidence

- Annotated README table
- Screenshots of five stubs
- Trace map
- Change control card
- Anti-pattern list
- Inventory export

---

## Knowledge check

1. Which rule type mutates a provisioning plan before connector execute?
2. Which rule computes identity attributes?
3. Name the Meridian AfterProvisioning stub.
4. Where is the lab cheat sheet?
5. Are empty stub bodies acceptable in Lesson 89?

### Answers

1. BeforeProvisioning.  
2. IdentityAttribute.  
3. `MNB-Rule-AfterProv-Ticket`.  
4. `lab-data/connectors/rules/README.md` (copied to `~/iiq-lab-data/connectors/rules/`).  
5. Yes—empty/comment stubs until later lessons fill them.

---

## Stretch lab

Add stubs `MNB-Rule-CertificationExclusion-BreakGlass` and `MNB-Rule-Policy-WireSoD` (comment bodies) for later policy/cert work.

---

## Summary

- Meridian standardizes rule names and types from the lab cheat sheet.
- Stubs establish inventory and change control before complex logic.
- Later lessons fill Before/After Prov and IdentityAttribute bodies.

---

**Previous:** [Lesson 88 — Connector Gateway / Cloud Patterns](88-connector-gateway-cloud-patterns.md)  
**Next:** [Lesson 90 — BeanShell vs Java Rules](90-beanshell-vs-java-rules.md)
