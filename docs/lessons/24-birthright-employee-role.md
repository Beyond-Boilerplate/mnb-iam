# Lesson 24 — Birthright Employee Role

**Level:** Intermediate  
**Track:** Roles  
**Time:** 60–90 minutes  
**Prereq:** Lesson 23 catalog sketch; MNB-ActiveDirectory (or entitlement source containing **ELDAP**) aggregated  

**Lab data:**
- HR identities: `amelia.brooks` (active teller), `samir.hassan` (terminated)
- Entitlement: **ELDAP** (Enterprise Directory)
- Catalog intent: Lesson 23 `MNB-Birthright-Employee` = ELDAP only

---

> **Verify:** Lab lesson — create `MNB-IT-ELDAP` + `MNB-Birthright-Employee` and assign on refresh. Academy **Verify now** checks both Bundles + `amelia.brooks`.

## Learning objectives

You will be able to:

- Navigate **Setup → Roles** and choose the correct **Create New** option (manual **Role**, not mining)
- Build Meridian’s two-tier birthright: IT pack **`MNB-IT-ELDAP`** (ELDAP) + business role **`MNB-Birthright-Employee`** (assignment + Required Role)
- Explain why type **business** shows *“Entitlements section is not supported”* and what to do instead
- Write an assignment rule (Match List) for active employees (`employeeType=Employee`, `inactive=false`)
- Run identity refresh with role assignment enabled and verify birthright on `amelia.brooks`
- Prove terminated / contractor identities do not receive this pack
- Document birthright composition, exclusions, and joiner SLA impact

---

## Why this matters

**Business.** Joiners should be productive on day one without tickets for baseline directory access. When `amelia.brooks` starts as a teller, Meridian’s promise is: HR goes active → refresh assigns birthright → ELDAP lands. Birthright that includes wire or cloud privilege turns that promise into an automatic control failure—every joiner becomes a privileged account factory.

**Control / audit.** Birthright composition is dual-approved (IAM + Risk). Evidence = role definition + assignment criteria + sample identities (positive and negative). Examiners ask: *“What does every employee get automatically, and what is excluded?”* Your answer must name ELDAP and explicitly exclude `WIRE_*`, `AWS_ADMIN`, `SAP_FI`, and `PRIV_BREAK`.

---

## Concepts

### Birthright is normative automation

A **birthright role** is automatically assigned when an identity matches criteria and typically deprovisioned when criteria fail (via refresh / lifecycle). It is normative—“you should have this”—not a detection of what you already hold (Lesson 27).

```
IF identity has MNB-HR account
 AND inactive = false (status = Active)
 AND employeeType = Employee
THEN assign MNB-Birthright-Employee
         └── entitlement ELDAP (Enterprise Directory)
```

| Include | Exclude |
| --- | --- |
| Active Employee | Contractor (`raj.external` and peers) |
| ELDAP only | WIRE_*, AWS_ADMIN, SAP_FI, PRIV_BREAK |
| Tellers, analysts, specialists | Terminated (`inactive=true` / `status=Terminated`, e.g. `samir.hassan`) |

### Why ELDAP alone

Directory login is the shared baseline for employees. Payment initiate, cloud admin, and break-glass are never “everyone needs it on day one.” Over-scoping birthright is how banks accidentally automate privilege. Under-scoping (no birthright at all) floods the service desk and creates shadow access.

### Contractors are a different promise

`raj.external` is a Cloud Platform Engineer contractor with vendor email and `AWS_ADMIN` risk. He must **not** receive `MNB-Birthright-Employee`. Lesson 32 defines a stricter contingent path. If your assignment rule forgets `employeeType=Employee`, every contractor inherits employee baseline—and examiners will find it in population reports.

---

## How it works

Identity refresh is the engine that turns the rule into cube state. Without assign-roles options enabled, the Bundle exists but nobody receives it.

```
MNB-HR aggregation ──► identity attributes (employeeType, inactive/status)
        │
        ▼
Refresh MNB Roles (or Refresh MNB Identities with assign roles ON)
        │
        ├── match rule? ──yes──► Assigned: MNB-Birthright-Employee
        │                              └── plan may grant ELDAP
        └── no match ──► remove / do not assign birthright
```

| Step | IIQ object | Meridian evidence |
| --- | --- | --- |
| Package access | IT Bundle `MNB-IT-ELDAP` → entitlement ELDAP | Entitlements / profile screenshot |
| Assign who | Business Bundle `MNB-Birthright-Employee` → Required Role + Match List | Role Information panel |
| Enforce | Identity Refresh task | Task Result + Amelia Roles tab |
| Negative proof | Terminated / Contractor cubes | Samir without birthright; Raj excluded |

