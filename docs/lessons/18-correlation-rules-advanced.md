# Lesson 18 — Correlation Rules & Edge Cases

**Level:** Intermediate  
**Track:** Correlation  
**Time:** 60–90 min  
**Prereq:** Lesson 17 (`MNB-IT-Access` basic correlation)  

**Lab data:**
- Focus identity/account: **`raj.external`** / `MNB00093` / vendor email `raj.contractor@vendor-mail.invalid`
- Apps: `MNB-IT-Access`, `MNB-AWS-Cloud` (privileged orphan risk)
- HR: contractor row in `HRApplications.txt`

---

## Learning objectives

You will be able to:

- Prefer **precision over false merges** when extending correlation beyond simple attribute maps
- Use `employeeId` to correlate vendor-email accounts like **raj.external** without weakening global email matching unsafely
- Identify dangerous correlation patterns (name-only, partial email local-part, overly broad rules)
- Document edge-case handling for contractors and non-`@meridiannb.com` mail
- Apply correlation consistently to at least one privileged platform app (`MNB-AWS-Cloud`)

---

## Why this matters

**Business.** Contractors and vendors often keep non-corporate mailboxes. If IAM cannot attach their cloud admin account to the HR contractor cube, privilege floats unowned—or worse, a fuzzy rule attaches it to the wrong employee.

**Control / audit.** False merges (two people collapsed into one cube) are as bad as orphans for banks: certifications attest the wrong access, SoD fires on the wrong human, and leavers disable the wrong account. Meridian’s standard is **precision first**.

---

## Concepts

**False merge.** Correlation links an account to the wrong identity. Causes: matching on first name, shared email aliases, truncated IDs, or custom rules that ignore uniqueness.

**False orphan.** Account should match but does not—usually missing primary key, typo, or email-only logic against vendor domains.

**Raj’s designed conflict:**

| Source | userName | email | employeeId |
| --- | --- | --- | --- |
| HR identity | `raj.external` | `raj.contractor@vendor-mail.invalid` | MNB00093 |
| AWS / IT account | `raj.external` | `raj.contractor@vendor-mail.invalid` | MNB00093 |

Email *can* match if both sides literally share the vendor address—but many enterprise email correlation policies **restrict** to `@meridiannb.com` or normalize corporate mail only. EmployeeId remains the safe bridge.

```
Bad idea:  match on local-part(email) only     → false merges
Bad idea:  match on lastName + department      → false merges
Good idea: employeeId exact match              → precision
OK secondary: full email exact match           → works for Raj IF both sides identical
```

**Rule types (conceptual).** Attribute assignments (Lesson 17) cover most Meridian files. Custom correlation **rules** (BeanShell/advanced) appear in mature IIQ shops—for this lab, prefer configuration precision; only sketch a rule if your instructor requires it.

---

## Before you start

- [ ] Lesson 17 complete; most staff correlate on `MNB-IT-Access`
- [ ] HR cube exists for `raj.external` / MNB00093 (`workerType` Contractor)
- [ ] `MNB-AWS-Cloud` aggregated (Lesson 13)
- [ ] Binder section “Correlation edge cases”
- [ ] Agreement: you will **not** invent a second “Raj” identity to force a link

---

## Lab procedure

### Task 1 — Reproduce the edge case

1. Open HR identity `raj.external`. Note email and employeeId; confirm Contractor.
2. Open `MNB-AWS-Cloud` account `raj.external`. Note email and employeeId; note `AWS_ADMIN`.
3. Open `MNB-IT-Access` account for Raj if present.
4. Observe current link state on each app (correlated vs uncorrelated).
5. Binder: screenshot identity header + AWS account side by side.

**Expected result:** Clear picture of Raj’s attributes and whether AWS/IT accounts already link via employeeId.

**If it fails:** If HR identity missing, re-aggregate `MNB-HR` before debugging correlation.

---

### Task 2 — Threat-model false merges

1. Write three **rejected** correlation ideas and why:

| Rejected idea | Failure mode |
| --- | --- |
| Match `userName` local part to email local part only | Collisions across domains |
| Match `lastName` + `departmentCode` | Common names in FIN/ITP |
| Auto-create identity when AWS_ADMIN uncorrelated | Privileged ghost identities |

2. Write the accepted Meridian rule of thumb: *Unique stable HR id first; exact email second; never create identities from privileged targets.*

**Expected result:** Explicit anti-patterns documented—training evidence that you chose precision knowingly.

---

### Task 3 — Harden MNB-IT-Access correlation

1. Re-open `MNB-IT-Access` correlation config.
2. Confirm **employeeId** mapping exists and is authoritative/first.
3. Keep **exact email** as secondary only—do not add substring/local-part matches.
4. Remove any experimental name-based mappings you may have added in stretch work.
5. Save. Re-run `Aggregate MNB-IT-Access` + Refresh.

**Expected result:** Configuration reflects precision hierarchy; no fuzzy keys.

