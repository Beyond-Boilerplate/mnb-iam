# Lesson 05 — HR Schema & Identity Attribute Design

| Field | Value |
| --- | --- |
| **Level** | Beginner |
| **Track** | Foundations |
| **Time** | 60–75 minutes |
| **Prereq** | Lesson 04 (`MNB-HR` aggregated; cubes exist) |
| **Lab data** | `~/iiq-lab-data/HRApplications.txt`; reference `departments.csv`, `job-codes.csv` |

## Learning objectives

You will be able to:

- Decide which bank HR fields belong on the Identity vs only on the Link (account)
- Map HR schema attributes so identity attributes populate after **`Refresh MNB Attributes`**
- Name the Identity Refresh task that must run after HR aggregation to promote Link → Identity attributes
- Validate manager linkage via `managersAssociateID` for a wire specialist toward Payments leadership
- Distinguish terminated (`inactive=true`) from leave-of-absence (`exceptions=LOA`)
- Publish a short Meridian identity attribute dictionary for roles/SoD/JML

## Why this matters

Attribute design decides what roles, lifecycle events, and certifications can see. If `departmentName` / `JobCode` live only on the account link, population rules and birthright roles silently miss people—control gaps with no red error banner. Real bank extracts are wide (50+ columns); promotion must be deliberate.

**Control / audit:** Examiners ask how manager certifications know who reports to whom, and how leavers are distinguished from leave-of-absence. Your attribute dictionary is the design record; the cube is the runtime proof. Use [`hr-column-map.md`](../../lab-data/reference/hr-column-map.md).

## Concepts

| Layer | Holds | Example |
| --- | --- | --- |
| **Account (Link)** | Raw connector attributes | Full bank HRIS row as aggregated |
| **Identity** | Promoted person attributes | Used by roles, policies, certs, selectors |

Promote fields that drive governance (bank column → identity use):

| Identity attribute | Source column | Used by |
| --- | --- | --- |
| email | email | Notifications, correlation |
| manager | managersAssociateID → identity | Certs, approvals |
| departmentName / division | departmentName, division | Roles, populations |
| JobCode | JobCode | Roles |
| inactive / status | inactive, status, statusFlag | Leaver controls |
| employeeType | employeeType / userType | Contractor SLAs |
| exceptions | exceptions (`LOA`) | Temporary freeze |
| location | location | Locational scopes |

```text
  HR account attributes (on Link after Aggregate MNB-HR)
        |  schema mapping / identity attribute assignment
        v
  Refresh MNB Attributes  (Identity Refresh — promote attrs from accounts)
        |
        v
  Identity attributes  -->  roles / populations / JML / cert display
```

**Codes beat display strings:** Rule on `JobCode` / `costCenter`, not free-text `title`. Display titles change; codes stay stable.

**Pipeline rule:** Mapping alone does not finish the job. After you save maps (and re-aggregate if required), you must run an **Identity Refresh** with attribute promotion—Meridian’s purpose-built task is `Refresh MNB Attributes` (created in Lesson 06). Aggregation writes the HR Link; refresh promotes selected fields onto the Identity.

**Termination vs leave:**

| Signal | Meaning | Control intent |
| --- | --- | --- |
| `inactive=true` / `status=Terminated` | Employment ended | Disable / remove access (leaver) |
| `exceptions=LOA` (still Active) | Still employed, temporarily away | Freeze / reduce access; retain identity |

## How it works

Account Aggregation stores raw connector attributes on the **Link**. Identity attribute maps (or rules) **promote** selected fields onto the Identity so roles, populations, and certifications can filter on person-level truth—not buried account XML.

```text
MNB-HR Link attributes (userId, managersAssociateID, departmentName, JobCode, …)
        │
        ▼
Identity attribute assignment / maps (saved on application / identity attrs)
        │
        ▼
Aggregate MNB-HR (if schema change requires it)
        │
        ▼
Refresh MNB Attributes  ← promotes Link fields onto Identity
Refresh MNB Managers    ← resolves managersAssociateID → manager Identity (Lesson 06)
        │
        ▼
Selectors / roles / JML / cert display consume Identity attrs
```

| Field pattern | Promote to Identity? | Meridian reason |
| --- | --- | --- |
| `departmentName`, `JobCode`, `costCenter` | Yes | Role & population filters |
| `employeeType`, `exceptions`, `inactive` / `status` | Yes | Lifecycle & contractor SLAs |
| Transient connector noise (`fax`, empty phones, …) | No | Keep Link-only |

