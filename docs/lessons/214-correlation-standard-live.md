# Lesson 214 — Nail Correlation Across Live Apps

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~70 minutes  
**Prereq:** Lessons 207, 204–210 (Workday cubes + live apps aggregated at least once)  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 05 (identity attrs / manager corr), 06 (refresh), 09 (create-identities OFF), 16 (agg order), 17–19 (correlation + remediation), 21–22 (manager / attr hygiene)

> **Why:** Bad correlation quietly creates permanent orphans and duplicate cubes — the most expensive mistake in a real IIQ deployment. You need a stable employee-id story before username reissue, or rehire will mint duplicates.

## What this is

By this point you’ve aggregated six live applications, each with its own native key. Classic Lessons **17–19** taught the Meridian correlation standard on CSV; this lesson proves the **same standard** across live connectors and practices the uncorrelated-account repair loop.

**Every employee-id-shaped attribute → identity `userId`. Every username-shaped attribute is login/display only.**

| App | Correlation key → IIQ `userId` | Login / display |
| --- | --- | --- |
| `MNB-Workday` (authoritative) | account `id` promoted to cube `userId` | `userName` / email |
| `MNB-OpenLDAP` | `employeeNumber` | `uid` |
| `MNB-ActiveDirectory-Live` | `employeeNumber` | `sAMAccountName` |
| `MNB-CoreBanking` | `employee_id` | `username` |
| `MNB-WirePortal` | app employee-id attr | account id |
| `MNB-Salesforce-CRM-Live` | `externalId` | `userName` |

Enterprise Path **skips** classic Lesson **05**. You still need Searchable cube `userId`, UIConfig visibility, and manager correlation — Task 1 and Task 6 carry that work here.

## Concept primer — vocabulary before you click

If any term below is fuzzy, stop and read it. Tasks assume these meanings.

### Meridian ID map

```text
Workday account id / LDAP employeeNumber / JDBC employee_id / CRM externalId
        │  (same MNB##### values)
        ▼
Identity cube attribute userId   ← correlation target
Identity name / userName         ← login / search convenience only
```

| Term | Plain English | Meridian example |
| --- | --- | --- |
| **`userId`** | Stable associate key on the **Identity cube** (`MNB#####`) | Helen’s cube has `userId=MNB00001` |
| **`employeeId` / `employeeNumber` / `employee_id`** | Account-side column names for the **same** `MNB#####` values — not a second HR key | OpenLDAP `employeeNumber=MNB00001` |
| **Schema `identityAttribute`** | Account **native key** on Application → **Schema** | Workday schema `id` |
| **Correlation “Identity Attribute”** | Cube attribute in Correlation dropdown (Identity Mappings) | Always **`userId`** here |
| **Authoritative / create-identities** | App flag: unmatched accounts may **mint cubes** | **Only** `MNB-Workday` |
| **Uncorrelated account** | Real app account with **no** Link to a cube — fixable | Core Banking after you set `employee_id=BOGUS` |
| **Orphan / ghost identity** | Cube minted from a **non**-authoritative app (often from LDAP `cn`) | `Helen Ross` beside `helen.ross` |

> **Watch out:** Never invent an HR `employeeId` column. IT dumps say `employeeId`; directories say `employeeNumber`; the cube always stores **`userId`**.

### Aggregation vs correlation vs refresh

These are three different machines. Mixing them up is how “I ran aggregation” still leaves blank attrs and split cubes.

| Process | What it does | What it does **not** do |
| --- | --- | --- |
| **Account Aggregation** | Reads the connector → creates/updates **Links** (accounts); runs correlation maps | Promote cube attrs; resolve managers; invent missing CorrelationConfig |
| **Account correlation** | During agg (or reprocess): match account key → existing cube → attach Link | Create people (unless create-identities is ON — never on targets) |
| **Identity Refresh** | Re-evaluates options on cubes: promote attrs, manager correlation, roles… | Replace the need to aggregate sources |

```text
Workday agg (authoritative) → cube exists (+ Link)
  → Identity Refresh → promote id → cube userId; resolve managers
  → other apps agg → match employee-id → Link on same cube
  → no match → Uncorrelated Accounts (fix the key — don't mint a second cube)
```

**Authoritative-first order** (classic 16, live here):

