# Lesson 211 — Keycloak as Workforce IdP

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~70 minutes  
**Prereq:** Lesson 201 (Keycloak up); Lesson 207 helpful if you already have Warehouse cubes  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 73

> **Why:** Meridian’s apps should not each keep their own password database. One workforce IdP (Okta-class) owns login; wrong public-vs-confidential client choices are silent SSO failures waiting for production.

## What this is

Keycloak (`quay.io/keycloak/keycloak:24.0`) is this estate’s **Okta-shaped** workforce **identity provider (IdP)** — the login authority a bank would give Okta or Microsoft Entra ID.

In this lab it:

- Owns passwords and MFA-shaped login for workforce personas
- Issues OIDC tokens so Employee Portal and Gitea can trust “Helen is Helen” without storing her password
- Boots with the `meridian` realm pre-imported from `lab-data/enterprise/keycloak/meridian-realm.json`

`MNB-Okta` is the IIQ Application aimed at this realm. SCIM aggregation against Keycloak is a stretch for later — **this lesson certifies the OIDC/SSO surface**, not a full Okta connector deep-dive.

## Concept primer — auth vocabulary you need before clicking

If any term below is fuzzy, stop and read it. Lessons 212–213 *use* these ideas; they do not re-teach them.

### Authentication vs authorization

| Term | Plain English | Meridian example |
| --- | --- | --- |
| **Authentication** (authn) | Proving *who you are* | Helen types `LabUser1!` at Keycloak |
| **Authorization** (authz) | Deciding *what you’re allowed to do* | Portal checks she is in `portal-users` before showing the app |

A login that succeeds at Keycloak can still fail at the app if group membership is wrong. That is authz failing after authn succeeded — not “SSO is broken.”

### IdP, SSO, relying party

| Term | Plain English | In this estate |
| --- | --- | --- |
| **IdP** (identity provider) | The system that authenticates people and asserts identity to apps | Keycloak (`meridian` realm) |
| **SSO** (single sign-on) | Sign in once at the IdP; many apps accept that proof | Portal + Gitea both trust Keycloak |
| **Relying party** / **client** | An app that *trusts* the IdP instead of checking passwords itself | Employee Portal, Gitea, (later) Wire Portal |
| **Workforce IdP** | IdP for employees/contractors — not customer banking login | Keycloak here; Okta/Entra in production |

```text
Helen’s browser
    │  1. opens app (Portal / Gitea)
    ▼
Relying party (client)
    │  2. “I don’t know her password — send her to the IdP”
    ▼
Keycloak (IdP)  ← Helen authenticates here
    │  3. “She’s Helen; here’s a short-lived proof (code/token)”
    ▼
Relying party trusts the proof → session in the app
```

**Wrong way:** Putting Helen’s password in Portal or Gitea config. SSO exists so apps never see workforce passwords.

### OAuth 2.0 vs OpenID Connect (OIDC)

| Term | What it is |
| --- | --- |
| **OAuth 2.0** | A *delegation* framework: “App A may act on behalf of a user / service for specific scopes.” It does **not** by itself define how you log a human in. |
| **OpenID Connect (OIDC)** | A thin identity layer **on top of OAuth 2.0**. Adds ID tokens and a standard “who is this user?” flow apps use for login. |

When this lesson says “OIDC client,” it means: Keycloak client whose `protocol` is `openid-connect` — the pattern Portal and Gitea use for SSO.

> **Tip:** People say “OAuth login” casually. For workforce SSO you almost always mean **OIDC** (identity), not raw OAuth alone (API access).

### Realm

A **realm** is an isolated tenancy inside Keycloak: its own users, groups, clients, and login pages.

| Realm | Job |
| --- | --- |
| `master` | Keycloak’s *own* admin realm — where you log in as `admin` to configure the server |
| `meridian` | Meridian’s workforce tenancy — personas, Portal/Gitea clients, groups |

Portal and Gitea authenticate against **`meridian`**, never `master`. Mixing them up is a common first-day mistake.

### Client types: public vs confidential

