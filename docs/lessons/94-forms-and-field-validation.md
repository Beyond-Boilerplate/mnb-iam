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

- Locate **provisioning policy forms** and LCM / Access Request forms used in Meridian requests
- Add FieldValue defaults and validation constraints for Meridian naming standards
- Create and attach `MNB-Form-AccessRequest-Extras` with ticket and justification fields
- Prove validation rejects bad input and accepts good input with binder screenshots
- Document ownership and accessibility notes so form text does not become tribal knowledge
- Explain to an examiner why empty “n/a” justifications fail a payments audit

---

## Why this matters

**Business.** Requesters abandon cryptic forms; bad defaults create wrong AD accounts and wrong Wire Portal entitlements. When `marcus.approve` requests access for a teammate and the form offers no ticket field, ServiceNow never gets linked — and ops cannot reconstruct *why* `GRP_WIRE` was granted six months later.

**Control / audit.** Mandatory justification and change-ticket fields produce examiner-ready IdentityRequests. Free-text without validation yields empty “n/a” audit trails. When the OCC asks *"show the business justification and change ticket for Priya’s Wire entitlement,"* the IdentityRequest form fields *are* the answer — if you forced them at request time.

---

## Concepts

### Form types in IdentityIQ

| Form concept | Purpose | Meridian example |
| --- | --- | --- |
| **Provisioning Policy form** | Fields for create/modify on an Application | AD OU, Wire account attributes |
| **Identity Request / LCM form** | Requester inputs during access request | Justification, ticket, cost center |
| **FieldValue rule** | Default or derive a single field value | Prefill `changeTicket` with `MNB-` |
| **Validation** | Required, regex, min length, allowed values | Reject `TEST` as a ticket |

A **form** is not decoration — it is the structured capture of control metadata onto the IdentityRequest and, often, into the provisioning plan. If a field is missing here, no amount of later reporting invents it.

### Why Meridian requires extras on privileged / payments paths

Meridian required extras for privileged and payments requests:

| Field | Constraint | Why |
| --- | --- | --- |
| `businessJustification` | Required; min length **20** | Stops “n/a” / “need access” |
| `changeTicket` | Required; pattern `MNB-[0-9]{4,}` | Links IAM to CAB / ITSM |

**Wrong way:** Hope requesters paste ticket numbers into comments. **Meridian way:** Validate at submit time; reject before the approval workflow even starts.

### Real-life Meridian example

`priya.wire` received a Wire Portal entitlement after a verbal manager approval with justification “ops.” During an internal audit, nobody could find a change ticket. The finding was not “IIQ failed” — it was “request metadata was optional.” This lesson makes metadata mandatory.

### FieldValue vs static default vs workflow mutation

| Approach | When to use | Risk |
| --- | --- | --- |
| Static default on field | Simple prefixes (`MNB-`) | Users overwrite carelessly |
| **FieldValue rule** | Derive from identity/app context | Wrong rule type → silent blank |
| Workflow step mutation | Late enrichment after submit | Too late for UX validation |

Prefer FieldValue / form validation for requester-facing controls; leave Workflow rules for orchestration (Lesson 93), not for fixing empty tickets after the fact.

---

## How it works

```
Requester UI form (Access Request / app policy)
        │
        ├── FieldValue defaults (e.g. changeTicket → "MNB-")
        ├── Validation (required, regex, min length)
        │         │
        │         ├── fail → stay on form with error
        │         └── pass ▼
        ▼
 IdentityRequest stores field values
        │
        ▼
 Approvals (Lesson 93) → ProvisioningPlan (may include form attrs)
        │
        ▼
 Examiner evidence = IdentityRequest detail + ticket pattern
```

| Stage | Object / rule | Meridian owner |
| --- | --- | --- |
| Render | Form `MNB-Form-AccessRequest-Extras` | IAM + app owner (help text) |
| Default | FieldValue `MNB-Rule-FieldValue-TicketPrefix` | IAM Ops |
| Validate | Form validators / scripts | IAM Ops |
| Persist | IdentityRequest attributes | Platform (immutable enough for audit) |
| Attach | App policy or LCM request form config | IAM — scope narrowly first |

