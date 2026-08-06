# Lesson 212 — Employee Portal SSO Proof

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~35 minutes  
**Prereq:** Lesson 211  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** DoD #3

> **Why:** A cube full of correlated accounts is not ops proof. Prove access with a real login — provision-then-login is the acceptance test correlation alone can never pass.

## What this is

Employee Portal (`tools/employee-portal`) is a small OIDC relying-party web app built to be a real login target:

```text
http://localhost:8092/
```

It authenticates against Keycloak’s `meridian` realm using the `employee-portal` public client (PKCE, `S256`) from Lesson 211, and checks that the signed-in user belongs to `portal-users`.

This is Success Criterion #3 from the Enterprise Lab Definition of Done: *User SSO into Employee Portal **and** Gitea via Keycloak.* A correlated account link on a cube is necessary but not sufficient — this lesson is the sufficient part.

## Know these

| Idea | Detail |
| --- | --- |
| Authorization-code + PKCE | Portal → Keycloak login → back to portal with a token — that round trip *is* the flow |
| Who checks the password | Keycloak — the portal never sees or handles credentials |
| Group gate | `portal-users` — authentication ≠ authorization |
| Session isolation | Sign out fully, then a *second* persona must show different content |

```text
Browser → Portal (:8092)
       → redirect → Keycloak meridian login
       → code + PKCE → Portal token exchange
       → portal-users check → authenticated UI
```

- **Wrong way:** Concluding “SSO works” after one persona once — you haven’t proven session isolation until a second persona shows different content after a full sign-out.

## Intent

- Complete a real OIDC login as a workforce persona (not just admin).
- Confirm the portal enforces `portal-users`, not “any valid Keycloak login.”
- Sign in as a second persona and prove session isolation.
- Know the rebuild fix for the common local redirect-URI / PKCE failure mode.

## Before you start

- [ ] Lesson 211 complete; `employee-portal` client confirmed in Keycloak
- [ ] Portal reachable: [http://localhost:8092/](http://localhost:8092/)
- [ ] Credentials ready: `helen.ross` / `LabUser1!`, `priya.wire` / `LabUser1!`
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/212
```

## Do this

### Task 1 — Start the SSO redirect

Open the portal and begin sign-in. You should leave the portal domain entirely.

1. Open [http://localhost:8092/](http://localhost:8092/)
2. Click sign in

- **Why:** redirect to Keycloak proves the portal is a relying party, not a local password form.
- **Expect:** browser lands on Keycloak at `http://localhost:8085/realms/meridian/...`, not a portal-hosted login form.

> **Watch out:** Use `localhost`, not `127.0.0.1` — the client’s redirect URIs are `http://localhost:8092/*` (and the container hostname variant).

### Task 2 — Sign in as Helen

Sign in as `helen.ross` / `LabUser1!`.

- **Why:** this round trip (portal → Keycloak → back with a token) is the entire authorization-code + PKCE flow.
- **Expect:** redirected back to `http://localhost:8092/` already authenticated; page reflects Helen’s identity (name, email, or similar).

Save a screenshot under `~/iiq-lab-evidence/sandbox/212/` (no passwords).

### Task 3 — Full sign-out

Sign out fully — not just closing the tab.

- **Why:** portal sign-out should also end the Keycloak session; otherwise a second “sign in” silently reuses Helen’s still-live SSO cookie.
- **Expect:** returning to the portal shows a logged-out state.

### Task 4 — Sign in as Priya (session isolation)

Sign in again as `priya.wire` / `LabUser1!`.

- **Why:** proves the session boundary is real, not a UI illusion or cached view.
- **Expect:** portal shows Priya’s identity, not a stale Helen view.

### Task 5 — Rebuild if PKCE / redirect fails

If you see a PKCE error, redirect-URI mismatch, or blank page after Keycloak redirects back:

```bash
docker compose -f docker-compose.iiq.yml -f docker-compose.enterprise.yml \
  --profile enterprise up -d --force-recreate --build employee-portal
```

- **Why:** known race when Keycloak’s realm import timing beats the portal’s boot — a clean rebuild re-reads current realm state.
- **Expect:** Helen/Priya flow succeeds after recreate.

### Task 6 — Contrast with pass-through (Lesson 206)

Compare what you just proved with Lesson 206’s pass-through login to IIQ.

| App | Mechanism |
| --- | --- |
| IIQ pass-through (206) | Directory bind check |
| Employee Portal (212) | OIDC authorization-code + PKCE via Keycloak |

- **Why:** same goal (“don’t check a local password”), two mechanisms you’ll see again with Gitea in Lesson 213.
- **Expect:** you can name which mechanism each app uses.

### Task 7 — Close with asserts

```bash
./tools/lab/enterprise/verify-lesson.sh 212
```

- **Why:** hard checks catch a down portal or missing IdP realm before you move on.
- **Expect:** PASS for portal `/health` and meridian realm available.

## If it fails

| Symptom | Fix |
| --- | --- |
| `Invalid redirect_uri` after Keycloak login | Access via `localhost`, not `127.0.0.1`; client allows `http://localhost:8092/*` |
| Keycloak login OK, portal blank/error | Check `docker logs mnb-employee-portal`; confirm `KEYCLOAK_INTERNAL_URL=http://host.docker.internal:8085` and `docker exec mnb-employee-portal getent hosts host.docker.internal` |
| Portal health down | `curl -sf http://localhost:8092/health` — restart the container if that fails |
| Priya’s login shows Helen’s data | Incomplete sign-out — clear cookies for `localhost:8092` and `localhost:8085`, then retry |

## You are done when

- [ ] Completed OIDC login as both `helen.ross` and `priya.wire`
- [ ] Full sign-out between them; second login shows different content
- [ ] Can explain why “correlated account” ≠ “can actually log in”
- [ ] `./tools/lab/enterprise/verify-lesson.sh 212` hard asserts PASS

## Control note

- **Control:** SSO acceptance testing — login proof, not correlation alone
- **Owner:** IAM Ops / application owner
- **SLA (lab):** SSO proof required same session before an app is marked “integrated”
- **Evidence:** `~/iiq-lab-evidence/sandbox/212/` — login screenshots for both personas, sign-out proof

## Quick check

1. Which client/flow does the portal use? → `employee-portal`, public + PKCE (`S256`)
2. What proves session isolation? → full sign-out, then a second persona with different content
3. Standard fix for PKCE/redirect race after Keycloak boots? → `--force-recreate --build employee-portal`

## Feedback

Could you redo Helen → sign-out → Priya without notes? If Priya still looked like Helen, note whether you cleared *both* portal and Keycloak cookies — that split session is the usual trap.

## Navigate

- Previous: [Lesson 211](211-keycloak-okta-shaped.md)
- Next: [Lesson 213](213-gitea-sso-app.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
