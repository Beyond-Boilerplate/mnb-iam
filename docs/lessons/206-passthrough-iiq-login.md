# Lesson 206 — Pass-Through Login to IIQ

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~40 minutes  
**Prereq:** Lesson **207** + Lesson **204** (Helen cube + OpenLDAP account link)  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 61 / auth

> **Why:** Operators should authenticate to IIQ as themselves against a real directory, not live forever as `spadmin`. Shared `spadmin` sessions make access logs and persona debugging useless — you need named-user logins to prove who did what.

## What this is

**Pass-through authentication** lets IIQ delegate the login bind to a source application instead of checking a local password hash.

Up to now every lesson has used `spadmin` / `admin` because that is the only account guaranteed to exist before Workday cubes and directory aggregation. From here on, you log in as `helen.ross` against **`MNB-OpenLDAP`** — the same live directory validated in Lesson 204 — using her real LDAP bind DN and password (`LabUser1!`).

Why it matters:

- Real IIQ deployments authenticate a directory-backed workforce this way (not local password hashes)
- Later lessons that say “as Helen, request access” or “as Marcus, approve” assume you can actually log in as that persona

Full runbook: [`lab-data/enterprise/PASS-THROUGH-AUTH.md`](../../lab-data/enterprise/PASS-THROUGH-AUTH.md).

## Know these

| Idea | Detail |
| --- | --- |
| Login field | Maps to `uid` (what a human types) — **not** `employeeNumber` (correlation key) |
| Aggregation ≠ login source | Aggregating accounts does **not** automatically make the app a login source — enable pass-through separately |
| Personas | `helen.ross` / `LabUser1!` and `priya.wire` / `LabUser1!` |
| Bind DN (Helen) | `uid=helen.ross,ou=people,dc=meridiannb,dc=com` |

- **Wrong way:** Testing persona logins in the same browser tab/profile as `spadmin` — session cookies persist aggressively, and you will misdiagnose “still logged in as admin” as a pass-through failure.

## Intent

- Confirm Helen’s directory bind works with `ldapsearch` *before* trusting IIQ’s login page with it.
- Configure IIQ’s pass-through / login source to authenticate against `MNB-OpenLDAP`.
- Successfully log in as `helen.ross` and log back out, without touching her password hash in IIQ’s own tables.
- Keep `spadmin` and persona sessions cleanly separated.

## Before you start

- [ ] Lesson 204 complete; `MNB-OpenLDAP` aggregated with Helen’s account link present
- [ ] `ldapsearch` available or `docker exec mnb-openldap ldapsearch` as fallback
- [ ] A second browser profile or private/incognito window ready for persona sessions
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/206
```

## Do this

### Task 1 — Prove Helen’s directory bind first

If this fails, the directory itself is the problem. If it succeeds and IIQ login still fails later, you’ve isolated the variable.

```bash
ldapsearch -x -H ldap://localhost:389 \
  -b ou=people,dc=meridiannb,dc=com \
  -D 'uid=helen.ross,ou=people,dc=meridiannb,dc=com' \
  -w 'LabUser1!' \
  '(uid=helen.ross)' dn