1. `MNB-Workday`
2. Directories (`MNB-OpenLDAP`, `MNB-ActiveDirectory-Live`)
3. Downstream apps (`MNB-CoreBanking`, `MNB-WirePortal`, `MNB-Salesforce-CRM-Live`)

Reverse order creates **transient orphans**. Empty CorrelationConfig + create-identities ON creates **permanent ghosts**.

### Three screens beginners confuse (classic 05)

| Screen | Job | Example |
| --- | --- | --- |
| Application → **Schema** | Account columns; native identity | Workday `identityAttribute=id` |
| **Gear → Identity Mappings** | Link attr → cube attr (promotion sources) | Workday `id` → cube `userId` (**Searchable**) |
| Application → **Correlation** | Account attr → cube attr (match during agg) **or** Manager Correlation | `employeeNumber` → `userId`; manager ref → manager’s `userId` |

### Uncorrelated vs orphan (classic 09 / 17)

```text
Uncorrelated IT / LDAP account
  ├─ create-identities OFF → stays uncorrelated (fix key / remediate) ✓
  └─ create-identities ON  → orphan Identity named like "Helen Ross" ✗
```

| App | Authoritative? | Creates identities? |
| --- | --- | --- |
| `MNB-Workday` | Yes | Yes |
| Every other live app in this lesson | No | **No** |

**Wrong way:** “Empty the uncorrelated list” by flipping create-identities ON. That manufactures ghost people with no Workday truth, no trustworthy leaver, and split app links.

### Key preference order (classic 17–18)

```text
Strongest ──► employee-id-shaped account attr = identity.userId
Next       ──► email = email (secondary only)
Avoid      ──► uid / sAMAccountName / userName / display name / fuzzy match
```

**False merge** (wrong person gets the Link) is worse than a **false orphan** (visible, remediable). Prefer precision over “everything linked.”

| Approach | Outcome |
| --- | --- |
| Email-only | Contractors / vendor mail fail; hidden orphans |
| Name / `cn` matching | False merges; `Helen Ross` ghost cubes |
| Create-identities on targets | Ghost cubes; apps split across duplicates |
| Employee-id → `userId`; create OFF | Residuals measurable and remediable |

### Manager correlation (classic 05 / 06 / 21)

**Manager correlation** is not account correlation. It resolves a **manager reference on the account** into a **pointer to another Identity** during Identity Refresh.

| Piece | Role |
| --- | --- |
| Workday / HCM `managerId` (Enterprise) | Manager’s associate id (`MNB00006` for Priya → Sanjay) |
| Classic CSV `managersAssociateID` | Same idea on `MNB-HR` |
| Display column `manager` / `cn` | **Display only** — never map or correlate from this |

```text
Priya’s Workday row managerId=MNB00006
  → Refresh with manager correlation
  → cube priya.wire.manager → sanjay.kapoor (userId MNB00006)
```

> **Watch out:** Mapping Identity `manager` from a display-name account column mints empty cubes named like people (“Helen Ross”) with blank First/Last/Email — the same ghost pattern as directory create-identities.

### Identity attribute hygiene (classic 22 — preview)

- **Workday owns** lifecycle identity attrs: `userId`, email, status, department, manager chain
- Live directories / JDBC / CRM own **account** facts and entitlements on the **Link**
- Do not promote AD title / LDAP `cn` onto cube fields that Workday already owns — that is how cubes **flip-flop** after every agg

## Intent

- Build Searchable cube `userId` (and UI visibility) the classic-05 way, then wire live-app correlation
- Re-aggregate authoritative-first; prove personas have one cube with all intended Links
- Detect and repair display-name duplicate cubes if you already minted them
- Break and heal one JDBC correlation (classic 19 loop)
- Confirm manager hierarchy for `priya.wire` after manager refresh

## Before you start

