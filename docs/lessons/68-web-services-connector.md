# Lesson 68 — Web Services Connector

**Level:** Intermediate  
**Track:** Connectors — Web APIs & SaaS  
**Time:** 90–120 min  
**Prereq:** Lesson 67 — SQLLoader Bulk Patterns; Lesson 52 connector selection; Lesson 55 feature matrix  

**Lab data:**
- Repo: `lab-data/connectors/webservices/wire-portal-openapi.yaml`
- Repo: `lab-data/connectors/webservices/sample-users.json`
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (Wire Portal API row)
- Runtime: `~/iiq-lab-data/connectors/webservices/`
- **Live mock (mandatory when Docker runs):** `http://localhost:8091` — service `connector-mock` from `./tools/lab/docker/up.sh`

---

## Learning objectives

You will be able to:

- Read Meridian’s Wire Portal OpenAPI and map every path to Web Services connector operations
- Create **MNB-Wire-Portal-WS** with schema aligned to `sample-users.json`
- Configure authentication placeholders (API key / OAuth) without committing secrets
- Start the Meridian **connector-mock**, Test Connection to `:8091`, and aggregate Priya/Marcus (Shadow only if Docker is impossible)
- Defend the Web Services vs SCIM choice and keep `WIRE_INIT` / `WIRE_APPR` SoD-safe

---

## Why this matters

**Business.** Meridian’s Wire Portal is a custom bank REST application. CSV extracts lag; when `priya.wire` receives `WIRE_INIT` at 10:00 and certifications use yesterday’s file, dual-control SoD is fiction. Native Web Services keep initiator/approver entitlements closer to truth.

**Control / audit.** Examiners ask how IAM connects to custom APIs, who owns the OpenAPI contract, and whether Test Connection / aggregation failures page someone. The operation map plus Task Results are the evidence — not a verbal “we have an API.”

---

## Concepts

### What the Web Services connector is

IdentityIQ’s **Web Services** connector calls REST/JSON (or SOAP) endpoints using configurable HTTP operations. You map each IIQ connector operation to method, URL, headers, body, and response parsing. There is no magic schema discovery unless you configure it — **the OpenAPI is the contract**.

### Wire Portal object model (from lab fixtures)

OpenAPI title: **MNB Wire Portal Mock API**. Server: `http://localhost:8091`.

| HTTP | Path | IIQ operation intent |
| --- | --- | --- |
| GET | `/users` | Account Aggregation iterate |
| GET | `/users/{id}` | Get Object |
| POST | `/users` | Create |
| PATCH | `/users/{id}` | Update |
| DELETE | `/users/{id}` | Delete |
| GET | `/users/{id}/entitlements` | Entitlement read (optional second phase) |

`sample-users.json` shape:

| JSON field | IIQ use |
| --- | --- |
| `id` | Optional native / secondary (`wp-90`) |
| `username` | Preferred native identity (`priya.wire`) |
| `email` | Correlation / mail |
| `employeeId` | Correlate to HR (`MNB00090`) |
| `active` | ENABLE semantics |
| `entitlements[]` | Managed entitlement (`WIRE_INIT`, `WIRE_APPR`) |

### Why not SCIM here?

Matrix: **Wire Portal API → Web Services**, alternate SCIM 2.0. Wire Portal is a **custom bank API** without a SCIM ListResponse. Use SCIM when the vendor speaks SCIM (Lesson 69). Forcing SCIM mappings onto a non-SCIM API produces fragile parsers and false confidence.

```
IIQ MNB-Wire-Portal-WS
        │
        ▼
 Web Services ops map (from OpenAPI)
        │
        ▼
 Wire Portal API (:8091) or fixture-backed Shadow
        │
        ▼
 Accounts + WIRE_INIT / WIRE_APPR entitlements
```

---

## How it works

At aggregation time IIQ invokes your configured **Get Accounts / iterate** operation (`GET /users`), parses the JSON array under `users`, and creates Links. Provisioning plans invoke Create/Update/Delete operations with body templates. Auth headers are attached per application connection settings.

