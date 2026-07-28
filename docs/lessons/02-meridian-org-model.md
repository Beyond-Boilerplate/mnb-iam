# Lesson 02 — Meridian Org Model & Risk Language

| Field | Value |
| --- | --- |
| **Level** | Beginner |
| **Track** | Foundations |
| **Time** | 60 minutes |
| **Prereq** | Lesson 01 |
| **Lab data** | `~/iiq-lab-data/reference/departments.csv`, `job-codes.csv`, `entitlement-dictionary.csv`, `sod-matrix.csv`; skim `HRApplications.txt`, `EmployeeData.txt` |

## Learning objectives

You will be able to:

- Explain Meridian’s department and job-code model from reference CSVs
- Map job codes to likely entitlements using the entitlement dictionary
- Classify entitlements by risk tier (medium / high / critical)
- Identify intentional SoD violators in lab data and state the business rationale
- Define birthright, requestable, privileged, and break-glass with Meridian examples

## Why this matters

IAM designs fail when they ignore org reality. Roles, SoD policies, and certification scopes must speak Meridian’s language: Retail vs Treasury vs Finance vs Technology—not generic “Department A”.

**Control / audit:** Examiners ask how dual control works for wires and why finance staff cannot also hold cloud admin. Your risk language and SoD pairs are the documented answer before any policy XML exists.

## Concepts

Authoritative HR carries structural codes that drive later IIQ rules:

| HR field | Purpose |
| --- | --- |
| `departmentName` | Org bucket (RET, TRS, FIN, …) for roles and populations |
| `jobCode` | Role of record (WIR01, GL01, TEL01, …) |
| `employeeType` | Employee vs Contractor lifecycle SLAs |
| `status` / `exceptions` (LOA) | Active, terminated, temporary freeze |

Entitlements are codes with a risk dictionary. SoD pairs encode toxic combinations.

```text
  departmentName + jobCode  -->  birthright / IT roles
  entitlement risk tier     -->  cert campaign scope
  sod-matrix pairs          -->  policy violations + remediation
```

**Critical Meridian entitlements (from dictionary):** `CORE`, `SAP_FI`, `AWS_ADMIN`, `WIRE_INIT`, `WIRE_APPR`, `ACH_OPS`, `PRIV_BREAK`.

**Intentional lab violators:**

| Persona | IDs | Toxic combo | Matrix rationale |
| --- | --- | --- | --- |
| `jordan.reed` | MNB00092 | `SAP_FI` + `AWS_ADMIN` | Finance SoR + cloud bypass |
| `kai.nguyen` | MNB00096 | `IBSI` + `ECOM` | Digital support + channel promotion |

## How it works

Meridian’s org model is not invented in IIQ—it is **imported from HR codes** and **enriched by reference dictionaries**. Roles, populations, SoD policies, and certification scopes later consume the same `departmentName`, `jobCode`, and entitlement risk tiers you learn here.

```text
departments.csv + job-codes.csv
        │
        ▼
HR row (departmentName, jobCode, employeeType)
        │
        ▼
Identity attributes after Aggregate MNB-HR / Refresh
        │
        ├── Birthright / IT roles (Lessons 23–28)
        ├── Populations (Lesson 07)
        └── SoD matrix + cert scope (Lessons 39–45)
```

| Artifact | Drives | Exam narrative |
| --- | --- | --- |
| `departmentName` | Populations, role assignment filters | “Retail vs Treasury scope” |
| `jobCode` | Birthright / IT role design | “WIR01 gets WIRE_INIT” |
| Entitlement risk tier | Cert campaign priority | “Critical first” |
| `sod-matrix.csv` | Policy objects | “Toxic pairs with rationale” |

**Real-life Meridian example.** `priya.wire` (`WIR01`, `TRS`) should receive wire-initiation birthright—not `AWS_ADMIN`. `jordan.reed` holding `SAP_FI`+`AWS_ADMIN` is an intentional SoD finding, not a modeling accident.

## Before you start

- [ ] Lesson 01 complete; IIQ login works
- [ ] Reference CSVs readable under `lab-data/reference/` or `~/iiq-lab-data/reference/`
- [ ] Notebook ready for org sketch and risk glossary

