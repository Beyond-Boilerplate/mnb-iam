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

- Inspect Meridian’s denormalized IT entitlement dump and count access codes
- Create non-authoritative Delimited File application `MNB-IT-Access`
- Mark `itAccess` as the entitlement/group attribute
- Create and run `Aggregate MNB-IT-Access` without creating new identities
- Spot-check toxic entitlements on `jordan.reed` and `kai.nguyen`

## Why this matters

Most banks start with a messy entitlement dump before perfect connectors. Meridian’s `EmployeeData.txt` is intentionally denormalized and duplicated—like production exports from a CMDB or access warehouse. You must onboard imperfect truth safely without letting IT invent people.

> **Production reality.** An inventory dump like this is a legitimate *interim* production pattern (many programs really do start here), but its endgame is decomposition: each system inside the dump graduates to its own application with a native connector — AD (Lessons 56–57), databases via JDBC (Lesson 63), SaaS via API/SCIM (Lessons 68–76). Part II of this curriculum walks that graduation path system by system.

**Control / audit:** Only HR creates identities. IT apps correlate. Examiners ask whether non-HR sources can create orphan identities. Your `MNB-IT-Access` config must show create-identities **off**.

## Concepts

| App | Authoritative? | Creates identities? | Purpose |
| --- | --- | --- | --- |
| `MNB-HR` | Yes | Yes | Workforce truth |
| `MNB-IT-Access` | No | **No** | Consolidated entitlement inventory |

**File shape:** One row per (user, entitlement). Same `userName` repeats.

| Column | Role |
| --- | --- |
| `userName` | Account native id candidate |
| `employeeId` | Correlation help toward HR |
| `email` | Secondary correlation / quality |
| `itAccess` | **Entitlement** code (WIRE_INIT, SAP_FI, …) |
| `accountStatus` | active/disabled on IT side |

```text
  EmployeeData.txt (many rows per person)
        |
        v
  MNB-IT-Access (non-authoritative)
        |
        v
  Aggregate MNB-IT-Access
        |
        v
  Links + entitlements on existing HR cubes
  (correlation may be partial until Lessons 17–18)
```

**SoD demo holders:** `jordan.reed` (`SAP_FI`+`AWS_ADMIN`), `kai.nguyen` (`IBSI`+`ECOM`), wire pair `priya.wire` / `marcus.approve`.

## Before you start

- [ ] `~/iiq-lab-data/EmployeeData.txt` exists (absolute path recorded)
- [ ] `MNB-HR` identities searchable
- [ ] Runbook updated to include IT aggregate after HR (Lesson 08)

## Lab procedure

### Task 1 — Inspect the dump

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

1. **Applications** → Add New → **DelimitedFile**.
2. Name: `MNB-IT-Access`. Owner: `spadmin` (lab); conceptually Technology owns inventory, IAM operates it.
3. File path: absolute path to `EmployeeData.txt`.
4. Delimiter: comma; has header: yes.
5. Save.

**Expected result:** Application `MNB-IT-Access` listed beside `MNB-HR`.

### Task 3 — Schema and entitlement attribute

1. Discover/define schema from header.
2. Set account identity attribute to `userName` **or** `employeeId` (pick one; document it—`employeeId` often correlates cleaner to HR; `userName` matches many IT exports). Curriculum default recommendation: **`employeeId`** if the connector allows stable account id from that column; otherwise `userName`.
3. Mark `itAccess` as the **entitlement** / group attribute (managed attribute promotion).
4. Include `accountStatus`, `email`, `userName` on schema.
5. Save.

**Expected result:** Schema shows `itAccess` as entitlement-bearing; account id choice documented in CHANGELOG.

### Task 4 — Non-authoritative confirmation

1. Open application settings for identity creation / authoritative flag.
2. Ensure `MNB-IT-Access` does **NOT** create identities.
3. Save. Write control statement: “Only `MNB-HR` creates identities.”

**Expected result:** Config screenshot or note proving create-identities disabled.

**If it fails:** If UI defaults to create, explicitly disable before first aggregation.

### Task 5 — Aggregate MNB-IT-Access

1. Create Account Aggregation task named `Aggregate MNB-IT-Access`.
2. Select application `MNB-IT-Access`.
3. Run Now.
4. Read task result counters; screenshot to evidence.
5. Update runbook inventory row from Lesson 08 to “created”.

