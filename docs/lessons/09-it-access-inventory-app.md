# Lesson 09 — Onboard IT Access Inventory App

| Field | Value |
| --- | --- |
| **Level** | Beginner |
| **Track** | Applications |
| **Time** | 75–90 minutes |
| **Prereq** | Lesson 08 (08b triage recommended); authoritative `MNB-HR` identities exist |
| **Lab data** | `~/iiq-lab-data/EmployeeData.txt` (also `apps/MNB-IT-Access.csv`) |

## Learning objectives

You will be able to:

- Inspect Meridian's denormalized IT entitlement dump (CSV) and count access codes
- Create the non-authoritative Delimited File application `MNB-IT-Access`
- Mark `itAccess` as entitlement **and** managed (multi-valued + merge rows) so aggregation fills the Entitlement Catalog
- Create and run `Aggregate MNB-IT-Access` without creating new (orphan) identities
- Explain why uncorrelated accounts must **not** become orphan identities via create-identities
- Spot-check toxic entitlement pairs on `jordan.reed` and `kai.nguyen`

## Why this matters

Most banks start with a messy entitlement dump before they have perfect connectors. Meridian's `EmployeeData.txt` is intentionally denormalized and duplicated — like a production export from a CMDB or access warehouse. Note that its content is **CSV** (comma-delimited with a header) even though the file extension is `.txt`. You must onboard this imperfect truth safely, without letting IT invent people.

> **Production reality.** An inventory dump like this is a legitimate *interim* production pattern — many programs really do start here — but its endgame is decomposition: each system inside the dump graduates to its own application with a native connector — Active Directory (Lessons 56–57), databases via JDBC (Lesson 63), SaaS via API/SCIM (Lessons 68–76). Part II of this curriculum walks that graduation path system by system.

**Control / audit:** Only HR creates identities. IT apps correlate. Examiners ask whether non-HR sources can create orphan identities — your `MNB-IT-Access` config must show create-identities **off**.

## Concepts

| App | Authoritative? | Creates identities? | Purpose |
| --- | --- | --- | --- |
| `MNB-HR` | Yes (set on the Delimited File app) | Yes | Workforce truth |
| `MNB-IT-Access` | No | **No** | Consolidated entitlement inventory |

### Orphan identities — what goes wrong if create-identities is on

