# Lesson 70 — SCIM Custom Schemas & Enterprise Attributes

**Level:** Intermediate  
**Track:** Connectors — Web APIs & SaaS  
**Time:** 60–75 min  
**Prereq:** Lesson 69 — SCIM 2.0 Connector  

**Lab data:**
- Repo: `lab-data/connectors/scim/Users.json` (extend in lab notes)
- Repo: `lab-data/connectors/features-string-glossary.md`
- Runtime: `~/iiq-lab-data/connectors/scim/`

---

## Learning objectives

You will be able to:

- Identify SCIM core vs enterprise vs vendor extension schemas
- Design Meridian extension attributes (`department`, `costCenter`, `mnbRiskTier`) on a SCIM app
- Update **MNB-SCIM-SaaS** (or `MNB-SCIM-Ext`) schema maps for custom attributes without breaking core User
- Produce a lab-without-live-target extended JSON fixture and aggregation checklist
- Document examiner impact: custom attrs in certifications and SoD selectors

---

## Why this matters

**Business.** SaaS tenants rarely stop at userName/email. Meridian needs cost center and risk tier on the cube for certifications and birthright—without forking a full Web Services project when SCIM extensions exist.

**Control / audit.** Custom attributes become control data. Examiners ask where `mnbRiskTier` is sourced and whether aggregation preserves it. Schema maps and sample payloads are the proof.

---

## Concepts

**Schema URIs (typical):**

| Schema | Purpose |
| --- | --- |
| `urn:ietf:params:scim:schemas:core:2.0:User` | Core User |
| `urn:ietf:params:scim:schemas:extension:enterprise:2.0:User` | Enterprise (manager, department, …) |
| Vendor URI | Product-specific extensions |

```
User resource
  schemas: [core, enterprise, urn:meridian:params:scim:schemas:extension:1.0:User]
  userName / emails / active     ← core
  department / manager           ← enterprise
  mnbRiskTier / costCenter       ← Meridian extension (lab design)
```

**Rule:** Never overwrite core mappings when adding extensions. Lab-without-live-target = author extended JSON + IIQ attribute map only.

---

## Before you start

- [ ] Lesson 69 `MNB-SCIM-SaaS` shell exists (or recreate)
- [ ] `Users.json` available to copy/extend
- [ ] HR attributes for department known from earlier lessons

---

## Lab procedure

### Task 1 — Baseline core map

1. Re-open `Users.json`; list core attributes already mapped in Lesson 69.
2. Mark gaps Meridian cares about: department, costCenter, risk tier—not in fixture yet.

**Expected result:** Gap list of 3+ attributes.

### Task 2 — Design Meridian extension

1. Choose extension URI: `urn:meridian:params:scim:schemas:extension:1.0:User` (lab-only).
2. Define attributes: `costCenter` (string), `mnbRiskTier` (string: low/medium/high/critical), `businessUnit` (string).
3. Also plan enterprise: `department`.

**Expected result:** Extension attribute dictionary page.

**If it fails:** Keep names simple; avoid colliding with IIQ reserved names.

### Task 3 — Author extended fixture (lab-without-live-target)

1. Copy `Users.json` → `Users-extended.json` under `~/iiq-lab-data/connectors/scim/`.
2. Add `schemas` array entries for enterprise + Meridian extension.
3. For `priya.wire` set `mnbRiskTier=high`, `costCenter=WIRE-OPS`; for `marcus.approve` set `mnbRiskTier=critical`, `costCenter=WIRE-CTRL`.
4. Validate JSON parses.

**Expected result:** Extended fixture committed only if repo allows—or keep under `~/iiq-lab-data` if policy blocks.

**If it fails:** Minimal valid JSON; fix commas/brackets.

### Task 4 — Map into IIQ application

1. Open `MNB-SCIM-SaaS` (or clone as `MNB-SCIM-Ext`).
2. Add account attributes for extension fields; mark which promote to Identity attributes via sync (Lesson 22 hygiene—document only if not implementing sync yet).
3. Save schema.

**Expected result:** Schema shows custom attributes.

### Task 5 — Aggregation checklist

1. Write steps: Test Connection → Account Aggregation → spot-check `mnbRiskTier` on account → optional Identity attribute sync.
2. If no live SCIM: Shadow CSV including new columns; aggregate DelimitedFile shadow.

**Expected result:** Checklist with Expected result column filled after dry-run.

### Task 6 — Cert / SoD impact note

1. Note which cert campaigns might filter on `mnbRiskTier=critical`.
2. Warn: custom attrs in policies need change control.

**Expected result:** One paragraph for Risk/IAM architecture board.

---


### Task 7 — Promotion note

1. List which extension attributes are safe to promote sandbox → prod.
2. Require vendor confirmation that Meridian URN (or enterprise attrs) exists in the tenant before enabling sync.
3. Add residual risk: *Lab URN may not exist in vendor—map to vendor-supported extension in prod.*

**Expected result:** Promotion checklist with residual risk id `RR-SCIM-EXT-01`.

**If it fails:** Still record RR even if all attrs are “account-only.”

### Task 8 — Binder packaging

1. Assemble files under `MNB-SCIM-Ext-Binder-YYYY-MM-DD`.
2. Include before/after schema screenshots and the extended JSON excerpt for `priya.wire` only (minimize PII).

**Expected result:** Dated binder folder name written in notes.


## Acceptance criteria

- [ ] Extension URI and attribute dictionary defined
- [ ] `Users-extended.json` (or equivalent) created and valid
- [ ] IIQ schema map updated on MNB-SCIM app
- [ ] Aggregation checklist completed (live or shadow)
- [ ] Cert/SoD impact note written

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Attribute blank after agg | Wrong schema URN / path | Match JSON extension object path to map |
| Core fields broke | Overwrote core schema | Restore core User mappings first |
| Invalid JSON | Trailing commas | Validate with json.tool |
| Identity attr not updating | No sync configured | Document as account-only until Lesson 22 pattern applied |
| Vendor rejects extension | Tenant not configured | Fall back to enterprise schema only; log RR |

---

## Training binder evidence

- Extension dictionary
- Extended JSON sample (redact PII if needed)
- Schema screenshot
- Aggregation checklist
- Cert/SoD impact paragraph

---

## Knowledge check

1. Name one standard SCIM enterprise schema use.
2. What lab extension URI did you choose for Meridian?
3. Which persona received `mnbRiskTier=critical` in the extended fixture?
4. Why separate extension schemas from core User?
5. What is the lab-without-live-target artifact for custom schemas?

### Answers

1. department / manager (enterprise:2.0:User) or similar enterprise fields.
2. `urn:meridian:params:scim:schemas:extension:1.0:User` (lab-only).
3. `marcus.approve`.
4. To avoid breaking standard interoperability and to version Meridian fields cleanly.
5. Extended JSON fixture + IIQ attribute map / Shadow CSV.

---

## Stretch lab

Propose mapping `manager.value` (enterprise) to Meridian manager correlation for `sofia.torres` reports. Document only—do not change production manager hierarchy.

---

## Summary

- SCIM extensions carry Meridian-specific governance attributes beyond core User.
- Extended fixtures unlock training when vendors are unavailable.
- Custom attributes need change control because certs and policies consume them.

---

**Previous:** [Lesson 69 — SCIM 2.0 Connector](69-scim2-connector.md)  
**Next:** [Lesson 71 — Salesforce Native Connector](71-salesforce-native-connector.md)
