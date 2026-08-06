# Lesson 213 — Second App: Gitea via OIDC

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~60 minutes  
**Prereq:** Lesson 211 (212 recommended)  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 73 / SSO

> **Why:** Two independent SSO apps prove the IdP — not any one application — is the control plane. Federating software you didn’t write is the integration you’ll actually do at a bank.

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

## Know these

| Idea | Detail |
| --- | --- |
| Local admin | `giteaadmin` / `GiteaAdmin1!` — config-only fallback, never a persona |
| Auth source name | Must be exactly `meridian` — embedded in the callback path |
| Auto-registration | `GITEA__oauth2_client__ENABLE_AUTO_REGISTRATION=true` creates the local user on first SSO |
| Auth vs authz | Login proves authentication; creating a private repo proves authorization |

```text
Gitea sign-in → "meridian" OAuth2 source
  → Keycloak (confidential client + secret)
  → callback /user/oauth2/meridian/callback
  → auto-register local user → real actions (create repo)
```

- **Wrong way:** Testing “SSO works” by only logging in — a broken role mapping can still let someone authenticate yet fail every real action.

## Intent

- Bootstrap Gitea’s local admin and confirm the API is reachable.
- Add an OAuth2 auth source pointing at the Keycloak `meridian` discovery document.
- Complete SSO as `helen.ross` and confirm auto-registration.
- Create a private repo as Helen to prove authorization, not just authentication.

## Before you start

- [ ] Lesson 211 complete; `gitea` confidential client confirmed in Keycloak
- [ ] Gitea reachable: [http://localhost:8093/](http://localhost:8093/)
- [ ] `helen.ross` / `LabUser1!` ready
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

- **Why:** the image should auto-install via `GITEA__security__INSTALL_LOCK=true`; a stuck install page means that didn’t apply.
- **Expect:** normal Gitea landing / sign-in page.

### Task 2 — Run the OIDC helper script

```bash
./tools/lab/enterprise/configure-gitea-oidc.sh
```

- **Why:** polls `GET /api/v1/version` until the API answers, creates the config-only admin (`giteaadmin` / `GiteaAdmin1!`), and prints the exact OAuth2 values to enter by hand.
- **Expect:** script prints Client ID, Client Secret, and discovery URL.

### Task 3 — Add the OAuth2 authentication source

In Gitea (as `giteaadmin`):

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

- **Why:** the auth source name is embedded in the callback path — renaming it breaks the redirect URI silently. Gitea fetches discovery **from inside its container**, so use `host.docker.internal` (not `localhost`) — `localhost:8085` inside Gitea is Gitea itself.
- **Expect:** source saves without a discovery-document fetch error.

> **Watch out:** Do not paste the browser URL `http://localhost:8085/...` into Discovery URL. Browser redirects still use `localhost:8085`; only the server-side discovery/token calls need `host.docker.internal`.

### Task 4 — Confirm the meridian SSO button

Save, log out of `giteaadmin`, open the sign-in page.

- **Why:** confirms the source is live for end users, not just saved in admin config.
- **Expect:** a **meridian** SSO button/link appears alongside (or instead of) local username/password.

### Task 5 — SSO as Helen

Sign in via **meridian** as `helen.ross` / `LabUser1!`.

- **Why:** same authorization-code flow as Lesson 212, but the relying party is third-party software you configured.
- **Expect:** redirected through Keycloak and back into Gitea, authenticated as Helen.

### Task 6 — Confirm auto-registration

As admin (or via UI), open **Site Administration → User Accounts**.

- **Why:** auto-registration creates Helen’s local Gitea user on first SSO — no manual provisioning step.
- **Expect:** Helen listed; username sourced from the OIDC claim; no hand-created account.

### Task 7 — Create a private repo (authorization proof)

As Helen, create a private repository named `iam-runbooks`.

- **Why:** proves *authorization* worked, not just *authentication*.
- **Expect:** repo creates successfully under Helen’s account.

Save a screenshot under `~/iiq-lab-evidence/sandbox/213/`.

### Task 8 — Close with asserts

```bash
./tools/lab/enterprise/verify-lesson.sh 213
```

- **Why:** hard check that Gitea’s API is up before you leave the SSO block.
- **Expect:** PASS for Gitea `/api/v1/version`.

## If it fails

| Symptom | Fix |
| --- | --- |
| `configure-gitea-oidc.sh` times out | SQLite init on a fresh volume can outlast ~120s — check `docker logs mnb-gitea` and retry |
| Could not fetch discovery document / `dial tcp [::1]:8085: connection refused` | Discovery URL still points at `localhost:8085`. Change it to `http://host.docker.internal:8085/realms/meridian/.well-known/openid-configuration`. Confirm with `docker exec mnb-gitea wget -qO- http://host.docker.internal:8085/realms/meridian/.well-known/openid-configuration` (expect JSON). If that fails too, add `extra_hosts: ["host.docker.internal:host-gateway"]` under `gitea` in compose and recreate |
| Sign-in redirects with `Missing parameter: code_challenge_method` | Keycloak `gitea` client has PKCE enforced. In Keycloak → Clients → `gitea` → Advanced / Capability config, clear **PKCE Code Challenge Method** (leave blank) and save |
| Sign-in redirects with an error | Redirect URI must be exactly `http://localhost:8093/user/oauth2/meridian/callback` — renaming the auth source breaks this |
| Helen logs in but isn’t auto-registered | `docker exec mnb-gitea env \| grep OAUTH2` — recreate from checked-in compose if auto-registration was overridden |
| Private repo create fails | Check Helen’s user type under Site Administration; confirm the app works as `giteaadmin` before debugging her account |

## You are done when

- [ ] Helen signed into Gitea entirely through Keycloak SSO (not local admin)
- [ ] Helen auto-registered on first login
- [ ] Private `iam-runbooks` repo created under her session
- [ ] `./tools/lab/enterprise/verify-lesson.sh 213` hard asserts PASS

## Control note

- **Control:** Third-party application federation — config-only OIDC onboarding of software you don’t own
- **Owner:** IAM Ops / Gitea application owner
- **SLA (lab):** new relying party federated within the same session it’s requested
- **Evidence:** `~/iiq-lab-evidence/sandbox/213/` — auth source config screenshot, login proof, `iam-runbooks` repo screenshot

## Quick check

1. Why must the auth source be named exactly `meridian`? → embedded in `/user/oauth2/meridian/callback`
2. What proves authorization, not just authentication? → Helen creating a private repo after SSO
3. Why must Discovery URL use `host.docker.internal` instead of `localhost`? → Gitea fetches it from inside the container; `localhost` there is Gitea itself

## Feedback

Could you re-add the OAuth2 source from the script output without this lesson open? If discovery failed with `connection refused`, note whether the URL still said `localhost` — that is the usual gotcha.

## Navigate

- Previous: [Lesson 212](212-employee-portal-sso.md)
- Next: [Lesson 214](214-correlation-standard-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