**Real-life Meridian example.** `sofia.torres` has `exceptions=LOA` on HR. Until that flag is promoted to the identity via `Refresh MNB Attributes`, leave-freeze workflows and the `MNB-On-Leave` population cannot see her—schema design is a control dependency, not cosmetics.

## Before you start

- [ ] `MNB-HR` exists and `Aggregate MNB-HR` has succeeded
- [ ] You can open cubes for `priya.wire`, `samir.hassan`, `sofia.torres`
- [ ] Lesson 03 attribute/path notes handy

## Lab procedure

### Task 1 — Attribute inventory

Before mapping anything in IIQ, inventory which HR columns are governance signals versus connector noise—promotion is a deliberate control decision.

1. List every HR header column in your notebook.
2. Mark each **Identity** (promote) or **Link-only** (keep on account).
3. Minimum identity set: `email`, `manager` (from `managersAssociateID`), `departmentName`, `JobCode`, `inactive`, `status`, `employeeType`, `exceptions`, `location`.
4. Optional promote: `costCenter`, `hireDate`, `title` (title is display-friendly but prefer `JobCode` for rules).

**Expected result:** Two-column inventory table completed before changing IIQ.

### Task 2 — Refine MNB-HR schema maps

Maps tell IIQ *which* Link fields become Identity attributes. Promotion still needs a refresh after aggregation.

1. Open application `MNB-HR` → Schema / Attribute mapping (or Identity attribute mappings—path varies).
2. Map account attributes onto identity attributes used by IIQ (normalize names if UI expects `firstname` vs `firstName`—match what your install shows for existing identities).
3. Confirm manager mapping uses `managersAssociateID` toward identity correlation (manager name/id as your version requires).
4. Save. Re-run `Aggregate MNB-HR` if the UI warns that schema changes need aggregation.
5. Note for Lesson 06: after that aggregate, run **`Refresh MNB Attributes`** to promote/update identity attributes from the HR Link. Manager display may still need **`Refresh MNB Managers`**.

**Expected result:** Mapping saved without errors. Notebook lists each identity attribute → bank HR column **and** the refresh task that finishes promotion.

**If it fails:** Prefer IIQ’s documented identity attribute names from Debug → Identity example; do not invent conflicting attribute names.

### Task 3 — Manager hierarchy check

1. Open identity `priya.wire` (MNB00090).
2. Confirm HR shows `managersAssociateID=MNB00005` in the source file.
3. After mappings (and refresh in Lesson 06 if manager not yet resolved), expect manager toward `rachel.evans`.
4. Open `rachel.evans` and note her `departmentName` (Treasury & Payments) / `JobCode` `WIR02`.
5. Sketch two levels: `rachel.evans` → `priya.wire` / `marcus.approve`.

**Expected result:** Written hierarchy snippet for Payments. If manager display is empty, note “pending Identity Refresh” and continue—Lesson 06 completes calculation.

### Task 4 — Inactive and leave flags

1. Open `samir.hassan` (MNB00094): `inactive=true`, `status=Terminated`, `terminationDate=2026-05-30`.
2. Open `sofia.torres` (MNB00095): `inactive=false`, `status=Active`, `exceptions=LOA`.
3. Write how Meridian should treat each:

| Persona | Flag | Treatment |
| --- | --- | --- |
| samir.hassan | terminated | Leaver disablement; hunt residual IT access |
| sofia.torres | LOA (`exceptions`) | Temporary freeze; do not treat as final exit |

**Expected result:** Clear written distinction—feeds Lessons 31–33.

### Task 5 — Contractor and email quality check

1. Open `raj.external` (MNB00093): `employeeType=Contractor`, email `raj.contractor@vendor-mail.invalid`.
2. Note: corporate identity attribute email may not be `@meridiannb.com`.
3. Document: “Do not overwrite authoritative email from non-HR apps; flag vendor domains for correlation review.”

**Expected result:** Data-quality note in attribute dictionary.

### Task 6 — Publish attribute dictionary

Create this table in `~/iiq-lab-notes/` (or binder):

| Attribute | Source app | Source field | Consumers |
| --- | --- | --- | --- |
| userId / name | MNB-HR | userId / name | Correlation, display |
| email | MNB-HR | email | Notify, correlate |
| manager | MNB-HR | managersAssociateID | Certs, approvals |
| departmentName | MNB-HR | departmentName | Roles, populations |
| JobCode | MNB-HR | JobCode | Roles |
| inactive / status | MNB-HR | inactive, status | Leaver, populations |
| employeeType | MNB-HR | employeeType | Contractor scope |
| exceptions | MNB-HR | exceptions | LoA controls |

