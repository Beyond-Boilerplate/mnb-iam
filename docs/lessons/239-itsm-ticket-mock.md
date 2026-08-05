# Lesson 239 — ITSM Ticket Mock Fulfillment

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~50 minutes  
**Prereq:** Lesson 221  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 72

> **Why:** Some access is ticket-fulfilled, not connector-provisioned. Governance still has to live in IIQ, or an examiner can't trace who approved a manually-fulfilled grant.

## What this is

`MNB-ServiceNow` (`WebServicesConnector`, base `http://connector-mock:8091/itsm/v1`) models a common bank pattern: some entitlements are too manual or system-specific for a real connector, so IIQ raises the request/decision but hands physical fulfillment to a ticket. The mock exposes `/itsm/v1/catalog` (what can be requested) and `/itsm/v1/tickets` (create/read). The `IdentityRequest` is still the system of record — the proof of completion is a ticket id round-tripped back into IIQ comments.

## Know these

| Endpoint | Purpose |
| --- | --- |
| `GET /itsm/v1/catalog` | Ticket-fulfilled access types (mainframe/RACF-style, physical badge) |
| `POST /itsm/v1/tickets` | Simulates what the connector does on IIQ's behalf |
| IdentityRequest comment | The actual audit link between request and real-world fulfillment |

**Wrong way:** Treating the IdentityRequest as complete with no ticket id in the comments — that leaves no evidence the real-world action ever happened.

## Intent

- Read the ITSM catalog to see what's ticket-fulfilled versus connector-provisioned.
- Create a ticket via the mock's API, simulating what IIQ's WS connector would do.
- Confirm `MNB-ServiceNow`'s Test Connection actually reaches the same endpoint.
- Attach the resulting ticket id to a real IdentityRequest's comments.

## Before you start

- [ ] `connector-mock` healthy: `curl -sf http://localhost:8091/health`
- [ ] `MNB-ServiceNow` application object present
- [ ] Lesson 221 request flow working for `helen.ross`
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/239`

## Do this

1. `curl -s http://localhost:8091/itsm/v1/catalog | python3 -m json.tool`.  
   **Expect:** Catalog items representing access types that are ticket-fulfilled, not auto-provisioned.
2. Submit a real access request in IIQ (**Manage Access → Request Access**, 221's flow) for one of these items as `helen.ross`. Note the resulting `IdentityRequest` id.  
   **Expect:** Request confirmation screen shows the id.
3. Simulate IIQ's side of fulfillment: `curl -s -X POST http://localhost:8091/itsm/v1/tickets -H 'Content-Type: application/json' -d '{"requester":"helen.ross","item":"<catalog item name>","identityRequestId":"<id from step 2>"}' | python3 -m json.tool`.  
   **Expect:** Returns a ticket id — capture it.
4. **Applications → Application Definition → MNB-ServiceNow → Test Connection**.  
   **Expect:** Succeeds and genuinely hits `/itsm/v1/catalog` (check `contextUrl` matches step 1) — proves the app object isn't decorative.
5. `curl -s http://localhost:8091/itsm/v1/tickets | python3 -m json.tool`.  
   **Expect:** Your ticket from step 3 listed with the correct `identityRequestId`.
6. In IIQ's **Access Request Status** (or the pending work item), add a comment with the ticket id, e.g. `Fulfilled via ServiceNow ticket <id>`.  
   **Expect:** Comment saved — this is the actual audit link.
7. Write one line: IIQ owns this access because the request/approval/policy decision happened in IIQ; ServiceNow only executed the mechanical fulfillment.  
   **Expect:** Note saved with evidence.
8. Save the catalog JSON, ticket creation response, and the commented IdentityRequest screenshot under `~/iiq-lab-evidence/sandbox/239/`.

## If it fails

- **POST to `/itsm/v1/tickets` returns 400** — check the mock's error message; `requester` and `item` are the minimum required fields.
- **Test Connection fails on MNB-ServiceNow** — confirm `connector-mock` is healthy and the app's `contextUrl` is exactly `/catalog` per its shipped config.
- **Ticket doesn't show the identityRequestId you sent** — re-check the GET response's exact field names and adjust your POST body to match.

## You are done when

A ticket id created against the live ITSM mock is linked into an IIQ IdentityRequest's comments, and you can explain who owns what in one line.

## Control note

- **Control:** Governance-of-record for manually-fulfilled (ticket-based) access.  
- **Owner:** IAM Engineering + ITSM/Ops.  
- **SLA (lab):** Ticket id attached to IdentityRequest same session as fulfillment.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/239/` — catalog JSON, ticket response, commented request.

## Quick check

1. Who "owns" ticket-fulfilled access — IIQ or ServiceNow? → IIQ (request/approval/policy); ServiceNow only executes.  
2. What proves the real-world action happened? → Ticket id in the IdentityRequest comments.  
3. What two fields does the mock require to create a ticket? → `requester`, `item`.

## Navigate

- Previous: Lesson 238
- Next: Lesson 240
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
