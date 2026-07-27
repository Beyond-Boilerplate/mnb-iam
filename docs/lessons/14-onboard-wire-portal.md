# Lesson 14 — Onboard Wire Portal (Dual Control)

**Level:** Intermediate  
**Track:** Applications  
**Time:** 60–90 min  
**Prereq:** Lesson 13  

**Lab data:**
- Repo: `lab-data/apps/MNB-WirePortal.csv`
- Optional splits: `lab-data/apps/MNB-WirePortal-Initiators.csv`, `MNB-WirePortal-Approvers.csv`
- Runtime: `~/iiq-lab-data/apps/MNB-WirePortal.csv`

---

## Learning objectives

You will be able to:

- Onboard **MNB-WirePortal** governing payment dual-control entitlements **WIRE_INIT** and **WIRE_APPR**
- Identify lab personas **priya.wire** (initiate) and **marcus.approve** (approve)
- Explain why initiate and approve must never be the same person on the same payment rail
- Configure a non-authoritative Delimited File app and Account Aggregation for the portal extract
- Document Payments Operations ownership (`rachel.evans`) and critical requestability rules

---

## Why this matters

**Business.** Wire fraud and fat-finger transfers are existential for a bank. Meridian’s Wire Portal enforces dual control: one role creates instructions (`WIRE_INIT`), another approves (`WIRE_APPR`).

**Control / audit.** Payment examiners ask how initiate vs approve are separated in IAM, not only in the portal UI. If both entitlements live as opaque codes with no application boundary, certifications and SoD policies fail. The SoD matrix line `WIRE_INIT,WIRE_APPR` is Meridian’s primary payment dual-control control.

---

## Concepts

**Dual control in IAM terms.** Two entitlements on one application (or tightly paired apps) that are mutually exclusive for the same identity.

| Entitlement | Meaning | Lab hero |
| --- | --- | --- |
| `WIRE_INIT` | Create wire instructions | `priya.wire` (MNB00090) |
| `WIRE_APPR` | Approve wire instructions | `marcus.approve` (MNB00091) |

Also in extract: managers/ops staff such as `rachel.evans` (WIRE_APPR) — useful as application owner.

```
   priya.wire                    marcus.approve
        │                              │
        ▼                              ▼
   WIRE_INIT  ──dual control──►  WIRE_APPR
        │                              │
        └──────── MNB-WirePortal ──────┘
```

**Single file vs split files.** This lesson uses the combined `MNB-WirePortal.csv` (both entitlements). Split initiator/approver CSVs exist for stretch or alternate connector demos—do not create duplicate apps unless instructed.

Extract size: **10** accounts.

> **Production reality.** An in-house wire portal typically exposes a REST API or SCIM endpoint rather than dropping CSVs. Production Meridian would govern it with the **Web Services connector** (Lesson 68) against the portal's user/role API — the repo even carries a stub OpenAPI spec for it (`lab-data/connectors/webservices/wire-portal-openapi.yaml`) — or **SCIM 2.0** (Lesson 69) if the portal team implements the standard. The dual-control design, ownership, and SoD line you write here carry over verbatim.

---

## How it works

`MNB-WirePortal` encodes **payment dual control**: `WIRE_INIT` and `WIRE_APPR` as distinct critical entitlements under Treasury ownership (`rachel.evans`). Healthy lab design keeps them on separate people.

```text
MNB-WirePortal.csv
        │
        ▼
App MNB-WirePortal (create OFF) → Aggregate
        │
        ├── WIRE_INIT → priya.wire (intent)
        └── WIRE_APPR → marcus.approve (intent)
        │
        ▼
SoD / dual-control narrative + payments certs
```

| Entitlement | Duty | Healthy holder |
| --- | --- | --- |
| `WIRE_INIT` | Create wire instructions | `priya.wire` |
| `WIRE_APPR` | Approve wires | `marcus.approve` |

**Real-life Meridian example.** Combining both on one cube is an exam-grade finding. The platform app makes dual control visible to certifications without tribal knowledge.

## Before you start

