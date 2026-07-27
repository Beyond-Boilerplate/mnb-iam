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

- Inspect the production-style Meridian HR header and map columns to governance roles ([`hr-column-map.md`](../../lab-data/reference/hr-column-map.md))
- Create Delimited File (CSV) application `MNB-HR` with an absolute file path
- Set account identity attribute to **`userId`** and set **authoritative / create identities on the application itself**
- Create and run Account Aggregation task `Aggregate MNB-HR`
- Know that after HR aggregation you must run an Identity Refresh (Lesson 06) to promote link attributes onto cubes
- Verify known identity cubes for leadership and scripted personas

## Why this matters

If HR is wrong, every downstream control is wrong. Authoritative aggregation is the root of joiner/mover/leaver truth at Meridian: when a Charlotte teller is hired or a New York wire specialist joins, HR gets the record first. The lab file uses a **real bank-style HRIS header** so you practice on columns you will see in production extracts—not a toy schema.

**Control / audit:** Examiners ask “what is the authoritative source of workforce identity?” Your answer is `MNB-HR` backed by HRIS extract—not AD and not the IT entitlement dump. Task results prove nightly (or on-demand) aggregation succeeded.

## Concepts

An **authoritative** application is allowed to create and update IdentityIQ identities from its accounts. That flag lives **on the application object** (for Meridian: on the Delimited File app `MNB-HR` itself)—not on the aggregation task and not as a global IIQ switch. Non-authoritative apps (Lesson 09+) only attach accounts/entitlements to existing people.

**CSV reality:** Delimited File feeds are almost always CSV (comma + header). Lab `HRApplications.txt` is CSV content with a `.txt` name—configure delimiter = comma and “has header.”

**Orphan trap (preview):** If a *non-HR* app has create-identities / authoritative enabled, uncorrelated accounts can be aggregated in as **orphan identities**—cubes with no real HR person behind them. Meridian turns create-identities **on** only for `MNB-HR`. Lesson 09 and Lessons 19–20 drill the orphan remediation path.

| Bank column | Governance role |
| --- | --- |
| `userId` | Stable account/identity key (`MNB#####`) — native identity |
| `name` | Login-style name (`helen.ross`) |
| `email` | Corporate or vendor mail |
| `managersAssociateID` | Manager’s `userId` (hierarchy) |
| `manager` | Manager display name |
| `inactive` / `status` / `statusFlag` | Active vs terminated (`false`/`Active`/`A` vs `true`/`Terminated`/`T`) |
| `exceptions` | Leave-of-absence marker (`LOA`) — not termination |
| `departmentName` / `division` / `JobCode` | Org model for roles & populations |
| `employeeType` / `userType` | Employee / Contractor |
| `hireDate` / `terminationDate` / `contractEndDate` | Lifecycle evidence |
| `costCenter`, `location`, `title`, … | Extended bank HRIS fields (see column map) |

Full header and promote list: [`lab-data/reference/hr-column-map.md`](../../lab-data/reference/hr-column-map.md).

```text
  HRApplications.txt  (real-bank header, 52 columns)
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

**Why `userId` over email as account id:** Emails change, contractors use vendor domains (`raj.external`), and rehires need a stable associate ID. Meridian `userId` values (`MNB#####`) are durable and match `employeeId` on IT dumps for correlation.

## How it works

An **authoritative** Delimited File application maps each HR row to an account whose **native identity** is `userId`. With create-identities enabled, Account Aggregation upserts Identity cubes; non-authoritative apps later only attach Links.