```

- **Why:** never debug the login page before the bind works at LDAP.
- **Expect:** returns Helen’s `dn:` line.

> **Tip:** Result `32 No such object` usually means a typo’d bind DN or search base — copy the DN exactly. No host `ldapsearch`? Use `docker exec mnb-openldap ldapsearch …` and drop `-H`.

### Task 2 — Enable pass-through against MNB-OpenLDAP

Aggregating accounts does **not** automatically make the app a login source — enable pass-through separately.

Follow [`PASS-THROUGH-AUTH.md`](../../lab-data/enterprise/PASS-THROUGH-AUTH.md). In IIQ:

1. **Gear → Global Settings → Login Configuration**
2. Enable authentication against application `MNB-OpenLDAP`
3. Map the login field to `uid` (optionally `mail` as fallback)

| Attribute | Job |
| --- | --- |
| `uid` | Login key — what a human types |
| `employeeNumber` | Correlation key (Lesson 214) — **not** the login field |

- **Why:** a real bank workforce types their directory username at login, never their internal employee id.
- **Expect:** setting saves without error.

### Task 3 — Log in as helen.ross (clean session)

A stale spadmin session masquerading as success is the most common false positive here.

1. Log out of `spadmin` fully (or open a **private/incognito** window)
2. Authenticate as `helen.ross` / `LabUser1!`

- **Why:** operators should authenticate as themselves against a real directory, not live forever as `spadmin`.
- **Expect:** lands on Helen’s own dashboard, not admin menus.

> **Watch out:** Keep spadmin and personas in **separate browser profiles** (or one normal + one private window) going forward — most later lessons need both open side by side.

### Task 4 — If login fails, check in this order

| Check | What “good” looks like |
| --- | --- |
| Bind DN template | Resolves to `uid=helen.ross,ou=people,dc=meridiannb,dc=com` |
| Account enabled | Not disabled in OpenLDAP |
| Auth-search attributes | Application XML `authSearchAttributes` include the field you typed (`uid`, `cn`, `mail`, …) |

- **Why:** one of these three is usually the root cause — don’t re-aggregate blindly.
- **Expect:** login succeeds after fixing the matching row.

### Task 5 — Repeat as priya.wire

Confirms pass-through isn’t a one-off fluke tied to Helen.

1. In the persona browser profile, log out
2. Authenticate as `priya.wire` / `LabUser1!`

- **Why:** later lessons say “as Priya, request…” and assume this works.
- **Expect:** Priya’s own dashboard loads cleanly.

> **Tip:** Pass-through only answers “is this the right password for this directory account?” It does **not** create IIQ capabilities, roles, or workgroup membership. A persona with no birthright yet (Lesson 216) still logs in but may see a mostly empty workspace — that is auth succeeding, not access failing.

### Task 6 — Close with asserts

```bash
./tools/lab/enterprise/verify-lesson.sh 206
```

- **Why:** hard checks cover `MNB-OpenLDAP` exists and login page reachable.
- **Expect:** hard asserts PASS.

## If it fails

| Symptom | Fix |
| --- | --- |
| `ldapsearch` bind fails but admin bind worked in Lesson 204 | Typo’d DN — must be full `uid=helen.ross,ou=people,dc=meridiannb,dc=com`, not just `helen.ross` |
| IIQ login page rejects valid credentials | Confirm `MNB-OpenLDAP` is enabled as an **authentication source**, separate from being merely aggregated |
| Login succeeds but lands on an error page / no capabilities | Needs default workforce capabilities; for a brand-new joiner, assign birthright first (Lesson 216) or use a seeded persona |
| Works for `helen.ross` but not `priya.wire` | Compare their Active/enabled attribute in phpLDAPadmin |
| Stuck “logged in as spadmin” no matter what | Clear cookies for `localhost:8080` or use a private window |

## You are done when

- [ ] Logged into IIQ as `helen.ross` via pass-through against `MNB-OpenLDAP`
- [ ] Logged in separately as `priya.wire`
- [ ] Dedicated browser profile/window set aside for persona sessions vs spadmin
- [ ] `./tools/lab/enterprise/verify-lesson.sh 206` hard asserts PASS

## Control note

- **Control:** Workforce authentication — named-user login, no shared local password hashes
- **Owner:** IAM Ops / Security
- **SLA (lab):** any new persona must pass-through login the same session their directory account is provisioned
- **Evidence:** `~/iiq-lab-evidence/sandbox/206/` — `ldapsearch` bind proof, login screenshots for both personas

## Quick check

1. What login-field attribute does pass-through map to? → `uid` (not `employeeNumber`)
2. What single toggle is separate from aggregation and easy to forget? → enabling the app as a login/authentication source
3. Why use two browser profiles for the rest of this path? → to avoid stale-session confusion between spadmin and persona work

## Feedback

Could you re-enable pass-through and log in as Helen from memory? If bind or login failed, note **Task number**, the exact DN you used, and whether `ldapsearch` succeeded before the IIQ login attempt.

## Navigate

- Previous: [Lesson 205](205-samba-ad-live-ops.md)
- Next: [Lesson 208](208-jdbc-core-banking.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
