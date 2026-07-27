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

- Compare **BeanShell** rules vs **compiled Java** (libraries, plugins, services) along maintainability, IDE support, testability, and promotion
- Decide when BeanShell is acceptable at Meridian vs when to compile and promote via SSB
- Document performance, security, and peer-review gates for high-risk rule types
- Produce a Java-shaped design note for `MNB-Rule-BeforeProv-AD` without writing production Java in this lab
- Apply an OWASP-minded security checklist (injection, secrets, PII logging) to rule review

---

## Why this matters

**Business.** When `nina.joiner`'s joiner refresh timed out because an IdentityAttribute rule called a remote API per cube, hiring managers saw "IAM is slow" for an entire Monday. Fragile or heavyweight rules delay joiners, movers, and certification campaigns — visible to the business as blocked access.

**Control / audit.** BeanShell in production is editable at runtime. Banks increasingly require compiled, reviewed artifacts for high-risk BeforeProvisioning and Policy logic. When the OCC examiner asks *"who can change the code that rewrites AD disables, and how do you prove the change was reviewed?"* Meridian needs an explicit decision record: BeanShell allowed here, Java required there, SSD-only promotion, Debug locked in prod.

---

## Concepts

### BeanShell: what it is and why IIQ uses it

**BeanShell** is a lightweight Java-like scripting language embedded in IdentityIQ. Rules store source text on the Rule object; the engine interprets it at the hook. That makes BeanShell ideal for *light*, *local* logic — FieldValue defaults, simple Correlation equality, small IdentityAttribute formatting — because you can iterate in lab Debug without a full compile cycle.

The cost: no real IDE refactoring, weak static analysis, easy copy-paste drift, and a temptation to hot-fix production. Interpretted code is "fine until it isn't" — a nested loop over all links inside IdentityAttribute during a full refresh will melt your Task Result.

### Compiled Java: libraries, rule wrappers, plugins

**Compiled Java** means logic lives in `.java` sources, built by Gradle/Maven (typically the SailPoint Services Standard Build — **SSB/SSD**), unit-tested with JUnit, and deployed as a jar or plugin. A thin BeanShell rule (or a Java rule class registered with IIQ) may call into that library. Plugins (`lab-data/connectors/plugins/README.md`) package UI, REST, and services — another compiled path when rules alone are not enough.

Meridian's default:

| Dimension | BeanShell rule | Compiled Java (SSB / plugin) |
| --- | --- | --- |
| Authoring | Debug UI / XML | IDE + build (SSB/plugin) |
| Hot change | Easy (risky in prod) | Controlled release only |
| Testability | Limited (persona dry-runs) | JUnit / integration tests possible |
| Performance | OK for light logic | Better for heavy loops and shared code |
| Reuse | Copy/paste risk across rules | Shared library / package |
| Meridian default | Stubs, FieldValue, light Correlation, simple IdentityAttribute | Complex BeforeProv, custom Policy, connector helpers, REST |

```
Complexity / risk
    low ──────────────────────────────────────────── high
    FieldValue     Correlation (equals)     BeforeProv AD OU+
    IdentityAttribute format     Policy SoD custom
         │                              │
         └── BeanShell OK (reviewed)    └── Prefer Java / plugin
              via SSD still                  via SSB + JUnit
```

### Maintainability and IDE reality

A senior teammate reviewing `MNB-Rule-BeforeProv-AD` in Debug sees a text blob. The same logic as `com.meridiannb.iiq.rule.BeforeProvAd` in IntelliJ/Eclipse gets breakpoints, null analysis, extract-method, and PR diffs that CAB can read. **Promotion via SSB is not optional polish** — it is how Meridian keeps lab and prod from diverging when someone "just fixed" BeanShell on Friday night.

### Security: script injection and secrets

BeanShell that concatenates identity attributes into LDAP filters, JDBC, or shell commands is a classic injection surface. Treat rule review like application code review:

- Never hardcode passwords, API keys, or service-account JSON in rule source.
- Never `Runtime.exec` on requester-supplied strings.
- Sanitize / parameterize anything that becomes a filter or query.
- Log request ids and application names — not SSNs, wire amounts, or full account numbers.

OWASP's injection and code-review guidance applies even though the "app" is inside IIQ.

### Wrong way vs Meridian way

| Wrong way | Why it fails | Meridian way |
| --- | --- | --- |
| 400-line BeforeProv in BeanShell only in prod | Untestable; hot-edit drift | Java library + thin rule; SSB promote |
| IdentityAttribute calls ServiceNow per cube | Refresh timeouts; rate limits | Precompute / cache / AfterProv or workflow |
| Secrets in rule comments "for convenience" | Vault bypass; exam finding | Encrypted config / credential config objects |
| Plugin for every FieldValue | Overbuilt | BeanShell FieldValue; plugin for UI/REST |

---

## How it works

```
Developer workstation
        │
        ├── Light rule ──► BeanShell in Rule XML ──► SSD project ──► lower env ──► peer review ──► prod
        │
        └── Heavy rule ──► Java sources (SSB) ──► jar/plugin ──► Rule or service calls library
                                    │
                                    └── JUnit (Given leaver When disable Then OU=…)
```

| Decision input | Prefer BeanShell | Prefer Java / plugin |
| --- | --- | --- |
| Lines of logic | Under ~30, local attrs only | Branching plan mutation, shared helpers |
| External I/O | None | HTTP, complex JDBC, shared clients |
| Risk if wrong | Low (display formatting) | High (AD OU, SoD, ticket storms) |
| Need IDE / JUnit | No | Yes |
| UI / REST packaging | N/A | Plugin (`mnb-iam-toolkit` track, Lessons 97+) |

Promotion always goes through SSD/SSB artifacts — **including** BeanShell rule XML. "BeanShell acceptable" never means "edit prod Debug."

---

## Real-world setup (SSB promotion and review gates)

### Step 1 — Classify the change

1. Open the Meridian decision matrix (you build it in Task 1).
2. Tag the rule: **BS-reviewed** or **Java-required**.
3. If Java-required, create/extend a package under the SSB project (e.g. `com.meridiannb.iiq.rule`) before writing production logic.

### Step 2 — Author and unit-test

1. BeanShell: author in lab, export Rule XML into SSD `config` / rules folder.
2. Java: implement with JUnit for personas (`helen.ross` leaver, `priya.wire` privileged disable).
3. No secrets in source; reference credential config or vault-backed settings.

### Step 3 — Peer review gate (mandatory for high risk)

BeforeProvisioning, AfterProvisioning, Policy, and Correlation require a second engineer to check:

- [ ] Null-safety on plan / identity / links
- [ ] Idempotency of side effects
- [ ] No injection into filters/commands
- [ ] Logging redacts PII
- [ ] Performance O(plan size) or O(1) attribute reads — no full-directory scans

### Step 4 — Promote and lock

1. Deploy via SSB pipeline to test, then prod with CAB ticket.
2. Confirm Debug rule edit is denied for day-to-day ops capabilities (Lesson 96 / 109).
3. Smoke-test with known IdentityRequests before closing the ticket.

---

## Before you start

- [ ] Lesson 89 stubs exist (`MNB-Rule-Correlation-EmployeeId`, `MNB-Rule-BeforeProv-AD`, others)
- [ ] IIQ Debug access at `http://localhost:8080/identityiq`
- [ ] Skim `lab-data/connectors/plugins/README.md` for plugin vs rule contrast
- [ ] Binder: `rules/beanshell-vs-java/`

---

## Lab procedure

### Task 1 — Decision matrix for Meridian

Production teams do not argue BeanShell vs Java in a Sev-1 bridge. Decide now, reuse forever.

1. Create matrix rows for these five cases:
   - FieldValue default email / ticket prefix
   - Correlation `employeeId` equals
   - BeforeProv multi-OU leaver on AD
   - AfterProv ServiceNow ticket on privileged disable
   - Custom REST "connector health ping" UI