- [ ] Enterprise stack up; IIQ healthy on `:8080`
- [ ] Lesson **207** done — Warehouse has Workday cubes (`helen.ross`, …)
- [ ] Lessons 204–210 apps exist and have aggregated at least once
- [ ] JDBC container reachable (`mnb-jdbc-sample` or your compose name)
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/214
```

## Do this

### Task 1 — Ensure cube `userId` is correlatable, then verify each app

Open each Application and confirm the correlation attribute maps to identity **`userId`** — don’t trust a table you memorized. First make sure `userId` can appear in the Correlation dropdown.

> **Double-check:** Correlation → **Identity Attribute** will never list Workday schema `id` — that name is Schema-only (account native key). You need cube **`userId`** (same `MNB#####` values). If it is missing from the dropdown: **Gear → Global Settings → Identity Mappings** → add Searchable `userId` sourced from `MNB-Workday` / `id` → **Identity Refresh** → reopen Correlation → map each app’s employee-id attr → `userId`.

#### 1a — Create Searchable `userId` (classic 05 work, done here)

Enterprise Path never ran classic Lesson **05**, so `userId` may never have been created as a Searchable identity attribute. Without that, Correlation’s Identity Attribute list cannot offer it — and Workday schema `id` will never appear there either.

1. **Gear (⚙) → Global Settings → Identity Mappings** (or System Setup → Identity Attributes)
2. If `userId` is missing: **Add New Attribute**
   - **Name:** `userId` (exact; no spaces — not `User ID`)
   - **Display Name:** `User ID` is fine
   - Turn **Searchable** **ON** (required for Correlation / manager / population dropdowns)
3. Add an **Attribute Source**: application `MNB-Workday` → account attribute **`id`** (same `MNB#####` values as the identity master)
4. **Save**, then run **Identity Refresh** with **promote / refresh identity attributes** enabled so existing Workday cubes promote `id` → cube `userId`
5. Re-open any Application → **Correlation** — Identity Attribute should now list `userId`

> **Watch out — dropdown “sets” then goes blank / grid row is empty:** This is usually **not** “Searchable is off.” In Identity Mappings, **Searchable** is implemented as an `extendedNumber` on ObjectConfig (your `userId` already has `extendedNumber="1"`). The failure mode is that AttributeAssignments never land on the CorrelationConfig.
>
> Check Debug → `CorrelationConfig` (the name on the app, e.g. `employeeId-corr`). If you see a bare `<CorrelationConfig name="…"/>` with **no** `<AttributeAssignments>`, the UI never persisted the map — even if the dropdowns looked filled for a moment.
>
> Fix the click path:
> 1. Application → **Correlation** → select or type a **Correlation Config** name first
> 2. Choose **Identity Attribute** = `userId`
> 3. Choose **Application Attribute** = `employeeNumber` (or that app’s employee-id attr)
> 4. Click the **Add** control (arrow / +) — do **not** only Save the Application
> 5. Confirm the **list below** shows both names in the row (not blank cells)
> 6. **Then** Save the Application
> 7. Re-open Debug → that CorrelationConfig must show AttributeAssignments
>
> If Add still inserts a blank row, or Save keeps an empty config: **stop using the stub.** Import a CorrelationConfig via Debug (XML below), then on the Application pick that **existing** config from the dropdown (do not keep reusing empty `employeeId-corr` / `employeeId` shells).

**Working CorrelationConfig XML (OpenLDAP example — import via Debug → Import):**

```xml
<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE CorrelationConfig PUBLIC "sailpoint.dtd" "sailpoint.dtd">
<CorrelationConfig name="MNB-OpenLDAP Correlation">
  <AttributeAssignments>
    <Filter operation="EQ" property="userId" value="employeeNumber"/>
  </AttributeAssignments>
</CorrelationConfig>
```

- `property` = **identity** attribute (`userId`)
- `value` = **account** attribute (`employeeNumber`)

Repeat per app (`employee_id`, `externalId`, …) with a distinct config name, or one shared config if every app uses the same account attr name (they do not — prefer one config per app).

**Prove Searchable / extended attr in ObjectConfig (optional):**

```xml
<ObjectAttribute displayName="User Id" extendedNumber="1" name="userId" type="string">
  <AttributeSource name="id">
    <ApplicationRef>
      <Reference class="sailpoint.object.Application" name="MNB-Workday"/>
    </ApplicationRef>
  </AttributeSource>
</ObjectAttribute>
```

`extendedNumber="1"` **is** Searchable in the Identity Mappings UI. Missing `searchable="true"` on the XML tag alone does not mean the checkbox is off.

