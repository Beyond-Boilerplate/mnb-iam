# Lesson 211 — Keycloak as Workforce IdP

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~45 minutes  
**Prereq:** Lesson 201  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 73

> **Why (1–2 lines):** Okta-class OIDC/SCIM behavior, proven live, without paying for or provisioning a real Okta tenant. An examiner reviewing SSO controls wants to see public-vs-confidential client choices justified, not copy-pasted.

## What this is

Keycloak (`quay.io/keycloak/keycloak:24.0`, `start-dev --import-realm`) is this estate's **Okta-shaped** workforce identity provider — it plays the role a real bank would give Okta or Azure AD: the OIDC broker every SSO app (Employee Portal, Gitea) authenticates through, and (in principle) a SCIM target IIQ can provision into. It boots with the `meridian` realm pre-imported from `lab-data/enterprise/keycloak/meridian-realm.json`: four OIDC clients (`employee-portal`, `wire-portal` — both public with PKCE; `iiq-scim` and `gitea` — confidential, service-account style with client secrets), five groups (`mnb-employees`, `mnb-managers`, `wire-initiators`, `wire-approvers`, `portal-users`), and the three named personas (`helen.ross`, `priya.wire`, `marcus.approve`) with `LabUser1!` passwords and an `employeeId` attribute already set for correlation. `MNB-Okta` is the IIQ Application object aimed at this realm — treat its SCIM aggregation as a documented stretch item for this lesson (see **If it fails**); the realm's OIDC discovery endpoint is the part you should fully trust today.

## Know these

| Client | Type | Pattern |
| --- | --- | --- |
| `employee-portal` | Public + PKCE (`S256`) | secretless browser/SPA app |
| `wire-portal` | Public + PKCE | same pattern |
| `gitea` | Confidential + secret + PKCE | server-side app that *can* keep a secret |
| `iiq-scim` | Confidential, service accounts on | machine-to-machine, no browser flow |

**Wrong way:** Configuring a browser-facing app (like `employee-portal`) as a confidential client with a hardcoded secret — a public SPA has nowhere safe to keep it; PKCE is the correct control for that trust level, not a shared secret.

## Intent

- Get comfortable in the Keycloak admin console: realm, clients, groups, users.
- Confirm all three seeded personas exist with correct group memberships and the `employeeId` attribute IIQ correlation depends on.
- Fetch the realm's OIDC discovery document and identify the endpoints every SSO app in this path (Portal, Gitea) will use.
- Understand exactly why the two browser-adjacent OIDC clients are configured differently (public+PKCE vs. confidential+secret) and what that implies operationally.

## Before you start

- [ ] Lesson 201 stack up; Keycloak reports healthy
- [ ] Admin console reachable at `http://localhost:8085/admin/`
- [ ] `curl` + `python3` available for the discovery document
- [ ] Evidence dir: `mkdir -p ~/iiq-lab-evidence/sandbox/211`

## Do this

1. Open `http://localhost:8085/admin/`, log in `admin`/`admin`, switch the realm selector to **meridian**.  
   **Why:** the `master` realm is Keycloak's own admin realm — all workforce config lives in `meridian`.  
   **Expect:** realm selector shows `meridian` active.

2. Under **Users**, confirm `helen.ross`, `priya.wire`, `marcus.approve` exist, each `Enabled`, credential `LabUser1!` (non-temporary). Open Helen's **Attributes** tab.  
   **Why:** `employeeId = MNB00001` is the exact attribute IIQ's SCIM/correlation logic keys off of, mirroring `employeeNumber` in the LDAP directories.  
   **Expect:** `employeeId` attribute present and correct for Helen.

3. Under **Groups**, confirm five groups exist and memberships: Helen in `mnb-employees` + `mnb-managers`, Priya in `wire-initiators`, Marcus in `wire-approvers`, all three also in `portal-users`.  
   **Why:** `portal-users` is the group Employee Portal login checks in Lesson 212.  
   **Expect:** memberships match exactly.

