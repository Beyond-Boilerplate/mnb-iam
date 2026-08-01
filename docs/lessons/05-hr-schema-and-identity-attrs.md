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
- [ ] You can open cubes for the personas below (see naming note)
- [ ] Lesson 03 attribute/path notes handy

### Beginner note — how cubes are named in this lab

Lesson 04 sets `MNB-HR` **native identity** = `userId`. That means Identity Warehouse **User Name** is usually `MNB00001`, not `helen.ross`.

| Persona (HR `name` / email) | Typical cube **User Name** | Display Name |
| --- | --- | --- |
| `helen.ross` | `MNB00001` | Helen Ross |
| `priya.wire` | `MNB00090` | Priya Mehta |
| `rachel.evans` | `MNB00005` | Rachel Evans |
| `samir.hassan` | `MNB00094` | Samir Hassan |
| `sofia.torres` | `MNB00095` | Sofia Torres |
| `raj.external` | `MNB00093` | Raj External |

Search Identity Warehouse by **display name**, **email**, or **`MNB…` id**. If you open a cube whose User Name is a plain display string (e.g. `Aisha Hughes`) with **no** Application Accounts, that is usually an orphan stub — not the real HR person. Prefer the `MNB…` cube.

## Lab procedure

### Task 1 — Attribute inventory

Before mapping anything in IIQ, inventory which HR columns are governance signals versus connector noise—promotion is a deliberate control decision.

1. List every HR header column in your notebook.
2. Mark each **Identity** (promote) or **Link-only** (keep on account).
3. Minimum identity set: `email`, `manager` (from `managersAssociateID`), `departmentName`, `JobCode`, `inactive`, `status`, `employeeType`, `exceptions`, `location`.
4. Optional promote: `costCenter`, `hireDate`, `title` (title is display-friendly but prefer `JobCode` for rules).

**Expected result:** Two-column inventory table completed before changing IIQ.

### Task 2 — Refine MNB-HR schema maps

Maps tell IIQ *which* Link fields become Identity attributes. **Saving maps does not fill the cube by itself**—aggregation writes the Link; **`Refresh MNB Attributes`** (Lesson 06) promotes Link → Identity. Manager display needs **`Refresh MNB Managers`**.

#### 2a — Do not confuse three different screens

| Screen | What it does | Lesson |
| --- | --- | --- |
| **Applications → MNB-HR → Schema** | Lists account (Link) columns from the CSV header (`firstname`, `JobCode`, …). Native identity = `userId`. | Lesson 04 (already done) |
| **Gear → Global Settings → Identity Mappings** | For each **Identity** attribute, adds an **Attribute Source**: Application `MNB-HR` + account attribute. This is the “schema map” this task means. | **This task** |
| **Applications → MNB-HR → Correlation** (Manager Correlation) | How IIQ resolves a manager *reference* on the account into another Identity (`managersAssociateID` → manager’s `userId`). | **This task** |

If you only edit Schema again, you are not mapping promotion. If Identity attrs stay blank after Lesson 06, come back here and check Identity Mappings + manager correlation.

#### 2b — Learn the names your install already uses

IIQ stock attributes are usually lowercase (`firstname`, `lastname`, `email`, `manager`)—not camelCase `firstName`. Custom Meridian fields (`departmentName`, `JobCode`, `exceptions`, …) must match **exactly** what you will use later in populations/roles.

1. Open a real HR cube (e.g. **`MNB00001`** / Helen Ross) → **Attributes** / view details.
2. Note the **exact** attribute names shown (spelling and case). Write them in your notebook.
3. Optional: **Debug** → Object Browser → `Identity` → open one identity → inspect `<Attributes>` / attribute keys. Prefer those names over inventing new ones.
4. Confirm on **MNB-HR → Schema** that the account columns you need exist (`email`, `firstname`, `lastname`, `displayName`, `managersAssociateID`, `departmentName`, `JobCode`, `inactive`, `status`, `employeeType`, `exceptions`, `location`, `costCenter`, `hireDate`, `terminationDate`). If a column is missing, rediscover schema (Lesson 04), save, then continue.

#### 2c — Map account → identity (Identity Mappings)

1. Open **Gear (⚙) → Global Settings → Identity Mappings**  
   (some builds: **System Setup → IdentityIQ Configuration → Identity Attributes**, or search the gear menu for “Identity Mappings”).
