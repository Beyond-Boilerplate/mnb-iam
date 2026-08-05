# Lesson 213 — Second App: Gitea via OIDC

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~60 minutes  
**Prereq:** Lesson 211  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 73 / SSO

> **Why (1–2 lines):** Two independent SSO apps prove the IdP — not any one application — is the real control plane. An examiner wants federation proven against software you didn't write, since that's the integration you'll actually do at a real bank.

## What this is

Gitea is a second, structurally different OIDC relying party: unlike Employee Portal (purpose-built for this lab), Gitea is a real, general-purpose developer Git server that happens to support "Authentication Sources → OAuth2" out of the box — exactly like a real bank would federate an actual internal tool (Jira, Confluence, a CI system) to its workforce IdP. It uses the confidential `gitea` client from Lesson 211 (client secret `mnb-gitea-oidc-secret`, redirect URI `http://localhost:8093/user/oauth2/meridian/callback`). Where Employee Portal only proves *your* code can do OIDC correctly, Gitea proves the pattern holds for **someone else's** software that you configure, not code — the more common real-world integration task.

## Know these

- Local admin `giteaadmin` / `GiteaAdmin1!` is a config-only operator fallback — never used as a persona identity.
- Auth source name must be exactly `meridian` — it's embedded in the callback path (`/user/oauth2/meridian/callback`); renaming the source silently breaks the redirect URI.
- `GITEA__oauth2_client__ENABLE_AUTO_REGISTRATION: "true"` means first SSO login creates Helen's local Gitea user automatically — no manual provisioning step.
- **Wrong way:** Testing "SSO works" by only logging in — creating Helen's private repo afterward is what proves *authorization*, not just authentication; a broken role mapping can still let someone log in yet fail every real action.

## Intent

- Bootstrap Gitea's local admin account (config-only fallback, not for personas) and confirm the API is reachable.
- Add an OAuth2 authentication source pointing at the Keycloak `meridian` realm's discovery document.
- Complete a real SSO login as `helen.ross` and confirm Gitea auto-registers her as a local user on first login.
- Create a private repository as Helen to prove the session carries real authorization, not just a login screen.

## Before you start

- [ ] Lesson 211 complete; `gitea` confidential client confirmed in Keycloak
- [ ] Gitea reachable at `http://localhost:8093/`
- [ ] `helen.ross` / `LabUser1!` credentials ready
- [ ] Evidence dir: `mkdir -p ~/iiq-lab-evidence/sandbox/213`

## Do this

1. Open `http://localhost:8093/`. If you land on the first-run "Install" page instead of the app, force-recreate it: `docker compose -f docker-compose.iiq.yml -f docker-compose.enterprise.yml --profile enterprise up -d --force-recreate gitea`.  
   **Why:** the image should auto-install via `GITEA__security__INSTALL_LOCK=true`; a stuck install page means that didn't apply.  
   **Expect:** normal Gitea landing/sign-in page loads.

2. Run `./tools/lab/enterprise/configure-gitea-oidc.sh`.  
   **Why:** polls `GET /api/v1/version` until Gitea's API answers, creates a local config-only admin (`giteaadmin`/`GiteaAdmin1!`), and prints the exact OAuth2 source values to enter by hand.  
   **Expect:** script prints Client ID, Client Secret, and discovery URL.

3. In Gitea, go to **Site Administration → Authentication Sources → Add Authentication Source**, type **OAuth2**, and fill in exactly what the script printed: Authentication Name `meridian`, Provider OpenID Connect, Client ID `gitea`, Client Secret `mnb-gitea-oidc-secret`, Discovery URL `http://localhost:8085/realms/meridian/.well-known/openid-configuration`, Scopes `openid profile email`.  
   **Why:** the auth source name (`meridian`) is embedded in the callback path itself — renaming it breaks the redirect URI silently.  
   **Expect:** source saves without a discovery-document fetch error.

