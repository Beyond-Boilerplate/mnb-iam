# Lesson 100 — IIQ REST & SCIM APIs

| Field | Value |
| --- | --- |
| **Level** | Intermediate |
| **Track** | Plugins, APIs & SSD |
| **Time** | 60–90 minutes |
| **Prereq** | [Lesson 99 — IIQ Console & Automation](99-iiq-console-and-automation.md) |
| **Lab data** | Toolkit ping from Lesson 98; Meridian identities; SCIM connector notes from catalog Lesson 69 (concepts) |

## Learning objectives

You will be able to:

- Distinguish **IIQ REST** (product/plugin APIs) from **SCIM** (identity provisioning API surface)
- Call a read API with basic auth or session cookie against lab IIQ
- Create a dedicated API identity (not `spadmin`) with least capabilities
- Map SCIM use cases for HR/ITSM integrations vs plugin REST for UI add-ins
- Document rate-limit, TLS, and audit expectations for Meridian

## Why this matters

ServiceNow, HR bots, and lab automations should not scrape the UI. APIs make integrations supportable—but a shared `spadmin` basic-auth header is a finding waiting to happen.

**Control / audit:** API accounts are non-human identities with named owners, rotated secrets, scoped capabilities, and SIEM-visible authentication failures (Lesson 104).

## Concepts

| Surface | Typical path | Meridian use |
| --- | --- | --- |
| IIQ REST (OOTB) | `/identityiq/rest/...` or documented SCIM/REST bases per version | Identities, launches, plugin resources |
| Plugin REST | Registered in plugin `manifest.xml` | `mnb-iam-toolkit` ping |
| SCIM 2.0 | `/identityiq/scim/v2/...` (confirm in your build) | External IdM / ITSM account sync |

```text
  External system (ITSM / HR bot)
           |
           | HTTPS + API identity
           v
  IIQ REST / SCIM  --->  Capabilities / scopes
           |
           +-- Audit events
           +-- Provisioning / cube updates
```

**Account design**

| Anti-pattern | Meridian pattern |
| --- | --- |
| `spadmin` in scripts | `mnb.api.itsm` identity + capability set |
| HTTP cleartext | TLS only (lab may be HTTP—document exception) |
| God rights | Read identities + specific launch rights only |
| Secrets in git | Vault / K8s secret / CI secret store |

**Personas:** Use `helen.ross` as control owner for API account inventory; technical account is non-interactive.

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq`
- [ ] `curl` or Postman available
- [ ] Lesson 96 capabilities; Lesson 98 toolkit optional
- [ ] Know whether SCIM module is enabled in your lab WAR
- [ ] Binder page: “API account register”

## Lab procedure

### Task 1 — Discover API bases

1. Open product docs or lab README for REST/SCIM base URLs for your IIQ version.
2. Record in binder:
   - REST base
   - SCIM base (if enabled)
   - Plugin REST pattern
3. Prefer HTTPS in any shared/homelab URL (`https://sailpoint.lmsapp.us/identityiq` alternate).

**Expected result:** URL table for this lab environment.

**If it fails:** Use Toolkit ping URL from Lesson 98 as the only confirmed custom endpoint and note OOTB paths as “confirm on Compass.”

### Task 2 — Create API identity

1. As `spadmin`, create identity `mnb.api.lab` (email `mnb.api.lab@meridiannb.com`).
2. Set a strong lab password; store only in local vault.
3. Assign **minimal** capabilities (identity read / SCIM as required)—not SystemAdministrator.
4. Add to workgroup `MNB-WG-IAM-Ops` notes as “owned API account” (membership optional).

**Expected result:** Non-spadmin API identity exists with least privilege.

**If it fails:** Use existing limited user temporarily but flag as non-compliant for prod design.

### Task 3 — Authenticated read call

1. With `curl`, call a safe read endpoint (identity list/get or plugin ping) using `mnb.api.lab`.
2. Example shape (adjust path to your build):

```bash
curl -u 'mnb.api.lab:***' \
  -H 'Accept: application/json' \
  'http://localhost:8080/identityiq/rest/...'
```

3. Confirm HTTP 200 and JSON/XML body.
4. Redact password from binder; keep status code + endpoint.

**Expected result:** Successful API read with API identity.

**If it fails:** 401—check password/capability; 404—fix base path; 403—add missing right only.

### Task 4 — Negative authz test

