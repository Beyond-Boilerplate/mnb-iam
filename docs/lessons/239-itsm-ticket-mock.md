# Lesson 239 — ITSM Ticket Mock Fulfillment

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~70 minutes  
**Prereq:** Lessons 221–222  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 72

> **Why:** Some access is ticket-fulfilled, not connector-provisioned — mainframe, badge, vendor portals. Governance still has to live in IIQ, or you cannot answer “who approved this and which INC actually did the work?” when helpdesk or IR asks later.

## What this is

**`MNB-ServiceNow`** is a `WebServicesConnector` fulfillment channel against:

```text
http://connector-mock:8091/itsm/v1
```

| Endpoint | Role |
| --- | --- |
| `GET /itsm/v1/catalog` | Ticket-fulfilled catalog items |
| `POST /itsm/v1/tickets` | Open a ticket (what IIQ’s Create Account op must call) |
| `GET /itsm/v1/tickets` | List tickets — proof of ticket id |

Seeded app often has **only Test Connection** → `/catalog`. This lesson wires **Create Account → POST /tickets`**, drives fulfillment from IIQ for disposable **`lab.itsm1`**, and captures the **ticket id** on the IdentityRequest / evidence — not a manual curl-only demo.

IIQ remains system of record (request / approval / policy). The mock only executes mechanical fulfillment.

> **Watch out:** A closed or created ticket alone is not revoke evidence on a real target. Here the **target is the ticket itself** — proof is ticket id round-tripped into IIQ comments / PT detail.

## Know these

```text
curl GET /itsm/v1/catalog → pick REQ-VPN (or REQ-LAPTOP)
  → Verify MNB-ServiceNow base URL + Test Connection
  → Add Create Account POST /tickets + JSON body ($plan.*)
  → Add Create provisioning policy fields
  → Hire lab.itsm1 + manager sanjay.kapoor
  → Request Access (or Create Account) so IIQ provisions ServiceNow
  → Approve if LCM requires (221–222 path)
  → curl GET /tickets → capture ticket id (INC…)
  → Paste ticket id on IdentityRequest comment
  → Evidence: catalog + ticket JSON + IR id + comment screenshot
```

| Term | Plain English | Meridian example |
| --- | --- | --- |
| **Fulfillment channel** | IIQ decides; ITSM executes | `MNB-ServiceNow` → mock tickets |
| **Catalog item** | What can be ticketed | `REQ-VPN`, `REQ-LAPTOP`, `REQ-WIRE` |
| **Ticket id** | External work reference | `INCAB12CD` from POST response |
| **IdentityRequest** | IIQ audit spine | Comment carries ticket id |
| **Create Account (WS)** | Provision op that POSTs | Body includes `requestedFor` + `catalogId` |

Catalog (lab seed — confirm live with curl):

| id | name | fulfillment |
| --- | --- | --- |
| `REQ-LAPTOP` | Laptop Access | manual |
| `REQ-VPN` | VPN Access | group |
| `REQ-WIRE` | Wire Portal Entitlement | iiq |

- **Wrong way:** Only `curl POST /tickets` without IIQ Create Account — that skips the governance path this lesson exists to prove.  
- **Wrong way:** Completing the IdentityRequest with no ticket id in comments.  
- **Wrong way:** Using Helen as the subject — use `lab.itsm1`.  
- **Wrong way:** Treating Test Connection green as “fulfillment works” — Create Account must be wired.  
- **Wrong way:** Confusing ServiceNow-as-**target** (account governance) with ServiceNow-as-**channel** (this lesson).

## Intent

- Read the live ITSM catalog.  
- Wire `MNB-ServiceNow` Create Account to `POST /tickets`.  
- Drive an IIQ provision for `lab.itsm1` that opens a real mock ticket.  
- Capture ticket id on the IdentityRequest and under evidence.

## Before you start

Complete every checkbox. Do not skip into Task 1 until these are true.

- [ ] IIQ up: [http://localhost:8080/identityiq](http://localhost:8080/identityiq) — `spadmin` / `admin`
- [ ] Mock healthy:

```bash
curl -sf http://localhost:8091/health
```

- [ ] Lesson 221–222 idea familiar (Request Access + approvals). You will **re-check** LCM if you use the request path.
- [ ] Evidence dir:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/239
```

