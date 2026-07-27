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

- Explain **BeforeProvisioning** vs **AfterProvisioning** in the plan lifecycle
- Implement safe Meridian stub logic comments and a minimal BeforeProv plan annotation
- Attach `MNB-Rule-BeforeProv-AD` and `MNB-Rule-AfterProv-Ticket` to an Application
- Test with a lab-safe IdentityRequest or plan preview without harming live AD
- Capture Task Result / plan evidence for the training binder

---

## Why this matters

**Business.** Leavers must land in the right OU and ticket queues without manual AD clicks. Plan mutation encodes bank policy into every disable.

**Control / audit.** Silent plan changes without rules inventory are dangerous. Examiners ask what rewrites provisioning before it hits AD—and what fires after success/failure.

---

## Concepts

```
LCM / cert / refresh
        │
        ▼
 Compile provisioning plan
        │
        ▼
 BeforeProvisioning  ◄── mutate AttributeRequests / OU / ops
        │
        ▼
 Connector execute
        │
        ▼
 AfterProvisioning   ◄── tickets, notifications, follow-up plans
```

| Rule | Meridian stub | Intent |
| --- | --- | --- |
| BeforeProvisioning | `MNB-Rule-BeforeProv-AD` | On disable/leaver, ensure OU/attribute policy |
| AfterProvisioning | `MNB-Rule-AfterProv-Ticket` | Open/update ticket on privileged or failed changes |

**Lab-without-live-target:** Attach rules to Delimited `MNB-ActiveDirectory` (or AD shell). Mutate plan fields that exist on file connector; do not require IQService.

---

## Before you start

- [ ] Stubs from Lesson 89 exist
- [ ] Application `MNB-ActiveDirectory` (Delimited lab) available
- [ ] Debug + Task Results access
- [ ] Binder: `rules/before-after-prov/`

---

## Lab procedure

### Task 1 — Lifecycle whiteboard

1. Draw the Concepts flow in binder.
2. Mark failures: BeforeProv exception aborts execute; AfterProv should not undo connector success carelessly.
3. Write: AfterProv must be idempotent (ticket create once per Request ID).

**Expected result:** Annotated flow diagram.

---

### Task 2 — Flesh BeforeProv stub (safe)

1. Open `MNB-Rule-BeforeProv-AD`.
2. Replace body with commented pseudocode + minimal safe BeanShell that logs plan application name only (no PII). Example intent comments:

```text
// IF operation is Disable on MNB-ActiveDirectory
// THEN ensure AttributeRequest department/ou placeholder = "OU=Leavers,..."
// LAB: set a custom attribute "mnbLeaverFlag" = "true" on plan account request if supported
```

3. If comfortable, implement only a null-safe loop that reads plan applications and writes `log.warn("MNB BeforeProv plan apps="+...);` without changing targets yet.
4. Save.

**Expected result:** Rule saves; contains Meridian leaver intent comments.

**If it fails:** Comments-only body still passes if attachment Tasks succeed.

---

### Task 3 — Flesh AfterProv stub (safe)

1. Open `MNB-Rule-AfterProv-Ticket`.
2. Add comments: create ServiceNow ticket when app in `{MNB-ActiveDirectory, MNB-PAM-CyberArk}` and operation Disable; include IdentityRequest id.
3. Optional: log result status at INFO without account numbers.
4. Save.

**Expected result:** AfterProv stub documents ticket hook; no external HTTP required in lab.

---

### Task 4 — Attach rules to Application

1. Open `MNB-ActiveDirectory` → Rules / Provisioning Rules section (labels vary).
2. Set Before Provisioning Rule = `MNB-Rule-BeforeProv-AD`.
3. Set After Provisioning Rule = `MNB-Rule-AfterProv-Ticket`.
4. Save Application.
5. Screenshot configuration.

**Expected result:** Both rules linked on the Application.

**If it fails:** Debug Application XML; set rule references by name.

---

### Task 5 — Exercise a lab plan

1. Pick identity `jordan.reed` or `nina.joiner`.
2. Trigger a **safe** entitlement remove or attribute update on `MNB-ActiveDirectory` (file connector).
3. Open IdentityRequest / provisioning plan; confirm BeforeProv ran (log line or mutated attribute if implemented).
4. Open Task Results; capture success.
5. If no execute path: use plan preview / “normalize plan” style tools if available—or document dry-run limitation.

**Expected result:** Evidence of rule attachment + at least log/preview proof.

**If it fails:** Keep file path valid (Lesson 47); do not point at live AD.

---

### Task 6 — Failure injection note

Write: If BeforeProv throws, connector should not execute; show how you would find the error (Task Result / log). Do **not** leave a throwing rule saved—revert to safe comments/log-only.

**Expected result:** Failure note + confirmation rule is non-throwing.

---

## Acceptance criteria

- [ ] Lifecycle diagram annotated
- [ ] BeforeProv and AfterProv stubs updated with Meridian intent
- [ ] Rules attached to `MNB-ActiveDirectory`
- [ ] Lab plan exercise evidenced (or documented dry-run limit)
- [ ] Rule left in non-throwing state
- [ ] Idempotency note for AfterProv written

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Rule not firing | Not attached / wrong app | Re-check Application rules tab |
| Plan unchanged | Comments-only body | Expected unless you implemented mutation |
| File provision fail | Bad path | Restore CSV path |
| AfterProv double tickets | Not idempotent | Key on IdentityRequest id |
| BeanShell error | Null plan | Null-check account requests |

---

## Training binder evidence

- Lifecycle diagram
- Rule source screenshots
- Application rule attachment screenshot
- IdentityRequest / Task Result evidence
- Idempotency + failure notes

---

## Knowledge check

1. Which rule runs before the connector?
2. Name both Meridian stubs used here.
3. Why must AfterProv be idempotent?
4. What lab application do you attach to?
5. What should you do after a throwing test?

### Answers

1. BeforeProvisioning.  
2. `MNB-Rule-BeforeProv-AD` and `MNB-Rule-AfterProv-Ticket`.  
3. So retries do not create duplicate tickets/side effects.  
4. `MNB-ActiveDirectory` (lab Delimited/shell).  
5. Revert to safe non-throwing rule body immediately.

---

## Stretch lab

Add OU AttributeRequest mutation for Disable operations in BeforeProv against a custom attribute your schema supports; re-test one IdentityRequest.

---

## Summary

- BeforeProv mutates plans; AfterProv handles post-actions like tickets.
- Meridian attaches named stubs to AD governance apps and proves them with lab file provisioning.
- Advanced lesson keeps rules safe, logged, and idempotent.

---

**Previous:** [Lesson 90 — BeanShell vs Java Rules](90-beanshell-vs-java-rules.md)  
**Next:** [Lesson 92 — Identity Attribute Rules](92-identity-attribute-rules.md)