- [ ] IIQ up; `spadmin` login
- [ ] `~/iiq-lab-data/apps/MNB-WirePortal.csv` present
- [ ] HR identities exist for `priya.wire`, `marcus.approve`, `rachel.evans`
- [ ] Dictionary entries for WIRE_INIT / WIRE_APPR (critical)
- [ ] SoD matrix skimmed: initiate vs approve rationale

---

## Lab procedure

### Task 1 — Inspect the Wire Portal extract

Dual control only works if INIT and APPR stay separable—verify the extract encodes that split before onboarding.

1. Open `~/iiq-lab-data/apps/MNB-WirePortal.csv`.
2. Build a two-column list: Initiators vs Approvers from the `entitlement` column.
3. Confirm:
   - `priya.wire` → `WIRE_INIT`, active
   - `marcus.approve` → `WIRE_APPR`, active
   - `rachel.evans` → `WIRE_APPR`, active
4. Confirm no single row grants both entitlements (each row is one entitlement). Dual control is enforced across rows/identities, then by policy later.
5. Optional: open the Initiators/Approvers split files and confirm they partition the same population.

**Expected result:** Clear initiate vs approve populations; Priya and Marcus identified as dual-control demo pair.

**If it fails:** Re-copy apps; do not merge entitlements into one row by hand.

---

### Task 2 — Create MNB-WirePortal

1. Applications → Add New → Delimited File.
2. Name: `MNB-WirePortal`.
3. Absolute path to `MNB-WirePortal.csv`; comma; header.
4. Owner: temporary `spadmin`.
5. Save.

**Expected result:** Application `MNB-WirePortal` listed.

**If it fails:** Naming must be exact for later lessons referencing this object.

---

### Task 3 — Schema: multi-value entitlement reality

1. Discover schema.
2. Account identity: `userName`.
3. Entitlement attribute: `entitlement`.
4. Note: some users appear once with one entitlement. If a person ever needs both (they should not for SoD), the inventory dump may show multiple rows—platform extract here is one entitlement per row.
5. Disable identity creation.
6. Save.

**Expected result:** Non-authoritative app; WIRE_* codes will materialize as entitlements.

**If it fails:** If schema discovery creates oddly named attributes, align names to CSV headers manually.

---

### Task 4 — Account Aggregation

1. Create `Aggregate MNB-WirePortal` (Account Aggregation).
2. Run Now. Expect ~**10** accounts.
3. Record task result counts and any warnings.

**Expected result:** Successful aggregation; both WIRE_INIT and WIRE_APPR appear in entitlement inventory for this app.

**If it fails:** Zero accounts → path; missing entitlements → entitlement attribute not set.

---

### Task 5 — Ownership and dictionary

1. Set application owner to `rachel.evans` (Payments Operations Manager) when available.
2. Enrich managed attributes:
   - `WIRE_INIT` → “Wire Portal — Initiate”; critical; requestable only with strict approvals (lab: treat as controlled)
   - `WIRE_APPR` → “Wire Portal — Approve”; critical; tightly controlled / often non-self-requestable
3. Binder narrative:

```text
Dual control: no identity should hold WIRE_INIT and WIRE_APPR together.
Owner: rachel.evans (Payments Ops).
Evidence: MNB-WirePortal aggregation + SoD policy (Lesson 40).
```

**Expected result:** Payment ownership and human-readable entitlement names ready for certs.

---

### Task 6 — Verify priya.wire and marcus.approve

1. Open `priya.wire` → confirm Wire Portal account / `WIRE_INIT` (cube or app account list).
2. Open `marcus.approve` → confirm `WIRE_APPR`.
3. Confirm they are **different people**—dual control is people separation, not only entitlement labels.
4. Spot-check `rachel.evans` as approver + future cert/app owner.

**Expected result:** Initiate and approve demo personas correctly entitled.

**If it fails:** Correlation may still be incomplete—verify on application accounts first.

---

### Task 7 — Dual-control walkthrough note

1. Write a short examiner script:

