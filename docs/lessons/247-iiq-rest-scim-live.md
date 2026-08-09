# Lesson 247 — IIQ REST & SCIM Live

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~80 minutes  
**Prereq:** Lesson 246  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 100

> **Why:** External tools integrate through IIQ’s own APIs. A ticketing system or BI dashboard has no Meridian plugin — it calls OOTB REST/SCIM, and that data must match the Identity Warehouse UI.

## What this is

Lesson 246 used **Meridian** `/plugin/rest/mnbToolkit/...`. This lesson uses **product** surfaces only:

| Surface | Base URL | Typical auth |
| --- | --- | --- |
| **OOTB REST** | `http://localhost:8080/identityiq/rest/` | HTTP Basic |
| **SCIM 2.0** | `http://localhost:8080/identityiq/scim/v2/` | HTTP Basic or Bearer |
| **OAuth2 token** | `http://localhost:8080/identityiq/oauth2/token` | Client id/secret → Bearer |

Nothing assumes SCIM is licensed/enabled. You will authenticate for real, call live endpoints, cross-check Warehouse UI for **two** identities, and record an honest outcome if SCIM is off.

OpenAPI references (mined): [`docs/api/openapi/openapi-ootb-rest.yaml`](../api/openapi/openapi-ootb-rest.yaml), [`openapi-scim-v2.yaml`](../api/openapi/openapi-scim-v2.yaml), [`openapi-oauth2.yaml`](../api/openapi/openapi-oauth2.yaml).

> **Watch out:** HTML login pages in `curl` output mean you are not authenticated — treat that as failure, not “empty JSON.”

## Know these

```text
Basic-auth probe → OOTB REST identity read
  → Cross-check helen.ross in Identity Warehouse
  → SCIM ServiceProviderConfig + Users filter (or record disabled)
  → Create/use OAuth client → token → Bearer SCIM/REST call
  → Repeat Warehouse cross-check for priya.wire
  → Auth-method note + JSON/screenshots under evidence
```

| Term | Plain English | Meridian example |
| --- | --- | --- |
| **OOTB REST** | Product JAX-RS under `/identityiq/rest` | Identity / work item helpers |
| **SCIM 2.0** | Standard Users/Groups-style API | `/scim/v2/Users?filter=userName eq "..."` |
| **Basic auth** | `Authorization: Basic …` (`spadmin:admin`) | Lab default |
| **OAuth2 client credentials** | App id+secret → access token | Bearer on SCIM |
| **Drift** | API field ≠ Warehouse UI | Fail the control |

- **Wrong way:** Assuming SCIM 404 means “IIQ is broken” without checking enablement.  
- **Wrong way:** Comparing toolkit `/mnbToolkit/enterprise/jml` to SCIM and calling them the same contract.  
- **Wrong way:** Paper-only “we would use OAuth” with zero token request.  
- **Wrong way:** Checking only Helen once and declaring parity.

## Intent

- Authenticate with Basic and (when possible) OAuth Bearer.  
- Read identity data via OOTB REST and SCIM (or document SCIM off).  
- Prove API attributes match Warehouse for `helen.ross` and `priya.wire`.  
- Leave an auth-method note an integrator could follow.

## Before you start

Complete every checkbox. Do not skip into Task 1 until these are true.

