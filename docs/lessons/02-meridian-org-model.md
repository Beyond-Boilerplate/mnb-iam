# Lesson 02 — Meridian Org Model & Risk Language

| Field | Value |
| --- | --- |
| **Level** | Beginner |
| **Track** | Foundations |
| **Time** | 75–90 minutes |
| **Prereq** | Lesson 01 |
| **Lab data** | `~/iiq-lab-data/reference/departments.csv`, `job-codes.csv`, `entitlement-dictionary.csv`, `sod-matrix.csv`; skim `HRApplications.txt`, `EmployeeData.txt` |

This lesson is **file-reading heavy** — you will spend most of today in CSVs and text files, not IIQ. There is almost no IIQ configuration here; you are building the vocabulary that Lessons 04–45 assume you already have.

## Learning objectives

You will be able to:

- Explain Meridian's department and job-code model from the reference CSVs
- Define **population**, **birthright**, **requestable**, **privileged**, **break-glass**, and **SoD** with Meridian examples
- Map job codes to likely entitlements using the entitlement dictionary
- Classify entitlements by risk tier (medium / high / critical) and say why the tier matters
- Spot intentional SoD violators in lab data and explain the business rationale
- Name control owners for wire, finance, cloud, core, and IAM

## Why this matters

Your pairing manager sits you down with the org CSVs before any role XML. The conversation sounds like: "Roles and policies that ignore Retail vs Treasury vs Finance will fail the first review question. We speak Meridian's language: department codes, job codes, entitlement risk, and toxic pairs. If you cannot explain why Priya may initiate a wire but must not also approve it, you are not ready to click Save on a policy." This lesson is that conversation on paper, plus the homework of walking the files yourself.

Reviewers ask how dual control works for wires and why finance staff cannot also hold cloud admin. Your risk language and SoD pairs are the documented answer **before** any policy object exists in IIQ.

## Concepts

### 1. Org reality comes from HR codes, not IIQ imagination

Meridian does not invent departments inside SailPoint. HR already stores structural fields; IIQ later **imports** them onto identity cubes and uses them as filters for roles, populations, and certifications. Use the CSV casing exactly: `JobCode` and `departmentName`.

| HR field (in `HRApplications.txt`) | What it means | Example |
| --- | --- | --- |
| `departmentName` | Org bucket the person sits in | `TRS` = Treasury & Payments |
| `JobCode` | Role of record / job family | `WIR01` = Wire Specialist |
| `employeeType` | Employment class | `Employee` vs `Contractor` |
| `status` / `inactive` | Whether they are active | Terminated people still appear until cleaned |
| `exceptions` | Temporary states | `LOA` = leave of absence (`sofia.torres`) |
| `managersAssociateID` | Manager's HR key | Builds manager hierarchy later |

```text
departments.csv + job-codes.csv  (reference dictionaries)
        │
        ▼
HR row (departmentName, JobCode, employeeType, …)  ──►  Identity attributes (Lesson 04–06)
        │
        ├── Populations (saved filters)       Lesson 07
        ├── Birthright / IT roles              Lessons 23–28
        └── SoD + certification scope          Lessons 39–45
```

**Worked example.** Priya (`priya.wire`, MNB00090) is `TRS` + `WIR01`. That combination should eventually drive wire-initiation access — not `AWS_ADMIN`. Jordan (`jordan.reed`) holding finance ERP admin **and** cloud admin is a finding you hunt on purpose in the lab, not a modeling accident.

> **Watch out:** Building a role named "Treasury People" with no link to `departmentName=TRS` or `JobCode=WIR01` looks fine in the demo. Six months later nobody knows who should get it. Always trace access decisions back to HR codes Risk and HR already understand.

### 2. Populations — "saved searches" of people

A **population** is a reusable filter over identities — a named query your team trusts, not a one-off Advanced Search you forget. Risk asks "certify all contractors this month"; you do not hand-pick names, you point the campaign at a population like `MNB-Contractors` (built in Lesson 07). Populations are not roles: a population **selects people**, a role **packages access**. You often combine them — "assign birthright role X to everyone in population Y."

| Population (concept) | Filter idea | Why it exists |
| --- | --- | --- |
| Active employees | `employeeType=Employee`, not terminated | Birthright and most certs |
| Contractors | `employeeType=Contractor` | Shorter SLA, tighter offboarding |
| Treasury | `departmentName=TRS` | Wire-related campaigns |
| Finance | `departmentName=FIN` | SAP / GL reviews |

### 3. Access classes — birthright, requestable, privileged, break-glass

