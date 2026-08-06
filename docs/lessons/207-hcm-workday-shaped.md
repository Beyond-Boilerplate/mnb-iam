# Lesson 207 — Authoritative HCM (Workday-Shaped)

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~70 minutes  
**Prereq:** Lesson 202 (do this **before** 204–206 — directories and pass-through need cubes)  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 77

> **Why:** Lifecycle should be driven by HR API events, not by someone hand-editing a CSV forever. In this estate, **you** create the first identity cubes from Workday — seed never pre-loads Helen into the Warehouse.

## What this is

`MNB-Workday` is a **Web Services** connector (`sailpoint.connector.webservices.WebServicesConnector`, `authoritative="true"`) pointed at:

```text
http://connector-mock:8091/hcm/v1
```

It is Workday-**shaped** REST served by `tools/connector-mock/serve.py` — not the native Workday connector (that needs a real Workday tenant).

**MNB Workday** is the lab helper UI for that same feed:

```text
http://localhost:8091/hcm/ui
```

Use it to browse workers, hire (add), edit, and terminate. Every action hits the same in-memory API IIQ aggregates.

| Verb / path | Job |
| --- | --- |
| `GET /workers` | Account aggregation + Test Connection (`rootPath` `$.workers` + **Response Mapping**) |
| `POST /hcm/v1/workers` | Create / upsert a worker (joiner) — UI **Add worker** |
| `PATCH /hcm/v1/workers/{id}` | Update fields or flip `active` / `status` — UI **Edit** / **Terminate** |

```text
MNB Workday UI / HCM API
        │  POST / PATCH (hire, terminate)
        ▼
connector-mock :8091/hcm/v1/workers
        │  GET (Account Aggregation)
        ▼
MNB-Workday (authoritative)
        │  Identity Refresh (create identities)
        ▼
Identity Warehouse cubes (helen.ross, …)
```

`MNB-HR` (Delimited File) is **not** authoritative here — leave it alone. Cubes come from Workday only.

## Know these

| Schema field | Role |
| --- | --- |
| `id` | Identity native key (`identityAttribute`) |
| `userName` | Login / display (`displayAttribute`) |
| `managerId` | Manager reference (`managerAttribute`) |

- Aggregation alone creates **account links**. **Identity Refresh** with “create identities” (plus the app’s `authoritative="true"`) is what mints cubes.
- Web Services needs **Response Mapping** on Account Aggregation (schema attr → JSON field). Without it, Test Connection can succeed while Preview/Aggregation return **zero** accounts.
- **Terminate** in the UI sets `active: false` / `status: Terminated` — it does **not** remove the row from the feed.
- Optional CLI: `./tools/lab/enterprise/hcm-scenario.sh joiner …` POSTs the same API.
- **Wrong way:** Aggregating `MNB-HR` to get cubes “faster” — that reintroduces the CSV authoritative path this estate retired.

## Intent

- Build (or select) an **Account Aggregation** task for `MNB-Workday` and an **Identity Refresh** that creates identities.
- Populate Warehouse with the first Meridian workforce cubes from HCM.
- Hire a joiner in the UI and watch a new cube appear after re-agg + refresh.
- Explain, in one sentence, why this is “Workday-shaped” rather than “the Workday connector.”

## Before you start