- **Why:** correlation looks up cubes by extended/searchable `userId`. Empty AttributeAssignments mean every aggregation correlates nothing — dropdown theater without a saved map.
- **Expect:** Debug CorrelationConfig shows real Filters; Application Correlation list shows non-blank rows after Add.

#### 1a-bis — Make `userId` visible on View Identity → Attributes (UIConfig XML)

Searchable + mapped is enough for Correlation dropdowns. The **Attributes** tab still hides custom fields until they are on the UIConfig whitelist (classic 05).

**UI path (same outcome):** Debug → Object Browser → `UIConfig` → `UIConfig` → edit `identityViewAttributes` → append `,userId` → Save → hard-refresh the browser.

**XML path (lesson default — export, edit, import):**

1. Debug → Object Browser → `UIConfig` → `UIConfig` → **Export** / copy the object XML (or console `get UIConfig UIConfig`)
2. Find the `identityViewAttributes` entry. Stock looks like:

```xml
<entry key="identityViewAttributes" value="name, firstname, lastname, email, manager, type, employeeType, administrator"/>
```

3. Append `userId`:

```xml
<entry key="identityViewAttributes" value="name, firstname, lastname, email, manager, type, employeeType, administrator,userId"/>
```

4. Import the edited XML (Debug → Import, or console `import` / MCP `import_sailpoint_object`)
5. Hard-refresh the browser; open `helen.ross` → **Attributes** and confirm **User ID** / `userId` shows `MNB00001`

> **Tip:** If Debug shows `userId=MNB00001` but Attributes does not, it is only the whitelist — not a failed Identity Mapping.

> **Watch out:** Do not pick Correlation Identity Attribute `name` just because Helen’s cube is searchable as `helen.ross`. Login/display can change; `userId` / Workday `id` must not.

#### 1b — Verify account correlation on each live app

1. **Applications → Application Definition** for each non-Workday row in the table above
2. Open **Correlation** (Account Correlation)
3. Map the employee-id-shaped **application** attribute → Identity Attribute **`userId`**
   - OpenLDAP / AD-Live: account `employeeNumber` → `userId` (not `employeeId` — LDAP’s attribute is `employeeNumber`)
   - Core Banking: `employee_id` → `userId`
   - CRM Live: `externalId` → `userId`
4. Confirm login attributes (`uid`, `sAMAccountName`, `userName`, …) are **not** the primary correlation key
5. Create-identities / authoritative stays **off** on these targets — only `MNB-Workday` mints cubes
6. **Save**, then prove the CorrelationConfig is not an empty shell:
   - Debug → Object Browser → `CorrelationConfig` → open the config referenced by the app (e.g. `employeeId-corr`)
   - You must see **AttributeAssignments** / Filter rows like:

```xml
<CorrelationConfig name="MNB-OpenLDAP Correlation">
  <AttributeAssignments>
    <Filter operation="EQ" property="userId" value="employeeNumber"/>
  </AttributeAssignments>
</CorrelationConfig>
```

   - `property` = **identity** attr (`userId`); `value` = **account** attr (`employeeNumber`)
   - An empty `<CorrelationConfig name="…"/>` with no assignments correlates **nothing** — every agg will orphan or mint ghosts
   - If the UI keeps saving empty configs: import the XML above (adjust name + account attr per app), then set Application → Correlation to reference that config

- **Why:** a single mis-mapped app is how duplicates sneak in after a clean Workday cube exists; an empty named CorrelationConfig is the silent version of “I thought I configured it.”
- **Expect:** every live app’s correlation key matches the table; Identity Attribute is `userId`, not schema `id`; CorrelationConfig XML has real AttributeAssignments.

> **Watch out:** Cubes come from Lesson **207** (`MNB-Workday`). Do **not** aggregate `MNB-HR` to “fix” missing identities.

### Task 2 — Re-aggregate in authoritative-first order

Correlation mappings alone do not rewrite Links already glued to the wrong cube. You must re-ingest accounts so the engine re-evaluates matches (classic 17).

Run **Account Aggregation** in this order:

1. `MNB-Workday`
2. `MNB-OpenLDAP`
3. `MNB-ActiveDirectory-Live`
4. `MNB-CoreBanking`
5. `MNB-WirePortal`
6. `MNB-Salesforce-CRM-Live`

Then run **Identity Refresh** (promote attributes at least once after Task 1a).