```text
HRApplications.txt (row per worker)
        │
        ▼
MNB-HR schema (native identity = userId)
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
| Connector | Delimited File | Lab stand-in for HRIS feed; format ≈ **CSV** |
| File format | Comma + header | Almost always CSV in real Delimited File work |
| Native identity | `userId` | Stable associate ID across email/vendor domains |
| Manager correlation | `managersAssociateID` → `userId` | Bank-style manager link |
| Authoritative / create identities | **ON on the `MNB-HR` application** | Workforce source of truth (app-level flag) |
| Task name | `Aggregate MNB-HR` | Auditable control activity |
| After aggregate | `Refresh MNB Attributes` (+ managers as needed) | Promotes Link attrs onto Identity (Lesson 06) |

> **Production reality:** Banks usually feed HR from Workday, SAP SuccessFactors, or similar via the native connector or a governed flat-file drop—not a hand-edited CSV. Lesson 04 teaches the authoritative pattern; Part II connector lessons cover live HRIS paths. When the feed *is* a file, treat it as CSV unless the vendor documents otherwise.

**Real-life Meridian example.** `amelia.brooks` appears in HR on hire day; after `Aggregate MNB-HR`, her cube exists so birthright and joiner workflows have a person to attach—not an orphan IT account.

## Before you start

- [ ] `realpath ~/iiq-lab-data/HRApplications.txt` works; `%%MNB_HR_FILE%%` aligned (Lesson 03)
- [ ] Logged in as `spadmin`
- [ ] Evidence folder for today exists (`~/iiq-lab-evidence/YYYY-MM-DD/`)
- [ ] Naming card from Lesson 03 available
- [ ] Prefer: `config/Application/MNB-Application-HR.xml` already imported (Debug shows `MNB-HR`)

## Lab procedure

### Task 0 — Bank craft path (import-first vs UI-first)

Meridian Ops does not rebuild `MNB-HR` from memory on every laptop. The academy seed owns the Application in git.

1. Open Debug / Applications. If **`MNB-HR`** exists from Lesson 03 import, take the **verify path**: open the app, confirm authoritative / CSV settings, fix file path if needed, skip create-from-scratch tasks but still walk Tasks 3–7 for schema and aggregation.
2. If `MNB-HR` is missing, take the **UI craft path** (Tasks 2–4), then **export** clean XML to `config/Application/MNB-Application-HR.xml` (or diff against the seed) as the bank craft exit gate.
3. CHANGELOG either: `Verified seed MNB-HR` or `UI-created MNB-HR → exported to config/`.

**Expected result:** You know which path you are on before creating duplicates.

### Task 1 — Inspect the HR header

Know the columns before you wire the connector—schema mistakes here cascade into every downstream cube. This header is intentionally **bank-realistic** (52 fields).

1. Open the file and column map:

```bash
head -1 ~/iiq-lab-data/HRApplications.txt | tr ',' '\n' | nl
wc -l ~/iiq-lab-data/HRApplications.txt
less ~/iiq-lab-data/reference/hr-column-map.md   # or open from repo lab-data/reference/
```

2. Confirm the header starts with `addressWork,city,company,...` and includes `userId`, `name`, `managersAssociateID`, `inactive`, `exceptions`, `employeeType`, `JobCode`.
3. Find a leaver: `inactive=true` / `status=Terminated` (e.g. `samir.hassan` MNB00094) and an on-leave worker: `exceptions=LOA` (e.g. `sofia.torres` MNB00095).

**Expected result:** Notebook lists key column → governance role mappings; you can cite one terminated and one LOA persona.

### Task 2 — Create application MNB-HR

You are creating a Delimited File application whose feed is CSV in all but name. Production HR drops are almost always comma-separated with a header—match that habit here.

1. In IIQ: **Applications** → **Add New Application** (or equivalent).
2. Application type: **DelimitedFile** (Delimited File connector).
3. Name: `MNB-HR`. Owner: `spadmin` (lab).
4. File settings:
   - File path: absolute path to `HRApplications.txt` (expanded `/Users/...`, not `~`)
   - **File format:** treat as **CSV** — delimiter: comma; has header row: yes
   - Do not switch to tab/pipe unless you are deliberately testing a non-CSV feed
5. Save.

**Expected result:** Application `MNB-HR` appears in the application list; notebook notes “Delimited File = CSV (comma + header).”

**If it fails:** Check connector type spelling; confirm file path is readable by Tomcat OS user.

### Task 3 — Schema discovery and identity attribute

1. Open `MNB-HR` → Schema (or Configuration → Schema).
2. Discover/preview attributes from the file header (or confirm the seeded schema from `config/Application/MNB-Application-HR.xml`).
3. Set **account identity attribute** (native identity) to **`userId`**.
4. Ensure key fields exist on the schema: `name`, `email`, `firstname`, `lastname`, `managersAssociateID`, `inactive`, `status`, `exceptions`, `departmentName`, `JobCode`, `employeeType`, `location`.
5. Save.

**Expected result:** Schema lists bank-style HR columns; account id is `userId`.

### Task 4 — Authoritative / create identities (on the application)

Authoritative is **not** a property of the aggregation task. It is set on the **Delimited File application** `MNB-HR`: when that app is marked to create identities, Account Aggregation will mint Identity cubes from HR accounts.

1. On `MNB-HR`, locate settings for creating identities from accounts (**Authoritative application** / **Create identities**—or equivalent wording for your IIQ version). This lives on the **application configuration**, not on `Aggregate MNB-HR`.
2. Enable identity creation from this application (`authoritative=true` / create-identities ON).
3. Save. Log in CHANGELOG: `MNB-HR authoritative=true`.
4. Confirm no other Meridian app will get this flag in later lessons—IT dumps must stay non-authoritative so uncorrelated rows do not become orphan identities.

**Expected result:** Notebook documents that **only** `MNB-HR` creates identities in the Meridian lab (IT apps must remain non-authoritative). CHANGELOG contains exactly: `MNB-HR authoritative=true`.

### Task 5 — Create and run Aggregate MNB-HR

Aggregation loads HR accounts onto Links (and creates cubes because the **app** is authoritative). It does **not** finish promoting every identity attribute or resolving managers—that is Identity Refresh (Lesson 06).

1. **Tasks** → New Task → type **Account Aggregation** (or equivalent).
2. Name: `Aggregate MNB-HR`.
3. Select application `MNB-HR`.
4. Save, then **Run Now**.
5. Open the **Task Result**. Note start time, duration, accounts scanned/created/updated, errors.
6. Write in your notebook: “Next control step after HR aggregate = run `Refresh MNB Attributes` (and `Refresh MNB Managers` when hierarchy matters)—Lesson 06. Aggregation alone is not enough to trust promoted identity attributes.”

**Expected result:** Task result Success (or Success with warnings you understand). Account count > 0 (lab HR is ~70–80 workers including header). Screenshot saved to evidence folder. Pipeline note points at the refresh tasks.

**If it fails:** Zero accounts → path, permissions, delimiter, or header parse. Check Tomcat logs; re-test file with `head`.

### Task 6 — Verify personas

1. **Identities** → search `helen.ross` (MNB00001). Open cube; confirm HR account from `MNB-HR`.
2. Search `priya.wire` (MNB00090)—active wire specialist, manager should resolve toward `rachel.evans` / MNB00005 after refresh (Lesson 06 may complete manager link).
3. Search `samir.hassan` (MNB00094)—terminated (`status=0`); note how inactive appears today.
4. Spot-check `amelia.brooks` (new teller) and `raj.external` (contractor, vendor email).

**Expected result:** At least four cubes found with `MNB-HR` accounts. Terminated vs active difference visible on status/inactive attributes (exact UI label varies).

### Task 7 — Binder note — control statement

Write: “Meridian’s authoritative workforce source is application `MNB-HR` (authoritative / create-identities set **on that Delimited File app**). Aggregation task `Aggregate MNB-HR` materializes accounts and cubes; Identity Refresh tasks from Lesson 06 promote HR Link attributes onto identities. Control owner (lab): IAM trainee / (prod) HRIS+IAM Ops.”

**Expected result:** One control statement ready for training binder.

## Acceptance criteria

- [ ] `MNB-HR` Delimited File app present (seed import **or** UI create) with absolute CSV path
- [ ] Account identity attribute = `userId`
- [ ] Authoritative / create identities enabled **on the application**; CHANGELOG: `MNB-HR authoritative=true`
- [ ] Bank craft exit: seed verified **or** XML exported/diffed under `config/Application/MNB-Application-HR.xml`
- [ ] `Aggregate MNB-HR` ran with non-zero accounts (task from seed or UI)
- [ ] Notebook notes the post-aggregate refresh tasks required (Lesson 06)
- [ ] Cubes verified for helen.ross, priya.wire, samir.hassan
- [ ] Evidence screenshot of task result filed
- [ ] CHANGELOG updated

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Duplicate MNB-HR | Created UI copy over seed | Delete duplicate; keep seed; re-import |
| 0 accounts aggregated | Bad path / perms / delimiter | Fix absolute path; confirm comma + header (CSV); check `%%MNB_HR_FILE%%` |
| Duplicate identities | Wrong account id (email) | Rebuild schema with `userId` |
| Missing columns | Schema not rediscovered after file change | Rediscover schema; re-aggregate |
| Tomcat cannot read file | macOS privacy / ownership | Adjust ACL; move under readable home path |
| Identities not searchable | Aggregation failed silently | Read full task result errors + syslog |
| Attrs blank after aggregate | Refresh not run yet | Expected—run `Refresh MNB Attributes` in Lesson 06 |
| Orphan cubes from IT later | Non-HR app left authoritative | Disable create-identities on IT apps (Lesson 09) |

## Training binder evidence

- Screenshot: `MNB-HR` application configuration (path visible, secrets none)
- Screenshot: successful `Aggregate MNB-HR` task result with counters
- Screenshot: `helen.ross` cube Accounts tab showing `MNB-HR`
- CHANGELOG lines for app + task creation

**Examiner question:** “Prove which system creates workforce identities and show the last successful aggregation.”

## Knowledge check

1. What makes an application authoritative?
2. Why prefer `userId` over email as account identity?
3. Where do you look first when aggregation returns zero accounts?
4. Which persona demonstrates a terminated worker in HR?
5. What is the exact task name for HR aggregation in this curriculum?
6. After `Aggregate MNB-HR`, which kind of task promotes identity attributes from the HR Link?
7. Where is `authoritative=true` set—on the task or on the application?

### Answers

1. It is configured on the **application** to create/update IdentityIQ identities from its accounts—HR is the workforce source of truth.
2. Emails change and vendors use non-corporate domains; bank associate `userId` values are stable (and match IT `employeeId` for correlation).
3. File path, OS permissions, delimiter/header parse (CSV settings)—before blaming IIQ logic.
4. `samir.hassan` (MNB00094), `inactive=true` / `status=Terminated` with terminationDate set.
5. `Aggregate MNB-HR`.
6. An **Identity Refresh** task with attribute promotion enabled—Meridian uses `Refresh MNB Attributes` (Lesson 06).
7. On the **Delimited File application** (`MNB-HR`), not on the aggregation task.

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
- Intentionally mis-set delimiter to pipe once on a **copy** app, observe zero accounts, then revert—reinforces “Delimited File ≈ CSV.”

## Summary

- `MNB-HR` is Meridian’s authoritative Delimited File (CSV) application keyed on **`userId`** (bank-style HRIS header); authoritative is set **on the app** (seed: `config/Application/MNB-Application-HR.xml`).
- `Aggregate MNB-HR` materializes identity cubes from `HRApplications.txt`; Identity Refresh (Lesson 06) promotes Link attributes onto cubes.
- Bank craft exit: object survives in git — verify seed or export UI work to `config/`.

---

**Previous:** [Lesson 03 — Lab Hygiene, Naming & Evidence Habits](03-lab-hygiene-and-naming.md)  
**Next:** [Lesson 05 — HR Schema & Identity Attribute Design](05-hr-schema-and-identity-attrs.md)
