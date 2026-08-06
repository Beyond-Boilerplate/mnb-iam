# Lesson 210 — CRM via SCIM Mock

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~40 minutes  
**Prereq:** Lesson 207 (Warehouse cubes from Workday)  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 69–71

> **Why:** SCIM is the reusable SaaS-account pattern — once you can aggregate one SCIM app, you can aggregate all of them. Ops needs one repeatable onboarding pattern across vendors, not five bespoke integrations that each break differently.

## What this is

`MNB-Salesforce-CRM-Live` is a real **SCIM 2.0** application (`sailpoint.connector.OpenConnectorAdapter` → `openconnector.connector.scim2.SCIM2Connector`, `scimProvider generic`) against:

```text
http://connector-mock:8091/crm/scim/v2
```

(IIQ’s SCIM **Base URL** is the full `/scim/v2` root — Users live at `{host}/Users`.)

It is Salesforce-**shaped** SCIM, not a real Salesforce org. The mock serves `GET /crm/scim/v2/Users` from `lab-data/connectors/crm/Users.json`, which Lesson 202’s generator regenerates from `identity-master.json`:

- Every active (non-terminated) identity → a SCIM `User`
- Fields: `userName`, `name.givenName` / `familyName`, `emails`, `active`
- `externalId` = HR `userId` — **the correlation key**

This replaces the Core Path CSV `MNB-Salesforce-CRM` for this path. Leave the CSV version alone (Lesson 214 retires it deliberately) and standardize on the Live one from here forward.

## Know these

| Idea | Detail |
| --- | --- |
| SCIM envelope | `schemas: ["urn:ietf:params:scim:api:messages:2.0:ListResponse"]`, `totalResults`, `Resources[]` |
| Correlation key | `externalId` (e.g. `MNB00001`) — **not** `id` (`crm-MNB00001`) or `userName` |
| Base URL | `http://connector-mock:8091/crm/scim/v2` (not bare `/crm`) |
| Auth / discovery | `authType` = **No Auth**; **Connect to Non Compliant Server** (`relaxConfiguration`) on — mock has no `/ResourceTypes` |
| Terminated personas | Generator excludes `status: "terminated"` — a missing terminated persona here is **correct** |
| Why SCIM scales | One connector pattern fronts Okta, Salesforce, ServiceNow, or any SCIM 2.0 SaaS — only base URL / `scimProvider` change |

- **Wrong way:** Continuing to run aggregation or edits against the CSV `MNB-Salesforce-CRM` “just to keep it fresh” — stale historical links are fine; adding new activity to a retired app defeats the point of standardizing on Live.

## Intent

- Read the CRM SCIM feed and spot-check a known persona (`helen.ross` / `MNB00001`).
- Aggregate `MNB-Salesforce-CRM-Live` and correlate `externalId` → identity `userId`.
- Deliberately stop using the CSV `MNB-Salesforce-CRM` for any exercise from this point forward.
- Recognize the SCIM `ListResponse` envelope — you’ll see it again in Lessons 211, 213, and 238.

## Before you start

- [ ] Lesson **207** complete — Warehouse has `helen.ross` / `priya.wire` (Workday cubes)
- [ ] Lesson 202 seed already run (`MNB-Salesforce-CRM-Live` Application exists)
- [ ] `curl` + `python3` available
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/210
```

## Do this

### Task 1 — Read the live SCIM feed first

Before you touch IIQ, prove the SaaS mock speaks standard SCIM 2.0. Production onboarding starts the same way: hit the vendor’s `/Users` endpoint and confirm the envelope — that shared shape is why one connector type covers Salesforce, Okta, and dozens of other SaaS products.

```bash
curl -s http://localhost:8091/crm/scim/v2/Users | python3 -m json.tool | head -40
```

- **Why:** ground truth outside IIQ — if the feed is wrong, aggregation can only amplify it.
- **Expect:** top-level `schemas` includes the ListResponse URN, plus `totalResults` and a non-empty `Resources` array.

> **Watch out:** Host curl uses `localhost:8091`. The Application’s **Base URL** must be `http://connector-mock:8091/crm/scim/v2` (Docker hostname + full SCIM root — different from Wire Portal’s base in Lesson 209). Also confirm **Authentication Type** = **No Auth** and **Connect to Non Compliant Server** is checked (this mock has no `/ResourceTypes`).