1. Create or use an identity with **no** API rights (e.g., `raj.external`).
2. Repeat the same curl; expect 401/403.
3. Screenshot or save response code.

**Expected result:** Denied call proves capability gating.

### Task 5 — SCIM probe (if enabled)

1. Attempt `GET` Users resource on SCIM base for filter `userName eq "helen.ross"` (syntax per SCIM).
2. If SCIM disabled, record “Not enabled in lab WAR” and design-only: which ITSM use cases need SCIM vs connector aggregation.
3. Never run bulk destructive SCIM deletes in shared lab.

**Expected result:** SCIM success **or** explicit lab limitation + design note.

### Task 6 — API register entry

1. Fill register row: Account | Owner (`helen.ross`) | Capabilities | Endpoints used | Secret location | Rotated on | Ticket.
2. Add monitoring expectation: failed logins → SIEM (Lesson 104).

**Expected result:** One completed register row for `mnb.api.lab`.

## Acceptance criteria

- [ ] API base URL table documented
- [ ] `mnb.api.lab` (or equivalent) created without SystemAdministrator
- [ ] Successful authenticated read
- [ ] Failed call with unprivileged user evidenced
- [ ] SCIM probed or waiver written
- [ ] API register row completed

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| 401 always | Basic auth disabled / wrong realm | Check web.xml / SSO; try session cookie login flow |
| HTML login page returned | Hit UI URL not REST | Use REST/SCIM path |
| 403 on SCIM | Module/capability missing | Enable SCIM; grant SCIM rights |
| Password in shell history | curl -u on shared host | Use `curl --netrc-file` with mode 600; rotate |
| Plugin ping works, OOTB REST fails | Different auth filter | Compare plugin vs OOTB security constraints |

## Training binder evidence

- URL table  
- API identity capability screenshot  
- curl status codes (success + deny)  
- API register row  

## Knowledge check

1. Why must integrations avoid `spadmin`?
2. What is the difference between plugin REST and SCIM?
3. Who owns the Meridian API account register?
4. What TLS rule applies outside pure local lab?
5. What negative test proves API authz?

### Answers

1. Shared break-glass credentials, over-privilege, non-attributable automation.  
2. Plugin REST = custom extension endpoints; SCIM = standard identity provisioning API.  
3. IAM lead / `helen.ross` (control owner) with AppSec review.  
4. HTTPS only for shared/homelab/prod; document HTTP-only local exceptions.  
5. Same endpoint with an unprivileged identity returns 401/403.

## Stretch lab

Document an ITSM “create access request” API sequence using IdentityRequest resources (version-specific); include idempotency key header design.

## Summary

- Prefer dedicated API identities with least privilege over `spadmin`.
- Separate OOTB REST, plugin REST, and SCIM in your integration design.
- Register, rotate, and SIEM-monitor every non-human account.

## Integration patterns for Meridian

| Consumer | API surface | Auth | Notes |
| --- | --- | --- | --- |
| ServiceNow IAM spoke | SCIM or REST requests | OAuth/basic per build | Prefer named `mnb.api.itsm` |
| HR bot (future) | SCIM Users | Cert auth | Do not bypass authoritative aggregation |
| Monitoring | Toolkit ping | Capability | Synthetic check only |
| Custom UI | Plugin REST | Session + right | Lesson 98 |

### Task 7 — Rate limit & abuse notes

1. Document expected calls/minute for lab API identity.
2. State response: disable identity + rotate secret on anomaly.
3. Add header hygiene: `X-Request-Id` if clients can send one; log it.
4. Forbid embedding passwords in Postman collections committed to git.

**Expected result:** Abuse-response paragraph in API register.

### SCIM vs connector aggregation

SCIM is for online identity CRUD from trusted peers. Meridian still aggregates AD/core via connectors for entitlement inventory. Do not assume SCIM replaces Account Aggregation for deep entitlement dictionaries.

## Lab curl hygiene

Prefer:

```bash
curl --netrc-file ~/.iiq-lab-netrc ...
chmod 600 ~/.iiq-lab-netrc
```

Never commit `.netrc` or Postman environments with secrets. Rotate `mnb.api.lab` after any shared-screen demo.

---

**Previous:** [Lesson 99 — IIQ Console & Automation](99-iiq-console-and-automation.md)  
**Next:** [Lesson 101 — SSB/SSD Promotion Discipline](101-ssb-ssd-promotion-discipline.md)
