# Lesson 90 — BeanShell vs Java Rules

**Level:** Intermediate  
**Track:** Rules, Workflows, Forms  
**Time:** 60–75 min  
**Prereq:** Lesson 89 — Rule Types Catalog  

**Lab data:**
- Repo: `lab-data/connectors/rules/README.md`
- Repo: `lab-data/connectors/plugins/README.md` (compiled extensibility contrast)
- Runtime: `~/iiq-lab-data/connectors/rules/`

---

## Learning objectives

You will be able to:

- Compare **BeanShell** rules vs **compiled Java** (libraries, plugins, services) for Meridian
- Decide when BeanShell is acceptable vs when to compile
- Document performance, testability, and promotion implications
- Refactor a trivial stub toward a Java-shaped design note without breaking lab IIQ
- Apply security review checks (injection, secrets, PII logging)

---

## Why this matters

**Business.** Slow or fragile rules delay joiner/mover provisioning and certification campaigns—visible to the business as “IAM is slow.”

**Control / audit.** BeanShell in production is editable at runtime; banks increasingly require compiled, reviewed artifacts for high-risk BeforeProvisioning and Policy logic. Meridian needs an explicit decision record.

---

## Concepts

| Dimension | BeanShell rule | Compiled Java |
| --- | --- | --- |
| Authoring | Debug UI / XML | IDE + build (SSB/plugin) |
| Hot change | Easy (risky) | Controlled release |
| Testability | Limited | JUnit possible |
| Performance | Interpretted; OK for light logic | Better for heavy loops |
| Reuse | Copy/paste risk | Shared library |
| Meridian default | Stubs, FieldValue, light Correlation | BeforeProv complex, connectors, REST |

```
Complexity / risk
    low ──────────────────────────────────────── high
    FieldValue    Correlation light    BeforeProv AD OU+
    IdentityAttribute format    Policy SoD custom
         │                              │
         └── BeanShell OK (reviewed)    └── Prefer Java / plugin
```

Plugins (`lab-data/connectors/plugins/README.md`) package UI/REST/services—another compiled path when rules are not enough.

---

## Before you start

- [ ] Lesson 89 stubs exist
- [ ] IIQ Debug access
- [ ] Binder: `rules/beanshell-vs-java/`

---

## Lab procedure

### Task 1 — Decision matrix for Meridian

1. Create matrix rows for: FieldValue default email, Correlation employeeId equals, BeforeProv multi-OU leaver, AfterProv ServiceNow ticket, custom REST ping.
2. Mark BeanShell / Java / Plugin for each.
3. Justify one sentence per row.

**Expected result:** Decision matrix with five rows.

**If it fails:** Use Concepts table defaults.

---

### Task 2 — Inspect a stub for BeanShell markers

1. Open `MNB-Rule-Correlation-EmployeeId` in Debug.
2. Confirm language/source is BeanShell (or rule source field).
3. Add comment header:

```text
// Meridian: BeanShell acceptable — simple equality correlation
// Promote via SSD; peer review required
```

4. Save.

**Expected result:** Header comment present on Correlation stub.

**If it fails:** Put header in binder if UI blocks edits.

---

### Task 3 — Design note for Java promotion

1. Pick `MNB-Rule-BeforeProv-AD` as future Java candidate.
2. Write design note:
   - Class name `com.meridiannb.iiq.rule.BeforeProvAd`
   - Inputs: plan, identity, context
   - Behavior: set OU on leaver disable
   - Tests: Given leaver helen.ross When plan disable AD Then OU=...
3. Reference plugin/services lessons (97–102) as implementation track—do not code Java in this lesson.

**Expected result:** One-page Java design note.

---

### Task 4 — Security review checklist

For any rule (BS or Java), check:

- [ ] No hardcoded passwords
- [ ] No unrestricted `Runtime.exec`
- [ ] Logs redact SSN/account numbers
- [ ] LDAP/filter inputs sanitized
- [ ] Timeouts on external calls (AfterProv)

Initial the checklist against Lesson 89 stubs (should be N/A clean).

**Expected result:** Signed checklist.

---

### Task 5 — Performance guardrails

Write Meridian guardrails:

1. No per-entitlement remote API in IdentityAttribute during full refresh without caching strategy.
2. BeforeProv must be O(plan size), not full directory search.
3. Prefer connector filters over rule-side filtering of entire aggregates.

**Expected result:** Guardrails card.

---

### Task 6 — Examiner statement

Draft two sentences Meridian IAM would say to audit: when BeanShell is allowed, when compiled code is required.

**Expected result:** Examiner statement in binder.

---

## Acceptance criteria

- [ ] Decision matrix complete
- [ ] Correlation stub header updated
- [ ] Java design note for BeforeProv-AD written
- [ ] Security checklist signed
- [ ] Performance guardrails documented
- [ ] Examiner statement drafted

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Refresh timeouts | Heavy IdentityAttribute | Move to Java + cache or precompute |
| Prod drift | Hot BeanShell edits | Lock down Debug; SSD only |
| Untestable SoD | Logic only in Workflow BS | Prefer Policy objects + Java |
| Secrets in rule | Copy/paste | Use encrypted config |
| Plugin vs rule confusion | Scope blur | REST/UI → plugin; plan mutate → rule/Java |

---

## Training binder evidence

- Decision matrix
- Rule header screenshot
- Java design note
- Security checklist
- Performance guardrails
- Examiner statement

---

## Knowledge check

1. Is FieldValue email default a strong Java candidate?
2. Why is BeforeProvisioning a Java candidate?
3. What Meridian stub did you annotate as BeanShell-acceptable?
4. Name one security ban for rules.
5. Where do plugins fit vs rules?

### Answers

1. No—light BeanShell is usually enough.  
2. Higher risk, complexity, and need for tests/review on plan mutation.  
3. `MNB-Rule-Correlation-EmployeeId`.  
4. Hardcoded passwords / dangerous exec / PII logging (any one).  
5. Plugins for UI/REST/services packaging; rules for engine-hooked logic (with Java library option).

---

## Stretch lab

Outline a JUnit test class skeleton (names only) for `BeforeProvAd` leaver OU behavior.

---

## Summary

- BeanShell is fine for light, reviewed Meridian stubs; compile high-risk logic.
- Decision records and security/performance guardrails are mandatory training outputs.
- BeforeProv-AD is the flagship candidate for Java promotion.

---

**Previous:** [Lesson 89 — Rule Types Catalog](89-rule-types-catalog.md)  
**Next:** [Lesson 91 — Before/After Provisioning Rules](91-before-after-provisioning-rules.md)
