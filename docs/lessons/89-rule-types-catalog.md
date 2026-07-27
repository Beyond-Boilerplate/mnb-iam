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

- List the major IdentityIQ **rule types** and state when Meridian uses each
- Explain where rules sit in the aggregation → correlation → refresh → provisioning lifecycle
- Create Debug stub rules matching the Meridian naming standard (`MNB-Rule-*`)
- Map each stub to the connector, LCM, certification, or policy object that will consume it
- Write a change-control card that an examiner would accept for rule promotion
- Recognize anti-patterns that turn opaque BeanShell into an audit finding

---

## Why this matters

**Business.** Last quarter, `priya.wire`'s Wire Portal entitlement grant stalled for two days because a nameless BeforeProvisioning snippet threw a null pointer and nobody knew which rule owned the plan. Custom logic fills gaps connectors and out-of-box workflows cannot — correlation, plan mutation, computed attributes, cert exclusions — but only if it is *findable*, *owned*, and *promotable*.

**Control / audit.** Untracked BeanShell in production is an OCC finding waiting to happen. When the examiner asks *"show me every rule that can rewrite an AD disable,"* your answer must be an inventory of named `MNB-Rule-*` objects with owners, promotion path (SSD/SSB), and peer-review evidence — not a fishing trip through Debug. This lesson builds that catalog before later lessons put real logic in the bodies.

---

## Concepts

### What a "rule" is in IdentityIQ

A **rule** is a named, typed script (usually BeanShell, sometimes wrapping compiled Java) that IdentityIQ invokes at a documented hook: during aggregation, correlation, identity refresh, form rendering, provisioning, certification, policy evaluation, or workflow steps. The **rule type** is not cosmetic — it determines the method signature, the arguments the engine passes in, and which objects can attach the rule.

Think of rule types as contracts: a Correlation rule must return an Identity (or null); a BeforeProvisioning rule receives a `ProvisioningPlan` and may mutate it; a FieldValue rule returns a single field value. Attach the wrong type and the engine fails at runtime — or worse, silently skips your logic.

### The Meridian catalog (when to use what)

From `lab-data/connectors/rules/README.md`, expanded with Meridian "when to use" guidance:

| Rule type | When Meridian uses it | Meridian example |
| --- | --- | --- |
| **BuildMap** | Delimited/JDBC row → resource object map before account create | HR CSV columns → `employeeId`, `manager` on `MNB-HR` |
| **Correlation** | Account → Identity matching when native keys need logic | Match AD `employeeID` to cube `employeeId` for `jordan.reed` |
| **IdentityCreation** | Defaults on brand-new cubes from authoritative source | Set `status=active` when HR creates `nina.joiner` |
| **IdentityAttribute** | Computed identity attributes during refresh | `displayName` = `Last, First (employeeId)` — Lesson 92 |
| **FieldValue** | Form field defaults on request / create forms | Prefill `changeTicket` with `MNB-` — Lesson 94 |
| **Provisioning** | Customize plan generation (less common than Before/After) | Rare at Meridian; prefer BeforeProvisioning |
| **BeforeProvisioning** | Mutate plan *before* connector execute | Leaver OU / disable attributes on `MNB-ActiveDirectory` — Lesson 91 |
| **AfterProvisioning** | Post-actions after connector result | Open ServiceNow ticket on privileged disable — Lesson 91 |
| **ResourceObjectCustomization** | Tweak aggregated resource objects before correlation | Normalize OU DN case from AD |
| **Policy** | Custom policy evaluation beyond OOTB SoD | Wire SoD edge cases — later policy lessons |
| **Workflow** | Logic inside LCM / custom workflow steps | Log IdentityRequest id without PII — Lesson 93 |
| **CertificationExclusion** | Remove items that should never appear on a cert | Exclude break-glass service accounts from manager certs |
| **Report** | Custom report data sources | Ops inventory extracts |
| **Listener** | Lifecycle event hooks (create/modify/delete identity) | Notify on high-risk attribute change |

The naive approach — one giant Workflow rule that "does everything" — fails at a bank under exam because you cannot certify, promote, or unit-test a 500-line opaque script. Meridian prefers the *smallest* typed rule at the *right* hook.

### Why stubs before bodies

Creating empty (comment-only) stubs in Lesson 89 is deliberate enterprise discipline:

1. **Inventory exists before logic** — Task Results and Debug searches already show `MNB-Rule-*`.
2. **Names are frozen** — Applications and mappings reference names; renaming later breaks attachments.
3. **Change control starts early** — peer review and SSD promotion apply to stubs the same as production code.
4. **Later lessons fill bodies** — 90–92 teach BeanShell vs Java, Before/After Prov, and IdentityAttribute without inventing new names.

