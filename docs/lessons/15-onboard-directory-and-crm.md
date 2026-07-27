# Lesson 15 — Directory, CRM & Digital Channel Apps

**Level:** Intermediate  
**Track:** Applications  
**Time:** 75–90 min  
**Prereq:** Lesson 14  

**Lab data:**
- `lab-data/apps/MNB-ActiveDirectory.csv` → **MNB-ActiveDirectory** (`ELDAP`)
- `lab-data/apps/MNB-Salesforce-CRM.csv` → **MNB-Salesforce-CRM** (`CRM`)
- `lab-data/apps/MNB-InternetBanking.csv` → **MNB-InternetBanking** (`IBSI`)
- `lab-data/apps/MNB-Ecommerce-Ops.csv` → **MNB-Ecommerce-Ops** (`ECOM`)
- Runtime copies under `~/iiq-lab-data/apps/`

---

## Learning objectives

You will be able to:

- Onboard four Meridian channel/directory applications with consistent Delimited File patterns
- Map entitlements **ELDAP**, **CRM**, **IBSI**, and **ECOM** with correct risk posture
- Demonstrate **kai.nguyen** holding both **IBSI** and **ECOM** (digital SoD seed)
- Keep all four apps non-authoritative (directory is not HR)
- Batch Account Aggregation and verify representative accounts per app

---

## Why this matters

**Business.** Meridian’s identity fabric is more than finance and wires. Directory login (`ELDAP`), commercial CRM, internet banking support (`IBSI`), and ecommerce change ops (`ECOM`) are how staff serve customers and ship digital changes.

**Control / audit.** Digital banking support plus channel promotion (`IBSI` + `ECOM`) is an SoD pair—someone who supports customers and can promote ecommerce changes can abuse both rails. Directory sprawl without an application object leaves orphan AD accounts invisible to certifications.

---

## Concepts

| Application | CSV | Entitlement | Risk | Notes |
| --- | --- | --- | --- | --- |
| `MNB-ActiveDirectory` | `MNB-ActiveDirectory.csv` | `ELDAP` | medium | Broad (~78 accounts); includes disabled |
| `MNB-Salesforce-CRM` | `MNB-Salesforce-CRM.csv` | `CRM` | medium | Includes `sofia.torres` |
| `MNB-InternetBanking` | `MNB-InternetBanking.csv` | `IBSI` | high | Includes `kai.nguyen` |
| `MNB-Ecommerce-Ops` | `MNB-Ecommerce-Ops.csv` | `ECOM` | high | Includes `kai.nguyen` |

```
kai.nguyen (MNB00096)
    ├─ MNB-InternetBanking / IBSI
    └─ MNB-Ecommerce-Ops / ECOM
            │
            ▼
     SoD: IBSI + ECOM (digital concentration)
```

**Directory is still a target.** Even though AD feels “foundational,” **MNB-HR** remains the only identity-creating source. `MNB-ActiveDirectory` correlates onto HR people; it must not invent cubes.

**Batch mindset.** You will create four apps. Use a checklist; do not invent custom schemas per file—the columns match the other platform extracts.

> **Production reality.** Each of these four systems has a real connector, and CSV would be a finding in production:
>
> | Lab app (this lesson) | Production connector | Lesson |
> | --- | --- | --- |
> | `MNB-ActiveDirectory` | Active Directory - Direct (LDAP + IQService) | 56–57 |
> | `MNB-Salesforce-CRM` | Salesforce native (profiles + permission sets) | 71 |
> | `MNB-InternetBanking` | Web Services / SCIM against the platform API | 68–69 |
> | `MNB-Ecommerce-Ops` | Web Services / JDBC depending on the stack | 68, 63 |
>
> The CSVs here teach the batch-onboarding discipline; Part II replaces each with the native path and a retirement plan for the file app.

---

## Before you start

