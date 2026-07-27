# Lesson 12 — Onboard SAP Finance

**Level:** Intermediate  
**Track:** Applications  
**Time:** 60–75 min  
**Prereq:** Lesson 11 (`MNB-CoreBanking` pattern)  

**Lab data:**
- Repo: `lab-data/apps/MNB-SAP-Finance.csv`
- Runtime path: `~/iiq-lab-data/apps/MNB-SAP-Finance.csv`
- Cross-check: `lab-data/apps/MNB-AWS-Cloud.csv` (Jordan’s toxic pair)

---

## Learning objectives

You will be able to:

- Onboard **MNB-SAP-Finance** from a finance ERP extract with entitlement **SAP_FI**
- Distinguish active vs disabled SAP accounts in the extract and in IIQ
- Identify **jordan.reed** as the seeded SoD / toxic-combination persona (`SAP_FI` + `AWS_ADMIN`)
- Keep the application non-authoritative and document Finance ownership
- Produce aggregation evidence suitable for SOX-style system-access questions

---

## Why this matters

**Business.** SAP Finance posts journals, vendor payments, and closing entries. Access labeled `SAP_FI` is not “another IT group”—it is the finance system of record for Meridian’s books.

**Control / audit.** SOX and internal audit ask who can post in SAP and whether those people also hold infrastructure bypass rights. Meridian’s SoD matrix flags **SAP_FI + AWS_ADMIN**. You need a clean application object before policy lessons can fire on real accounts.

---

## Concepts

**Toxic combination (preview).** Holding finance SoR access and cloud admin together enables both changing financial records and potentially covering tracks in infrastructure. Lab persona:

| Persona | employeeId | SAP_FI | AWS_ADMIN | Intent |
| --- | --- | --- | --- | --- |
| `jordan.reed` | MNB00092 | active | active (Lesson 13) | SoD demo — toxic |
| `samir.hassan` | MNB00094 | disabled | — | Terminated residual (Lesson 20) |
| `anita.ross` | MNB00010 | disabled | disabled in AWS file | Inactive finance staff |

```
Finance extract ──► MNB-SAP-Finance ──► entitlement SAP_FI
                         │
                         ├── correlate later to HR cube
                         └── jordan.reed also gets AWS_ADMIN (Lesson 13)
                                    │
                                    ▼
                         SoD policy (Lessons 39–41)
```

| CSV field | Notes in this extract |
| --- | --- |
| `entitlement` | Always `SAP_FI` |
| `accountStatus` | Mix of `active` and `disabled` — preserve both |
| Row count | **8** accounts (header + 8 data rows) |

Do **not** filter out disabled rows at aggregation time. Disabled-but-present accounts are governance signal (leavers, suspended staff).

> **Production reality.** Real SAP governance does not run on a CSV of one `SAP_FI` code. Production uses the **SAP Direct security connector** (Lesson 79), which aggregates actual SAP roles and profiles (`SAP_ALL`, `Z*` composite roles) over RFC/BAPI, and SAP HR/HCM (Lesson 78) if SAP feeds workforce data. The CSV here stands in so you can learn the toxic-pair story first; the SoD policy you'll build in Lessons 39–41 works identically against real SAP role entitlements.

---

## How it works

`MNB-SAP-Finance` mirrors Core as a non-authoritative platform extract with entitlement `SAP_FI` (critical) under Finance ownership (`deepa.nair`). It exists so SoD can pair finance SoR access with cloud admin as a named finding.

```text
MNB-SAP-Finance.csv → Application (create OFF) → Aggregate
        │
        ▼
SAP_FI entitlement on finance holders
        │
        ▼
Later: correlation + MNB-SOD finance/cloud policies
```

| Checkpoint | Value |
| --- | --- |
| Entitlement | `SAP_FI` |
| Owner | `deepa.nair` (FIN) |
| Create identities | Off |
| SoD partner | `AWS_ADMIN` |

**Real-life Meridian example.** `jordan.reed` holding `SAP_FI` plus `AWS_ADMIN` is the intentional finance–cloud toxic pair—visible because SAP is its own application object.

## Before you start

