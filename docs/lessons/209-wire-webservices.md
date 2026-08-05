# Lesson 209 — Wire Portal Web Services

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~50 minutes  
**Prereq:** Lesson 202  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 68

> **Why (1–2 lines):** Custom in-house bank APIs — like a wire payments portal — ship as Web Services connectors, not CSVs. An examiner reviewing a critical-risk app wants to see the connector was built against a documented schema, not reverse-engineered under pressure during an incident.

## What this is

The Wire Portal is a custom, in-house Meridian application, not a vendor product — so unlike `MNB-Workday` or `MNB-CoreBanking`, there's no pre-built Application XML for it in `config/`. That's intentional: this lesson has you **build** the Web Services connector yourself, the way you would for any bespoke bank API. `connector-mock` serves it two ways at `http://connector-mock:8091`: a plain REST list at `GET /users` (backed by `lab-data/connectors/webservices/sample-users.json` — a simple `{id, username, email, employeeId, active, entitlements[]}` shape) and a SCIM 2.0 surface at `/scim/v2/Users` with `PATCH` support for `active`. You'll aggregate the plain REST shape here (matching the app estate's `MNB-WirePortal` entry) — Lesson 238 revisits the SCIM surface in depth.

## Know these

- Seeded users: `priya.wire` (`employeeId MNB00090`, entitlement `WIRE_INIT`), `marcus.approve` (`employeeId MNB00091`, entitlement `WIRE_APPR`).
- Two separate stores for the "same" app: plain REST (`GET /users`) and SCIM (`/scim/v2/Users`) — flipping one does not flip the other.
- Schema flags that make entitlements governable: `entitlement="true" managed="true" multi="true"` on the `entitlements` attribute.
- IIQ calls `connector-mock` by its Docker service name, never `localhost` — same rule as every other live app in this path.
- **Wrong way:** Building the schema without marking `entitlements` as `entitlement="true" managed="true"` — it aggregates as a plain string list instead of governable entitlements, and Lessons 216/224 have nothing to certify or police.

## Intent

- Read the mock's REST users feed directly and understand its flat schema before wiring a connector to it.
- Build a Web Services Application in IIQ from scratch (base URL, endpoint, schema) — no XML import to lean on.
- Aggregate and correlate wire users to identities by `employeeId`.
- Flip a user's `active` flag via the SCIM `PATCH` surface and prove the change round-trips into IIQ on re-aggregation.

## Before you start

- [ ] `connector-mock` healthy (`curl -sf http://localhost:8091/health`)
- [ ] IIQ admin access to create a new Application from scratch
- [ ] `curl` + `python3` available for reading JSON
- [ ] Evidence dir: `mkdir -p ~/iiq-lab-evidence/sandbox/209`

## Do this

1. Read the live data first: `curl -s http://localhost:8091/users | python3 -m json.tool`.  
   **Why:** this is the smallest possible "custom API" shape — an `id`, `username`, `email`, correlation key (`employeeId`), boolean `active`, and entitlement array — know it before wiring a connector.  
   **Expect:** `priya.wire` and `marcus.approve` both visible with their `employeeId`/entitlement.

2. In IIQ, **Applications → Application Definition → New → Web Services**. Name it `MNB-WirePortal`. Set `genericWebServiceBaseUrl` to `http://connector-mock:8091`.  
   **Why:** IIQ calls this from inside the container network — `localhost:8091` would resolve to the IIQ container itself, not the mock.  
   **Expect:** base URL saved without a connection test yet.

3. Add an endpoint: method `GET`, operation type Account Aggregation, context URL `/users`, root path `$.users`. Add a second endpoint for Test Connection at the same path.  
   **Why:** the simplest possible smoke check for a read-only mock reuses the aggregation path.  
   **Expect:** both endpoints saved.

4. Define the account schema by hand from step 1: `id` (native identity attribute), `username` (display attribute), `email`, `employeeId`, `active` (boolean), `entitlements` (`entitlement="true" managed="true" multi="true"`).  
   **Why:** these flags are what make `WIRE_INIT`/`WIRE_APPR` show up as governable entitlements instead of plain strings.  
   **Expect:** schema attributes saved with correct flags.

5. Save, **Test Connection**, then run **Account Aggregation**.  
   **Why:** correlate by `employeeId` → identity `userId`, same pattern as every other live app.  
   **Expect:** both `priya.wire` and `marcus.approve` land as correlated account links.

6. Open `priya.wire`'s cube and confirm the `MNB-WirePortal` link shows entitlement `WIRE_INIT`.  
   **Why:** this is the entitlement Lesson 216's birthright-vs-request logic and Lesson 224's SoD policy both reference — get it clean now.  
   **Expect:** entitlement visible under Application Accounts/Entitlements.

7. Optional stretch — prove the SCIM surface independently: `curl -s -X PATCH http://localhost:8091/scim/v2/Users/wp-90 -H 'Content-Type: application/json' -d '{"active": false}'`, then `curl -s "http://localhost:8091/scim/v2/Users?filter=userName%20eq%20%22priya.wire%22"`.  
   **Why:** the SCIM store and the plain REST store are two separate JSON files — flipping one does not flip the other, exactly the "two systems of record for the same app" mess real integrations create.  
   **Expect:** SCIM record shows `active: false`; the plain `/users` feed is unaffected.

## If it fails

- **Test Connection can't resolve `connector-mock`** — you typed `localhost`; IIQ's container can't see your host's `localhost:8091`, only the internal network.
- **Aggregation returns a schema mismatch / empty list** — double check `rootPath`/context URL exactly match `$.users` and `/users`; a stray trailing slash silently returns zero rows.
- **Entitlements aggregate as plain strings** — you forgot `entitlement="true" managed="true"` on the schema attribute; re-save and refresh the Entitlement Catalog for this app.
- **PATCH to `/scim/v2/Users/wp-90` returns 404** — list `/scim/v2/Users` first to confirm Priya's exact SCIM-store id (it may differ from the REST-store `id`).
- **Test Connection 500s** — the mock returns `2xx` for known paths and `404` for unknown ones; a `500` means the context URL is misspelled.

## You are done when

You've built `MNB-WirePortal` from scratch (no XML import), both wire personas aggregate with correlated `employeeId` links, and you've independently proven the SCIM surface's `PATCH /active` behaves differently from the plain REST feed.

## Control note

- **Control:** Custom API onboarding standard — schema-defined connector build, not ad hoc reverse-engineering.
- **Owner:** IAM Engineering.
- **SLA (lab):** new in-house app onboarded and correlated within the same session it's requested.
- **Evidence:** `~/iiq-lab-evidence/sandbox/209/` — schema screenshot, aggregation Task Result, SCIM PATCH before/after.

## Quick check

1. What hostname must the Application use for the mock, and why? → `connector-mock` (Docker service name — `localhost` resolves to the IIQ container itself).
2. What schema flags make `entitlements` governable? → `entitlement="true" managed="true" multi="true"`.
3. Why doesn't a SCIM `PATCH` show up on the plain `/users` feed? → they're two separate JSON stores for the same app.

## Navigate

- Previous: Lesson 208
- Next: Lesson 210
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