```
MNB-Birthright-Employee  (type = business)
 ├── Assignment Rule (Match List) ── who gets it
 └── Required Roles ──► MNB-IT-ELDAP  (type = it)
                              └── Entitlements ──► ELDAP
```

**Why two objects?** Stock IdentityIQ role types set **business** to `noProfiles` — the **Entitlements** panel is not supported on business roles. Entitlements live on **IT** (or entitlement) roles; business roles point at them via **Required Roles**. If you see *Warning: The 'Entitlements' section is not supported by the selected role type*, you picked **business** and tried to add ELDAP there — ignore Entitlements on that role and use the IT pack instead.

**IIQ terms:** Bundle (role), Required Roles, assignment rule / selector, role detection vs assignment (Lesson 27), provisioning policy (may be stubbed in file lab—still verify **assignment**).

---

## Before you start

- [ ] IIQ at `http://localhost:8080/identityiq` as `spadmin`
- [ ] ELDAP exists as a managed entitlement (dictionary Lesson 10; AD or IT inventory)
- [ ] `amelia.brooks` cube exists from HR (`MNB00097`, TEL01, active)
- [ ] Catalog v0 lists birthright as ELDAP-only
- [ ] Backup note: role XML export path if your lab exports bundles

### Where to create roles (IIQ 8.x lab UI)

Roles are **not** under Identities. Use:

| Path | Steps |
| --- | --- |
| **Primary** | Top nav **Setup → Roles** → **Role Viewer** tab |
| **Create** | **Add** / **Create New** / **New Role** (wording varies by build) |

#### Create New — pick the right option

The create menu usually offers **four** choices. For this lesson (and Lessons 25–28), use only the first:

| Option | What it does | This lesson |
| --- | --- | --- |
| **Role** | Opens the **Role Editor** so you define name, type, entitlements, and assignment rule by hand | **Select this** |
| **Business Role Mining** | Auto-generates business roles from identity attributes (department, job, …) | Skip — mined roles start disabled and use mining criteria you do not control yet |
| **IT Role Mining** | Auto-generates IT roles from entitlement patterns across a population | Skip — Lesson 26 packaging is deliberate, not mined |
| **Entitlement Analysis** | Analyzes entitlement combinations; can seed profiles later | Skip — you already know the single entitlement (ELDAP) |

Wrong click = you land in a mining wizard instead of the Role Editor. If that happens, cancel / close and choose **Role**.

#### Two roles — cheat sheet (create IT first)

| | **IT role** (Task 2) | **Business role** (Tasks 3–4) |
| --- | --- | --- |
| **Name** | `MNB-IT-ELDAP` | `MNB-Birthright-Employee` |
| **Type** | **it** | **business** |
| **Owner** | `spadmin` | `spadmin` |
| **Disabled** | Unchecked | Unchecked |
| **Entitlements** | **ELDAP** only (Simple or Advanced View) | *Not supported* — skip this panel |
| **Required Roles** | Leave empty | **`MNB-IT-ELDAP`** |
| **Assignment Rule** | Leave empty (IT roles are not auto-assigned this way) | **Match List** (Task 4) |
| **Requestable** | Off | Off |

**Ignore this warning on the business role:** *The 'Entitlements' section is not supported by the selected role type.* That is expected for type **business**. Do not switch the business role to **it** just to clear the warning — keep assignment on **business** and entitlements on **it**.

### Filter rules for the assignment Match List (read before Task 4)

| Do | Do not |
| --- | --- |
| Match custom **`employeeType` = `Employee`** | Use stock **Type = Employee** (usually blank in this lab — Lesson 05 / 07) |
| Require active: **`inactive` = false** / Is Inactive = False | Rely on display status alone without checking the cube |
| Keep the rule short (2 criteria) | Add blank Match List rows that filter everyone out |
| Exclude contractors by requiring Employee | Forget `employeeType` and birthright every human |

---

## Lab procedure

### Task 1 — Confirm ELDAP entitlement object

Birthright can only grant what exists as a managed entitlement. Confirm the building block before the Bundle.

1. Open **Applications → Entitlement Catalog** (or **Applications →** the AD / directory app → Entitlements / Accounts).
2. Search **ELDAP**. Display name should resemble “Enterprise Directory”.
3. Note the owning application (typically `MNB-ActiveDirectory` or your directory app).
4. Confirm it is medium-risk in the dictionary sense—birthright-worthy, not critical payment privilege.

**Expected result:** ELDAP located; you know which application owns it.