- [ ] IIQ up; `spadmin`
- [ ] All four CSVs present under `~/iiq-lab-data/apps/`
- [ ] Prior platform apps (Core, SAP, AWS, Wire) already done—pattern muscle memory ready
- [ ] Search finds `kai.nguyen`, `sofia.torres`, `helen.ross`
- [ ] Dictionary skim for ELDAP, CRM, IBSI, ECOM

---

## Lab procedure

### Task 1 — Inspect all four extracts

1. Open each CSV; confirm shared header: `userName,email,employeeId,entitlement,accountStatus`.
2. Note approximate sizes: AD large; CRM ~10; IB ~6; ECOM ~6.
3. Find `kai.nguyen` in **both** Internet Banking and Ecommerce files (`IBSI` and `ECOM`, `MNB00096`).
4. Find `sofia.torres` in CRM; confirm AD includes leadership and scripted personas.
5. Notebook table: app name → entitlement → hero user.

**Expected result:** Four files understood; Kai flagged as digital SoD seed.

**If it fails:** Re-copy `lab-data/apps`; verify filenames match exactly.

---

### Task 2 — Create MNB-ActiveDirectory

1. Delimited File app `MNB-ActiveDirectory`.
2. Path: `~/iiq-lab-data/apps/MNB-ActiveDirectory.csv`.
3. Schema: account id `userName`; entitlement `entitlement` → `ELDAP`.
4. **Create identities: OFF.**
5. Owner intent: `helen.ross` or IAM team; temporary `spadmin` OK.
6. Save.

**Expected result:** AD app configured as target, not HR replacement.

---

### Task 3 — Create MNB-Salesforce-CRM

1. Delimited File `MNB-Salesforce-CRM` → `MNB-Salesforce-CRM.csv`.
2. Entitlement → `CRM`.
3. Non-authoritative.
4. Owner intent: commercial banking leadership (e.g. `sanjay.kapoor`) or `spadmin` proxy.
5. Mark CRM requestable in dictionary terms (medium risk; business-requestable with approval).
6. Save.

**Expected result:** CRM app ready; `sofia.torres` will appear after aggregate.

---

### Task 4 — Create MNB-InternetBanking and MNB-Ecommerce-Ops

1. Create `MNB-InternetBanking` → `MNB-InternetBanking.csv` → entitlement `IBSI` (high).
2. Create `MNB-Ecommerce-Ops` → `MNB-Ecommerce-Ops.csv` → entitlement `ECOM` (high).
3. Both non-authoritative; owners: Digital leadership / Technology proxy.
4. Dictionary: IBSI and ECOM **not** birthright; SoD pair documented.
5. Save both.

**Expected result:** Digital channel apps exist as separate control objects.

**If it fails:** Do not combine IB and ECOM into one app for this curriculum—SoD and certs expect separation.

---

### Task 5 — Batch Account Aggregation

1. Create tasks (or one-by-one):
   - `Aggregate MNB-ActiveDirectory`
   - `Aggregate MNB-Salesforce-CRM`
   - `Aggregate MNB-InternetBanking`
   - `Aggregate MNB-Ecommerce-Ops`
2. Run in that order (directory first is a useful ops habit; not a hard dependency).
3. Record counts: AD should be far larger than the digital apps.
4. Confirm no mass identity-creation side effect.

**Expected result:** All four tasks succeed; entitlements ELDAP/CRM/IBSI/ECOM visible on accounts.

**If it fails:** Fix one failing app at a time; continue others (Lesson 16 failure matrix preview).

---

### Task 6 — Verify kai.nguyen digital pair

1. Open `kai.nguyen` cube / app accounts.
2. Confirm `IBSI` on Internet Banking and `ECOM` on Ecommerce Ops (linked or via app lists).
3. Binder note: **Digital SoD seed** for `IBSI,ECOM` matrix line.
4. Open `sofia.torres` → CRM present.
5. Open `helen.ross` → ELDAP on AD (sanity check for directory breadth).

**Expected result:** Kai holds both high-risk digital entitlements; CRM and AD spot-checks pass.