**Expected result:** Success with accounts/entitlements > 0. No unexplained spike in brand-new identities that lack HR (if any appear, stop and fix authoritative flags/correlation).

### Task 6 — Verify entitlements on cubes

1. Open `jordan.reed` → Accounts / Entitlements. Look for `SAP_FI`, `AWS_ADMIN`, `GL_POST`, `ELDAP` (correlation may show under `MNB-IT-Access` link).
2. Open `kai.nguyen` → confirm `IBSI`, `ECOM`.
3. Open `priya.wire` / `marcus.approve` → `WIRE_INIT` / `WIRE_APPR`.
4. Open `samir.hassan` → residual IT rows with disabled status.
5. If entitlements missing or uncorrelated, note “correlation deferred to Lessons 17–19” but confirm aggregation created application accounts.

**Expected result:** Written spot-check table for at least three personas. Partial correlation is acceptable this lesson if accounts exist on the app.

### Task 7 — Preview platform extracts (no onboard yet)

1. Skim `~/iiq-lab-data/apps/MNB-SAP-Finance.csv` and `MNB-CoreBanking.csv`.
2. Note why later lessons split crown-jewel platforms from the mega-dump.

**Expected result:** One paragraph: inventory app vs per-platform apps.

## Acceptance criteria

- [ ] IT dump inspected; distinct entitlements noted
- [ ] `MNB-IT-Access` created with absolute path
- [ ] `itAccess` configured as entitlement attribute
- [ ] Create-identities disabled
- [ ] `Aggregate MNB-IT-Access` succeeded with evidence
- [ ] jordan.reed / kai.nguyen / wire personas spot-checked
- [ ] CHANGELOG + runbook updated

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| 0 accounts | Path/delimiter/header | Same hygiene as HR; verify absolute path |
| New orphan identities | App marked authoritative | Disable create identities; clean orphans carefully |
| No entitlements visible | `itAccess` not marked entitlement | Fix schema; re-aggregate |
| Duplicates alarms | Multi-row file | Expected—document; do not “dedupe away” entitlements blindly |
| Nothing on cube | Correlation mismatch | Confirm account id choice; continue to Lesson 17 |

## Training binder evidence

- Screenshot: `MNB-IT-Access` config showing non-authoritative
- Screenshot: `Aggregate MNB-IT-Access` result
- Screenshot: `jordan.reed` entitlements (or account link)
- Distinct entitlement count note vs dictionary

**Examiner question:** “Can your IT inventory feed create identities? Show me the setting and last aggregation.”

## Knowledge check

1. Why must IT apps be non-authoritative?
2. What column becomes the entitlement?
3. Name two people useful for SoD demos.
4. Why does the file have multiple rows per userName?
5. Where does `Aggregate MNB-IT-Access` sit in the nightly order?

### Answers

1. Only HR should create workforce identities; IT must not invent people from messy dumps.
2. `itAccess`.
3. `jordan.reed` (SAP_FI+AWS_ADMIN) and `kai.nguyen` (IBSI+ECOM).
4. Denormalized entitlement inventory—one entitlement per row.
5. After `Aggregate MNB-HR`, before `Refresh MNB Identities`.

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “Delimited File connector” and “authoritative application.”
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — threads on inventory dumps vs per-app connectors.
- [FFIEC IT Handbook — Information Security](https://ithandbook.ffiec.gov/it-booklets/information-security/) — access inventory and ownership expectations.
- Lessons 51–55 and 56+ — where each dump system graduates to a native connector.

## Stretch lab

- Point a second app at `apps/MNB-IT-Access.csv` only if paths differ—otherwise treat it as the same dataset.
- Preview `apps/MNB-SAP-Finance.csv` schema for Lesson 12.
- Attempt advanced search for identities with `AWS_ADMIN` (may depend on entitlement indexing).

## Summary

- `MNB-IT-Access` onboards Meridian’s messy entitlement dump without creating identities.
- `itAccess` is the governable entitlement attribute; aggregation feeds cubes for SoD demos.
- Platform-specific apps come next; the inventory teaches imperfect-truth discipline.

---

**Previous:** [Lesson 08 — Task Operations & Scheduling Discipline](08-task-ops-and-scheduling.md)  
**Next:** [Lesson 10 — Entitlement Dictionary & Managed Attributes](10-entitlement-dictionary.md)
