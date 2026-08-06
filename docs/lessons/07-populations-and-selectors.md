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

- Explain why reusable populations beat ad-hoc "all identities" scopes
- Create `MNB-Active-Employees`, `MNB-Contractors`, and `MNB-Treasury` populations
- Distinguish stock `Type` from Meridian's custom `employeeType` attribute when filtering
- Point a refresh (or a copy of one) at a population and run it
- Document population membership logic for audit

## Why this matters

A branch teller and a treasury wire clerk should never land in the same certification with the same cadence. `amelia.brooks` (retail) and `priya.wire` (treasury) carry very different risk, so Meridian scopes campaigns, refreshes, and reports to named **populations** instead of re-typing "all identities" filters under deadline pressure. Ad-hoc scopes don't scale and they don't survive staff turnover on the IAM team.

**Control / audit:** Population definitions are reusable controls. When an examiner asks "how did you select who entered this campaign?", the answer is a named, versioned filter object — "we used `MNB-Treasury`, defined as `departmentName` contains Payments/Treasury" — not "someone typed a query that morning."

## Concepts

A **population** (also called an identity selector or group filter, wording varies by build) is a saved filter over identity attributes and/or links. Once saved, tasks, certifications, and reports reference it by name so scope stays consistent across runs.

| Population | Filter logic | Later use |
| --- | --- | --- |
| `MNB-Active-Employees` | `inactive=false` / `status=Active` | Default refresh & broad certs |
| `MNB-Contractors` | custom `employeeType=Contractor` | Short-cycle certs, tight JML |
| `MNB-Treasury` | `departmentName` contains Payments/Treasury (or `JobCode`/`division`) | Wire/payments campaigns |
| `MNB-On-Leave` (stretch) | `exceptions=LOA` | Temporary freeze controls |

```text
  Identity attributes
        |
        v
  [Population filter] ---> Refresh / Certification / Report scope
```

> **Watch out:** Stock **Type** is usually blank on this lab's cubes. Meridian's contractor flag is the **custom** identity attribute `employeeType` from Lesson 05 — not the stock `Type` dropdown. Filtering on `Type=Employee` silently zeroes out results.

## How it works

Populations sit between raw identity attributes and every consumer that needs a scoped list. Tasks, certifications, and reports reference the population object by name, so the definition — not a retyped query — is the audit trail.

```text
Identity attrs (status, employeeType, departmentName, exceptions=LOA)
        │
        ▼
Population / selector definition (MNB-*)
        │
        ├── Refresh MNB Attributes (population-scoped)
        ├── Certification campaigns
        └── Reports / Advanced Analytics
```

**Real-life Meridian example.** Targeting a contractor-only certification at `raj.external`'s peers without a saved population means someone retypes `employeeType=Contractor` from memory every quarter and eventually mistypes it, or forgets it, and contractors slip into the wrong campaign. `MNB-Contractors` makes the answer reproducible and reviewable.

## Before you start

- [ ] Identities exist from `MNB-HR` (cubes are `MNB…` User Names — see Lesson 05 naming note)
- [ ] Refresh has promoted `inactive`, custom **`employeeType`**, and `departmentName` / `JobCode` — verify on a few `MNB…` cubes
- [ ] Custom filter attributes are **Searchable** in Identity Mappings
- [ ] You can reach Advanced Analytics or Setup → Populations (paths below)

### Where to create populations (IIQ 8.x lab UI)

Populations are **not** under Identities → Identity Warehouse. Use one of these paths, in order of preference:

| Path | Steps |
| --- | --- |
| **A — Setup (if present)** | Top nav **Setup → Populations** → New / Add |
| **B — Advanced Analytics (always works)** | **Intelligence → Advanced Analytics** → search **Identities** → set filters → run → **Save As** / **Save Population** |
| **C — Debug `GroupDefinition` (last resort)** | Object Browser → `GroupDefinition` → New |

If **Setup** has no Populations entry, use path B — it works on every build in this curriculum.

### Filter rules for beginners (read before Task 2)

Filters in Advanced Analytics are **AND**ed. Extra fields left with wrong or empty values zero out your result set.

| Do | Do not |
| --- | --- |
| Filter **Is Inactive = False** for active workers | Also require **Type = Employee** |
| Filter custom **`employeeType` = `Contractor`** for contractors | Use the stock **Type** dropdown for HR employee/contractor |
| Filter **`departmentName`** / **`JobCode`** only after they are promoted + Searchable | Add **Is Manager = True** unless you truly want managers only |
| Clear unused filter rows (including empty Software Version) | Leave blank criteria that still participate in the query |

## Lab procedure

### Task 1 — Verify filterable attributes

Populations only work if the attributes you filter on are present and promoted on cubes. Spot-check a handful of personas before building selectors, so a broken mapping doesn't masquerade as an empty population.