## Do this

### Task 1 — Read the ITSM catalog (ground truth)

```bash
curl -s http://localhost:8091/itsm/v1/catalog | python3 -m json.tool
```

Save as `catalog.json`. Pick **`REQ-VPN`** for this drill (any catalog `id` works if you stay consistent).

- **Why:** Create Account body must send a real `catalogId` the mock accepts.
- **Expect:** JSON list with `REQ-LAPTOP`, `REQ-VPN`, `REQ-WIRE` (or regenerated equivalents).

### Task 2 — Verify `MNB-ServiceNow` Application

1. **Applications → Application Definition → MNB-ServiceNow**  
2. Confirm:

| Setting | Required |
| --- | --- |
| Type | **Web Services** |
| Base URL | `http://connector-mock:8091/itsm/v1` |
| Auth | No Auth |
| featuresString | includes **`PROVISIONING`** |

3. **Test Connection** → green (seed op is usually `GET /catalog`)

If the Application is missing: **New → Web Services**, name `MNB-ServiceNow`, base URL above, Test Connection `GET` context `/catalog`, schema attrs `id`, `name`, `fulfillment` (identity=`id`, display=`name`), featuresString `PROVISIONING`.

- **Why:** assume-nothing — seed may be absent after wipe.
- **Expect:** Test Connection reaches the same catalog you curled in Task 1.

### Task 3 — Add Create Account → POST `/tickets`

On **HTTP Operations**, add (keep existing Test Connection):

| Field | Value |
| --- | --- |
| Operation | **Create Account** |
| Method | **POST** |
| Context URL | `/tickets` |
| Body format | raw JSON |
| Success codes | `2**` |

JSON body (paste exactly):

```json
{
  "requestedFor": "$plan.nativeIdentity$",
  "requester": "spadmin",
  "catalogId": "$plan.catalogId$",
  "item": "$plan.catalogId$",
  "shortDescription": "IIQ fulfillment for $plan.nativeIdentity$ item $plan.catalogId$",
  "identityRequestId": "$plan.identityRequestId$"
}
```

Response Mapping (capture ticket id into account `id` if the UI allows):

| Schema attr | JSON path |
| --- | --- |
| `id` | `id` |
| `name` | `shortDescription` |
| `fulfillment` | `state` |

**Save** the Application.

> **Tip:** If `$plan.identityRequestId$` does not expand on direct Create Account (no IR yet), the mock still accepts the POST — you will paste the ticket id onto the IR manually in Task 9. Prefer the Request Access path (Task 7–8) so an IR exists.

- **Why:** this is the E2E wire — IIQ provision must call the mock, not only your terminal.
- **Expect:** Create Account operation saved on `MNB-ServiceNow`.

### Task 4 — Create provisioning policy fields

1. **Applications → MNB-ServiceNow → Provisioning Policies** (or Policies tab)  
2. Add **Create** policy with fields:

| Field name | Value / type |
| --- | --- |
| `nativeIdentity` / account id | String — will be `lab.itsm1` (requestedFor) |
| `catalogId` | String — default or form value `REQ-VPN` |
| `name` | optional display |

Exact UI labels vary — the plan attribute names must match `$plan.catalogId$` and `$plan.nativeIdentity$` in Task 3.

3. **Save**

- **Why:** without policy fields, Create Account POST sends empty catalog/requester and the mock returns 400.
- **Expect:** Create policy exists before you provision.

### Task 5 — Disposable identity `lab.itsm1`

