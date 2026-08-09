# Lesson 213 — Second App: Gitea via OIDC

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~70 minutes  
**Prereq:** Lesson 211 (212 recommended)  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 73 / SSO

> **Why:** Two independent SSO apps prove the IdP — not any one application — is the control plane. Federating software you didn’t write is the integration you’ll actually do at a bank. Examiners want evidence that a second relying party works with the same realm, not a one-off Portal demo.

## What this is

Gitea is a second, structurally different OIDC relying party:

```text
http://localhost:8093/
```

Unlike Employee Portal (purpose-built for this lab), Gitea is a real developer Git server with **Authentication Sources → OAuth2** out of the box — the same pattern you’d use for Jira, Confluence, or a CI system.

It uses the confidential `gitea` client from Lesson 211:

| Setting | Value |
| --- | --- |
| Client ID | `gitea` |
| Client secret | `mnb-gitea-oidc-secret` |
| Redirect URI | `http://localhost:8093/user/oauth2/meridian/callback` |

Portal proved *your* code can do OIDC. Gitea proves the pattern holds for **someone else’s** software you configure — the more common real-world task.

Assume nothing is pre-wired: verify the Keycloak client, bootstrap Gitea admin, add the OAuth2 source with exact fields, then prove SSO + auto-register + private repo.

## Know these

```text
Gitea past Install + API /version
  → Verify Keycloak confidential client `gitea` (secret + redirect)
  → configure-gitea-oidc.sh (admin + printed values)
  → Auth source name exactly `meridian` + host.docker.internal discovery
  → SSO as helen.ross → auto-register
  → Create private repo iam-runbooks (authorization proof)
```

| Idea | Detail |
| --- | --- |
| Local admin | `giteaadmin` / `GiteaAdmin1!` — config-only fallback, never a persona |
| Auth source name | Must be exactly `meridian` — embedded in the callback path |
| Discovery URL host | `host.docker.internal` from inside Gitea — **not** `localhost` |
| Auto-registration | `GITEA__oauth2_client__ENABLE_AUTO_REGISTRATION=true` creates the local user on first SSO |
| Auth vs authz | Login proves authentication; creating a private repo proves authorization |
| Confidential client | Server-side secret (`mnb-gitea-oidc-secret`) — unlike Portal’s public+PKCE client |

```text
Gitea sign-in → "meridian" OAuth2 source
  → Keycloak (confidential client + secret)
  → callback /user/oauth2/meridian/callback
  → auto-register local user → real actions (create repo)
```

- **Wrong way:** Testing “SSO works” by only logging in — a broken role mapping can still let someone authenticate yet fail every real action.  
- **Wrong way:** Pasting `http://localhost:8085/...` as Discovery URL inside Gitea.  
- **Wrong way:** Renaming the auth source away from `meridian` — silent redirect breakage.  
- **Wrong way:** Using `giteaadmin` as the DoD persona proof.

## Intent

- Verify Gitea health and the Keycloak `gitea` client before configuring OAuth2.
- Bootstrap Gitea’s local admin and confirm the API is reachable.
- Add an OAuth2 auth source pointing at the Keycloak `meridian` discovery document.
- Complete SSO as `helen.ross` and confirm auto-registration.
- Create a private repo as Helen to prove authorization, not just authentication.

## Before you start