2. Mark each **BeanShell** / **Java** / **Plugin**.
3. Justify in one sentence per row (risk, testability, packaging).

**Expected result:** Decision matrix with five rows and justifications.

**If it fails:** Use Concepts table defaults: FieldValue/Correlation → BeanShell; BeforeProv → Java; AfterProv ticket → Java or workflow service; REST ping → Plugin.

### Task 2 — Inspect a stub for BeanShell markers

You are documenting an explicit "BeanShell acceptable" decision on a light rule so future reviewers do not "upgrade" it to Java without cause — or worse, leave heavy logic in Correlation by accident.

1. Open `MNB-Rule-Correlation-EmployeeId` in Debug.
2. Confirm language/source is BeanShell (rule source field).
3. Add a header comment:

```text
// Meridian: BeanShell acceptable — simple equality correlation
// Promote via SSD; peer review required; no hot-edit in prod
// Classification: BS-reviewed (Lesson 90)
```

4. Save. Do **not** implement full correlation logic here unless your earlier correlation lessons already did — header is the deliverable.

**Expected result:** Header comment present on the Correlation stub classifying it BS-reviewed.

**If it fails:** Put the same header text in the binder if UI blocks edits; note the limitation.

### Task 3 — Design note for Java promotion

`MNB-Rule-BeforeProv-AD` is Meridian's flagship Java candidate: plan mutation, leaver OU policy, high blast radius.

1. Write a one-page design note (no Java code required in IIQ this lesson):
   - **Class:** `com.meridiannb.iiq.rule.BeforeProvAd`
   - **Inputs:** `ProvisioningPlan`, identity, context / application
   - **Behavior:** on Disable / leaver for `MNB-ActiveDirectory`, ensure OU / leaver attribute policy (details Lesson 91)
   - **Tests:** Given leaver `helen.ross` When plan Disable on AD Then OU/leaver flag set; Given non-disable Then plan unchanged
   - **Thin rule:** BeanShell or Java rule entry calls `BeforeProvAd.apply(plan, …)`
2. Reference plugins/services lessons (97–102) as the implementation track — do not code the Java class in this lesson.

**Expected result:** One-page Java design note in binder.

### Task 4 — Security review checklist

Apply the same gate you will use in CAB. For any rule (BeanShell or Java):

- [ ] No hardcoded passwords, tokens, or key files
- [ ] No unrestricted `Runtime.exec`
- [ ] Logs redact SSN / account numbers / wire amounts
- [ ] LDAP / JDBC / filter inputs parameterized or validated
- [ ] Timeouts and idempotency on external calls (AfterProv)
- [ ] No string-built queries from requester form fields without validation (ties Lesson 94)

Initial the checklist against Lesson 89 stubs (comment-only bodies should be N/A clean). Note OWASP injection as the review lens for any future filter construction.

**Expected result:** Signed security checklist in binder.

### Task 5 — Performance guardrails

Write Meridian guardrails on a card:

1. No per-entitlement remote API inside IdentityAttribute during full refresh without a documented caching strategy.
2. BeforeProv must be O(plan size) — never a full directory search "to find the user again."
3. Prefer connector filters and aggregation options over rule-side filtering of entire aggregates.
4. AfterProv ticket create must key on IdentityRequest id (or equivalent) — no unbounded retry storms.

**Expected result:** Performance guardrails card.

### Task 6 — Examiner statement

Draft two sentences Meridian IAM would say to audit:

1. When BeanShell is allowed (light, local, reviewed, SSD-promoted).
2. When compiled Java/plugin is required (plan mutation, SoD, external I/O, shared libraries).

Include: Debug is not a production change channel.

**Expected result:** Examiner statement in binder (two sentences + Debug lockdown clause).

### Task 7 — Contrast with plugins

1. Open `lab-data/connectors/plugins/README.md`.
2. Write three bullets: QuickLink/workflow enough → rule; shared Java library → SSB jar; custom UI/REST → plugin.
3. Note: secrets never in plugin XML or QuickLink query strings (Lesson 95).

