# Lesson 245 — Workgroups, Capabilities, Scopes

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~90 minutes  
**Prereq:** Lessons 206, 226, 244  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 96 / 07

> **Why:** Least privilege inside IIQ matters like on targets. A bank never gives every certifier `SystemAdministrator` — prove reduced privilege; do not assume it.

## What this is

So far you often logged in as `spadmin`. Production day-2 work uses **reduced** IIQ rights:

| Object | Plain English | Meridian example |
| --- | --- | --- |
| **Capability** | Bundle of IIQ rights (what you may *do*) | `Certification Administrator` |
| **Workgroup** | Named group; members **inherit** capabilities | `MNB-WG-Wire-Owners` |
| **Population** | Saved identity filter (classic Lesson 07) | `MNB-Treasury`, `MNB-Active-Employees` |
| **Scope** | Data partition — which identities/objects you may *see* | `MNB-Scope-Treasury` |
| **DynamicScope** | Who sees QuickLinks (Lesson 244) — not the same as Scope | `Self Service` |

Nothing for this drill is pre-built. You will:

1. Create reusable **populations** (07 absorption — light)  
2. Create workgroup **`MNB-WG-Wire-Owners`** with certifier capability only  
3. Add **`priya.wire`** as a member (inherited rights, not a sticky direct grant)  
4. Prove Priya can certify and **cannot** open Global Settings  
5. Attach population/scope so a cert campaign is not “whole bank”  

> **Watch out:** **DynamicScope** (QuickLinks) ≠ **Scope** (data visibility) ≠ **Population** (saved filter). Same word family, three different objects.

## Know these

```text
Create populations MNB-Active-Employees + MNB-Treasury (Advanced Analytics)
  → Create Workgroup MNB-WG-Wire-Owners + Capability Certification Administrator only
  → Add priya.wire as member (no direct SystemAdministrator)
  → Log in as priya.wire → Certifications visible; Global Settings denied
  → Create Scope MNB-Scope-Treasury (or bind population on cert definition)
  → Launch small Targeted Cert as Priya → member set matches Treasury filter
  → Evidence: denied screen + inherited caps + scoped count
```

| Term | Plain English | Meridian example |
| --- | --- | --- |
| **Inherited capability** | Right comes from workgroup membership | Priya via `MNB-WG-Wire-Owners` |
| **Direct capability** | Stuck on the identity even after WG removal | Debugging leftover `SystemAdministrator` |
| **Population** | Named filter over cubes | `departmentName` contains Treasury/Payments |
| **Controlled / assigned Scope** | Limits which identities an admin/certifier sees | Treasury-only view |
| **Least privilege** | Minimum rights for the job | Certify ≠ configure IIQ |

- **Wrong way:** Granting `SystemAdministrator` “just to test” and forgetting to strip it.  
- **Wrong way:** Filtering populations on stock **Type=Employee** (often blank) instead of `inactive` / `employeeType` / `departmentName`.  
- **Wrong way:** Defining a Scope/population and never attaching it to the cert.  
- **Wrong way:** Using Helen / Marcus as the certifier subject when the drill is about Priya’s rights.  
- **Wrong way:** Confusing Lesson 244 DynamicScope fixes with this lesson’s data Scope.

## Intent

- Build populations you can reuse on refresh/cert/report scope.  
- Prove workgroup-inherited certifier rights without full admin.  
- Prove an admin-only URL is denied for Priya.  
- Prove a cert campaign membership is limited by population/scope — not the whole warehouse.

## Before you start

Complete every checkbox. Do not skip into Task 1 until these are true.