Every app that talks OIDC registers as a **client**. The security question is: *can this app keep a secret?*

| Client type | Can it hide a secret? | Typical app | How it proves itself |
| --- | --- | --- | --- |
| **Public** | No — code runs in a browser the user controls | SPA / browser app (`employee-portal`) | **PKCE** (below) — no client secret |
| **Confidential** | Yes — secret lives on a server you control | Server-side app (`gitea`), M2M (`iiq-scim`) | Client ID **+** client secret (PKCE optional — Gitea does not send it) |

```text
Browser / SPA     →  public client  + PKCE
Server web app    →  confidential   + secret (+ often PKCE)
IIQ / automation  →  confidential   + service account (no human browser flow)
```

**Wrong way:** Marking `employee-portal` confidential and pasting a secret into frontend JavaScript. Anyone can open DevTools and steal it — that “secret” was never secret.

### PKCE and S256

**PKCE** (Proof Key for Code Exchange, pronounced “pixie”) stops a common attack on the authorization-code flow in public clients:

1. App creates a random **code verifier** and a derived **code challenge**
2. Browser is redirected to the IdP with the challenge
3. After login, the IdP returns an authorization **code**
4. App redeems the code *and* the original verifier at the token endpoint

An attacker who steals only the code cannot redeem it without the verifier.

**S256** means the challenge is a SHA-256 hash of the verifier (the modern required method). When Keycloak says PKCE requires `S256`, that is what you want.

### Authorization code flow (“Standard flow”)

The usual browser SSO dance:

1. App redirects Helen’s browser to the IdP **authorization endpoint**
2. Helen signs in (and consents if asked)
3. IdP redirects back to the app’s **redirect URI** with a short-lived **authorization code**
4. App’s backend (or PKCE-capable frontend) exchanges the code at the **token endpoint** for tokens

In Keycloak’s UI this is **Standard flow** = ON. Turn it off only for pure machine clients that never involve a browser.

### Redirect URI

The **redirect URI** is the exact URL the IdP is allowed to send Helen back to after login. It is an allow-list security control:

- Too loose (`*` everywhere) → open redirect / token theft risk
- Too strict / typo → `Invalid redirect_uri` and a “broken SSO” ticket that is really a config mismatch

Gitea’s callback embeds the auth-source name:

```text
http://localhost:8093/user/oauth2/meridian/callback
                              └──── source name must match
```

### Discovery document, issuer, JWKS

OIDC clients should not hardcode every endpoint. They fetch a **discovery document**:

```text
http://localhost:8085/realms/meridian/.well-known/openid-configuration
```

| Field | Meaning |
| --- | --- |
| `issuer` | Canonical IdP identity string — tokens must match this |
| `authorization_endpoint` | Where the browser is sent to log in |
| `token_endpoint` | Where the app exchanges the code for tokens |
| `jwks_uri` | Where the app fetches public keys to **verify** token signatures |
| `userinfo_endpoint` | Optional “give me profile claims” API |

**JWKS** = JSON Web Key Set — the IdP’s public keys. Apps verify signatures locally; they do not “trust the token because it arrived over HTTPS” alone.

> **Watch out:** `issuer` is often `http://localhost:8085/realms/meridian`. Inside another Docker container, `localhost` means *that* container — not Keycloak. Portal uses `host.docker.internal` for backend calls; Gitea hits the same class of bug in Lesson 213.

### Tokens (just enough)

You will not decode JWTs in this lesson, but you need the names:

| Token | Job |
| --- | --- |
| **ID token** | OIDC proof of *who* logged in (for the relying party) |
| **Access token** | OAuth credential to call APIs (scopes) |
| **Refresh token** | Long-lived way to get new access tokens without re-prompting the user (if issued) |

Never paste tokens into tickets or screenshots.

### Groups, claims, and correlation

| Idea | Detail |
| --- | --- |
| **Groups** | Collections in the IdP used for coarse authorization (`portal-users`, `wire-initiators`) |
| **Attribute / claim** | Extra fields on the user (e.g. `employeeId=MNB00001`) that apps or IIQ can consume |
| **Correlation** | Matching an IdP/account attribute to an IIQ identity — here `employeeId` ↔ cube `userId` (same pattern as LDAP `employeeNumber`) |

