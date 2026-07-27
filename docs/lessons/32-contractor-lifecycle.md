# Lesson 32 — Contractor & Contingent Worker Lifecycle

**Level:** Intermediate  
**Track:** Lifecycle  
**Time:** 60–75 minutes  
**Prereq:** Lesson 31 (leaver disablement); populations from Lesson 07; AWS app from Lesson 13  

**Lab data:**
- `lab-data/hr/MNB-HR-Employees.csv` — filter `workerType=Contractor`
- Spotlight identity: `raj.external` (`MNB00093`) — `lab-data/apps/MNB-AWS-Cloud.csv`
- Related: `lab-data/reference/entitlement-dictionary.csv` (`AWS_ADMIN` critical)

---

## Learning objectives

You will be able to:

1. Inventory Meridian contractors from HR using `workerType=Contractor`.
2. Define a contractor birthright policy that is stricter than employees (minimal or request-only directory access).
3. Enforce expiry / end-date expectations for contractors holding `AWS_ADMIN`, using `raj.external` as the worked example.
4. Draft a manager attestation cadence for contingent workers.
5. Tie poor contractor onboarding data (vendor email) to correlation and offboarding risk.
6. Explain to Risk why contractors must not inherit broad employee birthright packs.

---

## Why this matters

**Business:** Contractors often outlive their statement of work (SOW) in the directory and cloud. A Cloud Platform Engineer with standing `AWS_ADMIN` after SOW end is an unpaid insider with production keys.

**Control / audit:** Regulators expect separate joiner/leaver SLAs and attestation for contingent workers. Control owner: IAM with Technology (cloud) and HR (worker type / end dates). Examiner question: *How do you prevent contractors from receiving employee birthright, and how do you expire cloud admin?*

---

## Concepts

### Worker type as a first-class control attribute

| `workerType` | Birthright expectation | Privileged access | Attestation |
| --- | --- | --- | --- |
| `Employee` | `MNB-Role-Employee` / ELDAP pack (Lesson 24) | Role / request with approvals | Periodic manager cert |
| `Contractor` | Minimal or request-only; no broad packs | Mandatory end date + tighter SLA | Monthly manager attestation |

### Spotlight — `raj.external`

| Field | Value | Control implication |
| --- | --- | --- |
| employeeId | `MNB00093` | Correlate on employeeId if email fails |
| email | `raj.contractor@vendor-mail.invalid` | Breaks email-based correlation |
| manager | `christopher.hayes` (`MNB00002`) | Cloud/tech manager owns attestation |
| job | Cloud Platform Engineer (`ITP` / `CLD01`) | AWS entitlement expected but must expire |
| entitlement | `AWS_ADMIN` active in AWS extract | Critical — weekly review while active |

### Contractor lifecycle (ASCII)

```text
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
                    │
         SOW end / status=0
                    ▼
         Same-day privileged disable (Lesson 31 rigor)
```