**If it fails:** Re-aggregate the missing digital app; confirm CSV rows for `kai.nguyen`.

---

### Task 7 — Application portfolio checklist

1. Update your notebook portfolio of Meridian apps:

| App | Authoritative? | Key entitlement |
| --- | --- | --- |
| MNB-HR | Yes | (identity source) |
| MNB-IT-Access | No | many |
| MNB-CoreBanking | No | CORE |
| MNB-SAP-Finance | No | SAP_FI |
| MNB-AWS-Cloud | No | AWS_ADMIN |
| MNB-WirePortal | No | WIRE_* |
| MNB-ActiveDirectory | No | ELDAP |
| MNB-Salesforce-CRM | No | CRM |
| MNB-InternetBanking | No | IBSI |
| MNB-Ecommerce-Ops | No | ECOM |

2. Confirm only `MNB-HR` creates identities.

**Expected result:** Complete applications-track inventory before the aggregation strategy lesson.

---

## Acceptance criteria

- [ ] All four apps created with correct CSV paths
- [ ] All non-authoritative; entitlement attributes mapped
- [ ] Four Account Aggregation tasks succeeded
- [ ] `kai.nguyen` verified for IBSI + ECOM
- [ ] Spot-checks: `sofia.torres` CRM; `helen.ross` ELDAP
- [ ] Portfolio table updated in binder

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| AD aggregation slow / large | Expected in lab scale | Wait; still tiny vs prod |
| Kai missing one digital ent | One task failed | Re-run that Aggregate task |
| AD created identities | Authoritative mistaken | Disable; this is severe—clean carefully |
| CRM empty | Wrong file path | Point to Salesforce CSV |
| Name typos (`MNB-AD`) | Inconsistent naming | Rename to curriculum names |

---

## Training binder evidence

1. Screenshots of all four application definitions
2. Four task results (or a single notes table of counts)
3. `kai.nguyen` IBSI + ECOM evidence
4. Portfolio table showing only HR is authoritative
5. SoD matrix line `IBSI,ECOM`

Examiner question: *“Is Active Directory your authoritative identity source?”* → **No. MNB-HR is.**

---

## Knowledge check

1. Name the four applications and their primary entitlements.
2. Why must `MNB-ActiveDirectory` not create identities?
3. Which persona seeds IBSI + ECOM toxic digital access?
4. Is CRM typically requestable relative to AWS_ADMIN?
5. What examiner trap does “AD feels foundational” create?

### Answers

1. ActiveDirectory/ELDAP; Salesforce-CRM/CRM; InternetBanking/IBSI; Ecommerce-Ops/ECOM.
2. HR remains authoritative; AD accounts correlate to people—creating identities from AD duplicates/conflicts with HR truth.
3. `kai.nguyen` (MNB00096).
4. Yes—CRM is medium/business requestable; AWS_ADMIN is critical privileged/non-requestable.
5. Teams wrongly mark directory authoritative and break HR-led joiner/mover/leaver.

---

## Further reading

- Lessons 56–57 (AD Direct), 71 (Salesforce), 68–69 (Web Services/SCIM) — production connectors for each CSV app in this lesson.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search each connector by name.
- [FFIEC IT Handbook — Information Security](https://ithandbook.ffiec.gov/it-booklets/information-security/) — application portfolio and SoD scope.

## Stretch lab

- Create population `MNB-Digital-SoD-Candidates` for identities with both IBSI and ECOM (after correlation).
- Compare AD account count vs HR identity count; note disabled AD rows for leavers (`samir.hassan`).

---

## Summary

- Directory, CRM, and digital channel apps are onboarded as governed targets.
- **kai.nguyen** demonstrates IBSI + ECOM concentration risk.
- Your Meridian application portfolio is complete for the aggregation runbook lesson.

---

**Previous:** [Lesson 14 — Onboard Wire Portal](14-onboard-wire-portal.md)  
**Next:** [Lesson 16 — Multi-App Aggregation Strategy](16-multi-app-aggregation-strategy.md)