### Service accounts (machine-to-machine)

A **service account** is a non-human identity attached to a confidential client. No browser, no Helen — IIQ (or a script) authenticates as the client to call admin/SCIM APIs.

`iiq-scim` is that pattern: confidential, service accounts on, standard/browser flow off.

### SCIM (why `MNB-Okta` exists)

**SCIM** (System for Cross-domain Identity Management) is a standard REST API for creating/updating users and groups in a directory/IdP. IIQ can provision *into* Okta-class systems over SCIM.

In this lesson: know that `MNB-Okta` is the IIQ Application for that path. Do **not** burn time on Test Connection failures — OIDC discovery is the pass criteria today.

## Know these (quick reference)

| Seeded client | Type | Pattern |
| --- | --- | --- |
| `employee-portal` | Public + PKCE (`S256`) | Browser / SPA — no secret |
| `wire-portal` | Public + PKCE | Same pattern |
| `gitea` | Confidential + secret (no PKCE) | Server-side app — Gitea’s OIDC client does not send PKCE |
| `iiq-scim` | Confidential + service account | Machine-to-machine |

Seeded users: `helen.ross`, `priya.wire`, `marcus.approve` — password `LabUser1!`.

Groups: `mnb-employees`, `mnb-managers`, `wire-initiators`, `wire-approvers`, `portal-users`.

## Intent

- Define IdP, SSO, OIDC, public vs confidential, PKCE, and discovery in your own words.
- Navigate the Keycloak admin console: realm, users, groups, clients.
- Confirm personas, `employeeId`, and group memberships that later lessons depend on.
- Fetch the discovery document and point to `issuer`, `authorization_endpoint`, `token_endpoint`, `jwks_uri`.
- Explain why `employee-portal` is public+PKCE and `gitea` / `iiq-scim` are confidential.

## Before you start

