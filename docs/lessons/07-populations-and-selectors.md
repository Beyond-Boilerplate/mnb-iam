# Lesson 07 — Populations & Identity Selectors

| Field | Value |
| --- | --- |
| **Level** | Beginner |
| **Track** | Foundations |
| **Time** | 60 minutes |
| **Prereq** | Lesson 06 (`Refresh MNB Attributes` works; identity attrs populated) |
| **Lab data** | HR-backed identity attributes (`inactive`, `employeeType`, `departmentName` / `JobCode`) |

## Learning objectives

You will be able to:

- Explain why reusable populations beat ad-hoc “all identities” scopes
- Create `MNB-Active-Employees`, `MNB-Contractors`, and `MNB-Treasury` populations
- Attempt a terminated-with-risk search pattern for residual access hunting
- Point a refresh (or copy) at a population and run it
- Document membership logic for audit

## Why this matters

Certifications, reports, and refreshes need scoped populations. “All identities” does not scale, floods managers, and scares auditors who expect risk-based targeting (Treasury first, contractors on short cadence, etc.).

**Control / audit:** Population definitions are reusable controls. Examiners ask how you select who enters a campaign. “We used `MNB-Treasury` where `departmentName` contains Payments/Treasury OR `JobCode`/`division` for Treasury” is a defensible answer.

## Concepts

A **population** (identity selector / group filter—wording varies) is a saved filter over identities by attributes and/or links.

| Population | Logic (intent) | Later use |
| --- | --- | --- |
| `MNB-Active-Employees` | Active workforce (`inactive=false` / `status=Active`) | Default refresh & certs |
| `MNB-Contractors` | `employeeType=Contractor` | Short-cycle certs, tight JML |
| `MNB-Treasury` | `departmentName` contains Payments/Treasury OR `JobCode`/`division` for Treasury | Wire/payments campaigns |
| `MNB-On-Leave` (stretch) | `exceptions=LOA` | Temporary freeze controls |

```text
  Identity attributes
        |
        v
  [Population filter] ---> Refresh / Certification / Report scope
```

**Design rule:** Name populations as durable control objects, not “tmp search 3”.

## How it works

A **population** (identity selector) is a saved filter over Identity attributes and/or Links. Tasks, certifications, and reports reference the population by name so scope stays consistent instead of retyping filters under pressure.

```text
Identity attrs (status, employeeType, departmentName, exceptions (LOA))
        │
        ▼
Population / selector definition (MNB-*)
        │
        ├── Refresh MNB Attributes (population-scoped)
        ├── Certification campaigns
        └── Reports / Advanced Analytics
```

| Population | Typical filter | Control use |
| --- | --- | --- |
| `MNB-Active-Employees` | Active / status=1 | Default refresh & broad certs |
| `MNB-Contractors` | employeeType=Contractor | Short-cycle reviews |
| `MNB-Treasury` | Treasury / Payments dept | Wire/payments campaigns |

**Real-life Meridian example.** Targeting a contractor-only cert at `raj.external`’s peers without a population means someone retypes `employeeType=Contractor` and misses people. `MNB-Contractors` makes the exam answer reproducible.

## Before you start

- [ ] Identities exist from `MNB-HR`
- [ ] Refresh has promoted `inactive`, `employeeType`, `departmentName` / `JobCode` (verify on a few cubes)
- [ ] You know UI path for Populations / Identity Selector / Advanced Analytics (version-dependent)

## Lab procedure

### Task 1 — Verify filterable attributes

Populations only work if the attributes you filter on are present and promoted on cubes—spot-check personas before building selectors.

1. Open `amelia.brooks` — confirm active status and a Retail-related `departmentName` / `division` / `JobCode`.
2. Open `raj.external` — confirm `employeeType=Contractor`.
3. Open `priya.wire` — confirm `departmentName` contains Payments/Treasury OR `JobCode`/`division` for Treasury.
4. Open `samir.hassan` — confirm inactive/terminated.

**Expected result:** You trust the attributes populations will filter on.

**If it fails:** Return to Lessons 05–06 mappings/refresh before building populations.

### Task 2 — Create MNB-Active-Employees

1. Navigate to **Populations** / **Identity Selectors** / Advanced search save-as (or equivalent).
2. Name: `MNB-Active-Employees`.
3. Filter: identities whose HR-driven status indicates active (e.g. `status=1` or inactive=false—match how your mapping stored it).
4. Optionally exclude `employeeType=Contractor` if you want employees-only; document your choice.
5. Save and preview membership count.

**Expected result:** Population saved; member count roughly matches active HR rows (lab ~70+ active depending on exclusions).

### Task 3 — Create MNB-Contractors

1. Create population `MNB-Contractors`.
2. Filter: `employeeType=Contractor`.
3. Preview; confirm `raj.external` appears.

**Expected result:** Non-zero contractor membership including `raj.external`.

### Task 4 — Create MNB-Treasury

1. Create population `MNB-Treasury`.
2. Filter: `departmentName` contains Payments/Treasury OR `JobCode`/`division` for Treasury.
3. Confirm `rachel.evans`, `priya.wire`, `marcus.approve` appear (and other TRS workers).

**Expected result:** Treasury-scoped list suitable for future wire-focused certifications.

### Task 5 — Terminated with residual risk (approximate)

1. Using Advanced Search or a population attempt: inactive/terminated identities.
2. Note: proving “still has IT accounts” may be approximate until `MNB-IT-Access` exists (Lesson 09) and correlation matures (Lessons 17–20).
3. For now, search terminated identities (include `samir.hassan`) and write the control intent: “Leaver population feeds residual-access hunting.”