### Task 2 — Map one User’s fields (Helen)

Find Helen’s object in `Resources` and write down these fields. The trap is treating `id` as the correlation key — it isn’t.

| Field | Example value | Role |
| --- | --- | --- |
| `id` | `crm-MNB00001` | Native account identity in the target |
| `userName` | `helen.ross` | Display / login-shaped name |
| `externalId` | `MNB00001` | **Correlation key** → identity `userId` |
| `emails[0].value` | `helen.ross@meridiannb.com` | Contact |
| `groups[0].display` | `CRM-Users` | Entitlement (managed group) |

- **Why:** you must separate native `id`, login `userName`, and HR-aligned `externalId` *before* you trust any cube link.
- **Expect:** Helen has all five; `externalId` is exactly `MNB00001`.

### Task 3 — Test Connection and aggregate the Live app

In IIQ (`http://localhost:8080/identityiq`):

1. Open **Applications → Application Definition → MNB-Salesforce-CRM-Live**.
2. On Configuration, confirm:
   - **Base URL** = `http://connector-mock:8091/crm/scim/v2`
   - **Authentication Type** = **No Auth**
   - **Connect to Non Compliant Server** = checked
   - Schema: `identityAttribute` = `id`, `displayAttribute` = `userName`
   - `groups` flagged `entitlement="true"` `managed="true"` `multi="true"`
3. Click **Test Connection**.
4. Run **Account Aggregation** (**Setup → Tasks** → create `Aggregate MNB-Salesforce-CRM-Live` if none exists yet).

- **Why:** seed imported the Application definition; operators own the first pull — same pattern as Workday in Lesson 207.
- **Expect:** Test Connection succeeds; aggregation Task Result succeeds (created/updated counts > 0).

> **Tip:** If aggregation looks “short,” check whether missing people are `status: "terminated"` in the identity master — the generator excludes them on purpose.

### Task 4 — Prove correlation on Helen’s cube

Open **Identities → Identity Warehouse** → `helen.ross`. Find the `MNB-Salesforce-CRM-Live` account link and confirm it attached via `externalId` → `userId` (`MNB00001`).

- **Why:** this is the correlation pattern shared by every live app on this path — get it right once, reuse it forever.
- **Expect:** CRM-Live link present on Helen’s cube, **distinct** from any leftover CSV `MNB-Salesforce-CRM` link.

> **Watch out:** Warehouse cubes come from Lesson **207** (Workday). If Helen isn’t there yet, finish 207 first — this lesson correlates accounts onto existing identities; it does not mint them.

### Task 5 — Freeze the CSV CRM path (deliberately)

Decide now: for the rest of this path, do **not** re-run aggregation or edit accounts against CSV `MNB-Salesforce-CRM`.

- **Why:** the CSV app is historical evidence of the migration. New activity on it undoes the point of standardizing on Live.
- **Expect:** you leave the CSV app alone from here forward (do **not** delete historical links — just stop using it).

### Task 6 — Spot-check the seeded estate from the API

Without opening source files, confirm the mock is serving the estate you seeded:

```bash
curl -s http://localhost:8091/crm/scim/v2/Users | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('totalResults=', d.get('totalResults'))
names = {r.get('userName'): r.get('externalId') for r in d.get('Resources', [])}
print('helen.ross', names.get('helen.ross'))
print('priya.wire', names.get('priya.wire'))
"
```

