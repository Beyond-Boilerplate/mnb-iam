# Lesson 70 — SCIM Custom Schemas

**Level:** Intermediate  
**Track:** Connectors — Web APIs & SaaS  
**Time:** 90–120 min  
**Prereq:** Lesson 69 — SCIM 2.0 Connector (`MNB-SCIM-SaaS`, `Users.json`)  

**Lab data:**
- Repo: `lab-data/connectors/scim/Users.json` (extend in lab notes)
- Repo: `lab-data/connectors/features-string-glossary.md`
- Runtime: `~/iiq-lab-data/connectors/scim/`

---

## Learning objectives

You will be able to:

- Distinguish SCIM **core**, **enterprise**, and **vendor/Meridian extension** schemas
- Design Meridian extension attributes (`costCenter`, `mnbRiskTier`, `businessUnit`) without breaking core User
- Author a valid extended JSON fixture from `Users.json` and map it into **MNB-SCIM-SaaS** (or `MNB-SCIM-Ext`)
- Produce an aggregation checklist (live or Shadow) that proves custom attributes survive the round-trip
- Document examiner impact: custom attrs in certifications, SoD selectors, and promotion residual risk

---

## Why this matters

**Business.** SaaS tenants rarely stop at `userName` and email. Meridian certifications and birthright rules need **cost center** and **risk tier** on the account (and sometimes the cube). When SCIM extensions exist, you should not fork a full Web Services project just to fetch three fields.

**Control / audit.** Custom attributes become control data. Examiners ask where `mnbRiskTier` is sourced and whether aggregation preserves it. Schema maps and sample payloads are the proof — inventing attributes only in IIQ with no target representation fails evidence review.

---

## Concepts

### Three layers of SCIM schemas

| Schema URN | Purpose | Examples |
| --- | --- | --- |
| `urn:ietf:params:scim:schemas:core:2.0:User` | Core User | `userName`, `emails`, `active`, `externalId` |
| `urn:ietf:params:scim:schemas:extension:enterprise:2.0:User` | Enterprise extension | `department`, `manager`, `costCenter` (standard) |
| Vendor / Meridian URN | Product or bank-specific | `mnbRiskTier`, bank-only flags |

**Rule:** Never overwrite core mappings when adding extensions. Extensions are additive objects keyed by their URN on the same User resource.

### Why extensions exist

Core User is intentionally small for interoperability. Banks need governance fields vendors never standardized. Two honest paths:

1. Use **enterprise:2.0:User** where it already defines the field (`department`, often `costCenter`).
2. Define a **Meridian extension** for bank-only semantics (`mnbRiskTier`) — and get vendor support (or accept account-only lab design).

Naive path: stuff `mnbRiskTier` into `title` or `displayName`. That breaks reporting, confuses helpdesk, and fails examiner “source of truth” questions.

### Lab baseline vs gaps

Lesson 69 `Users.json` has core only. Gaps Meridian cares about: `department`, `costCenter`, `mnbRiskTier`, `businessUnit`.

```
User resource
  schemas: [core, enterprise, urn:meridian:params:scim:schemas:extension:1.0:User]
  userName / emails / active / externalId   ← core (do not break)
  department / manager                      ← enterprise
  mnbRiskTier / costCenter / businessUnit   ← Meridian extension (lab)
```

---

## How it works

A SCIM User JSON carries multiple schema URNs. Extension attributes live under a nested object named by the extension URN (or a shortened key per vendor — **always match the vendor payload**). The IIQ SCIM connector maps those paths into account attributes; optional identity attribute sync promotes them to the cube (Lesson 22 hygiene — document before enabling).

```
GET /Users/{id}
{
  "schemas": ["…core:2.0:User", "…enterprise:2.0:User", "urn:meridian:…:1.0:User"],
  "userName": "priya.wire",
  "externalId": "MNB00090",
  "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User": {
    "department": "Wire Operations"
  },
  "urn:meridian:params:scim:schemas:extension:1.0:User": {
    "mnbRiskTier": "high",
    "costCenter": "WIRE-OPS",
    "businessUnit": "Payments"
  }
}
```

| Layer | IIQ mapping focus | Cert / policy use |
| --- | --- | --- |
| Core | Correlation + ENABLE | Leaver disable |
| Enterprise | Org context | Manager / dept filters |
| Meridian ext | Risk / CC | Targeted certs, SoD selectors |

---

## Real-world setup (outside IIQ)

### Step 1 — Vendor capability check

1. Ask: which extension URNs does the tenant support? Enterprise only? Custom schema admin UI?
2. Do **not** invent a Meridian URN in production without vendor confirmation — map to supported extensions instead.
3. Record residual risk if lab URN ≠ vendor URN (`RR-SCIM-EXT-01`).

