# Lesson 69 — SCIM 2.0 Connector

**Level:** Intermediate  
**Track:** Connectors — Web APIs & SaaS  
**Time:** 90–120 min  
**Prereq:** Lesson 68 — Web Services Connector  

**Lab data:**
- Repo: `lab-data/connectors/scim/Users.json`
- Repo: `lab-data/connectors/connector-selection-matrix.csv`
- Repo: `lab-data/connectors/features-string-glossary.md`
- Runtime: `~/iiq-lab-data/connectors/scim/`

---

## Learning objectives

You will be able to:

- Explain SCIM 2.0 ListResponse and core User schema as consumed by IdentityIQ’s SCIM connector
- Create **MNB-SCIM-SaaS** configured against the lab `Users.json` contract
- Map `userName`, `emails`, `active`, and `externalId` to account attributes and HR correlation
- Run or simulate Account Aggregation for `priya.wire` and `marcus.approve`
- Choose SCIM vs Web Services correctly for Meridian SaaS onboarding

---

## Why this matters

**Business.** Each new SaaS tool should not become a bespoke Web Services project. When a vendor speaks SCIM, Meridian can reuse a standard Users/Groups pattern — faster onboarding, fewer one-off JSONPath maps, consistent leaver disable via `active=false`.

**Control / audit.** Examiners expect comparable joiner/leaver evidence across SaaS. SCIM’s standard User resource makes disablement and aggregation **comparable** across vendors; custom REST (Lesson 68) does not.

---

## Concepts

### SCIM in one paragraph

**SCIM 2.0** (System for Cross-domain Identity Management) is a standard REST API for users and groups. Resources carry a `schemas` array of URNs. Collections return a **ListResponse** with `totalResults` and `Resources`. IdentityIQ’s **SCIM 2.0** connector speaks this dialect — not arbitrary JSON.

### Lab fixture truth (`Users.json`)

```
schemas: urn:ietf:params:scim:api:messages:2.0:ListResponse
totalResults: 2
Resources[] → User resources (core:2.0:User)
```

| SCIM attribute | Value (examples) | Meridian IIQ use |
| --- | --- | --- |
| `id` | `scim-90`, `scim-91` | Optional native / secondary key |
| `userName` | `priya.wire`, `marcus.approve` | Preferred account native identity |
| `emails[primary].value` | `*@meridiannb.com` | Mail / fallback correlation |
| `externalId` | `MNB00090`, `MNB00091` | **Preferred** HR link → `employeeId` |
| `active` | `true` | ENABLE / disable |
| `name.givenName` / `familyName` | Priya / Mehta | Display attributes |

### SCIM vs Web Services (decision rule)

| Situation | Choose |
| --- | --- |
| Vendor documents SCIM Users/Groups | **SCIM 2.0** |
| Custom bank API (Wire Portal OpenAPI) | **Web Services** |
| “Almost SCIM” proprietary JSON | Web Services — do not fake SCIM |

Matrix: **SCIM-compliant SaaS → SCIM 2.0**, alternate Web Services.

### Why `externalId` beats email correlation

Email renames break correlation; HR `employeeId` in `externalId` survives. Meridian lab fixture already carries `MNB00090` / `MNB00091` — use them.

```
IIQ MNB-SCIM-SaaS
        │
        ▼
 SCIM 2.0 connector
        │
        ▼
 GET /Users → ListResponse.Resources[]
        │
        └── priya.wire (MNB00090), marcus.approve (MNB00091)
```

---

## How it works

The connector issues SCIM protocol operations (list/get/create/patch/delete) against a base URL such as `https://saas.example/scim/v2`. Aggregation follows ListResponse paging (`startIndex` / `count` or vendor cursor — configure per docs). Disable typically PATCHes `active=false`.

```
IdentityIQ (MNB-SCIM-SaaS)
        │  OAuth / Bearer token (vaulted)
        ▼
GET /Users?startIndex=1&count=100
        │
        ▼
ListResponse { totalResults, Resources: [ User, User ] }
        │
        ▼
Links correlated on externalId → employeeId
```

| Operation | SCIM idea | IIQ behavior |
| --- | --- | --- |
| Test Connection | Auth + service provider config / Users reachability | Connection proof |
| Account aggregation | Filter/list Users | One Link per Resource |
| Get Object | GET `/Users/{id}` | Single refresh |
| Create | POST `/Users` | Joiner |
| Disable | PATCH `active=false` | ENABLE feature |
| Groups (if licensed) | `/Groups` | Entitlements |