**Expected result:** Three-bullet packaging contrast note.

---

## Acceptance criteria

- [ ] Decision matrix complete (five rows)
- [ ] Correlation stub header updated (BS-reviewed)
- [ ] Java design note for BeforeProv-AD written
- [ ] Security checklist signed (OWASP injection awareness)
- [ ] Performance guardrails documented
- [ ] Examiner statement drafted
- [ ] Plugin vs rule vs Java packaging note written

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Refresh timeouts | Heavy IdentityAttribute / remote calls | Move I/O out; Java + cache or precompute |
| Prod drift from lab | Hot BeanShell edits in prod | Lock Debug; SSD-only; restore from build |
| Untestable SoD | Logic only in Workflow BeanShell | Prefer Policy objects + Java |
| Secrets in rule source | Copy/paste "temporary" | Encrypted config / vault; rotate exposed secrets |
| Plugin vs rule confusion | Scope blur | REST/UI → plugin; plan mutate → rule/Java library |
| "Java rewrite" of FieldValue | Over-engineering | Keep light FieldValue as BeanShell |

---

## Training binder evidence

- Decision matrix (five cases)
- Rule header screenshot (`MNB-Rule-Correlation-EmployeeId`)
- Java design note for `BeforeProvAd`
- Security checklist (signed)
- Performance guardrails card
- Examiner statement
- Plugin vs rule packaging note

---

## Knowledge check

1. Is a FieldValue email/ticket-prefix default a strong Java candidate? Why or why not?
2. Why is BeforeProvisioning Meridian's flagship Java candidate?
3. What Meridian stub did you annotate as BeanShell-acceptable?
4. Name two security bans for rules (BeanShell or Java).
5. Where do plugins fit vs rules vs SSB Java libraries?
6. Does "BeanShell acceptable" allow editing the rule in production Debug?

### Answers

1. No — light, local defaulting is usually enough as reviewed BeanShell.
2. Higher risk and complexity on plan mutation; needs tests, IDE review, and controlled promotion.
3. `MNB-Rule-Correlation-EmployeeId`.
4. Hardcoded passwords; unrestricted `Runtime.exec`; PII in logs; unsanitized filter injection (any two).
5. Plugins for UI/REST packaging; rules for engine hooks; SSB Java libraries for shared/testable logic called from rules.
6. No — BeanShell still promotes via SSD; Debug stays locked in prod-like environments.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search "BeanShell" and "Java rules" for embedding patterns and Rule class expectations for your version.
- [SailPoint Services Standard Build (SSB) / SSD documentation](https://community.sailpoint.com/) — search "Services Standard Build" for how rule XML and custom jars promote between environments.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — real threads on BeanShell performance pitfalls and Debug lockdown.
- [OWASP Code Review Guide](https://owasp.org/www-project-code-review-guide/) — injection and unsafe API patterns that apply to scripted rules.
- [OWASP Scripting / Injection cheat sheets](https://cheatsheetseries.owasp.org/) — search "Injection" and "Input Validation" for review checklists.
- [Oracle Java SE documentation](https://docs.oracle.com/en/java/) — language baseline for compiled rule libraries (Java 11/17 per your IIQ version support matrix).

---

## Stretch lab

Outline a JUnit test class skeleton (method names only) for `BeforeProvAd`: `disablesLeaver_setsOuPolicy`, `nonDisable_leavesPlanUnchanged`, `nullPlan_safeNoOp`. Do not implement — Lesson 91 stays lab-safe.

---

## Summary

- BeanShell is fine for light, reviewed Meridian stubs; compile high-risk plan mutation and shared logic.
- Maintainability, IDE support, JUnit, and SSB promotion — not "which language is cooler" — drive the decision.
- Security and performance guardrails are mandatory training outputs; Debug is never the production change channel.

---

**Previous:** [Lesson 89 — Rule Types Catalog](89-rule-types-catalog.md)  
**Next:** [Lesson 91 — Before/After Provisioning Rules](91-before-after-provisioning-rules.md)