```
IdentityIQ (MNB-Wire-Portal-WS)
        │  Authorization: Bearer <vaulted token>
        ▼
GET http://localhost:8091/users
        │
        ▼
{ "users": [ { username, entitlements[] }, … ] }
        │
        ▼
Links on priya.wire / marcus.approve cubes
```

| IIQ need | OpenAPI | Parse notes |
| --- | --- | --- |
| Iterate | GET `/users` | Root `users` array — not SCIM `Resources` |
| Get Object | GET `/users/{id}` | Path id = `wp-90` style |
| Create | POST `/users` | 201 Created |
| Update | PATCH `/users/{id}` | Not PUT — contract says PATCH |
| Delete | DELETE `/users/{id}` | 204 |
| Entitlements | GET `…/entitlements` or embed | Lab sample embeds array on user |

---

## Real-world setup (outside IIQ)

### Step 1 — Own the OpenAPI

1. Wire Portal engineering publishes OpenAPI under change control (lab file is the stand-in).
2. IAM reviews breaking changes (path renames, auth, entitlement shape) before IIQ upgrades.
3. Contract owner: Wire ops business contact `priya.wire`; IAM `helen.ross`.

### Step 2 — Authentication

1. Prefer OAuth2 client credentials or short-lived API keys in a vault — never long-lived tokens in Application XML git exports.
2. Separate **read** client (aggregation) from **write** client (provisioning) when the API allows.
3. Rotate on bank schedule; page on 401 bursts.

### Step 3 — Network + start the lab mock

1. IIQ servers → Wire Portal VIP only; TLS in non-lab.
2. Lab mock listens on **8091** — do not assume 8080 (that is IIQ).

```bash
./tools/lab/docker/up.sh   # starts connector-mock
# or: python3 tools/connector-mock/serve.py
curl -s http://localhost:8091/health
curl -s http://localhost:8091/users | python3 -m json.tool | head
```

From the IIQ container use base URL `http://connector-mock:8091` (not `localhost`).

### Step 4 — SoD before go-live

1. Confirm IIQ SoD still blocks `WIRE_INIT` + `WIRE_APPR` on one identity (Lessons 40–41).
2. API-level enforcement is defense in depth — not a substitute for IIQ policy.

---

## Before you start

- [ ] IIQ at `http://localhost:8080/identityiq` as `spadmin`
- [ ] `~/iiq-lab-data/connectors/webservices/` contains OpenAPI + `sample-users.json`
- [ ] HR cubes for `priya.wire` / `marcus.approve` if correlation will be tested
- [ ] Lesson 55: Wire Portal features still Unknown until this OpenAPI read
- [ ] `curl http://localhost:8091/health` returns ok (or dated deferral if Docker impossible)

---

## Lab procedure

### Task 1 — Read the OpenAPI contract end-to-end

The connector is only as correct as your reading of this file.

1. Open `~/iiq-lab-data/connectors/webservices/wire-portal-openapi.yaml`.
2. Confirm `info.title` = MNB Wire Portal Mock API; `servers.url` = `http://localhost:8091`.
3. List every path/method in the binder matching the Concepts table.
4. Open `sample-users.json`; inventory both users and entitlements:

| id | username | employeeId | entitlements |
| --- | --- | --- | --- |
| wp-90 | `priya.wire` | MNB00090 | WIRE_INIT |
| wp-91 | `marcus.approve` | MNB00091 | WIRE_APPR |

**Expected result:** Operation inventory + JSON field list written.

**If it fails:** Re-copy from repo `lab-data/connectors/webservices/`.

### Task 2 — Matrix and feature-matrix updates

1. Confirm matrix: Wire Portal API → **Web Services**.
2. Binder sentence: *Custom REST uses Web Services; SCIM only if vendor adds SCIM later.*
3. Update Lesson 55 row for `MNB-WirePortal-WS`: PROVISIONING=Y (POST/PATCH/DELETE exist); ENABLE=Y if `active` is writable via PATCH; PASSWORD/UNLOCK=N unless API documents them (lab OpenAPI does not).