Stub names (empty body OK until later lessons):

- `MNB-Rule-BuildMap-HR`
- `MNB-Rule-Correlation-EmployeeId`
- `MNB-Rule-BeforeProv-AD`
- `MNB-Rule-AfterProv-Ticket`
- `MNB-Rule-IdentityAttribute-DisplayName`

### Wrong way vs Meridian way

| Wrong way | Why it fails under exam | Meridian way |
| --- | --- | --- |
| Edit BeanShell live in prod Debug | No promotion evidence; drift from lab | SSD/SSB only; Debug locked in prod |
| Untitled rule "fix correlation" | Cannot inventory or own | `MNB-Rule-Correlation-EmployeeId` + owner |
| SoD only in Workflow BeanShell | No Policy object, no cert/mitigate UX | Policy rule + Policy object |
| Correlation that returns first identity | False positives; wrong cubes get accounts | Explicit employeeId equality + null on miss |

---

## How it works

Rules do not run "whenever." The engine calls them at fixed points in object processing:

```
Account Aggregation (e.g. MNB-HR, MNB-ActiveDirectory)
        │
        ▼
 BuildMap / ResourceObjectCustomization
        │  (shape the resource object)
        ▼
 Correlation rule ──► link to Identity cube (or leave uncorrelated)
        │
        ▼
 Identity refresh
        │
        ├── IdentityCreation (new cubes only)
        └── IdentityAttribute (computed attrs, e.g. displayName)
        │
        ▼
 LCM / Access Request / Cert remediation
        │
        ▼
 Compile ProvisioningPlan
        │
        ▼
 BeforeProvisioning ──► mutate AttributeRequests / ops safely
        │
        ▼
 Connector execute (AD, Google, file lab, …)
        │
        ▼
 AfterProvisioning ──► tickets, notifications (idempotent)
```

| Lifecycle stage | Rule types that fire | Meridian control owner |
| --- | --- | --- |
| Inbound aggregation | BuildMap, ResourceObjectCustomization | App owner + IAM (`helen.ross`) |
| Matching | Correlation | IAM Academy / Identity Ops |
| Cube shaping | IdentityCreation, IdentityAttribute | IAM Ops |
| Request UX | FieldValue, form validation | IAM + app owner |
| Outbound provision | BeforeProvisioning, AfterProvisioning | IAM + Security for privileged apps |
| Governance | Policy, CertificationExclusion, Workflow | Risk / Cert owners |

One consequence worth remembering: **attaching a rule is a configuration change equal in risk to changing correlation or schema.** Treat rule XML as code — versioned, reviewed, promoted.

---

## Real-world setup (outside the lab UI)

Even though this lesson creates stubs in Debug, production Meridian follows a promotion path you must understand now:

### Step 1 — Author in lower environment

1. Develop rules in lab/dev IIQ or in source control as XML under the SailPoint Services Standard Build (SSB/SSD) project.
2. Name with `MNB-Rule-<Type>-<Purpose>`; set Description and Owner (`helen.ross` or `MNB-WG-IAM-Ops` from Lesson 96).

### Step 2 — Code review gate

1. Peer review for BeforeProvisioning, AfterProvisioning, Policy, and Correlation — at minimum.
2. Checklist: no secrets, no unrestricted `Runtime.exec`, no PII in logs, null-safe, idempotent side effects (Lesson 90).
3. For BeanShell: OWASP-minded review of string concatenation into LDAP filters / SQL / shell (script injection risk).

### Step 3 — Promote via SSD/SSB

1. Export rule XML into the build; never "copy-paste into prod Debug."
2. Deploy with the same CAB ticket as Application / Identity Mapping changes that reference the rule.
3. Smoke-test with known personas (`jordan.reed`, `priya.wire`) before declaring done.

### Step 4 — Inventory discipline