- **Why:** authoritative source first creates/updates cubes so later apps have something to attach to; refresh makes `userId` and managers trustworthy on the cube.
- **Expect:** Task Results succeed. Reverse order often creates transient uncorrelated noise.

> **Tip:** Aggregation lives under **Setup → Tasks**. Application Definition only has **Test Connection**.

### Task 3 — Spot-check persona cubes (and catch display-name duplicates)

Open **Identities → Identity Warehouse** and search each persona **twice**: by login (`helen.ross`) and by display name (`Helen Ross`).

| Good cube | Bad / ghost cube |
| --- | --- |
| Name `helen.ross`, `userId=MNB00001`, Workday link present | Name `Helen Ross` (space, title case), **no** `userId`, often only an OpenLDAP / AD link |

Count Application Accounts links on the **good** cube only.

- **Why:** when CorrelationConfig is empty or create-identities was on for a directory, IIQ mints a second cube from LDAP `cn` / AD display name. Apps then **split** across the pair — Workday+CRM on `helen.ross`, OpenLDAP on `Helen Ross`. Agg + Refresh will not heal that by themselves.
- **Expect:** one cube per persona; every live app they should have is on that cube; Warehouse search for `"Helen Ross"` / `"Priya Mehta"` style names returns **zero** workforce ghosts (or only ones you are about to delete).

> **Double-check:** If you already have the split, fix config first (Task 1), then repair cubes (Task 3a) before trusting Task 2’s re-agg as “done.”

### Task 3a — Repair split / duplicate cubes (only if Task 3 found ghosts)

This is classic **19** remediation — not “create identity to clean the list.”

1. Confirm create-identities / authoritative is **off** on every non-Workday app; fix CorrelationConfig AttributeAssignments (Task 1b step 6)
2. On the **good** cube (`helen.ross`): note which apps are missing
3. On the **ghost** cube (`Helen Ross`): note which apps landed there (usually OpenLDAP / AD)
4. Prefer **uncorrelate** the ghost’s accounts, then **delete** the empty ghost identity — do **not** leave two people for one human
5. Optional advanced: Identity merge (Debug / merge tooling) ghost → `helen.ross` if your build supports it cleanly
6. Re-aggregate the affected apps in Task 2 order so accounts re-attach via `employeeNumber` → `userId`

- **Why:** correlation only runs for accounts being aggregated; a Link already glued to the wrong cube stays there until you break that link or merge.
- **Expect:** Warehouse has a single `helen.ross` (and peers) with all intended app links; ghost display-name identities are gone; identity **count** does not spike after re-agg.

### Task 4 — Sweep Uncorrelated Accounts (classic 19 dispositions + Sev-1)

Open **Identities → Uncorrelated Accounts** (or each Application’s uncorrelated list).

Treat unexplained hits for seeded personas as bugs. Every residual lands in **exactly one** disposition — “TBD” is not allowed for Sev-1.

| Disposition | When | Action |
| --- | --- | --- |
| **Correlate** | Valid Workday person exists; key mismatch / typo / rule gap | Fix data or manual correlate with associate-key proof |
| **Disable** | No valid owner; terminated vendor; stale ID | Disable in source / flag app owner; track ticket |
| **Exception** | Break-glass or service account pending vaulting | Owner + review date + compensating control — never forever |

**Privileged residuals are Sev-1** (classic 19): uncorrelated `WIRE_*`, core-banking privileged, `AWS_ADMIN`-class, break-glass → triage within **24h**, close within **5 business days** (lab: same session). Soft CRM/directory residuals are Sev-2/3.

| Temptation | Why it fails exam |
| --- | --- |
| Create identity from privileged orphan | Ghost cube; no HR leaver; certs attest fiction |
| Leave Sev-1 “for next sprint” | No age/disposition evidence when sampled |
| Exception with no review date | Permanent unowned access with a form attached |

- **Why:** uncorrelated privileged access is a control metric, not UI clutter — classify → act → evidence.
- **Expect:** zero unexplained hits for Helen / Priya / Marcus; any privileged leftover has Correlate|Disable|Exception + ticket note under evidence.

### Task 5 — Break and heal one JDBC correlation (classic 19 loop)

Deliberately break Helen’s Core Banking link, then repair it — prove you can diagnose orphans without minting cubes.