**IIQ terms:** *Population* (e.g. `MNB-Contractors`) filters identities for certs and reports. *Birthright* is automatic role assignment—contractors should usually be excluded via assignment rule (`workerType == "Employee"`). *Attestation / certification* is the evidence that the manager still needs the contractor.

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq`; login as `spadmin`.
- [ ] `~/iiq-lab-data/` includes HR and `apps/MNB-AWS-Cloud.csv`.
- [ ] Population `MNB-Contractors` exists (Lesson 07) or you can recreate: `workerType equals Contractor`.
- [ ] You understand Jordan’s leaver residual pattern (Lesson 31)—contractors use the same privileged urgency.
- [ ] Notebook for policy and attestation cadence.

---

## Lab procedure

### Task 1 — Inventory contractors from HR

1. Open `~/iiq-lab-data/hr/MNB-HR-Employees.csv` (or your live HR feed).
2. Filter / search `Contractor` in the `workerType` column.
3. List at least: `raj.external`, plus other contractors (e.g. `rachel.khatri`, `james.nguyen`, `priya.torres`, `grace.howard`, `rohan.price` if present).
4. In IIQ, open population `MNB-Contractors` (or Advanced Search on identity attribute `workerType` = `Contractor`) and compare counts.

**Expected result:** Written contractor roster with employeeId, manager, department, and whether each holds privileged entitlements.

**If it fails:** Confirm `workerType` is mapped on the HR application schema (Lesson 05).

---

### Task 2 — Define contractor birthright policy

1. Open the employee birthright role from Lesson 24 (e.g. `MNB-Role-Employee` or equivalent).
2. Confirm assignment logic requires `workerType` = `Employee` (or excludes Contractor).
3. Write Meridian policy text:

```text
MNB Contractor Birthright Policy
- Default: no automatic business-app birthright.
- Directory (ELDAP): allowed only when SOW requires interactive login; else request-only.
- CRM / Wire / SAP / Core / AWS: never birthright for contractors.
- Joiner SLA: identity created within 1 business day of HR active row; access only via request or explicit SOW pack.
```

4. Identify one contractor who incorrectly looks “employee-like” in access (notebook).

**Expected result:** Policy paragraph + confirmation that employee birthright does not assign to `workerType=Contractor`.

**If it fails:** Document the gap and open a config ticket—do not broaden birthright to “fix” contractors.

---

### Task 3 — AWS contractor expiry for `raj.external`

1. Open identity `raj.external` in the Identity Warehouse.
2. Confirm AWS / `AWS_ADMIN` linkage (or note uncorrelated account if email blocked correlation—Lesson 17/18).
3. Open `~/iiq-lab-data/apps/MNB-AWS-Cloud.csv` and locate:

```text
raj.external,...,AWS_ADMIN,active
```

4. Draft expiry controls (lab standard):

| Control | Meridian rule |
| --- | --- |
| End date source | HR `terminationDate` or companion SOW end-date attribute |
| Max standing AWS for contractor | Align to SOW end; never open-ended |
| While active | Weekly manager + cloud owner review |
| After SOW | Same-day disable (Sev-1), same as privileged leaver |

5. Add remediation note for vendor email: onboarding must use `@meridiannb.com` alias or correlation on `employeeId` only—tie to “contractor onboarding email quality.”

**Expected result:** Worked example showing `raj.external` as the poster child for AWS expiry + correlation hygiene.

**If it fails:** If identity missing, aggregate HR + AWS; if uncorrelated, record as finding and continue with file evidence.

---

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

---

### Task 5 — Ghost / orphan risk write-up

1. Compare Raj’s HR email (`vendor-mail.invalid`) to Meridian domain standard `@meridiannb.com`.
2. Write a short finding:

```text
Finding: Contractor cloud admin with non-Meridian email increases uncorrelated/orphan risk
and delays leaver disablement. Remediation: require Meridian alias before AWS grant;
correlate on employeeId; include contractors in orphan hunt (Lesson 20).
```

3. Link to Lesson 31: when Raj’s SOW ends, treat AWS disable with Jordan-level urgency.

**Expected result:** Finding suitable for training binder and for Technology onboarding checklist.

---

## Acceptance criteria

- [ ] Contractor inventory produced from HR / population.
- [ ] Birthright policy excludes broad employee packs for contractors.
- [ ] `raj.external` AWS_ADMIN expiry + weekly review documented.
- [ ] Monthly (and privileged weekly) attestation cadence written.
- [ ] Vendor-email / correlation finding recorded.

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

1. Filtered HR screenshot or exported contractor list.
2. Population `MNB-Contractors` membership count.
3. Birthright policy text excluding contractors.
4. `raj.external` cube + AWS CSV line.
5. Attestation cadence table.
6. Vendor-email finding note.

---

## Knowledge check

1. How should contractor birthright differ from employee birthright at Meridian?
2. What attestation cadence applies to contingent workers generally vs AWS contractors?
3. Why is `raj.external` a special risk beyond “is a contractor”?
4. Which manager owns Raj’s attestation in the lab data?
5. Should `CRM` or `WIRE_INIT` ever be contractor birthright?

### Answers

1. Contractors get minimal/request-only access; employees may get approved birthright packs. No broad automatic business entitlements for contractors.
2. Monthly manager attestation for all contractors; weekly for those with `AWS_ADMIN`.
3. Holds critical `AWS_ADMIN` and uses a vendor email that undermines correlation and timely offboarding.
4. `christopher.hayes` (`MNB00002`).
5. No—those are request or job-pack only with approvals, never contractor birthright.

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