1. Maintain an `MNB-Rule-*` inventory export (you will produce one in Task 6).
2. Orphan rules (no Application / mapping / workflow reference) are tech debt — retire or document.

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq` as `spadmin`; Debug → Rules access
- [ ] Copy `lab-data/connectors/rules/README.md` to `~/iiq-lab-data/connectors/rules/`
- [ ] Binder folder ready: `rules/catalog/`
- [ ] Lesson 88 connector/gateway concepts clear enough that "plan" and "aggregation" are familiar

---

## Lab procedure

### Task 1 — Study the cheat sheet

Every production rule program starts with a shared catalog so two engineers do not invent two names for the same hook. You will annotate the lab README into a personal Meridian cheat sheet.

1. Open `~/iiq-lab-data/connectors/rules/README.md` (or the repo path if copy is missing).
2. Copy the rule-type table into your binder; add a column **Meridian example**.
3. Fill examples using personas and apps you already know:
   - Correlation → `employeeId` match for `jordan.reed` on AD
   - BeforeProv-AD → OU / leaver flag on disable for `samir.hassan`-style leavers
   - AfterProv-Ticket → ticket on Wire / PAM privileged disable for `priya.wire`
   - IdentityAttribute-DisplayName → `Wire, Priya (MNB00xxx)` pattern
4. Star the five stub types you will create in Task 2.

**Expected result:** Annotated cheat sheet with a Meridian examples column and five starred stubs.

**If it fails:** Use repo `lab-data/connectors/rules/README.md` directly; content is identical.

### Task 2 — Create five stub rules in Debug

In production these would land via SSD import. In lab, Debug creates the inventory objects later lessons attach to Applications and Identity Mappings.

1. Debug → Rules → Add New (or equivalent menu path).
2. For each stub name from Concepts:
   - **Name** exact (case-sensitive): e.g. `MNB-Rule-Correlation-EmployeeId`
   - **Type** matching purpose (Correlation, BuildMap, BeforeProvisioning, AfterProvisioning, IdentityAttribute)
   - **Source:** comment only — `// Meridian stub — Lesson 89 — body filled in later lessons`
   - **Owner / description:** IAM Academy; control owner `helen.ross`
3. Save each. Confirm all five appear in the Rules list with the `MNB-Rule-` prefix.

**Expected result:** Five Rules listed: BuildMap-HR, Correlation-EmployeeId, BeforeProv-AD, AfterProv-Ticket, IdentityAttribute-DisplayName.

**If it fails:** Create XML import stubs with the same names; types must still match. Comment-only bodies avoid BeanShell compile errors.

### Task 3 — Trace map: rule → object → future lesson

Stubs without a home become orphan inventory. Map each stub to what will attach it and which lesson fills the body.

Build this table in the binder:

| Stub | Attaches to | Lesson that fills body |
| --- | --- | --- |
| `MNB-Rule-BuildMap-HR` | `MNB-HR` Delimited / JDBC path | Earlier HR / refresh lessons |
| `MNB-Rule-Correlation-EmployeeId` | Apps needing employeeId match | Correlation track (17–18) |
| `MNB-Rule-BeforeProv-AD` | `MNB-ActiveDirectory` | Lesson 91 |
| `MNB-Rule-AfterProv-Ticket` | Critical apps (AD, PAM, Wire) | Lesson 91 |
| `MNB-Rule-IdentityAttribute-DisplayName` | Identity Mappings | Lesson 92 |

Add a note: Lesson 90 decides BeanShell vs compiled Java *before* you write complex BeforeProv logic.

**Expected result:** Trace map in binder linking stubs → objects → lessons.

### Task 4 — Change control card

Meridian does not promote rules by tribal knowledge. Write a one-page card an examiner could read:

1. **No direct prod edit** — SSD/SSB promotion only (preview Lesson 101); Debug locked in prod-like environments.
2. **Peer review required** for BeforeProvisioning, AfterProvisioning, Policy, and Correlation.
3. **Unit / persona tests** for Correlation using known cubes (`helen.ross`, `jordan.reed`, `raj.external`).
4. **Logging policy** — no full SSN, account numbers, or wire amounts in rule logs; prefer request ids and application names.
5. **Owner** — `helen.ross` / `MNB-WG-IAM-Ops`; CAB ticket required for prod deploy.

**Expected result:** One-page change control card signed (initialed) in the binder.

### Task 5 — Negative catalog (what not to use)

Showing what you refuse is as important as the catalog. List three anti-patterns with a one-line "why forbidden":

1. Business SoD enforced only in opaque Workflow rules with no Policy object — no mitigate UX, no cert line.
2. Correlation that always returns the first Identity in a search — silent mis-links, nightmare remediation.
3. AfterProvisioning that calls external HTTP without timeout, retry policy, and idempotency key — duplicate tickets / hung threads on every retry.

Initial the list. You will revisit AfterProv idempotency in Lesson 91 and BeanShell security in Lesson 90.

**Expected result:** Anti-pattern list initialed in binder.

### Task 6 — Registry of existing rules

Inventory is living evidence. Produce today's baseline so drift is visible later.