Confirm `featuresString` (`PROVISIONING`, `ENABLE`, …) via glossary/registry before SLAs.

---

## Real-world setup (outside IIQ)

### Step 1 — Vendor SCIM readiness

1. Confirm SCIM 2.0 Users (and Groups if needed) in vendor docs — not “SCIM-like.”
2. Obtain tenant base URL (`…/scim/v2`).
3. Agree supported operations (some vendors are read-only SCIM).

### Step 2 — OAuth / token

1. Create a least-privilege integration user or OAuth client scoped to SCIM.
2. Vault client secret; separate read vs write clients when possible.
3. Never commit bearer tokens; redact binder screenshots.

### Step 3 — Attribute contract

1. Require vendor to populate `externalId` with Meridian `employeeId`.
2. Document which core attributes are authoritative on the SaaS vs HR.
3. Create-identities **OFF** — SaaS is a target.

### Step 4 — Network / IP allow lists

Many SaaS products allowlist IIQ egress IPs — request before Test Connection day.

---

## Before you start

- [ ] IIQ up; Lesson 68 ops-map concepts fresh (contrast only)
- [ ] `Users.json` copied under `~/iiq-lab-data/connectors/scim/`
- [ ] Know `externalId` values MNB00090 / MNB00091
- [ ] Feature glossary available

---

## Lab procedure

### Task 1 — Parse the SCIM fixture like a protocol engineer

Do not skim — aggregation bugs come from misreading ListResponse vs User.

1. Open `~/iiq-lab-data/connectors/scim/Users.json`.
2. Validate JSON:

```bash
python3 -m json.tool ~/iiq-lab-data/connectors/scim/Users.json >/dev/null
```

3. Confirm `totalResults` = 2; schemas include ListResponse and `urn:ietf:params:scim:schemas:core:2.0:User`.
4. Build inventory:

| id | userName | email | externalId | active |
| --- | --- | --- | --- | --- |
| scim-90 | `priya.wire` | priya.wire@meridiannb.com | MNB00090 | true |
| scim-91 | `marcus.approve` | marcus.approve@meridiannb.com | MNB00091 | true |

**Expected result:** Two-row inventory table in binder.

**If it fails:** Re-copy fixture; fix JSON syntax before continuing.

### Task 2 — Matrix confirmation and naming

1. Open selection matrix: SCIM-compliant SaaS → **SCIM 2.0**.
2. Application name: `MNB-SCIM-SaaS`. Owner: `helen.ross`.
3. Write decision card stub: *SCIM when vendor-compliant; Wire Portal remains Web Services.*

**Expected result:** Naming + decision stub archived.

### Task 3 — Create MNB-SCIM-SaaS

1. Applications → Add New → **SCIM 2.0** (or equivalent).
2. Base URL placeholder: `https://saas.example.meridiannb.com/scim/v2` (lab) or vendor URL.
3. Auth placeholders only — no real tokens in repo.
4. Create-identities **OFF**. Save.

**Expected result:** Application shell saved.

**If it fails:** Document intended settings in notes; continue attribute mapping.

### Task 4 — Schema and correlation map

1. Native identity: `userName` (document if you prefer `id` — pick one).
2. Correlate `externalId` → Identity `employeeId` (primary).
3. Map primary email; map `active` → disable/inactive semantics per your build’s SCIM ENABLE behavior.
4. featuresString expectations: PROVISIONING, ENABLE — note in binder.

**Expected result:** Attribute/correlation map table signed off.

### Task 5 — Aggregation (live or lab-without-live-target)

**Live SCIM:** Test Connection; run **Account Aggregation** `MNB-SCIM-SaaS-Account-Aggregation`; expect 2 accounts.

**No live target:** Flatten to `MNB-SCIM-SaaS-Shadow.csv`:

```csv
id,userName,email,employeeId,active
scim-90,priya.wire,priya.wire@meridiannb.com,MNB00090,true
scim-91,marcus.approve,marcus.approve@meridiannb.com,MNB00091,true
```

DelimitedFile shadow app; aggregate; label training shadow clearly.

**Expected result:** Two accounts visible; cubes link when employeeIds match HR.

**If it fails:** Fix correlation keys; note uncorrelated for remediation patterns if HR missing.

### Task 6 — Disablement storyboard