1. Open **`MNB00097`** (`amelia.brooks`) — confirm active (`Is Inactive` false) and a Retail-related `departmentName` / `division` / `JobCode` on the **Identity** attributes (not only on the Link).
2. Open **`MNB00093`** (`raj.external`) — confirm identity attribute **`employeeType=Contractor`**. If you only see a blank stock **Type**, fix the Lesson 05 mapping first.
3. Open **`MNB00090`** (`priya.wire`) — confirm `departmentName` contains Payments/Treasury (or `JobCode`/`division` for Treasury).
4. Open **`MNB00094`** (`samir.hassan`) — confirm inactive/terminated.

**Expected result:** You trust the attributes populations will filter on before you build a single selector.

**If it fails:** Return to Lessons 05–06 mappings/refresh (and UIConfig visibility if the Attributes tab hides custom fields) before building populations.

### Task 2 — Create MNB-Active-Employees

1. Open **Intelligence → Advanced Analytics** (or Setup → Populations).
2. Choose **Identities**. Clear any leftover filters.
3. Set **only**: **Is Inactive** = **False** (label may read `inactive` / "Is Inactive").
4. Run the search — expect a large list (roughly 70+). An empty result means an extra filter (Type, Is Manager, Software Version…) is still attached; remove it and retry.
5. **Save As Population** (wording varies). Name: `MNB-Active-Employees`.
6. Optionally add a second criterion later to exclude `employeeType=Contractor` if you want employees-only; document your choice either way. Do not use stock Type for that exclusion.

**Expected result:** Population saved; member count roughly matches active HR rows.

### Task 3 — Create MNB-Contractors

1. Start a new Advanced Analytics search (or new population).
2. Filter: **`employeeType`** equals **`Contractor`**. If the custom attribute is missing from the picker, enable **Searchable** on `employeeType` in Identity Mappings first.
3. Preview; confirm **`MNB00093`** / Raj External appears.

**Expected result:** Non-zero contractor membership including Raj (`MNB00093`).

### Task 4 — Create MNB-Treasury

1. Create population `MNB-Treasury`.
2. Filter: `departmentName` contains `Treasury` or `Payments` (or `JobCode` / `division` for Treasury — match whatever you promoted).
3. Confirm Rachel (`MNB00005`), Priya (`MNB00090`), and Marcus (`MNB00091`) appear, along with other TRS workers.

**Expected result:** A Treasury-scoped list suitable for a future wire-focused certification.

### Task 5 — Terminated with residual risk (approximate)

Auditors eventually want "terminated staff who still hold IT access" as a standing report. You cannot fully prove that yet — `MNB-IT-Access` doesn't exist until Lesson 09, and correlation matures across Lessons 17–20 — so today's job is to define the population half of that story.

1. Using Advanced Search (or a population attempt), filter **Is Inactive = True** (and/or `status=Terminated` if you promoted `status`).
2. Confirm terminated identities appear, including **`MNB00094`** / `samir.hassan`.
3. Write the control intent in your notebook: "Leaver population feeds residual-access hunting once IT access is onboarded (Lesson 09) and correlation is proven (Lessons 17–19)."

**Expected result:** Written query/population attempt plus a note that IT residual proof lands after IT app onboarding — treat this as a known gap, not a bug.

### Task 6 — Apply population to a refresh

1. Clone `Refresh MNB Attributes` into a copy (e.g. `Refresh MNB Active Employees`) so the broad attribute-refresh task stays untouched.
2. Set the copy's filter/population to `MNB-Active-Employees`.
3. Keep attribute-promotion options on — same purpose as the original task; don't pile on unrelated policy checks.
4. Run once and capture the task result.

**Expected result:** Refresh succeeds scoped to the population; the result or task definition shows the population name/filter as evidence.

### Task 7 — Document membership logic

In the binder, record each population's logic, owner, and review cadence:

| Name | Filter logic | Owner | Review cadence |
| --- | --- | --- | --- |
| MNB-Active-Employees | `inactive=false` | IAM Ops (lab: you) | Quarterly |
| MNB-Contractors | `employeeType=Contractor` | IAM Ops | Monthly |
| MNB-Treasury | Treasury / Payments dept | Payments + IAM | Quarterly |

**Expected result:** An audit-ready population register page.

### Task 8 — Population vs. ad-hoc search drill

1. Run an ad-hoc Advanced Search for `departmentName` contains Payments/Treasury (or `JobCode`/`division` for Treasury) without saving it.
2. Compare the member count to `MNB-Treasury`.
3. Write why the saved population wins for certifications: it's a named, repeatable, reviewable control that tasks can reference — an ad-hoc search disappears the moment the browser tab closes.

**Expected result:** Counts match (or the difference is explained); one examiner-ready sentence in the binder, e.g. "Campaign X uses population `MNB-Treasury`, defined as Treasury/Payments department filter as of [review date]."

