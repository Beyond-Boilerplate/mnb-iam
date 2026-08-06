# Lesson 209 — Wire Portal Web Services

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~50 minutes  
**Prereq:** Lesson 202  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 68

> **Why:** Custom in-house bank APIs — like a wire payments portal — ship as Web Services connectors, not CSVs. Build against a documented schema now — reverse-engineering the connector under pressure during an incident is how critical-risk apps fail silently.

## What this is

The Wire Portal is a custom, in-house Meridian application. Unlike `MNB-Workday` or `MNB-CoreBanking`, the enterprise pack does **not** hand you a ready Web Services Application for it — you **build** the connector yourself, the way you would for any bespoke bank API.

`connector-mock` serves it two ways at `http://connector-mock:8091`:

| Surface | Path | Notes |
| --- | --- | --- |
| Plain REST | `GET /users` | Backed by `lab-data/connectors/webservices/sample-users.json` — `{id, username, email, employeeId, active, entitlements[]}` |
| SCIM 2.0 | `/scim/v2/Users` | Supports `PATCH` for `active` — Lesson 238 goes deeper |

You’ll aggregate the plain REST shape here. (Core Path may still have a Delimited File `MNB-WirePortal` CSV app — leave it; this lesson’s Web Services app is the live path.)

## Know these

- Seeded users:
  - `priya.wire` — `employeeId` `MNB00090`, entitlement `WIRE_INIT`
  - `marcus.approve` — `employeeId` `MNB00091`, entitlement `WIRE_APPR`
- Two separate stores for the “same” app: plain REST and SCIM — flipping one does **not** flip the other.
- Schema flags that make entitlements governable: `entitlement="true"` `managed="true"` `multi="true"` on `entitlements`.
- **Response Mapping is required** on the Account Aggregation endpoint — map each schema attribute to its JSON field (same names is fine: `id`→`id`, `username`→`username`, …). Without it, **Test Connection can succeed while Preview and Aggregation return zero accounts**.
- Schema must include the **identity** and **display** attributes as real `AttributeDefinition`s (`id`, `username`) — setting them only as identity/display dropdowns is not enough.
- Turn **Enable Has More** / paging **off** for this non-paged mock (`enableHasMore=false`).
- IIQ calls `connector-mock` by its Docker service name, never `localhost`.
- **Wrong way:** Trusting Test Connection alone — it only proves HTTP `2xx`, not that IIQ can parse accounts.

## Intent

- Read the mock’s REST users feed and understand its flat schema before wiring a connector.
- Build a Web Services Application in IIQ from scratch (base URL, endpoint, schema, **Response Mapping**).
- Aggregate and correlate wire users to identities by `employeeId`.
- Flip a user’s `active` flag via the SCIM `PATCH` surface and prove the change does **not** affect the plain REST feed.

## Before you start

- [ ] `connector-mock` healthy:

```bash
curl -sf http://localhost:8091/health
```

- [ ] IIQ admin access to create a new Application from scratch
- [ ] `curl` + `python3` available
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/209
```

## Do this

### Task 1 — Read the live REST feed first

Smallest possible “custom API” shape — know it before you wire a connector.

```bash
curl -s http://localhost:8091/users | python3 -m json.tool
```

| Field | Role |
| --- | --- |
| `id` | Native account identity |
| `username` | Display |
| `email` | Contact |
| `employeeId` | **Correlation key** → identity `userId` |
| `active` | Boolean lifecycle |
| `entitlements[]` | Governable entitlements |

- **Why:** schema and Response Mapping come from this JSON — not from guessing UI labels.
- **Expect:** `priya.wire` and `marcus.approve` both visible with their `employeeId` / entitlement.

### Task 2 — Create the Web Services Application

IIQ calls this from inside the container network — `localhost:8091` would resolve to the IIQ container itself.

1. **Applications → Application Definition → New → Web Services**
2. Name: `MNB-WirePortal`
3. `genericWebServiceBaseUrl`: `http://connector-mock:8091`

- **Why:** Docker service name is required; host `localhost` is wrong from IIQ’s POV.
- **Expect:** base URL saved (connection test comes later).

### Task 3 — Add Test Connection and Account Aggregation endpoints

1. Method `GET`, operation type **Account Aggregation**, context URL `/users`, root path `$.users`
2. Second endpoint for **Test Connection** at the same path (root path optional for Test Connection)

- **Why:** the simplest smoke check for a read-only mock reuses the aggregation path.
- **Expect:** both endpoints saved.

### Task 4 — Define the account schema by hand

Add each as a real `AttributeDefinition` — identity/display dropdowns alone are not enough.

| Attribute | Notes |
| --- | --- |
| `id` | Native identity attribute |
| `username` | Display attribute |
| `email` | — |
| `employeeId` | Correlation |
| `active` | Boolean |
| `entitlements` | `entitlement="true"` `managed="true"` `multi="true"` |

- **Why:** those flags make `WIRE_INIT` / `WIRE_APPR` governable instead of plain strings.
- **Expect:** schema attributes saved with correct flags.

### Task 5 — Add Response Mapping on Account Aggregation

IIQ does not invent account rows from `rootPath` alone — Response Mapping binds each JSON object to the schema.

