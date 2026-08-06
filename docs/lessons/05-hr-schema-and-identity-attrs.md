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
- Tell apart three IIQ screens that beginners confuse: Schema, Identity Mappings, and Manager Correlation
- Map HR schema attributes so identity attributes populate after **`Refresh MNB Attributes`**
- Correlate managers via `managersAssociateID` — never the display-name column `manager`
- Distinguish terminated (`inactive=true`) from leave-of-absence (`exceptions=LOA`)
- Publish a short Meridian identity attribute dictionary for roles/SoD/JML

## Why this matters

Attribute design decides what roles, lifecycle events, and certifications can see. If `departmentName` / `JobCode` live only on the account link, population rules and birthright roles silently miss people — control gaps with no red error banner. Real bank extracts are wide (50+ columns); promotion must be deliberate.

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

> **Tip:** Rule on `JobCode` / `costCenter`, not free-text `title`. Display titles change; codes stay stable.

**Termination vs leave:**

| Signal | Meaning | Control intent |
| --- | --- | --- |
| `inactive=true` / `status=Terminated` | Employment ended | Disable / remove access (leaver) |
| `exceptions=LOA` (still Active) | Still employed, temporarily away | Freeze / reduce access; retain identity |

## How it works

Account Aggregation stores raw connector attributes on the **Link**. Identity attribute maps (or rules) **promote** selected fields onto the Identity so roles, populations, and certifications can filter on person-level truth — not buried account XML. **Mapping is design; promotion is a separate Refresh run (Lesson 06)** — saving maps here does not, by itself, fill the cube.