```text
Q: How does Meridian separate wire create vs approve in IAM?
A: Entitlements WIRE_INIT and WIRE_APPR on MNB-WirePortal; SoD policy
   prevents combination; personas priya.wire vs marcus.approve demonstrate.
```

2. Optional stretch preview: open `MNB-IT-Access` / EmployeeData and note Priya may also hold `ACH_OPS`—cross-rail risk appears in SoD matrix (`ACH_OPS,WIRE_INIT`).

**Expected result:** You can explain dual control without opening the portal UI.

---

## Acceptance criteria

- [ ] **Bank craft exit:** `MNB-WirePortal` matches `config/Application/MNB-Application-WirePortal.xml` (import-verify or UI+export)

- [ ] `MNB-WirePortal` created; non-authoritative; aggregated (~10 accounts)
- [ ] `WIRE_INIT` and `WIRE_APPR` both present
- [ ] `priya.wire` = initiate; `marcus.approve` = approve verified
- [ ] Owner `rachel.evans` (or proxy) documented
- [ ] Dual-control / SoD narrative written for binder

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Only INIT or only APPR | Pointing at a split CSV by mistake | Use combined `MNB-WirePortal.csv` |
| Duplicate apps for wire | Created split apps accidentally | Prefer one app this lesson; document if you keep splits |
| Priya missing | HR not aggregated / wrong file | Fix HR first; re-aggregate Wire |
| Both ents on one cube wrongly | Looking at denormalized IT dump | Distinguish inventory vs Wire Portal app |
| Owner left bank later | Stale owner | Keep owners current (Lesson 10 tip) |

---

## Training binder evidence

1. Application definition + aggregation result
2. Screenshot: `priya.wire` WIRE_INIT
3. Screenshot: `marcus.approve` WIRE_APPR
4. Dictionary entries for both entitlements
5. SoD matrix line for WIRE_INIT vs WIRE_APPR
6. Examiner Q&A script from Task 7

Examiner question: *“Prove initiate and approve are separable entitlements with different people.”*

---

## Knowledge check

1. Which persona initiates wires in the lab? Which approves?
2. Why is a single application with two entitlements acceptable for dual control?
3. Who is the intended Meridian owner of the Wire Portal app?
4. What SoD pair must policy eventually block?
5. Should Wire Portal aggregation create identities for unknown operators?

### Answers

1. Initiate: `priya.wire`. Approve: `marcus.approve`.
2. Dual control is enforced by mutually exclusive entitlements (and later policy), not by requiring two connectors—though some banks split apps for ownership clarity.
3. `rachel.evans` (Payments Operations Manager).
4. `WIRE_INIT` + `WIRE_APPR` on the same identity.
5. No — non-authoritative target only.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “entitlement” and “SOD policy” for encoding dual-control pairs.
- [SailPoint Community](https://community.sailpoint.com/) — search “wire dual control” for payments access patterns.
- [NIST SP 800-53 AC-5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) — separation of duties for critical transaction paths.
- [FFIEC IT Examination Handbook — Information Security](https://ithandbook.ffiec.gov/it-booklets/information-security.aspx) — dual control / funds transfer examiner language.
- [FFIEC — Retail Payment Systems booklet](https://ithandbook.ffiec.gov/it-booklets/retail-payment-systems.aspx) — payments risk context Treasury maps to IAM.


## Stretch lab

- Onboard split apps `MNB-WirePortal-Initiators` and `MNB-WirePortal-Approvers` **or** document why Meridian prefers one app.
- Draft approval chain idea: manager + `rachel.evans` for either entitlement request (Lesson 36 preview).

---

## Summary

- **MNB-WirePortal** governs critical payment dual-control entitlements.
- **priya.wire** / **marcus.approve** demonstrate initiate vs approve separation.
- Ownership and SoD narrative are ready for payment policy deep-dives.

---

**Previous:** [Lesson 13 — Onboard AWS Cloud](13-onboard-aws-cloud.md)  
**Next:** [Lesson 15 — Directory, CRM & Digital](15-onboard-directory-and-crm.md)
