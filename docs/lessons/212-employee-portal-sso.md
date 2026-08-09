# Lesson 212 — Employee Portal SSO Proof

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~45 minutes  
**Prereq:** Lesson 211  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** DoD #3

> **Why:** A cube full of correlated accounts is not ops proof. Prove access with a real login — provision-then-login is the acceptance test correlation alone can never pass. Examiners ask for evidence that workforce SSO works for named personas, not that an IdP container is “healthy.”

## What this is

Employee Portal (`tools/employee-portal`) is a small OIDC relying-party web app built to be a real login target:

```text
http://localhost:8092/
```

It authenticates against Keycloak’s `meridian` realm using the `employee-portal` public client (PKCE, `S256`) from Lesson 211, and checks that the signed-in user belongs to `portal-users`.

This is Success Criterion #3 from the Enterprise Lab Definition of Done: *User SSO into Employee Portal **and** Gitea via Keycloak.* A correlated account link on a cube is necessary but not sufficient — this lesson is the sufficient part.

Nothing about client config, group membership, or portal health is assumed — you verify each gate, then prove Helen → sign-out → Priya.

## Know these

```text
Portal /health + Keycloak meridian up
  → Verify employee-portal client (public + PKCE + redirect URIs)
  → Verify helen.ross in portal-users (Keycloak Groups)
  → Browser: Portal → Keycloak login → back with token
  → Full sign-out (portal + IdP session)
  → Second persona (priya.wire) → different content
```

| Idea | Detail |
| --- | --- |
| Authorization-code + PKCE | Portal → Keycloak login → back to portal with a token — that round trip *is* the flow |
| Who checks the password | Keycloak — the portal never sees or handles credentials |
| Group gate | `portal-users` — authentication ≠ authorization |
| Session isolation | Sign out fully, then a *second* persona must show different content |
| Redirect host | Use `localhost`, not `127.0.0.1` — client redirect URIs are host-specific |

```text
Browser → Portal (:8092)
       → redirect → Keycloak meridian login
       → code + PKCE → Portal token exchange
       → portal-users check → authenticated UI
```

- **Wrong way:** Concluding “SSO works” after one persona once — you haven’t proven session isolation until a second persona shows different content after a full sign-out.  
- **Wrong way:** Using `127.0.0.1:8092` — `Invalid redirect_uri`.  
- **Wrong way:** Treating Keycloak admin login as Portal proof.  
- **Wrong way:** Assuming `portal-users` membership survived a Keycloak recreate — **verify**.

## Intent

- Verify Portal health, Keycloak realm, client, and group membership before clicking Sign in.
- Complete a real OIDC login as a workforce persona (not just admin).
- Confirm the portal enforces `portal-users`, not “any valid Keycloak login.”
- Sign in as a second persona and prove session isolation.
- Know the rebuild fix for the common local redirect-URI / PKCE failure mode.

## Before you start

