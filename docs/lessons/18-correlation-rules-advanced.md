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
- Sketch safe rule logic an examiner would accept without implementing reckless BeanShell

---

## Why this matters

**Business.** Contractors and vendors often keep non-corporate mailboxes. If IAM cannot attach Raj’s `AWS_ADMIN` account to the HR contractor cube, privilege floats unowned — or worse, a fuzzy rule attaches it to the wrong employee. At Meridian, that is cloud admin access with no manager attestation path.

**Control / audit.** False merges (two people collapsed into one cube) are as bad as orphans for banks: certifications attest the wrong access, SoD fires on the wrong human, and leavers disable the wrong account. Meridian’s standard is **precision first** — leave a few accounts uncorrelated for remediation rather than guess.

---

**Meridian ID map:** HR native key is `userId`. IT dumps use `employeeId` with the **same values** as HR `userId`. Promote/correlate accordingly—do not invent a separate HR `employeeId` column.

## Concepts

### False merge vs false orphan

A **false merge** links an account to the wrong identity. Causes: matching on first name, shared email aliases, truncated IDs, or custom rules that ignore uniqueness. A **false orphan** is an account that *should* match but does not — usually missing primary key, typo, or email-only logic against vendor domains.

Under exam, a false merge is catastrophic because evidence looks “clean”: the account is correlated, certifications ran, SoD “passed” — all on the wrong person. An orphan is visible and remediable (Lesson 19). Prefer visible orphans over silent wrong links.

### Raj’s designed conflict

Meridian seeded Raj specifically so email-centric thinking fails and employeeId thinking succeeds:

| Source | userName | email | employeeId |
| --- | --- | --- | --- |
| HR identity | `raj.external` | `raj.contractor@vendor-mail.invalid` | MNB00093 |
| AWS / IT account | `raj.external` | `raj.contractor@vendor-mail.invalid` | MNB00093 |

Email *can* match if both sides literally share the vendor address — but many enterprise email correlation policies **restrict** to `@meridiannb.com` or normalize corporate mail only. When that policy is in force, email secondary matching never sees Raj. **EmployeeId remains the safe bridge.**

**Real-life Meridian example.** Ops once proposed matching on email local-part (`raj.contractor` ↔ anything) “to catch vendors.” That would also collide with any future `raj.contractor@meridiannb.com` hire or shared alias. Rejected. Raj links on `MNB00093` or waits in uncorrelated with a ticket — never on local-part guesswork.

### Anti-patterns Meridian rejects

```
Bad idea:  match on local-part(email) only     → false merges
Bad idea:  match on lastName + department      → false merges (common names in FIN/ITP)
Bad idea:  auto-create identity when AWS_ADMIN uncorrelated → privileged ghost identities
Good idea: employeeId exact match              → precision
OK secondary: full email exact match           → works for Raj IF both sides identical
```

### Attribute maps vs custom rules

**Attribute assignments** (Lesson 17) cover most Meridian delimited files and many production connectors. Custom correlation **rules** (BeanShell / advanced) appear in mature IIQ shops for multi-step logic (e.g. “employeeId if present; else corporate email only; else leave uncorrelated”). For this lab, prefer configuration precision; only sketch a rule unless your instructor requires deployment. A sketched safe rule is examiner-ready; an untested merge rule is an incident waiting for production.

---

## How it works

Correlation runs per application. Hardening `MNB-IT-Access` does not automatically harden `MNB-AWS-Cloud` — privileged platforms need the same hierarchy configured explicitly, with create-identities **especially** forbidden.

```
Account (raj.external on MNB-AWS-Cloud)
        │
        ▼
Try #1: employeeId == MNB00093  ──► match → Link on raj.external cube
        │ no
        ▼
Try #2: email exact match
        │  (may fail if corporate-only allowlist)
        ▼
No match → uncorrelated (ticket / Lesson 19)
        ✗ never: local-part / lastName+dept / create-identity
```

| Decision | Production consequence |
| --- | --- |
| employeeId first on AWS | Contractor admin accounts attach to HR contractor cubes |
| Exact email only as secondary | No substring collisions across domains |
| Create-identities OFF on AWS | Unmatched AWS_ADMIN enters remediation, not a new cube |
| Document rejected patterns | Training evidence that precision was a choice, not an accident |

---

## Before you start

- [ ] Lesson 17 complete; most staff correlate on `MNB-IT-Access`
- [ ] HR cube exists for `raj.external` / MNB00093 (`employeeType` Contractor)
- [ ] `MNB-AWS-Cloud` aggregated (Lesson 13)
- [ ] Binder section “Correlation edge cases”
- [ ] Agreement: you will **not** invent a second “Raj” identity to force a link

---

## Lab procedure

### Task 1 — Reproduce the edge case

You cannot harden what you have not observed. Start by putting Raj’s HR attributes next to his AWS account attributes — side by side is the training artifact.

1. Open HR identity `raj.external`. Note email and `userId`; confirm Contractor.
2. Open `MNB-AWS-Cloud` account `raj.external`. Note email and `employeeId`; note `AWS_ADMIN`.
3. Open `MNB-IT-Access` account for Raj if present.
4. Observe current link state on each app (correlated vs uncorrelated).
5. Binder: screenshot identity header + AWS account side by side.

