# Lesson 212 — Employee Portal SSO Proof

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~35 minutes  
**Prereq:** Lesson 211  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** DoD #3

> **Why (1–2 lines):** Provision-then-login is the acceptance test a cube full of correlated accounts alone can never prove. An examiner asking "does access actually work" wants a login screenshot, not a database row.

## What this is

Employee Portal (`tools/employee-portal`, built from `docker/Dockerfile.employee-portal`) is a small OIDC relying-party web app whose entire purpose is to be a real, working login target. It authenticates against Keycloak's `meridian` realm using the `employee-portal` public client (PKCE, `S256`) you inspected in Lesson 211, and it checks that the signed-in user belongs to the `portal-users` group — every seeded persona already does. This is Success Criterion #3 from the Enterprise Lab Definition of Done: "User SSO into Employee Portal **and** Gitea via Keycloak." A correlated account link on a cube is necessary but not sufficient proof that access actually works end to end — this lesson is the sufficient part.

## Know these

- Login flow: portal → redirect to Keycloak `meridian` login → back to portal already authenticated — this round trip *is* the authorization-code + PKCE flow.
- The portal never sees or handles a persona's password itself — Keycloak owns the credential check.
- `MAILPIT_PUBLIC_URL`/`GITEA_PUBLIC_URL` env vars are baked into the portal's own config if it surfaces links to those tools.
- The portal's group check against `portal-users` is enforcement, not decoration — a Keycloak login that succeeds for a user *outside* that group should still fail the portal's own authorization check, distinct from failing authentication.
- **Wrong way:** Concluding "SSO works" after signing in as one persona once — you haven't proven session isolation until you sign out fully and sign in as a *second* persona and see different content.

## Intent

- Complete a real OIDC authorization-code + PKCE login flow as a workforce persona, not just admin.
- Confirm the portal enforces group membership (`portal-users`), not just "any valid Keycloak login."
- Sign in as a second, distinct persona and confirm the portal shows persona-specific content, not a shared/cached session.
- Know the one fix (`--force-recreate`/rebuild) for the most common local OIDC redirect-URI failure mode.

## Before you start

- [ ] Lesson 211 complete; `employee-portal` and `gitea` clients confirmed in Keycloak
- [ ] Employee Portal reachable at `http://localhost:8092/`
- [ ] Two persona credentials ready: `helen.ross` / `LabUser1!`, `priya.wire` / `LabUser1!`
- [ ] Evidence dir: `mkdir -p ~/iiq-lab-evidence/sandbox/212`

## Do this

1. Open `http://localhost:8092/` and click sign in.  
   **Why:** you should be redirected to Keycloak's own login page at `http://localhost:8085/realms/meridian/...` — the portal never handles the password itself.  
   **Expect:** redirect lands on Keycloak's login form, not a portal-hosted one.

2. Sign in as `helen.ross` / `LabUser1!`.  
   **Why:** this round trip (portal → Keycloak → back to portal with a token) is the entire authorization-code flow, compressed into one click.  
   **Expect:** redirected back to `http://localhost:8092/` already authenticated.

3. Explore whatever the portal UI exposes (profile info, links out to Mailpit/Gitea).  
   **Why:** the specific UI content matters less than the fact you got here via real SSO — this is proof, not a feature tour.  
   **Expect:** page reflects Helen's identity somewhere (name, email, or similar).

4. Sign out fully — not just closing the tab.  
   **Why:** the portal's own sign-out should also end the Keycloak session; otherwise a second "sign in" would silently reuse Helen's still-live session.  
   **Expect:** returning to the portal shows a logged-out state.

5. Sign in again as `priya.wire` / `LabUser1!`.  
   **Why:** proof the session boundary is real, not a UI illusion.  
   **Expect:** portal shows Priya's identity, not a stale cached view of Helen.

6. If you see a PKCE error, redirect-URI mismatch, or blank page after the Keycloak redirect, rebuild the portal fresh: `docker compose -f docker-compose.iiq.yml -f docker-compose.enterprise.yml --profile enterprise up -d --force-recreate --build employee-portal`.  
   **Why:** a known class of issue when Keycloak's realm import timing races the portal's own boot — a clean rebuild re-reads the current realm state.  
   **Expect:** the flow succeeds after rebuild.

7. Compare what you just proved against Lesson 206's pass-through login to IIQ itself.  
   **Why:** pass-through delegates a bind check to a directory; OIDC SSO delegates an entire browser redirect and token exchange to an IdP — same underlying goal ("don't check a local password"), two different mechanisms you'll see again with Gitea in Lesson 213.  
   **Expect:** you can name which mechanism (LDAP bind vs. OIDC authorization code) each app in this path uses.

## If it fails

- **"Invalid redirect_uri" after Keycloak login** — the `employee-portal` client's redirect URIs are `http://localhost:8092/*` and `http://employee-portal:8092/*`; access the portal via `localhost`, not `127.0.0.1`.
- **Login succeeds at Keycloak but portal shows a blank/error page** — check `docker logs mnb-employee-portal`; almost always the internal-vs-public Keycloak URL confusion from Lesson 211 (`KEYCLOAK_INTERNAL_URL=http://host.docker.internal:8085` for backend token exchange, `KEYCLOAK_PUBLIC_URL=http://localhost:8085` for browser redirects) — confirm `host.docker.internal` resolves inside the container: `docker exec mnb-employee-portal getent hosts host.docker.internal`.
- **Portal health endpoint is down** — `curl -sf http://localhost:8092/health`; if that fails, the container needs a restart, not a login-flow fix.
- **Priya's login shows Helen's data** — incomplete sign-out; clear the portal's session/cookies for `localhost:8092` and Keycloak's own SSO cookie for `localhost:8085` before retrying.

## You are done when

You've completed a real OIDC login as both `helen.ross` and `priya.wire`, confirmed a full sign-out between them, and can explain in one sentence why "she has a correlated account" and "she can actually log in" are different claims.

## Control note

- **Control:** SSO acceptance testing — login proof, not correlation alone.
- **Owner:** IAM Ops / application owner.
- **SLA (lab):** SSO proof required same session before an app is marked "integrated" in the DoD tracker.
- **Evidence:** `~/iiq-lab-evidence/sandbox/212/` — login screenshots for both personas, sign-out proof.

## Quick check

1. Which client/flow does the portal use? → `employee-portal`, public client with PKCE (`S256`).
2. What proves session isolation, not just "SSO works once"? → full sign-out then a second, different persona login showing different content.
3. What's the standard fix for a PKCE/redirect-URI race after Keycloak boots? → force-recreate/rebuild the `employee-portal` container.

## Navigate

- Previous: Lesson 211
- Next: Lesson 213
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