**If it fails:** Aggregate AD/IT inventory; promote group/entitlement; apply dictionary display name (Lesson 10).

### Task 2 — Create IT pack `MNB-IT-ELDAP` (entitlements live here)

Composition is the control. One extra critical entitlement here is a Sev-1 design defect. In stock IIQ, **only IT roles** accept the Entitlements panel—create that pack first.

1. Top nav: **Setup → Roles** → **Role Viewer** tab.
2. **Add** / **Create New** / **New Role** → choose **Role** (not mining).
3. In the Role Editor, set:
   - **Name:** `MNB-IT-ELDAP`
   - **Display Name:** `MNB-IT-ELDAP` (or “Meridian IT — Enterprise Directory”)
   - **Type:** **it**  ← required so Entitlements is supported
   - **Owner:** `spadmin`
   - **Description:** `IT pack: Enterprise Directory (ELDAP) only. Required by employee birthright.`
4. Leave **Disabled** unchecked. Leave Assignment Rule empty.
5. Scroll to **Entitlements**:
   - Click **Add** (opens the entitlement / profile editor).
   - Prefer **Simple View**. If Simple View is empty or awkward, switch to **Advanced View** and build a filter for the ELDAP managed attribute on the directory application.
   - **Application:** the app that owns ELDAP (from Task 1).
   - Select / add entitlement **ELDAP** only.
   - Submit / OK the profile so you return to the Role Editor.
6. Confirm the Entitlements list shows **only ELDAP** (no `WIRE_INIT`, `AWS_ADMIN`, `CRM`).
7. **Submit** the IT role.

**Expected result:** `MNB-IT-ELDAP` exists as type **it** with a single entitlement profile for ELDAP. No Entitlements warning.

**If it fails:** Still see *Entitlements section is not supported* → Type is still **business**; change Type to **it** and re-add. Wrong application → pick the directory app from Task 1. Advanced View needed → Application + attribute/value for ELDAP, then Add Filter / Save.

### Task 3 — Create business role `MNB-Birthright-Employee` + Required Role

This name is permanent for certifications and reports. The business role answers *who*; the IT role answers *what access*.

1. **Setup → Roles** → **Create New → Role** again (manual **Role**).
2. Set:
   - **Name:** `MNB-Birthright-Employee`
   - **Display Name:** `MNB-Birthright-Employee` (or “Meridian Birthright — Employee”)
   - **Type:** **business**
   - **Owner:** `spadmin`
   - **Description:** `Baseline directory access for active Meridian employees. No payment or cloud privilege.`
3. Leave **Disabled** unchecked. If **Requestable** / **Available in Access Request** appears, leave it **off**.
4. **Ignore** the Entitlements panel / warning on this role — do **not** try to Add ELDAP here.
5. In **Required Roles**, click **Modify Required Roles** (or equivalent):
   - Search / select **`MNB-IT-ELDAP`**
   - **Add** → **Save**
6. Do **not** Submit yet if you can still reach Assignment Rule on the same screen — continue to Task 4. Otherwise Submit now and re-open the role for Task 4.

**Expected result:** Business role exists; Required Roles lists `MNB-IT-ELDAP` only. Entitlements warning (if shown) is expected and ignored.

**If it fails:** Cannot find `MNB-IT-ELDAP` → finish Task 2 and ensure it was Submitted. Accidentally put ELDAP on the business role → remove; keep Required Role link only.

### Task 4 — Assignment rule for active employees

The rule is the difference between “every human” and “active employees only.” **Assignment Rule** exists on **business** roles; that is what refresh evaluates.

1. Open `MNB-Birthright-Employee` in the Role Editor (re-open from Role Viewer if needed).
2. Find **Assignment Rule**.
3. Set the rule type to **Match List** (not Filter / Script / Rule / Population unless Match List is unavailable).
4. Add identity criteria (labels vary slightly):

   | Attribute | Operator | Value |
   | --- | --- | --- |
   | `employeeType` | equals | `Employee` |
   | `inactive` (or **Is Inactive**) | equals | `false` / **False** |

5. Optional hardening: add application account on `MNB-HR` present (Match List → Application attribute) if your lab UI makes that easy.
6. Do **not** add a criterion on stock **Type** — that field is usually blank (Lesson 07 trap).
7. Confirm **Required Roles** still lists `MNB-IT-ELDAP`.
8. **Submit** the role (plain Submit is fine for the academy).
9. In Role Viewer, click the role and confirm Role Information shows the Match List summary and Required Role `MNB-IT-ELDAP`.
10. Binder note (plain English + pseudo-logic):

