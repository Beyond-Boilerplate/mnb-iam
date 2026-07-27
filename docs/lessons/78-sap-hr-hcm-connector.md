# Lesson 78 — SAP HR/HCM Connector

**Level:** Intermediate  
**Track:** Connectors — ERP / HR / Banking  
**Time:** 75–90 min  
**Prereq:** Lesson 77 — Workday HCM; Lesson 12 SAP Finance onboard helpful  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (SAP HR row)
- Repo: `lab-data/apps/MNB-SAP-Finance.csv` (contrast app security extract)
- Repo: `lab-data/connectors/features-string-glossary.md`

---

## Learning objectives

You will be able to:

- Distinguish **SAP HR/HCM** (people) from **SAP Direct** (security/roles) for Meridian
- Create **MNB-SAP-HR** application shell for employee master data patterns
- Map personnel number, org assignment, and employment status into IIQ identity attributes
- Complete lab-without-live-target mock HR infotype-style extract
- Document coexistence with Workday/CSV HR and with SAP security apps

---

## Why this matters

**Business.** Some Meridian entities still run SAP HCM for payroll and org management. IAM needs clean employee attributes even when finance roles live in a different SAP connector.

**Control / audit.** Examiners confuse SAP user security with HR master data. Separate applications prevent certifying the wrong control.

---

## Concepts

**SAP HR/HCM connector.** Focused on HR master / org data (people), not ECC role assignment.

| Connector | Governs | Meridian app |
| --- | --- | --- |
| SAP HR/HCM | Employees / org | `MNB-SAP-HR` |
| SAP Direct | Users / roles / profiles | `MNB-SAP-Direct` (Lesson 79) |
| DelimitedFile finance | Legacy role extract | `MNB-SAP-Finance` |

```
SAP HCM (HR) ----→ MNB-SAP-HR (identity attrs)
SAP ECC security → MNB-SAP-Direct (entitlements)  [next lesson]
```

**Matrix:** SAP HR → SAP HR/HCM; alternate DelimitedFile.

**Lab-without-live-target.** Mock personnel extract + maps; do not enable second authoritative source carelessly.

---

## Before you start

- [ ] IIQ up; Lessons 12 and 77 concepts reviewed
- [ ] `MNB-SAP-Finance.csv` available for contrast only
- [ ] Know `PERNR`-style employee numbers may differ from `MNB#####`—document correlation bridge

---

## Lab procedure

### Task 1 — Separation statement

1. Write: *SAP HR feeds who people are; SAP Direct feeds what they can do in SAP.*
2. Paste into binder as mandatory architecture rule.

**Expected result:** Separation statement.

### Task 2 — Create MNB-SAP-HR

1. Applications → Add New → **SAP HR/HCM** (or equivalent).
2. Name: `MNB-SAP-HR`. Owner: `helen.ross`; HR contact `sofia.torres`.
3. SAP gateway / message server / credentials placeholders.
4. Save shell.

**Expected result:** Application object created.

**If it fails:** Note RFC user requirements; continue mock.

### Task 3 — Attribute & correlation bridge

1. Map SAP personnel number → secondary identity attr `sapPernr`.
2. Map to Meridian `employeeId` via HR bridge table design (document CSV bridge `employeeId,sapPernr`).
3. Map status/employment to inactive flags.
4. Manager pernr → manager resolution plan.

**Expected result:** Bridge design page.

### Task 4 — Mock extract (lab-without-live-target)

1. Create `~/iiq-lab-data/connectors/sap/MNB-SAP-HR-mock.csv` with `sapPernr,employeeId,userName,email,status,orgUnit,managerPernr`.
2. Rows for `sofia.torres`, `samir.hassan`, `amelia.brooks`.
3. Shadow aggregate non-authoritative.

**Expected result:** Mock + Task Result.

### Task 5 — Aggregation task

1. `MNB-SAP-HR-Account-Aggregation` (or identity aggregation—document).
2. Confirm no unintended identity creates if authoritative off.

**Expected result:** Safe aggregation evidence.

### Task 6 — Coexistence matrix

1. Table: Source | Population | Authoritative?
2. Example: Workday corporate employees; SAP HR subsidiary; CSV lab fallback.
3. Mark conflicts as residual risks.

**Expected result:** Coexistence matrix.

### Task 7 — Examiner Q&A

*Show you are not certifying SAP HR as finance roles.* Point to separate apps Lesson 12/79.

**Expected result:** Written distinction answer.

### Task 8 — Residual risk

`RR-SAP-PERNR-01`: PERNR↔employeeId bridge errors cause uncorrelated Workers.

**Expected result:** RR with owner `sofia.torres`.

---


### Task 9 — Binder packaging

Assemble `MNB-SAP-HR-Binder-YYYY-MM-DD` with separation statement, bridge design, mock Task Result, coexistence matrix, examiner answer, and `RR-SAP-PERNR-01`.

**Expected result:** Dated binder index with six artifacts checked off.


## Acceptance criteria

- [ ] HR vs security separation statement written
- [ ] `MNB-SAP-HR` shell + PERNR bridge design
- [ ] Mock extract aggregated (shadow/live)
- [ ] Coexistence matrix completed
- [ ] Examiner distinction answer + RR-SAP-PERNR-01
- [ ] Dated binder index packaged

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Wrong people in finance cert | Using SAP-Finance for HR attrs | Keep apps separate; fix cert scope |
| Uncorrelated cubes | PERNR bridge missing | Load bridge; correlation rule |
| Authoritative clash | SAP HR + Workday both auth | Segment populations or disable one |
| RFC failures | Network/SAP_ALL temptation | Least-privilege RFC user; Shadow path |
| Org unit churn noise | Full agg too frequent | Schedule + delta if supported |

---

## Training binder evidence

- Separation statement
- App + bridge design
- Mock/Task Result
- Coexistence matrix
- Examiner answer + RR

---

## Knowledge check

1. What does `MNB-SAP-HR` govern versus SAP Direct?
2. Why maintain an employeeId↔PERNR bridge?
3. Which alternate does the matrix list for SAP HR?
4. Name the residual risk id for bridge errors.
5. Who is the HR contact proxy?

### Answers

1. People/HR master data vs SAP application security roles.
2. Meridian cubes key on `MNB#####` while SAP keys on PERNR.
3. DelimitedFile.
4. `RR-SAP-PERNR-01`.
5. `sofia.torres`.

---

## Stretch lab

Sketch population selector: `identity.sapPernr != null` for subsidiary-only certs.

---

## Summary

- SAP HR/HCM is people data—not finance role governance.
- Lab-without-live-target mocks and PERNR bridges keep training safe.
- Coexistence with Workday/CSV requires explicit authoritative segmentation.

---

**Previous:** [Lesson 77 — Workday HCM Connector](77-workday-hcm-connector.md)  
**Next:** [Lesson 79 — SAP Direct Security](79-sap-direct-security.md)