```bash
./tools/lab/enterprise/hcm-scenario.sh joiner lab.itsm1 Lab Itsm \
  lab.itsm1@meridiannb.com 'Bank Operations'
```

```bash
curl -s http://localhost:8091/hcm/v1/workers/lab.itsm1 \
  | python3 -m json.tool | grep -E 'userName|email|active|status'
```

1. Aggregate **`MNB-Workday`** → Complete  
2. **Refresh Identity Cube** for `lab.itsm1` → Complete  
3. Edit cube → set **Manager** = **`sanjay.kapoor`** → Save  

- **Why:** Manager Approval (if LCM mapped) needs a real manager; disposable subject keeps Helen clean.
- **Expect:** cube exists with manager Sanjay.

### Task 6 — Confirm LCM map (if using Request Access)

Do not assume Lesson 222 left the map correct.

1. Gear → **Lifecycle Manager** → **Business Processes**  
2. Prefer both **Access Request** and **Roles Request** → `MNB-Workflow-Access-Approval`  
3. Fallback: `LCM Provisioning` with `approvalScheme=manager,owner`, `approvalMode=serial`  

Write under evidence which path you use.

- **Why:** wrong map = wrong approvers = stuck request, no provision, no ticket.
- **Expect:** LCM confirmed before Task 7.

### Task 7 — Drive fulfillment from IIQ (preferred: Request Access)

Goal: an IdentityRequest that ends in a ServiceNow Create Account / provision calling `POST /tickets`.

**Option A — Create Account directly (fastest proof of connector wire):**

1. Open `lab.itsm1` → **Create Account** → **`MNB-ServiceNow`**  
2. Set native identity / requestedFor = `lab.itsm1`  
3. Set `catalogId` = `REQ-VPN`  
4. Submit → wait Provisioning Transaction **Committed**  
5. Note PT id under evidence  

**Option B — Request Access (full governance path):**

1. Ensure a **requestable** role or entitlement path that provisions `MNB-ServiceNow` / catalog item `REQ-VPN`  
   - If none exists: create IT pack + requestable business role whose provision plan includes Create Account on `MNB-ServiceNow` with `catalogId=REQ-VPN`, **or** use Option A and still open/complete a small Access Request for an existing requestable role so you have an IR to comment  
2. As `spadmin`, **Request Access** on behalf of `lab.itsm1`  
3. Justification:

```text
LAB-239 — ticket fulfillment drill for REQ-VPN
```

4. Approve Manager (Sanjay) + Owner as needed  
5. Wait for provision / PT Committed  

Write:

```text
Path used: Option A Create Account | Option B Request Access
IdentityRequest id (if any): ________
Provisioning Transaction id: ________
```

- **Why:** the lesson bar is IIQ→mock, not terminal→mock.
- **Expect:** PT Committed for `MNB-ServiceNow` Create.

> **Watch out:** If you only have Option A, still create or locate an IdentityRequest (even a related access request) so Task 9 has a comment target — or comment on the PT and record that as the audit link for lab purposes.

### Task 8 — Prove the ticket id on the mock

```bash
curl -s http://localhost:8091/itsm/v1/tickets | python3 -m json.tool
```

Find the ticket where `requestedFor` / `requester` is `lab.itsm1` and `catalogId` / `item` is `REQ-VPN`.

Save full object as `ticket.json`. Copy **`id`** (e.g. `INC…`).

```bash
# optional: pretty one-liner
curl -s http://localhost:8091/itsm/v1/tickets \
  | python3 -c "import sys,json; ts=json.load(sys.stdin).get('tickets') or [];
print('\n'.join(f\"{t.get('id')} for={t.get('requestedFor')} cat={t.get('catalogId')} ir={t.get('identityRequestId')}\" for t in ts))"
```

- **Why:** ticket id is the external evidence string auditors ask for.
- **Expect:** at least one new ticket for `lab.itsm1` / `REQ-VPN` created by IIQ’s POST (timestamp matches your PT).