An **orphan identity** is a cube IIQ created from an application account that does **not** represent a real HR person (or isn't yet correlated to one). Uncorrelated IT accounts get minted as orphan identities the moment the target application is marked authoritative / create-identities **on**.

| Outcome | When it happens | Meridian posture |
| --- | --- | --- |
| Account stays uncorrelated | Create-identities **off**; no matching Identity | Correct interim state → remediated in Lessons 17–19 |
| Orphan Identity minted | Create-identities **on** for a non-HR app | **Wrong** — ghost people, fake certs, no leaver path |
| Correlated Link on HR cube | Keys match after correlation | Desired end state |

```text
  Uncorrelated IT account
        |
        +-- create-identities OFF --> uncorrelated account (fixable)
        |
        +-- create-identities ON  --> orphan Identity cube (control failure)
```

> **Watch out:** Never "empty the uncorrelated list" by flipping create-identities on for `MNB-IT-Access`. That doesn't fix correlation — it manufactures ghost identities that break leaver processing and pollute certifications.

**File shape:** One row per (user, entitlement); the same `userName` repeats across rows.

| Column | Role |
| --- | --- |
| `userName` | Account native id candidate |
| `employeeId` | Correlation help toward HR — **same values as HR `userId`** (`MNB#####`) |
| `email` | Secondary correlation / quality signal |
| `itAccess` | **Entitlement** code (`WIRE_INIT`, `SAP_FI`, …) |
| `accountStatus` | active/disabled on the IT side |

```text
  EmployeeData.txt (CSV; many rows per person)
        |
        v
  MNB-IT-Access (non-authoritative)
        |
        v
  Aggregate MNB-IT-Access
        |
        v
  Links + entitlements on existing HR cubes
  (correlation may be partial until Lessons 17–18;
   uncorrelated rows stay accounts — not orphan identities)
```

**SoD demo holders:** `jordan.reed` (`SAP_FI` + `AWS_ADMIN`), `kai.nguyen` (`IBSI` + `ECOM`), wire pair `priya.wire` / `marcus.approve`.

## How it works

`MNB-IT-Access` is a **non-authoritative** multi-valued entitlement inventory: many CSV rows share one `userName`, each carrying an `itAccess` code. Aggregation creates/updates accounts and entitlements — it must **never** mint Identity cubes.

```text
EmployeeData.txt  (userName × itAccess rows)
        │
        ▼
MNB-IT-Access (create-identities OFF)
        │
        ▼
Aggregate MNB-IT-Access
        │
        ├── Account / Link per native id
        ├── Entitlements (WIRE_INIT, SAP_FI, …)
        └── Correlation later (Lessons 17–19) → HR cubes
```

| Config checkpoint | Required value | Why it matters |
| --- | --- | --- |
| Authoritative / create identities | **Off** | Only HR creates people |
| Entitlement + **managed** attribute | `itAccess` (`entitlement` **and** `managed`) | Catalog promotion source |
| Multi-valued + merge rows | `itAccess` multi; merge on account id | One Link collects all codes |
| Correlation keys | `employeeId` / `email` (later) | Ties access back to an owner |

**Real-life Meridian example.** `jordan.reed` has separate IT dump rows for `SAP_FI` and `AWS_ADMIN`. That multi-row shape is exactly how SoD later detects a toxic combo on one cube — but if create-identities were on, you would also invent ghost people for any unmatched vendor rows.

## Before you start

- [ ] `~/iiq-lab-data/EmployeeData.txt` exists (absolute path recorded)
- [ ] `MNB-HR` identities searchable
- [ ] Runbook updated to include IT aggregate after HR (Lesson 08)

## Lab procedure

### Task 0 — Build in the UI

Create `MNB-IT-Access` and `Aggregate MNB-IT-Access` in the UI (authoritative=false). Optional export to `config/Application/MNB-Application-IT-Access.xml`.

**Expected result:** CHANGELOG cites the UI create (and optional config export path).

### Task 1 — Inspect the dump

Before creating the application, understand the multi-row-per-person shape — it drives both entitlement aggregation and later SoD detection.

1. Inspect header and samples:

```bash
head -5 ~/iiq-lab-data/EmployeeData.txt
wc -l ~/iiq-lab-data/EmployeeData.txt
```

2. List distinct entitlement codes:

```bash
cut -d',' -f7 ~/iiq-lab-data/EmployeeData.txt | sort | uniq -c | sort -nr
```

3. Confirm duplicate usernames (multiple rows per person) and note `accountStatus` values including `disabled` for leavers with residual rows (`samir.hassan`).
4. Spot `raj.external`'s vendor email in the dump.

**Expected result:** Notebook lists distinct `itAccess` codes aligned to `entitlement-dictionary.csv`; you recognize duplicates as normal, not a data-quality bug.

### Task 2 — Create MNB-IT-Access

Same Delimited File habit as HR: almost always **CSV** (comma + header), absolute path, `MNB-` name.

1. **Applications** → Add New → **DelimitedFile**.
2. Name: `MNB-IT-Access`. Owner: `spadmin` (lab) — conceptually Technology owns the inventory, IAM operates it.
3. File path: absolute path to `EmployeeData.txt`.
4. Delimiter: comma; has header: yes (CSV).
5. Save.

**Expected result:** Application `MNB-IT-Access` listed beside `MNB-HR`.

### Task 3 — Schema and entitlement attribute

1. Discover/define the schema from the header.
2. Set the account identity attribute to `userName` **or** `employeeId` (pick one and document it — `employeeId` often correlates more cleanly to HR; `userName` matches many IT exports). Curriculum default: **`employeeId`** if your connector allows a stable account id from that column, otherwise `userName`.
3. Configure `itAccess` for **both** Link entitlements **and** Entitlement Catalog promotion:
   - Mark **entitlement** — values appear on accounts / identity entitlements.
   - Mark **managed** — distinct values promote into `ManagedAttribute` catalog entries when Account Aggregation runs with **Promote managed attributes** enabled.
   - Mark **multi-valued** — required for this denormalized dump (many rows per person).
   - On the Delimited File app, enable **merge rows** (merge/index on the account identity attribute) so one Link accumulates every `itAccess` code instead of keeping only the last CSV row.
   - UI labels vary by build ("Managed", "Managed Attribute", a checkbox beside Entitlement). In exported XML you want both flags: `entitlement="true" managed="true" multi="true"`.
4. Include `accountStatus`, `email`, `userName` on the schema.
5. Save.

> **Watch out:** Don't stop at entitlement-only. `entitlement="true"` without `managed="true"` puts codes on cubes but leaves the Entitlement Catalog empty — Lesson 10 can't enrich what was never promoted.

**Expected result:** Schema shows `itAccess` as entitlement **and** managed (multi-valued); merge rows on; account id choice documented in CHANGELOG.

### Task 4 — Non-authoritative confirmation (prevent orphan identities)

Authoritative / create-identities is an **application** setting — the same place you enabled it for `MNB-HR`. Here it must stay off so uncorrelated dump rows don't become orphan identities.

1. Open application settings for identity creation / authoritative flag on `MNB-IT-Access`.
2. Ensure `MNB-IT-Access` does **NOT** create identities (authoritative=false / create-identities OFF).
3. Save. Write the control statement: "Only `MNB-HR` creates identities. Uncorrelated IT accounts remain accounts until correlation/remediation — never auto-minted as orphans."
4. CHANGELOG: `MNB-IT-Access authoritative=false`.

**Expected result:** Config screenshot or note proving create-identities disabled; orphan-risk sentence in the binder.

**If it fails:** If the UI defaults to create, explicitly disable it before the first aggregation.

### Task 5 — Aggregate MNB-IT-Access

1. Create an Account Aggregation task named `Aggregate MNB-IT-Access`.
2. Select application `MNB-IT-Access`.
3. Confirm **Promote managed attributes** is enabled on the task (needed alongside `managed="true"` on `itAccess` to populate the Entitlement Catalog — this is not a separate "entitlement aggregation" task for a Delimited File app).
4. Run Now.
5. Read the task result counters; screenshot to evidence.
6. Spot-check **Applications** → `MNB-IT-Access` → Entitlements / **Entitlement Catalog** for codes such as `WIRE_INIT` or `SAP_FI`. If the catalog is empty but values are on cubes, the schema is missing **managed** — fix Task 3 and re-aggregate.
7. Compare identity counts before vs. after: you should **not** see a spike of brand-new cubes with no HR record — that would signal orphan creation.
8. Update the runbook inventory row from Lesson 08 to "created."

**Expected result:** Success with accounts/entitlements greater than zero **and** ManagedAttribute/catalog entries for distinct `itAccess` codes. Uncorrelated accounts are fine here; new orphan identities are not.

### Task 6 — Verify entitlements on cubes

Correlation between HR and IT accounts doesn't land until Lessons 17–18, because the two sources key off different fields (`userId` vs. `userName`/`employeeId`). Prove inventory landed on the **Application** side first — that's your Lesson 09 evidence, not a broken correlation.

1. Open `jordan.reed` → Accounts / Entitlements. Look for `SAP_FI`, `AWS_ADMIN`, `GL_POST`, `ELDAP` (may be absent on the cube until correlation).
2. Confirm the same codes exist under **Applications → `MNB-IT-Access`** (required).
3. Open `kai.nguyen` → confirm `IBSI`, `ECOM` on the app and/or cube.
4. Open `priya.wire` / `marcus.approve` → `WIRE_INIT` / `WIRE_APPR`.
5. Open `samir.hassan` → residual IT rows with disabled status.
6. If entitlements are missing on cubes or uncorrelated, note "correlation deferred to Lessons 17–19" but confirm aggregation created **application** accounts (uncorrelated accounts, not orphan identities).

**Expected result:** A written spot-check table for at least three personas. Partial or zero correlation on HR cubes is acceptable as long as accounts exist on the app.

### Task 7 — Preview platform extracts (no onboard yet)

1. Skim `~/iiq-lab-data/apps/MNB-SAP-Finance.csv` and `MNB-CoreBanking.csv`.
2. Note why later lessons split crown-jewel platforms out of the mega-dump instead of leaving everything in one inventory file.

**Expected result:** One paragraph on inventory app vs. per-platform apps.

## Acceptance criteria

- [ ] IT dump inspected as CSV; distinct entitlements noted
- [ ] `MNB-IT-Access` created with absolute path
- [ ] `itAccess` configured as entitlement **and** managed (multi-valued); merge rows enabled
- [ ] Create-identities disabled; CHANGELOG `MNB-IT-Access authoritative=false`
- [ ] Bank craft exit: works in IIQ; optional XML under `config/Application/MNB-Application-IT-Access.xml`
- [ ] Orphan vs. uncorrelated distinction written in binder
- [ ] `Aggregate MNB-IT-Access` succeeded with evidence (promote managed attributes on)
- [ ] Entitlement Catalog shows distinct `itAccess` codes (not only on identity cubes)
- [ ] `jordan.reed` / `kai.nguyen` / wire personas spot-checked
- [ ] CHANGELOG + runbook updated

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| 0 accounts | Path/delimiter/header | Same hygiene as HR; verify absolute path + CSV comma/header |
| New orphan / login-named cubes | App marked authoritative / create-identities ON | Disable create identities; clean orphans carefully (Lesson 19); never re-enable "to clear" uncorrelated |
| No entitlements visible | `itAccess` not marked entitlement | Fix schema; re-aggregate; Lesson 10 ManagedAttribute repair if catalog stays empty |
| Entitlements on cubes, **catalog empty** | `entitlement` set but **managed** not set (or promote off on task) | Set `managed="true"` on `itAccess`; enable Promote managed attributes; re-aggregate |
| Only one code per person | Merge rows off / `itAccess` not multi | Enable merge on account id; mark multi-valued; re-aggregate |
| Duplicates alarm you | Multi-row file | Expected — document; don't dedupe entitlements away |
| Nothing on HR cube, rows on app | Correlation not configured yet | Expected — verify under Application → Accounts; correlation lands in Lessons 17–18 |

## Training binder evidence

- Screenshot: `MNB-IT-Access` config showing non-authoritative
- Screenshot: `Aggregate MNB-IT-Access` result
- Screenshot: `jordan.reed` entitlements (or account link)
- Distinct entitlement count note vs. dictionary
- Binder note: uncorrelated ≠ orphan identity

**Ops note:** If a compliance question ever asks "can your IT inventory create identities?" — the answer is a config screenshot and a task result, not a promise.

## Knowledge check

1. Why must IT apps be non-authoritative?
2. What column becomes the entitlement, and which two schema flags must both be set for catalog promotion?
3. Name two personas useful for SoD demos.
4. Why does the file have multiple rows per `userName`?
5. Where does `Aggregate MNB-IT-Access` sit in the nightly order?
6. What is an orphan identity, and how do uncorrelated accounts become one?
7. Why can identity entitlements show `WIRE_INIT` while the Entitlement Catalog stays empty?

### Answers

1. Only HR should create workforce identities; IT must not invent people from a messy dump.
2. `itAccess`; **entitlement** and **managed** (plus multi-valued + merge rows for this dump).
3. `jordan.reed` (`SAP_FI`+`AWS_ADMIN`) and `kai.nguyen` (`IBSI`+`ECOM`).
4. Denormalized entitlement inventory — one entitlement per row.
5. After `Aggregate MNB-HR`, before `Refresh MNB Attributes` / managers.
6. A cube minted from an app account without a real HR person; it happens when create-identities/authoritative is on for a non-HR app — uncorrelated accounts should stay accounts until remediated.
7. Schema has `entitlement` without `managed` (or Promote managed attributes off) — values attach to Links but never become `ManagedAttribute` catalog objects.

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search "Delimited File connector" and "create identities" for non-authoritative target patterns.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — threads on inventory dumps vs. per-app connectors.
- [NIST SP 800-53 AC-2](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — account management requiring known owners for accounts and privileges.
- [FFIEC IT Examination Handbook — Information Security](https://ithandbook.ffiec.gov/it-booklets/information-security.aspx) — access inventory and ownership expectations.
- [CIS Controls v8 — Control 5](https://www.cisecurity.org/controls/account-management) — maintaining an inventory of accounts and entitlements.

## Stretch lab

- Preview `apps/MNB-SAP-Finance.csv` schema for Lesson 11.
- Attempt an advanced search for identities with `AWS_ADMIN` (may depend on entitlement indexing).
- On a **throwaway copy** app only, briefly enable create-identities, aggregate a tiny fake CSV with a nonsense user, observe the orphan cube, then delete the app/orphan and document why Meridian forbids this on `MNB-IT-Access`.

## Summary

- `MNB-IT-Access` onboards Meridian's messy CSV entitlement dump without creating identities.
- Uncorrelated accounts are fixable; orphan identities from create-identities-on are a control failure.
- `itAccess` must be entitlement **and** managed (multi + merge rows); aggregation feeds cubes **and** the Entitlement Catalog for SoD/certs.
- Platform-specific apps come next; the inventory app teaches imperfect-truth discipline first.

## Feedback

Could you explain orphan vs uncorrelated, and why `itAccess` needs **managed** as well as entitlement — without looking? If the Entitlement Catalog was empty after a "successful" aggregate, note whether Promote managed attributes was ON and whether merge rows was enabled.

---

**Previous:** [Lesson 08 — Task Operations & Scheduling Discipline](08-task-ops-and-scheduling.md)  
**Next:** [Lesson 10 — Entitlement Dictionary & Managed Attributes](10-entitlement-dictionary.md)
