# Lesson 04 — Authoritative HR Source

| Field | Value |
| --- | --- |
| **Level** | Beginner |
| **Track** | Foundations |
| **Time** | 75–90 minutes |
| **Prereq** | Lesson 03 (lab data copied; absolute paths known) |
| **Lab data** | `~/iiq-lab-data/HRApplications.txt` |

## Learning objectives

You will be able to:

- Inspect the Meridian HR header and explain each column’s governance role
- Create Delimited File application `MNB-HR` with an absolute file path
- Set account identity attribute to `employeeId` and enable identity creation
- Create and run Account Aggregation task `Aggregate MNB-HR`
- Verify known identity cubes for leadership and scripted personas

## Why this matters

If HR is wrong, every downstream control is wrong. Authoritative aggregation is the root of joiner/mover/leaver truth at Meridian: when a Charlotte teller is hired or a New York wire specialist joins, HR gets the record first.

**Control / audit:** Examiners ask “what is the authoritative source of workforce identity?” Your answer is `MNB-HR` backed by HRIS extract—not AD and not the IT entitlement dump. Task results prove nightly (or on-demand) aggregation succeeded.

## Concepts

An **authoritative** application is allowed to create and update IdentityIQ identities from its accounts. Non-authoritative apps (Lesson 09+) only attach accounts/entitlements to existing people.

| Column | Role |
| --- | --- |
| `employeeId` | Stable account/identity key (`MNB#####`) |
| `userName` | Login-style name (`helen.ross`) |
| `email` | Corporate mail (`@meridiannb.com`) |
| `managerId` | Manager’s `employeeId` (hierarchy) |
| `status` | `1` active, `0` terminated |
| `departmentCode` / `jobCode` | Org model for roles |
| `workerType` | Employee / Contractor |
| `onLeave` | Temporary freeze flag (`true`/`false`) |
| `hireDate` / `terminationDate` | Lifecycle evidence |

```text
  HRApplications.txt
        |
        v
  [MNB-HR DelimitedFile] --authoritative--> create/update Identity
        |
        v
  Aggregate MNB-HR (Account Aggregation task)
        |
        v
  Identity cubes (helen.ross, priya.wire, samir.hassan, ...)
```

**Why `employeeId` over email as account id:** Emails change, contractors use vendor domains (`raj.external`), and rehires need a stable key. Meridian employee IDs are durable.

## How it works

An **authoritative** Delimited File application maps each HR row to an account whose **native identity** is `employeeId`. With create-identities enabled, Account Aggregation upserts Identity cubes; non-authoritative apps later only attach Links.

```text
HRApplications.txt (row per worker)
        │
        ▼
MNB-HR schema (native identity = employeeId)
        │
        ▼
Account Aggregation task: Aggregate MNB-HR
        │
        ├── create Identity if missing
        ├── update attributes if present
        └── Link account on cube
```

| Setting | Meridian value | Why |
| --- | --- | --- |
| Connector | Delimited File | Lab stand-in for HRIS feed |
| Native identity | `employeeId` | Stable across email/vendor domains |
| Create identities | ON (HR only) | Workforce source of truth |
| Task name | `Aggregate MNB-HR` | Auditable control activity |

> **Production reality:** Banks usually feed HR from Workday, SAP SuccessFactors, or similar via the native connector or a governed flat-file drop—not a hand-edited CSV. Lesson 04 teaches the authoritative pattern; Part II connector lessons cover live HRIS paths.

**Real-life Meridian example.** `amelia.brooks` appears in HR on hire day; after `Aggregate MNB-HR`, her cube exists so birthright and joiner workflows have a person to attach—not an orphan IT account.

## Before you start

- [ ] `realpath ~/iiq-lab-data/HRApplications.txt` works
- [ ] Logged in as `spadmin`
- [ ] Evidence folder for today exists (`~/iiq-lab-evidence/YYYY-MM-DD/`)
- [ ] Naming card from Lesson 03 available

## Lab procedure

### Task 1 — Inspect the HR header

1. Open the file:

```bash
head -3 ~/iiq-lab-data/HRApplications.txt
wc -l ~/iiq-lab-data/HRApplications.txt
```

2. Confirm header includes: `employeeId,userName,firstName,lastName,email,managerId,status,departmentCode,jobCode,jobTitle,locationCode,country,workerType,onLeave,costCenter,hireDate,terminationDate`.
3. Find a leaver: `status=0` (e.g. `samir.hassan` MNB00094) and an on-leave worker: `onLeave=true` (e.g. `sofia.torres` MNB00095).

**Expected result:** Notebook lists column meanings; you can cite one terminated and one on-leave persona.

### Task 2 — Create application MNB-HR

1. In IIQ: **Applications** → **Add New Application** (or equivalent).
2. Application type: **DelimitedFile** (Delimited File connector).
3. Name: `MNB-HR`. Owner: `spadmin` (lab).
4. File settings:
   - File path: absolute path to `HRApplications.txt` (expanded `/Users/...`, not `~`)
   - Delimiter: comma
   - Has header row: yes
5. Save.

**Expected result:** Application `MNB-HR` appears in the application list.

**If it fails:** Check connector type spelling; confirm file path is readable by Tomcat OS user.

### Task 3 — Schema discovery and identity attribute

1. Open `MNB-HR` → Schema (or Configuration → Schema).
2. Discover/preview attributes from the file header (or define manually to match columns).
3. Set **account identity attribute** (native identity) to `employeeId`.
4. Ensure key fields exist on the schema: `userName`, `email`, `firstName`, `lastName`, `managerId`, `status`, `departmentCode`, `jobCode`, `workerType`, `onLeave`.
5. Save.