If the list is empty: open PT detail for HTTP status/body; confirm Create Account context URL is `/tickets` (relative to base `/itsm/v1`); retry Create.

### Task 9 — Attach ticket id to the IdentityRequest

1. Open the IdentityRequest from Task 7 (Access Request Status / Manage Access Requests)  
2. Add comment (exact pattern):

```text
Fulfilled via ServiceNow ticket <PASTE_TICKET_ID> — catalog REQ-VPN — lab.itsm1
```

3. Screenshot comment under evidence  
4. If you used Option A only and have no IR: paste the same comment onto the Provisioning Transaction notes / work item and write:

```text
No IdentityRequest for direct Create Account — ticket id recorded on PT ________
```

- **Why:** without the id in IIQ, the mock ticket is orphaned from governance.
- **Expect:** ticket id visible in IIQ comments **and** in `ticket.json`.

### Task 10 — Ownership one-liner + evidence pack

Write `ownership.txt`:

```text
IIQ owns request/approval/policy decision; ServiceNow mock only executed fulfillment.
Ticket id: ________
Subject: lab.itsm1
Catalog: REQ-VPN
IdentityRequest / PT: ________
```

Confirm folder contains:

```text
catalog.json
ticket.json
ownership.txt
(IR or PT screenshot with ticket id)
```

- **Expect:** one pack that answers “which INC fulfilled this grant?”

## If it fails

| Symptom | Fix |
| --- | --- |
| Test Connection fails | Base URL `http://connector-mock:8091/itsm/v1`; context `/catalog`; mock healthy |
| POST 400 from mock | Body needs `requestedFor`/`requester` and `catalogId`/`item` |
| Create Account missing | featuresString `PROVISIONING` + Task 3 operation |
| PT Failed | Open detail — wrong contextUrl (`/tickets` not `/itsm/v1/tickets` when base already includes `/itsm/v1`) |
| Tickets list empty after Committed | IIQ did not hit mock — confirm Docker hostname; re-test with curl POST using same JSON |
| No IdentityRequest | Use Option B or record ticket on PT (Task 9 honesty line) |
| Manager WI missing | Task 5 manager + Task 6 LCM; **resubmit** after fixing map |
| Used Helen | Stop — create `lab.itsm1` from Task 5 |

## You are done when

- [ ] `MNB-ServiceNow` Create Account posts to `/tickets`  
- [ ] IIQ provision for `lab.itsm1` / `REQ-VPN` reached Committed  
- [ ] `ticket.json` contains the ticket **id** for that subject  
- [ ] Ticket id appears on IdentityRequest comment (or documented PT fallback)  
- [ ] Ownership one-liner saved  

## Control note

- **Control:** Governance-of-record for ticket-fulfilled access (IR ↔ ticket id)  
- **Owner:** IAM Engineering + ITSM/Ops  
- **SLA (lab):** Ticket id attached same session as fulfillment  
- **Evidence:** `~/iiq-lab-evidence/sandbox/239/`  
- **Out of scope:** Real ServiceNow Table API / RITM workflows; verify-after-close on a separate connector target

## Quick check

1. Who owns ticket-fulfilled access — IIQ or ServiceNow? → IIQ (decision); ServiceNow executes  
2. What proves the real-world action in this lab? → Ticket id in IR/PT comments + mock GET  
3. Which HTTP op must IIQ call? → `POST /itsm/v1/tickets` via Create Account  
4. Why not curl-only? → Skips IdentityRequest / approval governance  
5. Why `lab.itsm1`? → Disposable subject; shared personas stay clean  

## Feedback

Could you wire a new ticket catalog item (`REQ-*`) through Create Account → approve → capture INC on the IR without this page?

If something failed, note the **task number**, PT error text, and whether `curl` showed a ticket while IIQ did not (or the reverse).

## Navigate

- Previous: [Lesson 238](238-scim-connector-deep.md)
- Next: [Lesson 240](240-logical-application-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
