# Lesson 09 — Onboard IT Access Inventory App

| Field | Value |
| --- | --- |
| **Level** | Beginner |
| **Track** | Applications |
| **Time** | 75–90 minutes |
| **Prereq** | Lesson 08; authoritative `MNB-HR` identities exist |
| **Lab data** | `~/iiq-lab-data/EmployeeData.txt` (also `apps/MNB-IT-Access.csv`) |

## Learning objectives

You will be able to:

- Inspect Meridian’s denormalized IT entitlement dump (CSV) and count access codes
- Create non-authoritative Delimited File application `MNB-IT-Access`
- Mark `itAccess` as the entitlement/group attribute
- Create and run `Aggregate MNB-IT-Access` without creating new (orphan) identities
- Explain why uncorrelated accounts must **not** become orphan identities via create-identities
- Spot-check toxic entitlements on `jordan.reed` and `kai.nguyen`

## Why this matters

Most banks start with a messy entitlement dump before perfect connectors. Meridian’s `EmployeeData.txt` is intentionally denormalized and duplicated—like production exports from a CMDB or access warehouse. The content is **CSV** (comma + header) even though the extension is `.txt`. You must onboard imperfect truth safely without letting IT invent people.

> **Production reality.** An inventory dump like this is a legitimate *interim* production pattern (many programs really do start here), but its endgame is decomposition: each system inside the dump graduates to its own application with a native connector — AD (Lessons 56–57), databases via JDBC (Lesson 63), SaaS via API/SCIM (Lessons 68–76). Part II of this curriculum walks that graduation path system by system.

**Control / audit:** Only HR creates identities. IT apps correlate. Examiners ask whether non-HR sources can create orphan identities. Your `MNB-IT-Access` config must show create-identities **off**.

## Concepts

| App | Authoritative? | Creates identities? | Purpose |
| --- | --- | --- | --- |
| `MNB-HR` | Yes (set **on the Delimited File app**) | Yes | Workforce truth |
| `MNB-IT-Access` | No | **No** | Consolidated entitlement inventory |

### Orphan identities — what goes wrong if create-identities is on

An **orphan identity** is a cube that IIQ created from an application account that does **not** represent a real HR person (or is not yet correlated to one). Uncorrelated IT accounts can be aggregated into the system as orphan identities when the target application is marked authoritative / create-identities **on**.

| Outcome | When it happens | Meridian posture |
| --- | --- | --- |
| Account stays uncorrelated | Create-identities **off**; no matching Identity | Correct interim state → Lessons 17–19 remediate |
| Orphan Identity minted | Create-identities **on** for a non-HR app | **Wrong** — ghost people, fake certs, no leaver path |
| Correlated Link on HR cube | Keys match after correlation | Desired end state |

```text
  Uncorrelated IT account
        |
        +-- create-identities OFF --> uncorrelated account (fixable)
        |
        +-- create-identities ON  --> orphan Identity cube (control failure)
```

Never “empty the uncorrelated list” by turning create-identities on for `MNB-IT-Access`. That manufactures ghosts.

**File shape:** One row per (user, entitlement). Same `userName` repeats. Format = **CSV**.

| Column | Role |
| --- | --- |
| `userName` | Account native id candidate |
| `employeeId` | Correlation help toward HR |
| `email` | Secondary correlation / quality |
| `itAccess` | **Entitlement** code (WIRE_INIT, SAP_FI, …) |
| `accountStatus` | active/disabled on IT side |

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
   uncorrelated rows stay accounts—not orphan identities)