## Lab procedure

### Task 1 — Read the org dictionaries

1. Open `lab-data/reference/departments.csv`.
2. Open `lab-data/reference/job-codes.csv`.
3. Sketch Meridian leadership from HR (`MNB00001`–`MNB00008`):

| userId (HR) | userName | Dept | Owns |
| --- | --- | --- | --- |
| MNB00001 | helen.ross | SEC | IAM / cyber |
| MNB00002 | christopher.hayes | ITP | Technology |
| MNB00003 | deepa.nair | FIN | Finance |
| MNB00004 | anthony.powell | RSK | Risk |
| MNB00005 | rachel.evans | TRS | Payments / wire |
| MNB00006 | sanjay.kapoor | CML | Commercial |
| MNB00007 | emily.bennett | RET | Retail branches |
| MNB00008 | daniel.griffin | OPS | Operations / core |

> IT dumps label the same associate key `employeeId` (= HR `userId`).

**Expected result:** Sketch shows ten department codes (RET, CML, TRS, FIN, RSK, OPS, DIG, ITP, HRP, SEC) and leaders who will own apps/entitlements later.

### Task 2 — Job code to entitlement mapping

1. From `job-codes.csv`, pick five codes: `TEL01`, `WIR01`, `WIR02`, `GL01`, `CLD01`.
2. Using `entitlement-dictionary.csv` and common sense, propose likely entitlements:

| jobCode | Likely entitlements |
| --- | --- |
| TEL01 | ELDAP (+ branch apps later) |
| WIR01 | ELDAP, WIRE_INIT, maybe ACH_OPS |
| WIR02 | ELDAP, WIRE_APPR |
| GL01 | ELDAP, SAP_FI, GL_POST |
| CLD01 | ELDAP, AWS_ADMIN |

3. Confirm against `EmployeeData.txt` for `amelia.brooks`, `priya.wire`, `marcus.approve`, `jordan.reed`, `raj.external`.

**Expected result:** Table of five mappings; at least three confirmed in the IT dump.

### Task 3 — Entitlement risk walkthrough

1. Open `entitlement-dictionary.csv`.
2. List all `risk=critical` codes in your notebook.
3. Separately list `high` and note which belong in first-wave certifications.

**Expected result:** Critical list includes at least `CORE`, `SAP_FI`, `AWS_ADMIN`, `WIRE_INIT`, `WIRE_APPR`, `ACH_OPS`, `PRIV_BREAK`.

### Task 4 — Find toxic access in data

1. In `EmployeeData.txt`, filter rows for `jordan.reed` and `kai.nguyen`.
2. Match entitlements to `sod-matrix.csv` rationales.
3. Note dual-control wire pair separately: `priya.wire` holds `WIRE_INIT`; `marcus.approve` holds `WIRE_APPR`—healthy separation when not combined on one person.

**Expected result:** Written note: jordan = SAP_FI+AWS_ADMIN; kai = IBSI+ECOM; wire dual control demonstrated by two people, not one.

### Task 5 — Contractor vs employee

1. In `HRApplications.txt`, find rows with `employeeType=Contractor` (e.g. `raj.external` MNB00093, plus others).
2. Note `raj.external` email domain: `raj.contractor@vendor-mail.invalid` (bad/vendor mail—data quality lesson later).
3. Write why contractors need tighter joiner/leaver SLAs than employees.

**Expected result:** Notebook states: shorter tenure, higher residual-risk if offboarding lags; population `MNB-Contractors` will scope certs later.

### Task 6 — Meridian risk glossary

Define in your notebook (one Meridian example each):

| Term | Definition | MNB example |
| --- | --- | --- |
| Birthright | Access every active worker of a class gets | ELDAP for employees |
| Requestable | Catalog item via access request | CRM, DWRP |
| Privileged | Elevated admin / production change | AWS_ADMIN, CORE |
| Break-glass | Emergency privileged path | PRIV_BREAK |

**Expected result:** Four definitions with Meridian codes—ready for Lessons 23–28 and 37.

