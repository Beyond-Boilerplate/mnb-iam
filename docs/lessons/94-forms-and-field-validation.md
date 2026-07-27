# Lesson 94 — Forms and Field Validation

**Level:** Intermediate  
**Track:** Rules, Workflows, Forms  
**Time:** 60–90 min  
**Prereq:** Lesson 93 — LCM Workflow Customization  

**Lab data:**
- Repo: `lab-data/connectors/rules/README.md` (FieldValue)
- Repo: `lab-data/apps/MNB-WirePortal.csv`
- Runtime: `~/iiq-lab-data/connectors/rules/`

---

## Learning objectives

You will be able to:

- Locate **provisioning policy forms** and LCM forms used in Meridian requests
- Add FieldValue defaults and validation constraints for Meridian naming
- Create/attach `MNB` form fields for ticket number and business justification
- Prove validation rejects bad input and accepts good input
- Document accessibility/ops notes for form owners

---

## Why this matters

**Business.** Requesters abandon cryptic forms; bad defaults create wrong AD accounts.

**Control / audit.** Mandatory justification and ticket fields produce examiner-ready IdentityRequests. Free-text without validation yields empty “n/a” audit trails.

---

## Concepts

| Form concept | Purpose |
| --- | --- |
| Provisioning Policy form | Fields for create/modify on an Application |
| Identity Request / LCM form | Requester inputs during access request |
| FieldValue rule | Default or derive field values |
| Validation | Required, regex, allowed values |

```
Requester UI form
        │
        ├── FieldValue defaults (e.g., email @meridiannb.com)
        ├── Validation (ticket MNB-[0-9]+)
        ▼
 IdentityRequest + provisioning plan fields
```

Meridian required extras for privileged / payments requests:

- `businessJustification` (required, min length 20)
- `changeTicket` (required, pattern `MNB-[0-9]{4,}`)

---

## Before you start

- [ ] IIQ up; ability to edit Applications and Forms (Debug)
- [ ] A requestable entitlement available (Wire Portal or IT Access)
- [ ] FieldValue rule type known from catalog
- [ ] Binder: `forms/`

---

## Lab procedure

### Task 1 — Inventory forms in play

1. Debug → Forms; search recent / LCM / provisioning policy forms.
2. Open Application `MNB-WirePortal` or `MNB-ActiveDirectory` provisioning policies; note form names.
3. List three forms in binder with owners.

**Expected result:** Inventory of ≥3 forms.

**If it fails:** Create a new Form object `MNB-Form-AccessRequest-Extras` from scratch for Tasks 2–5.

---

### Task 2 — Create Meridian extras form section

1. Create or edit form `MNB-Form-AccessRequest-Extras`.
2. Add fields:
   - `businessJustification` — Textarea, required
   - `changeTicket` — String, required
3. Help text: “Ticket pattern MNB-1234; justification must explain business need.”
4. Save.

**Expected result:** Form object saved with two fields.

---

### Task 3 — FieldValue default (optional email)

1. Create rule `MNB-Rule-FieldValue-TicketPrefix` type FieldValue **or** set static default `MNB-` on changeTicket.
2. If rule: return `"MNB-"` as default prefix only—requester completes digits.
3. Attach FieldValue to `changeTicket` if UI allows.
4. Save.

**Expected result:** Default prefix or FieldValue attached.

**If it fails:** Document manual default instruction in help text.

---

### Task 4 — Validation rules

1. On `businessJustification`: required=true; min length 20 (script/validator per version).
2. On `changeTicket`: regex `MNB-[0-9]{4,}` (or equivalent Allowed Values / validation script).
3. Save form.
4. Write expected error messages in binder.

**Expected result:** Validations configured; expected errors documented.

**If it fails:** Use required-only validation and enforce pattern in a Workflow rule note for stretch.

---

### Task 5 — Attach form to request path

1. Attach `MNB-Form-AccessRequest-Extras` to Access Request provisioning policy / LCM form configuration / application request form—whichever your version supports for extra requester fields.
2. Screenshot attachment point.
3. If global attach is risky, attach only to `MNB-WirePortal` provisioning policy Modify form for lab.

**Expected result:** Form reachable from a lab request UI.

**If it fails:** Preview form from Debug form preview if available; still complete Task 6 logically.

---

### Task 6 — Prove accept / reject

1. Start access request for `priya.wire` or `marcus.approve` entitlement add (lab-safe).
2. Attempt submit with empty justification → expect reject.
3. Attempt `changeTicket=TEST` → expect reject.
4. Submit with justification ≥20 chars and `MNB-24001` → expect accept.
5. Capture screenshots of reject and accept.

**Expected result:** Both reject and accept evidence in binder.

**If it fails:** Use form preview/test harness; record limitation.

---

## Acceptance criteria

- [ ] Form inventory done
- [ ] `MNB-Form-AccessRequest-Extras` exists with two fields
- [ ] Validation documented and configured
- [ ] Form attached or previewed on lab path
- [ ] Reject + accept evidence captured
- [ ] Help text references Meridian ticket pattern

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Form not shown | Not attached | Re-check policy/LCM form config |
| Regex never fires | Wrong validator type | Use script validation |
| Defaults blank | FieldValue not linked | Attach rule or static default |
| Users confused | No help text | Add examples `MNB-24001` |
| Breaks all requests | Global mis-attach | Scope to one app; rollback |

---

## Training binder evidence

- Form inventory
- Form field screenshots
- Validation rules write-up
- Attachment screenshot
- Reject + accept screenshots
- Owner note (IAM owns form; app owners own entitlement text)

---

## Knowledge check

1. What two Meridian extra fields does this lab add?
2. What ticket regex is required?
3. What rule type defaults field values?
4. Minimum justification length?
5. Which payment personas are useful for Wire Portal form tests?

### Answers

1. `businessJustification` and `changeTicket`.  
2. `MNB-[0-9]{4,}`.  
3. FieldValue.  
4. 20 characters.  
5. `priya.wire`, `marcus.approve`.

---

## Stretch lab

Add FieldValue that sets `ownerEmail` default from application owner identity email for a create account form on a lab app.

---

## Summary

- Forms capture examiner-grade justification and ticket metadata.
- Meridian standardizes extras on `MNB-Form-AccessRequest-Extras` with validation.
- Prove both rejection and acceptance in the lab UI.

---

**Previous:** [Lesson 93 — LCM Workflow Customization](93-workflow-lcm-customization.md)  
**Next:** [Lesson 95 — QuickLinks and Custom UI](95-quicklinks-custom-ui.md)
