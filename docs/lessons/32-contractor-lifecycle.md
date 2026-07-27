# Lesson 32 — Contractor & Contingent Worker Lifecycle

**Level:** Intermediate  
**Track:** Lifecycle  
**Time:** 60–75 minutes  
**Prereq:** Lesson 31 (leaver disablement); populations from Lesson 07; AWS app from Lesson 13  

**Lab data:**
- `lab-data/hr/MNB-HR-Employees.csv` — filter `workerType=Contractor`
- Spotlight identity: `raj.external` (`MNB00093`) — `lab-data/apps/MNB-AWS-Cloud.csv`
- Related: `lab-data/reference/entitlement-dictionary.csv` (`AWS_ADMIN` critical)
- Birthright exclusion: Lesson 24 `MNB-Birthright-Employee` requires `workerType=Employee`

---

## Learning objectives

You will be able to:

- Inventory Meridian contractors from HR using `workerType=Contractor`
- Define a contractor birthright policy that is stricter than employees (minimal or request-only directory access)
- Enforce expiry / end-date expectations for contractors holding `AWS_ADMIN`, using `raj.external` as the worked example
- Draft a manager attestation cadence for contingent workers
- Tie poor contractor onboarding data (vendor email) to correlation and offboarding risk
- Explain to Risk why contractors must not inherit broad employee birthright packs

---

## Why this matters

**Business.** Contractors often outlive their statement of work (SOW) in the directory and cloud. `raj.external` is a Cloud Platform Engineer with standing `AWS_ADMIN` and a vendor mailbox (`raj.contractor@vendor-mail.invalid`). After SOW end he is an unpaid insider with production keys—unless IAM treats contingent workers as a first-class lifecycle, not a watered-down employee.

**Control / audit.** Regulators expect separate joiner/leaver SLAs and attestation for contingent workers. Control owner: IAM with Technology (cloud) and HR (worker type / end dates). Examiner question: *How do you prevent contractors from receiving employee birthright, and how do you expire cloud admin?*

---

## Concepts

### Worker type as a first-class control attribute

| `workerType` | Birthright expectation | Privileged access | Attestation |
| --- | --- | --- | --- |
| `Employee` | `MNB-Birthright-Employee` / ELDAP (Lesson 24) | Role / request with approvals | Periodic manager cert |
| `Contractor` | Minimal or request-only; no broad packs | Mandatory end date + tighter SLA | Monthly manager attestation |

### Spotlight — `raj.external`

| Field | Value | Control implication |
| --- | --- | --- |
| employeeId | `MNB00093` | Correlate on employeeId if email fails |
| email | `raj.contractor@vendor-mail.invalid` | Breaks email-based correlation |
| manager | `christopher.hayes` (`MNB00002`) | Cloud/tech manager owns attestation |
| job | Cloud Platform Engineer (`ITP` / `CLD01`) | AWS entitlement expected but must expire |
| entitlement | `AWS_ADMIN` active in AWS extract | Critical — weekly review while active |

### Why vendor email is a governance defect

Lessons 17–18 taught precision correlation. Raj’s vendor domain means email-only policies create orphans—or false merges if you loosen matching. Privileged orphans delay leaver disablement. Onboarding must require a `@meridiannb.com` alias **before** AWS grant, or correlate strictly on `employeeId`.

### The wrong way

Broadening `MNB-Birthright-Employee` to “fix” contractors who cannot log in. That grants every contingent worker the employee pack forever. Correct path: exclude contractors from employee birthright; define a minimal contingent pack or request-only directory; privilege only via request with end date.

---

## How it works

Contractor lifecycle is HR signal → role exclusion → privileged request with expiry → attestation → same-day privileged disable at SOW end.

```
SOW start ──► HR row (workerType=Contractor, end date)
                    │
                    ▼
         Aggregate MNB-HR + Refresh
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
 Minimal birthright      Privileged via request
 (or ELDAP only)         (AWS_ADMIN + expiry)
        │                       │
        └───────────┬───────────┘
                    ▼
         Monthly manager attestation
         (weekly if AWS_ADMIN)
                    │
         SOW end / status=0
                    ▼
         Same-day privileged disable (Lesson 31 rigor)
```

| Control | Meridian rule |
| --- | --- |
| Birthright | Employee pack excludes Contractor |
| End date source | HR `terminationDate` or companion SOW end-date attribute |
| Max standing AWS | Align to SOW end; never open-ended |
| While AWS active | Weekly manager + cloud owner review |
| After SOW | Same-day disable (Sev-1) |

