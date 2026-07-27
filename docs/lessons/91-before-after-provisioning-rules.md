# Lesson 91 — Before / After Provisioning Rules

**Level:** Advanced  
**Track:** Rules, Workflows, Forms  
**Time:** 75–90 min  
**Prereq:** Lesson 90 — BeanShell vs Java Rules  

**Lab data:**
- Repo: `lab-data/connectors/rules/README.md`
- Repo: `lab-data/apps/MNB-ActiveDirectory.csv` (lab target context)
- Runtime: `~/iiq-lab-data/connectors/rules/`

---

## Learning objectives

You will be able to:

- Explain **BeforeProvisioning** vs **AfterProvisioning** in the provisioning plan lifecycle
- Mutate plans **safely** — only adjust attributes/ops that policy requires; never invent accounts casually
- Implement Meridian intent on `MNB-Rule-BeforeProv-AD` and `MNB-Rule-AfterProv-Ticket` (comments + lab-safe logging)
- Attach both rules to `MNB-ActiveDirectory` and prove they are in the path
- Design AfterProv for **idempotency** (one ticket per IdentityRequest id on retries)
- Capture Task Result / plan evidence for the training binder without harming a live AD

---

## Why this matters

**Business.** When `samir.hassan` left Meridian, the leaver workflow disabled his AD account — but left him in `OU=CommercialLending`. Residual GPOs and nested group quirks kept a mailbox forwarding path alive for three days. BeforeProvisioning is how Meridian encodes "on disable, also enforce leaver OU / flags" into *every* disable, not only the ones a human remembered.

**Control / audit.** Silent plan changes without a rules inventory are dangerous. Examiners ask: *"What rewrites provisioning before it hits AD? What fires after success or failure? Prove retries do not open five ServiceNow tickets."* Named stubs, attachment screenshots, and an idempotency note are the answer.

---

## Concepts

### BeforeProvisioning — mutate the plan, carefully

A **BeforeProvisioning** rule runs after IdentityIQ has compiled a `ProvisioningPlan` and *before* the connector executes it. You may inspect AccountRequests and AttributeRequests, add or adjust attributes (e.g. OU, `mnbLeaverFlag`), or in rare cases change operations — but only when policy demands it.

**Never invent accounts casually.** Creating an AccountRequest for an application the plan did not already target turns a simple attribute update into an unexpected account create. At a bank that is how you get orphan AD objects, license waste, and "who provisioned this?" incidents. Meridian BeforeProv on AD:

- May **enrich** an existing Disable / Modify for `MNB-ActiveDirectory`.
- Must **not** add new Application AccountRequests for unrelated systems.
- Must **null-check** plan, account requests, and attributes before touching them.

### AfterProvisioning — side effects after the connector

An **AfterProvisioning** rule runs after the connector returns a result. Typical uses: open or update a ticket, send a notification, enqueue a follow-up. It should **not** casually undo a successful connector operation, and it must tolerate **retries** — IIQ and connectors may re-enter provisioning paths.

**Idempotency:** if the ticket create keys only on "user disabled," a retry opens a second ticket. Key on IdentityRequest id (or provisioning request id) + application + operation so the second call updates or no-ops.

### Lab vs live AD

```
LCM / cert / refresh / access request
        │
        ▼
 Compile ProvisioningPlan
        │
        ▼
 BeforeProvisioning  ◄── MNB-Rule-BeforeProv-AD
        │                 (mutate OU / leaver attrs on Disable)
        ▼
 Connector execute
        │  lab: Delimited MNB-ActiveDirectory (file)
        │  prod: AD Direct + IQService
        ▼
 AfterProvisioning   ◄── MNB-Rule-AfterProv-Ticket
                          (ticket hook; idempotent; no HTTP required in lab)
```

