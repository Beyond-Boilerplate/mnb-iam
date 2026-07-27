# Lesson 68 — Web Services Connector

**Level:** Intermediate  
**Track:** Connectors — Web APIs & SaaS  
**Time:** 75–90 min  
**Prereq:** Lesson 67 — SQLLoader Bulk Patterns; Lesson 52 connector selection  

**Lab data:**
- Repo: `lab-data/connectors/webservices/wire-portal-openapi.yaml`
- Repo: `lab-data/connectors/webservices/sample-users.json`
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (Wire Portal API row)
- Runtime: `~/iiq-lab-data/connectors/webservices/`
- Optional live: mock API on `http://localhost:8091` per OpenAPI servers

---

## Learning objectives

You will be able to:

- Map Wire Portal OpenAPI operations to Web Services connector **Get Object / Test / Create / Update / Delete / Get Accounts** style operations
- Create application **MNB-Wire-Portal-WS** with schema aligned to `sample-users.json`
- Configure authentication placeholders (API key / OAuth) without committing secrets
- Complete **lab-without-live-target**: operation map spreadsheet + JSON fixture aggregation path
- Define Account Aggregation and a create-account provisioning sketch for `priya.wire`

---

## Why this matters

**Business.** Meridian’s Wire Portal is a custom bank REST app. CSV extracts lag; native Web Services keep initiator/approver entitlements (`WIRE_INIT`, `WIRE_APPR`) closer to real-time for dual-control SoD.

**Control / audit.** Examiners ask how IAM connects to custom APIs, who owns the OpenAPI contract, and whether Test Connection / aggregation failures page someone. Operation maps and Task Results are the evidence.

---

## Concepts

**Web Services connector.** IdentityIQ connector that calls REST/JSON (or SOAP) endpoints using configurable HTTP operations. You map each IIQ connector operation to a method, URL, headers, body, and response parsing rules.

**Meridian Wire Portal (lab).** OpenAPI at `wire-portal-openapi.yaml` defines:

| HTTP | Path | IIQ operation intent |
| --- | --- | --- |
| GET | `/users` | Iterate / Get Accounts |
| GET | `/users/{id}` | Get Object |
| POST | `/users` | Create |
| PATCH | `/users/{id}` | Update |
| DELETE | `/users/{id}` | Delete |
| GET | `/users/{id}/entitlements` | Entitlement read |

```
IIQ MNB-Wire-Portal-WS
        │
        ▼
 Web Services connector ops map
        │
        ▼
 Wire Portal API (live :8091 or fixture JSON)
        │
        ▼
 Accounts + WIRE_INIT / WIRE_APPR entitlements
```

**Matrix:** Wire Portal API → preferred **Web Services**, alternate SCIM 2.0.

**Lab-without-live-target.** Build the full operation map from OpenAPI; use `sample-users.json` as the response contract; optionally point a DelimitedFile/JSON shadow for aggregation practice when `:8091` is down.

---

## Before you start

- [ ] IIQ at `http://localhost:8080/identityiq`
- [ ] `~/iiq-lab-data/connectors/webservices/` contains OpenAPI + sample-users.json
- [ ] Personas: `priya.wire`, `marcus.approve` present in HR cubes if possible
- [ ] Matrix CSV available; Lesson 14 CSV Wire Portal knowledge helpful but not required

---

## Lab procedure

### Task 1 — Read the OpenAPI contract

1. Open `~/iiq-lab-data/connectors/webservices/wire-portal-openapi.yaml`.
2. Confirm `info.title` = MNB Wire Portal Mock API; server URL `http://localhost:8091`.
3. List paths and methods in your binder matching the Concepts table.
4. Open `sample-users.json`; note fields: `id`, `username`, `email`, `employeeId`, `active`, `entitlements`.

**Expected result:** Operation inventory + JSON field list written.

**If it fails:** Re-copy from repo `lab-data/connectors/webservices/`.

### Task 2 — Matrix confirmation

1. Open `connector-selection-matrix.csv`.
2. Confirm Wire Portal API → Web Services.
3. Write: *MNB Wire Portal custom REST uses Web Services; SCIM only if vendor adds SCIM later.*

**Expected result:** Decision sentence archived.

### Task 3 — Create MNB-Wire-Portal-WS

1. Applications → Add New → **Web Services** (or Web Services connector template).
2. Name: `MNB-Wire-Portal-WS`. Owner: `helen.ross`; business contact `priya.wire` (Wire ops).
3. Base URL placeholder: `http://localhost:8091` (or lab gateway).
4. Auth: configure API key / Basic / OAuth fields as your build allows—use env/vault placeholders; never commit tokens.
5. Save application shell.