- [ ] IIQ up; logged in as `spadmin`
- [ ] `~/iiq-lab-data/apps/MNB-SAP-Finance.csv` present
- [ ] `MNB-HR` contains `jordan.reed` and `samir.hassan`
- [ ] Lesson 11 pattern fresh (Delimited File, non-authoritative, Account Aggregation)
- [ ] Dictionary: SAP_FI = SAP Finance, risk **critical**; owner intent `deepa.nair` (Director of Finance)

---

## Lab procedure

### Task 1 — Inspect the SAP Finance extract

Finance SoR access is an exam magnet—inventory who holds SAP_FI before you create the application object.

1. Open `~/iiq-lab-data/apps/MNB-SAP-Finance.csv`.
2. List each `userName` and `accountStatus`.
3. Highlight:
   - Active: `amelia.foster`, `priya.fernandez`, `meera.nair`, **`jordan.reed`**
   - Disabled: `anita.ross`, `kai.howard`, `theo.foster`, **`samir.hassan`**
4. Confirm `jordan.reed` email `jordan.reed@meridiannb.com` / `MNB00092`.
5. Open `MNB-AWS-Cloud.csv` briefly and confirm `jordan.reed` also has `AWS_ADMIN` / active — note “toxic pair pending Lesson 13.”

**Expected result:** Eight SAP accounts; Jordan active on SAP_FI; Samir disabled on SAP_FI; toxic AWS overlap documented for Jordan.

**If it fails:** Re-copy lab apps folder; do not hand-edit Jordan’s row.

---

### Task 2 — Create MNB-SAP-Finance

1. Applications → Add New → Delimited File.
2. Name: `MNB-SAP-Finance`.
3. Path: absolute `~/iiq-lab-data/apps/MNB-SAP-Finance.csv`.
4. Delimiter comma; has header.
5. Owner: `spadmin` temporarily (Task 5 assigns Finance owner).
6. Save.

**Expected result:** Application `MNB-SAP-Finance` saved.

**If it fails:** Avoid name collisions with any earlier stretch app from Lesson 09.

---

### Task 3 — Schema and entitlement mapping

1. Discover/define schema: `userName`, `email`, `employeeId`, `entitlement`, `accountStatus`.
2. Account identity attribute: `userName`.
3. Entitlement attribute: `entitlement` → values will be `SAP_FI`.
4. Ensure create-identities / authoritative is **off**.
5. Save.

**Expected result:** Non-authoritative target with SAP_FI as entitlement.

**If it fails:** Match attribute names exactly to the CSV header (case-sensitive in many IIQ builds).

---

### Task 4 — Account Aggregation

1. Create task `Aggregate MNB-SAP-Finance` (Account Aggregation type).
2. Select `MNB-SAP-Finance`. Run Now.
3. Record in notebook: accounts aggregated, errors, duration.

**Expected result:** Successful run with ~**8** accounts; both active and disabled statuses retained per extract.

**If it fails:** Open task result detail; fix path/schema; re-run. Do not enable identity creation to “make accounts show on cubes.”

---

### Task 5 — Ownership and dictionary enrichment

1. Set application owner to `deepa.nair` if present; else note proxy `spadmin` → Finance Director.
2. Enrich managed attribute `SAP_FI`:
   - Display name: SAP Finance
   - Description: ERP finance modules
   - Risk: critical
   - Requestable: **no** (tightly controlled)
3. Write approval narrative: *SAP_FI requires manager + Finance application owner; cloud admin combination prohibited by SoD.*

**Expected result:** Ownership and entitlement dictionary aligned with Lesson 10 / Meridian risk language.

---

### Task 6 — Verify jordan.reed and samir.hassan

1. Search `jordan.reed`. Open Accounts / Entitlements.
2. Confirm `MNB-SAP-Finance` account with `SAP_FI` when correlated; otherwise confirm on application account list with status **active**.
3. Search `samir.hassan`. Confirm SAP account present with status **disabled** (not deleted).
4. Notebook: “Jordan = toxic SoD seed; Samir = terminated residual seed.”

**Expected result:** Jordan shows live SAP_FI; Samir shows disabled SAP_FI still in inventory—both intentional.