| Rule | Meridian stub | Intent |
| --- | --- | --- |
| BeforeProvisioning | `MNB-Rule-BeforeProv-AD` | On Disable/leaver, ensure OU / leaver attribute policy |
| AfterProvisioning | `MNB-Rule-AfterProv-Ticket` | Ticket on privileged or failed changes (AD, PAM) |

**Lab-without-live-target:** Attach rules to Delimited `MNB-ActiveDirectory` (or AD shell). Mutate plan fields your schema supports; do not require IQService. Log-only bodies are acceptable if mutation is deferred to stretch.

### Wrong way vs Meridian way

| Wrong way | Why it fails | Meridian way |
| --- | --- | --- |
| BeforeProv creates AD account "just in case" | Orphan accounts; license/audit noise | Only enrich existing AccountRequests |
| AfterProv HTTP with no timeout | Hung threads; cascading failures | Timeouts + idempotent ticket API |
| Throw from BeforeProv "to test" and leave it | Blocks all AD provisioning | Revert immediately to non-throwing |
| Log full DN + SSN on every plan | PII finding | Log app name + request id only |

---

## How it works

| Phase | Engine behavior | Failure semantics |
| --- | --- | --- |
| Plan compile | LCM/cert/request builds AccountRequests | Bad request data → plan errors before rules |
| BeforeProvisioning | Rule may mutate plan | Exception → connector typically does **not** execute |
| Connector | AD / file / SaaS apply ops | Native errors return in result |
| AfterProvisioning | Rule sees result | Should not "un-disable" on ticket failure; log and alert |

```
IdentityRequest IR-24001 (e.g. leaver samir.hassan)
        │
        ▼
 Plan: MNB-ActiveDirectory / Disable (+ attrs)
        │
        ▼
 BeforeProv: add mnbLeaverFlag / OU policy attrs
        │
        ▼
 Connector: success
        │
        ▼
 AfterProv: ensure ticket TCK-… exists for IR-24001 (once)
```

Lesson 90 already classified BeforeProv-AD as a **Java candidate**. This lesson implements **lab-safe** BeanShell comments and logging so you learn the hook without shipping 400 lines of untested script. Production Meridian promotes the Java design note from Lesson 90 via SSB.

---

## Real-world setup (plan mutation discipline)

### Step 1 — Policy before code

1. Write the leaver AD attribute contract: which OU, which flags, which groups are removed by workflow vs BeforeProv.
2. Agree with AD owners (`helen.ross` + directory engineering) — BeforeProv is not a secret side channel around CAB.

### Step 2 — Implement in lower env only

1. Attach `MNB-Rule-BeforeProv-AD` / `MNB-Rule-AfterProv-Ticket` on non-prod `MNB-ActiveDirectory` first.
2. Test with personas: `jordan.reed` (safe modify), `samir.hassan`-style disable path if available.
3. Prefer compiled Java for the real OU mutation (Lesson 90 design note).

### Step 3 — Ticket integration

1. ServiceNow (or equivalent) account with least privilege to create/update incidents.
2. Idempotency key = IdentityRequest id + app + operation.
3. Timeouts and circuit breaking — AfterProv must not block the identity cube forever.

### Step 4 — Promote together

1. Rule XML + Application rule references + any schema attrs (`mnbLeaverFlag`) in one SSD bundle.
2. Peer review mandatory (Lesson 89/90 gates).

---

## Before you start

- [ ] Stubs from Lesson 89 exist; Lesson 90 classification understood
- [ ] Application `MNB-ActiveDirectory` (Delimited lab) available — file path valid
- [ ] Debug + Task Results access at `http://localhost:8080/identityiq`
- [ ] Binder: `rules/before-after-prov/`
- [ ] Do **not** point this lab at live production AD / IQService

---

## Lab procedure

### Task 1 — Lifecycle whiteboard

Before writing a line of BeanShell, fix the mental model. Wrong mental models create invent-account bugs.