```bash
docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps -c \
  "update mnb_app_accounts set employee_id='BOGUS' where username='helen.ross';"
```

1. Re-aggregate `MNB-CoreBanking`
2. Confirm Helen’s Core Banking link is uncorrelated (or gone from her cube)
3. Restore:

```bash
docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps -c \
  "update mnb_app_accounts set employee_id='MNB00001' where username='helen.ross';"
```

4. Re-aggregate `MNB-CoreBanking` again

- **Why:** this is the classic 19 repair loop on a live target — ops proof you can diagnose orphans.
- **Expect:** uncorrelated after break; self-heals after fix. Note Task Result timestamps under evidence.

> **Tip:** If the container name differs, run `docker ps --format '{{.Names}}'` and substitute.

> **Watch out:** Test Connection is not aggregation. A broken row will not show as uncorrelated until you run a full Account Aggregation.

### Task 6 — Confirm manager hierarchy (classic 05 / 06 / 21)

Account correlation attaches apps. **Manager correlation** builds the org chart managers, approvals, and certifiers trust (Lessons **218** movers, **226** manager certs).

1. On `MNB-Workday`, confirm **Manager attribute** (schema / manager setting) points at the HCM manager ref (`managerId` in this estate)
2. Confirm Manager Correlation (or equivalent) matches that ref to identity **`userId`** (Searchable — same Task 1a attribute)
3. Run Identity Refresh with **manager correlation / refresh manager** enabled (classic `Refresh MNB Managers` pattern — purpose-built, not every checkbox)
4. Open `priya.wire`

| Situation | Risk | Response |
| --- | --- | --- |
| Exec / chain top, empty manager ref | Intentional — chain must end | No defect |
| Mid-level blank or unresolved `managerId` | Certs / approvals stall (“no certifier”) | Defect to HR; temporary **fallback certifier** + SLA — never permanent `spadmin` dump |
| Manager terminated; HR still points at them | Open certs route to inactive identity | Fallback + HR correction |

- **Why:** manager blank after a clean account-correlation pass usually means the manager’s Workday row wasn’t aggregated, Searchable `userId` was missing, or you never ran the managers refresh — not “Priya has no manager in HR.”
- **Expect:** manager resolves to `sanjay.kapoor` (`MNB00006` per identity master), not blank and not a raw id string.

> **Watch out:** Do **not** add Identity Mapping Attribute Source `manager` ← account display-name column. That classic-05 anti-pattern creates empty display-name cubes. Do **not** invent a permanent manager on the cube — HR owns `managerId`; next Workday agg overwrites fiction.

> **Tip:** Exec tops with empty `managerId` / `managersAssociateID` can be intentional. Blank manager on a mid-level Wire specialist like Priya is a broken chain.

### Task 7 — Evidence note: login ≠ correlation

Under `~/iiq-lab-evidence/sandbox/214/`, write one sentence explaining why the login key must not be the correlation key.

- **Why:** forces the design rule into ops language you’ll reuse in every connector review.
- **Expect:** something like: username may reissue; `employeeNumber` / `userId` must not for the employment relationship.

## If it fails

