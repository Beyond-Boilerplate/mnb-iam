# Lesson 238 — SCIM Connector Depth

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~65 minutes  
**Prereq:** Lesson 210  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 69–70

> **Why:** Filter, PATCH, and schema-gap skills transfer straight to Okta/Entra-class IdPs. If you only ever full-aggregate a mock, the first real tenant that returns nested `emails[]` or rejects your filter syntax becomes a multi-day outage.

## What this is

Lesson 210 aggregated **`MNB-Salesforce-CRM-Live`** (`SCIM 2.0` / `scimProvider=generic`) against:

```text
http://connector-mock:8091/crm/scim/v2
```

This lesson goes deeper on the **same CRM mock** — not Keycloak/`MNB-Okta`:

1. Raw `curl` filter before trusting IIQ  
2. Attribute map vs real JSON (including `emails[]` and `groups`)  
3. Live SCIM **PATCH** of `active` for disposable **`lab.scimdeep1`**  
4. Re-aggregate and prove the cube/link matches the mock  

Wire’s separate `/scim/v2/Users` store (Lesson 209/237) is a contrast only — your drills hit **`/crm/scim/v2`**.

> **Watch out:** Do **not** use Helen / Priya / Marcus as the PATCH subject. You create `lab.scimdeep1` in HCM **and** in the CRM mock so shared personas stay intact.

## Know these

```text
curl CRM ListResponse → map fields vs IIQ schema
  → curl filter userName eq "…" (URL-encoded)
  → Confirm MNB-Salesforce-CRM-Live Base URL + relaxConfiguration
  → Hire lab.scimdeep1 + POST CRM User (externalId aligned)
  → Aggregate CRM → link on cube
  → PATCH active=false on CRM id
  → curl GET proves inactive → Aggregate → IIQ shows inactive
  → Schema-gap note (what a real Salesforce/Okta would also send)
```

| SCIM idea | Plain English | CRM mock |
| --- | --- | --- |
| **ListResponse** | Envelope around accounts | `schemas`, `totalResults`, `Resources[]` |
| **filter** | Server-side select | `userName eq "lab.scimdeep1"` |
| **PATCH** | Partial update | `Operations` → `path: active` |
| **`id` vs `externalId`** | Native key vs HR key | `crm-lab.scimdeep1` vs cube `userId` |
| **`emails`** | Often array of objects | `[{ "value": "...", "primary": true }]` |
| **`groups`** | Multi entitlement | `[{ "display": "CRM-Users" }]` → managed `groups` |

| IIQ schema attr | JSON source | Notes |
| --- | --- | --- |
| `id` | `id` | identityAttribute |
| `userName` | `userName` | displayAttribute |
| `active` | `active` | boolean lifecycle |
| `externalId` | `externalId` | **correlation** → identity `userId` |
| `groups` | `groups[].display` (connector mapping) | entitlement / managed / multi |

- **Wrong way:** Blaming IIQ’s filter before `curl` proves the mock accepts the syntax.  
- **Wrong way:** Correlating on `id` (`crm-…`) instead of `externalId`.  
- **Wrong way:** PATCHing Wire `/scim/v2/Users` and expecting CRM links to change — different stores.  
- **Wrong way:** Using Priya’s UUID from memory — always GET the current `id`.  
- **Wrong way:** Treating CSV `MNB-Salesforce-CRM` as the live target (retired for this path).

## Intent

- Prove CRM filter with `curl`, then align IIQ’s attribute map to the real JSON.  
- Create disposable `lab.scimdeep1` in HCM + CRM mock; aggregate and correlate.  
- PATCH `active=false`; re-aggregate; prove IIQ and mock agree.  
- Write a one-page schema-gap note vs a real SaaS IdP.

## Before you start

Complete every checkbox. Do not skip into Task 1 until these are true.