1. Draw the Concepts flow in your binder (plan → BeforeProv → connector → AfterProv).
2. Annotate failures: BeforeProv exception aborts execute; AfterProv failure must not casually undo connector success.
3. Write in bold on the page: **AfterProv must be idempotent** (ticket once per Request ID).
4. Write: **BeforeProv must not invent AccountRequests** for apps not already on the plan.

**Expected result:** Annotated flow diagram with failure and idempotency notes.

### Task 2 — Flesh BeforeProv stub (safe)

You are encoding leaver policy intent without risking mass AD creates. Comments + null-safe logging are enough to pass; mutation is optional and schema-bound.

1. Open `MNB-Rule-BeforeProv-AD`.
2. Replace body with Meridian intent comments plus optional lab-safe logging:

```text
// IF operation is Disable on MNB-ActiveDirectory
// THEN ensure AttributeRequest for leaver OU / mnbLeaverFlag per policy
// NEVER add a new AccountRequest for another application
// LAB: prefer log-only or set custom attr your schema already supports
// Promote complex mutation as Java (Lesson 90 design note) via SSB
```

3. If comfortable, implement only a null-safe loop that reads plan applications and writes  
   `log.warn("MNB BeforeProv plan apps="+...);`  
   without creating accounts and without PII.
4. Save. Confirm rule type remains BeforeProvisioning.

**Expected result:** Rule saves; contains Meridian leaver intent comments; no invent-account logic.

**If it fails:** Comments-only body still passes if attachment tasks succeed.

### Task 3 — Flesh AfterProv stub (safe)

1. Open `MNB-Rule-AfterProv-Ticket`.
2. Add comments:
   - Create/update ServiceNow ticket when app in `{MNB-ActiveDirectory, MNB-PAM-CyberArk}` and operation Disable (or failure on privileged change).
   - Include IdentityRequest id; **idempotent** upsert keyed on that id.
   - Timeouts required; no unbounded retries in-rule.
3. Optional: log result status at INFO without account numbers.
4. Save. Do **not** call real HTTP from lab IIQ unless you have a mock endpoint and timeouts.

**Expected result:** AfterProv stub documents ticket hook and idempotency; no required external HTTP in lab.

### Task 4 — Attach rules to Application

Attachment is what makes the inventory examiner-visible on the Application object.

1. Open `MNB-ActiveDirectory` → Rules / Provisioning Rules section (labels vary by version).
2. Set Before Provisioning Rule = `MNB-Rule-BeforeProv-AD`.
3. Set After Provisioning Rule = `MNB-Rule-AfterProv-Ticket`.
4. Save Application.
5. Screenshot the configuration.

**Expected result:** Both rules linked on the Application; screenshot in binder.

**If it fails:** Debug Application XML; set rule references by name; keep Delimited file path intact.

### Task 5 — Exercise a lab plan

Prove the path with a **safe** change — not a production disable.

1. Pick identity `jordan.reed` or `nina.joiner`.
2. Trigger a lab-safe entitlement remove or attribute update on `MNB-ActiveDirectory` (file connector).
3. Open IdentityRequest / provisioning plan; confirm BeforeProv ran (log line or mutated attribute if implemented).
4. Open Task Results; capture success.
5. If no execute path exists in your build: use plan preview / normalize-plan style tools if available — or document dry-run limitation explicitly.

**Expected result:** Evidence of rule attachment + at least log/preview proof on a named persona.

**If it fails:** Restore CSV path from Lesson 47 patterns; do not retarget live AD.

### Task 6 — Failure injection note (then revert)

1. Write: If BeforeProv throws, connector should not execute; find the error in Task Result / `iiq.log`.
2. Optionally test a deliberate throw **only if** you can revert in under two minutes.
3. **Do not leave a throwing rule saved** — revert to safe comments/log-only immediately.
4. Confirm with a second save that the rule is non-throwing.

**Expected result:** Failure note + confirmation rule is non-throwing.

