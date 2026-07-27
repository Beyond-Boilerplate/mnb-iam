# Lesson 13 — Onboard AWS Cloud Admin

**Level:** Intermediate  
**Track:** Applications  
**Time:** 60–75 min  
**Prereq:** Lesson 12 (`MNB-SAP-Finance`; Jordan toxic pair context)  

**Lab data:**
- Repo: `lab-data/apps/MNB-AWS-Cloud.csv`
- Runtime path: `~/iiq-lab-data/apps/MNB-AWS-Cloud.csv`

---

## Learning objectives

You will be able to:

- Onboard **MNB-AWS-Cloud** with entitlement **AWS_ADMIN** (critical privileged cloud access)
- Complete the **jordan.reed** toxic combination (`SAP_FI` + `AWS_ADMIN`)
- Recognize **raj.external** as a vendor-email / contractor orphan-correlation risk
- Keep create-identities off and document cloud ownership (`christopher.hayes` intent)
- Capture privileged-access aggregation evidence for exam and SOC narratives

---

## Why this matters

**Business.** AWS account administration can create IAM users, alter logging, and reach production workloads. Meridian treats `AWS_ADMIN` as break-glass-adjacent privilege—never birthright, always certified.

**Control / audit.** Cloud admin combined with finance SoR access is an explicit SoD failure. Separately, vendor emails that do not match corporate `@meridiannb.com` patterns break naive email correlation and create **uncorrelated privileged accounts**—a favorite examiner finding.

---

## Concepts

**Privileged target application.** Same Delimited File pattern as Core/SAP, but every active `AWS_ADMIN` is high scrutiny.

**Two seeded stories in one file:**

| Persona | Email | employeeId | Story |
| --- | --- | --- | --- |
| `jordan.reed` | `jordan.reed@meridiannb.com` | MNB00092 | Toxic with SAP_FI |
| `raj.external` | `raj.contractor@vendor-mail.invalid` | MNB00093 | Contractor; vendor email → correlation edge case |

```
MNB-AWS-Cloud.csv
   │
   ├─ jordan.reed + AWS_ADMIN  ──► pairs with MNB-SAP-Finance SAP_FI
   └─ raj.external + AWS_ADMIN ──► email ≠ @meridiannb.com
                                   employeeId still MNB00093 (HR has contractor)
```

**Correlation preview (Lessons 17–18):** Prefer `employeeId` over email. Email-only rules falsely orphan Raj even though HR knows `MNB00093`. Email-only rules that are too loose can also false-merge strangers—precision matters.

Extract size: **9** accounts (mix of active/disabled).

> **Production reality.** A quarterly CSV of cloud admins is exactly the anti-pattern Lesson 76 dismantles: cloud access changes hourly, and a stale extract certifies a fiction. Production Meridian governs AWS with the **native AWS IAM connector** (Lesson 76) — continuous aggregation of users, groups, directly-attached policies, and access keys — plus Okta group governance (Lesson 73) for federated access. This lesson's CSV app `MNB-AWS-Cloud` is retired on a documented plan once the native app is proven (see Lesson 76, Task 8).

---

## Before you start

- [ ] IIQ up as `spadmin`
- [ ] `~/iiq-lab-data/apps/MNB-AWS-Cloud.csv` present
- [ ] `MNB-SAP-Finance` aggregated; Jordan’s SAP_FI noted
- [ ] HR contains `raj.external` (contractor, `workerType` Contractor) and `jordan.reed`
- [ ] Dictionary: AWS_ADMIN critical, non-requestable; owner intent `christopher.hayes`

---

## Lab procedure

### Task 1 — Inspect the AWS extract

1. Open `~/iiq-lab-data/apps/MNB-AWS-Cloud.csv`.
2. Confirm header matches other platform apps.
3. Locate:
   - `jordan.reed` → `AWS_ADMIN`, `active`
   - `raj.external` → email **`raj.contractor@vendor-mail.invalid`**, `AWS_ADMIN`, `active`
4. List disabled AWS admins (`anita.ross`, `benjamin.mehta`)—retain as signal.
5. Notebook: “Raj vendor mail will break email-only correlation.”

**Expected result:** Nine rows understood; Jordan and Raj flagged for later lessons.

**If it fails:** Ensure you did not open Wire or SAP file by mistake.

---

### Task 2 — Create MNB-AWS-Cloud

1. Applications → Add New → Delimited File named `MNB-AWS-Cloud`.
2. Absolute path to the CSV; comma; header yes.
3. Owner temporary `spadmin`.
4. Save.

**Expected result:** Application object exists with `MNB-` naming.

---

### Task 3 — Schema, non-authoritative, entitlement

1. Schema attributes from CSV.
2. Account id: `userName`.
3. Entitlement attribute: `entitlement` → `AWS_ADMIN`.
4. **Disable** identity creation.
5. Save.

**Expected result:** Target app ready; will not mint identities for vendor-looking accounts.

**If it fails:** If someone previously enabled create-identities on a cloud app, turn it off before aggregating.

---

### Task 4 — Aggregate MNB-AWS-Cloud

1. Create Account Aggregation task `Aggregate MNB-AWS-Cloud`.
2. Run Now. Record counts.
3. Confirm task success with ~**9** accounts.

**Expected result:** Jordan and Raj accounts present in IIQ application account list with `AWS_ADMIN`.

**If it fails:** Path/schema first; then check for locked file handles.

---

### Task 5 — Ownership and privileged control narrative