1. Leaver path: PATCH `active=false` for a terminated user (storyboard `raj.external` hypothetical on this app).
2. Re-aggregate; account shows inactive — examiner evidence with Task Result.
3. Tie SLA to Lesson 55 ENABLE=Y only after features confirmed.

**Expected result:** One-page disablement storyboard.

### Task 7 — SCIM vs Web Services decision card (final)

| App | Connector | Why |
| --- | --- | --- |
| Wire Portal | Web Services | Custom OpenAPI; not SCIM |
| Generic SCIM SaaS | SCIM 2.0 | Standard Users/ListResponse |
| Future “SCIM-ish” vendor | Web Services until true SCIM | Avoid fake mappings |

**Expected result:** Decision card ready for architecture reviews.

### Task 8 — Residual risk + CHANGELOG

1. `RR-SCIM-PAGE-01`: *If paging is misconfigured, totalResults disagrees with aggregated Links — always reconcile counts.*
2. CHANGELOG: “Lesson 69 SCIM 2.0 MNB-SCIM-SaaS against Users.json contract.”

**Expected result:** RR + CHANGELOG.

---

## Acceptance criteria

- [ ] `Users.json` parsed and inventoried (2 users, externalIds noted)
- [ ] `MNB-SCIM-SaaS` shell + attribute/correlation map
- [ ] Aggregation Task Result (live or Shadow)
- [ ] Disablement storyboard + SCIM vs WS decision card
- [ ] `RR-SCIM-PAGE-01` + CHANGELOG

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| totalResults mismatch | Pagination not followed | Configure startIndex/count; verify paging |
| Email not correlating | Wrong path to emails.value | Use primary email mapping |
| Prefer email over externalId | Habit | Switch correlation to externalId |
| active ignored | ENABLE / flag mapping | Map active→disable; retest |
| Groups missing | Only Users configured | Add Groups or document gap |
| Shadow promoted | Naming error | Keep `-Shadow`; delete before prod |
| Parsed as Web Services JSON | Wrong connector type | Use SCIM 2.0 for ListResponse |

---

## Training binder evidence

- Annotated Users.json inventory
- App config redacted
- Attribute/correlation map
- Aggregation evidence
- Disablement storyboard + decision card + RR

**Examiner question:** *“Show consistent SaaS disable evidence using a standard attribute — not a vendor-specific flag.”*

---

## Knowledge check

1. What schema URI identifies a SCIM ListResponse in the lab file?
2. Which attribute links SCIM users to Meridian HR employee ids?
3. Name the two userNames in the lab SCIM fixture.
4. When should Meridian choose SCIM over Web Services?
5. What does lab-without-live-target use instead of a live `/Users` endpoint?
6. What is `totalResults` in the lab fixture?

### Answers

1. `urn:ietf:params:scim:api:messages:2.0:ListResponse`.
2. `externalId` (e.g., MNB00090).
3. `priya.wire` and `marcus.approve`.
4. When the SaaS vendor provides standard SCIM Users/Groups.
5. Flattened fixture/CSV Shadow app plus full attribute map.
6. `2`.

---

## Further reading

- [RFC 7643 — SCIM Core Schema](https://datatracker.ietf.org/doc/html/rfc7643) — User attributes (`userName`, `emails`, `active`, `externalId`).
- [RFC 7644 — SCIM Protocol](https://datatracker.ietf.org/doc/html/rfc7644) — ListResponse, paging, PATCH semantics the connector relies on.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “SCIM 2.0 connector” for version-specific config.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — SCIM paging, active flag, and correlation threads.
- [OpenID SCIM overview resources](https://openid.net/) — search SCIM for ecosystem context (optional background).

---

## Stretch lab

Add a Groups ListResponse stub JSON and document how group entitlements would appear on `MNB-SCIM-SaaS`. Keep stubs labeled lab-only. Preview Lesson 70: which Meridian attributes are missing from core User (`costCenter`, `mnbRiskTier`) and must become extensions.

---

## Summary

- SCIM 2.0 standardizes SaaS user aggregation and enable/disable for Meridian; `Users.json` is the golden contract when no tenant exists.
- Correlate on `externalId` → `employeeId`; treat Wire Portal as Web Services, not faux-SCIM.
- Paging reconcile and disable storyboards are examiner-facing controls.

---

**Previous:** [Lesson 68 — Web Services Connector](68-web-services-connector.md)  
**Next:** [Lesson 70 — SCIM Custom Schemas](70-scim-custom-schemas.md)
