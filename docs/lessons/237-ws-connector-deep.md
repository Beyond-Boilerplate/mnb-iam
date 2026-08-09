# Lesson 237 — Web Services Connector Depth

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~70 minutes  
**Prereq:** Lesson 209  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 68

> **Why:** WS outages trace to bad `rootPath`, missing Response Mapping, unfollowed pagination, or silent auth breakage — and Create/Update/Disable only work when each operation is wired to a real HTTP verb. Practice diagnosing mapping vs auth, then prove a full provision cycle against the live Wire mock before a real portal pages you.

## What this is

Lesson 209 built **`MNB-WirePortal`** as a read path (`WebServicesConnector` → `GET /users`). This lesson deepens that same Application:

| Surface | Path | This lesson |
| --- | --- | --- |
| Plain REST | `GET/POST /users`, `PATCH /users/{id}` | Aggregation + Create / Update / Disable |
| SCIM (separate store) | `/scim/v2/Users` | Optional contrast only — not your provision target |

You will **not** assume the 209 app survived wipe. You verify-or-rebuild operations, break `rootPath` on purpose, then Create → Update entitlements → Disable for disposable **`lab.wsdeep1`** and prove each step with `curl`.

**Credential custody** is out of scope. Here IIQ talks HTTP; the mock is ground truth.

> **Watch out:** Core Path may still have a Delimited File `MNB-WirePortal` CSV app. This lesson’s target is the **Web Services** Application against `http://connector-mock:8091` — same name as Lesson 209. Confirm **Type = Web Services** before editing.

## Know these

```text
curl GET /users → confirm $.users shape
  → Verify MNB-WirePortal (WS) or rebuild from 209 pattern
  → Operation table: Test Connection | Account Aggregation | Get Object
                    | Create Account | Update Account | Disable Account
  → Break rootPath → read Task Result error → fix + re-agg
  → Break auth → Test Connection fails differently from mapping
  → Hire lab.wsdeep1 → Create Account → curl shows user
  → Update entitlements → curl shows WIRE_INIT
  → Disable → curl active=false → re-agg cube matches
```

| WS operation | HTTP | Mock path | Purpose |
| --- | --- | --- | --- |
| **Test Connection** | `GET` | `/users` | Reachability / auth smoke |
| **Account Aggregation** | `GET` | `/users` | `rootPath` `$.users` + Response Mapping |
| **Get Object** | `GET` | `/users/$plan.nativeIdentity$` | Single-account refresh |
| **Create Account** | `POST` | `/users` | New wire user JSON body |
| **Update Account** | `PATCH` | `/users/$plan.nativeIdentity$` | Entitlements / email changes |
| **Disable Account** | `PATCH` | `/users/$plan.nativeIdentity$` | `{ "active": false }` |

| Term | Plain English | Meridian example |
| --- | --- | --- |
| **`genericWebServiceBaseUrl`** | Host IIQ calls (Docker name) | `http://connector-mock:8091` |
| **`rootPath`** | JSON pointer to the account array | `$.users` |
| **Response Mapping** | Schema attr → JSON field | `username` → `username` |
| **`$plan.nativeIdentity$`** | Account key in provision URL/body | Wire `id` e.g. `wp-lab-wsdeep1` |
| **featuresString** | What IIQ may attempt | Must include `PROVISIONING` (+ `ENABLE` for Disable) |

- **Wrong way:** Trusting Test Connection alone — it can pass while Aggregation returns zero accounts.  
- **Wrong way:** Using Helen / Priya / Marcus as the write subject — use `lab.wsdeep1`.  
- **Wrong way:** Pointing Create/Update at `/scim/v2/...` while aggregating `/users` — two separate stores.  
- **Wrong way:** Leaving `Enable Has More` on for this non-paged mock — empty or truncated imports.  
- **Wrong way:** Assuming Create/Disable endpoints from Lesson 209 — 209 was read-only; you add them here.

## Intent

- Verify-or-rebuild `MNB-WirePortal` WS with a full operation table.  
- Diagnose a deliberate `rootPath` failure and a distinct auth failure.  
- Create, update, and disable `lab.wsdeep1` through IIQ; prove each with `curl`.  
- Leave evidence under `~/iiq-lab-evidence/sandbox/237/`.

## Before you start

Complete every checkbox. Do not skip into Task 1 until these are true.