On the **Account Aggregation** endpoint, open **Response Mapping** and map:

| Schema attribute | JSON path / attribute |
| --- | --- |
| `id` | `id` |
| `username` | `username` |
| `email` | `email` |
| `employeeId` | `employeeId` |
| `active` | `active` |
| `entitlements` | `entitlements` |

- **Why:** skip this and Preview/Aggregation stay empty even when Test Connection is green.
- **Expect:** mapping saved on the aggregation endpoint (not only on Test Connection).

> **Watch out:** Set **Enable Has More** to **false** (WS template often defaults it on). After save, confirm `rootPath` is still `$.users` — it can clear when you close the endpoint dialog.

### Task 6 — Save, Test Connection, Preview, Aggregate

1. **Save** the Application
2. **Test Connection**
3. **Preview** (optional) — should list `priya.wire` / `marcus.approve`
4. Run **Account Aggregation** (**Setup → Tasks** if needed)

- **Why:** correlate by `employeeId` → identity `userId`, same pattern as every other live app (cubes from Lesson 207).
- **Expect:** Preview lists both users; Task Result created/updated counts > 0; both land as correlated links.

### Task 7 — Confirm WIRE_INIT on Priya’s cube

This entitlement is what Lesson 216’s birthright-vs-request logic and Lesson 224’s SoD policy both reference.

1. **Identities → Identity Warehouse → priya.wire**
2. Confirm `MNB-WirePortal` link shows entitlement `WIRE_INIT`

- **Why:** get the entitlement pipeline clean now before SoD and request labs.
- **Expect:** entitlement visible under Application Accounts / Entitlements.

### Task 8 — Optional stretch: prove SCIM is a separate store

The SCIM store and the plain REST store are two separate JSON files — flipping one does not flip the other.

```bash
curl -s -X PATCH http://localhost:8091/scim/v2/Users/wp-90 \
  -H 'Content-Type: application/json' \
  -d '{"active": false}'

curl -s "http://localhost:8091/scim/v2/Users?filter=userName%20eq%20%22priya.wire%22"
```

- **Why:** Lesson 238 goes deeper on SCIM; here you only need to see the split.
- **Expect:** SCIM record shows `active: false`; plain `/users` feed is unaffected.

### Task 9 — Close with asserts

```bash
./tools/lab/enterprise/verify-lesson.sh 209
```

- **Why:** hard checks cover Wire mock `/users` and SCIM reachable.
- **Expect:** hard asserts PASS.

## If it fails

| Symptom | Fix |
| --- | --- |
| Test Connection can’t resolve `connector-mock` | You typed `localhost`; IIQ’s container can’t see your host’s `localhost:8091` |
| Test Connection OK but Preview / Aggregation show **zero** accounts | Missing **Response Mapping** on Account Aggregation — add `id`/`username`/… maps; confirm `rootPath` is still `$.users` after save; set Enable Has More = false |
| Aggregation returns a schema mismatch / empty list | Double-check `rootPath` / context URL exactly match `$.users` and `/users`; schema must include AttributeDefinitions for `id` and `username` |
| Entitlements aggregate as plain strings | You forgot `entitlement="true"` `managed="true"` on the schema attribute; re-save and refresh the Entitlement Catalog |
| PATCH to `/scim/v2/Users/wp-90` returns 404 | List `/scim/v2/Users` first to confirm Priya’s exact SCIM-store id |
| Test Connection 500s | Mock returns `2xx` for known paths and `404` for unknown ones; a `500` means the context URL is misspelled |

## You are done when

- [ ] You’ve built `MNB-WirePortal` from scratch (no XML import for the WS app)
- [ ] Account Aggregation has **Response Mapping** (not just `rootPath` + schema)
- [ ] Both wire personas aggregate with correlated `employeeId` links
- [ ] You’ve independently proven the SCIM surface’s `PATCH /active` behaves differently from the plain REST feed
- [ ] `./tools/lab/enterprise/verify-lesson.sh 209` hard asserts PASS

## Control note

- **Control:** Custom API onboarding standard — schema-defined connector build, not ad hoc reverse-engineering
- **Owner:** IAM Engineering
- **SLA (lab):** new in-house app onboarded and correlated within the same session it’s requested
- **Evidence:** `~/iiq-lab-evidence/sandbox/209/` — schema screenshot, aggregation Task Result, SCIM PATCH before/after

## Quick check

1. What hostname must the Application use for the mock, and why? → `connector-mock` (Docker service name — `localhost` resolves to the IIQ container itself)
2. What schema flags make `entitlements` governable? → `entitlement="true"` `managed="true"` `multi="true"`
3. Why doesn’t a SCIM `PATCH` show up on the plain `/users` feed? → they’re two separate JSON stores for the same app
4. Test Connection works but Preview is empty — what’s missing? → **Response Mapping** on Account Aggregation (and usually `rootPath` + identity/display AttributeDefinitions)

## Feedback

Could you rebuild the Web Services schema from the `/users` JSON without looking? If entitlements didn’t show as managed, note whether you refreshed the Entitlement Catalog after saving the schema flags.

## Navigate

- Previous: [Lesson 208](208-jdbc-core-banking.md)
- Next: [Lesson 210](210-crm-scim.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