### Task 9 — Negative test

1. Confirm Amelia (`MNB00097`, retail teller) is **not** in `MNB-Treasury`.
2. Confirm Raj (`MNB00093`) is **not** in `MNB-Active-Employees` if you excluded contractors — or document that you included all actives.
3. Confirm Samir (`MNB00094`) is **not** in active employees.

**Expected result:** Negative membership checks written; you trust the filter logic in both directions, not just the happy path.

## Acceptance criteria

- [ ] Three populations created and previewed
- [ ] `raj.external` in contractors; TRS personas in Treasury
- [ ] Terminated search/population attempt documented, with the Lesson 09+ dependency noted
- [ ] Population-scoped refresh run with evidence
- [ ] Population register written
- [ ] Ad-hoc vs. population comparison and negative tests done
- [ ] CHANGELOG updated

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Empty population / empty search | Extra AND filters (Type=Employee, Is Manager, blank Software Version) | Clear all but the one intended criterion; re-run |
| Empty after Type = Employee | Stock `type` blank on cubes | Don't use Type; use `inactive` / custom `employeeType` |
| `employeeType` missing from filter dropdown | Not Searchable / not created | Identity Mappings → `employeeType` → Searchable ON; refresh |
| `employeeType` blank on everyone | Mapped to stock `type` or never refreshed | Custom attr + `Refresh MNB Attributes` |
| Empty population | Attribute only on Link, not Identity | Lesson 05 map + Lesson 06 attribute refresh |
| Cannot find Populations UI | Under Setup or missing from menu | **Intelligence → Advanced Analytics → Save Population** |
| Contractors include employees | Wrong attribute / typo | Verify identity `employeeType` exact value `Contractor` |

## Training binder evidence

- Screenshots: population definitions + member previews
- Screenshot: population-scoped refresh result
- Population register table
- Note linking `MNB-Treasury` to a future wire certification scope

**Ops note:** Keep the population register current when you add or retire personas — this is the artifact you'd hand a new IAM Ops teammate on day one.

## Knowledge check

1. Why do populations beat ad-hoc filters?
2. Which population should most certifications start with?
3. How do contractors differ in scope/SLA?
4. What attribute defines `MNB-Treasury`?
5. Why is "terminated with IT access" incomplete before Lesson 09?

### Answers

1. Reusable, named, reviewable controls with stable logic — auditable and consistent across tasks/certs.
2. Active employees (or a risk-tiered subset) — not all identities including leavers.
3. Shorter tenure and higher offboarding risk drive a tighter certification cadence and JML SLA.
4. `departmentName` contains Payments/Treasury (or `JobCode`/`division` for Treasury).
5. IT accounts and entitlements aren't onboarded yet; residual access needs `MNB-IT-Access` (and later correlation).

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search "population" and "identity selector" for filter syntax and task scoping.
- [SailPoint Community](https://community.sailpoint.com/) — search "certification population" for campaign-scoping patterns used in banks.
- [NIST SP 800-53 AC-6 — Least Privilege](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — scoping reviews and admin work to the right populations.
- [FFIEC IT Examination Handbook — Information Security](https://ithandbook.ffiec.gov/it-booklets/information-security.aspx) — expectations for risk-based review populations (contractors, privileged, payments).
- [CIS Controls v8 — Control 5](https://www.cisecurity.org/controls/account-management) — inventorying and grouping accounts for governance.

## Stretch lab

- Create `MNB-On-Leave` (`exceptions=LOA`) and write which control freezes access for `sofia.torres`.
- Create `MNB-Finance` (`departmentName` contains Finance) for later SoD campaigns targeting `jordan.reed`'s org.
- Export member lists (if the UI allows) into evidence for count reconciliation against the HR file.
- Create `MNB-Terminated` on inactive status and note it as a future input to Lesson 20's orphan/dormant hunting.

## Summary

- Populations are reusable scopes for refresh, certs, and reports — create them via **Setup → Populations** or **Advanced Analytics → Save Population**.
- Meridian baselines: Active Employees (`inactive=false`), Contractors (custom `employeeType`), Treasury (`departmentName` / job signals).
- Never confuse stock **Type** with HR **`employeeType`**; keep filters minimal so AND logic doesn't zero out results.
- Membership logic belongs in the training binder as control documentation.

## Feedback

Could you recreate `MNB-Active-Employees` and explain why stock **Type = Employee** empties the result — without looking? If a population returned zero people, note the **filter fields you used** and whether the attribute was Searchable on the Identity (not only on the Link).

---

**Previous:** [Lesson 06 — Identity Cubes & Refresh](06-identity-cubes-and-refresh.md)  
**Next:** [Lesson 08 — Task Operations & Scheduling Discipline](08-task-ops-and-scheduling.md)