**If it fails:** Disabled rows skipped usually means a filter or “only aggregate active” option—disable that filter and re-aggregate.

---

### Task 7 — SOX-oriented evidence note

1. Add binder text:

```text
System: MNB-SAP-Finance (SAP_FI)
Population: Finance ERP users from nightly extract
Key risk user (lab): jordan.reed — also AWS_ADMIN (see MNB-AWS-Cloud)
Leaver residual (lab): samir.hassan — SAP_FI disabled but still present
```

**Expected result:** You can brief Internal Audit on how SAP access enters IIQ.

---

## Acceptance criteria

- [ ] **Bank craft exit:** `MNB-SAP-Finance` matches `config/Application/MNB-Application-SAP-Finance.xml` (import-verify or UI+export)

- [ ] `MNB-SAP-Finance` created; non-authoritative
- [ ] `Aggregate MNB-SAP-Finance` succeeded (~8 accounts)
- [ ] `SAP_FI` entitlement mapped and dictionary-enriched
- [ ] `jordan.reed` confirmed active SAP_FI; toxic AWS pair noted
- [ ] `samir.hassan` confirmed disabled SAP account retained
- [ ] Finance owner documented (`deepa.nair` or proxy)

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Only active accounts appear | Active-only aggregation option | Include disabled; re-aggregate |
| Jordan missing | CSV not the lab file / wrong path | Verify `MNB00092` row in file IIQ reads |
| Identities created for contractors | Authoritative flag on | Turn off; remediate stray cubes |
| SAP_FI not on cube | Correlation gap | Check app account list; defer to Lesson 17 |
| Confused with IT dump | Looking at `MNB-IT-Access` | Use platform app for ownership/certs |

---

## Training binder evidence

1. App definition screenshot (`MNB-SAP-Finance`)
2. Aggregation task result
3. `jordan.reed` SAP_FI evidence + note linking to AWS toxic pair
4. `samir.hassan` disabled SAP account screenshot
5. SoD matrix line: `SAP_FI,AWS_ADMIN` rationale

Examiner question: *“How do you detect finance users who also hold cloud admin?”* Answer path: platform apps + correlation + policy (later lessons).

---

## Knowledge check

1. What entitlement code does this application govern?
2. Why keep disabled SAP accounts in the extract?
3. Which persona is the toxic SAP_FI + AWS_ADMIN seed?
4. Who should own `MNB-SAP-Finance` at Meridian?
5. Should aggregating SAP create a new identity if email is unknown? Why?

### Answers

1. `SAP_FI`.
2. Disabled accounts still represent residual or suspended access that certifications and leaver hunts must see.
3. `jordan.reed` (MNB00092).
4. Finance leadership — lab intent `deepa.nair` (Director of Finance).
5. **No** — target apps must not create identities; unknowns become uncorrelated for remediation.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “SAP Direct connector” for the production path this CSV simulates.
- [SailPoint Community](https://community.sailpoint.com/) — search “SAP segregation of duties” for finance SoD design patterns.
- [ISACA](https://www.isaca.org/) — search “SAP segregation of duties” for SOX/ITGC framing of finance access.
- [NIST SP 800-53 AC-5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) — separation of duties behind finance vs infrastructure privilege splits.
- [FFIEC IT Examination Handbook — Information Security](https://ithandbook.ffiec.gov/it-booklets/information-security.aspx) — financial application access controls.


## Stretch lab

- Build a notebook table of all active SAP_FI users and mark which also appear in `MNB-AWS-Cloud.csv`.
- Draft the one-sentence SoD control statement you will reuse in Lesson 39.

---

## Summary

- **MNB-SAP-Finance** onboards critical ERP finance access (`SAP_FI`) as its own governed application.
- Active and disabled accounts are preserved as control signal.
- **jordan.reed** is staged for toxic combination work with AWS in the next lesson.

---

**Previous:** [Lesson 11 — Onboard Core Banking](11-onboard-core-banking.md)  
**Next:** [Lesson 13 — Onboard AWS Cloud Admin](13-onboard-aws-cloud.md)