- [ ] IIQ up: [http://localhost:8080/identityiq](http://localhost:8080/identityiq) — `spadmin` / `admin`
- [ ] `priya.wire` can log in (`LabUser1!` or seed password)
- [ ] Identities exist from Workday path (Lesson 207+) — Warehouse not empty
- [ ] Spot-check attributes used by populations (open cubes as `spadmin`):

| Identity | Confirm |
| --- | --- |
| `helen.ross` (or similar active worker) | **Is Inactive** = false |
| `priya.wire` | Department / job looks Treasury / Payments / Wire-related |
| A contractor if present | Custom **`employeeType=Contractor`** if you will filter contractors later |

- [ ] Lesson 244 QuickLinks idea understood (Certifications tile may appear after capability grant)
- [ ] Evidence dir:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/245
```

## Do this

### Task 1 — Create population `MNB-Active-Employees` (classic 07)

Populations are **not** under Identity Warehouse. Prefer:

| Path | Steps |
| --- | --- |
| **A** | **Setup → Populations** → New (if menu exists) |
| **B (always works)** | **Intelligence → Advanced Analytics** → Identities → filter → **Save As Population** |

1. Open **Intelligence → Advanced Analytics** → search type **Identities**  
2. **Clear** leftover filters (Type, Is Manager, Software Version, empty rows)  
3. Set **only**: **Is Inactive** = **False**  
4. **Run** — expect a large list (dozens). Empty → an extra filter is still AND’d; clear and retry  
5. **Save As Population** → name exactly `MNB-Active-Employees`  
6. Note approximate member count under evidence

- **Why:** reusable “who is in scope” beats retyping filters under cert deadline pressure.  
- **Expect:** named population saved; count > 0.

> **Watch out:** Stock **Type = Employee** often zeros the result on this estate. Do not add it.

### Task 2 — Create population `MNB-Treasury`

1. Advanced Analytics → Identities → clear filters  
2. Set filters that match Meridian treasury/wire staff on **your** cubes, for example:
   - **Department** / `departmentName` **contains** `Treasury` **or** `Payments` **or** `Wire`  
   - **AND** **Is Inactive** = **False**  
3. **Run** — expect a **small** set that includes `priya.wire` (adjust attribute/value until it does)  
4. **Save As Population** → `MNB-Treasury`  
5. Record member count and the exact filter you used in `populations.txt`

- **Why:** wire/payments certs must not pull every retail teller (classic 07 control story).  
- **Expect:** `priya.wire` is a member; Helen (retail/ops) is usually **not**.

If department attributes are blank: run **Refresh Identity Cube** with promote attributes (Lesson 207/214 pattern), then rebuild the population.

### Task 3 — Create workgroup `MNB-WG-Wire-Owners`

1. **Setup → Groups → Workgroups** (path may read **Setup → Workgroups**) → **New Workgroup** / Create  
2. Set:

| Field | Value |
| --- | --- |
| **Name** | `MNB-WG-Wire-Owners` |
| **Display name** | `MNB Wire Owners` (optional) |
| **Description** | `Reduced-privilege wire/treasury certifiers. Not SystemAdministrator.` |
| **Capabilities** | **`Certification Administrator`** only — do **not** add SystemAdministrator / Full Access / CapabilityAdministrator |

3. **Members** → Add **`priya.wire`**  
4. **Save**  
5. Re-open and confirm: one capability, Priya listed

- **Why:** rights ride membership — removing Priya later removes the certifier right cleanly.  
- **Expect:** workgroup saved with exactly the certifier capability.

> **Tip:** Capability label may appear as `Certification Administrator` or `CertificationAdministrator`. Pick the stock cert-admin capability, not a custom empty one.

### Task 4 — Strip accidental direct admin on Priya

1. **Identities → Identity Warehouse → priya.wire**  
2. Open **Capabilities** (or Rights / assigned capabilities)  
3. If **`SystemAdministrator`** (or Full Access) is assigned **directly**, **remove** it  
4. Confirm she still has certifier rights **via workgroup** (may show as inherited / workgroup-sourced depending on UI)  
5. **Save**

- **Why:** direct grants stack with workgroup grants and survive WG removal — the classic least-privilege leak.  
- **Expect:** no standing `SystemAdministrator` on Priya.

### Task 5 — Prove Priya can certify (positive path)

1. Log out → log in as `priya.wire` / `LabUser1!`  
2. Confirm **Certifications** appears (nav and/or Lesson 244 QuickLink)  
3. Open Certifications — page must load (list may be empty)  
4. If missing: log out/in once; as `spadmin` re-check workgroup membership; optionally **Refresh Identity Cube** for `priya.wire` if capabilities are cube-cached on your build

- **Why:** inherited capability must be usable, not only visible on the workgroup form.  
- **Expect:** Certifications UI reachable as Priya.

### Task 6 — Prove admin screen denied (negative path)

Still as `priya.wire`:

1. Try **Gear → Global Settings** (or **Setup → Global Settings**)  
2. Also try direct URL:

```text
http://localhost:8080/identityiq/system/globalSettings.jsf
```

3. Screenshot the denied / missing-menu / access-denied result → `priya-denied-global-settings.png`

- **Why:** certifier ≠ platform admin — this is the examiner sound bite.  
- **Expect:** access denied or menu not rendered — **not** the full Global Settings editor.

If Global Settings opens fully: return to Task 4 — she still has a direct admin capability.

### Task 7 — Create Scope `MNB-Scope-Treasury` (or document population-only path)

IIQ **Scope** objects partition data for scoped administrators. Builds differ; complete **one** of these paths and record which.

#### Path A — Scope object (preferred when UI exists)

1. As `spadmin`: **Setup → Scopes** (or Debug → **Scope** → New)  
2. **Name:** `MNB-Scope-Treasury`  
3. Bind the scope to Treasury identities — commonly by attaching population **`MNB-Treasury`**, or by defining the same filter the population uses  
4. Assign the scope to workgroup **`MNB-WG-Wire-Owners`** and/or to `priya.wire` (Controlled Scope / assigned scopes — labels vary)  
5. **Save**

#### Path B — Population on certification definition only

If your build has no usable Scope editor:

1. Record in evidence: `Scope UI unavailable — using population MNB-Treasury on cert definition`  
2. Continue — Task 8 still proves limited membership via population

- **Why:** “Priya only certifies Commercial/Treasury” must be an object reference, not a verbal hope.  
- **Expect:** Scope saved **or** honest Path B note.

### Task 8 — Launch a small Targeted Certification scoped to Treasury

1. As `spadmin` (campaign create often needs admin) **or** as Priya if she can create targeted certs:  
   **Certifications → Create New Certification** / Targeted Certification wizard  
2. Set:
   - **Name:** `MNB-Cert-Lab-245-Treasury`  
   - **Certifier:** `priya.wire` (or workgroup `MNB-WG-Wire-Owners` if your wizard allows)  
   - **Population / who is certified:** **`MNB-Treasury`** (not Everyone / Active Employees)  
3. Include a small access set (one application or role — keep it tiny)  
4. **Schedule / Launch** → wait until the cert is active  
5. Log in as `priya.wire` → open the cert  
6. Count identities on the cert  

- **Why:** proves population/scope attachment, not only workgroup capability.  
- **Expect:** identity count ≈ `MNB-Treasury` membership (Task 2), **not** full `MNB-Active-Employees`.

Write under evidence:

```text
Cert name: MNB-Cert-Lab-245-Treasury
Population: MNB-Treasury
Members on cert: ________
MNB-Treasury population count: ________
Scope path used: A (MNB-Scope-Treasury) | B (population only)
```

> **Tip:** If the cert shows the whole bank, the wizard ignored the population — edit the certification definition and set the population again, or recreate.

### Task 9 — Inherited-capability proof screenshot

1. As `spadmin`, open `priya.wire` → Capabilities  
2. Screenshot showing certifier right associated with **`MNB-WG-Wire-Owners`** (inherited), not a random direct grant  
3. Save with the denied-admin screenshot and cert count note

- **Why:** cleanup story for Lesson 249 — inherited rights are removable by WG membership.  
- **Expect:** three artifacts in `~/iiq-lab-evidence/sandbox/245/`.

## If it fails

| Symptom | Fix |
| --- | --- |
| Population save missing | Use Advanced Analytics → Save As Population (path B) |
| Population empty | Clear AND filters; do not use stock Type; refresh cubes so department/inactive exist |
| `priya.wire` not in `MNB-Treasury` | Loosen department contains filter until she matches; document the attribute you used |
| Priya still no Certifications | Membership save; log out/in; strip conflicting caps; Refresh Identity Cube |
| Priya can open Global Settings | Remove direct SystemAdministrator (Task 4) |
| Cert shows entire bank | Population not attached on definition — edit/recreate with `MNB-Treasury` |
| Scope menu missing | Use Path B; still pass via population-limited cert |
| Workgroup capability list empty | Import/enable stock capabilities; pick Certification Administrator from OOTB list |

## You are done when

- [ ] Populations `MNB-Active-Employees` and `MNB-Treasury` exist  
- [ ] Workgroup `MNB-WG-Wire-Owners` exists with **only** certifier-level capability  
- [ ] `priya.wire` is a member; no unjustified direct `SystemAdministrator`  
- [ ] Priya can open Certifications and is **denied** Global Settings  
- [ ] Cert `MNB-Cert-Lab-245-Treasury` membership matches Treasury scope/population  
- [ ] Evidence screenshots + counts saved  

## Control note

- **Control:** Least-privilege certifier model (workgroup-inherited) + reusable population scope  
- **Owner:** IAM Engineering + Access Governance  
- **SLA (lab):** No certifier persona holds `SystemAdministrator` without a written exception  
- **Evidence:** `~/iiq-lab-evidence/sandbox/245/`  
- **Out of scope:** Full multi-host task-server design (Lesson 249 / classic 105)

## Quick check

1. Why prefer workgroup-inherited capabilities? → Removing membership removes the right; direct grants linger  
2. Population vs Scope vs DynamicScope? → Saved filter vs data partition vs QuickLink visibility  
3. Why not filter `Type=Employee` here? → Often blank; use `inactive` / `employeeType` / `departmentName`  
4. What proves least privilege? → Cert UI works **and** Global Settings denied  
5. What proves scoping? → Cert member count ≈ `MNB-Treasury`, not whole warehouse  

## Feedback

Could you recreate Priya’s certifier model from a wiped workgroup list (populations → WG + capability → member → deny admin → Treasury-scoped cert) without this page?

If something failed, note the **task number**, whether the failure was capability vs population vs cert membership count.

## Navigate

- Previous: [Lesson 244](244-quicklinks-live.md)
- Next: [Lesson 246](246-toolkit-apis-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