**Expected result:** Application object exists with Meridian naming.

**If it fails:** Import Application XML stub; still complete operation map offline.

### Task 4 — Map connector operations (lab-without-live-target OK)

1. For each IIQ operation (Test Connection, Account Aggregation iterate, Get Object, Create, Update, Delete), fill: Method, URL, body template, success codes, identity attribute path.
2. Example iterate: `GET /users` → parse `users[*].username` as native identity; entitlements from `entitlements` array.
3. Example create: `POST /users` body with `username`, `email`, `employeeId` from plan.
4. Save map as `MNB-Wire-Portal-WS-Ops-Map.md` in binder (or lab notes folder—not secrets).

**Expected result:** Complete ops map covering read + write paths.

**If it fails:** Copy OpenAPI paths verbatim; mark “response parse TBD” rather than inventing JSONPath incorrectly.

### Task 5 — Aggregation path

**If mock API up:** configure iterate op; run **Account Aggregation** task `MNB-Wire-Portal-WS-Account-Aggregation`; expect `priya.wire` and `marcus.approve`.

**If API down (lab-without-live-target):** create shadow DelimitedFile `MNB-Wire-Portal-WS-Shadow` from a flattened CSV derived from `sample-users.json` (two rows, entitlements `WIRE_INIT` / `WIRE_APPR`). Aggregate the shadow; document that production will use Web Services.

**Expected result:** Task Result Success with two Meridian wire users (live or shadow).

**If it fails:** Validate JSON flattening; check entitlement multi-value handling.

### Task 6 — Provisioning sketch

1. Draft AttributeRequests for creating account for `nina.joiner` with no wire ents (birthright later).
2. Note dual-control: never auto-grant `WIRE_APPR` with `WIRE_INIT` (Lesson 40 SoD).
3. If live API: optional Test Connection + single Get Object for `wp-90`.

**Expected result:** Provisioning sketch + SoD reminder in binder.

---

## Acceptance criteria

- [ ] OpenAPI paths mapped to IIQ Web Services operations
- [ ] `MNB-Wire-Portal-WS` application shell created
- [ ] Ops map document completed (lab-without-live-target acceptable)
- [ ] Account Aggregation Task Result for live API or Shadow app
- [ ] No secrets committed; SoD note for WIRE_INIT vs WIRE_APPR recorded

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| 401/403 on Test Connection | Bad token / wrong header name | Fix auth header; rotate lab key; do not log secrets |
| Empty aggregation | Wrong JSON root (`users` vs `data`) | Align parse path to sample-users.json |
| Entitlements not managed | Array not marked entitlement | Configure multi-value entitlement attribute; re-agg |
| Shadow left as prod | Training app promotion error | Retire `-Shadow` before any non-lab env |
| PATCH vs PUT confusion | OpenAPI says patch | Use PATCH `/users/{id}` per contract |
| Timeouts | No mock server | Start mock or use lab-without-live-target shadow |

---

## Training binder evidence

- OpenAPI + sample-users annotated screenshots
- Ops map file
- Application config (redacted)
- Aggregation Task Result
- SoD reminder for wire entitlements

---

## Knowledge check

1. What preferred connector does the matrix assign to Wire Portal API?
2. Which lab file defines the REST paths for Meridian Wire Portal?
3. Name two personas in `sample-users.json` and their entitlements.
4. What do you do when `localhost:8091` is unavailable?
5. Why must Web Services auth secrets stay out of git?
6. Which HTTP method updates a user per the lab OpenAPI?

### Answers

1. Web Services (alternate SCIM 2.0).
2. `lab-data/connectors/webservices/wire-portal-openapi.yaml`.
3. `priya.wire` → WIRE_INIT; `marcus.approve` → WIRE_APPR.
4. Complete ops map + Shadow DelimitedFile aggregation from fixture JSON/CSV.
5. Tokens/keys are credentials; use vault/env and redact binder screenshots.
6. PATCH `/users/{id}`.

---

## Stretch lab

Implement response mapping for `/users/{id}/entitlements` as a separate entitlement aggregation step. Document whether Meridian will use single-call user+ents vs two-phase read.

---

## Summary

- Web Services maps OpenAPI operations to IIQ connector ops for custom bank APIs.
- `MNB-Wire-Portal-WS` plus ops map is valid training evidence without a live mock.
- Wire entitlements remain SoD-sensitive—aggregation must preserve initiator vs approver.

---

**Previous:** [Lesson 67 — SQLLoader Bulk Patterns](67-sqlloader-bulk-patterns.md)  
**Next:** [Lesson 69 — SCIM 2.0 Connector](69-scim2-connector.md)