- [ ] IIQ up: [http://localhost:8080/identityiq](http://localhost:8080/identityiq) — `spadmin` / `admin`
- [ ] Lesson 210 idea familiar (CRM Live Base URL + `externalId` correlation) — you will **re-verify** the app
- [ ] Mock healthy:

```bash
curl -sf http://localhost:8091/health
```

- [ ] CRM list readable:

```bash
curl -s http://localhost:8091/crm/scim/v2/Users | python3 -m json.tool | head -50
```

  - **Expect:** `ListResponse` with non-empty `Resources`.

- [ ] Evidence dir:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/238
```

> **Tip:** If CRM `?filter=` or `PATCH` returns `404`, restart the enterprise stack so connector-mock loads filter/PATCH handlers.

## Do this

### Task 1 — Read CRM schema shape with curl

```bash
curl -s http://localhost:8091/crm/scim/v2/Users \
  | python3 -m json.tool | head -80
```

Pick Helen’s object (or any Resource) and write under evidence `schema-shape.txt`:

```text
id: ________
userName: ________
externalId: ________
emails type: string | array-of-objects = ________
groups present: yes/no ; shape = ________
active: ________
name.givenName / familyName: ________
```

- **Why:** IIQ’s attribute map must match nested reality — especially `emails` and `groups`.
- **Expect:** you can describe `emails` and `groups` precisely before opening the Application.

### Task 2 — Filter by hand (before IIQ)

```bash
curl -s -G 'http://localhost:8091/crm/scim/v2/Users' \
  --data-urlencode 'filter=userName eq "helen.ross"' \
  | python3 -m json.tool
```

- **Expect:** `totalResults` = 1 (or small), `Resources[0].userName` = `helen.ross`.

Save as `filter-helen.json`.

Optional second filter (HR key):

```bash
curl -s -G 'http://localhost:8091/crm/scim/v2/Users' \
  --data-urlencode 'filter=externalId eq "MNB00001"' \
  | python3 -m json.tool | head -40
```

- **Why:** if curl filter fails, IIQ aggregation filters will fail the same way — fix syntax before config blame.
- **Expect:** filter works with URL-encoded `eq` and quotes.

> **Watch out:** Spaces in `userName eq "…"` must be encoded (`%20`) if you hand-build the URL instead of `--data-urlencode`.

### Task 3 — Verify `MNB-Salesforce-CRM-Live` attribute map

1. **Applications → Application Definition → MNB-Salesforce-CRM-Live**  
2. Confirm Configuration:

| Setting | Required |
| --- | --- |
| **Base URL** | `http://connector-mock:8091/crm/scim/v2` |
| **Authentication** | No Auth |
| **Connect to Non Compliant Server** / `relaxConfiguration` | **on** |
| **scimProvider** | `generic` |
| Schema identity | `id` |
| Schema display | `userName` |

3. Open **Schema** (account) and compare to Task 1:

| Attribute | Must exist | Flags |
| --- | --- | --- |
| `id` | yes | identity |
| `userName` | yes | display |
| `active` | yes | boolean |
| `externalId` | yes | correlation source |
| `groups` | yes | entitlement / managed / multi |

4. If `groups` or `externalId` missing — add them, **Save**, plan to re-aggregate after Task 6  
5. Correlation (Account Mapping / Correlation tab): `externalId` → Identity `userId` (or your estate’s equivalent). Create Identities = **OFF**

Screenshot schema under evidence.

- **Why:** Lesson 210 may have been wiped; assume-nothing for this lesson’s objects.
- **Expect:** map matches CRM JSON; correlation on `externalId`, not `id`.

### Task 4 — IIQ filter / preview (if the UI exposes it)

1. On the Application, look for Aggregation filter / Preview filter  
2. If present, set the same filter: `userName eq "helen.ross"` (UI may wrap SCIM filter differently)  
3. Run Preview or a scoped aggregation if available  

- **Expect:** only Helen (or one account) when filter works.

If your build has **no** filter field on the SCIM template:

```text
IIQ UI filter: not exposed on this build — curl filter-helen.json is the filter proof.
```

Save that line under evidence. Continue with full aggregation later — do not invent a non-existent field.

- **Why:** some SCIM templates hide filter; honesty beats fake clicks.
- **Expect:** either scoped preview works or you recorded the UI gap.

### Task 5 — Create disposable `lab.scimdeep1` (HCM + CRM)

#### 5a — HCM / Workday cube

```bash
./tools/lab/enterprise/hcm-scenario.sh joiner lab.scimdeep1 Lab Scimdeep \
  lab.scimdeep1@meridiannb.com 'Bank Operations'
```

```bash
curl -s http://localhost:8091/hcm/v1/workers/lab.scimdeep1 \
  | python3 -m json.tool | grep -E 'userName|email|active|id|workerId'
```

1. Aggregate **`MNB-Workday`** → Complete  
2. **Refresh Identity Cube** for `lab.scimdeep1` → Complete  
3. Open the cube — note **`userId`** (use this exact string as CRM `externalId`). If blank, set `userId` = `lab.scimdeep1` and Save.

#### 5b — Create CRM SCIM user (mock)

```bash
curl -s -X POST http://localhost:8091/crm/scim/v2/Users \
  -H 'Content-Type: application/json' \
  -d '{
    "userName": "lab.scimdeep1",
    "externalId": "lab.scimdeep1",
    "email": "lab.scimdeep1@meridiannb.com",
    "givenName": "Lab",
    "familyName": "Scimdeep",
    "active": true,
    "groups": [{"display": "CRM-Users"}]
  }' | python3 -m json.tool
```

- **Expect:** `201` body with `"id": "crm-lab.scimdeep1"` (or similar) and `"active": true`.

Save as `crm-create.json`. Copy the **`id`** — you need it for PATCH.

> **Watch out:** Set `"externalId"` to the **same** value as the cube `userId` or correlation will leave an uncorrelated account.

- **Why:** disposable CRM row + cube lets you PATCH without damaging Helen’s seed row.
- **Expect:** HCM cube + CRM user both exist before aggregation.

### Task 6 — Aggregate CRM and prove the link

1. **Test Connection** on `MNB-Salesforce-CRM-Live` → green  
2. Run **Account Aggregation** → Complete  
3. Open `lab.scimdeep1` → **Application Accounts**  

- **Expect:** link to `MNB-Salesforce-CRM-Live`, `active` true, group entitlement visible if managed `groups` promoted.

```bash
curl -s -G 'http://localhost:8091/crm/scim/v2/Users' \
  --data-urlencode 'filter=userName eq "lab.scimdeep1"' \
  | python3 -m json.tool
```

Save as `before-patch.json`.

- **Why:** prove correlation before you change lifecycle — otherwise PATCH “proof” is ambiguous.
- **Expect:** filtered GET and IIQ link agree on `userName` / `externalId`.

### Task 7 — PATCH `active=false` on the CRM mock

Substitute the real `id` from Task 5b (example uses `crm-lab.scimdeep1`):

```bash
CRM_ID='crm-lab.scimdeep1'   # replace if your create returned a different id

curl -s -X PATCH "http://localhost:8091/crm/scim/v2/Users/${CRM_ID}" \
  -H 'Content-Type: application/json' \
  -d '{
    "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
    "Operations": [
      { "op": "replace", "path": "active", "value": false }
    ]
  }' | python3 -m json.tool
```

- **Expect:** `200` with `"active": false`.

Confirm persistence with GET (not only the PATCH response):

```bash
curl -s "http://localhost:8091/crm/scim/v2/Users/${CRM_ID}" | python3 -m json.tool | grep -E 'userName|active|id'
```

Save as `after-patch.json`.

- **Why:** simulates IdP-side deactivation outside IIQ — re-agg must pick it up.
- **Expect:** GET still shows `active: false` after PATCH.

### Task 8 — Re-aggregate; prove IIQ sees inactive

1. Aggregate **`MNB-Salesforce-CRM-Live`** again → Complete  
2. Open `lab.scimdeep1` → CRM link  

- **Expect:** account / `active` reflects **false** (disabled/inactive in UI wording).

Write under evidence:

```text
CRM id: ________
PATCH active=false at: ________
IIQ link active after re-agg: false
```

- **Why:** aggregation is how IIQ learns out-of-band IdP changes; skipping re-agg leaves a false “still active” story.
- **Expect:** mock and IIQ both inactive.

### Task 9 — Schema-gap note (mock vs real SaaS)

Write `schema-gap.txt`:

```text
CRM mock returns: id, userName, name.*, emails[], active, externalId, groups[].display
IIQ map today: ________ (list attrs you confirmed in Task 3)

Real Salesforce / Okta-class SCIM often also sends:
  meta.created / meta.lastModified / meta.location
  name.formatted, locale, timezone
  groups[].value (UUID) in addition to display
  enterprise extension urn (manager, department) on some tenants

Gap for onboarding: ________ (one sentence — what you would verify before go-live)
```

- **Why:** treating the mock schema as production-complete is how attribute sync and certs miss fields later.
- **Expect:** gap note saved; not a claim that the mock is a full IdP.

### Task 10 — Evidence pack

Confirm `~/iiq-lab-evidence/sandbox/238/` has:

```text
schema-shape.txt
filter-helen.json
crm-create.json
before-patch.json
after-patch.json
schema-gap.txt
```

- **Expect:** filter + PATCH + gap story in one folder.

## If it fails

| Symptom | Fix |
| --- | --- |
| Filter 400 / empty | Use `--data-urlencode`; mock supports `userName eq` and `externalId eq` with quotes |
| PATCH 404 | Wrong `id` — GET filter for `lab.scimdeep1` and use returned `id` |
| PATCH 200 but GET still active | Old mock without mutable CRM — restart connector-mock / enterprise stack |
| Account uncorrelated | `externalId` ≠ cube `userId`; fix CRM user or cube; re-agg |
| `groups` not on link | Schema flags entitlement/managed/multi; re-agg; check Entitlement Catalog |
| IIQ filter field missing | Expected on some builds — keep curl as proof (Task 4) |
| Used Helen for PATCH | Stop — create `lab.scimdeep1` (Task 5) and PATCH that id |
| Editing CSV CRM app | Wrong app — use `MNB-Salesforce-CRM-Live` only |

## You are done when

- [ ] `curl` filter for `helen.ross` (or lab user) returned a tight ListResponse  
- [ ] IIQ schema/correlation verified against CRM JSON (`externalId` → `userId`)  
- [ ] `lab.scimdeep1` exists in HCM + CRM; correlated after aggregation  
- [ ] PATCH set `active=false`; GET + re-agg both show inactive  
- [ ] Schema-gap note saved under evidence  

## Control note

- **Control:** SCIM filter / PATCH / schema-gap awareness before onboarding a real IdP  
- **Owner:** IAM Engineering  
- **SLA (lab):** Gap documented; out-of-band deactivate visible after one re-agg  
- **Evidence:** `~/iiq-lab-evidence/sandbox/238/`  
- **Out of scope:** Keycloak/`MNB-Okta` admin SCIM (birthright path) — CRM Live only here

## Quick check

1. What SCIM verb enables partial updates? → `PATCH`  
2. Correlation key on CRM Live? → `externalId` → identity `userId` (not SCIM `id`)  
3. Why curl the filter first? → Proves mock syntax before blaming IIQ  
4. Are `emails` always a string? → No — often an array of objects; check before mapping  
5. Why not PATCH Priya on Wire SCIM for this lesson? → Wrong store; this drill is `/crm/scim/v2`  

## Feedback

Could you onboard a new SaaS SCIM app tomorrow: curl ListResponse → map attrs → filter → PATCH deactivate → re-agg — without this page?

If something failed, note the **task number**, the exact `id` you PATCHed, and whether curl or IIQ disagreed on `active`.

## Navigate

- Previous: [Lesson 237](237-ws-connector-deep.md)
- Next: [Lesson 239](239-itsm-ticket-mock.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
