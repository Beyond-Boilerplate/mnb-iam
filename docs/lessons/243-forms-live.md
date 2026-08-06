# Lesson 243 — Forms & Field Validation

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~50 minutes  
**Prereq:** Lesson 221  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 94

> **Why:** Forms stop requesters from submitting garbage. A blank or one-word "business justification" is useless when someone later asks why access was granted.

## What this is

Every Access Request in the Manage Access flow is rendered by an IIQ `Form` object — the same mechanism Lesson 242's approval work item and role provisioning policies use. The stock request form accepts any free-text justification, including a blank one. This lesson adds a real minimum-length validation rule, proves it blocks a bad submission and allows a good one, then exports the form.

## Know these

| Object | Detail |
| --- | --- |
| Form field | Justification/comments on the Access Request form |
| Validation script | Must return a `String` error message or `null` — not `false`/throw |
| Export target | `config/Form/` |

**Wrong way:** Returning `false` or throwing from a BeanShell validation script — it raises a generic error instead of your message, which defeats the point of writing one.

## Intent

- Locate the Form object backing the Access Request justification field.
- Add a validation rule requiring a minimum character length (e.g. 20 characters).
- Submit a too-short justification and confirm the form blocks submission with a clear message.
- Submit a valid justification and confirm the request proceeds normally.
- Export the form to `config/Form/` once the validation is proven.

## Before you start

- [ ] Lesson 221 request flow working for `helen.ross`
- [ ] Know which workflow renders the request form (`MNB-Workflow-Access-Approval` or LCM request workflow)
- [ ] `helen.ross` / `LabUser1!` credentials on hand
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/243`

## Do this

1. **Setup → Forms** (or trace the form from `MNB-Workflow-Access-Approval`'s early steps). Open the justification/comments field's definition.  
   **Expect:** Field definition located and editable.
2. Add a **Validation** script or `minLength` validator: reject values under 20 characters with `Justification must be at least 20 characters — explain business need, not just "need access".`  
   **Expect:** Script returns a `String` error message on failure, `null` on pass.
3. Save the form.  
   **Expect:** No DTD/schema errors on save.
4. As `helen.ross` (`LabUser1!`), **Manage Access → Request Access**, add an entitlement, type `need it` as justification, attempt to submit.  
   **Expect:** Blocked inline with your validation message — not a generic error page.
5. Replace with a real sentence over 20 characters (e.g. `Need CRM access to support Commercial Banking client onboarding this quarter.`). Submit again.  
   **Expect:** Request proceeds; note the `IdentityRequest` id.
6. Export the form: Debug page export or Object Exporter to `config/Form/MNB-Form-AccessRequest-Justification.xml`, scrubbing internal ids per `config/README.md`.  
   **Expect:** File re-importable.
7. Save the blocked-submission screenshot, the successful `IdentityRequest` id, and the exported form path under `~/iiq-lab-evidence/sandbox/243/`.

## If it fails

- **Can't find the exact form** — check **Manage Access → Request Access**'s underlying workflow for a `Form` reference in its early steps; UI screen name and internal `Form` name often differ.
- **Validation script errors instead of showing your message** — must return a `String` or `null`; fix the return type.
- **Valid submission also gets blocked** — check trimmed-whitespace handling; padded spaces can falsely pass or fail length checks.

## You are done when

The form blocks a too-short justification with your message and allows a valid one through to a real `IdentityRequest`.

## Control note

- **Control:** Business-justification quality gate on access requests.  
- **Owner:** IAM Engineering + Access Governance.  
- **SLA (lab):** Sub-20-character justifications never reach an `IdentityRequest`.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/243/` + `config/Form/MNB-Form-AccessRequest-Justification.xml`.

## Quick check

1. What must a BeanShell validation script return on failure? → A `String` error message (not `false`/throw).  
2. Where does the request form's real name usually differ from what you'd guess? → The workflow that renders it, not the UI screen label.  
3. Why export to `config/Form/`? → So the validation survives a rebuild (248's promotion path).

## Navigate

- Previous: Lesson 242
- Next: Lesson 244
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