### Step 2 — Governance dictionary

1. Define allowed `mnbRiskTier` values: `low` / `medium` / `high` / `critical`.
2. Assign data owner (Risk) and technical owner (IAM `helen.ross`).
3. Change-control any cert filter or SoD selector that consumes these fields.

### Step 3 — Promotion rules

1. Sandbox first: account attributes only.
2. Promote identity sync only after correlation and aggregation are stable.
3. Document which attrs are safe sandbox → prod.

### Step 4 — Keep core stable

Regression test Lesson 69 attributes after every schema change — core breakage is the most common extension accident.

---

## Before you start

- [ ] Lesson 69 `MNB-SCIM-SaaS` shell exists (or recreate)
- [ ] `Users.json` available to copy/extend under `~/iiq-lab-data/connectors/scim/`
- [ ] HR department concepts from earlier lessons known
- [ ] JSON validator available (`python3 -m json.tool`)

---

## Lab procedure

### Task 1 — Baseline core map and gap list

Extensions only make sense when core is solid.

1. Re-open `~/iiq-lab-data/connectors/scim/Users.json`.
2. List core attributes already mapped in Lesson 69: `id`, `userName`, `emails`, `active`, `externalId`, names.
3. Gap list (≥3): `department`, `costCenter`, `mnbRiskTier` (add `businessUnit`).

**Expected result:** Written gap list before editing JSON.

### Task 2 — Design Meridian extension dictionary

1. Extension URI (lab-only): `urn:meridian:params:scim:schemas:extension:1.0:User`.
2. Attributes:

| Attribute | Type | Allowed values / notes |
| --- | --- | --- |
| `costCenter` | string | e.g. `WIRE-OPS`, `WIRE-CTRL` |
| `mnbRiskTier` | string | low / medium / high / critical |
| `businessUnit` | string | e.g. Payments |

3. Also plan enterprise: `department` under enterprise URN.
4. Owners: Risk for tier semantics; IAM for connector mapping.

**Expected result:** Extension attribute dictionary page.

**If it fails:** Keep names simple; avoid IIQ-reserved collisions.

### Task 3 — Author extended fixture from Users.json

This is the lab-without-live-target golden payload.

1. Copy `Users.json` → `~/iiq-lab-data/connectors/scim/Users-extended.json`.
2. For each Resource, extend `schemas` to include enterprise + Meridian URNs.
3. Set:

| userName | department | costCenter | mnbRiskTier | businessUnit |
| --- | --- | --- | --- | --- |
| `priya.wire` | Wire Operations | WIRE-OPS | high | Payments |
| `marcus.approve` | Wire Controls | WIRE-CTRL | critical | Payments |

4. Validate:

```bash
python3 -m json.tool ~/iiq-lab-data/connectors/scim/Users-extended.json >/dev/null
```

5. Keep under `~/iiq-lab-data` if repo policy blocks committing lab-only URNs.

**Expected result:** Valid extended fixture; `marcus.approve` is `critical`.

**If it fails:** Fix commas/brackets; minimal valid JSON first, then add fields.

### Task 4 — Map into IIQ application

1. Open `MNB-SCIM-SaaS` (or clone as `MNB-SCIM-Ext` to preserve Lesson 69 baseline).
2. Add account attributes for enterprise `department` and Meridian extension fields.
3. Document identity sync intent (account-only until Lesson 22 pattern applied).
4. Confirm core mappings still present — regression check.
5. Save schema.

**Expected result:** Schema shows custom attributes; core intact.

**If it fails:** Restore core User mappings first; re-add extensions.

### Task 5 — Aggregation checklist (live or Shadow)

1. Checklist:

| Step | Expected result |
| --- | --- |
| Test Connection | Success (live) or N/A Shadow |
| Account Aggregation | 2 accounts |
| Spot-check `priya.wire` | `mnbRiskTier=high`, `costCenter=WIRE-OPS` |
| Spot-check `marcus.approve` | `mnbRiskTier=critical` |
| Core regression | `externalId` / `active` still populated |

2. Shadow path: CSV including new columns; DelimitedFile shadow; aggregate.
3. Record actual results after dry-run.

**Expected result:** Checklist completed with evidence notes.

### Task 6 — Cert / SoD impact note

1. Targeted cert idea: filter holders where `mnbRiskTier=critical` (Marcus story).
2. Warn: custom attrs in policies need change control — silent schema edits break campaigns.
3. SoD selectors must use stable codes (`critical`), not free-text.