4. Under **Clients**, open `employee-portal`: `Public client` = ON, `Standard flow` = ON, PKCE requires `S256`.  
   **Why:** the modern secretless SPA/browser pattern — appropriate because the portal has nothing safe to hide a secret in.  
   **Expect:** settings match.

5. Open `gitea`: `Public client` = OFF (confidential), client secret `mnb-gitea-oidc-secret`, PKCE also configured, redirect URI `http://localhost:8093/user/oauth2/meridian/callback`.  
   **Why:** the right pattern for a server-side app that *can* keep a secret; you'll type source name `meridian` into Gitea itself in Lesson 213.  
   **Expect:** settings match.

6. Open `iiq-scim`: confidential, `Service Accounts Enabled` = ON, no standard/browser flow.  
   **Why:** the machine-to-machine credential pattern IIQ itself would use to call Keycloak's admin/SCIM APIs directly, versus a human browser login.  
   **Expect:** settings match.

7. Fetch the discovery document: `curl -s http://localhost:8085/realms/meridian/.well-known/openid-configuration | python3 -m json.tool | head -20`.  
   **Why:** every OIDC relying party (Portal, Gitea) resolves `authorization_endpoint`, `token_endpoint`, `jwks_uri` from this one document instead of hardcoding them.  
   **Expect:** all three endpoints visible in the output.

8. Note the `issuer` value: `http://localhost:8085/realms/meridian`.  
   **Why:** any *server-side* process inside another container needing this issuer URL must resolve `localhost` from inside its own container — which does not point at Keycloak by default. This is exactly why Employee Portal's compose config adds `extra_hosts: host.docker.internal:host-gateway` and a separate `KEYCLOAK_INTERNAL_URL`; you'll hit the same class of issue with Gitea in Lesson 213.  
   **Expect:** you can explain this gotcha before starting Lesson 213.

## If it fails

- **Admin console won't load** — Keycloak's healthcheck has a 60s `start_period`; check `docker logs mnb-keycloak` for `Imported realm meridian` before assuming it's stuck.
- **Admin console redirects to HTTPS or refuses HTTP** — the `keycloak-http-relax` one-shot job should have relaxed the master realm's HTTPS-only default; re-trigger it: `docker compose -f docker-compose.iiq.yml -f docker-compose.enterprise.yml --profile enterprise up -d keycloak-http-relax`.
- **`MNB-Okta` Test Connection in IIQ fails or times out** — expected and documented: Keycloak SCIM often needs an admin token not wired up in this lab profile. Don't burn time on this; the OIDC discovery surface (steps 7–8) is what this lesson actually certifies.
- **A persona is missing or has no password** — re-import the realm: tear down the Keycloak volume, then `up.sh --enterprise` again to re-import from the JSON file fresh.
- **`curl` to the discovery endpoint hangs** — use `localhost:8085`, not `keycloak:8080` (internal hostname only resolves inside the Docker network).

## You are done when

You can log into the Keycloak admin console for the `meridian` realm, name all three seeded personas' group memberships from memory, and have fetched the realm's OIDC discovery document with `curl`.

## Control note

- **Control:** Workforce IdP configuration integrity — client trust model matches app risk profile.
- **Owner:** IAM Ops / IdP team.
- **SLA (lab):** any new client's public-vs-confidential choice reviewed before go-live.
- **Evidence:** `~/iiq-lab-evidence/sandbox/211/` — discovery document output, client config screenshots for all four clients.

## Quick check

1. Why is `employee-portal` public+PKCE instead of confidential? → it's a browser/SPA app with nowhere safe to keep a secret.
2. Which attribute does Keycloak carry for IIQ correlation? → `employeeId`.
3. Why can't Gitea reach `localhost:8085` from inside its own container for the discovery URL? → `localhost` there means the Gitea container itself, not the Docker host running Keycloak.

## Navigate

- Previous: Lesson 210
- Next: Lesson 212
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