**Expected result:** Dictionary page exists; CHANGELOG notes “attribute dictionary v1”.

### Task 7 — Anti-patterns checklist

Add these “do not” rules to the dictionary footer:

1. Do not map IT `accountStatus` onto HR `inactive` / `status`.
2. Do not drive roles from free-text `title` when `JobCode` exists.
3. Do not let non-HR apps overwrite authoritative `email`.
4. Do not treat `exceptions=LOA` as terminated (`inactive=true`).

**Expected result:** Four anti-patterns listed; reusable in code reviews for later connectors.

## Acceptance criteria

- [ ] Identity vs Link inventory complete
- [ ] `MNB-HR` mappings updated and saved
- [ ] **Bank craft:** Optional export of maps/app of `config/Application/MNB-Application-HR.xml` when identity maps are durable
- [ ] Manager chain sketched for priya.wire → rachel.evans
- [ ] Termination vs exceptions (LOA) comparison written
- [ ] raj.external email anomaly noted
- [ ] Attribute dictionary published in notes/binder
- [ ] Anti-patterns checklist written

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Identity attrs blank | Not mapped / no refresh yet | Fix maps; run `Refresh MNB Attributes` (Lesson 06) |
| Manager shows raw id only | Manager correlation not run | Run `Refresh MNB Managers` |
| Wrong department on cube | Mapped display name instead of code | Map `departmentName` |
| Duplicate custom attributes | Invented names | Align to standard identity attrs |
| Contractor looks like employee | `employeeType` not promoted | Promote; re-aggregate; run `Refresh MNB Attributes` |

## Training binder evidence

- Attribute inventory table
- Screenshot: `priya.wire` attributes showing department/job/manager (or id)
- Screenshot: `sofia.torres` exceptions (LOA) vs `samir.hassan` inactive
- Attribute dictionary v1 document

**Examiner question:** “Which identity attributes drive your termination controls versus leave-of-absence controls?”

## Knowledge check

1. Which flag drives termination vs temporary freeze?
2. Why keep `JobCode` / department on the identity?
3. Name one attribute certifications commonly display.
4. Why avoid overwriting email from IT apps?
5. Who should be manager of `marcus.approve` per HR?
6. After HR aggregation, which Meridian Identity Refresh task promotes Link attributes onto the cube?

### Answers

1. `inactive=true` / `status=Terminated` (termination) vs `exceptions=LOA` (temporary freeze while still employed).
2. Roles and populations filter people by org/job codes; link-only fields are invisible to many selectors.
3. Examples: display name, department, job title, manager, email.
4. HR is authoritative; IT dumps can be stale or wrong (vendor domains, typos).
5. `rachel.evans` / MNB00005 (Payments Operations Manager).
6. `Refresh MNB Attributes` (Identity Refresh with attribute promotion from accounts).

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “identity attribute assignment” and “application schema” for map vs rule promotion patterns.
- [SailPoint Community](https://community.sailpoint.com/) — search “manager correlation” for hierarchy resolution tips after HR aggregation (`managersAssociateID`).
- [NIST SP 800-53 AC-2](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — account management attributes that must be accurate for lifecycle controls.
- [FFIEC IT Examination Handbook — Information Security](https://ithandbook.ffiec.gov/it-booklets/information-security.aspx) — expectations that identity attributes supporting access decisions are complete and current.
- [OWASP Identity Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Identity_and_Access_Management_Cheat_Sheet.html) — attribute hygiene and lifecycle signals (active vs leave vs terminated).

## Stretch lab

- Promote `costCenter` to the identity, run `Refresh MNB Attributes`, and show it on `helen.ross`.
- Build a one-page “forbidden mappings” list (e.g. never map IT `accountStatus` onto HR `inactive`).
- Using Debug, compare Identity XML before vs after mapping changes (post-refresh).

## Summary

- Governance needs bank HR fields on the identity, not buried only on the link.
- Codes (`JobCode`, `costCenter`) and lifecycle flags (`inactive`, `exceptions=LOA`) power roles and JML.
- After HR aggregation, `Refresh MNB Attributes` (Lesson 06) finishes Link → Identity promotion; the attribute dictionary is Meridian’s design contract for later lessons.

---

**Previous:** [Lesson 04 — Authoritative HR Source](04-authoritative-hr-source.md)  
**Next:** [Lesson 06 — Identity Cubes & Refresh](06-identity-cubes-and-refresh.md)