**Expected result:** Decision sentence + feature cells no longer Unknown for documented ops.

### Task 3 — Create MNB-Wire-Portal-WS

1. Applications → Add New → **Web Services** (or equivalent template).
2. Name: `MNB-Wire-Portal-WS`. Owner: `helen.ross`; business contact `priya.wire`.
3. Base URL: `http://localhost:8091` (host IIQ) or `http://connector-mock:8091` (IIQ in Docker).
4. Auth: API key / Basic / OAuth fields per build — vault placeholders only; never commit tokens. Lab mock accepts unauthenticated GETs.
5. Create-identities **OFF**. Save.

**Expected result:** Application object exists with Meridian naming.

**If it fails:** Import XML stub; still complete the ops map offline.

### Task 4 — Build the operations map (required artifact)

This map is examiner evidence that IAM understood the API.

1. Create `~/iiq-lab-data/connectors/webservices/MNB-Wire-Portal-WS-Ops-Map.md`.
2. For Test Connection, Account Aggregation iterate, Get Object, Create, Update, Delete, fill: Method, URL, headers, body template, success codes, identity JSON path.
3. Iterate example: `GET /users` → native identity `users[*].username`; entitlements `users[*].entitlements`.
4. Create example: `POST /users` with `username`, `email`, `employeeId` from plan; expect 201 (OpenAPI; mock may be read-heavy).
5. Update example: `PATCH /users/{id}` per OpenAPI — do not invent PUT.

**Expected result:** Complete ops map covering read + write paths.

**If it fails:** Copy OpenAPI paths verbatim; mark “response parse TBD” rather than guessing JSONPath.

### Task 5 — Aggregation against connector-mock (primary)

**Primary (live mock):** configure iterate op to `GET /users` with `rootPath` `$.users`; add **Response Mapping** on Account Aggregation (`id`→`id`, `username`→`username`, `email`→`email`, `employeeId`→`employeeId`, `active`→`active`, `entitlements`→`entitlements`); set Enable Has More = false; **Test Connection**; run Account Aggregation `MNB-Wire-Portal-WS-Account-Aggregation`; expect `priya.wire` and `marcus.approve`.

**Fallback only if Docker/mock impossible (lab-without-live-target):** flatten `sample-users.json` to CSV and create Shadow DelimitedFile `MNB-Wire-Portal-WS-Shadow`; binder must say live path was *unavailable*, not skipped.

```csv
id,username,email,employeeId,active,entitlements
wp-90,priya.wire,priya.wire@meridiannb.com,MNB00090,true,WIRE_INIT
wp-91,marcus.approve,marcus.approve@meridiannb.com,MNB00091,true,WIRE_APPR
```

**Expected result:** Task Result Success with two wire users from `:8091` (or dated Shadow deferral).
**If it fails:** Wrong JSON root (`users` vs `data`); fix parse path to match fixture.

### Task 6 — Provisioning sketch + SoD

1. Draft AttributeRequests for `nina.joiner` create with **no** wire entitlements (birthright later).
2. Explicit note: never auto-grant `WIRE_APPR` with `WIRE_INIT`.
3. Optional live: Get Object for `wp-90`.

**Expected result:** Provisioning sketch + SoD reminder in binder.

### Task 7 — Examiner drill and residual risk

*“Show how IdentityIQ lists Wire Portal users and who owns the API contract.”*

Answer: ops map + OpenAPI revision + aggregation Task Result; owners `helen.ross` / `priya.wire`.

Record `RR-WS-ENT-01`: *If production stops embedding entitlements on GET /users and only exposes `/users/{id}/entitlements`, iterate alone under-reports access — need two-phase read.*

**Expected result:** Examiner answer + RR in binder.

### Task 8 — CHANGELOG

