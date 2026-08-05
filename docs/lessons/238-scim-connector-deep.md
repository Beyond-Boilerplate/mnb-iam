# Lesson 238 — SCIM Connector Depth

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~50 minutes  
**Prereq:** Lesson 210  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 69–70

> **Why:** Filter/patch/schema skills transfer directly to Okta/Entra-class IdPs — the generic SCIM template's schema discovery doesn't always match what a real IdP returns.

## What this is

`MNB-Okta` and `MNB-Salesforce-CRM-Live` both use IIQ's generic SCIM 2.0 template (`scimProvider="generic"`) against connector-mock's `/scim/v2/Users` and `/crm/scim/v2/Users` endpoints. SCIM's advantage over WS is standard verbs — filtered `GET`, `PATCH` for partial updates. This lesson exercises filtered read, a live PATCH, and documents exactly where IIQ's schema map disagrees with the mock's real attributes.

## Know these

| SCIM field | Mock behavior |
| --- | --- |
| `emails` | May be a string or array of objects — check before assuming |
| `groups` | CRM declares it; not every app schema does |
| `active` (PATCH) | Simulates an out-of-band deactivation from the IdP side |

**Wrong way:** Blaming IIQ's aggregation filter before confirming with a raw `curl` that the mock even supports the filter syntax you're using.

## Intent

- Run a SCIM filter query by hand with `curl` before trusting IIQ's aggregation filter.
- Aggregate with the same filter applied inside IIQ, if supported.
- PATCH a user's `active` flag directly against the mock and re-aggregate to see the change land.
- Compare the mock's real schema fields to IIQ's configured attribute map and note any gaps.

## Before you start

- [ ] Lesson 210 `MNB-Okta`/CRM SCIM aggregating cleanly
- [ ] `connector-mock` reachable at `http://localhost:8091`
- [ ] Know `priya.wire`'s SCIM `id` (UUID, not username)
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/238`

## Do this

1. `curl -s "http://localhost:8091/scim/v2/Users?filter=userName%20eq%20%22priya.wire%22" | python3 -m json.tool`.  
   **Expect:** Single-user JSON — confirms the mock supports SCIM filter syntax before you blame IIQ.
2. Note the exact JSON shape — is `emails` a string or array of objects; does `groups` appear at all (compare to `MNB-Salesforce-CRM-Live`'s multi-valued `groups`).  
   **Expect:** You can describe the shape precisely.
3. **Applications → Application Definition → MNB-Okta → Aggregation**, check for a filter expression field; if present, set the same filter and run a scoped aggregation.  
   **Expect:** Only that one account imports.
4. `curl -s -X PATCH "http://localhost:8091/scim/v2/Users/<id>" -H 'Content-Type: application/json' -d '{"Operations":[{"op":"replace","path":"active","value":false}]}'` (substitute the real `id` from step 1).  
   **Expect:** 200 response — simulates an IdP-side deactivation outside IIQ.
5. Re-aggregate `MNB-Okta` (full, not filtered).  
   **Expect:** The identity's link shows `active:false`/disabled — re-aggregation picks up externally-made changes.
6. Compare the mock's returned fields (`id`, `userName`, `active`, `emails`, `externalId`) against `MNB-Application-Okta.xml`'s declared schema; write one line on what a real Okta tenant would also send (`groups`, `name.givenName/familyName`, `meta`) that this mock omits.  
   **Expect:** Gap note saved.
7. Save the filter query result, the PATCH response, and your schema-gap note under `~/iiq-lab-evidence/sandbox/238/`.

## If it fails

- **Filter query returns 400/empty** — the mock may only support exact `eq` on `userName`; check URL-encoding (`%22` for quotes) or drop the filter to confirm the endpoint works at all.
- **IIQ aggregation filter field not present** — not every SCIM template exposes a UI filter; fall back to full aggregation and treat step 1's curl as your filter proof.
- **PATCH accepted (200) but re-aggregation shows no change** — confirm you PATCHed the correct `id` (SCIM ids are UUIDs, not usernames); re-run step 1's GET.

## You are done when

You've run a real SCIM filter, applied a live PATCH that changed data on re-aggregation, and written down where the mock's schema differs from a real Okta-class IdP.

## Control note

- **Control:** SCIM schema-gap awareness before onboarding a real IdP.  
- **Owner:** IAM Engineering.  
- **SLA (lab):** Gap documented before treating mock schema as production-ready.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/238/` — filter result, PATCH response, gap note.

## Quick check

1. What SCIM verb enables partial updates? → `PATCH`.  
2. Is `groups` guaranteed present on every SCIM app schema here? → No — CRM declares it, `MNB-Okta` may not.  
3. Why curl the filter by hand first? → Confirms the mock supports the syntax before blaming IIQ's aggregation config.

## Navigate

- Previous: Lesson 237
- Next: Lesson 239
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