1. Debug → search Rules with prefix `MNB-`.
2. Export or copy the name list to binder `MNB-Rule-Inventory-YYYY-MM-DD.txt` (use today's date).
3. Flag any non-stub custom rules (bodies beyond Lesson 89 comments) for review.
4. Note orphans: rules with no Application / Identity Mapping / Workflow reference yet (stubs are expected orphans until 91–92).

**Expected result:** Inventory file saved; flags noted.

### Task 7 — Examiner question drill

*"Show me every rule that can affect Active Directory provisioning."*

Write the three-artifact answer: (1) Application `MNB-ActiveDirectory` Rules tab screenshot (will show attachments after Lesson 91), (2) `MNB-Rule-Inventory-*.txt` listing BeforeProv/AfterProv stubs, (3) change control card proving promotion discipline.

**Expected result:** Written proof steps in the binder (attachments may be "pending Lesson 91" — that is fine).

---

## Acceptance criteria

- [ ] **Bank craft exit:** New Meridian rules land under `config/Rule/` with `MNB-Rule-*` names (HelloWorld + Correlation already seeded)

- [ ] Annotated cheat sheet complete with Meridian examples column
- [ ] Five named stubs created with correct types and comment-only bodies
- [ ] Trace map links stubs to future lessons and attach points
- [ ] Change control card written (SSD, peer review, logging, owner)
- [ ] Anti-patterns listed and initialed
- [ ] Inventory export saved with today's date
- [ ] Examiner proof steps drafted

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Wrong rule type in dropdown | Mis-click at create time | Recreate with correct type; type is hard to change safely later |
| Name collision | Prior lab run left same name | Reuse the stub (preferred) or rename old with `-retired` suffix |
| Cannot save BeanShell | Syntax error in "empty" body | Comment-only lines; no unmatched braces |
| Missing type in dropdown | Version / license variance | Closest type + Description note of intended type |
| Too many orphan rules | No inventory hygiene | Run Task 6 monthly; retire unused |
| README not in runtime path | Copy step skipped | Use repo `lab-data/connectors/rules/README.md` |

---

## Training binder evidence

- Annotated README / cheat sheet table
- Screenshots of five `MNB-Rule-*` stubs
- Trace map (stub → object → lesson)
- Change control card
- Anti-pattern list
- `MNB-Rule-Inventory-YYYY-MM-DD.txt`
- Examiner proof steps

---

## Knowledge check

1. Which rule type mutates a provisioning plan *before* the connector executes?
2. Which rule type computes identity attributes during refresh?
3. Name the Meridian AfterProvisioning stub from this lesson.
4. Where is the lab rule cheat sheet, and why do stubs come before bodies?
5. Why is "Correlation that returns the first identity" forbidden at Meridian?
6. What promotion path replaces editing BeanShell directly in production Debug?

### Answers

1. BeforeProvisioning.
2. IdentityAttribute.
3. `MNB-Rule-AfterProv-Ticket`.
4. `lab-data/connectors/rules/README.md` (copied to `~/iiq-lab-data/connectors/rules/`); stubs freeze names/inventory/change control before complex logic.
5. It causes silent false correlations — accounts link to the wrong cube with no deterministic key.
6. SSD/SSB (Services Standard Build) promotion with peer review and CAB — never hot-edit prod Debug.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search "rule types" and "BeanShell rules" for the version-specific rule reference and argument signatures.
- [SailPoint Community / Compass](https://community.sailpoint.com/) — search "BeforeProvisioning rule best practices" for real-world plan mutation patterns and pitfalls.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — threads on rule promotion via SSB and Debug lockdown in prod.
- [OWASP Code Review Guide — Injection](https://owasp.org/www-project-code-review-guide/) — mindset for reviewing BeanShell that builds LDAP filters, SQL, or commands from identity attributes.
- [NIST SP 800-53 CM / AU families (overview)](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — configuration management and audit evidence expectations that map to rule inventory + promotion.

---

## Stretch lab

Add stubs `MNB-Rule-CertificationExclusion-BreakGlass` and `MNB-Rule-Policy-WireSoD` (comment bodies only). Update your inventory file and add rows to the trace map pointing at future cert/policy lessons. Do not implement exclusion or SoD logic yet.

---

## Summary

- Meridian standardizes rule names and types from the lab cheat sheet; the type is a contract with the engine.
- Comment-only stubs establish inventory, ownership, and change control before later lessons fill bodies.
- Promotion via SSD, peer review for high-risk types, and examiner-ready inventory are part of the control — not optional polish.

---

**Previous:** [Lesson 88 — Connector Gateway / Cloud Patterns](88-connector-gateway-cloud-patterns.md)  
**Next:** [Lesson 90 — BeanShell vs Java Rules](90-beanshell-vs-java-rules.md)