**IIQ terms:** *Population* (e.g. `MNB-Contractors`) filters identities for certs and reports. *Birthright* assignment rules must require `workerType == "Employee"`. *Attestation / certification* is evidence the manager still needs the contractor.

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq`; login as `spadmin`
- [ ] `~/iiq-lab-data/` includes HR and `apps/MNB-AWS-Cloud.csv`
- [ ] Population `MNB-Contractors` exists (Lesson 07) or you can recreate: `workerType equals Contractor`
- [ ] You understand Jordan’s leaver residual pattern (Lesson 31)—contractors use the same privileged urgency
- [ ] Notebook for policy and attestation cadence

---

## Lab procedure

### Task 1 — Inventory contractors from HR

You cannot control what you cannot list. Start with a roster.

1. Open `~/iiq-lab-data/hr/MNB-HR-Employees.csv` (or your live HR feed).
2. Filter / search `Contractor` in the `workerType` column.
3. List at least: `raj.external`, plus other contractors (e.g. `rachel.khatri`, `james.nguyen`, `priya.torres`, `grace.howard`, `rohan.price` if present).
4. In IIQ, open population `MNB-Contractors` (or Advanced Search on identity attribute `workerType` = `Contractor`) and compare counts.

**Expected result:** Written contractor roster with employeeId, manager, department, and whether each holds privileged entitlements.

**If it fails:** Confirm `workerType` is mapped on the HR application schema (Lesson 05).

### Task 2 — Define contractor birthright policy

Employee birthright must already exclude contractors—verify, then write policy text Risk can sign.

1. Open the employee birthright role from Lesson 24 (`MNB-Birthright-Employee`).
2. Confirm assignment logic requires `workerType` = `Employee` (or excludes Contractor).
3. Write Meridian policy text:

```text
MNB Contractor Birthright Policy
- Default: no automatic business-app birthright.
- Directory (ELDAP): allowed only when SOW requires interactive login; else request-only.
- CRM / Wire / SAP / Core / AWS: never birthright for contractors.
- Joiner SLA: identity created within 1 business day of HR active row; access only via request or explicit SOW pack.
```

4. Identify one contractor who incorrectly looks “employee-like” in access (notebook). Confirm `raj.external` does **not** hold `MNB-Birthright-Employee`.

**Expected result:** Policy paragraph + confirmation that employee birthright does not assign to `workerType=Contractor`.

**If it fails:** Document the gap and open a config ticket—do not broaden birthright to “fix” contractors.

### Task 3 — AWS contractor expiry for `raj.external`

Raj is the poster child: critical entitlement + dirty identity data.

1. Open identity `raj.external` in the Identity Warehouse.
2. Confirm AWS / `AWS_ADMIN` linkage (or note uncorrelated account if email blocked correlation—Lesson 17/18).
3. Open `~/iiq-lab-data/apps/MNB-AWS-Cloud.csv` and locate:

```text
raj.external,...,AWS_ADMIN,active
```

4. Draft expiry controls:

| Control | Meridian rule |
| --- | --- |
| End date source | HR `terminationDate` or companion SOW end-date attribute |
| Max standing AWS for contractor | Align to SOW end; never open-ended |
| While active | Weekly manager + cloud owner review |
| After SOW | Same-day disable (Sev-1), same as privileged leaver |

5. Add remediation note for vendor email: onboarding must use `@meridiannb.com` alias or correlation on `employeeId` only.

**Expected result:** Worked example showing `raj.external` as the poster child for AWS expiry + correlation hygiene.

**If it fails:** If identity missing, aggregate HR + AWS; if uncorrelated, record as finding and continue with file evidence.

### Task 4 — Manager attestation cadence

1. Identify managers of contractors from your roster (e.g. `christopher.hayes` for Raj).
2. Write attestation schedule:

| Population | Cadence | Reviewer | Scope |
| --- | --- | --- | --- |
| `MNB-Contractors` | Monthly | Manager | All accounts/ents |
| Contractors with `AWS_ADMIN` | Weekly | Manager + Technology owner | Cloud admin only |

3. Note future cert campaign name for Lesson 45 style: `MNB-Cert-Contractors-Monthly`.

**Expected result:** Cadence table ready for Risk sign-off; distinguishes all contractors vs AWS subset.

**If it fails:** Use monthly as minimum; privileged weekly is non-negotiable in Meridian training.

### Task 5 — Ghost / orphan risk write-up

1. Compare Raj’s HR email (`vendor-mail.invalid`) to Meridian domain standard `@meridiannb.com`.
2. Write a short finding:

```text
Finding: Contractor cloud admin with non-Meridian email increases uncorrelated/orphan risk
and delays leaver disablement. Remediation: require Meridian alias before AWS grant;
correlate on employeeId; include contractors in orphan hunt (Lesson 20).
```

3. Link to Lesson 31: when Raj’s SOW ends, treat AWS disable with Jordan-level urgency. Link to Lesson 28: CloudAdmin is request-only—contractors never inherit employee packs to “get AWS.”

**Expected result:** Finding suitable for training binder and for Technology onboarding checklist.

### Task 6 — Dual-control and payments exclusion

Contractors must never receive wire initiate/approve birthright. Dual control is employee job packs only.

1. Confirm policy text forbids `WIRE_INIT` / `WIRE_APPR` as contractor birthright.
2. Note: if a contractor needs payments access for a SOW, it is request + Treasury owner approval—never automatic.

**Expected result:** Explicit payments exclusion line in the contractor policy page.

---

## Acceptance criteria

- [ ] Contractor inventory produced from HR / population
- [ ] Birthright policy excludes broad employee packs for contractors
- [ ] `raj.external` AWS_ADMIN expiry + weekly review documented
- [ ] Monthly (and privileged weekly) attestation cadence written
- [ ] Vendor-email / correlation finding recorded

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Population empty | Attribute not mapped / not refreshed | Map `workerType`; Aggregate HR; Refresh |
| Raj missing in IIQ | HR row absent or aggregation skipped | Re-aggregate MNB-HR |
| AWS not on cube | Uncorrelated account | Use employeeId correlation; fix email |
| Contractors got employee role | Assignment rule too broad | Restrict to Employee workerType |
| No end date in HR | Schema gap | Add SOW end attribute or use terminationDate process |

---

## Training binder evidence

1. Filtered HR screenshot or exported contractor list
2. Population `MNB-Contractors` membership count
3. Birthright policy text excluding contractors
4. `raj.external` cube + AWS CSV line
5. Attestation cadence table
6. Vendor-email finding note

**Control owner:** IAM + Technology (cloud) + HR (worker type / end dates)  
**Examiner question:** “How do you prevent contractors from receiving employee birthright, and how do you expire cloud admin?”

---

## Knowledge check

1. How should contractor birthright differ from employee birthright at Meridian?
2. What attestation cadence applies to contingent workers generally vs AWS contractors?
3. Why is `raj.external` a special risk beyond “is a contractor”?
4. Which manager owns Raj’s attestation in the lab data?
5. Should `CRM` or `WIRE_INIT` ever be contractor birthright?
6. Why does vendor email threaten the leaver SLA?

### Answers

1. Contractors get minimal/request-only access; employees may get approved birthright packs. No broad automatic business entitlements for contractors.
2. Monthly manager attestation for all contractors; weekly for those with `AWS_ADMIN`.
3. Holds critical `AWS_ADMIN` and uses a vendor email that undermines correlation and timely offboarding.
4. `christopher.hayes` (`MNB00002`).
5. No—those are request or job-pack only with approvals, never contractor birthright.
6. Uncorrelated privileged accounts delay disablement—the cube never owns the account when HR says SOW ended.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “populations” and “lifecycle events” for contingent-worker filtering and LCM hooks.
- [SailPoint Community](https://community.sailpoint.com/) — search “contractor” / “contingent worker” for birthright exclusion patterns.
- [NIST SP 800-53 AC-2](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — account management for temporary and third-party accounts.
- [NIST SP 800-53 PS-7](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — third-party personnel security; maps to SOW end and attestation.
- [FFIEC IT Handbook — Information Security](https://ithandbook.ffiec.gov/) — third-party and access administration expectations for banks.

---

## Stretch lab

1. Propose a second authoritative **Contingent Worker** delimited file (vendor id, SOW end, badge id) feeding a separate application that correlates to HR `employeeId`.
2. Create or refine population `MNB-Contractors-AWS` (Contractor AND entitlement `AWS_ADMIN`) for weekly certs.
3. Draft an onboarding email template requiring `@meridiannb.com` before cloud access approval.

---

## Summary

- You inventoried Meridian contractors and separated their birthright from employees.
- You hardened AWS expiry and attestation expectations around `raj.external`.
- You connected dirty contractor identity data to correlation and offboarding failure modes.

---

**Previous:** [Lesson 31 — Leaver & Access Disablement](31-leaver-disablement.md)  
**Next:** [Lesson 33 — Leave of Absence Controls](33-leave-of-absence.md)
