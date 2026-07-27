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
- Enrich managed attributes / entitlement catalog entries in IIQ for key codes
- Mark requestable vs tightly controlled entitlements
- Assign conceptual business owners for wire, SAP, and AWS access
- Capture evidence that a manager could understand in a certification

## Why this matters

If entitlements remain opaque codes, managers rubber-stamp certifications. “Approve WIRE_INIT?” means nothing; “Approve Wire Portal — Initiate (create wire instructions)?” is a real control decision. Risk tiers also drive which campaigns run first.

**Control / audit:** Examiners ask whether reviewers see business-meaningful access descriptions and whether privileged entitlements are non-requestable. Managed attribute metadata is the evidence—codes alone are not.

## Concepts

**Managed attributes** (entitlement catalog entries) carry governance metadata on top of raw connector values:

| Metadata | Purpose | Meridian example |
| --- | --- | --- |
| Display name | Human review | Wire Portal — Initiate |
| Description | What it does | Create wire instructions |
| Risk | Campaign / SoD priority | critical |
| Owner | Accountable business/IT owner | rachel.evans (wire) |
| Requestable | Appears in access request catalog | CRM yes; AWS_ADMIN no |

```text
  entitlement-dictionary.csv
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
| WIRE_INIT / WIRE_APPR | rachel.evans | TRS |
| SAP_FI / GL_POST | deepa.nair | FIN |
| AWS_ADMIN | christopher.hayes | ITP |
| CORE | daniel.griffin | OPS |
| ELDAP | christopher.hayes / directory admin | ITP |

## How it works

Raw connector values (`WIRE_INIT`) are opaque to managers. **Managed attributes** add display name, description, owner, risk, and requestable flags so certifications and access requests are human-readable and owned.

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
| Risk | Flat campaigns | Critical buried with ELDAP |
| Description | Rubber-stamp reviews | Examiner rejects evidence quality |
| Requestable=false on admin | Self-service AWS_ADMIN | Privilege sprawl |

**Real-life Meridian example.** `rachel.evans` owns `WIRE_INIT`/`WIRE_APPR`. When a manager certifies `priya.wire`, dictionary-backed display “Wire Portal — Initiate” makes the decision defensible—not the raw code alone.

## Before you start

- [ ] `Aggregate MNB-IT-Access` completed
- [ ] Dictionary CSV open beside the browser
- [ ] Evidence folder ready

## Lab procedure

### Task 1 — Load the dictionary beside the UI

Treat the CSV as the business source of truth—IIQ enrichment should mirror it, not invent display names under exam pressure.

1. Open:

```bash
column -s, -t < ~/iiq-lab-data/reference/entitlement-dictionary.csv | less -S
```

2. Keep `sod-matrix.csv` available for risk context.
3. Highlight all `risk=critical` rows in your notebook.

**Expected result:** Working list of codes you will enrich today.

### Task 2 — Find managed attributes in IIQ

1. Navigate to entitlement / managed attribute UI (often **Applications** → `MNB-IT-Access` → Accounts/Entitlements, or **Global Settings** / **Entitlement Catalog** / Debug `ManagedAttribute`—path varies).
2. Search for `WIRE_INIT` (or open via `jordan.reed` / `priya.wire` entitlement link → catalog entry).
3. Confirm the raw value exists from aggregation.

**Expected result:** You can open at least one managed attribute object for an `itAccess` value.

**If it fails:** Re-aggregate; confirm `itAccess` is entitlement-typed on `MNB-IT-Access`; use Debug object search for `ManagedAttribute` as fallback.

### Task 3 — Enrich five core entitlements

For each of `WIRE_INIT`, `WIRE_APPR`, `SAP_FI`, `AWS_ADMIN`, `ELDAP`:

1. Set **display name** from dictionary `name`.
2. Set **description** from dictionary `description`.
3. Set or note **risk** if your UI supports risk levels/tags (else record risk in notebook for later policy use).
4. Save.

**Expected result:** Five entitlements show business-readable names in the UI.

### Task 4 — Requestable flags

1. Mark **requestable** (or equivalent catalog flag): `CRM`, `DWRP` (and optionally `ODS`) if present in aggregated data.
2. Mark **not requestable** / tightly controlled: `AWS_ADMIN`, `PRIV_BREAK`, `WIRE_INIT`, `WIRE_APPR`, `CORE`, `SAP_FI`.
3. Document rule: “Critical payment and admin entitlements are requestable only via break-glass or privileged process—not self-service.”

**Expected result:** Written requestable vs non-requestable lists matching Meridian risk posture.

### Task 5 — Owner assignment

1. On wire entitlements, set owner to `rachel.evans` if the UI allows identity owners; otherwise record owners in the binder as the system of record until app-owner fields are wired.
2. Assign conceptual owners: `deepa.nair` → SAP_FI; `christopher.hayes` → AWS_ADMIN.
3. Note control: owners who leave the bank break certifications—keep owners current (tie to leaver process later).

**Expected result:** Owner map recorded; at least one owner set in IIQ if supported.

### Task 6 — Manager readability test

1. View `WIRE_INIT` as it would appear to a reviewer (catalog / entitlement details).
2. Write one sentence a branch/payments manager would understand.
3. Screenshot enriched entitlement for evidence.

**Expected result:** Screenshot + sentence: e.g. “Allows creating wire payment instructions; requires dual control with a separate approver.”

### Task 7 — Align with SoD matrix

1. For each sod-matrix pair, confirm both entitlements are enriched or queued.
2. Note `PRIV_BREAK` for Lesson 37 (stretch if time).

**Expected result:** Checklist that SoD pair codes have dictionary coverage.

## Acceptance criteria

- [ ] Dictionary critical list in notebook
- [ ] At least five entitlements enriched (name + description)
- [ ] Requestable vs non-requestable lists documented
- [ ] Owner map recorded (wire/SAP/AWS)
- [ ] Evidence screenshot of enriched entitlement
- [ ] CHANGELOG updated

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Entitlement not in catalog | Not aggregated / not marked entitlement | Fix schema; re-run Aggregate MNB-IT-Access |
| Cannot edit managed attribute | Missing capability | Use spadmin; check capabilities |
| Names revert | Re-agg overwrites without promotion strategy | Re-apply; note connector refresh behavior for your version |
| Owner field missing | Edition/UI difference | Keep binder as SoR; set at application level |
| Managers still see codes | Display name not set / wrong locale | Confirm display name field; re-open cert preview later |

## Training binder evidence

- Screenshot: enriched `WIRE_INIT` (name + description)
- Requestable vs non-requestable table
- Owner map
- Note tying critical risk to certification priority

**Examiner question:** “Show how a manager sees wire initiate access during a certification—not just the code.”

## Knowledge check

1. Why do display names matter in certifications?
2. Which entitlements should never be self-requestable?
3. Who should own `WIRE_APPR`?
4. What risk tier is `ELDAP` in the dictionary?
5. What Meridian file is the source of truth for entitlement descriptions?

### Answers

1. Reviewers must understand business impact; opaque codes drive rubber-stamping.
2. Privileged/critical ones: e.g. `AWS_ADMIN`, `PRIV_BREAK`, `CORE`, wire dual-control entitlements, `SAP_FI` (per Meridian posture).
3. `rachel.evans` (Payments Operations Manager, TRS).
4. medium.
5. `reference/entitlement-dictionary.csv`.

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “managed attribute” and “entitlement catalog” for enrichment fields and owners.
- [SailPoint Community](https://community.sailpoint.com/) — search “entitlement owner certification” for app-owner campaign prerequisites.
- [NIST SP 800-53 AC-2 / AC-6](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) — documenting and limiting privileges with accountable owners.
- [FFIEC IT Examination Handbook — Information Security](https://ithandbook.ffiec.gov/it-booklets/information-security.aspx) — privileged access inventories and business ownership.
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) — least privilege and clear privilege meaning for reviewers.


## Stretch lab

- Enrich `PRIV_BREAK` with a strongly worded description and non-requestable flag.
- Enrich all `risk=high` entitlements (`IBSI`, `ECOM`, `AML_CASE`, `GL_POST`).
- Draft a change ticket template for “new entitlement code added to Meridian dictionary + IIQ catalog.”

## Summary

- Managed attributes turn raw codes into reviewable, ownable access objects.
- Meridian dictionary drives display names, risk, and requestability.
- Enriched entitlements are prerequisites for credible certifications and access requests.

---

**Previous:** [Lesson 09 — Onboard IT Access Inventory App](09-it-access-inventory-app.md)  
**Next:** [Lesson 11 — Onboard Core Banking Extract](11-onboard-core-banking.md)