- [ ] Lesson 211 complete (or you will verify the `gitea` client in Task 2)
- [ ] Gitea reachable: [http://localhost:8093/](http://localhost:8093/)
- [ ] Keycloak admin: [http://localhost:8085/](http://localhost:8085/) — `admin` / `admin`
- [ ] `helen.ross` / `LabUser1!` ready (Keycloak user exists and can log in)
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/213
```

## Do this

### Task 1 — Confirm Gitea is past first-run install

Open [http://localhost:8093/](http://localhost:8093/). If you land on the first-run **Install** page instead of the app:

```bash
docker compose -f docker-compose.iiq.yml -f docker-compose.enterprise.yml \
  --profile enterprise up -d --force-recreate gitea
```

API smoke:

```bash
curl -sf http://localhost:8093/api/v1/version | python3 -m json.tool
```

- **Why:** the image should auto-install via `GITEA__security__INSTALL_LOCK=true`; a stuck install page means that didn’t apply.
- **Expect:** normal Gitea landing / sign-in page; `/api/v1/version` returns JSON.

### Task 2 — Verify the Keycloak `gitea` client (assume nothing)

In Keycloak → realm **`meridian`** → **Clients** → **`gitea`**:

| Check | Expect |
| --- | --- |
| Access type | **Confidential** |
| Client secret | `mnb-gitea-oidc-secret` (or matches what you will paste into Gitea) |
| Valid redirect URI | exactly `http://localhost:8093/user/oauth2/meridian/callback` |
| PKCE | Prefer **not** forcing PKCE on this confidential client — Gitea’s OAuth2 path often breaks with `Missing parameter: code_challenge_method` |

If the client is missing, recreate from Lesson 211 before continuing.

Discovery from the **host** (browser path) for your own sanity:

```bash
curl -sf http://localhost:8085/realms/meridian/.well-known/openid-configuration \
  | python3 -m json.tool | head -n 15
```

Discovery from **inside Gitea** (what the auth source must use):

```bash
docker exec mnb-gitea wget -qO- \
  http://host.docker.internal:8085/realms/meridian/.well-known/openid-configuration \
  | head -c 200; echo
```

- **Why:** Gitea fetches discovery/token URLs from inside its container; host `localhost` there is Gitea itself.
- **Expect:** confidential client correct; in-container discovery returns JSON.

> **Watch out:** Do not paste the browser URL `http://localhost:8085/...` into Discovery URL. Browser redirects still use `localhost:8085`; only the server-side discovery/token calls need `host.docker.internal`.

### Task 3 — Run the OIDC helper script

```bash
./tools/lab/enterprise/configure-gitea-oidc.sh
```

- **Why:** polls `GET /api/v1/version` until the API answers, creates the config-only admin (`giteaadmin` / `GiteaAdmin1!`), and prints the exact OAuth2 values to enter by hand.
- **Expect:** script prints Client ID, Client Secret, and discovery URL.

Save the printed block under evidence.

### Task 4 — Add the OAuth2 authentication source

Log in to Gitea as `giteaadmin` / `GiteaAdmin1!`.

1. **Site Administration → Authentication Sources → Add Authentication Source**
2. Type **OAuth2**
3. Fill in exactly:

| Field | Value |
| --- | --- |
| Authentication Name | `meridian` |
| Provider | OpenID Connect |
| Client ID | `gitea` |
| Client Secret | `mnb-gitea-oidc-secret` |
| Discovery URL | `http://host.docker.internal:8085/realms/meridian/.well-known/openid-configuration` |
| Scopes | `openid profile email` |

4. **Save**
5. Re-open the source and confirm the name is still exactly `meridian`

If an auth source named `meridian` already exists, open it and **verify** every field above — do not create a duplicate with a different name.

- **Why:** the auth source name is embedded in the callback path — renaming it breaks the redirect URI silently.
- **Expect:** source saves without a discovery-document fetch error.

### Task 5 — Confirm the meridian SSO button

1. Log out of `giteaadmin`
2. Open the sign-in page
3. Screenshot the SSO affordance under evidence

- **Why:** confirms the source is live for end users, not just saved in admin config.
- **Expect:** a **meridian** SSO button/link appears alongside (or instead of) local username/password.

### Task 6 — SSO as Helen

1. Click **meridian**
2. Complete Keycloak login as `helen.ross` / `LabUser1!`
3. Confirm you land back in Gitea authenticated as Helen (not `giteaadmin`)
4. Screenshot under evidence

- **Why:** same authorization-code flow as Lesson 212, but the relying party is third-party software you configured.
- **Expect:** redirected through Keycloak and back into Gitea, authenticated as Helen.

### Task 7 — Confirm auto-registration

1. Log out of Helen (or open admin in another profile)
2. As `giteaadmin`: **Site Administration → User Accounts**
3. Find Helen’s local user

- **Why:** auto-registration creates Helen’s local Gitea user on first SSO — no manual provisioning step.
- **Expect:** Helen listed; username sourced from the OIDC claim; no hand-created account required for her.

### Task 8 — Create a private repo (authorization proof)

As Helen (SSO session):

1. Create a new repository
2. Name: `iam-runbooks`
3. Visibility: **Private**
4. Create / initialize as the UI allows
5. Screenshot the repo home under `~/iiq-lab-evidence/sandbox/213/`

- **Why:** proves *authorization* worked, not just *authentication*.
- **Expect:** repo creates successfully under Helen’s account.

### Task 9 — Optional second persona (session isolation)

If time allows: full sign-out → SSO as `priya.wire` → confirm a different Gitea user context (and that Helen’s private repo is not writable as Priya unless shared).

- **Why:** matches Lesson 212’s isolation bar on a second app.
- **Expect:** Priya is a distinct Gitea user after SSO.

### Task 10 — Close with asserts

```bash
./tools/lab/enterprise/verify-lesson.sh 213
```

- **Why:** hard check that Gitea’s API is up before you leave the SSO block.
- **Expect:** PASS for Gitea `/api/v1/version`.

## If it fails

| Symptom | Fix |
| --- | --- |
| `configure-gitea-oidc.sh` times out | SQLite init on a fresh volume can outlast ~120s — check `docker logs mnb-gitea` and retry |
| Could not fetch discovery document / `dial tcp [::1]:8085: connection refused` | Discovery URL still points at `localhost:8085`. Change it to `http://host.docker.internal:8085/realms/meridian/.well-known/openid-configuration`. Confirm with Task 2’s `docker exec … wget`. If that fails too, add `extra_hosts: ["host.docker.internal:host-gateway"]` under `gitea` in compose and recreate |
| Sign-in redirects with `Missing parameter: code_challenge_method` | Keycloak `gitea` client has PKCE enforced. In Keycloak → Clients → `gitea` → Advanced / Capability config, clear **PKCE Code Challenge Method** (leave blank) and save |
| Sign-in redirects with an error | Redirect URI must be exactly `http://localhost:8093/user/oauth2/meridian/callback` — renaming the auth source breaks this |
| Helen logs in but isn’t auto-registered | `docker exec mnb-gitea env \| grep OAUTH2` — recreate from checked-in compose if auto-registration was overridden |
| Private repo create fails | Check Helen’s user type under Site Administration; confirm the app works as `giteaadmin` before debugging her account |
| Confidential client missing | Re-do Lesson 211 `gitea` client before Task 4 |

## You are done when

- [ ] Gitea API up; Keycloak `gitea` client verified (secret + redirect + in-container discovery)
- [ ] OAuth2 source `meridian` saved with `host.docker.internal` discovery
- [ ] Helen signed into Gitea entirely through Keycloak SSO (not local admin)
- [ ] Helen auto-registered on first login
- [ ] Private `iam-runbooks` repo created under her session
- [ ] `./tools/lab/enterprise/verify-lesson.sh 213` hard asserts PASS

## Control note

- **Control:** Third-party application federation — config-only OIDC onboarding of software you don’t own
- **Owner:** IAM Ops / Gitea application owner
- **SLA (lab):** new relying party federated within the same session it’s requested
- **Evidence:** `~/iiq-lab-evidence/sandbox/213/` — client/discovery checks, auth source config screenshot, login proof, `iam-runbooks` repo screenshot

## Quick check

1. Why must the auth source be named exactly `meridian`? → embedded in `/user/oauth2/meridian/callback`  
2. What proves authorization, not just authentication? → Helen creating a private repo after SSO  
3. Why must Discovery URL use `host.docker.internal` instead of `localhost`? → Gitea fetches it from inside the container; `localhost` there is Gitea itself  
4. Portal vs Gitea client type? → Portal public+PKCE; Gitea confidential+secret

## Feedback

Could you re-add the OAuth2 source from the script output without this lesson open — including the in-container discovery check? If discovery failed with `connection refused`, note whether the URL still said `localhost` — that is the usual gotcha.

## Navigate

- Previous: [Lesson 212](212-employee-portal-sso.md)
- Next: [Lesson 214](214-correlation-standard-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