4. Save, log out of `giteaadmin`, go to the sign-in page.  
   **Why:** confirms the new source is actually live for end users, not just saved in config.  
   **Expect:** a "meridian" SSO button/link appears alongside (or instead of) the local username/password form.

5. Sign in via **meridian** as `helen.ross` / `LabUser1!`.  
   **Why:** same authorization-code flow as Lesson 212, but this time the relying party is real third-party software you configured, not a lab-built app.  
   **Expect:** redirected through Keycloak and back into Gitea, authenticated.

6. Confirm Helen's account appears under **Site Administration → User Accounts** after this first login.  
   **Why:** `GITEA__oauth2_client__ENABLE_AUTO_REGISTRATION: "true"` auto-registers her as a local user, username sourced from the OIDC `userid` claim.  
   **Expect:** Helen listed as a user with no manual provisioning step taken.

7. As Helen, create a private repository named `iam-runbooks`.  
   **Why:** proves *authorization* worked, not just *authentication* — a broken group/role mapping might still let someone log in but fail on real actions.  
   **Expect:** repo creates successfully under Helen's account.

8. If the discovery URL fails to resolve from inside the Gitea container, understand why before working around it: Keycloak's realm `issuer` is fixed to `http://localhost:8085/realms/meridian` (Lesson 211's `--hostname=localhost`), and Gitea's backend — not your browser — has to reach that same host-shaped URL from inside its own container, where `localhost` means "the Gitea container itself."  
   **Expect:** you can state this before applying the workaround in **If it fails**.

## If it fails

- **Gitea API never comes up (`configure-gitea-oidc.sh` times out)** — check `docker logs mnb-gitea`; SQLite init on a fresh volume can outlast the script's default 60 polls × 2s = 120s wait on a slow disk.
- **"Could not fetch discovery document"** — the `localhost` resolution gotcha from step 8. Confirm it first: `docker exec mnb-gitea wget -qO- http://localhost:8085/realms/meridian/.well-known/openid-configuration` should fail with connection refused from inside the container. Work around it by adding `extra_hosts: ["host.docker.internal:host-gateway"]` to the `gitea` service in `docker-compose.enterprise.yml` and using `http://host.docker.internal:8085/realms/meridian/.well-known/openid-configuration` as the discovery URL, then recreate the container.
- **Sign-in via meridian redirects back with an error** — confirm the redirect URI matches exactly `http://localhost:8093/user/oauth2/meridian/callback` (renaming the auth source breaks this silently).
- **Helen logs in but isn't auto-registered** — confirm `GITEA__oauth2_client__ENABLE_AUTO_REGISTRATION` is `true` in the running container (`docker exec mnb-gitea env | grep OAUTH2`); recreate from the checked-in compose file if overridden.
- **Private repo create fails with a permissions error** — Helen's auto-registered account may have a restricted default role; check her user type under Site Administration, or fall back to `giteaadmin` to confirm the app itself works before debugging her account.

## You are done when

Helen has signed into Gitea entirely through Keycloak SSO (not the local admin account), her user was auto-registered on first login, and she has created a private `iam-runbooks` repository under her own session.

## Control note

- **Control:** Third-party application federation — config-only OIDC onboarding of software you don't own.
- **Owner:** IAM Ops / Gitea application owner.
- **SLA (lab):** new relying party federated within the same session it's requested; production target is typically within a sprint.
- **Evidence:** `~/iiq-lab-evidence/sandbox/213/` — auth source config screenshot, login proof, `iam-runbooks` repo screenshot.

## Quick check

1. Why must the auth source be named exactly `meridian`? → it's embedded in the OAuth2 callback path (`/user/oauth2/meridian/callback`).
2. What proves authorization, not just authentication? → Helen successfully creating a private repo after SSO login.
3. Why can't Gitea's backend reach `localhost:8085` for the discovery URL? → `localhost` inside the Gitea container means the Gitea container itself, not the Docker host running Keycloak.

## Navigate

- Previous: Lesson 212
- Next: Lesson 214
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