2. You will see a list of identity attributes (`firstname`, `email`, `manager`, …). For **each** stock row in the table below that already exists:
   - Open / edit that identity attribute.
   - **Do not rename** the attribute **Name** (technical key). Especially never rename **Display Name** (`displayName`) — IIQ will error: *“The attribute named 'Display Name' is required and cannot be renamed.”*
   - Under **Attribute Sources** (or “Value Source” / “Application Attribute”), **Add Source**.
   - Application: **`MNB-HR`**.
   - Attribute: the **account** column from the table (right column).
   - Prefer a single HR source for these fields (do not add IT apps here—Lesson 22 hygiene).
   - Save the attribute, then the next.
3. If an identity attribute does **not** exist yet (common for bank fields like `JobCode`, `exceptions`, `departmentName`, `employeeType`, `userId`):
   - Use **Add New Attribute** / **Create** on Identity Mappings (labels vary).
   - **Name** (technical key): **exactly** as in the left column below — no spaces, case-sensitive (`userId`, not `User ID`).
   - **Display Name** (UI label): friendly text is fine (e.g. `User ID`, `Employee Type`).
   - Type: string (unless your UI offers boolean for `inactive`—string is fine for lab CSV `"true"`/`"false"`).
   - Turn **Searchable** **ON** for custom fields you will use in manager correlation, populations, or Advanced Analytics (`userId`, `employeeType`, `departmentName`, `JobCode`, `exceptions`, `status`, …). Searchable assigns an extended attribute slot; without it, dropdowns often omit the field.
   - Then add the `MNB-HR` attribute source as above.

**Name vs Display Name (beginner trap):**

| Field on “Add Attribute” | Example correct | Example wrong |
| --- | --- | --- |
| **Name** (technical) | `employeeType` | `Employee Type` or `type` |
| **Display Name** (label) | `Employee Type` | (optional; can match Name) |

**Do not map HR `employeeType` onto stock IIQ `type`.** Stock **Type** is reserved for IIQ identity types (`employee`, `contractor`, … lowercase). Mapping CSV values `Employee` / `Contractor` onto `type` is skipped or can break the Attributes page. Always create a **custom** attribute named **`employeeType`**.

**Minimum maps for Meridian (copy into notebook):**

| Identity attribute (cube) | Source application | Account attribute (Link / CSV column) | Notes |
| --- | --- | --- | --- |
| `firstname` | MNB-HR | `firstname` | Stock — map source only; do not rename |
| `lastname` | MNB-HR | `lastname` | Stock |
| `email` | MNB-HR | `email` | Authoritative mail |
| `displayName` | MNB-HR | `displayName` | Or `fullName` if your cube already uses that; **never rename** this attribute |
| `departmentName` | MNB-HR | `departmentName` | Create + **Searchable** if missing |
| `JobCode` | MNB-HR | `JobCode` | Capital **J** and **C**—match CSV; **Searchable** |
| `inactive` | MNB-HR | `inactive` | Stock boolean / `"true"`/`"false"` from file |
| `status` | MNB-HR | `status` | Create + Searchable if missing |
| `employeeType` | MNB-HR | `employeeType` | **Custom** attr — not stock `type` |
| `exceptions` | MNB-HR | `exceptions` | `LOA` for leave; Searchable |
| `location` | MNB-HR | `location` | Searchable if used in filters |
| `costCenter` | MNB-HR | `costCenter` | Optional but useful |
| `hireDate` | MNB-HR | `hireDate` | Optional |
| `terminationDate` | MNB-HR | `terminationDate` | Optional; used for leavers |
| `userId` | MNB-HR | `userId` | Create + **Searchable** — required for manager correlation dropdown |

**Do not map for promotion (Link-only noise):** `fax`, empty phone columns, `wid_owner`, most `rf*` fields unless a later lesson needs them.

**Display name tip:** If Identity Mappings already has `name` or `displayName` sourced from somewhere else, keep **one** clear HR source (`displayName` or `fullName`). Do not create three competing name sources.

#### 2c-extra — Make custom fields show on View Identity → Attributes

Mapping + Searchable is not always enough for the **Attributes** tab. That page uses a whitelist in **UIConfig**:

1. Confirm the value exists first: **Debug → Identity → `MNB00001`** (or Accounts tab Link). If Debug shows `employeeType=Employee` but the Attributes tab does not, it is a UI list issue—not a failed map.
2. **Debug → Object Browser → UIConfig → `UIConfig`**.
3. Find entry **`identityViewAttributes`** (comma-separated list, e.g. `name,firstname,lastname,email,manager,type,…`).
4. Append your custom names (no spaces around commas), e.g. `,userId,employeeType,departmentName,JobCode,exceptions,status,inactive`.
5. Save. Hard-refresh the browser. Re-open the identity.

Until Lesson 06 refresh runs, Identity-level values may still be blank even when the Link is correct.

#### 2d — Manager: use `managersAssociateID`, not the display-name column

HR has **two** manager-related columns—do not mix them up:

| CSV column | Example value | Role |
| --- | --- | --- |
| `managersAssociateID` | `MNB00005` | **Correlation key** → manager’s `userId` |
| `manager` | `Rachel Evans` | Human-readable display only—**not** the correlation key |

1. Open **Applications → Application Definition → MNB-HR** (edit).
2. Open the **Correlation** tab (sometimes under Configuration / Advanced—search the app page for “Manager”).
3. Set **Manager Correlation** (wording varies). There are **two different dropdowns**:
   - **Manager attribute** (on the **account** / this app’s schema): `managersAssociateID`
   - **Identity attribute** (on the **manager’s** cube to match against): `userId`  
     If `userId` is missing from this dropdown, go back to Identity Mappings, edit `userId`, enable **Searchable**, save, then re-open the application page.
4. Save the application.
5. In **Identity Mappings**, open the stock identity attribute **`manager`**:
   - **Do not** add Attribute Source `manager` ← account column `manager` (display string like `Rachel Evans`).
   - That pattern creates dozens of empty orphan identities named after display strings and leaves First/Last/Email blank on those stubs.
   - Manager is filled when **manager correlation** runs during Identity Refresh (`Refresh MNB Managers` in Lesson 06). Your job here is correct correlation config + ensuring `managersAssociateID` exists on the Link after aggregation.
6. Optional notebook check: for Priya (`MNB00090`), HR has `managersAssociateID=MNB00005` → expect manager cube `MNB00005` / Rachel Evans **after** Lesson 06 refresh—not necessarily filled today.

**Wrong patterns (fix if you see them):**

| Wrong | Why it hurts |
| --- | --- |
| Manager correlation: account `manager` → identity `name` / display name | Duplicates, collisions, orphans |
| Identity Mapping: `manager` ← `MNB-HR.manager` (display string) | Same — orphan cubes with no HR Link |
| Identity attribute dropdown missing `userId` | `userId` not Searchable yet |

#### 2e — Save, re-aggregate if warned, then stop (refresh is Lesson 06)

1. Save Identity Mappings and the `MNB-HR` application (no red errors).
2. If the UI warns that schema / correlation changes require aggregation, run **`Aggregate MNB-HR`** (Tasks → existing aggregation task from Lesson 04 → Run Now). Wait for Success.
3. **Sanity check without full promotion:** open identity **`MNB00090`** (Priya) → **Application Accounts** → `MNB-HR` link → confirm Link attributes show `departmentName`, `JobCode`, `managersAssociateID=MNB00005`, `exceptions` (empty for Priya), etc. If the **Link** is wrong, fix Schema/file/aggregation—not Identity Mappings.
4. Identity-level `departmentName` / `manager` may still be empty or stale until Lesson 06. That is expected. Write in your notebook:

```text
After Aggregate MNB-HR:
  → Refresh MNB Attributes   (promotes mapped Link fields onto Identity)
  → Refresh MNB Managers     (resolves managersAssociateID → manager Identity)
(Create/run those tasks in Lesson 06.)
```

**Expected result:**  
- Identity Mappings rows saved for the minimum table.  
- Manager correlation uses `managersAssociateID` → `userId`.  
- Notebook lists each identity attribute → bank HR column **and** names the two refresh tasks that finish promotion.  
- Link attributes visible on at least one HR account.

**If it fails:**