### Task 7 — Idempotency and "never invent accounts" card

Write a half-page card:

1. AfterProv ticket key fields: IdentityRequest id + application + operation.
2. BeforeProv allowed mutations: attribute/OU enrichment on existing AD AccountRequest only.
3. Forbidden: creating accounts on `MNB-WirePortal`, Google, PAM, etc., from AD BeforeProv "for convenience."

**Expected result:** Idempotency + safe-mutation card in binder.

---

## Acceptance criteria

- [ ] Lifecycle diagram annotated (failures + idempotency)
- [ ] BeforeProv and AfterProv stubs updated with Meridian intent
- [ ] Rules attached to `MNB-ActiveDirectory`
- [ ] Lab plan exercise evidenced (or documented dry-run limit)
- [ ] Rule left in non-throwing state
- [ ] Idempotency note and "never invent accounts" card written

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Rule not firing | Not attached / wrong app | Re-check Application rules tab |
| Plan unchanged | Comments-only body | Expected unless you implemented mutation |
| Unexpected new account on another app | Invent-account anti-pattern | Remove that AccountRequest logic immediately |
| File provision fail | Bad Delimited path | Restore CSV path; retest |
| AfterProv double tickets | Not idempotent | Key on IdentityRequest id |
| BeanShell error | Null plan / null lists | Null-check account requests before loops |

---

## Training binder evidence

- Lifecycle diagram with failure notes
- Rule source screenshots (Before + After)
- Application rule attachment screenshot
- IdentityRequest / Task Result evidence (`jordan.reed` or `nina.joiner`)
- Idempotency + never-invent-accounts card
- Failure injection note (and revert confirmation)

---

## Knowledge check

1. Which rule runs before the connector executes?
2. Name both Meridian stubs used here.
3. Why must AfterProv be idempotent?
4. What does "never invent accounts casually" mean for BeforeProv?
5. What lab application do you attach to?
6. What should you do after a throwing BeforeProv test?

### Answers

1. BeforeProvisioning.
2. `MNB-Rule-BeforeProv-AD` and `MNB-Rule-AfterProv-Ticket`.
3. So retries do not create duplicate tickets or duplicate side effects.
4. Do not add AccountRequests for applications that were not already on the plan; only enrich existing requests per policy.
5. `MNB-ActiveDirectory` (lab Delimited/shell).
6. Revert to a safe non-throwing rule body immediately and confirm with a save.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search "BeforeProvisioning" and "AfterProvisioning" for plan object arguments and attachment points on Applications.
- [SailPoint Community / Compass](https://community.sailpoint.com/) — search "BeforeProvisioning best practices" and "ProvisioningPlan AccountRequest" for safe mutation patterns.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — threads on AfterProvisioning idempotency and ticket integration pitfalls.
- [OWASP Application Security Verification Standard](https://owasp.org/www-project-application-security-verification-standard/) — relevant to timeout, retry, and injection concerns when AfterProv calls external ticketing.
- [NIST SP 800-53 SI / CM families](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — change control and flaw remediation mindset for plan-mutating code.

---

## Stretch lab

Add OU / `mnbLeaverFlag` AttributeRequest mutation for Disable operations in BeforeProv against a custom attribute your schema already supports; re-test one IdentityRequest. Still do not invent accounts on other applications. Draft the SSB Java method signature matching Lesson 90's design note.

---

## Summary

- BeforeProv mutates plans safely; AfterProv handles post-actions like tickets — with idempotency.
- Meridian attaches named stubs to `MNB-ActiveDirectory` and proves them with lab file provisioning.
- Never invent accounts casually; never leave throwing rules in place; promote real OU logic as reviewed Java via SSB.

---

**Previous:** [Lesson 90 — BeanShell vs Java Rules](90-beanshell-vs-java-rules.md)  
**Next:** [Lesson 92 — Identity Attribute Rules](92-identity-attribute-rules.md)