```
Assign MNB-Birthright-Employee when:
  employeeType == "Employee"
  AND inactive == false
Required access: MNB-IT-ELDAP → ELDAP only
Never: Contractor, Terminated, privileged entitlements in the IT pack.
```

**Expected result:** Role saved, enabled; Match List limits to active Employees; Raj’s `employeeType=Contractor` would not match.

**If it fails:** Match List empty after save → re-edit and Submit again. Zero matches later → you used stock Type or left a blank row. If only Filter/Script is available, encode the same two conditions—keep logic identical.

### Task 5 — Refresh with role assignment

Creating the Bundle does nothing until refresh evaluates assignment rules.

1. Top nav: **Setup → Tasks** (or **Gear → Tasks** if that is where your build lists them).
2. Open **`Refresh MNB Roles`** if you created the split refresh tasks (Lessons 06 / 16b).  
   Otherwise open **`Refresh MNB Identities`** or create **New Task → Identity Refresh**.
3. Enable the options that assign roles (wording varies; enable all that apply):
   - **Refresh assigned, detected roles and promote additional entitlements**
   - **Provision assigned roles** (if present — needed when connectors can grant ELDAP)
4. Optional: filter / population to a small set that includes `amelia.brooks` if a full refresh is slow.
5. **Save**, then **Run Now**. Wait for Success on the Task Result.

**Expected result:** Task completes; result may mention role assignment activity.

**If it fails:** Role still Disabled → re-open role, clear Disabled, Submit, re-run. Options unchecked → edit task arguments. Filter excluding tellers → widen scope.

### Task 6 — Positive verify: `amelia.brooks`

1. Top nav: **Identities → Identity Warehouse** (or Identities search).
2. Search `amelia.brooks` or `MNB00097` → open the cube.
3. Confirm Attributes: active Employee teller (`employeeType=Employee`, inactive false, JobCode TEL01).
4. Open the **Roles** tab.
5. Confirm **`MNB-Birthright-Employee`** appears under **Assigned** roles (not only Detected — Lesson 27 explains the difference).

**Expected result:** Assigned birthright role present on Amelia.

**If it fails:** Attributes wrong → fix Identity Mappings / re-aggregate HR / `Refresh MNB Attributes`, then re-run Task 5. Rule wrong → Task 4. Role Disabled → enable and refresh again.

### Task 7 — Negative verify: terminated / non-employee

Positive proof without negative proof fails exams—examiners sample leavers and contractors.

1. Open `samir.hassan` (`MNB00094`) → **Roles** tab.
2. Confirm birthright is **not** assigned (or is pending removal if it was assigned before termination).
3. Open `raj.external` (`MNB00093`) → confirm **no** `MNB-Birthright-Employee`.
4. Annotate screenshots: “terminated excluded” / “contractor excluded.”

**Expected result:** Terminated and contractor personas lack employee birthright assignment.

**If it fails:** Rule missing `employeeType=Employee` or active check → tighten Task 4; ensure status mapping uses HR authoritative attributes (Lesson 22).

### Task 8 — Birthright control document

1. Write `MNB-Ctrl-Birthright-Employee` including:
   - UI path used: Setup → Roles → Create New → **Role** (manual), twice (IT then business)
   - Composition: `MNB-Birthright-Employee` (business) → Required → `MNB-IT-ELDAP` → ELDAP
   - Inclusion: active Employee (`employeeType` + inactive)
   - Exclusions: contractors, privileged ents, payment ents
   - Joiner SLA: identity + birthright within same refresh cycle after HR active (target ≤ 1 hour in production pattern)

**Expected result:** One-page control doc suitable for exam binder.

---

## Acceptance criteria

- [ ] **Bank craft exit:** Birthright role works in IIQ; optional export to `config/Bundle/MNB-Bundle-Birthright-Employee.xml`

