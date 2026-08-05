# Lesson 210 — CRM via SCIM Mock

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~40 minutes  
**Prereq:** Lesson 202  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 69–71

> **Why (1–2 lines):** SCIM is the reusable SaaS-account pattern — once you can aggregate one SCIM app, you can aggregate all of them. An examiner comparing your SaaS onboarding process across five vendors expects one repeatable pattern, not five bespoke integrations.

## What this is

`MNB-Salesforce-CRM-Live` is a real `SCIM 2.0` application (`sailpoint.connector.OpenConnectorAdapter`, `scimProvider generic`) against `http://connector-mock:8091/crm` — a Salesforce-**shaped** SCIM 2.0 surface, not a real Salesforce org. The mock serves `GET /crm/scim/v2/Users` from `lab-data/connectors/crm/Users.json`, which Lesson 202's generator regenerates directly from `identity-master.json`: every active (non-terminated) identity becomes a SCIM `User` resource with `userName`, `name.givenName/familyName`, `emails`, `active`, and `externalId` set to the HR `userId` — that `externalId` is the correlation key. This replaces the Core Path CSV `MNB-Salesforce-CRM` application for this path; you leave the CSV version alone (Lesson 214 explicitly calls out retiring it deliberately, not by accident) and standardize on the Live one from here forward.

## Know these

- SCIM `ListResponse` envelope: `schemas: ["urn:ietf:params:scim:api:messages:2.0:ListResponse"]`, `totalResults`, `Resources[]` — you'll see this exact shape again in Lessons 211, 213, and 238.
- Correlation key is `externalId` (e.g. `MNB00001`), not `id` (e.g. `crm-MNB00001`) or `userName`.
- The generator excludes `status: "terminated"` identities from the CRM feed on purpose — a missing terminated persona here is correct, not a bug.
- SCIM's standardized envelope is why one `sailpoint.connector.OpenConnectorAdapter` configuration pattern can front Okta, Salesforce, ServiceNow, or any other SCIM 2.0-compliant SaaS product — only the base URL and `scimProvider` value change between them.
- **Wrong way:** Continuing to run aggregation or edits against the CSV `MNB-Salesforce-CRM` "just to keep it fresh" — stale historical links are fine to leave as evidence of the migration; adding new activity to a retired app defeats the point of standardizing on Live.

## Intent

- Read the CRM SCIM feed directly and confirm it matches the identity master 1:1 (no drift).
- Aggregate `MNB-Salesforce-CRM-Live` and correlate `externalId` to identity `userId`.
- Deliberately stop using the CSV `MNB-Salesforce-CRM` for any exercise from this point forward.
- Recognize the SCIM `ListResponse` envelope shape — you'll see it again in Lessons 211, 213, and 238.

## Before you start

- [ ] Lesson 202 seed complete; `lab-data/connectors/crm/Users.json` freshly generated
- [ ] `MNB-Salesforce-CRM-Live` Application exists in IIQ
- [ ] `curl` + `python3` available
- [ ] Evidence dir: `mkdir -p ~/iiq-lab-evidence/sandbox/210`

## Do this

1. Read the feed: `curl -s http://localhost:8091/crm/scim/v2/Users | python3 -m json.tool | head -40`.  
   **Why:** confirm the standard SCIM 2.0 envelope shape — the reason one connector type covers Okta, Salesforce, and dozens of other real SaaS products.  
   **Expect:** `schemas`, `totalResults`, and a `Resources` array present.

2. Pick one resource and note its fields: `id` (e.g. `crm-MNB00001`), `userName` (`helen.ross`), `externalId` (`MNB00001` — the correlation key), `emails[0].value`, `groups[0].display` (`CRM-Users`).  
   **Why:** distinguishes the native `id` from the correlation key `externalId` before you configure anything.  
   **Expect:** all fields present and matching the identity master.

3. In IIQ, open **Applications → Application Definition → MNB-Salesforce-CRM-Live**, **Test Connection**, then **Account Aggregation**.  
   **Why:** schema's `identityAttribute` is `id`, `displayAttribute` is `userName`; `groups` is `entitlement="true" managed="true" multi="true"`.  
   **Expect:** aggregation Task Result succeeds.

4. Correlate `externalId` → identity `userId`. Open Helen's cube.  
   **Why:** confirms the correlation pattern shared across every live app in this path.  
   **Expect:** `MNB-Salesforce-CRM-Live` link present, distinct from any leftover CSV `MNB-Salesforce-CRM` link.

5. Decide, right now, to stop editing or re-running aggregation against the CSV `MNB-Salesforce-CRM` for the rest of this path.  
   **Why:** it's fine as historical evidence of the migration; adding new activity to it undermines standardizing on the Live app.  
   **Expect:** no further changes made to the CSV app from here forward.

6. Compare the SCIM feed's `totalResults` against the count of active (non-terminated) identities in `identity-master.json`.  
   **Why:** proves the generator is the actual source of truth here, not a hand-maintained fixture that can drift.  
   **Expect:** the two counts match exactly.

7. Open `priya.wire`'s cube alongside `helen.ross`'s and compare `groups[0].display` on their respective CRM-Live links.  
   **Why:** every seeded user gets the same static `CRM-Users` placeholder group in this mock — real Salesforce SCIM would carry role-specific groups, so don't over-read significance into this particular value beyond "the entitlement pipeline works."  
   **Expect:** both show `CRM-Users`; this is expected mock behavior, not a correlation bug.

## If it fails

- **Test Connection fails** — confirm the app's `host` attribute is `http://connector-mock:8091/crm` (with the `/crm` suffix — a different base path than Wire Portal's `http://connector-mock:8091` from Lesson 209).
- **Aggregation returns fewer users than expected** — the generator excludes `status: "terminated"` identities on purpose (see `write_crm_scim` in `generate-identity-artifacts.py`); this is correct, not a bug.
- **`externalId` correlation doesn't match anyone** — stale `Users.json` from before your last `identity-master.json` edit; re-run `python3 tools/lab/enterprise/generate-identity-artifacts.py` and re-aggregate.
- **Old CSV CRM links won't disappear** — expected; the point is to stop *using* the CSV path going forward, not delete historical links.
- **`groups` shows as a plain attribute, not managed** — refresh the Entitlement Catalog for this application's account schema.

## You are done when

`MNB-Salesforce-CRM-Live` aggregates cleanly, Helen's cube shows a correlated CRM-Live link with `externalId MNB00001`, and the SCIM feed's `totalResults` matches your active identity count exactly.

## Control note

- **Control:** SaaS SCIM onboarding + deliberate legacy-app retirement discipline.
- **Owner:** IAM Ops.
- **SLA (lab):** cut over to live SCIM within the same session; CSV path frozen, not deleted.
- **Evidence:** `~/iiq-lab-evidence/sandbox/210/` — feed count vs. identity-master count screenshot, correlated cube screenshot.

## Quick check

1. Which field is the correlation key — `id` or `externalId`? → `externalId`.
2. Why might a terminated persona be legitimately missing from the CRM feed? → the generator excludes `status: "terminated"` on purpose.
3. What should you do with the CSV `MNB-Salesforce-CRM` app going forward? → leave it as historical evidence, stop adding new activity to it.

## Navigate

- Previous: Lesson 209
- Next: Lesson 211
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