CHANGELOG: “Lesson 68 Web Services connector MNB-Wire-Portal-WS mapped from wire-portal-openapi.yaml.”

**Expected result:** CHANGELOG entry.

---

## Acceptance criteria

- [ ] OpenAPI paths mapped to IIQ Web Services operations in Ops-Map.md
- [ ] `MNB-Wire-Portal-WS` shell created; secrets not in git
- [ ] Feature matrix Wire Portal row updated from OpenAPI evidence
- [ ] Account Aggregation Task Result (live `:8091` or Shadow)
- [ ] SoD note + `RR-WS-ENT-01` + examiner answer recorded

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| 401/403 on Test Connection | Bad token / header name | Fix auth; rotate lab key; do not log secrets |
| Empty aggregation / Preview empty but Test Connection OK | Wrong JSON root **or** missing Response Mapping | Align `rootPath` to `$.users`; map every schema attr on Account Aggregation; Enable Has More = false |
| Entitlements not managed | Array not marked entitlement | Multi-value entitlement attr; re-agg |
| Shadow left as prod | Naming error | Retire `-Shadow` before non-lab |
| PATCH vs PUT confusion | Guessing REST style | Use PATCH per OpenAPI |
| Timeouts | No mock server | Start mock or use Shadow path |
| Port conflict | Hitting IIQ :8080 | Wire Portal mock is **8091** |

---

## Training binder evidence

- Annotated OpenAPI + sample-users inventory
- `MNB-Wire-Portal-WS-Ops-Map.md`
- Application config (redacted)
- Aggregation Task Result
- SoD + RR + feature matrix update

**Examiner question:** *“Show how IdentityIQ lists Wire Portal users and who owns the API contract.”*

---

## Knowledge check

1. What preferred connector does the matrix assign to Wire Portal API?
2. Which lab file defines the REST paths?
3. Name two personas in `sample-users.json` and their entitlements.
4. What do you do when `localhost:8091` is unavailable?
5. Why must Web Services auth secrets stay out of git?
6. Which HTTP method updates a user per the lab OpenAPI?

### Answers

1. Web Services (alternate SCIM 2.0).
2. `lab-data/connectors/webservices/wire-portal-openapi.yaml`.
3. `priya.wire` → WIRE_INIT; `marcus.approve` → WIRE_APPR.
4. Prefer `./tools/lab/docker/up.sh` / `connector-mock` on `:8091`; only if Docker is impossible, complete ops map + Shadow DelimitedFile and date the deferral.
5. Tokens are credentials; use vault/env; redact screenshots.
6. PATCH `/users/{id}`.

---

## Further reading

- [OpenAPI Specification](https://swagger.io/specification/) — how to read `paths`, `servers`, and methods the connector will call.
- [RFC 7386 JSON Merge Patch](https://datatracker.ietf.org/doc/html/rfc7386) — background for PATCH-style updates (conceptual; follow vendor body schema).
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/) — authn/z and excessive data exposure risks for bank APIs.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “Web Services connector” for operation mapping fields.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — Web Services JSONPath / paging troubleshooting threads.

---

## Stretch lab

Implement response mapping for `GET /users/{id}/entitlements` as a separate entitlement aggregation step. Document Meridian’s choice: single-call user+ents (lab sample) vs two-phase read. Add pagination assumptions if Wire Portal later returns cursors — and update `RR-WS-ENT-01`.

---

## Summary

- Web Services maps OpenAPI operations to IIQ connector ops for custom bank APIs — Wire Portal is the Meridian exemplar.
- Primary path aggregates against `connector-mock` `:8091`; Shadow is fallback only when Docker is impossible.
- Wire entitlements remain SoD-sensitive; aggregation must preserve initiator vs approver.

---

**Previous:** [Lesson 67 — SQLLoader Bulk Patterns](67-sqlloader-bulk-patterns.md)  
**Next:** [Lesson 69 — SCIM 2.0 Connector](69-scim2-connector.md)
