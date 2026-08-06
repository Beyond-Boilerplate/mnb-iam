# Lesson 10 — Entitlement Dictionary & Managed Attributes

| Field | Value |
| --- | --- |
| **Level** | Beginner |
| **Track** | Applications |
| **Time** | 60 minutes |
| **Prereq** | Lesson 09 (`MNB-IT-Access` aggregated; entitlements present) |
| **Lab data** | `~/iiq-lab-data/reference/entitlement-dictionary.csv`, `sod-matrix.csv` |

## Learning objectives

You will be able to:

- Use the Meridian entitlement dictionary as the business source of display names and risk
- Enrich managed attributes / entitlement catalog entries in IIQ for five critical codes
- Manually pull or create a missing catalog entry via Debug's `ManagedAttribute` object editor when aggregation didn't materialize it
- Mark requestable vs. tightly controlled entitlements
- Assign conceptual business owners for wire, SAP, AWS, and core banking access
- Capture evidence a manager could actually use during a certification

## Why this matters

If entitlements stay opaque codes, managers rubber-stamp certifications. "Approve `WIRE_INIT`?" means nothing to a branch manager. "Approve Wire Portal — Initiate (create wire instructions)?" is a real control decision they can actually make. Risk tiers also drive which campaigns run first when Payments Ops has limited review bandwidth.

> **Production reality.** Real banks maintain this business glossary in a governed IGA/GRC catalog or a business-glossary tool — not a spreadsheet someone edits under exam pressure. The `entitlement-dictionary.csv` in this lab plays that role: it's the single source of truth that IIQ enrichment must mirror, exactly the way a production entitlement-catalog governance process would sync from a change-controlled glossary into the Entitlement Catalog. Lesson 44 (App Owner Certifications) builds on this owner map when certification campaigns need a human to escalate to.

**Control / audit:** Examiners ask whether reviewers see business-meaningful access descriptions and whether privileged entitlements are non-requestable. Managed attribute metadata is the evidence — codes alone are not.

## Concepts

**Managed attributes** (entitlement catalog entries) carry governance metadata on top of raw connector values. When Account Aggregation runs with `itAccess` marked as both **entitlement** and **managed** (and **Promote managed attributes** enabled on the task — Lesson 09), it **promotes** each distinct group/value into a `ManagedAttribute` object automatically. `entitlement` alone puts codes on Links/cubes; **`managed` is what fills the Entitlement Catalog**. When a code is missing from the catalog — schema not managed/entitlement-typed, promote off, or you need an entry before the next aggregate — you pull it in manually through Debug's object editor instead of waiting.

| Metadata | Purpose | Meridian example |
| --- | --- | --- |
| Display name | Human review | Wire Portal — Initiate |
| Description | What it does | Create wire instructions |
| Risk | Campaign / SoD priority | critical |
| Owner | Accountable business/IT owner | `rachel.evans` (wire) |
| Requestable | Appears in access request catalog | CRM yes; AWS_ADMIN no |

```text
  entitlement-dictionary.csv (business SoT)
        |
        +--> Aggregate MNB-IT-Access  --> ManagedAttribute (auto, preferred)
        |
        +--> Debug ManagedAttribute   --> ManagedAttribute (manual pull/create, alternate)
        |
        v
  Enrich managed attributes in IIQ
        |
        +--> Certifications (readable)
        +--> Access requests (requestable flags)
        +--> SoD / risk scoring (later)
```

**Dictionary extract (critical subset):**

| code | name | risk |
| --- | --- | --- |
| WIRE_INIT | Wire Portal — Initiate | critical |
| WIRE_APPR | Wire Portal — Approve | critical |
| SAP_FI | SAP Finance | critical |
| AWS_ADMIN | AWS Admin | critical |
| CORE | Core Banking (AS400) | critical |
| PRIV_BREAK | Break-Glass Admin | critical |
| ELDAP | Enterprise Directory | medium |

**Owner map (conceptual):**

| Entitlement | Owner persona | Dept |
| --- | --- | --- |
| WIRE_INIT / WIRE_APPR | `rachel.evans` | TRS |
| SAP_FI / GL_POST | `deepa.nair` | FIN |
| AWS_ADMIN | `christopher.hayes` | ITP |
| CORE | `daniel.griffin` | OPS |
| ELDAP | `christopher.hayes` / directory admin | ITP |