- [ ] Lessons 201–202 done; Warehouse has **no** workforce cubes (only `spadmin`)
- [ ] `connector-mock` healthy: `curl -sf http://localhost:8091/health`
- [ ] **MNB Workday** UI loads: [http://localhost:8091/hcm/ui](http://localhost:8091/hcm/ui)
- [ ] `MNB-Workday` Application exists in IIQ
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/207
```

> If the UI 404s:  
> `docker compose -f docker-compose.iiq.yml up -d --build --force-recreate connector-mock`

## Do this

### Task 1 — Open the live HCM UI

Know the live source before trusting IIQ’s aggregated view. Cubes come from this feed — not from CSV.

1. Open **MNB Workday**: [http://localhost:8091/hcm/ui](http://localhost:8091/hcm/ui)
2. Search `helen.ross`
3. Confirm `id` `MNB00001`, `managerId` empty / `—`, status **Active**

- **Why:** if Helen isn’t in HCM, aggregation cannot invent her.
- **Expect:** Helen visible; toolbar shows a populated worker count.

### Task 2 — Peek at the raw API the connector speaks

The UI is convenience; the Web Services connector still speaks `GET /hcm/v1/workers` with `rootPath` `$.workers`.

```bash
curl -s http://localhost:8091/hcm/v1/workers | python3 -m json.tool | head -40
```

- **Why:** you’ll recognize this envelope when you configure Response Mapping.
- **Expect:** JSON envelope `{"total": N, "workers": […]}`.

### Task 3 — Confirm MNB-Workday schema and Response Mapping

Test Connection only proves HTTP `2xx`. Response Mapping is what turns each `$.workers[*]` object into an account.

1. **Applications → Application Definition → MNB-Workday**
2. Confirm **authoritative** / create-identities intent
3. Confirm schema:
   - `id` → identityAttribute
   - `userName` → displayAttribute
   - `managerId` → managerAttribute
4. Open the **Account Aggregation** endpoint:
   - `rootPath` = `$.workers`
   - **Response Mapping** present (or add) for at least `id`, `userName`, `email`, `managerId`, `active`
5. Set **Enable Has More** to **false** if it is on (this mock is not paged)
6. Click **Test Connection**

- **Why:** skip Response Mapping and Preview/Aggregation stay empty even when Test Connection is green.
- **Expect:** connection succeeds; Response Mapping present; schema fields match.

### Task 4 — Create and run Account Aggregation

Seed imported the *application*, not a finished run of aggregation — operators own the first pull.

1. **Setup → Tasks → New Task → Account Aggregation** (or equivalent)
2. Name: `Aggregate MNB-Workday`
3. Application: `MNB-Workday`
4. **Save**, then **Execute** / Run

- **Why:** without this pull, Warehouse stays empty of workforce forever.
- **Expect:** Task Result succeeds (accounts created/updated counts > 0).

> **Tip:** If a generic `MNB-Acct-Aggregation` task already exists, open it, point it at `MNB-Workday`, and run — same outcome.

### Task 5 — Identity Refresh with create identities

Aggregation alone only creates account links — refresh promotes them into **cubes**.

1. **Setup → Tasks** → Refresh Identity Cube (or New → Identity Refresh)
2. Enable options that **create identities** / promote attributes
3. Scope: all identities / include new accounts from authoritative apps as needed
4. **Execute**

- **Why:** this is the first time Meridian people become governed cubes in this estate — sourced from Workday, not CSV.
- **Expect:** Task Result succeeds.

### Task 6 — Prove cubes in Identity Warehouse

1. **Identities → Identity Warehouse**
2. Search `helen.ross`, `priya.wire`, `marcus.approve`
3. Open Helen — confirm a `MNB-Workday` account link
4. Open Priya — manager should resolve toward `sanjay.kapoor` (may need a second refresh)

- **Why:** Warehouse search is the acceptance gate for everything after this lesson.
- **Expect:** all three cubes exist.

### Task 7 — Hire a joiner in the HCM UI

UI `POST`s to `/hcm/v1/workers` — a real lifecycle event, not a fixture edit.

1. Click **Add worker**
2. Fill:

   | Field | Value |
   | --- | --- |
   | `userName` | `e2e.sandbox` |
   | `firstName` | `E2E` |
   | `lastName` | `Sandbox` |
   | `email` | `e2e.sandbox@meridiannb.com` |
   | `department` | `Identity & Access` |

3. **Save** — note the generated `id`

- **Why:** proves joiners can enter through live HCM, not only through the identity master JSON.
- **Expect:** new row for `e2e.sandbox` with status **Active**.

### Task 8 — Re-aggregate + refresh; find the new cube

1. Re-run **Aggregate MNB-Workday**
2. Re-run **Identity Refresh** (create identities)
3. Search Warehouse for `e2e.sandbox`

- **Why:** UI → API → aggregate → refresh is the full joiner path.
- **Expect:** cube exists for `e2e.sandbox`.

### Task 9 — Optional stretch: soft terminate

Leavers are status events; hard-deleting from HR is not the Meridian control pattern.

1. In the UI, **Edit** a throwaway hire or **Terminate** it
2. Confirm status flips to **Terminated**, row remains

- **Why:** soft terminate (`active: false`) keeps the audit trail.
- **Expect:** Terminate confirms; badge shows Terminated.

> **Tip:** This lab proves the *pattern* (authoritative HR-as-a-service, lifecycle status events, manager attribute wiring) — not Workday’s native SOAP/REST APIs or auth model.

### Task 10 — Close with asserts

```bash
./tools/lab/enterprise/verify-lesson.sh 207
```

- **Why:** hard checks cover app + HCM UI + Helen in the feed; soft identity checks may also PASS after Tasks 4–6.
- **Expect:** hard asserts PASS.

## If it fails

| Symptom | Fix |
| --- | --- |
| `/hcm/ui` 404 or blank | Rebuild `connector-mock` (see Before you start) |
| Test Connection fails | `curl -sf http://localhost:8091/health` |
| Test Connection OK but Preview / Aggregation show zero accounts | Missing **Response Mapping** on Account Aggregation; also confirm `rootPath` `$.workers` and Enable Has More = false |
| Aggregation zero accounts | Confirm UI lists workers; then check Response Mapping / `rootPath` as above |
| Cubes never appear | You aggregated but skipped Identity Refresh, or refresh ran **without** create identities |
| UI hire succeeds but IIQ never sees them | Re-aggregate after the UI POST — IIQ does not push-listen to the mock |
| Terminate left the worker in the list | Expected — soft terminate (`active: false`) |
| Cubes appeared from `MNB-HR` instead | You aggregated the CSV app — disable/stop using it as authoritative; wipe and redo from Workday |
| Prefer CLI over UI | `./tools/lab/enterprise/hcm-scenario.sh joiner <username> <first> <last> <email> [department]` |

## You are done when

- [ ] You created/ran Account Aggregation for `MNB-Workday` and Identity Refresh with create identities
- [ ] Warehouse shows Helen / Priya / Marcus as cubes sourced from Workday
- [ ] You hired `e2e.sandbox` in the UI and saw a new cube after re-agg + refresh
- [ ] You can name `managerId` → `managerAttribute` as the manager hierarchy wiring
- [ ] `./tools/lab/enterprise/verify-lesson.sh 207` hard asserts PASS

## Control note

- **Control:** Authoritative HR source integrity — joiner / first cubes from governed HCM
- **Owner:** HRIS / IAM Ops
- **SLA (lab):** first cubes and joiner visible in the same session; production target is typically same-day
- **Evidence:** `~/iiq-lab-evidence/sandbox/207/` — Task Result ids, Warehouse screenshot, UI hire screenshot

## Quick check

1. What flag on `MNB-Workday` makes it create new cubes, not just links? → `authoritative="true"` (plus refresh with create identities)
2. What does the UI **Terminate** button call? → `PATCH /hcm/v1/workers/{id}` with `active: false`
3. Why is Warehouse empty after Lesson 202? → Seed imports definitions only; this lesson is the first aggregation
4. Test Connection works but aggregation is empty — what’s missing? → **Response Mapping** on Account Aggregation (and `rootPath` `$.workers`)

## Feedback

Could you recreate Aggregate + Refresh for Workday and hire one joiner without looking? If the cube never appeared, note whether aggregation Task Result and Identity Refresh both succeeded — and whether “create identities” was checked.

## Navigate

- Previous: [Lesson 202](202-identity-master-and-seed.md)
- Next (recommended path): [Lesson 203](203-mailpit-iiq-email.md) or [Lesson 204](204-openldap-live-ops.md) (directories need cubes from this lesson)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