- **Why:** ops proof that the feed matches known personas — and that terminated identities are absent by design.
- **Expect:**
  - `totalResults` is a positive count
  - `helen.ross` → `MNB00001`
  - `priya.wire` → `MNB00090`

Save the output under `~/iiq-lab-evidence/sandbox/210/`.

### Task 7 — Compare entitlements on two cubes

Open `priya.wire`’s cube alongside `helen.ross`. On each CRM-Live link, check `groups` / `CRM-Users`.

- **Why:** this mock gives every seeded user the same static `CRM-Users` placeholder. Real Salesforce SCIM would carry role-specific groups — here you’re proving the **entitlement pipeline**, not CRM role design.
- **Expect:** both cubes show a CRM-Live link with `CRM-Users`.

### Task 8 — Close with asserts

```bash
./tools/lab/enterprise/verify-lesson.sh 210
```

- **Why:** hard checks catch a missing Live app or a dead SCIM feed before you move on.
- **Expect:** PASS for `MNB-Salesforce-CRM-Live` exists and CRM SCIM feed includes `helen.ross`.

## If it fails

| Symptom | Fix |
| --- | --- |
| `Missing connector class name` | App attribute `connectorClass` must be `openconnector.connector.scim2.SCIM2Connector` — re-import `config/Application/MNB-Application-Salesforce-CRM-Live.xml` or set it on the Configuration tab |
| `Config attribute 'authType' is required` | Set **Authentication Type** to **No Auth** (mock has no credentials) |
| `/ResourceTypes` / “Please check base URL” | Base URL = `http://connector-mock:8091/crm/scim/v2` **and** enable **Connect to Non Compliant Server** (`relaxConfiguration`) — mock serves Users only |
| Test Connection fails (other) | Confirm host is `connector-mock` (not `localhost`) and path ends in `/crm/scim/v2` |
| Aggregation returns fewer users than expected | Generator excludes `status: "terminated"` on purpose — correct, not a bug |
| `externalId` correlation doesn’t match anyone | Stale `Users.json` — re-run `python3 tools/lab/enterprise/generate-identity-artifacts.py` and re-aggregate |
| Old CSV CRM links won’t disappear | Expected; stop *using* the CSV path going forward, don’t delete historical links |
| `groups` shows as a plain attribute, not managed | Refresh the Entitlement Catalog for this application’s account schema |

## You are done when

- [ ] `MNB-Salesforce-CRM-Live` aggregates cleanly
- [ ] Helen’s and Priya’s cubes show correlated CRM-Live links
- [ ] Live SCIM curl spot-checks `helen.ross` → `externalId` `MNB00001` (and Priya → `MNB00090`)
- [ ] You’ve frozen the CSV `MNB-Salesforce-CRM` path (no new activity)
- [ ] `./tools/lab/enterprise/verify-lesson.sh 210` hard asserts PASS

## Control note

- **Control:** SaaS SCIM onboarding + deliberate legacy-app retirement discipline
- **Owner:** IAM Ops
- **SLA (lab):** cut over to live SCIM within the same session; CSV path frozen, not deleted
- **Evidence:** `~/iiq-lab-evidence/sandbox/210/` — SCIM curl spot-check output, aggregation Task Result, correlated cube screenshot

## Quick check

1. Which field is the correlation key — `id` or `externalId`? → `externalId`
2. Why might a terminated persona be legitimately missing from the CRM feed? → the generator excludes `status: "terminated"` on purpose
3. What should you do with the CSV `MNB-Salesforce-CRM` app going forward? → leave it as historical evidence, stop adding new activity to it

## Feedback

Could you explain `externalId` vs `id` vs `userName` on a SCIM User without looking? If aggregation count looked “too low,” note whether the missing people were terminated in the identity master — that is usually the lesson, not a bug.

## Navigate

- Previous: [Lesson 209](209-wire-webservices.md)
- Next: [Lesson 211](211-keycloak-okta-shaped.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
