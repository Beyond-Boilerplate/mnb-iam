# Lesson 69 — SCIM 2.0 Connector

**Level:** Intermediate  
**Track:** Connectors — Web APIs & SaaS  
**Time:** 75–90 min  
**Prereq:** Lesson 68 — Web Services Connector  

**Lab data:**
- Repo: `lab-data/connectors/scim/Users.json`
- Repo: `lab-data/connectors/connector-selection-matrix.csv`
- Repo: `lab-data/connectors/features-string-glossary.md`
- Runtime: `~/iiq-lab-data/connectors/scim/`

---

## Learning objectives

You will be able to:

- Explain SCIM 2.0 ListResponse and User core schema as used by IdentityIQ’s SCIM connector
- Create application **MNB-SCIM-SaaS** configured against lab `Users.json` contract
- Map `userName`, `emails`, `active`, `externalId` to IIQ account attributes and correlation
- Run or simulate Account Aggregation for `priya.wire` and `marcus.approve`
- Contrast SCIM vs Web Services for Meridian SaaS onboarding decisions

---

## Why this matters

**Business.** Vendors that speak SCIM reduce custom Web Services mapping. Meridian wants a repeatable pattern for SCIM-compliant SaaS so each new tool is not a bespoke REST project.

**Control / audit.** Examiners expect consistent joiner/leaver disable (`active=false`) evidence on SaaS. SCIM’s standard User resource makes disablement and aggregation comparable across vendors.

---

## Concepts

**SCIM 2.0 (System for Cross-domain Identity Management).** Standard REST API for users/groups. IdentityIQ’s **SCIM 2.0** connector speaks this dialect.

**ListResponse (lab fixture):**

```
schemas: urn:ietf:params:scim:api:messages:2.0:ListResponse
totalResults → Resources[] → User resources
```

| SCIM attribute | Meridian IIQ use |
| --- | --- |
| `id` | Optional native / secondary key |
| `userName` | Preferred account native identity |
| `emails[primary].value` | Correlation / mail |
| `externalId` | HR link (`MNB00090`) |
| `active` | Enable/disable |

```
IIQ MNB-SCIM-SaaS  →  SCIM 2.0 connector  →  /Users (ListResponse)
                              │
                              └── Resources: priya.wire, marcus.approve
```

**Matrix:** SCIM-compliant SaaS → preferred SCIM 2.0, alternate Web Services.

**Lab-without-live-target.** Treat `Users.json` as the golden response; configure app base URL placeholders; build attribute map; optionally shadow-aggregate a flattened CSV.

---

## Before you start

- [ ] IIQ up; Web Services lesson ops map concepts fresh
- [ ] `Users.json` copied under `~/iiq-lab-data/connectors/scim/`
- [ ] Know `externalId` values MNB00090 / MNB00091

---

## Lab procedure

### Task 1 — Parse the SCIM fixture

1. Open `~/iiq-lab-data/connectors/scim/Users.json`.
2. Confirm `totalResults` = 2; schemas include ListResponse and core User.
3. Record for each Resource: `id`, `userName`, email, `externalId`, `active`.
4. Note `priya.wire@meridiannb.com` / `marcus.approve@meridiannb.com`.

**Expected result:** Two-row inventory table in binder.

**If it fails:** Re-copy fixture; validate JSON with `python -m json.tool`.

### Task 2 — Create MNB-SCIM-SaaS

1. Applications → Add New → **SCIM 2.0** (or equivalent).
2. Name: `MNB-SCIM-SaaS`. Owner: `helen.ross`.
3. Enter base URL / Users endpoint placeholders (e.g., `https://saas.example.meridiannb.com/scim/v2`).
4. Auth placeholders only—no real tokens in repo.
5. Save.

**Expected result:** Application shell saved.

**If it fails:** Document intended SCIM settings in XML export notes; continue mapping.

### Task 3 — Schema and correlation map

1. Map `userName` → identity attribute account id.
2. Map `externalId` → correlate to Identity `employeeId`.
3. Map `active` → IIQ IIQDisabled / inactive semantics per your build’s SCIM enable feature.
4. Confirm featuresString expectations: PROVISIONING, ENABLE, etc., via glossary.

**Expected result:** Attribute map table signed off in binder.

### Task 4 — Aggregation (live or lab-without-live-target)

**Live SCIM:** Test Connection; run **Account Aggregation** `MNB-SCIM-SaaS-Account-Aggregation`.

**No live target:** Flatten `Users.json` to CSV (`userName,email,employeeId,active`) as `MNB-SCIM-SaaS-Shadow.csv`; DelimitedFile shadow app; aggregate; label clearly as training shadow.

**Expected result:** Two accounts visible; cubes link when employeeIds match HR.

**If it fails:** Fix correlation keys; ensure HR has MNB00090/91 or note uncorrelated for remediation lesson patterns.

### Task 5 — Disablement storyboard

1. Write the leaver path: set SCIM `active=false` for `raj.external` scenario (hypothetical).
2. Note Account Aggregation must show inactive after provision.
3. Tie to examiner question: *Show Task Result for disable + post-agg screenshot.*

**Expected result:** One-page disablement storyboard.

### Task 6 — SCIM vs Web Services decision card

1. When vendor has full SCIM Users/Groups → SCIM connector.
2. When custom banking API (Wire Portal) → Web Services.
3. Paste matrix rows into the card.

**Expected result:** Decision card ready for architecture reviews.

---

## Acceptance criteria

- [ ] `Users.json` parsed and inventoried
- [ ] `MNB-SCIM-SaaS` app shell + attribute/correlation map
- [ ] Aggregation Task Result (live or Shadow)
- [ ] Disablement storyboard written
- [ ] SCIM vs Web Services decision card complete

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| totalResults mismatch | Pagination not followed | Configure startIndex/count; verify connector paging |
| Email not correlating | Wrong JSON path to emails.value | Use primary email mapping |
| active ignored | ENABLE feature / flag mapping | Map active→IIQ disable attribute; retest |
| Groups missing | Only Users endpoint configured | Add Groups if vendor supports; else document gap |
| Shadow promoted | Naming error | Keep `-Shadow` suffix; delete before prod |

---

## Training binder evidence

- Annotated Users.json
- App config redacted
- Attribute map
- Aggregation evidence
- Disablement storyboard + decision card

---

## Knowledge check

1. What schema URI identifies a SCIM ListResponse in the lab file?
2. Which attribute links SCIM users to Meridian HR employee ids?
3. Name the two userNames in the lab SCIM fixture.
4. When should Meridian choose SCIM over Web Services?
5. What does lab-without-live-target use instead of a live /Users endpoint?

### Answers

1. `urn:ietf:params:scim:api:messages:2.0:ListResponse`.
2. `externalId` (e.g., MNB00090).
3. `priya.wire` and `marcus.approve`.
4. When the SaaS vendor provides standard SCIM Users/Groups.
5. Flattened fixture/CSV Shadow app plus full attribute map documentation.

---

## Stretch lab

Add a Groups ListResponse stub JSON and document how group entitlements would appear on `MNB-SCIM-SaaS`. Do not invent vendor APIs—keep stubs labeled lab-only.

---

## Summary

- SCIM 2.0 standardizes SaaS user aggregation and enable/disable for Meridian.
- `MNB-SCIM-SaaS` training uses `Users.json` when no vendor tenant exists.
- Prefer SCIM for compliant SaaS; keep Web Services for custom bank APIs.

---

**Previous:** [Lesson 68 — Web Services Connector](68-web-services-connector.md)  
**Next:** [Lesson 70 — SCIM Custom Schemas](70-scim-custom-schemas.md)
