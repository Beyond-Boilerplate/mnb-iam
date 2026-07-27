# Lesson 79 — SAP Direct Security Connector

**Level:** Intermediate  
**Track:** Connectors — ERP / HR / Banking  
**Time:** 75–90 min  
**Prereq:** Lesson 78 — SAP HR/HCM; Lesson 12 SAP Finance CSV  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (SAP ECC security row)
- Repo: `lab-data/apps/MNB-SAP-Finance.csv`
- Repo: `lab-data/connectors/features-string-glossary.md`

---

## Learning objectives

You will be able to:

- Configure **MNB-SAP-Direct** for SAP user and role/profile aggregation
- Map SAP roles (e.g., finance, basis) to IIQ entitlements with critical risk tiers
- Contrast native SAP Direct vs legacy `MNB-SAP-Finance` DelimitedFile
- Complete lab-without-live-target role inventory and SoD touchpoints (design only)
- Define Account Aggregation and provisioning feature expectations for role assign/remove

---

## Why this matters

**Business.** SAP roles control posting, configuration, and basis. Meridian finance SoD depends on accurate role inventory—not a monthly spreadsheet.

**Control / audit.** Examiners test whether toxic SAP role combinations are detectable. Native aggregation feeds SoD engines; stale CSV fails the narrative.

---

## Concepts

**SAP Direct connector.** Connects to SAP ABAP systems for users and authorization roles/profiles (security), not HR infotypes.

```
MNB-SAP-Direct
        │
        ▼
 SAP RFC / Direct
        │
        ├── Aggregate users + roles
        └── Provision role assign/remove / lock user (per features)
```

| Entitlement example | Risk |
| --- | --- |
| `SAP_FI_POST` | high |
| `SAP_FI_APPROVE` | high |
| `SAP_BASIS_ADMIN` | critical |
| `SAP_DISPLAY_ONLY` | low |

**Matrix:** SAP ECC security → SAP - Direct; alternate SAP HR/HCM (wrong for security—use Direct).

**Lab-without-live-target.** Role dictionary + mock user-role CSV + upgrade plan from `MNB-SAP-Finance`.

---

## Before you start

- [ ] IIQ up; `MNB-SAP-Finance.csv` inspected
- [ ] Lesson 39–40 SoD concepts remembered
- [ ] No SAP_ALL in lab promises without controls

---

## Lab procedure

### Task 1 — CSV contrast

1. Open `lab-data/apps/MNB-SAP-Finance.csv` (or `~/iiq-lab-data/apps/...`).
2. List entitlements present.
3. Write why Direct is preferred for ongoing governance.

**Expected result:** Contrast notes.

### Task 2 — Create MNB-SAP-Direct

1. Applications → Add New → **SAP** / **SAP Direct**.
2. Name: `MNB-SAP-Direct`. Owner: `helen.ross`; SAP security contact `samir.hassan`.
3. System id / client / RFC user placeholders.
4. Save shell.

**Expected result:** Application object.

**If it fails:** Document RFC auth objects needed; continue mock.

### Task 3 — Role dictionary

1. Define Meridian roles: `SAP_FI_POST`, `SAP_FI_APPROVE`, `SAP_BASIS_ADMIN`, `SAP_DISPLAY_ONLY`, `SAP_SECURITY_ADMIN`.
2. Mark dual-control pairs for later SoD: POST vs APPROVE.
3. Align naming with prior finance CSV where possible.

**Expected result:** Dictionary table with risk + SoD pair flag.

### Task 4 — Mock inventory (lab-without-live-target)

1. Create `~/iiq-lab-data/connectors/sap/MNB-SAP-Direct-mock.csv` with `sapUser,email,employeeId,roles,locked`.
2. Include `amelia.brooks` (FI), `marcus.approve` (approve), `samir.hassan` (basis)—ensure POST and APPROVE not on same person for clean example; add toxic row `toxic.user` for teaching only.
3. Shadow **Account Aggregation**.

**Expected result:** Aggregation shows clean + toxic examples.

### Task 5 — Aggregation task

1. `MNB-SAP-Direct-Account-Aggregation`
2. Compare role counts vs CSV app.
3. Plan CSV retirement criteria.

**Expected result:** Task Result + retirement criteria list.

### Task 6 — Provisioning expectations

1. Using glossary, note PROVISIONING / ENABLE (lock) features to confirm in registry.
2. Storyboard: remove `SAP_FI_POST` from leaver; lock SAP user.
3. Evidence chain identical to Lesson 47 playbook.

**Expected result:** Provisioning/leaver storyboard.

### Task 7 — SoD design touchpoint

1. Draft policy name `MNB-SOD-SAP-FI-POST-APPROVE` (do not activate unless instructed).
2. Owner `helen.ross`; severity high.

**Expected result:** Draft policy card.

### Task 8 — Examiner drill

*Show toxic SAP access detection path.* Answer: Direct agg → entitlement on cube → SoD policy → violation work item.

**Expected result:** Path written end-to-end.

---

## Acceptance criteria

- [ ] CSV vs Direct contrast documented
- [ ] `MNB-SAP-Direct` shell + role dictionary with SoD pair
- [ ] Mock aggregation includes clean and toxic examples
- [ ] Provisioning/leaver storyboard complete
- [ ] Draft SoD policy card + examiner path written

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Roles missing composites | Only single roles aggregated | Include composite roles if required by design |
| RFC user locked | Failed logins | Coordinate with BASIS; Shadow path |
| Toxic not detected | SoD not built/active | Design card only until Lesson 39 patterns applied |
| CSV still certified | Campaign scope wrong | Repoint certs to `MNB-SAP-Direct` |
| User lock not working | ENABLE feature absent | Confirm featuresString; use role remove + manual lock RR |

---

## Training binder evidence

- Contrast notes
- App config redacted
- Dictionary + mock Task Result
- Leaver storyboard
- SoD draft + examiner path

---

## Knowledge check

1. What Meridian app name is used for SAP security roles?
2. Which two roles form the dual-control SoD pair in this lab?
3. Who is the SAP security contact?
4. What is the examiner detection path at a high level?
5. Why is SAP HR the wrong connector for ECC roles?

### Answers

1. `MNB-SAP-Direct`.
2. `SAP_FI_POST` vs `SAP_FI_APPROVE`.
3. `samir.hassan`.
4. Aggregate roles → cube entitlements → SoD policy → violation.
5. HR/HCM governs people data, not ABAP security roles.

---

## Stretch lab

Map `SAP_BASIS_ADMIN` into privileged access role packaging (Lesson 28) with mandatory manager + security approval.

---

## Summary

- `MNB-SAP-Direct` is Meridian’s SAP ECC security governance connector.
- Lab-without-live-target role mocks still teach SoD and leaver evidence design.
- Retire finance CSV after Direct aggregation proves complete.

---

**Previous:** [Lesson 78 — SAP HR/HCM Connector](78-sap-hr-hcm-connector.md)  
**Next:** [Lesson 80 — PeopleSoft HCM Connector](80-peoplesoft-hcm-connector.md)