- [ ] IIQ up: [http://localhost:8080/identityiq](http://localhost:8080/identityiq) — `spadmin` / `admin`
- [ ] Cubes exist: `helen.ross`, `priya.wire` (aggregate/refresh Workday if missing)
- [ ] Lesson 246 toolkit ping still works (stack healthy) — optional but useful
- [ ] Reference: [`docs/api/UI-VS-API-GAPS.md`](../api/UI-VS-API-GAPS.md) if a path 404s
- [ ] Evidence dir:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/247
```

## Do this

### Task 1 — Basic auth probe (fail fast)

```bash
curl -sS -u 'spadmin:admin' -D - -o /tmp/iiq-rest-probe.body \
  'http://localhost:8080/identityiq/rest/identities' \
  | head -40
file /tmp/iiq-rest-probe.body
head -c 200 /tmp/iiq-rest-probe.body; echo
```

- **Why:** proves Basic works before you chase filter syntax.  
- **Expect:** HTTP **200** (or **405** if GET-not-allowed on that exact resource) — **not** 401 and **not** an HTML login form.

If **401**: fix `spadmin` password.  
If HTML login: add headers some builds want:

```bash
curl -sS -u 'spadmin:admin' \
  -H 'Accept: application/json' \
  -H 'X-Requested-With: XMLHttpRequest' \
  'http://localhost:8080/identityiq/rest/identities'
```

Save the working probe under `rest-probe-headers.txt`.

### Task 2 — OOTB REST identity read for Helen

IIQ versions differ on query params. Try **in order** until you get Helen’s JSON (not an empty unrelated list):

```bash
# A — common name path
curl -sS -u 'spadmin:admin' -H 'Accept: application/json' \
  'http://localhost:8080/identityiq/rest/identities/helen.ross' \
  | tee ~/iiq-lab-evidence/sandbox/247/rest-helen.json \
  | python3 -m json.tool | head -60
```

```bash
# B — query style (if A 404s)
curl -sS -u 'spadmin:admin' -H 'Accept: application/json' \
  'http://localhost:8080/identityiq/rest/identities?name=helen.ross' \
  | tee ~/iiq-lab-evidence/sandbox/247/rest-helen.json \
  | python3 -m json.tool | head -60
```

If both fail, open **Debug** / product REST docs on your build and use the documented identity-get path — still save raw JSON as `rest-helen.json`.

Extract and write down:

```text
REST path used: ________
name / displayName: ________
email (if present): ________
manager (if present): ________
inactive / status: ________
```

- **Why:** integrators need a reproducible path, not “whatever worked once.”  
- **Expect:** JSON clearly about `helen.ross`.

### Task 3 — Cross-check Warehouse UI (Helen)

1. **Identities → Identity Warehouse → helen.ross**  
2. Compare name, email, manager, inactive/status to Task 2  
3. Screenshot Attributes header → `ui-helen.png`  
4. Note any drift (blank in API but present in UI is still a finding)

- **Why:** control is **parity**, not “API returned 200.”  
- **Expect:** no material drift on the fields you listed.

### Task 4 — SCIM ServiceProviderConfig (enablement probe)

```bash
curl -sS -u 'spadmin:admin' -H 'Accept: application/scim+json' \
  'http://localhost:8080/identityiq/scim/v2/ServiceProviderConfig' \
  | tee ~/iiq-lab-evidence/sandbox/247/scim-spc.json \
  | python3 -m json.tool | head -80
```

| Result | Meaning | What you do |
| --- | --- | --- |
| **200** + schemas/patch config | SCIM live | Continue Task 5 |
| **404** / not found | Not enabled or not in this WAR | Task 4b |
| **401/403** | Auth/capability | Fix rights; retry |

#### Task 4b — If SCIM is not available

1. As `spadmin`, check **Gear → Global Settings** for **SCIM** / API / platform options (label varies)  
2. Write `scim-status.txt`:

```text
SCIM /scim/v2/ServiceProviderConfig result: ________
Reason: not enabled | not licensed | capability missing | other: ________
UI setting checked: ________
```

That **is** a valid completion for the SCIM half — do not fake Users JSON.

- **Why:** “record the real reason” beats pretending SCIM worked.  
- **Expect:** either SPC JSON or an honest status file.

### Task 5 — SCIM Users filter for Helen (when Task 4 succeeded)

```bash
curl -sS -u 'spadmin:admin' \
  -H 'Accept: application/scim+json' \
  'http://localhost:8080/identityiq/scim/v2/Users?filter=userName%20eq%20%22helen.ross%22&count=1' \
  | tee ~/iiq-lab-evidence/sandbox/247/scim-helen.json \
  | python3 -m json.tool | head -100
```

Compare shape to OOTB REST:

| SCIM (typical) | OOTB REST (typical) |
| --- | --- |
| `userName`, `emails[]`, `active`, `name.givenName` | Flat `name` / `email` / display fields |
| `schemas`: `urn:ietf:params:scim:schemas:core:2.0:User` | Product-specific JSON |

Cross-check `userName` / emails / `active` against Warehouse (Task 3).

- **Why:** external ITSM tools speak SCIM shape, not Meridian toolkit shape.  
- **Expect:** one User resource for Helen; fields match UI.

### Task 6 — OAuth2 client + Bearer token (live auth #2)

Basic is the lab fallback. Integrators prefer tokens.

1. As `spadmin`: **Gear → Global Settings → API Authentication** / **OAuth** / **OAuth clients** (label varies by 8.5 build)  
2. **Create** a client (or open an existing lab client):
   - **Name:** `MNB-Lab-247-SCIM`  
   - Grant type: **Client Credentials** (or the closest machine grant your UI offers)  
   - Assign capabilities/rights sufficient for SCIM read / REST read (often includes SCIM or admin-equivalent lab right)  
3. Copy **client id** and **client secret** once into your evidence notes (do not commit secrets to git)

Token request:

```bash
export MNB_OAUTH_CLIENT_ID='PASTE_ID'
export MNB_OAUTH_CLIENT_SECRET='PASTE_SECRET'

curl -sS -u "${MNB_OAUTH_CLIENT_ID}:${MNB_OAUTH_CLIENT_SECRET}" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=client_credentials' \
  'http://localhost:8080/identityiq/oauth2/token' \
  | tee ~/iiq-lab-evidence/sandbox/247/oauth-token.json \
  | python3 -m json.tool
```

If the token endpoint wants form fields instead of Basic client auth, use the variant your UI documents, for example:

```bash
curl -sS -H 'Content-Type: application/x-www-form-urlencoded' \
  -d "grant_type=client_credentials&client_id=${MNB_OAUTH_CLIENT_ID}&client_secret=${MNB_OAUTH_CLIENT_SECRET}" \
  'http://localhost:8080/identityiq/oauth2/token' \
  | tee ~/iiq-lab-evidence/sandbox/247/oauth-token.json \
  | python3 -m json.tool
```

Extract `access_token`, then call SCIM (or REST) with Bearer:

```bash
TOKEN=$(python3 -c 'import json;print(json.load(open("'"$HOME"'/iiq-lab-evidence/sandbox/247/oauth-token.json"))["access_token"])')

curl -sS -H "Authorization: Bearer ${TOKEN}" \
  -H 'Accept: application/scim+json' \
  'http://localhost:8080/identityiq/scim/v2/Users?filter=userName%20eq%20%22helen.ross%22&count=1' \
  | tee ~/iiq-lab-evidence/sandbox/247/scim-helen-bearer.json \
  | python3 -m json.tool | head -60
```

If OAuth UI/token is unavailable in this lab image, write in `auth-methods.txt`:

```text
OAuth client credentials: NOT AVAILABLE — reason: ________
Fallback used: HTTP Basic spadmin
```

- **Why:** “how it would really be done” must include at least one token attempt or a concrete blocker.  
- **Expect:** Bearer call works **or** documented blocker + Basic still proven.

### Task 7 — Repeat REST (+ SCIM if enabled) for `priya.wire`

```bash
curl -sS -u 'spadmin:admin' -H 'Accept: application/json' \
  'http://localhost:8080/identityiq/rest/identities/priya.wire' \
  | tee ~/iiq-lab-evidence/sandbox/247/rest-priya.json \
  | python3 -m json.tool | head -60
```

If you used query style for Helen, use the **same** path pattern for Priya.

When SCIM is on:

```bash
curl -sS -u 'spadmin:admin' -H 'Accept: application/scim+json' \
  'http://localhost:8080/identityiq/scim/v2/Users?filter=userName%20eq%20%22priya.wire%22&count=1' \
  | tee ~/iiq-lab-evidence/sandbox/247/scim-priya.json \
  | python3 -m json.tool | head -80
```

1. Open Warehouse → `priya.wire` → screenshot `ui-priya.png`  
2. Confirm name/email/department/manager parity for the fields your API returns  

- **Why:** one identity can be a lucky match; two identities prove the method.  
- **Expect:** Priya parity recorded the same way as Helen.

### Task 8 — Auth-method + parity note

Write `~/iiq-lab-evidence/sandbox/247/auth-methods.txt`:

```text
Basic auth: WORKED | FAILED
OAuth client credentials: WORKED | NOT AVAILABLE (reason)
SCIM: ENABLED | DISABLED (reason)
REST path used for identity get: ________
Helen parity: PASS | DRIFT (fields: ________)
Priya parity: PASS | DRIFT (fields: ________)
```

- **Why:** the deliverable for an integrator is the note, not only JSON files.  
- **Expect:** file saved beside the JSON/screenshots.

## If it fails

| Symptom | Fix |
| --- | --- |
| 401 on all calls | `spadmin`/`admin`; avoid expired custom password |
| HTML login body | Add `Accept` + `X-Requested-With`; ensure `-u` present |
| `/rest/identities/{name}` 404 | Try query form; check `openapi-ootb-rest.yaml` / Debug docs for your build |
| SCIM 404 everywhere | Task 4b — record disabled/not licensed; continue with REST + auth note |
| SCIM 403 | Capability missing for SCIM — grant appropriate admin/SCIM right to caller or OAuth client |
| OAuth token 401 | Wrong client secret; wrong grant_type; client not enabled |
| API/UI drift on email | Refresh Identity Cube; re-agg authoritative app; re-compare |
| Used toolkit URLs by mistake | Wrong lesson surface — drop `/plugin/rest/mnbToolkit` for this drill |

## You are done when

- [ ] Basic-auth OOTB REST read works for Helen and Priya  
- [ ] Warehouse screenshots match API fields (or drifts explicitly listed)  
- [ ] SCIM Users proven **or** `scim-status.txt` explains why not  
- [ ] OAuth Bearer proven **or** `auth-methods.txt` explains why not  
- [ ] Evidence pack under `~/iiq-lab-evidence/sandbox/247/`  

## Control note

- **Control:** External-tool integration parity (API data matches UI data)  
- **Owner:** IAM Engineering  
- **SLA (lab):** Zero unexplained drift between REST/SCIM and Warehouse for sampled identities  
- **Evidence:** `~/iiq-lab-evidence/sandbox/247/`  
- **Out of scope:** Meridian toolkit feature flags (Lesson 246); SSD promote (Lesson 248)

## Quick check

1. Biggest shape difference REST vs SCIM? → Flat product fields vs `userName` / `emails[]` / schemas  
2. SCIM 404 everywhere — what do you do? → Check enablement; record reason; do not invent success  
3. Auth fallback that should always work in lab? → HTTP Basic as `spadmin`  
4. Why two identities? → Avoid one-off parity luck  
5. Token URL for this lab? → `http://localhost:8080/identityiq/oauth2/token`

## Feedback

Could you prove Warehouse parity for two users with Basic + (token or documented blocker) on a wiped notes folder without this page?

If something failed, note the **task number**, HTTP status, and the exact path you called.

## Navigate

- Previous: [Lesson 246](246-toolkit-apis-live.md)
- Next: [Lesson 248](248-ssd-promote-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md) · OpenAPI: [docs/api/openapi/](../api/openapi/)
