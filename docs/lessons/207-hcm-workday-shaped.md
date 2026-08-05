# Lesson 207 — Authoritative HCM (Workday-Shaped)

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~55 minutes  
**Prereq:** Lesson 202  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 77

> **Why (1–2 lines):** Lifecycle should be driven by HR API events, not by someone hand-editing a CSV forever. An examiner testing joiner controls wants to see a real API event turn into a real cube — not a fixture file someone remembered to update.

## What this is

`MNB-Workday` is a `Web Services` connector application (`sailpoint.connector.webservices.WebServicesConnector`, `authoritative="true"`) pointed at `http://connector-mock:8091/hcm/v1` — a Workday-**shaped** REST API served by `tools/connector-mock/serve.py`, not the native Workday connector (that requires a real Workday tenant, out of scope per the Feasibility Boundaries in [`ENTERPRISE-LAB-V2.md`](../ENTERPRISE-LAB-V2.md)). It has two configured endpoints: `GET /workers` for account aggregation and Test Connection (root path `$.workers`). The mock also exposes `POST /hcm/v1/workers` (create/upsert a worker) and `PATCH /hcm/v1/workers/{id}` (update fields or flip `active`/`status`) — those two verbs let you *drive* joiner/mover/leaver scenarios instead of only reading a static snapshot. This is the authoritative source for identity cubes in this estate: the one application marked `authoritative="true"`, meaning IIQ creates new identity cubes directly from its aggregation — the same role `MNB-HR` plays in Core Path.

## Know these

- Schema mapping: `id` → identity native key, `userName` → login/display, `managerId` → manager reference (`managerAttribute`).
- `authoritative="true"` + aggregation creates account links; **Identity Refresh** is what promotes them into cube attributes and new cubes.
- `hcm-scenario.sh joiner <username> <first> <last> <email> [department]` POSTs a real joiner event to the mock.
- **Wrong way:** Editing `lab-data/connectors/hcm/workers.json` by hand to simulate a joiner — that bypasses the live API entirely; the point of this lesson is driving lifecycle through `POST`/`PATCH`, the same verbs a real HR system would call.

## Intent

- Read the mock HCM API directly with `curl` before ever touching IIQ, so you know what "authoritative" data actually looks like on the wire.
- Aggregate `MNB-Workday` and confirm the schema mapping (`id`→identity native key, `userName`→login, `managerId`→manager reference).
- Drive a real joiner through the HCM mock's `POST` endpoint and watch a brand-new identity cube appear after aggregate + refresh.
- Explain, in one sentence, why this is "Workday-shaped" rather than "the Workday connector."

## Before you start

- [ ] `connector-mock` healthy: `curl -sf http://localhost:8091/health`
- [ ] `MNB-Workday` Application exists in IIQ (Lesson 202 seed)
- [ ] `python3` available for pretty-printing JSON
- [ ] Evidence dir: `mkdir -p ~/iiq-lab-evidence/sandbox/207`

## Do this

1. Read the live feed before touching IIQ: `curl -s http://localhost:8091/hcm/v1/workers | python3 -m json.tool | head -40`.  
   **Why:** know the shape (`{"total": N, "workers": [{"id": "MNB00001", "workerId": "MNB00001", "userName": "helen.ross", "managerId": null, "active": true, "status": "Active", ...}]}`) before trusting IIQ's aggregated view of it.  
   **Expect:** Helen's record visible with `managerId: null`.

2. In IIQ, open **Applications → Application Definition → MNB-Workday**, click **Test Connection**, then run **Account Aggregation**.  
   **Why:** Test Connection hits `GET /workers` and expects `2xx` — cheapest possible smoke check before a full aggregation.  
   **Expect:** both succeed.

3. Confirm the schema mapping in the Application definition: `id` is `identityAttribute`, `userName` is `displayAttribute`, `managerId` is `managerAttribute`.  
   **Why:** this is how IIQ builds manager hierarchy straight from HR data instead of a separate lookup step.  
   **Expect:** all three fields set as described.

4. Run an **Identity Refresh**.  
   **Why:** aggregation alone only creates account links — `authoritative="true"` plus refresh is what promotes them into cube attributes.  
   **Expect:** refresh Task Result succeeds.

5. Drive a joiner through the live API: `./tools/lab/enterprise/hcm-scenario.sh joiner e2e.sandbox E2E Sandbox e2e.sandbox@meridiannb.com 'Identity & Access'`.  
   **Why:** POSTs to `/hcm/v1/workers` with `userName`/`firstName`/`lastName`/`email`/`department`, getting back a fresh mock-generated `id` — this is the real lifecycle event, not a fixture edit.  
   **Expect:** script prints the new worker's generated `id`.

6. Confirm the new worker exists at the source: `curl -s http://localhost:8091/hcm/v1/workers | python3 -m json.tool | grep -A3 e2e.sandbox`.  
   **Why:** verify the API-level truth before chasing it in IIQ.  
   **Expect:** `e2e.sandbox`'s record visible in the raw feed.

7. Re-run **Account Aggregation** on `MNB-Workday`, then **Identity Refresh** with "create identities" enabled, then search **Identities → Identity Warehouse** for `e2e.sandbox`.  
   **Why:** proves a brand-new cube can be sourced entirely from a live HCM API POST, with no CSV involved anywhere in the chain.  
   **Expect:** a new cube exists for `e2e.sandbox`.

8. State the "shaped, not native" distinction out loud: this proves the *pattern* (authoritative HR-as-a-service, `PATCH` for lifecycle events, manager attribute wiring), not Workday's actual SOAP/REST APIs, auth model, or report-writer exports.  
   **Expect:** you can say this in one sentence without notes.

## If it fails

- **Test Connection fails** — confirm `connector-mock` is up: `curl -sf http://localhost:8091/health`.
- **Aggregation runs but zero accounts appear** — the mock's `rootPath` (`$.workers`) must match the live JSON exactly; if you hand-edited `workers.json` and broke the array, regenerate via Lesson 202's generator instead.
- **New joiner never shows as an identity cube** — you aggregated but skipped Identity Refresh, or refresh ran without "create identities" enabled.
- **`hcm-scenario.sh joiner` errors with usage text** — the exact form is `joiner <username> <first> <last> <email> [department]`.
- **Manager hierarchy looks wrong after aggregation** — `managerId` values are HCM `id`s, not names; a manager not yet aggregated leaves the chain incomplete until their own worker record is pulled in.

## You are done when

`e2e.sandbox` exists as a real identity cube in IIQ, sourced purely from a live `POST` to the HCM mock followed by aggregate + refresh, and you can name the one Application attribute (`managerId` → `managerAttribute`) that makes manager hierarchy work automatically.

## Control note

- **Control:** Authoritative HR source integrity — joiner event reaches a governed cube.
- **Owner:** HRIS / IAM Ops.
- **SLA (lab):** joiner visible as a cube in the same session; production target is typically same-day.
- **Evidence:** `~/iiq-lab-evidence/sandbox/207/` — `curl` output before/after, aggregation and refresh Task Result ids.

## Quick check

1. What flag on `MNB-Workday` makes it create new cubes, not just links? → `authoritative="true"` (plus a refresh with "create identities").
2. What verb drives a lifecycle event without editing a fixture? → `POST /hcm/v1/workers` (or `PATCH` for updates).
3. What's the one-sentence "shaped vs native" distinction? → it proves the pattern (authoritative HR API + manager wiring), not real Workday's auth/API surface.

## Navigate

- Previous: Lesson 206
- Next: Lesson 208
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
