# Lesson 100 — IIQ REST & SCIM APIs

**Level:** Intermediate  
**Track:** Plugins, APIs & SSD  
**Time:** 75–90 min  
**Prereq:** Lesson 99 — IIQ Console & Automation  

**Lab data:**
- Toolkit ping from Lesson 98; Meridian identities
- SCIM concepts foreshadow connector catalog Lesson 69
- API register home: binder + `~/iiq-lab-data/api/`

---

## Learning objectives

You will be able to:

- Distinguish **IIQ REST** (product/plugin APIs) from **SCIM** (identity provisioning API surface)
- Call a read API with basic auth or session cookie against lab IIQ using a dedicated API identity
- Create `mnb.api.lab` (not `spadmin`) with least capabilities and prove positive/negative authz
- Map SCIM use cases for HR/ITSM integrations vs plugin REST for UI add-ins
- Document OAuth/TLS, rate-limit, and audit expectations for Meridian API accounts

---

## Why this matters

**Business.** ServiceNow, HR bots, and lab automations should not scrape the UI. When Meridian’s ITSM team asked for “just use helen’s password in the spoke,” IAM refused — correctly. APIs make integrations supportable. A shared `spadmin` basic-auth header is a finding waiting to happen and an incident waiting to be unattributable.

**Control / audit.** API accounts are non-human identities with named owners (`helen.ross`), rotated secrets, scoped capabilities, and SIEM-visible authentication failures (Lesson 104). Examiners ask *"which non-human accounts can read or change identities?"* Your answer is the API register — not a password in a Postman collection on a shared drive.

---

## Concepts

### Three API surfaces — do not conflate them

| Surface | Typical path | Meridian use |
| --- | --- | --- |
| IIQ REST (OOTB) | `/identityiq/rest/...` (confirm in your build) | Identities, launches, product APIs |
| Plugin REST | Registered in plugin `manifest.xml` | `mnb-iam-toolkit` ping |
| SCIM 2.0 | `/identityiq/scim/v2/...` (if module enabled) | External IdM / ITSM account sync |

**SCIM** (System for Cross-domain Identity Management) is an IETF standard for representing users/groups and performing CRUD over HTTP. IIQ’s SCIM module exposes a standards-shaped surface for trusted peers. It does **not** replace Account Aggregation for deep entitlement dictionaries on AD, core banking, or AWS.

### Account design — anti-patterns vs Meridian

| Anti-pattern | Meridian pattern |
| --- | --- |
| `spadmin` in scripts | `mnb.api.lab` / prod `mnb.api.itsm` + capability set |
| HTTP cleartext on shared hosts | TLS only (lab HTTP → document exception) |
| God rights | Read identities + specific launch/SCIM rights only |
| Secrets in git / Postman committed | Vault / K8s / CI secret store; `chmod 600` netrc |

### Integration patterns

| Consumer | API surface | Auth | Notes |
| --- | --- | --- | --- |
| ServiceNow IAM spoke | SCIM or REST requests | OAuth/basic per build | Named `mnb.api.itsm` |
| HR bot (future) | SCIM Users | Cert/OAuth | Do not bypass authoritative aggregation |
| Monitoring | Toolkit ping | Capability | Synthetic check only |
| Custom UI | Plugin REST | Session + right | Lesson 98 |

### Examiner question (API)

*"Which non-human accounts can read Meridian identities, and when was each secret last rotated?"* Answer from the API register — account, owner `helen.ross`, capabilities, secret location, rotated-on date — not from a shared Postman workspace.

---

## How it works

```text
  External system (ITSM / HR bot / monitor)
           │
           │ HTTPS + API identity (OAuth token or basic)
           ▼
  IIQ REST / SCIM / Plugin REST
           │
           ├── Capabilities / scopes gate each call
           ├── Audit events (auth success/fail, changes)
           └── Cube / request updates (if write APIs used)
```