| Symptom | Fix |
| --- | --- |
| Cannot find “Identity Mappings” | Gear search; or Debug → `ObjectConfig` named `Identity` (advanced). Lesson 92 also documents this path. |
| Attribute source dropdown empty for MNB-HR | Schema missing that column → rediscover Schema on `MNB-HR`, save, re-open Mappings. |
| Invented `firstName` / `dept` names | Delete/rename; align to cube names from step 2b. |
| Manager still a raw id or blank after Lesson 06 | Correlation pointed at `manager` display column, or forgot `Refresh MNB Managers`. |
| Error renaming Display Name | Leave stock `displayName` Name as-is; only add Attribute Source |
| `userId` missing from Manager Correlation identity dropdown | Edit `userId` in Identity Mappings → enable **Searchable** → save → reopen app |
| Custom field missing on Attributes tab but present in Debug | Append name to UIConfig `identityViewAttributes` (step 2c-extra) |
| Serious error / incident after editing Type | Do not map onto stock `type`; restore `type` and use custom `employeeType` |

### Task 3 — Manager hierarchy check

1. Open identity **`MNB00090`** (persona `priya.wire`).
2. Confirm HR shows `managersAssociateID=MNB00005` in the source file (Accounts tab is enough today).
3. After mappings (and refresh in Lesson 06 if manager not yet resolved), expect manager → **`MNB00005`** / Rachel Evans.
4. Open **`MNB00005`** and note her `departmentName` (Treasury & Payments) / `JobCode` `WIR02` (on Link now; on Identity after Lesson 06).
5. Sketch two levels: Rachel (`MNB00005`) → Priya (`MNB00090`) / Marcus (`MNB00091`).

**Expected result:** Written hierarchy snippet for Payments. If manager display is empty, note “pending Identity Refresh” and continue—Lesson 06 completes calculation.

### Task 4 — Inactive and leave flags

1. Open **`MNB00094`** (`samir.hassan`): Link shows `inactive=true`, `status=Terminated`, `terminationDate=2026-05-30`.
2. Open **`MNB00095`** (`sofia.torres`): `inactive=false`, `status=Active`, `exceptions=LOA`.
3. Write how Meridian should treat each:

| Persona | Flag | Treatment |
| --- | --- | --- |
| samir.hassan (`MNB00094`) | terminated | Leaver disablement; hunt residual IT access |
| sofia.torres (`MNB00095`) | LOA (`exceptions`) | Temporary freeze; do not treat as final exit |

**Expected result:** Clear written distinction—feeds Lessons 31–33.

### Task 5 — Contractor and email quality check

1. Open **`MNB00093`** (`raj.external`): Link `employeeType=Contractor`, email `raj.contractor@vendor-mail.invalid`.
2. Note: corporate identity attribute email may not be `@meridiannb.com`.
3. Document: “Do not overwrite authoritative email from non-HR apps; flag vendor domains for correlation review.”
4. Confirm you created identity attribute **`employeeType`** (not stock **Type**) for Lesson 07 contractor populations.

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
5. Do not map HR `employeeType` onto stock identity **`type`** — use custom `employeeType`.
6. Do not map or correlate manager from the HR **display-name** column `manager` — use `managersAssociateID` → `userId`.
7. Do not rename stock attributes (`displayName`, `firstname`, …) — only add Attribute Sources.
8. Do not create custom attributes with spaces in the **Name** (`User ID`); use `userId` and put spaces only in Display Name.

**Expected result:** Eight anti-patterns listed; reusable in code reviews for later connectors.

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
| Cannot find `helen.ross` identity | Cube named `MNB00001` | Search display name / `MNB…` / email |
| Empty cube named like “Aisha Hughes” | Orphan from manager display-name mapping | Use `MNB…` cube; remove bad `manager`←display source; delete orphans if needed |
| “Display Name … cannot be renamed” | Tried to rename stock `displayName` | Cancel; add Attribute Source only |
| Custom attr not in correlation / analytics dropdown | Not Searchable | Enable Searchable on the identity attribute |
| Custom attr not on Attributes tab | Not in UIConfig whitelist | Append to `identityViewAttributes` |
| Incident / NPE after editing Type | Mapped onto stock `type` | Restore `type`; create `employeeType` instead |

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
- Create custom attrs carefully: exact **Name**, **Searchable** on, never abuse stock `type` / `displayName`, never manager-from-display-name.
- After HR aggregation, `Refresh MNB Attributes` (Lesson 06) finishes Link → Identity promotion; the attribute dictionary is Meridian’s design contract for later lessons.

---

**Previous:** [Lesson 04 — Authoritative HR Source](04-authoritative-hr-source.md)  
**Next:** [Lesson 06 — Identity Cubes & Refresh](06-identity-cubes-and-refresh.md)