```text
MNB-HR Link attributes (userId, managersAssociateID, departmentName, JobCode, …)
        │
        ▼
Identity attribute assignment / maps  ←── this lesson stops here
        │
        ▼
Aggregate MNB-HR (if schema change requires it)
        │
        ▼
Refresh MNB Attributes  ← promotes Link fields onto Identity (Lesson 06)
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

**Real-life Meridian example.** `sofia.torres` has `exceptions=LOA` on HR. Until that flag is promoted to the identity via `Refresh MNB Attributes`, leave-freeze workflows and the `MNB-On-Leave` population cannot see her — schema design is a control dependency, not cosmetics.

## Before you start

- [ ] `MNB-HR` exists and `Aggregate MNB-HR` has succeeded
- [ ] You can open cubes for the personas below (see naming note)
- [ ] Lesson 03 attribute/path notes handy

### Beginner note — how cubes are named in this lab

Lesson 04 sets `MNB-HR` **native identity** = `userId`, so Identity Warehouse **User Name** is `MNB00001`, not `helen.ross`. Search by **display name**, **email**, or **`MNB…` id** — all three work.

| Persona (HR `name` / email) | Cube **User Name** | Display Name |
| --- | --- | --- |
| `helen.ross` | `MNB00001` | Helen Ross |
| `priya.wire` | `MNB00090` | Priya Mehta |
| `rachel.evans` | `MNB00005` | Rachel Evans |
| `samir.hassan` | `MNB00094` | Samir Hassan |
| `sofia.torres` | `MNB00095` | Sofia Torres |
| `raj.external` | `MNB00093` | Raj External |

> **Watch out:** If you open a cube whose User Name is a plain display string (e.g. `Aisha Hughes`) with **no** Application Accounts, that is usually an orphan stub — not the real HR person. Prefer the `MNB…` cube.

## Lab procedure

### Task 1 — Attribute inventory

Before mapping anything in IIQ, inventory which HR columns are governance signals versus connector noise — promotion is a deliberate control decision.

1. List every HR header column in your notebook.
2. Mark each **Identity** (promote) or **Link-only** (keep on account).
3. Minimum identity set: `email`, `manager` (from `managersAssociateID`), `departmentName`, `JobCode`, `inactive`, `status`, `employeeType`, `exceptions`, `location`.
4. Optional promote: `costCenter`, `hireDate`, `title` (prefer `JobCode` for rules).

**Expected result:** Two-column inventory table completed before changing IIQ.

### Task 2 — Three screens, not one

Beginners conflate three different IIQ screens. Learn the split before you touch anything:

| Screen | What it does | Status |
| --- | --- | --- |
| **Applications → MNB-HR → Schema** | Lists account (Link) columns from the CSV header. Native identity = `userId`. | Done in Lesson 04 |
| **Gear → Global Settings → Identity Mappings** | For each **Identity** attribute, adds an **Attribute Source**: application `MNB-HR` + account attribute. | **This task** |
| **Applications → MNB-HR → Correlation** (Manager Correlation) | Resolves a manager *reference* on the account into another Identity (`managersAssociateID` → manager's `userId`). | **This task** |

If you only re-edit Schema, you have not mapped promotion. If Identity attrs stay blank after Lesson 06, come back here and check Identity Mappings + manager correlation — not Schema.

### Task 3 — Map account → identity (Identity Mappings)

IIQ stock attributes are usually lowercase (`firstname`, `email`, `manager`) — not camelCase. Custom Meridian fields (`departmentName`, `JobCode`, `exceptions`, …) must match **exactly** what later lessons use in populations/roles.

1. Open a real HR cube (e.g. `MNB00001` / Helen Ross), note the **exact** attribute names shown (or Debug → Object Browser → `Identity` → `<Attributes>` keys).
2. Open **Gear (⚙) → Global Settings → Identity Mappings** (some builds: System Setup → IdentityIQ Configuration → Identity Attributes).
3. For each **stock** attribute already listed (`firstname`, `lastname`, `email`, `displayName`): open it, add **Attribute Source** → application `MNB-HR` → matching account column. **Never rename** the attribute Name — especially `displayName` (IIQ blocks renaming Display Name).
4. For attributes that do **not** exist yet (`userId`, `JobCode`, `exceptions`, `departmentName`, `employeeType`, `status`): use **Add New Attribute**.
   - **Name** (technical key): exactly as in the table below — case-sensitive, no spaces (`userId`, not `User ID`).
   - **Display Name**: friendly label is fine (`User ID`, `Employee Type`).
   - Turn **Searchable** ON for anything used in manager correlation, populations, or Advanced Analytics — without it, dropdowns omit the field.
   - Add the `MNB-HR` attribute source, then save.

**Minimum maps for Meridian (copy into notebook):**

| Identity attribute | Account attribute (CSV column) | Notes |
| --- | --- | --- |
| `firstname` / `lastname` | `firstname` / `lastname` | Stock — map source only, never rename |
| `email` | `email` | Authoritative mail |
| `displayName` | `displayName` | Never rename this attribute |
| `departmentName` | `departmentName` | Create + **Searchable** |
| `JobCode` | `JobCode` | Capital J/C — match CSV; **Searchable** |
| `inactive` | `inactive` | Stock boolean (`"true"`/`"false"`) |
| `status` | `status` | Create + Searchable |
| `employeeType` | `employeeType` | **Custom** attr — never stock `type` |
| `exceptions` | `exceptions` | `LOA` for leave; Searchable |
| `location` | `location` | Searchable if used in filters |
| `costCenter` / `hireDate` / `terminationDate` | same | Optional but useful for leavers |
| `userId` | `userId` | Create + **Searchable** — required for manager correlation dropdown |

> **Watch out:** Do not map HR `employeeType` onto stock IIQ `type`. Stock **Type** is reserved for IIQ identity types (`employee`, `contractor`, lowercase); mapping CSV `Employee`/`Contractor` onto it is skipped or can break the Attributes page. Always create a **custom** `employeeType` attribute.

**Do not map for promotion (Link-only noise):** `fax`, empty phone columns, `wid_owner`, most `rf*` fields.

### Task 4 — Make custom fields show on View Identity → Attributes

Mapping + Searchable is not always enough for the **Attributes** tab — that page uses a whitelist in **UIConfig**.

1. Confirm the value exists first: **Debug → Identity → `MNB00001`**. If Debug shows `employeeType=Employee` but Attributes does not, it is a UI list issue, not a failed map.
2. **Debug → Object Browser → UIConfig → `UIConfig`** → find `identityViewAttributes` (comma-separated list).
3. Append your custom names, no spaces around commas: `,userId,employeeType,departmentName,JobCode,exceptions,status,inactive`.
4. Save, hard-refresh, re-open the identity. Values may still read blank until Lesson 06 refresh runs — that is expected.

**Expected result:** Custom fields appear on the Attributes tab once a value exists on the Link.

### Task 5 — Manager: `managersAssociateID`, not the display column

HR has two manager-related columns — do not mix them up: `managersAssociateID` (`MNB00005`, the correlation key) vs `manager` (`Rachel Evans`, display-only).

1. Open **Applications → MNB-HR → Correlation** (Manager Correlation; sometimes under Configuration/Advanced).
2. Set **Manager attribute** (on this app's schema) = `managersAssociateID`; **Identity attribute** to match against (on the manager's cube) = `userId`. If `userId` is missing from the dropdown, make it Searchable first (Task 3), then reopen.
3. Save the application. In Identity Mappings, open stock attribute `manager`: **do not** add Attribute Source `manager` ← account `manager` (display string) — that pattern creates orphan identities named after display strings with First/Last/Email blank.
4. Manager fills in when **manager correlation runs during Identity Refresh** (`Refresh MNB Managers`, Lesson 06) — your job here is correct config, not the fill itself. For Priya (`MNB00090`), HR has `managersAssociateID=MNB00005` → expect manager cube `MNB00005` / Rachel Evans **after** Lesson 06 refresh, not necessarily today.

**Expected result:** Correlation uses `managersAssociateID` → `userId`; Identity Mappings has no `manager` ← display-name source.

**If it fails:** Manager still a raw id or blank after Lesson 06 → correlation pointed at the `manager` display column, or you forgot to run `Refresh MNB Managers`.

### Task 6 — Save, sanity-check, then stop (refresh is Lesson 06)

1. Save Identity Mappings and the `MNB-HR` application (no red errors). If the UI warns that changes require aggregation, re-run `Aggregate MNB-HR` and wait for Success.
2. Sanity check without full promotion: open `MNB00090` (Priya) → **Application Accounts** → `MNB-HR` link → confirm the **Link** shows `departmentName`, `JobCode`, `managersAssociateID=MNB00005`, `exceptions` (empty for Priya). If the Link is wrong, fix Schema/file/aggregation — not Identity Mappings.
3. Identity-level `departmentName` / `manager` may still be empty until Lesson 06. Write in your notebook: "After Aggregate MNB-HR → Refresh MNB Attributes (promote) → Refresh MNB Managers (resolve). Create/run those tasks in Lesson 06."

**Expected result:** Mappings saved; manager correlation config correct; notebook names the two refresh tasks that finish the job. Do **not** run an Identity Refresh in this lesson — that is Lesson 06's job.

### Task 7 — Termination, LOA, contractor, and the attribute dictionary

1. Open `MNB00094` (`samir.hassan`): Link shows `inactive=true`, `status=Terminated`, `terminationDate` set. Treatment: leaver disablement; hunt residual IT access.
2. Open `MNB00095` (`sofia.torres`): `inactive=false`, `status=Active`, `exceptions=LOA`. Treatment: temporary freeze, not final exit.
3. Open `MNB00093` (`raj.external`): `employeeType=Contractor`, email `raj.contractor@vendor-mail.invalid`. Authoritative email may not be `@meridiannb.com` for vendors — do not overwrite it from non-HR apps.
4. Publish an attribute dictionary table (`userId`/`name`, `email`, `manager` ← `managersAssociateID`, `departmentName`, `JobCode`, `inactive`/`status`, `employeeType`, `exceptions`) with source app/field/consumers, then append the anti-patterns checklist below as its footer.

**Anti-patterns (do not do these):**

1. Map IT `accountStatus` onto HR `inactive` / `status`.
2. Drive roles from free-text `title` when `JobCode` exists.
3. Let non-HR apps overwrite authoritative `email`.
4. Treat `exceptions=LOA` as terminated (`inactive=true`).
5. Map HR `employeeType` onto stock identity **`type`** — use custom `employeeType`.
6. Map or correlate manager from the HR **display-name** column `manager` — use `managersAssociateID` → `userId`.
7. Rename stock attributes (`displayName`, `firstname`, …) — only add Attribute Sources.
8. Create custom attributes with spaces in the **Name** (`User ID`); use `userId` and put spaces only in Display Name.

**Expected result:** Dictionary + eight anti-patterns published; CHANGELOG notes "attribute dictionary v1".

## Acceptance criteria

- [ ] Identity vs Link inventory complete
- [ ] `MNB-HR` mappings updated and saved (three-screens distinction understood)
- [ ] **Bank craft:** Optional export of maps/app to `config/Application/MNB-Application-HR.xml`
- [ ] Manager correlation uses `managersAssociateID` → `userId`; no display-name `manager` source
- [ ] Termination vs exceptions (LOA) comparison written
- [ ] raj.external email anomaly noted
- [ ] Attribute dictionary + anti-patterns published in notes/binder
- [ ] No Identity Refresh run this lesson — deferred to Lesson 06

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Identity attrs blank | Not mapped / no refresh yet | Fix maps; run `Refresh MNB Attributes` (Lesson 06) |
| Manager shows raw id only | Manager correlation not run | Run `Refresh MNB Managers` (Lesson 06) |
| Wrong department on cube | Mapped display name instead of code | Map `departmentName`, not free text |
| Contractor looks like employee | `employeeType` not promoted | Promote custom attr; re-aggregate; refresh |
| Cannot find `helen.ross` | Cube is `MNB00001` | Search display name / `MNB…` / email |
| Empty cube named like "Aisha Hughes" | Orphan from manager display-name mapping | Use `MNB…` cube; remove bad `manager` source; delete orphans |
| "Display Name … cannot be renamed" | Tried to rename stock `displayName` | Cancel; add Attribute Source only |
| `userId` missing from correlation dropdown | Not Searchable | Enable Searchable, save, reopen app |
| Custom attr not on Attributes tab | Not in UIConfig whitelist | Append to `identityViewAttributes` |
| Incident / error after editing Type | Mapped onto stock `type` | Restore `type`; create `employeeType` instead |

## Training binder evidence

- Attribute inventory table
- Screenshot: `priya.wire` Link showing department/job/`managersAssociateID`
- Screenshot: `sofia.torres` exceptions (LOA) vs `samir.hassan` inactive
- Attribute dictionary v1 document with anti-patterns footer

## Knowledge check

1. Which flag drives termination vs temporary freeze?
2. Why keep `JobCode` / department on the identity instead of only the Link?
3. Which HR column is the manager **correlation key**, and which is display-only?
4. Why avoid overwriting email from IT apps?
5. Which Identity Refresh task (Lesson 06) promotes Link attributes onto the cube?
6. Why does this lesson stop before running any refresh?

### Answers

1. `inactive=true` / `status=Terminated` (termination) vs `exceptions=LOA` (temporary freeze while still employed).
2. Roles and populations filter people by org/job codes; link-only fields are invisible to many selectors.
3. `managersAssociateID` is the correlation key (→ manager's `userId`); `manager` is a display-only string and must never be mapped or correlated against.
4. HR is authoritative; IT dumps can be stale or wrong (vendor domains, typos).
5. `Refresh MNB Attributes` (with `Refresh MNB Managers` for hierarchy).
6. Mapping is design; promotion is a Refresh run. Running refresh belongs to Lesson 06 so the pipeline order (aggregate → attributes → managers) stays intact and auditable.

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search "identity attribute assignment" and "application schema" for map vs rule promotion patterns.
- [SailPoint Community](https://community.sailpoint.com/) — search "manager correlation" for hierarchy resolution tips after HR aggregation (`managersAssociateID`).
- [NIST SP 800-53 AC-2](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — account management attributes that must be accurate for lifecycle controls.
- [FFIEC IT Examination Handbook — Information Security](https://ithandbook.ffiec.gov/it-booklets/information-security.aspx) — expectations that identity attributes supporting access decisions are complete and current.
- [OWASP Identity Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Identity_and_Access_Management_Cheat_Sheet.html) — attribute hygiene and lifecycle signals (active vs leave vs terminated).

## Stretch lab

- Promote `costCenter` to the identity now; leave the actual refresh for Lesson 06, and predict what `helen.ross` will show afterward.
- Build a one-page "forbidden mappings" list (e.g. never map IT `accountStatus` onto HR `inactive`).
- Using Debug, capture Identity XML now so you can diff it against post-refresh XML in Lesson 06.

## Summary

- Governance needs bank HR fields on the identity, not buried only on the link — and three separate screens (Schema, Identity Mappings, Manager Correlation) each do one job.
- Codes (`JobCode`, `costCenter`) and lifecycle flags (`inactive`, `exceptions=LOA`) power roles and JML; manager correlation must use `managersAssociateID`, never the display column.
- Mapping alone does not fill the cube — this lesson stops at save; `Refresh MNB Attributes` and `Refresh MNB Managers` (Lesson 06) finish Link → Identity promotion.

## Feedback

Could you explain, without notes, why `manager` (display) and `managersAssociateID` (correlation key) are not interchangeable? If any mapping step produced a surprise (orphan cube, blocked rename, blank dropdown), record the task number and symptom — that is the fastest way to sharpen this lesson.

## Navigation

**Previous:** [Lesson 04 — Authoritative HR Source](04-authoritative-hr-source.md)  
**Next:** [Lesson 06 — Identity Cubes & Refresh](06-identity-cubes-and-refresh.md)