- [ ] Lesson 211 complete (or you will verify the client yourself in Task 2)
- [ ] Portal reachable: [http://localhost:8092/](http://localhost:8092/)
- [ ] Keycloak admin: [http://localhost:8085/](http://localhost:8085/) — `admin` / `admin`
- [ ] Credentials ready: `helen.ross` / `LabUser1!`, `priya.wire` / `LabUser1!`
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/212
```

## Do this

### Task 1 — Prove Portal and IdP are answering

```bash
curl -sf http://localhost:8092/health && echo
curl -sf http://localhost:8085/realms/meridian/.well-known/openid-configuration \
  | python3 -m json.tool | head -n 20
```

- **Why:** SSO failures that are really “portal down” or “realm missing” waste hours in the browser.
- **Expect:** Portal health OK; discovery JSON shows `issuer` containing `/realms/meridian`.

### Task 2 — Verify the `employee-portal` client (assume nothing)

In Keycloak Admin → realm **`meridian`** → **Clients** → **`employee-portal`**:

| Check | Expect |
| --- | --- |
| Client type / access | **Public** (no required secret for browser PKCE) |
| PKCE | `S256` / challenge method configured for the portal flow |
| Valid redirect URIs | includes `http://localhost:8092/*` (and container variant if listed) |
| Web origins | allows the portal origin (or `+` per your Lesson 211 setup) |

If the client is missing, recreate it from Lesson 211 (or re-import the realm) before continuing — do not invent a second client id.

- **Why:** wrong client type or redirect URI produces opaque browser errors after an otherwise valid password.
- **Expect:** client matches the public + PKCE + `localhost:8092` contract.

### Task 3 — Verify Helen is authorized (`portal-users`)

Authentication ≠ authorization. Portal checks group membership.

1. Keycloak → **Users** → `helen.ross`
2. Confirm user is **Enabled**
3. **Groups** (or Role/Group mappings) → must include **`portal-users`**
4. Optionally confirm `priya.wire` also has `portal-users` before Task 8

If Helen authenticates to Keycloak but Portal rejects her, this is the usual cause — add the group (or re-run birthright / IdP provision from Lessons 216–217 if that is how your estate populates groups).

- **Why:** a valid password with no `portal-users` is a successful IdP login and a failed app authorization.
- **Expect:** Helen listed in `portal-users` before you claim SSO proof.

### Task 4 — Start the SSO redirect

Open the portal and begin sign-in. You should leave the portal domain entirely.

1. Open [http://localhost:8092/](http://localhost:8092/) — use **`localhost`**, not `127.0.0.1`
2. Click **Sign in** (wording may vary)
3. Watch the address bar

- **Why:** redirect to Keycloak proves the portal is a relying party, not a local password form.
- **Expect:** browser lands on Keycloak at `http://localhost:8085/realms/meridian/...`, not a portal-hosted login form.

> **Watch out:** Use `localhost`, not `127.0.0.1` — the client’s redirect URIs are `http://localhost:8092/*`.

### Task 5 — Sign in as Helen (full OIDC proof)

Sign in as `helen.ross` / `LabUser1!`.

1. Complete Keycloak login
2. Wait for redirect back to `http://localhost:8092/`
3. Confirm the authenticated UI shows Helen’s identity (name, email, or username)
4. Screenshot under `~/iiq-lab-evidence/sandbox/212/` (no passwords)

- **Why:** this round trip (portal → Keycloak → back with a token) is the entire authorization-code + PKCE flow.
- **Expect:** authenticated portal view for Helen — not an error page, blank page, or Keycloak account console.

### Task 6 — Full sign-out (both sessions)

Sign out fully — not just closing the tab.

1. Use Portal **Sign out** / **Log out**
2. Confirm the portal shows a logged-out / sign-in state
3. If a second “Sign in” silently restores Helen without a password prompt, clear cookies for **both**:
   - `localhost:8092`
   - `localhost:8085`
4. Re-open the portal — must require credentials again

- **Why:** portal sign-out should also end the Keycloak SSO session; otherwise Task 7 is a false isolation proof.
- **Expect:** returning to the portal shows a logged-out state; next sign-in prompts for credentials.

### Task 7 — Sign in as Priya (session isolation)

Sign in again as `priya.wire` / `LabUser1!`.

1. Complete the same Portal → Keycloak → Portal path
2. Confirm the UI shows **Priya**, not a stale Helen view
3. Screenshot under evidence

- **Why:** proves the session boundary is real, not a UI illusion or cached view.
- **Expect:** portal shows Priya’s identity; Helen’s data is gone.

### Task 8 — Negative check (optional but strong)

If you have a Keycloak user **without** `portal-users` (or temporarily remove Priya from the group, test, then restore):

1. Attempt Portal SSO
2. Expect denial / unauthorized — not a full Portal home

Restore group membership immediately after.

- **Why:** proves the group gate is enforced, not decorative.
- **Expect:** missing `portal-users` ≠ successful Portal session.

### Task 9 — Rebuild if PKCE / redirect fails

If you see a PKCE error, redirect-URI mismatch, or blank page after Keycloak redirects back:

```bash
docker compose -f docker-compose.iiq.yml -f docker-compose.enterprise.yml \
  --profile enterprise up -d --force-recreate --build employee-portal
```

Then repeat Tasks 4–7.

- **Why:** known race when Keycloak’s realm import timing beats the portal’s boot — a clean rebuild re-reads current realm state.
- **Expect:** Helen/Priya flow succeeds after recreate.

### Task 10 — Contrast with pass-through (Lesson 206)

Compare what you just proved with Lesson 206’s pass-through login to IIQ.

| App | Mechanism |
| --- | --- |
| IIQ pass-through (206) | Directory bind check |
| Employee Portal (212) | OIDC authorization-code + PKCE via Keycloak |

- **Why:** same goal (“don’t check a local password”), two mechanisms you’ll see again with Gitea in Lesson 213.
- **Expect:** you can name which mechanism each app uses.

### Task 11 — Close with asserts

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
| Login OK in Keycloak, Portal says unauthorized | Task 3 — add `portal-users` |
| Portal health down | `curl -sf http://localhost:8092/health` — restart / Task 9 rebuild |
| Priya’s login shows Helen’s data | Incomplete sign-out — clear cookies for `localhost:8092` and `localhost:8085`, then retry |
| Client missing in Keycloak | Re-do Lesson 211 client create / realm import |

## You are done when

- [ ] Portal `/health` and meridian discovery verified
- [ ] `employee-portal` client + Helen `portal-users` verified
- [ ] Completed OIDC login as both `helen.ross` and `priya.wire`
- [ ] Full sign-out between them; second login shows different content
- [ ] Can explain why “correlated account” ≠ “can actually log in”
- [ ] `./tools/lab/enterprise/verify-lesson.sh 212` hard asserts PASS

## Control note

- **Control:** SSO acceptance testing — login proof, not correlation alone
- **Owner:** IAM Ops / application owner
- **SLA (lab):** SSO proof required same session before an app is marked “integrated”
- **Evidence:** `~/iiq-lab-evidence/sandbox/212/` — health/discovery notes, client/group checks, login screenshots for both personas, sign-out proof

## Quick check

1. Which client/flow does the portal use? → `employee-portal`, public + PKCE (`S256`)  
2. What proves session isolation? → full sign-out, then a second persona with different content  
3. Standard fix for PKCE/redirect race after Keycloak boots? → `--force-recreate --build employee-portal`  
4. What group must Helen have for Portal authorization? → `portal-users`

## Feedback

Could you redo Helen → sign-out → Priya without notes, including the client and `portal-users` checks? If Priya still looked like Helen, note whether you cleared *both* portal and Keycloak cookies — that split session is the usual trap.

## Navigate

- Previous: [Lesson 211](211-keycloak-okta-shaped.md)
- Next: [Lesson 213](213-gitea-sso-app.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