| Class | Definition | Meridian example |
| --- | --- | --- |
| **Birthright** | Access every active worker of a class gets automatically — no ticket, no manager hunt | `ELDAP` for active employees; teller starter pack for `JobCode=TEL01` |
| **Requestable** | Access asked for through a catalog, usually with approval | `CRM` (relationship managers), `DWRP` dev workstation/repo access |
| **Privileged** | Elevated rights that can change production systems, move money, or bypass app controls | `AWS_ADMIN`, `CORE`, `SAP_FI`, `WIRE_INIT`/`WIRE_APPR`, `ACH_OPS` |
| **Break-glass** | Time-bound emergency elevation, checked out under an incident, reviewed after the fact | `PRIV_BREAK` |

Birthright is **not** "everything someone might eventually need" — cloud admin is never birthright for a teller. If everyone got `CRM` automatically, certifications would drown in noise, which is why requestable access stays catalog-driven.

> **Watch out:** Quietly leaving `AWS_ADMIN` on a developer "just in case" is standing privilege, not break-glass. Day-to-day access stays least-privilege; the emergency path is separate, logged, and certified.

### 4. Entitlement risk tiers

Open `entitlement-dictionary.csv` — each code carries a **risk** column: `medium`, `high`, or `critical`.

| Tier | Meaning in practice | What you do differently |
| --- | --- | --- |
| **medium** | Useful access; abuse is limited or detectable | Standard manager cert cadence |
| **high** | Sensitive ops or customer/channel impact | Earlier cert waves; stronger owners |
| **critical** | Money movement, core/ERP admin, cloud admin, emergency admin | First-wave certs; SoD pairs; dual control |

| Code | Risk | Plain-language "so what?" |
| --- | --- | --- |
| `ELDAP` | medium | Needed widely; still review leavers |
| `IBSI` | high | Digital banking support console |
| `ECOM` | high | Can promote channel changes |
| `WIRE_INIT` | critical | Can create wire instructions |
| `WIRE_APPR` | critical | Can approve wires |
| `PRIV_BREAK` | critical | Emergency admin — always explainable |

Risk tiers drive **certification priority** later: critical first when time is short. They do not replace SoD — something can be medium risk alone but toxic **in combination**.

### 5. Segregation of duties (SoD) — toxic combinations

**SoD** means one person should not hold two (or more) entitlements that together let them commit and hide a bad act, or bypass a control meant to require two people. Classic example: Person A creates a wire (`WIRE_INIT`); Person B approves it (`WIRE_APPR`). If **one** person holds both, dual control is gone — fraud or error can clear with a single actor.

```text
WIRE_INIT + WIRE_APPR  →  Payment dual control broken
```

SoD is about the **combination**. Holding `WIRE_INIT` alone is expected for Priya; holding `WIRE_APPR` alone is expected for Marcus. Holding **both** on one person is the violation.

| Entitlement A | Entitlement B | Why toxic |
| --- | --- | --- |
| `WIRE_INIT` | `WIRE_APPR` | Same person initiates and approves payments |
| `SAP_FI` | `AWS_ADMIN` | Finance system-of-record rights + cloud bypass of app controls |
| `IBSI` | `ECOM` | Support console + ability to promote channel changes |
| `GL_POST` | `SOX_VIEW` | Post journals and attest your own controls |
| `CORE` | `AWS_ADMIN` | Core ops + infrastructure escape |
| `ACH_OPS` | `WIRE_INIT` | Too much payment-initiation concentration across rails |

**Intentional lab violators** (seeded so you have something to find later):

| Persona | Toxic combo | Story |
| --- | --- | --- |
| `jordan.reed` (MNB00092) | `SAP_FI` + `AWS_ADMIN` | Finance access plus cloud admin |
| `kai.nguyen` (MNB00096) | `IBSI` + `ECOM` | Digital support plus channel promotion |

**Healthy dual control (not a violation):** `priya.wire` holds `WIRE_INIT` only; `marcus.approve` holds `WIRE_APPR` only.

> **Say this out loud once:** dual control is the **business design** ("two people required"). SoD **policy** is how IAM detects when one identity breaks that design. Dual control can also exist outside IIQ (maker-checker in the wire app itself); IIQ still watches the entitlement combo.

### 6. Contractors vs employees

Contractors (`employeeType=Contractor`) often have shorter tenure and higher residual risk if offboarding lags. `raj.external` (MNB00093) uses vendor email `raj.contractor@vendor-mail.invalid` — a data-quality red flag that will bite correlation and lifecycle later. Rule of thumb: tighter joiner/leaver SLAs for contractors, a separate population for certs, never assume birthright equals employee birthright. You are not configuring those SLAs today — you are learning why the HR field exists.

## Before you start

- [ ] Lesson 01 complete; IIQ login works
- [ ] You can explain identity / account / entitlement without notes
- [ ] Reference CSVs readable under `lab-data/reference/` or `~/iiq-lab-data/reference/`
- [ ] Notebook ready for org sketch, glossary, and SoD notes