**Expected result:** Written query/population attempt + note that IT residual proof comes after IT app onboarding.

### Task 6 — Apply population to refresh

1. Clone or edit `Refresh MNB Attributes` (prefer a copy: `Refresh MNB Active Employees` if you want to preserve the broad attrs task).
2. Set filter/population to `MNB-Active-Employees`.
3. Keep **attribute promotion** options on (same purpose as `Refresh MNB Attributes`); do not pile on policy checks.
4. Run once.
5. Capture task result screenshot.

**Expected result:** Refresh succeeds scoped to the population; evidence shows population name/filter in result or task definition.

### Task 7 — Document membership logic

In the binder, for each population write:

| Name | Filter logic | Owner | Review cadence |
| --- | --- | --- | --- |
| MNB-Active-Employees | inactive false | IAM Ops (lab: you) | Quarterly |
| MNB-Contractors | employeeType=Contractor | IAM Ops | Monthly |
| MNB-Treasury | Treasury / Payments dept | Payments + IAM | Quarterly |

**Expected result:** Audit-ready population register page.

### Task 8 — Population vs ad-hoc search drill

1. Run an ad-hoc Advanced Search for `departmentName` contains Payments/Treasury OR `JobCode`/`division` for Treasury without saving.
2. Compare member count to `MNB-Treasury`.
3. Write why the saved population wins for certifications: named control, repeatable, reviewable, referenceable from tasks.
4. Add an examiner-ready sentence: “Campaign X uses population `MNB-Treasury` defined as Treasury/Payments department filter as of [review-date].”

**Expected result:** Counts match (or difference explained); one examiner-ready sentence in the binder.

### Task 9 — Negative test

1. Confirm `amelia.brooks` (RET teller) is **not** in `MNB-Treasury`.
2. Confirm `raj.external` is **not** in `MNB-Active-Employees` if you excluded contractors—or document if you included all actives.
3. Confirm `samir.hassan` is **not** in active employees.

**Expected result:** Negative membership checks written; filter logic trusted.

## Acceptance criteria

- [ ] Three populations created and previewed
- [ ] `raj.external` in contractors; TRS personas in Treasury
- [ ] Terminated search/population attempt documented
- [ ] Population-scoped refresh run with evidence
- [ ] Population register written
- [ ] Ad-hoc vs population comparison + negative tests done
- [ ] CHANGELOG updated

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Empty population | Attribute not on identity / wrong value type | Fix maps; refresh; compare cube attrs |
| String `"1"` vs number | Type mismatch in filter | Match stored type; test with known user |
| Cannot find Populations UI | Version/menu difference | Use Advanced Analytics saved query; note equivalent |
| Refresh ignores filter | Filter not saved on task | Re-open task; confirm population attached |
| Contractors include employees | Wrong attribute / typo | Verify `employeeType` exact value `Contractor` |

## Training binder evidence

- Screenshots: population definitions + member previews
- Screenshot: population-scoped refresh result
- Population register table
- Note linking `MNB-Treasury` to future wire certification scope

**Examiner question:** “How do you scope a certification to Treasury without selecting all bank staff?”

## Knowledge check

1. Why do populations beat ad-hoc filters?
2. Which population should most certifications start with?
3. How do contractors differ in scope/SLA?
4. What attribute defines `MNB-Treasury`?
5. Why is “terminated with IT access” incomplete before Lesson 09?

### Answers

1. Reusable, named, reviewable controls with stable logic—auditable and consistent across tasks/certs.
2. Active employees (or a risk-tiered subset)—not all identities including leavers.
3. Shorter tenure and higher offboarding risk → tighter certification cadence and JML SLAs.
4. `departmentName` contains Payments/Treasury OR `JobCode`/`division` for Treasury.
5. IT accounts/entitlements are not onboarded yet; residual access needs `MNB-IT-Access` (and correlation).

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “population” and “identity selector” for filter syntax and task scoping.
- [SailPoint Community](https://community.sailpoint.com/) — search “certification population” for campaign-scoping patterns used in banks.
- [NIST SP 800-53 AC-6 — Least Privilege](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — scoping reviews and admin work to the right populations.
- [FFIEC IT Examination Handbook — Information Security](https://ithandbook.ffiec.gov/it-booklets/information-security.aspx) — expectations for risk-based review populations (contractors, privileged, payments).
- [CIS Controls v8 — Control 5](https://www.cisecurity.org/controls/account-management) — inventorying and grouping accounts for governance.

## Stretch lab

- Create `MNB-On-Leave` (`exceptions=LOA`) and write which control freezes access for `sofia.torres`.
- Create `MNB-Finance` (`departmentName contains Finance`) for later SoD campaigns targeting `jordan.reed`’s org.
- Export member lists (if UI allows) into evidence for count reconciliation vs HR file.
- Create `MNB-Terminated` on inactive status and attach it as a future input to Lesson 20 orphan/dormant hunting notes.

## Summary

- Populations are reusable scopes for refresh, certs, and reports.
- Meridian baselines: Active Employees, Contractors, Treasury.
- Membership logic belongs in the training binder as control documentation.

---

**Previous:** [Lesson 06 — Identity Cubes & Refresh](06-identity-cubes-and-refresh.md)  
**Next:** [Lesson 08 — Task Operations & Scheduling Discipline](08-task-ops-and-scheduling.md)