**If it fails:** UI may show a single combined condition—ensure employeeId equality is present.

---

### Task 4 — Correlate MNB-AWS-Cloud with the same standard

1. Open `MNB-AWS-Cloud` → Correlation.
2. Map `employeeId` → identity `employeeId`.
3. Map `email` → identity `email` (exact).
4. Create-identities: **OFF** (critical for AWS_ADMIN).
5. Save. Run `Aggregate MNB-AWS-Cloud` + Refresh.

**Expected result:** `raj.external` AWS account links to the contractor cube via employeeId even when email domain looks “wrong” to humans.

**If it fails:** Verify both account and identity have identical `MNB00093`. Typos in CSV vs HR break precision—and should, rather than fuzzy-match.

---

### Task 5 — Validate jordan.reed still precise

1. Open `jordan.reed`.
2. Confirm SAP and AWS platform accounts still attach to **Jordan**, not another Reed/Foster.
3. Confirm entitlements did not “jump” cubes after correlation changes.
4. Binder note: regression check after correlation hardening.

**Expected result:** No false merge side effects on the toxic SoD persona.

---

### Task 6 — Optional advanced rule sketch (no unsafe code required)

1. In notebook, draft pseudo-logic only:

```text
if account.employeeId is not blank:
    return identity where employeeId == account.employeeId
else if account.email endsWith @meridiannb.com:
    return identity where email == account.email
else:
    leave uncorrelated  // vendor mail without employeeId = manual review
```

2. Explain why blank employeeId + vendor email must **not** guess.
3. Do **not** paste unverified BeanShell into production-like lab objects unless your course explicitly practices rule deployment.

**Expected result:** You can describe a safe rule to an examiner without implementing a reckless merge.

---

### Task 7 — Edge-case register

1. Create a living table in the binder:

| Case | Example | Handling |
| --- | --- | --- |
| Vendor email + employeeId | raj.external | Correlate on employeeId |
| Terminated + residual ents | samir.hassan | Lesson 20 hunt |
| Dual digital ents | kai.nguyen | SoD later |
| Typo employeeId | (simulate carefully) | Uncorrelated → remediate |

2. Add control owner: IAM Engineering; reviewer: `helen.ross` (Head of IAM) conceptually.

**Expected result:** Edge-case register ready for ops handoff.

---

## Acceptance criteria

- [ ] Anti-false-merge patterns documented
- [ ] `MNB-IT-Access` correlation hardened (employeeId first; no fuzzy keys)
- [ ] `MNB-AWS-Cloud` correlation configured; create-identities off
- [ ] `raj.external` AWS (and IT if present) linked via employeeId **or** explicitly ticketed if data prevents it
- [ ] Jordan regression check passed
- [ ] Edge-case register started

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Raj still uncorrelated | employeeId missing on account or identity | Fix source data; do not fuzzy match |
| Raj linked to wrong person | Bad secondary rule | Remove rule; re-aggregate; verify MNB00093 |
| New contractor identities spawned | Create-identities on AWS | Disable; delete erroneous cubes |
| Email domain allowlist blocks Raj | Secondary email policy too strict | Rely on employeeId primary |
| Works in IT dump but not AWS | AWS correlation never configured | Task 4 |

---

## Training binder evidence

1. Side-by-side Raj identity vs AWS account attributes
2. Correlation config screenshots for IT-Access and AWS-Cloud
3. Rejected false-merge ideas table
4. Pseudo-rule sketch
5. Edge-case register page

Examiner question: *“Would you correlate on email local-part to catch vendors?”* → **No—false merge risk; use employeeId.**

---

## Knowledge check

1. What is a false merge?
2. Why is `raj.external` the advanced correlation persona?
3. What key should attach Raj’s `AWS_ADMIN` account?
4. Name one correlation anti-pattern Meridian rejects.
5. Why is create-identities especially dangerous on `MNB-AWS-Cloud`?

### Answers

1. Linking an account to the wrong identity.
2. Vendor email domain stresses email-centric matching while employeeId remains valid.
3. Exact `employeeId` = `MNB00093`.
4. Examples: name-only, local-part-only email, lastName+department, auto-create on privileged apps.
5. Unmatched privileged accounts would mint unmanaged privileged identities instead of entering uncorrelated remediation.

---

## Stretch lab

- Intentionally break a **copy** of a lab CSV employeeId (in a scratch file, not the shared lab source if others use it), point a throwaway app at it, and show it stays uncorrelated.
- Extend the same correlation standard to `MNB-SAP-Finance` and `MNB-WirePortal`.

---

## Summary

- Precision beats coverage: avoid false merges even if a few accounts wait for remediation.
- **raj.external** proves employeeId-first correlation for vendor mail and privileged AWS access.
- Edge cases are registered controls, not one-off UI clicks.

---

**Previous:** [Lesson 17 — Account Correlation Basics](17-correlation-basics.md)  
**Next:** [Lesson 19 — Uncorrelated Account Remediation](19-uncorrelated-remediation.md)
