# Lesson 228 — Targeted / Focused Campaign

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~65 minutes  
**Prereq:** Lessons 220, 226–227  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 45

> **Why:** Targeted certs shrink blast radius — a full sweep is slow and noisy when you only need to prove one population or one high-risk app before calling remediation done.

## What this is

Lessons 226–227 generate **broad** certifications: everything a manager’s reports hold, or every account on an app.

A **Targeted Certification** (focused campaign) scopes deliberately:

| Scope type | Example | Who certifies? |
| --- | --- | --- |
| **Population / Identity filter** | `employeeType == "Contractor"` | A **named** identity you pick |
| **Application** | `MNB-WirePortal` only | Named identity **or** app owner |

Same decide → provision → sign-off mechanics — fewer rows, faster completion, clearer story for auditors (“we reviewed all contractors this month”).

You will run one contractor-population cert and one Wire-only cert, then write a **row-count / time comparison** against Lesson 226’s broad manager cert. “Targeted” on the label is not proof — the numbers are.

## Know these

```text
Broad (226): Helen's whole org — many apps, many entitlements
Targeted A:  employeeType=Contractor only → Helen certifies that population
Targeted B:  MNB-WirePortal accounts only → Marcus certifies Wire slice

Proof scoping helped:
  targeted_rows / minutes  vs  lesson_226_rows / minutes
```

| Term | Plain English |
| --- | --- |
| **Targeted / focused campaign** | Cert limited by filter or single app |
| **Population filter** | Who is in scope (contractors, dept, …) |
| **Named certifier** | Explicit person — not auto manager/owner resolution |
| **Blast radius** | How many decisions one campaign forces |

- **Wrong way:** Assuming “targeted” automatically means faster — verify row count actually shrank vs Lesson 226.
- **Wrong way:** Filter that returns 0 because `employeeType` never promoted — empty cert teaches nothing.
- **Wrong way:** Leaving certifier as spadmin default — pick Specific Identity.

## Intent

- Build a Targeted Certification scoped to contractors (Lesson 220 personas).
- Build a second scoped to a single application (Wire / CRM).
- Complete both; record row counts and elapsed time vs Lesson 226.
- Leave evidence an auditor could use to argue for narrower, more frequent campaigns.

## Before you start

- [ ] Lesson 220 contractors exist: `rachel.khatri`, `james.nguyen` with `employeeType=Contractor`
- [ ] Lesson 226 manager cert row count / rough time noted (even approximate)
- [ ] `helen.ross` and `marcus.approve` can log in (`LabUser1!`)
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/228
```

## Do this

### Task 1 — Targeted cert: contractors population

1. **Certifications → Schedule / Generate → Targeted Certification**  
2. Certification Type: **Identity** (population)  
3. Population / filter matching contractors, e.g. `employeeType == "Contractor"` (use the filter UI your build offers — MatchExpression / advanced search)  
4. Certifier: **Specific Identity** → `helen.ross`  
5. Name: `MNB-Targeted-Contractors-<today>`  
6. **Generate Now**  

- **Expect:** Generation succeeds; row count visible on confirmation / cert summary.

Write down the row count immediately.

> **Tip:** If filter returns 0, open Rachel’s cube and confirm `employeeType=Contractor` was promoted — Refresh Identity Cubes if needed (Lesson 220).

### Task 2 — Note population row count

Under evidence:

```text
Targeted contractors rows: ____
```

- **Expect:** a number you can compare to Lesson 226.

### Task 3 — Complete as Helen; time it

1. Log in as `helen.ross`  
2. Open **My Certifications** → contractor targeted cert  
3. Decide every row (Approve or Revoke as appropriate)  
4. **Complete Certification**  
5. Note elapsed wall-clock minutes  

- **Expect:** targeted feels faster — less per-identity noise than a full org sweep.

```text
Targeted contractors time: ____ minutes
```

### Task 4 — Targeted cert: single application

1. Generate another **Targeted Certification**  
2. Type: **Application**  
3. Scope: `MNB-WirePortal` only (or `MNB-Salesforce-CRM-Live`)  
4. Certifier: **Specific Identity** → `marcus.approve`  
5. Name: `MNB-Targeted-Wire-<today>`  
6. **Generate Now**  

- **Expect:** row set is only that app’s accounts — excludes other apps Marcus might own.

```text
Targeted Wire/app rows: ____
```

### Task 5 — Complete as Marcus

Log in as `marcus.approve`, decide, **Complete Certification**, note time.

```text
Targeted Wire/app time: ____ minutes
```

- **Expect:** smaller than a full app-owner sweep covering every account on every app he owns (Lesson 227 baseline if you have it).

### Task 6 — Write the comparison (the real deliverable)

One line under evidence — fill with your numbers:

```text
Targeted contractors: <N> rows in <M> min
Targeted Wire: <N2> rows in <M2> min
Lesson 226 broad manager: <N3> rows in <M3> min

Conclusion: narrower scope cut decisions from <N3> to <N>/<N2>,
supporting monthly high-risk reviews vs one annual mega-cert.
```

- **Why:** this is the number you’d bring to a bank auditor arguing for focused campaigns.
- **Expect:** concrete comparison recorded — not “it felt faster.”

### Task 7 — Save cert summaries

Save both cert summaries (screenshots or exports) + the comparison note under `~/iiq-lab-evidence/sandbox/228/`.

## If it fails

| Symptom | Fix |
| --- | --- |
| Population filter returns 0 | Confirm `employeeType=Contractor` on cubes; Refresh; re-check Lesson 220 |
| Still shows all apps for “app” targeted | Application filter not applied — only labeled targeted |
| Certifier greyed out / defaults to spadmin | Pick **Specific Identity**, don’t leave default resolution |
| No Lesson 226 baseline | Use best-memory estimate and mark it approximate — still write the comparison |

## You are done when

- [ ] Contractor-focused campaign completed  
- [ ] App-focused campaign completed  
- [ ] Written row-count / time comparison vs Lesson 226  

## Control note

- **Control:** Scoped / targeted certification design  
- **Owner:** IAM Ops (campaign design) + compliance (population selection)  
- **SLA (lab):** Same session; production targeted campaigns often run monthly for high-risk populations vs annual broad sweeps  
- **Evidence:** `~/iiq-lab-evidence/sandbox/228/` — both cert summaries, row-count/time comparison  

## Quick check

1. What two scope types does Targeted Certification support here? → Population/Identity filter, or single Application  
2. Who becomes certifier when scope isn’t manager/owner auto-resolve? → A named identity you pick  
3. What’s the actual proof scoping helped? → Written row-count/time comparison, not a feeling  
4. Why review contractors as a population? → Different risk / birthright profile than employees (Lesson 220)  

## Feedback

Could you argue for monthly targeted certs vs one annual mega-cert using *your* row counts? If the contractor filter was empty, note whether `employeeType` was on the cube — filter syntax is useless without promoted attributes.

## Navigate

- Previous: [Lesson 227](227-app-owner-cert-live.md)
- Next: [Lesson 229](229-cert-remediation-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