---

## Real-world setup (enterprise form discipline)

### Step 1 — Inventory before inventing

1. List provisioning policy forms on `MNB-WirePortal` and `MNB-ActiveDirectory`.
2. List LCM / Access Request forms already in play.
3. Decide whether extras are **global** (all requests) or **app-scoped** (Wire only first).

### Step 2 — Naming and ownership

1. Form name: `MNB-Form-AccessRequest-Extras`.
2. Owner: IAM Academy / `helen.ross`; app owners own entitlement *descriptions*, IAM owns validation *rules*.
3. Help text must show a worked example: `MNB-24001`.

### Step 3 — Validation contract

1. Write expected error messages *before* configuring (binder).
2. Regex: `MNB-[0-9]{4,}` — four or more digits after the prefix.
3. Justification min length 20 — count characters, not words.

### Step 4 — Promote via SSD later

1. Export form XML to `config/Form/` (Lesson 101).
2. Never leave a global attach that breaks every request without a rollback note.

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq`; edit Applications and Forms (Debug)
- [ ] A requestable entitlement available (Wire Portal or IT Access)
- [ ] FieldValue rule type known from Lesson 89 catalog
- [ ] Binder: `forms/`
- [ ] Personas for test: `priya.wire`, `marcus.approve`

---

## Lab procedure

### Task 1 — Inventory forms in play

You cannot attach what you cannot name. Inventory prevents duplicate “justification” fields with three different spellings.

1. Debug → Forms; search recent / LCM / provisioning policy forms.
2. Open Application `MNB-WirePortal` or `MNB-ActiveDirectory` provisioning policies; note form names.
3. List **three** forms in the binder with owners (or “unknown — assign `helen.ross`”).

**Expected result:** Inventory of ≥3 forms with owner column.

**If it fails:** Create a new Form object `MNB-Form-AccessRequest-Extras` from scratch for Tasks 2–6 — still list any OOTB forms you found.

### Task 2 — Create Meridian extras form

In production this is the control metadata contract for payments requests.

1. Create or edit form `MNB-Form-AccessRequest-Extras`.
2. Add fields:
   - `businessJustification` — Textarea, required
   - `changeTicket` — String, required
3. Help text: “Ticket pattern `MNB-1234`; justification must explain business need (min 20 characters). Example ticket: `MNB-24001`.”
4. Owner / description: IAM Academy; control owner `helen.ross`.
5. Save.

**Expected result:** Form object saved with two named fields and help text.

### Task 3 — FieldValue default for ticket prefix

Defaults reduce typos; they do not replace validation.

1. Create rule `MNB-Rule-FieldValue-TicketPrefix` type **FieldValue**, **or** set static default `MNB-` on `changeTicket`.
2. If rule: return `"MNB-"` as default prefix only — requester completes the digits.
3. Attach FieldValue to `changeTicket` if the UI allows.
4. Save. Comment body: `// Meridian Lesson 94 — default ticket prefix`.

**Expected result:** Default prefix or FieldValue attached.

**If it fails:** Document the manual default instruction in help text; validation in Task 4 still carries the control.

### Task 4 — Validation rules

Validation is the control. Help text without reject behavior is decoration.

1. On `businessJustification`: required=true; min length **20** (script/validator per version).
2. On `changeTicket`: regex `MNB-[0-9]{4,}` (or equivalent Allowed Values / validation script).
3. Save form.
4. Write expected error messages in the binder (exact strings if your build shows them).

**Expected result:** Validations configured; expected errors documented.

**If it fails:** Use required-only validation now; enforce pattern in a Workflow rule note for stretch — flag residual risk `RR-FORM-REGEX-01`.

### Task 5 — Attach form to request path

Global attach can break every request in the bank. Scope narrow first.

1. Attach `MNB-Form-AccessRequest-Extras` to Access Request provisioning policy / LCM form configuration / application request form — whichever your version supports for extra requester fields.
2. Prefer scoping to `MNB-WirePortal` Modify / request form for lab before going global.
3. Screenshot the attachment point.
4. Write rollback: detach form name X from policy Y.

**Expected result:** Form reachable from a lab request UI (or preview path documented).