| Concern | Lab practice | Production expectation |
| --- | --- | --- |
| Auth | Basic auth for `mnb.api.lab` | Prefer OAuth2/OIDC client credentials where supported; short-lived tokens |
| Transport | `http://localhost:8080` OK with documented exception | TLS everywhere; no cleartext on shared/homelab URLs |
| Authz | Minimal capabilities | Separate read vs write clients if possible |
| Abuse | Document calls/minute | Rate limits; disable identity + rotate on anomaly |
| Correlation | Optional `X-Request-Id` | Log request IDs into SIEM |

---

## Real-world setup (OAuth, TLS, client registration)

Read this even if lab uses basic auth — examiners assume you know the production shape.

### Step 1 — Decide the consumer and surface

1. ITSM account sync → SCIM Users (if enabled) or documented REST alternative.
2. Synthetic monitor → toolkit ping only.
3. Never give a UI-scraping robot `spadmin`.

### Step 2 — Register a non-human identity

1. Create identity `mnb.api.<purpose>@meridiannb.com` (lab: `mnb.api.lab@meridiannb.com`).
2. Non-interactive: no email approvals; exclude from human certifications (service-account inventory — Lesson 20 patterns).
3. Owner: `helen.ross`; technical contact on the API register.

### Step 3 — Authn material

1. **Lab:** strong password in vault; call via `curl --netrc-file` mode `600`.
2. **Prod:** prefer OAuth2 client credentials (or mutual TLS) per your IIQ/IdP integration; store client secret in vault; rotate on schedule.
3. Never commit Postman environments with secrets.

### Step 4 — Least privilege and monitoring

1. Grant only the capabilities the consumer needs; deny SystemAdministrator.
2. Enable auth success/failure audits (Lesson 104); SIEM alert on repeated 401s.
3. Document expected calls/minute and the disable+rotate response.

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq`
- [ ] `curl` or Postman available
- [ ] Lesson 96 capabilities; Lesson 98 toolkit optional but useful
- [ ] Know whether SCIM module is enabled in your lab WAR
- [ ] Binder page ready: “API account register”

---

## Lab procedure

### Task 1 — Discover API bases

You cannot secure what you cannot name. Record the bases for *this* lab build.

1. Open product docs or lab README for REST/SCIM base URLs for your IIQ version.
2. Record in binder: REST base, SCIM base (if enabled), plugin REST pattern.
3. Prefer HTTPS in any shared/homelab URL (`https://sailpoint.lmsapp.us/identityiq` alternate).

**Expected result:** URL table for this lab environment.

**If it fails:** Use Toolkit ping URL from Lesson 98 as the confirmed custom endpoint; note OOTB paths as “confirm on Compass.”

### Task 2 — Create API identity

`spadmin` in automation is the finding. Build the correct pattern now.

1. As `spadmin`, create identity `mnb.api.lab` (email `mnb.api.lab@meridiannb.com`).
2. Set a strong lab password; store only in local vault.
3. Assign **minimal** capabilities (identity read / SCIM as required) — not SystemAdministrator.
4. Note ownership under `MNB-WG-IAM-Ops` / `helen.ross` as “owned API account.”

**Expected result:** Non-spadmin API identity exists with least privilege.

### Task 3 — Authenticated read call

1. With `curl`, call a safe read endpoint (identity get/list or plugin ping) using `mnb.api.lab`:

```bash
curl --netrc-file ~/.iiq-lab-netrc \
  -H 'Accept: application/json' \
  'http://localhost:8080/identityiq/rest/...'
```

2. Confirm HTTP 200 and JSON/XML body.
3. Redact password from binder; keep status code + endpoint.

**Expected result:** Successful API read with API identity.

**If it fails:** 401 — password/capability; 404 — wrong base path; 403 — add missing right only.

### Task 4 — Negative authz test

1. Use an identity with **no** API rights (e.g. `raj.external`).
2. Repeat the same curl; expect 401/403.
3. Save response code.

**Expected result:** Denied call proves capability gating.

### Task 5 — SCIM probe (if enabled)

1. Attempt `GET` Users on SCIM base with filter `userName eq "helen.ross"` (syntax per SCIM).
2. If SCIM disabled, record “Not enabled in lab WAR” and design-only: which ITSM use cases need SCIM vs connector aggregation.
3. Never run bulk destructive SCIM deletes in shared lab.