- [ ] Lesson 201 stack up; Keycloak healthy
- [ ] Admin console: [http://localhost:8085/admin/](http://localhost:8085/admin/)
- [ ] `curl` + `python3` available
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/211
```

## Do this

### Task 1 — Open the meridian realm (not master)

You are about to configure workforce SSO. That config lives in a **realm** — an isolated tenancy. Logging into Keycloak as admin lands you in `master` first; workforce apps do not.

1. Open [http://localhost:8085/admin/](http://localhost:8085/admin/)
2. Log in `admin` / `admin`
3. Switch the realm selector (top-left) to **meridian**

- **Why:** `master` is Keycloak’s own admin realm. Portal and Gitea authenticate against `meridian`.
- **Expect:** realm selector shows `meridian` active.

> **Watch out:** If you create a client or user while still on `master`, Lessons 212–213 will look “broken” even though Keycloak is healthy.

### Task 2 — Confirm seeded personas and employeeId

These users are the people the IdP can **authenticate**. IIQ will later **correlate** them using a stable HR id — not their login name.

Under **Users**, open `helen.ross`, `priya.wire`, and `marcus.approve`.

1. Confirm each is **Enabled**
2. Confirm credential `LabUser1!` (non-temporary)
3. Open Helen’s **Attributes** tab

- **Why:** `employeeId = MNB00001` is the correlation key (same story as LDAP `employeeNumber` → identity `userId`). Login name can change; employment id should not.
- **Expect:** Helen’s `employeeId` is exactly `MNB00001`.

### Task 3 — Confirm groups (authorization, not authentication)

Groups answer *what can she do after she proves who she is?* Missing `portal-users` means Keycloak login can succeed while Portal still rejects her.

Under **Groups**, confirm five groups exist, then check memberships:

| Persona | Groups |
| --- | --- |
| `helen.ross` | `mnb-employees`, `mnb-managers`, `portal-users` |
| `priya.wire` | `wire-initiators`, `portal-users` |
| `marcus.approve` | `wire-approvers`, `portal-users` |

- **Why:** Lesson 212’s Portal checks `portal-users`. Wire lessons care about `wire-initiators` / `wire-approvers` for dual-control stories.
- **Expect:** memberships match the table.

### Task 4 — Inspect the public portal client (PKCE)

This is the **public client** pattern: the app runs where users can see its code, so it must not rely on a client secret.

Under **Clients**, open `employee-portal` and confirm:

| Setting | Expected |
| --- | --- |
| Public client | ON |
| Standard flow | ON (authorization code / browser SSO) |
| PKCE | Requires `S256` |
| Client secret | Not used as the trust anchor (public) |

- **Why:** PKCE replaces “shared secret in the browser” with a per-login verifier/challenge. `S256` is the hash method for that challenge.
- **Expect:** public + Standard flow + PKCE `S256` — not confidential.

> **Tip:** “Standard flow” *is* the authorization-code flow. If it is off, browser SSO for this client cannot work.

### Task 5 — Inspect the confidential Gitea client

Gitea is a **server-side** app. It *can* store a secret on the server, so Keycloak treats it as **confidential**.

Open `gitea` and confirm:

| Setting | Expected |
| --- | --- |
| Public client | OFF (confidential) |
| Client secret | `mnb-gitea-oidc-secret` |
| PKCE Code Challenge Method | blank (not required) |
| Valid redirect URI | `http://localhost:8093/user/oauth2/meridian/callback` |

- **Why:** confidential clients authenticate with ID + secret at the token endpoint. Gitea’s built-in OIDC client does **not** send PKCE (`code_challenge`); enforcing S256 on this client breaks Lesson 213 with `Missing parameter: code_challenge_method`. The redirect URI allow-list stops the IdP from sending codes to an attacker-controlled URL. The path segment `meridian` must match the auth-source name you will type in Lesson 213.
- **Expect:** settings match; you can explain *why* this differs from `employee-portal`.

### Task 6 — Inspect the machine-to-machine client

Humans are not the only callers. IIQ (or automation) needs a **service account** — no browser, no Helen.

Open `iiq-scim` and confirm:

| Setting | Expected |
| --- | --- |
| Confidential | Yes |
| Service Accounts Enabled | ON |
| Standard / browser flow | OFF |

- **Why:** this is client-credentials-style access for SCIM/admin APIs. Turning Standard flow on here would imply a human login path that should not exist for this client.
- **Expect:** service account on; no browser SSO flow.

### Task 7 — Side-by-side: name the trust model on each client

Re-open the three clients and say aloud (or note in evidence) which trust model each uses — before you leave the Clients screen.

| App / client | Trust model you should see |
| --- | --- |
| `employee-portal` | Public + PKCE (`S256`) — browser cannot keep a secret |
| `gitea` | Confidential + client secret (no PKCE) — server can keep a secret; Gitea OIDC omits PKCE |
| `iiq-scim` | Confidential + service account — machine-to-machine, no browser flow |

- **Why:** this is the production review question IdP owners ask before every new client goes live. If you can only recite settings but not *why*, the next misconfigured SPA will ship with a leaked secret.
- **Expect:** you can justify each row without looking at the primer.

### Task 8 — Fetch and read the OIDC discovery document

Relying parties should discover endpoints from one document instead of hardcoding fragile URLs.

```bash
curl -s http://localhost:8085/realms/meridian/.well-known/openid-configuration \
  | python3 -m json.tool | tee ~/iiq-lab-evidence/sandbox/211/oidc-discovery.json | head -40
```

In the JSON, locate and note:

1. `issuer`
2. `authorization_endpoint`
3. `token_endpoint`
4. `jwks_uri`

- **Why:** Portal/Gitea use these to start login, redeem codes, and verify token signatures. If `issuer` or discovery is wrong, SSO fails in confusing ways.
- **Expect:** all four present; `issuer` is `http://localhost:8085/realms/meridian`.

> **Watch out:** Host curl uses `localhost:8085`. From inside another container, `localhost` is that container — not Keycloak. Remember this for Lesson 213.

Optional — print just the four fields:

```bash
python3 - <<'PY'
import json
from pathlib import Path
d = json.loads(Path.home().joinpath("iiq-lab-evidence/sandbox/211/oidc-discovery.json").read_text())
for k in ("issuer", "authorization_endpoint", "token_endpoint", "jwks_uri"):
    print(f"{k}: {d.get(k)}")
PY
```

### Task 9 — Glance at MNB-Okta in IIQ (do not deep-debug SCIM)

Open IIQ → **Applications → Application Definition → MNB-Okta**.

- **Why:** connects this IdP lesson to IIQ’s Okta-shaped Application object. SCIM Test Connection may fail without an admin token wired — that is expected today.
- **Expect:** Application exists. You move on after noting it; discovery (Task 8) is the certification bar.

### Task 10 — Close with asserts

```bash
./tools/lab/enterprise/verify-lesson.sh 211
```

- **Why:** hard checks catch a down realm or missing `MNB-Okta` before you start Portal SSO.
- **Expect:** PASS for meridian realm up and `MNB-Okta` exists.

## If it fails

| Symptom | Fix |
| --- | --- |
| Admin console won’t load | Wait for `docker logs mnb-keycloak` to show `Imported realm meridian` (healthcheck has a long start period) |
| Console redirects to HTTPS / refuses HTTP | `docker compose -f docker-compose.iiq.yml -f docker-compose.enterprise.yml --profile enterprise up -d keycloak-http-relax` |
| Created users/clients but Portal can’t see them | You were probably on realm `master` — switch to `meridian` and re-check |
| `MNB-Okta` Test Connection fails / times out | Expected for this lesson — certify discovery (Task 8), don’t burn time on SCIM |
| Persona missing or no password | Tear down the Keycloak volume and re-run `./tools/lab/docker/up.sh --enterprise` to re-import the realm JSON |
| Discovery `curl` hangs | Use `localhost:8085`, not `keycloak:8080` (internal Docker DNS only) |

## You are done when

- [ ] You can explain authn vs authz, IdP vs relying party, and OIDC vs “just OAuth” in one sentence each
- [ ] Logged into Keycloak admin for the `meridian` realm
- [ ] Confirmed personas, `employeeId`, and group memberships
- [ ] Contrasted public+PKCE vs confidential vs M2M clients on real objects
- [ ] Saved discovery JSON and can point to `issuer`, `authorization_endpoint`, `token_endpoint`, `jwks_uri`
- [ ] `./tools/lab/enterprise/verify-lesson.sh 211` hard asserts PASS

## Control note

- **Control:** Workforce IdP configuration integrity — client trust model matches app risk profile
- **Owner:** IAM Ops / IdP team
- **SLA (lab):** any new client’s public-vs-confidential choice reviewed before go-live
- **Evidence:** `~/iiq-lab-evidence/sandbox/211/` — discovery JSON, client config screenshots for all four clients

## Quick check

1. What is the difference between authentication and authorization? → authn = who you are; authz = what you’re allowed to do
2. Why is `employee-portal` public+PKCE instead of confidential? → browser/SPA has nowhere safe to keep a client secret; PKCE replaces it
3. What does the authorization-code (Standard) flow give the app before tokens? → a short-lived authorization code, redeemed at the token endpoint
4. Which discovery fields must a relying party resolve? → at least `issuer`, `authorization_endpoint`, `token_endpoint`, `jwks_uri`
5. Which attribute does Keycloak carry for IIQ correlation? → `employeeId`
6. Why can’t another container reach Keycloak at `localhost:8085` by default? → `localhost` inside that container is itself, not the Docker host

## Feedback

Could you teach a teammate public vs confidential vs PKCE without opening this page? If something was still fuzzy (OIDC vs OAuth, redirect URI, JWKS, service accounts), note the term and which task you were on — that is the signal for the next edit of this lesson.

## Navigate

- Previous: [Lesson 210](210-crm-scim.md)
- Next: [Lesson 212](212-employee-portal-sso.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