**Expected result:** Schema lists HR columns; account id is `employeeId`.

### Task 4 — Authoritative / create identities

1. On `MNB-HR`, locate settings for creating identities from accounts (Authoritative application / Create identities—or equivalent wording for your IIQ version).
2. Enable identity creation from this application.
3. Save. Log in CHANGELOG: “MNB-HR authoritative=true”.

**Expected result:** Notebook documents that **only** `MNB-HR` creates identities in the Meridian lab (IT apps must remain non-authoritative).

### Task 5 — Create and run Aggregate MNB-HR

1. **Tasks** → New Task → type **Account Aggregation** (or equivalent).
2. Name: `Aggregate MNB-HR`.
3. Select application `MNB-HR`.
4. Save, then **Run Now**.
5. Open the **Task Result**. Note start time, duration, accounts scanned/created/updated, errors.

**Expected result:** Task result Success (or Success with warnings you understand). Account count > 0 (lab HR is ~70–80 workers including header). Screenshot saved to evidence folder.

**If it fails:** Zero accounts → path, permissions, delimiter, or header parse. Check Tomcat logs; re-test file with `head`.

### Task 6 — Verify personas

1. **Identities** → search `helen.ross` (MNB00001). Open cube; confirm HR account from `MNB-HR`.
2. Search `priya.wire` (MNB00090)—active wire specialist, manager should resolve toward `rachel.evans` / MNB00005 after refresh (Lesson 06 may complete manager link).
3. Search `samir.hassan` (MNB00094)—terminated (`status=0`); note how inactive appears today.
4. Spot-check `amelia.brooks` (new teller) and `raj.external` (contractor, vendor email).

**Expected result:** At least four cubes found with `MNB-HR` accounts. Terminated vs active difference visible on status/inactive attributes (exact UI label varies).

### Task 7 — Binder note — control statement

Write: “Meridian’s authoritative workforce source is application `MNB-HR`. Aggregation task `Aggregate MNB-HR` is the control activity that materializes identities. Control owner (lab): IAM trainee / (prod) HRIS+IAM Ops.”

**Expected result:** One control statement ready for training binder.

## Acceptance criteria

- [ ] `MNB-HR` Delimited File app created with absolute path
- [ ] Account identity attribute = `employeeId`
- [ ] Identity creation enabled (authoritative)
- [ ] `Aggregate MNB-HR` ran with non-zero accounts
- [ ] Cubes verified for helen.ross, priya.wire, samir.hassan
- [ ] Evidence screenshot of task result filed
- [ ] CHANGELOG updated

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| 0 accounts aggregated | Bad path / perms / delimiter | Fix absolute path; confirm comma + header |
| Duplicate identities | Wrong account id (email) | Rebuild schema with `employeeId` |
| Missing columns | Schema not rediscovered after file change | Rediscover schema; re-aggregate |
| Tomcat cannot read file | macOS privacy / ownership | Adjust ACL; move under readable home path |
| Identities not searchable | Aggregation failed silently | Read full task result errors + syslog |

## Training binder evidence

- Screenshot: `MNB-HR` application configuration (path visible, secrets none)
- Screenshot: successful `Aggregate MNB-HR` task result with counters
- Screenshot: `helen.ross` cube Accounts tab showing `MNB-HR`
- CHANGELOG lines for app + task creation

**Examiner question:** “Prove which system creates workforce identities and show the last successful aggregation.”

## Knowledge check

1. What makes an application authoritative?
2. Why prefer `employeeId` over email as account identity?
3. Where do you look first when aggregation returns zero accounts?
4. Which persona demonstrates a terminated worker in HR?
5. What is the exact task name for HR aggregation in this curriculum?

### Answers

1. It is configured to create/update IdentityIQ identities from its accounts—HR is the workforce source of truth.
2. Emails change and vendors use non-corporate domains; employee IDs are stable.
3. File path, OS permissions, delimiter/header parse—before blaming IIQ logic.
4. `samir.hassan` (MNB00094), `status=0` with terminationDate set.
5. `Aggregate MNB-HR`.

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “authoritative application” and “Delimited File” for create-identities and schema identity attribute settings.
- [SailPoint Community](https://community.sailpoint.com/) — search “HR authoritative source” for patterns that keep AD/IT apps non-authoritative.
- [NIST SP 800-53 AC-2 — Account Management](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — workforce account lifecycle expectations tied to an authoritative source.
- [NIST SP 800-63A — Enrollment and Identity Proofing](https://pages.nist.gov/800-63-3/sp800-63a.html) — why stable identifiers matter when binding a person to accounts.
- [FFIEC IT Examination Handbook — Information Security](https://ithandbook.ffiec.gov/it-booklets/information-security.aspx) — examiner questions on authoritative identity sources and joiner/leaver evidence.

## Stretch lab

- Append `~/iiq-lab-data/scenarios/joiner/hr-delta-new-hire.csv` content into a copy of the HR file (keep a backup), re-run `Aggregate MNB-HR`, and find `nina.joiner`.
- Compare account counts in task results before vs after the joiner append.
- Document rollback: restore original `HRApplications.txt` from `lab-data/`.

## Summary

- `MNB-HR` is Meridian’s authoritative Delimited File application keyed on `employeeId`.
- `Aggregate MNB-HR` materializes identity cubes from `HRApplications.txt`.
- Persona verification proves active, contractor, and terminated patterns exist in the lab.

---

**Previous:** [Lesson 03 — Lab Hygiene, Naming & Evidence Habits](03-lab-hygiene-and-naming.md)  
**Next:** [Lesson 05 — HR Schema & Identity Attribute Design](05-hr-schema-and-identity-attrs.md)