**Expected result:** SCIM success **or** explicit lab limitation + design note.

### Task 6 — API register entry

1. Fill register row: Account | Owner (`helen.ross`) | Capabilities | Endpoints used | Secret location | Rotated on | Ticket.
2. Add monitoring expectation: failed logins → SIEM (Lesson 104).
3. Add abuse-response paragraph: expected calls/minute; disable + rotate on anomaly; prefer `X-Request-Id`.

**Expected result:** One completed register row for `mnb.api.lab` with abuse notes.

### Task 7 — Curl hygiene attestation

1. Create `~/.iiq-lab-netrc` mode `600` (never commit).
2. Attest: no passwords in Postman collections committed to git; rotate `mnb.api.lab` after any shared-screen demo.
3. Write one sentence: SCIM does not replace Account Aggregation for entitlement inventory.

**Expected result:** Hygiene attestation in binder.

---

## Acceptance criteria

- [ ] API base URL table documented
- [ ] `mnb.api.lab` (or equivalent) created without SystemAdministrator
- [ ] Successful authenticated read
- [ ] Failed call with unprivileged user evidenced
- [ ] SCIM probed or waiver written
- [ ] API register row + abuse/hygiene notes completed

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| 401 always | Basic auth disabled / wrong realm | Check web.xml / SSO; try session cookie login flow |
| HTML login page returned | Hit UI URL not REST | Use REST/SCIM path |
| 403 on SCIM | Module/capability missing | Enable SCIM; grant SCIM rights |
| Password in shell history | `curl -u` on shared host | Use `--netrc-file` mode 600; rotate |
| Plugin ping works, OOTB REST fails | Different auth filter | Compare plugin vs OOTB security constraints |

---

## Training binder evidence

- URL table
- API identity capability screenshot
- curl status codes (success + deny)
- API register row + abuse notes
- Hygiene attestation

---

## Knowledge check

1. Why must integrations avoid `spadmin`?
2. What is the difference between plugin REST and SCIM?
3. Who owns the Meridian API account register?
4. What TLS rule applies outside pure local lab?
5. What negative test proves API authz?
6. Why does SCIM not replace Account Aggregation for AD entitlements?

### Answers

1. Shared break-glass credentials, over-privilege, non-attributable automation.
2. Plugin REST = custom extension endpoints; SCIM = standard identity provisioning API.
3. IAM lead / `helen.ross` (control owner) with AppSec review.
4. HTTPS only for shared/homelab/prod; document HTTP-only local exceptions.
5. Same endpoint with an unprivileged identity returns 401/403.
6. SCIM exposes online identity CRUD; deep entitlement dictionaries still come from connectors/aggregation.

---

## Further reading

- [RFC 7644 — SCIM Protocol](https://www.rfc-editor.org/rfc/rfc7644) — the protocol surface ITSM peers expect.
- [RFC 7643 — SCIM Core Schema](https://www.rfc-editor.org/rfc/rfc7643) — User/Group resource shapes.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “SCIM” and “REST API” for your version’s base paths and auth options.
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/) — broken authz, excessive data exposure, and lack of rate limiting.
- [NIST SP 800-63B](https://pages.nist.gov/800-63-3/sp800-63b.html) — authenticator management for non-human and OAuth-style clients.
- [OAuth 2.0 RFC 6749](https://www.rfc-editor.org/rfc/rfc6749) — client credentials pattern for service-to-service calls.

---

## Stretch lab

Document an ITSM “create access request” API sequence using IdentityRequest resources (version-specific); include an idempotency key header design and map errors to Problem+JSON-style operator runbook notes.

---

## Summary

- Prefer dedicated API identities with least privilege over `spadmin`.
- Separate OOTB REST, plugin REST, and SCIM in integration design — SCIM ≠ entitlement aggregation.
- Register, rotate, TLS-protect, and SIEM-monitor every non-human account.

---

**Previous:** [Lesson 99 — IIQ Console & Automation](99-iiq-console-and-automation.md)  
**Next:** [Lesson 101 — SSB/SSD Promotion Discipline](101-ssb-ssd-promotion-discipline.md)
