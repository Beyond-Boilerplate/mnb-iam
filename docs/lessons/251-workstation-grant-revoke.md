# Lesson 251 — Workstation Grant → Login → Revoke Lockout

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~55 minutes  
**Prereq:** Lessons 211–213, 221–222  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** access + login proof (DoD #3/#4)

> **Why:** Laptop access is only real if the user can log in after grant and cannot after revoke. Authentication without entitlement is not access — it's a login screen that says no.

## What this is

**Workstation Portal** (`http://localhost:8094/`) is an OIDC relying party. After Keycloak authenticates you, the app checks the ID token `groups` claim for `mnb-workstation-users`. Missing group → **Access denied** — you authenticated, but you are not entitled. This is the lab stand-in for "can this person unlock a laptop/workstation session?", not Intune enrollment. Helen is seeded **with** the group; Priya is seeded **without** it so you can prove both paths.

## Know these

| State | Proof |
| --- | --- |
| Authenticated, not entitled | Keycloak login succeeds, app shows **Access denied** |
| Entitled | `groups` claim contains `mnb-workstation-users` |
| Two grant paths | IIQ role→group (production story) or direct Keycloak group add (fast lab path) |

**Wrong way:** Treating a successful Keycloak login as proof of access — authentication and entitlement are two different checks; this app enforces both.

## Intent

- Deny Priya at the workstation gate before any grant.
- Request/approve `MNB-Bundle-Workstation-Access` (or add her to Keycloak group `mnb-workstation-users`).
- Prove Priya can complete Workstation login after grant.
- Revoke the group/role and prove she is locked out again.

## Before you start

- [ ] `workstation-portal` container healthy on `:8094`
- [ ] `priya.wire` / `LabUser1!` and `helen.ross` / `LabUser1!` credentials confirmed
- [ ] Keycloak Admin reachable at `http://localhost:8085/admin/`, realm `meridian`
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/251`

## Do this

1. `curl -sf http://127.0.0.1:8094/health | python3 -m json.tool`.  
   **Expect:** `requiredGroups: ["mnb-workstation-users"]`.
2. Open `http://localhost:8094/` → sign in as `priya.wire` / `LabUser1!`.  
   **Expect:** After IdP login, lands on **Access denied** (no workstation group). Leave the tab open as evidence of the deny state.
3. As `spadmin` (or Helen), make `MNB-Bundle-Workstation-Access` requestable if needed, then submit an Access Request for Priya (or add her to Keycloak group `/mnb-workstation-users` directly for a faster first pass).  
   **Expect:** IIQ role→group is the production story; Keycloak admin proves the gate itself before connector wiring is perfect.
4. If you used IIQ, complete approvals (222's pattern), then ensure the Keycloak group membership exists (manual add for lab if SCIM→Keycloak isn't wired for this role).  
   **Expect:** Membership visible in Keycloak Admin.
5. Sign out of Workstation; sign in again as `priya.wire`.  
   **Expect:** **Signed in** / workstation session established.
6. Revoke: remove Priya from `mnb-workstation-users` in Keycloak (and/or revoke the IIQ role and re-provision). Sign out and sign in again.  
   **Expect:** **Access denied** returns.
7. Optional control: as `helen.ross`, confirm she can still sign in (seeded with the group).  
   **Expect:** Helen unaffected by Priya's revoke.

## If it fails

- **No `groups` claim / always denied even after Keycloak group add** — realm clients need the `oidc-group-membership-mapper`. Fresh Keycloak volume re-imports `lab-data/enterprise/keycloak/meridian-realm.json`; existing volume — add the mapper on client `workstation-portal` or wipe `mnb-keycloak-data` and recreate Keycloak.
- **8094 not up** — `docker compose -f docker-compose.iiq.yml -f docker-compose.enterprise.yml --profile enterprise up -d --build workstation-portal`.
- **IdP login works but wrong client** — confirm `OIDC_CLIENT_ID=workstation-portal` and redirect URI `http://localhost:8094/*`.

## You are done when

Priya is denied without the group, allowed after grant, and denied again after revoke — with Helen still able to sign in.

## Control note

- **Control:** Workstation entitlement gate (grant/revoke lockout proof).  
- **Owner:** IAM Engineering + Endpoint/Workstation Ops.  
- **SLA (lab):** Revoke reflected in denied login same session.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/251/` — three login states (denied, granted, denied again).

## Quick check

1. Does a successful Keycloak login prove access? → No — the app separately checks the `groups` claim.  
2. What claim gates workstation access? → `groups` containing `mnb-workstation-users`.  
3. Why keep Helen's control check? → Proves the revoke was scoped to Priya, not global.

## Navigate

- Previous: Lesson 250
- Next: Lesson 252
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