### Task 7 — Control-owner map (starter)

Assign owners you will reuse when apps are onboarded:

| Domain | Control owner | Identity |
| --- | --- | --- |
| IAM platform | Head of Identity & Access | helen.ross |
| Wire / payments entitlements | Payments Operations Manager | rachel.evans |
| Finance ERP | Director of Finance | deepa.nair |
| Cloud admin | Director of Technology | christopher.hayes |
| Core banking | Operations Manager | daniel.griffin |
| SoD policy design | Risk + IAM | anthony.powell + helen.ross |

**Expected result:** Owner map page in binder—prevents “orphan entitlement” ownership later.

## Acceptance criteria

- [ ] Org sketch for leaders MNB00001–08 complete
- [ ] Five job→entitlement mappings documented
- [ ] Critical entitlement list recorded
- [ ] jordan.reed and kai.nguyen SoD notes written
- [ ] Contractor SLA rationale written
- [ ] Risk glossary (4 terms) complete
- [ ] Control-owner map starter complete

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Reference CSVs missing | Lab data not copied | `cp -R lab-data/reference ~/iiq-lab-data/` |
| Cannot find jordan.reed | Searching HR only | Check `EmployeeData.txt` IT rows |
| Confused WIRE vs SoD | Dual control ≠ SoD always | SoD is toxic *combo*; dual control is split duties across people |
| Too many departments | Over-modeling | Stick to codes in `departments.csv` only |
| Invented entitlement codes | Freelancing | Update dictionary first—do not invent |

## Training binder evidence

- Org sketch (photo or digital)
- Highlighted print/screenshot of `sod-matrix.csv`
- Risk glossary page
- Note: “Control owner for wire entitlements: rachel.evans (TRS)”

**Examiner question:** “How do you decide which entitlements are critical for quarterly certification?”

## Knowledge check

1. Name two critical entitlements and why they are critical.
2. Which persona holds `WIRE_INIT` without `WIRE_APPR`?
3. Why is `SAP_FI` + `AWS_ADMIN` toxic?
4. Which department code is Treasury & Payments?
5. What makes `raj.external` a data-quality red flag?

### Answers

1. Examples: `WIRE_INIT`/`WIRE_APPR` (payment movement), `CORE` (core banking), `AWS_ADMIN` (infra escape), `SAP_FI` (finance SoR), `PRIV_BREAK` (emergency admin).
2. `priya.wire` (MNB00090).
3. Finance system of record plus cloud admin enables bypass of application controls—see sod-matrix.
4. `TRS`.
5. Non-corporate email (`@vendor-mail.invalid`) while appearing in IT access—correlation and lifecycle risk.

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “identity attributes” and “populations” to see how HR codes become selectable filters.
- [SailPoint Community](https://community.sailpoint.com/) — search “birthright roles” and “job code based access” for bank-style role design patterns.
- [NIST SP 800-53 AC-2 / AC-5](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — account management and separation of duties language behind Meridian’s risk glossary.
- [FFIEC IT Examination Handbook — Information Security](https://ithandbook.ffiec.gov/it-booklets/information-security.aspx) — examiner expectations for dual control and privileged access classification.
- [ISACA — Segregation of Duties primers](https://www.isaca.org/) — search “segregation of duties” for SOX/ITGC vocabulary Risk uses with IAM.

## Stretch lab

- Propose a third SoD pair Meridian should add (not already in the matrix) and write a one-paragraph rationale for Risk.
- Map every `risk=high` entitlement to a likely business owner (dept leader).
- Draft a one-slide “Meridian risk language” for new IAM engineers.

## Summary

- Meridian IAM is driven by department/job codes and entitlement risk tiers.
- Lab data embeds intentional SoD violators and healthy wire dual control.
- Shared risk language (birthright / requestable / privileged / break-glass) will drive later roles and policies.

---

**Previous:** [Lesson 01 — Bank Briefing & UI Orientation](01-bank-briefing-and-ui.md)  
**Next:** [Lesson 03 — Lab Hygiene, Naming & Evidence Habits](03-lab-hygiene-and-naming.md)