## How it works

Raw connector values (`WIRE_INIT`) are opaque to managers. **Managed attributes** add display name, description, owner, risk, and requestable flags so certifications and access requests are human-readable and owned. Aggregation is the normal factory; Debug's `ManagedAttribute` editor is the manual intake valve for the rare case a group must exist in the catalog before the next aggregate runs.

```text
entitlement-dictionary.csv (business SoT)
        │
        ▼
Managed Attribute / entitlement enrichment in IIQ
        │
        ├── Display + description → cert UI
        ├── Owner → escalation / app-owner campaigns
        ├── Risk → scoring & campaign priority
        └── Requestable → access request catalog
```

| Metadata | If missing | Bank consequence |
| --- | --- | --- |
| Owner | Orphan privilege | No cert/escalation owner |
| Risk | Flat campaigns | Critical buried with `ELDAP` |
| Description | Rubber-stamp reviews | Weak evidence for audit |
| Requestable=false on admin | Self-service `AWS_ADMIN` | Privilege sprawl |

**Real-life Meridian example.** `rachel.evans` owns `WIRE_INIT`/`WIRE_APPR`. When a manager certifies `priya.wire`, the dictionary-backed display "Wire Portal — Initiate" makes the decision defensible — not the raw code alone. If `WIRE_INIT` never appeared in the catalog after aggregation, Ops would use Debug's `ManagedAttribute` editor to pull the group in, then enrich from the dictionary — not invent a second shadow spreadsheet.

## Before you start

- [ ] `Aggregate MNB-IT-Access` completed
- [ ] Dictionary CSV open beside the browser
- [ ] Evidence folder ready

## Lab procedure

### Task 1 — Load the dictionary beside the UI

Treat the CSV as the business source of truth — IIQ enrichment should mirror it, not invent display names under pressure.

1. Open it:

```bash
column -s, -t < ~/iiq-lab-data/reference/entitlement-dictionary.csv | less -S
```

2. Keep `sod-matrix.csv` available for risk context.
3. Highlight every `risk=critical` row in your notebook.

**Expected result:** A working list of codes you will enrich today.

### Task 2 — Find managed attributes in IIQ (primary path)