## Lab procedure

### Task 1 — Read the org dictionaries first

Your staff engineer opens `departments.csv` and `job-codes.csv` before touching IIQ. Do the same.

1. Open `lab-data/reference/departments.csv`. Confirm ten department codes: `RET`, `CML`, `TRS`, `FIN`, `RSK`, `OPS`, `DIG`, `ITP`, `HRP`, `SEC`.
2. Open `lab-data/reference/job-codes.csv`. Find `TEL01`, `WIR01`, `WIR02`, `GL01`, `CLD01`, `IAM01`.
3. Sketch Meridian leadership from HR (`MNB00001`–`MNB00008`):

| userId | userName | Dept | Owns |
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

**Expected result:** Sketch shows ten department codes and leaders who will own apps/entitlements later; you can say out loud what `TRS` and `WIR01` mean.

### Task 2 — Job code to entitlement mapping (with reasoning)

Do not memorize a magic table — reason from job title to dictionary.

1. Pick five codes: `TEL01`, `WIR01`, `WIR02`, `GL01`, `CLD01`.
2. Using `entitlement-dictionary.csv`, propose likely entitlements and write **one sentence why**:

| JobCode | Likely entitlements | Why (your words) |
| --- | --- | --- |
| TEL01 | ELDAP (+ branch apps later) | Teller needs login, not cloud admin |
| WIR01 | ELDAP, WIRE_INIT, maybe ACH_OPS | Wire specialist initiates; should not also approve |
| WIR02 | ELDAP, WIRE_APPR | Approver path — separate person from WIR01 |
| GL01 | ELDAP, SAP_FI, GL_POST | Accountant on finance system of record / journals |
| CLD01 | ELDAP, AWS_ADMIN | Cloud engineer — privileged, not birthright for Retail |

3. Confirm against `EmployeeData.txt` for `amelia.brooks`, `priya.wire`, `marcus.approve`, `jordan.reed`, `raj.external`.

**Expected result:** Table of five mappings with "why" sentences; at least three confirmed in the IT dump.

### Task 3 — Entitlement risk walkthrough