**If it fails:** Preview form from Debug form preview if available; still complete Task 6 logically with predicted accept/reject.

### Task 6 — Prove accept / reject

Examiner evidence is reject *and* accept — not only the happy path.

1. Start an access request for `priya.wire` or `marcus.approve` entitlement add (lab-safe).
2. Attempt submit with empty justification → expect reject.
3. Attempt `changeTicket=TEST` → expect reject.
4. Submit with justification ≥20 chars and `MNB-24001` → expect accept.
5. Capture screenshots of reject and accept; note IdentityRequest id on accept.

**Expected result:** Both reject and accept evidence in binder.

**If it fails:** Use form preview/test harness; record limitation and still write the three attempt outcomes.

### Task 7 — Examiner question drill

*"Show the business justification and change ticket for a Wire entitlement grant."*

Write the three-artifact answer: (1) form definition with validation rules, (2) IdentityRequest detail showing `businessJustification` and `changeTicket=MNB-24001`, (3) attachment screenshot proving the form was on the Wire path.

**Expected result:** Written proof steps in the binder.

---

## Acceptance criteria

- [ ] Form inventory done (≥3)
- [ ] `MNB-Form-AccessRequest-Extras` exists with two fields and help text
- [ ] Validation documented and configured (or residual risk logged)
- [ ] Form attached or previewed on lab path with rollback note
- [ ] Reject + accept evidence captured
- [ ] Examiner proof steps drafted
- [ ] Owner note: IAM owns form; app owners own entitlement text

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Form not shown | Not attached | Re-check policy / LCM form config |
| Regex never fires | Wrong validator type | Use script validation; test with `TEST` |
| Defaults blank | FieldValue not linked | Attach rule or static default |
| Users confused | No help text / examples | Add `MNB-24001` example |
| Breaks all requests | Global mis-attach | Scope to one app; rollback per Task 5 |
| Accepts “n/a” | Min length too low / missing | Enforce 20+; retest |

---

## Training binder evidence

- Form inventory
- Form field screenshots + help text
- Validation rules write-up + expected errors
- Attachment screenshot + rollback note
- Reject + accept screenshots + IdentityRequest id
- Owner note (IAM vs app owner)
- Examiner proof steps

---

## Knowledge check

1. What two Meridian extra fields does this lab add?
2. What ticket regex is required?
3. What rule type defaults field values?
4. What is the minimum justification length?
5. Which payment personas are useful for Wire Portal form tests?
6. Why scope the form to Wire before attaching globally?

### Answers

1. `businessJustification` and `changeTicket`.
2. `MNB-[0-9]{4,}`.
3. FieldValue.
4. 20 characters.
5. `priya.wire`, `marcus.approve`.
6. A bad global attach can block every Access Request in the bank; narrow scope limits blast radius.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “forms,” “provisioning policies,” and “FieldValue rules” for argument signatures and attachment points.
- [SailPoint Community / Compass](https://community.sailpoint.com/) — search “access request form validation” for regex and required-field patterns.
- [OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html) — mindset for allow-lists, length limits, and rejecting bad tickets before they become audit noise.
- [NIST SP 800-53 Rev. 5 — SI-10 / AU-3](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — information input validation and audit record content expectations.
- [FFIEC IT Handbook — Information Security](https://ithandbook.ffiec.gov/) — auditability of privileged access changes (search Information Security booklet).

---

## Stretch lab

Add a FieldValue that sets `ownerEmail` default from the application owner identity email for a create-account form on a lab app. Keep validation on `changeTicket` unchanged. Export the form XML path you would place under `config/Form/` for Lesson 101.

---

## Summary

- Forms capture examiner-grade justification and ticket metadata at request time — not in after-the-fact comments.
- Meridian standardizes extras on `MNB-Form-AccessRequest-Extras` with FieldValue defaults and real validation.
- Prove both rejection and acceptance; scope attachments narrowly; promote via SSD later.

---

**Previous:** [Lesson 93 — LCM Workflow Customization](93-workflow-lcm-customization.md)  
**Next:** [Lesson 95 — QuickLinks and Custom UI](95-quicklinks-custom-ui.md)