1. Navigate to the entitlement / managed attribute UI (often **Applications** → `MNB-IT-Access` → Accounts/Entitlements, or **Global Settings** / **Entitlement Catalog** — path varies by build).
2. Search for `WIRE_INIT` (or open via `jordan.reed` / `priya.wire`'s entitlement link → catalog entry).
3. Confirm the raw value exists from aggregation.

**Expected result:** You can open at least one managed attribute object for an `itAccess` value.

**If it fails:** Confirm `itAccess` is **entitlement and managed** on `MNB-IT-Access` (Lesson 09); enable Promote managed attributes; re-aggregate. If cubes show codes but the catalog is still empty, the usual miss is `managed="true"` never set. If you need the entry now, use Task 2b instead of waiting on a re-aggregate.

### Task 2b — Manually pull a group via Debug (alternate path)

Aggregation is preferred, but every IIQ engineer should know how to manually create or fetch a `ManagedAttribute` when a group is missing from the catalog. Use `spadmin` in lab only — treat production catalog creates as change-controlled, not a self-service fix.

1. Open **Debug** → Object Browser (or equivalent) → type **`ManagedAttribute`**.
2. Search by value `PRIV_BREAK` or application `MNB-IT-Access`. If missing, choose **New** / create.
3. Set at minimum:
   - Application: `MNB-IT-Access`
   - Attribute: `itAccess` (the entitlement attribute name)
   - Value: `PRIV_BREAK` (a dictionary code you can prove)
   - Display name / description from `entitlement-dictionary.csv`
4. Save. Re-open in the Entitlement Catalog UI and confirm it appears.
5. CHANGELOG: `ManagedAttribute created via Debug for PRIV_BREAK`.

**Expected result:** One ManagedAttribute opened or created via Debug; you can explain "aggregation vs. manual Debug pull" in one sentence.

**If it fails:** Capability missing → use `spadmin`. Duplicate value error → the object already exists, search instead of create. Never mass-create catalog entries that aren't in the Meridian dictionary — Lesson 100 covers REST/console automation for that once you're past manual repair.

### Task 3 — Enrich five core entitlements

For each of `WIRE_INIT`, `WIRE_APPR`, `SAP_FI`, `AWS_ADMIN`, `ELDAP`:

1. Set **display name** from the dictionary `name` column.
2. Set **description** from the dictionary `description` column.
3. Set or note **risk** if your UI supports risk levels/tags (otherwise record risk in your notebook for later policy use).
4. Save.

**Expected result:** Five entitlements show business-readable names in the UI.

### Task 4 — Requestable flags

1. Mark **requestable** (or equivalent catalog flag): `CRM`, `DWRP` (and optionally `ODS` if present in aggregated data).
2. Mark **not requestable** / tightly controlled: `AWS_ADMIN`, `PRIV_BREAK`, `WIRE_INIT`, `WIRE_APPR`, `CORE`, `SAP_FI`.
3. Document the rule: "Critical payment and admin entitlements are requestable only via break-glass or a privileged process — never self-service."

**Expected result:** Written requestable vs. non-requestable lists matching Meridian's risk posture.

### Task 5 — Owner assignment

> **Watch out:** Changing a ManagedAttribute owner can trigger an "Update Account Group" LCM workflow. The Task Result may sit at **Approval** with a work item owned by the **entitlement owner** (e.g. `MNB00003` / `rachel.evans`) — **not** `spadmin` — so it won't show up in the spadmin inbox. Set a password on the owner identity and approve under **My Work**, or **Forward** the work item to `spadmin` first. Don't treat a stuck Approval step as a failed aggregation.

1. On wire entitlements, set owner to `rachel.evans` if the UI allows identity owners; otherwise record owners in the binder as the system of record until app-owner fields are wired.
2. Assign the remaining conceptual owners: `deepa.nair` → SAP_FI; `christopher.hayes` → AWS_ADMIN; `daniel.griffin` → CORE.
3. Note the control: owners who leave the bank break certifications — keep owners current (ties into the leaver process later).
4. If a Task Result shows Pending Approval after saving, resolve it via the owner's work item (or forward to spadmin), then continue.

**Expected result:** Owner map recorded; at least one owner set in IIQ if supported; any owner-change approvals completed or documented.

### Task 6 — Manager readability test

1. View `WIRE_INIT` as a reviewer would see it (catalog / entitlement details).
2. Write one sentence a branch/payments manager would actually understand.
3. Screenshot the enriched entitlement for evidence.

**Expected result:** Screenshot + sentence, e.g. "Allows creating wire payment instructions; requires dual control with a separate approver."

### Task 7 — Align with the SoD matrix

1. For each `sod-matrix.csv` pair, confirm both entitlements are enriched or queued for enrichment.
2. Note `PRIV_BREAK` for Lesson 37 if you have time to look ahead.

**Expected result:** A checklist confirming SoD pair codes have dictionary coverage.

### Task 7b — Bank craft exit (catalog metadata)

Durable entitlement metadata belongs in git once your build exports ManagedAttributes (or document enrichment in the binder until export is practical). At minimum, CHANGELOG the five enriched codes and note `config/` as the source of truth for the Application/TaskDefinition that produce those ManagedAttributes.

**Expected result:** Binder lists the codes plus "ManagedAttribute enrichment applied; Application = MNB-IT-Access."

## Acceptance criteria

- [ ] Dictionary critical list in notebook
- [ ] At least five entitlements enriched (name + description)
- [ ] Debug `ManagedAttribute` alternate path practiced (list or create at least one group)
- [ ] Requestable vs. non-requestable lists documented
- [ ] Owner map recorded (wire/SAP/AWS/core)
- [ ] Evidence screenshot of an enriched entitlement
- [ ] CHANGELOG updated

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Entitlement not in catalog | Not aggregated / not entitlement **or not managed** / promote off | Set `entitlement` + `managed` on `itAccess` (Lesson 09); enable Promote managed attributes; re-run `Aggregate MNB-IT-Access`; or use Task 2b |
| Codes on cubes, catalog empty | `entitlement` without `managed` | Add `managed="true"`; re-aggregate (there's no separate entitlement aggregation task) |
| Cannot edit managed attribute | Missing capability | Use `spadmin`; check capabilities |
| Names revert | Re-agg overwrites without a promotion strategy | Re-apply; note connector refresh behavior for your version |
| Owner field missing | Edition/UI difference | Keep the binder as system of record; set at application level |
| Task Result stuck at Approval after owner change | LCM work item assigned to the entitlement owner, not spadmin | Log in as owner (set password) → My Work → Approve; or forward the work item to spadmin then approve |
| Managers still see codes | Display name not set / wrong locale | Confirm the display name field; re-open the cert preview later |
| Duplicate ManagedAttribute | Manual create when aggregation already promoted it | Search first; delete the duplicate carefully in lab only |

## Training binder evidence

- Screenshot: enriched `WIRE_INIT` (name + description)
- Note or screenshot: Debug `ManagedAttribute` pull (object id or value)
- Requestable vs. non-requestable table
- Owner map
- Note tying critical risk to certification priority

**Ops note:** "How does a missing group get into the catalog without waiting for a full re-aggregate?" is a fair question from any new hire — the answer is Task 2b, documented and change-controlled.

## Knowledge check

1. Why do display names matter in certifications?
2. Which entitlements should never be self-requestable?
3. Who should own `WIRE_APPR`?
4. What risk tier is `ELDAP` in the dictionary?
5. What Meridian file is the source of truth for entitlement descriptions?
6. How can you manually pull a group into IIQ if aggregation didn't create the ManagedAttribute?

### Answers

1. Reviewers must understand business impact; opaque codes drive rubber-stamping.
2. Privileged/critical ones: `AWS_ADMIN`, `PRIV_BREAK`, `CORE`, wire dual-control entitlements, `SAP_FI` (per Meridian posture).
3. `rachel.evans` (Payments Operations Manager, TRS).
4. Medium.
5. `reference/entitlement-dictionary.csv`.
6. Through Debug's `ManagedAttribute` object editor — search or create the value, set application/attribute/value/display fields, save, then enrich from the dictionary.

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search "managed attribute" for enrichment fields and owner configuration.
- [SailPoint Community](https://community.sailpoint.com/) — search "entitlement owner certification" for app-owner campaign prerequisites.
- [NIST SP 800-53 AC-2 / AC-6](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) — documenting and limiting privileges with accountable owners.
- [FFIEC IT Examination Handbook — Information Security](https://ithandbook.ffiec.gov/it-booklets/information-security.aspx) — privileged access inventories and business ownership.
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) — least privilege and clear privilege meaning for reviewers.

## Stretch lab

- Enrich `PRIV_BREAK` with a strongly worded description and non-requestable flag (create it via Debug if missing).
- Enrich all `risk=high` entitlements (`IBSI`, `ECOM`, `AML_CASE`, `GL_POST`).
- Draft a change ticket template for "new entitlement code added to Meridian dictionary + IIQ catalog."
- If your build exposes console/REST access to `ManagedAttribute`, script a one-shot check that every `risk=critical` dictionary code exists as a ManagedAttribute on `MNB-IT-Access` — Lesson 100 goes deeper on REST/SCIM automation.

## Summary

- Managed attributes turn raw codes into reviewable, ownable access objects.
- The Meridian dictionary drives display names, risk, and requestability; aggregation creates the objects when `itAccess` is entitlement **and** managed with promote on — Debug's `ManagedAttribute` editor is the manual fallback when you can't wait for the next aggregate.
- Enriched entitlements are prerequisites for credible certifications and access requests.

## Feedback

Could you enrich `WIRE_INIT` from the dictionary and state why critical wire entitlements are non-requestable — without looking? If an owner change left a stuck approval, note the **work-item owner** (often Rachel / Deepa, not `spadmin`) — that is the lesson.

---

**Previous:** [Lesson 09 — Onboard IT Access Inventory App](09-it-access-inventory-app.md)  
**Next:** [Lesson 11 — Onboard Core Banking Extract](11-onboard-core-banking.md)