1. Open `entitlement-dictionary.csv` and list all `risk=critical` codes.
2. Separately list `high` codes and note which you would put in a first-wave certification if time were limited.
3. Pick one critical code and write two sentences: what abuse looks like, and who the control owner should be (use Task 7's map).

**Expected result:** Critical list includes at least `CORE`, `SAP_FI`, `AWS_ADMIN`, `WIRE_INIT`, `WIRE_APPR`, `ACH_OPS`, `PRIV_BREAK`; one abuse/owner note written.

### Task 4 — Find toxic access in data (SoD practice)

Treat this like a tabletop exercise with Risk.

1. In `EmployeeData.txt`, filter rows for `jordan.reed` and `kai.nguyen`.
2. Match their entitlements to `sod-matrix.csv` rationales; copy the rationale into your notebook in your own words.
3. Note the healthy wire pair separately: `priya.wire` holds `WIRE_INIT`; `marcus.approve` holds `WIRE_APPR`.
4. Answer in one sentence each: is Priya an SoD violator? Is Jordan?

**Expected result:** Notes state jordan = `SAP_FI`+`AWS_ADMIN`; kai = `IBSI`+`ECOM`; wire dual control demonstrated by two people; Priya alone is **not** a violation.

### Task 5 — Contractor vs employee

1. In `HRApplications.txt`, find rows with `employeeType=Contractor` (e.g. `raj.external` MNB00093, plus others).
2. Note the email domain: `raj.contractor@vendor-mail.invalid`.
3. Write three bullets: why contractors need tighter offboarding, why a separate population helps certifications, why vendor email is a data-quality red flag for correlation later.

**Expected result:** Notebook states residual-risk + future population `MNB-Contractors` + email quality issue, without claiming you already built the population in IIQ.

### Task 6 — Meridian risk glossary

For each term, write: (a) plain definition, (b) Meridian example, (c) one "not an example."

| Term | Definition | MNB example | Not an example |
| --- | --- | --- | --- |
| Population | Saved filter of identities | "All `TRS` workers" | A role that grants `WIRE_INIT` |
| Birthright | Automatic access for a class | `ELDAP` for active employees | Standing `AWS_ADMIN` for all of IT |
| Requestable | Catalog access with approval | `CRM` via access request | Emergency `PRIV_BREAK` with no ticket |
| Privileged | Elevated / production-impacting | `CORE`, `SAP_FI`, `AWS_ADMIN` | Read-only intranet bookmark |
| Break-glass | Time-bound emergency elevation | `PRIV_BREAK` under incident | Quiet permanent admin "for weekends" |
| SoD | Policy against toxic entitlement combos | `WIRE_INIT`+`WIRE_APPR` on one person | Priya holding only `WIRE_INIT` |

**Expected result:** Six rows complete, ready for Lessons 07, 23–28, 37, and 39 without re-learning vocabulary under pressure.

### Task 7 — Control-owner map (starter)

Assign owners you will reuse when apps are onboarded. If ownership is unclear in production, that is a finding — IIQ cannot invent it.

| Domain | Control owner | Identity |
| --- | --- | --- |
| IAM platform | Head of Identity & Access | helen.ross |
| Wire / payments entitlements | Payments Operations Manager | rachel.evans |
| Finance ERP | Director of Finance | deepa.nair |
| Cloud admin | Director of Technology | christopher.hayes |
| Core banking | Operations Manager | daniel.griffin |
| SoD policy design | Risk + IAM | anthony.powell + helen.ross |

**Expected result:** Owner map page in binder — prevents "orphan entitlement" ownership later.

## Acceptance criteria

- [ ] Org sketch for leaders MNB00001–08 complete
- [ ] Can explain population vs role in one sentence each
- [ ] Five job-to-entitlement mappings documented with why
- [ ] Critical entitlement list recorded
- [ ] `jordan.reed` and `kai.nguyen` SoD notes written; Priya/Marcus dual control noted
- [ ] Contractor rationale written (SLA + population + email quality)
- [ ] Risk glossary (6 terms) complete with "not an example"
- [ ] Control-owner map starter complete

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Reference CSVs missing | Lab data not copied | `cp -R lab-data/reference ~/iiq-lab-data/` |
| Cannot find jordan.reed | Searching HR only | Check `EmployeeData.txt` IT rows |
| Confused WIRE vs SoD | Dual control ≠ "any SoD" | Dual control is the business split; SoD policy detects a toxic *combo* on one identity |
| Thinks Priya is a violator | Mixing "critical" with "toxic combo" | Critical alone is fine; the combo with approve is the violation |
| Invented entitlement codes | Freelancing | Update the dictionary first — never invent |

## Training binder evidence

- Org sketch, highlighted `sod-matrix.csv`, and the six-term risk glossary page
- Note: "Control owner for wire entitlements: rachel.evans (TRS); Priya/Marcus = healthy dual control; Jordan/Kai = intentional SoD seed data"

## Knowledge check

1. Name two critical entitlements and why they are critical.
2. Which persona holds `WIRE_INIT` without `WIRE_APPR`? Is that an SoD violation?
3. Why is `SAP_FI` + `AWS_ADMIN` toxic?
4. Which department code is Treasury & Payments?
5. What makes `raj.external` a data-quality red flag?
6. In one sentence each: what is a **population**, and what is **birthright**?

### Answers

1. Examples: `WIRE_INIT`/`WIRE_APPR` (payment movement), `CORE` (core banking), `AWS_ADMIN` (infra escape), `SAP_FI` (finance system of record), `PRIV_BREAK` (emergency admin).
2. `priya.wire` (MNB00090). Not a violation — a violation requires the toxic **pair** on one person.
3. Finance system-of-record rights plus cloud admin enables bypass of application controls.
4. `TRS`.
5. Non-corporate email (`@vendor-mail.invalid`) while appearing in IT access — a correlation and lifecycle risk.
6. Population = a saved filter of identities. Birthright = automatic access every member of a defined class receives.

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search "identity attributes" and "populations" to see how HR codes become selectable filters.
- [NIST SP 800-53 AC-2 / AC-5](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — account management and separation-of-duties language behind Meridian's risk glossary.

## Stretch lab

- Propose a third SoD pair Meridian should add and write a one-paragraph rationale, as if Anthony Powell asked you in standup.
- Map every `risk=high` entitlement to a likely business owner (dept leader).

## Summary

- Meridian IAM is driven by department/job codes and entitlement risk tiers — not by inventing org charts in IIQ.
- You can explain populations, birthright, requestable, privileged, break-glass, and SoD with Meridian examples and counterexamples.
- Lab data embeds intentional SoD violators and healthy wire dual control; control owners are named before apps are onboarded.

## Feedback

Could you re-derive the six risk-glossary terms from memory, with a Meridian example for each? If a task tripped you up, note the task number and whether the confusion was the CSV data itself or the vocabulary — that distinction tells us whether to fix the lab data or the explanation.

## Navigate

- Previous: [Lesson 01 — Bank Briefing & UI Orientation](01-bank-briefing-and-ui.md)
- Next: [Lesson 03 — Lab Hygiene, Naming & Evidence Habits](03-lab-hygiene-and-naming.md)