**Expected result:** Clear picture of Raj’s attributes and whether AWS/IT accounts already link via employeeId.

**If it fails:** If HR identity missing, re-aggregate `MNB-HR` before debugging correlation.

### Task 2 — Threat-model false merges

Before adding “clever” matching, write down what you refuse to do. This table is often more valuable to an examiner than a successful link screenshot.

1. Write three **rejected** correlation ideas and why:

| Rejected idea | Failure mode |
| --- | --- |
| Match `userName` local part to email local part only | Collisions across domains |
| Match `lastName` + `departmentName` | Common names in FIN/ITP |
| Auto-create identity when AWS_ADMIN uncorrelated | Privileged ghost identities |

2. Write the accepted Meridian rule of thumb: *Unique stable HR id first; exact email second; never create identities from privileged targets.*

**Expected result:** Explicit anti-patterns documented—training evidence that you chose precision knowingly.

### Task 3 — Harden MNB-IT-Access correlation

Stretch experiments from Lesson 17 sometimes leave name-based mappings behind. Remove them now so the inventory app reflects the enterprise standard.

1. Re-open `MNB-IT-Access` correlation config.
2. Confirm **employeeId** mapping exists and is authoritative/first.
3. Keep **exact email** as secondary only—do not add substring/local-part matches.
4. Remove any experimental name-based mappings you may have added in stretch work.
5. Save. Re-run `Aggregate MNB-IT-Access` + Refresh.

**Expected result:** Configuration reflects precision hierarchy; no fuzzy keys.

**If it fails:** UI may show a single combined condition—ensure employeeId equality is present.

### Task 4 — Correlate MNB-AWS-Cloud with the same standard

Privileged platforms are where false orphans hurt most. Configure AWS to the same hierarchy — and leave create-identities off even if the uncorrelated list looks ugly.

1. Open `MNB-AWS-Cloud` → Correlation.
2. Map account `employeeId` → identity `userId`.
3. Map `email` → identity `email` (exact).
4. Create-identities: **OFF** (critical for AWS_ADMIN).
5. Save. Run `Aggregate MNB-AWS-Cloud` + Refresh.

**Expected result:** `raj.external` AWS account links to the contractor cube via employeeId even when email domain looks “wrong” to humans.

**If it fails:** Verify both account and identity have identical `MNB00093`. Typos in CSV vs HR break precision—and should, rather than fuzzy-match.

### Task 5 — Validate jordan.reed still precise

Correlation changes can silently reassign Links. Jordan’s toxic SoD entitlements must stay on Jordan — a false merge here poisons every later certification and policy lesson.

1. Open `jordan.reed`.
2. Confirm SAP and AWS platform accounts still attach to **Jordan**, not another Reed/Foster.
3. Confirm entitlements did not “jump” cubes after correlation changes.
4. Binder note: regression check after correlation hardening.

**Expected result:** No false merge side effects on the toxic SoD persona.

### Task 6 — Optional advanced rule sketch (no unsafe code required)

Mature shops eventually encode the hierarchy in a rule. Practice describing it safely — implementing untested BeanShell against privileged apps is how labs become cleanup weekends.

1. In notebook, draft pseudo-logic only:

```text
if account.employeeId is not blank:
    return identity where userId == account.employeeId
else if account.email endsWith @meridiannb.com:
    return identity where email == account.email
else:
    leave uncorrelated  // vendor mail without employeeId = manual review
```

2. Explain why blank employeeId + vendor email must **not** guess.
3. Do **not** paste unverified BeanShell into production-like lab objects unless your course explicitly practices rule deployment.

**Expected result:** You can describe a safe rule to an examiner without implementing a reckless merge.

### Task 7 — Edge-case register

Ops needs a living list of known exceptions so every residual is not rediscovered from scratch after each pipeline run.

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
| Raj still uncorrelated | `employeeId` missing on account or `userId` missing on identity | Fix source data; do not fuzzy match |
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
3. Exact associate key: IT `employeeId` = HR `userId` = `MNB00093`.
4. Examples: name-only, local-part-only email, lastName+department, auto-create on privileged apps.
5. Unmatched privileged accounts would mint unmanaged privileged identities instead of entering uncorrelated remediation.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “correlation rule” and “account correlation” for attribute assignments vs custom rule hooks in your version.
- [SailPoint Community (Compass)](https://community.sailpoint.com/) — search “false correlation” / “wrong identity linked” for real merge-incident write-ups and recovery patterns.
- [NIST SP 800-63A — Enrollment and Identity Proofing](https://pages.nist.gov/800-63-3/sp800-63a.html) — why unique, stable identifiers matter when binding credentials/accounts to a person.
- [FFIEC IT Examination Handbook — Architecture, Infrastructure, and Operations](https://ithandbook.ffiec.gov/it-booklets/architecture-infrastructure-and-operations.aspx) — examiner expectations for accountable system access and third-party/contractor coverage.
- [CIS Controls v8 — Control 5 (Account Management)](https://www.cisecurity.org/controls/account-management) — industry baseline for inventorying accounts and tying them to known owners.

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
