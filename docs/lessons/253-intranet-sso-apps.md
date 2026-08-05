# Lesson 253 — Intranet SSO Apps (HR + Finance)

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~45 minutes  
**Prereq:** Lesson 251  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** logical apps / SSO estate

> **Why:** A bank has many internal websites; each needs its own grant and the same revoke proof. If HR and Finance share one group, you can't prove least privilege between them.

## What this is

Two more SSO gates share the Workstation (251) code path:

| App | URL | Required Keycloak group | IIQ role |
| --- | --- | --- | --- |
| HR Self-Service | `:8095` | `mnb-hr-intranet` | `MNB-Bundle-HR-Intranet` |
| Finance Portal | `:8096` | `mnb-finance-portal` | `MNB-Bundle-Finance-Portal` |

Helen is seeded into both groups; Priya is not. Employee Portal tiles link to these apps.

## Know these

| Concept | Detail |
| --- | --- |
| Independent gates | Each app checks its own required group — no shared group means no shared access |
| Health JSON | Exposes `requiredGroups` for each app — the exact match string |
| Shared image | Both apps run `mnb-sso-gate:local`, differ only by config |

**Wrong way:** Assuming granting one intranet group grants the other — these are deliberately independent gates; that's the point of the lesson.

## Intent

- Prove Priya denied on HR and Finance.
- Grant one group (HR), prove HR works while Finance still denies.
- Grant Finance, prove both work; revoke Finance, prove Finance denies again.

## Before you start

- [ ] Lesson 251 Workstation gate pattern understood
- [ ] `priya.wire` and `helen.ross` credentials confirmed
- [ ] Keycloak Admin reachable at `http://localhost:8085/admin/`, realm `meridian`
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/253`

## Do this

1. `curl -sf http://127.0.0.1:8095/health; curl -sf http://127.0.0.1:8096/health`.  
   **Expect:** Both return `requiredGroups` matching the table above.
2. As `priya.wire`, open `http://localhost:8095/` and `http://localhost:8096/`.  
   **Expect:** **Access denied** after IdP login on both.
3. In Keycloak Admin, add Priya to `/mnb-hr-intranet` only (or request `MNB-Bundle-HR-Intranet` and mirror the group).  
   **Expect:** Membership visible in Keycloak.
4. Retry HR, then Finance.  
   **Expect:** HR **Signed in**; Finance still **Access denied** — proves independent gates.
5. Add `/mnb-finance-portal`.  
   **Expect:** Both HR and Finance now succeed.
6. Remove the Finance group.  
   **Expect:** Finance denies again; HR still works.
7. From Employee Portal (`:8092`) as Helen, open the Workstation/HR/Finance tiles.  
   **Expect:** Each tile lands on the correct port.

## If it fails

- **Ports down** — `docker compose ... --profile enterprise up -d --build workstation-portal hr-intranet finance-portal` (shared `mnb-sso-gate:local` image).
- **Wrong required group** — health JSON shows `requiredGroups`; must match the Keycloak group name without a leading `/`.
- **Realm missing clients** — wipe/reimport the Keycloak volume or create clients `hr-intranet`/`finance-portal` with PKCE + groups mapper.

## You are done when

You demonstrated independent grant/revoke on HR vs Finance for the same user.

## Control note

- **Control:** Independent least-privilege gates across multiple intranet apps.  
- **Owner:** IAM Engineering + HR/Finance App Owners.  
- **SLA (lab):** Grant/revoke on one app never leaks entitlement to the other.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/253/` — deny-both, HR-only, both-granted, Finance-revoked states.

## Quick check

1. Does the HR group grant Finance access too? → No — independent required groups per app.  
2. Where do you find the exact group name an app checks? → Its `/health` JSON `requiredGroups`.  
3. What image do both apps share? → `mnb-sso-gate:local`, differing only by config.

## Navigate

- Previous: Lesson 252
- Next: Lesson 254
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
