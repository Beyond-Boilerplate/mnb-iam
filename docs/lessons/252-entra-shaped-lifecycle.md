# Lesson 252 — Entra-Shaped Lifecycle (Mock Graph/SCIM)

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~50 minutes  
**Prereq:** Lessons 210–211, 251  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 59 / 73 (Entra/Okta narrative)

> **Why:** You need an Entra-shaped account API for IIQ labs without paying a Microsoft tenant tax — but confusing "account disabled in the directory mock" with "SSO actually dead" is exactly the silent failure that breaks leaver proof.

## What this is

`MNB-EntraID` talks to **connector-mock** Entra-shaped APIs (`/entra/v1/users`, `/entra/scim/v2/Users`) — not a real Entra tenant. **Browser SSO still uses Keycloak.** This app exists so aggregation, disable, and group metadata look like cloud directory work in IIQ. Login proofs after disable still require disabling/removing groups in **Keycloak** — the identity master sync story.

## Know these

| System | Owns |
| --- | --- |
| `MNB-EntraID` (connector-mock) | IIQ lifecycle: aggregation, disable state, group metadata |
| Keycloak | Actual browser SSO / login |
| PATCH on the mock | Does **not** by itself kill Keycloak SSO |

**Wrong way:** Assuming PATCHing `active:false` on the Entra-shaped mock kills a user's Employee Portal login — that's out of scope for the mock; only Keycloak controls SSO.

## Intent

- Hit the Entra-shaped mock with curl and see Helen/Priya/Marcus.
- Import/test `MNB-EntraID` and aggregate accounts.
- PATCH disable on the mock and note it does **not** by itself kill Keycloak SSO.
- Document the honest split: mock = IIQ lifecycle; Keycloak = login.

## Before you start

- [ ] `connector-mock` healthy: `curl -sf http://localhost:8091/health`
- [ ] Lesson 210/211 SCIM and Keycloak concepts fresh
- [ ] `MNB-EntraID` application object or its config XML available
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/252`

## Do this

1. `curl -sf http://localhost:8091/entra/v1/users | python3 -m json.tool | head -40`.  
   **Expect:** Graph-shaped user list including Helen/Priya/Marcus.
2. `curl -sf 'http://localhost:8091/entra/scim/v2/Users?filter=userName%20eq%20%22priya.wire%22' | python3 -m json.tool`.  
   **Expect:** SCIM-shaped single-user result.
3. Ensure `MNB-EntraID` is in IIQ (`./tools/lab/enterprise/seed-enterprise.sh` or import `config/Application/MNB-Application-EntraID.xml`). Test connection / aggregate accounts (SCIM base path `/entra/scim/v2` on `http://connector-mock:8091`).  
   **Expect:** Aggregation completes with accounts imported.
4. Correlate `externalId`/`userName` to identity `userId`/`name` using the enterprise correlation standard.  
   **Expect:** Accounts correlate to existing identities.
5. PATCH disable Priya on the mock: `curl -sf -X PATCH http://localhost:8091/entra/scim/v2/Users/entra-priya -H 'Content-Type: application/json' -d '{"Operations":[{"op":"replace","path":"active","value":false}]}' | python3 -m json.tool`.  
   **Expect:** 200 response confirming the mock's record is now inactive.
6. Re-aggregate `MNB-EntraID`.  
   **Expect:** Priya's account shows inactive in IIQ.
7. Confirm Employee Portal SSO as Priya **still works** until she's also disabled in Keycloak or her groups removed.  
   **Expect:** Login succeeds — write that one-liner in your evidence notes so the two systems never get confused.

## If it fails

- **404 on /entra/...** — rebuild connector-mock so `serve.py` includes Entra routes.
- **IIQ SCIM path wrong** — set host to `http://connector-mock:8091` and SCIM base `/entra/scim/v2` in the application.
- **Expecting SSO death from mock PATCH alone** — out of scope for the mock; Keycloak is the IdP.

## You are done when

You have aggregated `MNB-EntraID`, disabled a user on the mock, and written the one-line Keycloak-vs-mock split in your notes.

## Control note

- **Control:** Correct system-of-record boundary for cloud-directory-shaped lifecycle vs actual SSO.  
- **Owner:** IAM Engineering.  
- **SLA (lab):** No lesson artifact conflates mock disable with SSO revocation.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/252/` — Graph/SCIM curl output, PATCH response, Keycloak-vs-mock note.

## Quick check

1. Does disabling a user on `MNB-EntraID` kill their Employee Portal login? → No — only Keycloak controls SSO.  
2. What does `MNB-EntraID` actually own? → IIQ lifecycle (aggregation, disable state, group metadata).  
3. What must also happen for SSO to actually die? → Disable/remove groups in Keycloak.

## Navigate

- Previous: Lesson 251
- Next: Lesson 253
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