1. Set owner to `christopher.hayes` (Director of Technology) if available; else document proxy.
2. Enrich `AWS_ADMIN` managed attribute: display name “AWS Admin”; critical; **not** requestable; description mentions cloud account administration.
3. Binder narrative:

```text
AWS_ADMIN is privileged. Requests require Technology owner + manager.
Combination with SAP_FI is prohibited (SoD).
Vendor/contractor admins require employeeId correlation and sponsor review.
```

**Expected result:** Privileged handling is explicit before request/cert lessons.

---

### Task 6 — Verify toxic combination on jordan.reed

1. Open `jordan.reed` cube.
2. Confirm (linked or via app lists):
   - `MNB-SAP-Finance` / `SAP_FI` active
   - `MNB-AWS-Cloud` / `AWS_ADMIN` active
3. Mark notebook: **SoD candidate ready** for Lessons 39–41.
4. Optional: open `reference/sod-matrix.csv` and read the SAP_FI/AWS_ADMIN rationale line.

**Expected result:** Jordan holds both critical entitlements in lab data as designed.

**If it fails:** Re-aggregate the missing app; do not manually invent entitlements on the cube.

---

### Task 7 — Flag raj.external orphan risk

1. Open application `MNB-AWS-Cloud` → account `raj.external`.
2. Note email domain `vendor-mail.invalid`.
3. Search Identities for `raj.external` / `MNB00093` — HR cube should exist from authoritative aggregate.
4. Observe whether the AWS account is already linked. If uncorrelated, **do not** “fix” it by creating a second identity or changing HR email casually.
5. Binder: “Lesson 18 edge case — precision correlation via employeeId.”

**Expected result:** You understand Raj as a correlation/remediation persona, not a missing-HR bug.

**If it fails:** If no HR cube for Raj, re-aggregate `MNB-HR` first—authoritative source must exist before blaming correlation.

---

### Task 8 — Privileged access evidence pack

1. Screenshot aggregation result.
2. Screenshot Jordan dual entitlements (or two app account screenshots).
3. Screenshot Raj account highlighting vendor email.
4. Write one exam answer sentence: *Cloud admin is governed in `MNB-AWS-Cloud`; toxic finance overlap is detectable after correlation via SoD policy.*

**Expected result:** Binder can support a privileged-access walkthrough.

---

## Acceptance criteria

- [ ] `MNB-AWS-Cloud` non-authoritative app created and aggregated (~9 accounts)
- [ ] `AWS_ADMIN` mapped and marked critical / non-requestable
- [ ] `jordan.reed` confirmed SAP_FI + AWS_ADMIN toxic pair
- [ ] `raj.external` vendor email and orphan risk documented
- [ ] Technology owner documented (`christopher.hayes` or proxy)

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Raj creates a new identity | Create-identities on | Disable immediately; clean up |
| Jordan missing AWS | Wrong CSV / failed task | Re-run Aggregate MNB-AWS-Cloud |
| Email match “works” for everyone except Raj | Expected | Use employeeId in Lesson 17–18 |
| Confused orphan vs terminated | Mixing Raj and Samir | Raj=contractor email risk; Samir=leaver residual |
| Owner blank on certs later | Never set app owner | Set `christopher.hayes` now |

---

## Training binder evidence

1. `MNB-AWS-Cloud` application + task result
2. Jordan toxic pair proof
3. Raj vendor-email account proof
4. SoD matrix excerpt for SAP_FI vs AWS_ADMIN
5. Privileged access control narrative paragraph

Examiner question: *“Show a privileged cloud admin that might not correlate on email.”* → `raj.external`.

---

## Knowledge check

1. What entitlement does `MNB-AWS-Cloud` govern?
2. Why is `jordan.reed` important in this lesson?
3. What makes `raj.external` a correlation edge case?
4. Should AWS aggregation create identities for unknown admins?
5. Who is the intended Meridian application owner?

### Answers

1. `AWS_ADMIN`.
2. Completes the toxic SAP_FI + AWS_ADMIN combination for SoD demos.
3. Email is `raj.contractor@vendor-mail.invalid`, not `@meridiannb.com`, so email-only correlation fails or is unreliable; `employeeId` MNB00093 is the reliable key.
4. No — privileged unknowns must become uncorrelated accounts for investigation, not new cubes.
5. `christopher.hayes` (Director of Technology), with `spadmin` as lab proxy if needed.

---

## Further reading

- Lesson 76 — AWS IAM connector (native upgrade path from this CSV).
- [CIS Amazon Web Services Foundations Benchmark](https://www.cisecurity.org/benchmark/amazon_web_services) — IAM user and access-key controls.
- [AWS IAM best practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html) — why static extracts fail for cloud admin governance.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “AWS connector.”

## Stretch lab

- Compare AWS_ADMIN holders in `MNB-AWS-Cloud` vs `itAccess=AWS_ADMIN` rows in `MNB-IT-Access.csv`.
- Draft a 24-hour SLA for “new uncorrelated AWS_ADMIN account” triage (used in Lesson 19).

---

## Summary

- **MNB-AWS-Cloud** onboards critical cloud admin access.
- **jordan.reed** now demonstrates the finance + cloud toxic pair.
- **raj.external** seeds vendor-email correlation and uncorrelated privileged remediation.

---

**Previous:** [Lesson 12 — Onboard SAP Finance](12-onboard-sap-finance.md)  
**Next:** [Lesson 14 — Onboard Wire Portal](14-onboard-wire-portal.md)
