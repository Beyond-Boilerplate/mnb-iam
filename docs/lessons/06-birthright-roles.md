# Lesson 06 — Birthright Roles for Bankers

**Level:** Intermediate  
**Prereq:** Lesson 05  
**Meridian story:** New retail staff should automatically get baseline digital access. Privileged finance access must never be birthright.

---

## Story

Birthright (business) roles answer: “Because of who you are at Meridian, what access do you always need?”

Examples:

| Role | Assignment idea | Entitlements (lab) |
| --- | --- | --- |
| `MNB-Birthright-Employee` | All active employees | `ELDAP` |
| `MNB-Role-Developer` | Job title / dept suggests engineering | `ODS`, `DWRP` |
| `MNB-Role-Operations` | Operations population | `Ecom` |
| `MNB-Role-CloudAdmin` | **Not** birthright — request only | `AWS` |

---

## How it works

Roles (Bundles) package entitlements. Assignment can be:

- **Assignment rules** (identity attribute matches)
- **Birthright** flags / Rapid Setup patterns
- Manual / requestable roles (Lesson 08)

After role changes, **Identity Refresh** must run (with role options enabled) so IIQ detects who should gain/lose access.

---

## Lesson goals

- [ ] Create at least two IT/business roles with entitlements from `MNB-IT-Access`
- [ ] Create one birthright-style assignment for baseline access
- [ ] Prove a user receives the role after refresh
- [ ] Explicitly keep `AWS` / `SAP` out of birthright

---

## Tasks

### Task 1 — Inventory entitlements in IIQ

1. Open `MNB-IT-Access` entitlements / groups.  
2. Confirm values like `ELDAP`, `ODS`, `AWS` exist.  
3. Pick owners (`spadmin` for lab).

### Task 2 — Create baseline role

1. Create role `MNB-Birthright-Employee`.  
2. Add entitlement `ELDAP` (if present; otherwise choose the safest common entitlement you have).  
3. Make it assignable by rule: e.g. identity has `MNB-HR` account AND status active (however you modeled status).  
4. Mark as birthright / non-requestable if options exist.  
5. Save.

### Task 3 — Create a job-based role

1. Create `MNB-Role-Developer`.  
2. Add `ODS` (+ `DWRP` if available).  
3. Assignment rule: `jobTitle` contains `Developer` **or** department/job codes you choose from HR.  
4. Save.

### Task 4 — Refresh and verify

1. Run `Refresh MNB Identities` with role detection/assignment enabled.  
2. Open a developer identity from `EmployeeData.txt`.  
3. Confirm assigned/detected roles and required entitlements show as needed/detected.

### Task 5 — Negative test

1. Open a user who should **not** be a cloud admin.  
2. Confirm they do **not** have an `AWS` birthright role.  
3. Document that `AWS` will be requestable in Lesson 08.

---

## Tips & tricks

- Start with **few roles**. Role explosion is a classic IGA failure mode.  
- Name roles with `MNB-` prefix and a clear purpose.  
- If nobody gets the role: assignment rule is wrong, refresh options off, or entitlement names don’t match.  
- Detected vs assigned roles: learn the difference in the identity UI tabs.

---

## Checkpoint

1. What is birthright access?  
2. Why must privileged bank access be requestable rather than automatic?  
3. Which task applies role assignment changes?

---

## Stretch

Model an SoD-aware design note: “Developer role must never include payment approval entitlements.” You will encode SoD in Lesson 09.

**Next:** [Lesson 07 — Joiner / Mover / Leaver](07-joiner-mover-leaver.md)