- [ ] Created via **Setup → Roles → Create New → Role** (not mining)
- [ ] `MNB-IT-ELDAP` exists as type **it** with ELDAP only
- [ ] `MNB-Birthright-Employee` exists as type **business** with Required Role → `MNB-IT-ELDAP` (not direct Entitlements)
- [ ] Assignment Match List limits to active Employees (`employeeType`, not stock Type)
- [ ] `amelia.brooks` shows **assigned** birthright after refresh
- [ ] Terminated and contractor examples do not keep birthright intent
- [ ] Control document completed with exclusions (contractors named)

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Landed in mining wizard | Chose Business/IT Role Mining | Cancel; **Create New → Role** |
| *Entitlements section is not supported* | Type = **business** (expected) | Put ELDAP on **`MNB-IT-ELDAP`** (type **it**); link via Required Roles |
| Role created but never assigned | Refresh without assign option | Enable refresh assigned / provision assigned roles |
| Everyone gets birthright including contractors | Rule too broad or used stock Type | Match List: `employeeType=Employee` |
| Amelia missing role | Inactive flag / wrong type / role Disabled / missing Required Role | Fix HR attrs; enable role; confirm Required → `MNB-IT-ELDAP`; refresh |
| Simple View empty for ELDAP | App/entitlement not promoted | Use **Advanced View**, or re-aggregate / promote ManagedAttribute (Lesson 10) |
| Provisioning errors for ELDAP | No connector provisioning in file lab | Document as assignment-only lab; still verify assignment |
| Birthright contains extras | Editing mistake on IT pack | Fix `MNB-IT-ELDAP`; re-approve composition |

---

## Training binder evidence

- Screenshot: **Setup → Roles** Create New menu (showing you picked **Role**)
- Screenshot: `MNB-IT-ELDAP` Entitlements (ELDAP only) — Simple or Advanced View
- Screenshot: `MNB-Birthright-Employee` Required Roles → `MNB-IT-ELDAP` + Assignment Match List
- Screenshot: `amelia.brooks` Roles tab with birthright Assigned
- Screenshot: `samir.hassan` / `raj.external` without birthright (annotated)
- Control doc `MNB-Ctrl-Birthright-Employee`

**Control owner:** IAM Engineering  
**Approver:** Risk (composition)  
**SLA:** Birthright assignment same cycle as HR active for joiners

---

## Knowledge check

1. From **Setup → Roles → Create New**, which option do you pick for this lesson—and which three do you skip?
2. Why does type **business** warn that Entitlements is not supported—and where do you put ELDAP instead?
3. Are contractors included in this role?
4. Which Match List attribute excludes `raj.external`—stock **Type** or **`employeeType`**?
5. Should users request birthright from the catalog?
6. Why is `amelia.brooks` a good positive test?

### Answers

1. Pick **Role** (manual Role Editor). Skip **Business Role Mining**, **IT Role Mining**, and **Entitlement Analysis**.
2. Stock **business** roles have `noProfiles`—Entitlements belong on type **it** (`MNB-IT-ELDAP`); the business role links it via **Required Roles**.
3. No—`employeeType=Employee` only; contractors need a tighter separate pack (Lesson 32).
4. **`employeeType`** — stock Type is usually blank in this lab.
5. No—automatic only; not requestable.
6. She is an active Employee teller with ELDAP-appropriate baseline and no treasury privilege expectation.

---

## Further reading

- [SailPoint IdentityIQ — Role Modeling](https://documentation.sailpoint.com/identityiq/help/roles_groups_and_populations/roles/role_modeling/index.html) — **Setup → Roles**, Role Viewer, and Role Editor fields.
- [SailPoint IdentityIQ — Role Mining](https://documentation.sailpoint.com/identityiq/help/roles_groups_and_populations/roles/role_modeling/role_mining.html) — why Business/IT Role Mining is a different workflow from manual **Role**.
- [SailPoint Community](https://community.sailpoint.com/) — search “assignment rule Match List” for version-specific selector patterns.
- [NIST SP 800-53 AC-2](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — account management; birthright is automated account/entitlement assignment with defined population.
- [NIST SP 800-53 AC-6](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — least privilege; the reason birthright stays ELDAP-only.
- [CIS Controls v8 — Control 5 & 6](https://www.cisecurity.org/controls) — account and access control management baselines for joiner automation.

---

## Stretch lab

- Create `MNB-Birthright-Contractor` with ELDAP only **or** a time-boxed directory group; exclude all critical ents; assignment `employeeType=Contractor` AND active. Same UI path: **Create New → Role** (still not mining).
- Add audit note: any birthright composition change requires change ticket + Risk approval.
- Compare Amelia vs `nina.joiner` after Lesson 29—both tellers should converge on same birthright.

---

## Summary

- Create under **Setup → Roles → Create New → Role**; never start with mining for this control.
- Two-tier: **IT** holds ELDAP (`MNB-IT-ELDAP`); **business** holds Match List + Required Role (`MNB-Birthright-Employee`). The Entitlements warning on business is expected.
- `amelia.brooks` validates positive assignment; terminated and contractor identities validate exclusion.

---

**Previous:** [Lesson 23 — Role Model Introduction](23-role-model-intro.md)  
**Next:** [Lesson 25 — Department & Job-Based Roles](25-dept-job-roles.md)