- [ ] IIQ up: [http://localhost:8080/identityiq](http://localhost:8080/identityiq) — login as `spadmin` / `admin`
- [ ] `connector-mock` healthy:

```bash
curl -sf http://localhost:8091/health
```

- [ ] Wire REST feed readable:

```bash
curl -s http://localhost:8091/users | python3 -m json.tool | head -40
```

  - **Expect:** top-level `"users": [ ... ]` with `priya.wire` / `marcus.approve` (or your prior lab rows).

- [ ] You know Lesson 209’s pattern (base URL, `$.users`, Response Mapping). You will **re-check** the live Application — do not assume it survived.
- [ ] Evidence dir:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/237
```

> **Tip:** If POST/PATCH to `/users` returns `404`, restart the enterprise stack so `connector-mock` picks up the mutable Wire handlers (`./tools/lab/docker/up.sh --enterprise` or recreate the mock container).

## Do this

### Task 1 — Map the live JSON before touching IIQ

```bash
curl -s http://localhost:8091/users | python3 -m json.tool
```

Save as `~/iiq-lab-evidence/sandbox/237/users-baseline.json`.

| Field | Role |
| --- | --- |
| `id` | Native identity (`identityAttribute`) |
| `username` | Display |
| `email` | Contact |
| `employeeId` | Correlation → identity `userId` |
| `active` | Lifecycle boolean |
| `entitlements` | Managed multi-valued entitlement |

- **Why:** every Response Mapping and Create body field comes from this shape — not from UI guesses.
- **Expect:** you can state the root array key is `users` (`$.users`).

### Task 2 — Verify-or-rebuild `MNB-WirePortal` (Web Services)

1. **Applications → Application Definition** → search `MNB-WirePortal`
2. Open it and confirm **Type = Web Services** (not Delimited File)
3. Confirm Configuration:

| Setting | Required value |
| --- | --- |
| **Base URL** / `genericWebServiceBaseUrl` | `http://connector-mock:8091` |
| **Authentication** | `No Auth` (lab) |
| **featuresString** | includes `PROVISIONING` and `ENABLE` (add if missing) |

4. If the app is missing or is CSV-only: create **New → Web Services**, name **`MNB-WirePortal`**, base URL as above — use Lesson 209 Tasks 2–5 for schema + Aggregation Response Mapping, then continue here for provision ops.

Schema (AttributeDefinitions — not dropdown-only):

| Attribute | Flags |
| --- | --- |
| `id` | identity |
| `username` | display |
| `email` | — |
| `employeeId` | — |
| `active` | boolean |
| `entitlements` | `entitlement=true` `managed=true` `multi=true` |

- **Why:** provision ops need PROVISIONING/ENABLE and a real schema; CSV Wire cannot Create/Disable against the mock.
- **Expect:** WS app open with base URL on `connector-mock`, not `localhost`.

### Task 3 — Build the operation table

On **Configuration → HTTP Operations** (wording varies), ensure these endpoints exist. Sequence numbers can differ; names and verbs must match.

#### 3a — Test Connection

| Field | Value |
| --- | --- |
| Operation | **Test Connection** |
| Method | `GET` |
| Context URL | `/users` |
| Success codes | `2**` |

#### 3b — Account Aggregation

| Field | Value |
| --- | --- |
| Operation | **Account Aggregation** |
| Method | `GET` |
| Context URL | `/users` |
| Root path | `$.users` |
| Enable Has More | **false** |
| Response Mapping | `id→id`, `username→username`, `email→email`, `employeeId→employeeId`, `active→active`, `entitlements→entitlements` |

#### 3c — Get Object

| Field | Value |
| --- | --- |
| Operation | **Get Object** |
| Method | `GET` |
| Context URL | `/users/$plan.nativeIdentity$` |
| Response Mapping | same attribute map as Aggregation (single object — no rootPath array) |

#### 3d — Create Account

| Field | Value |
| --- | --- |
| Operation | **Create Account** |
| Method | `POST` |
| Context URL | `/users` |
| Body format | raw JSON |

Body (paste exactly; adjust only if your plan attribute names differ):

```json
{
  "id": "$plan.nativeIdentity$",
  "username": "$plan.username$",
  "email": "$plan.email$",
  "employeeId": "$plan.employeeId$",
  "active": true,
  "entitlements": []
}
```

Response Mapping should capture returned `id` (native identity).

#### 3e — Update Account

| Field | Value |
| --- | --- |
| Operation | **Update Account** |
| Method | `PATCH` |
| Context URL | `/users/$plan.nativeIdentity$` |
| Body | raw JSON with changed attrs, e.g. `"entitlements": ["WIRE_INIT"]` via `$plan.entitlements$` if your UI supports list placeholders — otherwise set a fixed lab body `["WIRE_INIT"]` for this drill |

#### 3f — Disable Account

| Field | Value |
| --- | --- |
| Operation | **Disable Account** |
| Method | `PATCH` |
| Context URL | `/users/$plan.nativeIdentity$` |
| Body | `{"active": false}` |

5. **Save** the Application  
6. Confirm **Enable Has More** is still false and Aggregation `rootPath` is still `$.users` after the dialog closes

- **Why:** without Create/Update/Disable endpoints, IIQ plans fail at the connector even when the mock supports the verbs.
- **Expect:** six operations saved; featuresString includes PROVISIONING + ENABLE.

> **Watch out:** After editing endpoints, re-open Aggregation and confirm `rootPath` did not clear — a common WS UI bug.

### Task 4 — Baseline Test Connection + Aggregation

1. **Test Connection** → green  
2. Run **Account Aggregation** on `MNB-WirePortal` → Task Result **Complete**  
3. Note account count from Task Result (or Preview)

```bash
curl -s http://localhost:8091/users | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('users') or []))"
```

Save count under evidence as `baseline-count.txt`.

- **Why:** you need a known-good count before you break mapping on purpose.
- **Expect:** Test Connection OK; aggregation count > 0 and in the same ballpark as curl.

### Task 5 — Break `rootPath`, read the error, fix it

1. Edit Account Aggregation → set root path to **`$.resources`** (wrong key)  
2. **Save** → Aggregate again  
3. Open Task Result — copy the warning/error text exactly into `~/iiq-lab-evidence/sandbox/237/rootpath-error.txt`  
4. Restore root path to **`$.users`** → Aggregate  
5. Confirm count matches Task 4

- **Why:** production incidents look like “zero accounts, green-ish task” until you read the parse path — practice that now.
- **Expect:** broken run shows zero/parse warning referencing the bad path; fixed run restores baseline count.

### Task 6 — Break auth, contrast with mapping failure

1. Change Authentication to **Basic** with fake user/password (or a method your build rejects)  
2. **Test Connection**  
3. Save the exact failure text as `auth-error.txt`  
4. Revert to **No Auth** → Test Connection green again

- **Why:** mapping failures and auth failures must look different so you stop guessing under pressure.
- **Expect:** auth error text is visibly different from Task 5’s mapping/path text.

> **Tip:** If Test Connection still passes with wrong Basic (reachability-only builds), run Aggregation anyway and note that gap under evidence — then still revert auth.

### Task 7 — Create disposable identity `lab.wsdeep1`

Never use Helen, Priya, or Marcus as the provision subject.

```bash
./tools/lab/enterprise/hcm-scenario.sh joiner lab.wsdeep1 Lab Wsdeep \
  lab.wsdeep1@meridiannb.com 'Bank Operations'
```

```bash
curl -s http://localhost:8091/hcm/v1/workers/lab.wsdeep1 \
  | python3 -m json.tool | grep -E 'userName|email|active|status|department'
```

1. Aggregate **`MNB-Workday`** → Complete  
2. **Refresh Identity Cube** for `lab.wsdeep1` (promote attributes) → Complete  
3. Open cube — confirm identity exists  
4. Note / set `userId` / employee id if your correlation needs it (Wire uses `employeeId` — put the same value you will send on Create, e.g. `lab.wsdeep1` or an `MNB#####` you assign)

- **Why:** throwaway subject keeps shared personas intact for certs/SoD.
- **Expect:** cube `lab.wsdeep1` exists before Create Account.

### Task 8 — Create Account via IIQ → prove with curl

1. Open `lab.wsdeep1` → **Application Accounts** → **Create Account** → **`MNB-WirePortal`**
2. Fill Create policy / form fields (names must match `$plan.*$` placeholders):

| Field | Value |
| --- | --- |
| Native identity / `id` | `wp-lab-wsdeep1` |
| `username` | `lab.wsdeep1` |
| `email` | `lab.wsdeep1@meridiannb.com` |
| `employeeId` | match cube `userId` (e.g. `lab.wsdeep1`) |

3. Submit → wait for Provisioning Transaction **Committed** (or retry if Failed — Lesson 230)  
4. Prove on the mock:

```bash
curl -s http://localhost:8091/users/wp-lab-wsdeep1 | python3 -m json.tool
```

- **Expect:** `username` `lab.wsdeep1`, `active` true.

5. Aggregate `MNB-WirePortal` → confirm link on the cube  

Save curl output as `after-create.json`.

- **Why:** UI “Created” without mock proof is theater.
- **Expect:** curl + IIQ link both show the new account.

If Create Account is missing from the UI: confirm `PROVISIONING` on featuresString and Create Account operation exists (Task 3d); then retry.

### Task 9 — Update Account (entitlements) → prove with curl

1. On the Wire link for `lab.wsdeep1`, update managed entitlements to include **`WIRE_INIT`** (Entitlement catalog / account entitlements — path varies), **or** trigger Update Account with body entitlements `["WIRE_INIT"]`  
2. Wait for Provisioning Transaction Committed  
3. Prove:

```bash
curl -s http://localhost:8091/users/wp-lab-wsdeep1 | python3 -m json.tool
```

- **Expect:** `"entitlements": ["WIRE_INIT"]` (or list containing `WIRE_INIT`).

Save as `after-update.json`.

- **Why:** Update is a different operation than Create — both must be wired or movers leave stale entitlement arrays.
- **Expect:** mock entitlements match the plan.

### Task 10 — Disable Account → prove with curl + re-agg

1. On the Wire account → **Disable** (or Manage → Disable Account)  
2. Wait for Committed  
3. Prove:

```bash
curl -s http://localhost:8091/users/wp-lab-wsdeep1 | python3 -m json.tool | grep -E 'username|active|entitlements'
```

- **Expect:** `"active": false` (row still present — not deleted).

4. Aggregate `MNB-WirePortal` → cube link shows inactive/disabled  

Save as `after-disable.json`.

- **Why:** leavers need soft-disable on the API; hard delete loses audit evidence.
- **Expect:** Disable op used PATCH `active=false`; Get Object / agg reflects it.

### Task 11 — Pagination note (document, don’t invent pages)

This mock’s `/users` is a single non-paged document. Under evidence write `pagination-note.txt`:

```text
Wire /users: no nextPageUrl / offset — Enable Has More must stay false.
If a future portal paginates, WS would need pagingInitialOffset + paginationSteps
(or next-link headers) — contrast SCIM startIndex/count on Lesson 238 CRM.
```

- **Why:** turning Has More on against a non-paged API is a common zero-account failure.
- **Expect:** note saved; you did not enable fake paging.

### Task 12 — Evidence pack

Confirm `~/iiq-lab-evidence/sandbox/237/` has:

```text
users-baseline.json
baseline-count.txt
rootpath-error.txt
auth-error.txt
after-create.json
after-update.json
after-disable.json
pagination-note.txt
```

- **Expect:** an IR lead can replay Create → Update → Disable from files alone.

## If it fails

| Symptom | Fix |
| --- | --- |
| App is Delimited File | Wrong object — create/use Web Services `MNB-WirePortal` (Lesson 209) |
| Test Connection can’t resolve host | Base URL must be `http://connector-mock:8091`, not `localhost` |
| Test OK, Aggregation zero | Response Mapping missing; `rootPath` not `$.users`; Has More still true |
| POST/PATCH `/users` → 404 from curl | Restart connector-mock / enterprise stack so mutable Wire handlers load |
| Create Account not in UI | Add `PROVISIONING` to featuresString + Create Account operation (Task 3d) |
| Disable fails / no op | Add `ENABLE` + Disable Account PATCH body `{"active":false}` |
| Plan Committed but curl unchanged | Wrong context URL or `$plan.nativeIdentity$` ≠ mock `id`; open PT detail |
| Used Helen/Priya/Marcus | Stop — create `lab.wsdeep1` and restart from Task 7 |

## You are done when

- [ ] Operation table includes Test Connection, Aggregation, Get Object, Create, Update, Disable  
- [ ] You captured distinct `rootPath` vs auth failure texts  
- [ ] `curl` proved Create (`wp-lab-wsdeep1`), Update (`WIRE_INIT`), Disable (`active=false`)  
- [ ] Re-agg shows the disabled link on `lab.wsdeep1`  
- [ ] Evidence folder has the files listed in Task 12  

## Control note

- **Control:** Web Services connector fault-diagnosis + provision-path competency (mapping vs auth vs write ops)  
- **Owner:** IAM Engineering  
- **SLA (lab):** Root cause from Task Result / PT text; Create→Disable proved same session  
- **Evidence:** `~/iiq-lab-evidence/sandbox/237/`  
- **Out of scope:** Real Wire Portal OAuth, SCIM provision (use REST ops here)

## Quick check

1. Name three common WS failure modes. → Bad root path / Response Mapping, unfollowed pagination, broken auth  
2. Does Test Connection prove Aggregation works? → No — mapping can still yield zero accounts  
3. Which mock path does Create use here? → `POST /users` (not SCIM)  
4. What proves Disable for real? → `curl` shows `active: false` on `/users/{id}`  
5. Why `lab.wsdeep1`? → Disposable write subject; shared personas stay clean for certs/SoD  

## Feedback

Could you rebuild the six-operation table and prove Create→Update→Disable for a new `lab.*` user without this page?

If something failed, note the **task number**, the Provisioning Transaction message (if any), and whether `curl` or IIQ disagreed.

## Navigate

- Previous: [Lesson 236](236-jdbc-provision-policies.md)
- Next: [Lesson 238](238-scim-connector-deep.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