| Symptom | Fix |
| --- | --- |
| No `id` under Correlation → Identity Attribute | Expected — schema `identityAttribute` is not that dropdown. Use cube `userId` (Task 1a) |
| No `userId` in Correlation Identity Attribute list | Create Searchable `userId` in Identity Mappings; source from Workday `id`; refresh; reopen app |
| `userId` in Debug but missing on Attributes tab | Append `userId` to UIConfig `identityViewAttributes` (Task 1a-bis XML) |
| CorrelationConfig exists but is empty XML | Add AttributeAssignments; confirm Filters in Debug (Task 1b step 6) |
| Correlation dropdown “sets” then clears / Add inserts blank row | Click **Add** before Application Save; if stub config stays empty, import CorrelationConfig XML and select that existing config (Task 1a Watch out) |
| `employeeId-corr` / `employeeId` never gain AttributeAssignments | Abandon the empty stub — import a new named CorrelationConfig with Filters, point the app at it |
| AD-Live mints `Helen Ross` cubes (one AD link, no `userId`) | Wrong CorrelationConfig: app points at JDBC map `userId`←`employee_id`. Use `employeeNumber`→`userId`. Also Samba must have `employeeNumber` populated (`seed-samba.sh`) |
| AD correlation still fails after correct config | `ldapsearch` Helen — if no `employeeNumber`, re-run `./tools/lab/enterprise/seed-samba.sh` |
| Duplicate cubes (`helen.ross` + `Helen Ross`) with apps split | Empty/wrong correlation + create-identities minted `cn` ghosts — Task 3a |
| Transient orphans after reverse-order agg | Re-run Task 2 in documented order |
| Broken JDBC row not showing uncorrelated | Force a full Account Aggregation — Test Connection is not enough |
| Manager blank / raw id after refresh | Re-aggregate `MNB-Workday`; run managers refresh; confirm `managerId` → Searchable `userId` |
| Empty cubes named like people, no Application Accounts | Classic manager display-name mapping or directory create-identities — delete ghosts; fix config |
| Correlation saved but links never attach | Cube `userId` still empty — re-run Identity Refresh after Task 1a, then re-aggregate the target |
| Identity title/email flips after directory agg | Target attrs promoted onto cube — unmap; Workday owns lifecycle attrs (classic 22) |
| No cubes at all | Finish Lesson **207** first — this lesson correlates onto existing Workday identities |
| Temptation to create identity from privileged orphan | Reject — use Correlate / Disable / Exception (Task 4), never mint ghosts |

## You are done when

- [ ] Searchable cube `userId` exists and appears in Correlation’s Identity Attribute list
- [ ] `userId` visible on View Identity → Attributes (UIConfig `identityViewAttributes` updated)
- [ ] CorrelationConfigs have real AttributeAssignments (not empty named stubs)
- [ ] One cube per persona — no `Helen Ross` / `Priya Mehta` style ghosts splitting apps
- [ ] All three personas show correlated links across every live app they should have
- [ ] You’ve broken and repaired one JDBC correlation by hand
- [ ] `priya.wire`’s manager resolves to `sanjay.kapoor` after managers refresh
- [ ] Evidence note explains login key ≠ correlation key

## Control note

- **Control:** Account correlation integrity (no unexplained orphans / duplicate cubes)
- **Owner:** IAM Ops
- **SLA (lab):** fix deliberate break same session; production orphan triage often ≤1 business day
- **Evidence:** `~/iiq-lab-evidence/sandbox/214/` — Task Result ids, before/after uncorrelated screenshots, ghost cleanup note if Task 3a ran

## Quick check

1. Which attribute on Samba must match Workday `userId`? → `employeeNumber`
2. Why aggregate Workday first? → cubes must exist before other apps can correlate
3. What’s the wrong correlation key on OpenLDAP? → `uid` (login), not `employeeNumber`
4. Why isn’t Workday schema `id` in Correlation → Identity Attribute? → that dropdown is cube attrs; map to `userId` (promote from Workday `id`)
5. `userId` in Debug but blank on Attributes — what XML key? → UIConfig `identityViewAttributes`
6. `helen.ross` has Workday, `Helen Ross` has OpenLDAP — root cause? → failed/empty correlation + create-identities minted a `cn` ghost
7. Aggregation vs Refresh — which promotes `id` → cube `userId`? → Identity Refresh (with promote attributes)
8. Why is a false merge worse than a false orphan? → wrong person owns access; orphan is visible and remediable
9. Manager correlation uses which cube attribute as the match target? → Searchable `userId` (never display-name `manager`)
10. Three uncorrelated dispositions? → Correlate / Disable / Exception — Sev-1 privileged never “TBD”
11. Broken mid-level manager chain — wrong fix? → Permanent spadmin dump; use named fallback + HR SLA

## Feedback

Could you name the six correlation keys without opening the table? If orphans appeared after reverse-order agg, note whether a second pass in Workday-first order cleared them. If you minted display-name duplicates, note whether CorrelationConfig XML was empty when you checked Debug — and whether Task 3a left identity count stable after cleanup. If a privileged uncorrelated row lingered, note which disposition + ticket you chose — classic 19 Sev-1.

## Navigate

- Previous: [Lesson 213](213-gitea-sso-app.md)
- Next: [Lesson 215](215-attribute-sync-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md) · Theory: [256 Connector Registry](256-connector-registry-theory.md)