**Expected result:** One paragraph for Risk/IAM architecture board.

### Task 7 — Promotion note and residual risk

1. List attrs safe to promote sandbox → prod (only those vendor supports).
2. Require vendor confirmation of Meridian URN **or** remap to vendor-supported extension.
3. Residual risk `RR-SCIM-EXT-01`: *Lab URN may not exist in vendor — map to vendor-supported extension in prod; until then treat tiers as account-only lab design.*
4. CHANGELOG: “Lesson 70 SCIM custom schemas / Users-extended.json.”

**Expected result:** Promotion checklist + RR + CHANGELOG.

### Task 8 — Binder packaging

1. Assemble `MNB-SCIM-Ext-Binder-YYYY-MM-DD` notes: dictionary, extended JSON excerpt for `priya.wire` only (minimize PII), before/after schema screenshots, aggregation checklist, cert/SoD paragraph, RR.
2. Examiner answer draft: *“`mnbRiskTier` is sourced from SCIM extension URN X, aggregated nightly, used in critical-tier targeted certs under change control.”*

**Expected result:** Dated binder package listed in notes.

---

## Acceptance criteria

- [ ] Extension URI and attribute dictionary defined
- [ ] `Users-extended.json` created and JSON-valid from `Users.json`
- [ ] IIQ schema map updated; core attributes regression-checked
- [ ] Aggregation checklist completed (live or Shadow) with tier spot-checks
- [ ] Cert/SoD impact note + promotion checklist + `RR-SCIM-EXT-01`

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Attribute blank after agg | Wrong schema URN / path | Match JSON extension object path to map |
| Core fields broke | Overwrote core schema | Restore core User mappings first |
| Invalid JSON | Trailing commas / brackets | `python3 -m json.tool` |
| Identity attr not updating | No sync configured | Account-only until sync designed |
| Vendor rejects extension | Tenant not configured | Fall back to enterprise only; keep RR |
| Cert filter empty | Typo in tier values | Enforce enum low/medium/high/critical |

---

## Training binder evidence

- Extension dictionary
- Extended JSON sample (`priya.wire` excerpt)
- Schema screenshot (core + extensions)
- Aggregation checklist with spot-checks
- Cert/SoD paragraph + promotion + RR

**Examiner question:** *“Where is mnbRiskTier sourced, and who change-controls campaigns that filter on it?”*

---

## Knowledge check

1. Name one standard SCIM enterprise schema use.
2. What lab extension URI did you choose for Meridian?
3. Which persona received `mnbRiskTier=critical` in the extended fixture?
4. Why separate extension schemas from core User?
5. What is the lab-without-live-target artifact for custom schemas?
6. What does `RR-SCIM-EXT-01` warn about?

### Answers

1. `department` / `manager` (enterprise:2.0:User) or similar enterprise fields.
2. `urn:meridian:params:scim:schemas:extension:1.0:User` (lab-only).
3. `marcus.approve`.
4. To preserve interoperability and version Meridian fields cleanly without breaking core.
5. Extended JSON fixture + IIQ attribute map / Shadow CSV.
6. Lab Meridian URN may not exist on the vendor — remap before prod sync.

---

## Further reading

- [RFC 7643 §4 — Enterprise User Schema Extension](https://datatracker.ietf.org/doc/html/rfc7643#section-4.3) — standard enterprise attributes before inventing bank fields.
- [RFC 7643 — defining extensions](https://datatracker.ietf.org/doc/html/rfc7643) — how schema URNs and extension attributes are intended to work.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “SCIM schema” / attribute mapping for connector field paths.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — custom SCIM attribute mapping threads.
- [NIST SP 800-53 AC-2 / AC-6](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) — account management / least privilege framing for risk-tiered access reviews.

---

## Stretch lab

Propose mapping enterprise `manager.value` to Meridian manager correlation for `sofia.torres` reports — document only; do not change production manager hierarchy. Draft a targeted certification definition that selects `mnbRiskTier=critical` on `MNB-SCIM-SaaS` using Lesson 45 patterns. Compare enterprise `costCenter` vs Meridian extension `costCenter` and pick one production home.

---

## Summary

- SCIM extensions carry Meridian governance attributes beyond core User without abandoning the SCIM connector.
- Extended fixtures unlock training when vendors are unavailable; core regression is mandatory.
- Custom attributes need change control because certifications and policies consume them — tracked as `RR-SCIM-EXT-01` until vendor URNs match.

---

**Previous:** [Lesson 69 — SCIM 2.0 Connector](69-scim2-connector.md)  
**Next:** [Lesson 71 — Salesforce Native Connector](71-salesforce-native-connector.md)
