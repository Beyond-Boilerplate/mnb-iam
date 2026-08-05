# Lesson 247 — IIQ REST & SCIM Live

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~60 minutes  
**Prereq:** Lesson 246  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 100

> **Why:** External tools integrate through IIQ's own APIs. A ticketing system or BI dashboard has no Meridian plugin — it calls IIQ's OOTB REST/SCIM directly, and that data must match the UI exactly.

## What this is

Lesson 246 exercised Meridian's custom plugin/MCP surface. This lesson uses IIQ's **own** OOTB REST API and, if enabled, its SCIM 2.0 endpoint — the interfaces a real external tool would call with no Meridian-specific plugin installed. You authenticate two ways, pull identity data through both OOTB REST and SCIM, and cross-check every result against the same identity's Warehouse UI page.

## Know these

| Interface | Base | Auth |
| --- | --- | --- |
| OOTB REST | `http://localhost:8080/identityiq/rest/` | Basic (`spadmin:admin`) baseline |
| SCIM 2.0 | `http://localhost:8080/identityiq/scim/v2/` | Same, if enabled on your build |
| Token/OAuth | `Setup → REST API Keys` | Optional, "how it'd really be done" |

**Wrong way:** Assuming SCIM is broken because it 404s — check the actual config flag first; not-licensed/not-enabled is a valid, recordable outcome, not a bug.

## Intent

- Call IIQ's OOTB identity search REST endpoint as `spadmin` and get a real result.
- If SCIM is enabled, list Users via `/scim/v2/Users` and compare the shape to the custom REST call.
- Cross-check both API results against the Identity Warehouse UI for the same person.
- Record which authentication method you actually used and why the other wasn't available/needed.

## Before you start

- [ ] `spadmin:admin` Basic auth confirmed working
- [ ] `docs/api/UI-VS-API-GAPS.md` available for reference
- [ ] Two identities picked to cross-check (`helen.ross`, `priya.wire`)
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/247`

## Do this

1. `curl -s -u spadmin:admin "http://localhost:8080/identityiq/rest/identities?q=helen.ross" | python3 -m json.tool` (adjust path/query param to your version's documented resource if this 404s — check **Debug → REST API docs**).  
   **Expect:** JSON includes `name`, `email`, and at least one cross-checkable attribute.
2. Open **Identities → Identity Warehouse → helen.ross** in the UI.  
   **Expect:** Same field values match the REST response exactly — department, manager name.
3. If SCIM 2.0 is enabled (**Global Settings → SCIM Configuration** or attempt directly): `curl -s -u spadmin:admin "http://localhost:8080/identityiq/scim/v2/Users?filter=userName%20eq%20%22helen.ross%22" | python3 -m json.tool`.  
   **Expect:** `userName`/`emails` array shape noticeably different from the custom REST call's flat `name`/`email`.
4. If SCIM isn't enabled, record that explicitly with the actual reason (not licensed, not turned on, unsupported in this version).  
   **Expect:** A documented outcome, not a silent skip.
5. Attempt the same calls with a different auth method if supported (OAuth2 client credentials or a personal access token). Record which method actually worked.  
   **Expect:** Basic auth against `spadmin` is the fallback that should always work.
6. Repeat the REST-vs-UI cross-check for `priya.wire`.  
   **Expect:** Confirms this isn't a one-off match on Helen specifically.
7. Save both API responses, the Warehouse UI screenshots for both identities, and your auth-method note under `~/iiq-lab-evidence/sandbox/247/`.

## If it fails

- **404 on the identity search REST path** — confirm the exact resource path for your IIQ build (some versions use `filter` instead of `q`); check `docs/api/UI-VS-API-GAPS.md` before assuming the API is broken.
- **401 on Basic auth** — confirm `spadmin`'s password matches Lesson 201's setup (default `admin` unless changed).
- **SCIM endpoint returns 404 everywhere** — may simply not be enabled/licensed; a valid "record and move on" outcome.
- **REST value doesn't match UI value** — check for a caching/refresh lag; force a Refresh Identity Cube and retry.

## You are done when

A REST (and SCIM, if available) read for at least two identities matches the Identity Warehouse UI exactly, and you've recorded which auth method actually worked.

## Control note

- **Control:** External-tool integration parity (API data matches UI data).  
- **Owner:** IAM Engineering.  
- **SLA (lab):** Zero drift between REST/SCIM response and Warehouse UI for the same identity.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/247/` — both API responses, UI screenshots, auth-method note.

## Quick check

1. What's the biggest visible shape difference between OOTB REST and SCIM? → Flat `name`/`email` vs `userName`/`emails` array.  
2. What should you do if SCIM 404s everywhere? → Check the config flag and record the real reason, don't assume broken.  
3. What's the auth fallback that should always work? → Basic auth as `spadmin`.

## Navigate

- Previous: Lesson 246
- Next: Lesson 248
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