```

**SoD demo holders:** `jordan.reed` (`SAP_FI`+`AWS_ADMIN`), `kai.nguyen` (`IBSI`+`ECOM`), wire pair `priya.wire` / `marcus.approve`.

## How it works

`MNB-IT-Access` is a **non-authoritative** multi-valued entitlement inventory: many CSV rows share one `userName`, each carrying an `itAccess` code. Aggregation creates/updates accounts and entitlements; it must **never** mint Identity cubes.

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

| Config checkpoint | Required value | Exam talk-track |
| --- | --- | --- |
| Authoritative / create identities | **Off** | Only HR creates people |
| Entitlement attribute | `itAccess` | Managed attribute source |
| Correlation keys | employeeId / email (later) | Owned access |

**Real-life Meridian example.** `jordan.reed` has separate IT dump rows for `SAP_FI` and `AWS_ADMIN`. That multi-row shape is how SoD later detects a toxic combo on one cube—if create-identities were on, you would also invent ghost people for unmatched vendor rows.

## Before you start

- [ ] `~/iiq-lab-data/EmployeeData.txt` exists (absolute path recorded)
- [ ] `MNB-HR` identities searchable
- [ ] Runbook updated to include IT aggregate after HR (Lesson 08)

## Lab procedure

### Task 0 — Bank craft (import-first)

Prefer seeded `config/Application/MNB-Application-IT-Access.xml` and `Aggregate MNB-IT-Access`. If present, verify authoritative=false and CSV path; extend schema/entitlement flags in UI; re-export if you change durable settings. If missing, create in UI then export to that git path.

**Expected result:** CHANGELOG cites seed verify or `config/Application/MNB-Application-IT-Access.xml` export.

### Task 1 — Inspect the dump

Before creating the application, understand the multi-row-per-person shape—that design drives entitlement aggregation and later SoD detection.

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
4. Spot `raj.external` vendor email in the dump.

**Expected result:** Notebook lists distinct `itAccess` codes aligned to `entitlement-dictionary.csv`; you acknowledge duplicates are normal.

### Task 2 — Create MNB-IT-Access

Same Delimited File habit as HR: almost always **CSV** (comma + header), absolute path, `MNB-` name.

1. **Applications** → Add New → **DelimitedFile**.
2. Name: `MNB-IT-Access`. Owner: `spadmin` (lab); conceptually Technology owns inventory, IAM operates it.
3. File path: absolute path to `EmployeeData.txt`.
4. Delimiter: comma; has header: yes (CSV).
5. Save.

**Expected result:** Application `MNB-IT-Access` listed beside `MNB-HR`.

### Task 3 — Schema and entitlement attribute

1. Discover/define schema from header.
2. Set account identity attribute to `userName` **or** `employeeId` (pick one; document it—`employeeId` often correlates cleaner to HR; `userName` matches many IT exports). Curriculum default recommendation: **`employeeId`** if the connector allows stable account id from that column; otherwise `userName`.
3. Mark `itAccess` as the **entitlement** / group attribute (managed attribute promotion). Lesson 10 shows how to enrich those objects in the UI and how to **manually pull/create groups via the ManagedAttribute API** when aggregation alone is not enough.
4. Include `accountStatus`, `email`, `userName` on schema.
5. Save.

**Expected result:** Schema shows `itAccess` as entitlement-bearing; account id choice documented in CHANGELOG.

### Task 4 — Non-authoritative confirmation (prevent orphan identities)

Authoritative / create-identities is an **application** setting—same place you enabled it for `MNB-HR`. Here it must stay off so uncorrelated dump rows do not become orphan identities.

1. Open application settings for identity creation / authoritative flag on `MNB-IT-Access`.
2. Ensure `MNB-IT-Access` does **NOT** create identities (authoritative=false / create-identities OFF).
3. Save. Write control statement: “Only `MNB-HR` creates identities. Uncorrelated IT accounts remain accounts until correlation/remediation—never auto-minted orphans.”
4. CHANGELOG: `MNB-IT-Access authoritative=false`.

**Expected result:** Config screenshot or note proving create-identities disabled; orphan-risk sentence in binder.

**If it fails:** If UI defaults to create, explicitly disable before first aggregation.

### Task 5 — Aggregate MNB-IT-Access

1. Create Account Aggregation task named `Aggregate MNB-IT-Access`.
2. Select application `MNB-IT-Access`.
3. Run Now.
4. Read task result counters; screenshot to evidence.
5. Compare identity counts before vs after: you should **not** see a spike of brand-new cubes that lack HR (that would mean orphan creation).
6. Update runbook inventory row from Lesson 08 to “created.”
7. Optional but recommended: run `Refresh MNB Attributes` if you mapped any IT fields to identity attrs (rare this early); otherwise note that HR attribute promotion already ran in Lesson 06.

**Expected result:** Success with accounts/entitlements > 0. Uncorrelated accounts may exist—that is OK. New orphan identities are **not** OK.

### Task 6 — Verify entitlements on cubes

1. Open `jordan.reed` → Accounts / Entitlements. Look for `SAP_FI`, `AWS_ADMIN`, `GL_POST`, `ELDAP` (correlation may show under `MNB-IT-Access` link).
2. Open `kai.nguyen` → confirm `IBSI`, `ECOM`.
3. Open `priya.wire` / `marcus.approve` → `WIRE_INIT` / `WIRE_APPR`.
4. Open `samir.hassan` → residual IT rows with disabled status.
5. If entitlements missing or uncorrelated, note “correlation deferred to Lessons 17–19” but confirm aggregation created application accounts (as uncorrelated accounts, **not** as orphan identities).

**Expected result:** Written spot-check table for at least three personas. Partial correlation is acceptable this lesson if accounts exist on the app.

### Task 7 — Preview platform extracts (no onboard yet)

1. Skim `~/iiq-lab-data/apps/MNB-SAP-Finance.csv` and `MNB-CoreBanking.csv`.
2. Note why later lessons split crown-jewel platforms from the mega-dump.

**Expected result:** One paragraph: inventory app vs per-platform apps.

## Acceptance criteria

- [ ] IT dump inspected as CSV; distinct entitlements noted
- [ ] `MNB-IT-Access` created with absolute path
- [ ] `itAccess` configured as entitlement attribute
- [ ] Create-identities disabled; CHANGELOG `MNB-IT-Access authoritative=false`
- [ ] Bank craft exit: seed verified **or** XML under `config/Application/MNB-Application-IT-Access.xml`
- [ ] Orphan vs uncorrelated distinction written in binder
- [ ] `Aggregate MNB-IT-Access` succeeded with evidence
- [ ] jordan.reed / kai.nguyen / wire personas spot-checked
- [ ] CHANGELOG + runbook updated

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| 0 accounts | Path/delimiter/header | Same hygiene as HR; verify absolute path + CSV comma/header |
| New orphan identities | App marked authoritative | Disable create identities; clean orphans carefully (Lesson 19) |
| No entitlements visible | `itAccess` not marked entitlement | Fix schema; re-aggregate; Lesson 10 ManagedAttribute API if catalog empty |
| Duplicates alarms | Multi-row file | Expected—document; do not “dedupe away” entitlements blindly |
| Nothing on cube | Correlation mismatch | Confirm account id choice; continue to Lesson 17 |

## Training binder evidence

- Screenshot: `MNB-IT-Access` config showing non-authoritative
- Screenshot: `Aggregate MNB-IT-Access` result
- Screenshot: `jordan.reed` entitlements (or account link)
- Distinct entitlement count note vs dictionary
- Binder note: uncorrelated ≠ orphan identity

**Examiner question:** “Can your IT inventory feed create identities? Show me the setting and last aggregation. What happens to uncorrelated accounts?”

## Knowledge check

1. Why must IT apps be non-authoritative?
2. What column becomes the entitlement?
3. Name two people useful for SoD demos.
4. Why does the file have multiple rows per userName?
5. Where does `Aggregate MNB-IT-Access` sit in the nightly order?
6. What is an orphan identity, and how do uncorrelated accounts become one?

### Answers

1. Only HR should create workforce identities; IT must not invent people from messy dumps.
2. `itAccess`.
3. `jordan.reed` (SAP_FI+AWS_ADMIN) and `kai.nguyen` (IBSI+ECOM).
4. Denormalized entitlement inventory—one entitlement per row.
5. After `Aggregate MNB-HR`, before `Refresh MNB Attributes` / managers.
6. A cube minted from an app account without a real HR person; it happens when create-identities/authoritative is on for a non-HR app—uncorrelated accounts should stay accounts until remediated.

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “Delimited File connector” and “create identities” for non-authoritative target patterns.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — threads on inventory dumps vs per-app connectors.
- [NIST SP 800-53 AC-2](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — account management requiring known owners for accounts and privileges.
- [FFIEC IT Examination Handbook — Information Security](https://ithandbook.ffiec.gov/it-booklets/information-security.aspx) — access inventory and ownership expectations.
- [CIS Controls v8 — Control 5](https://www.cisecurity.org/controls/account-management) — maintaining an inventory of accounts and entitlements.


## Stretch lab

- Point a second app at `apps/MNB-IT-Access.csv` only if paths differ—otherwise treat it as the same dataset.
- Preview `apps/MNB-SAP-Finance.csv` schema for Lesson 12.
- Attempt advanced search for identities with `AWS_ADMIN` (may depend on entitlement indexing).
- On a **throwaway copy** app only, briefly enable create-identities, aggregate a tiny fake CSV with a nonsense user, observe the orphan cube, then delete the app/orphan and document why Meridian forbids this on `MNB-IT-Access`.

## Summary

- `MNB-IT-Access` onboards Meridian’s messy CSV entitlement dump without creating identities.
- Uncorrelated accounts are fixable; orphan identities from create-identities-on are a control failure.
- `itAccess` is the governable entitlement attribute; aggregation feeds cubes for SoD demos.
- Platform-specific apps come next; the inventory teaches imperfect-truth discipline.

---

**Previous:** [Lesson 08 — Task Operations & Scheduling Discipline](08-task-ops-and-scheduling.md)  
**Next:** [Lesson 10 — Entitlement Dictionary & Managed Attributes](10-entitlement-dictionary.md)
