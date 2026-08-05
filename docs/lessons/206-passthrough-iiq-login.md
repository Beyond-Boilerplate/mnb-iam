# Lesson 206 — Pass-Through Login to IIQ

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~40 minutes  
**Prereq:** Lesson 204  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 61 / auth

> **Why (1–2 lines):** Operators should authenticate to IIQ as themselves against a real directory, not live forever as `spadmin`. An examiner reviewing access logs expects to see named-user logins, not one shared admin session for every persona's activity.

## What this is

Pass-through authentication lets IIQ delegate the login bind to a source application instead of checking a local password hash. Up to now every lesson has used `spadmin`/`admin` because that's the only account guaranteed to exist before any directory is aggregated. From here on, you'll log in as `helen.ross` against **`MNB-OpenLDAP`** — the same live directory validated in Lesson 204 — using her real LDAP bind DN and password (`LabUser1!`). This matters for two reasons: it's the honest way real IIQ deployments authenticate a directory-backed workforce (never local passwords), and every later lesson that says "as Helen, request access" or "as Marcus, approve" assumes you can actually log in as that persona, not just view their cube as spadmin.

## Know these

- Login field maps to `uid` (what a human types), not `employeeNumber` (the correlation key) — confusing the two is a classic real-world misconfiguration.
- Aggregating accounts from an app does not automatically make it a login source — enabling pass-through is a separate configuration toggle.
- Personas covered here: `helen.ross` and `priya.wire`, both `/ LabUser1!`.
- **Wrong way:** Testing persona logins in the same browser tab/profile as `spadmin` — session cookies persist aggressively, and you'll frequently misdiagnose "still logged in as admin" as a pass-through failure.

## Intent

- Confirm Helen's directory bind works with `ldapsearch` *before* trusting IIQ's login page with it.
- Configure IIQ's pass-through / login source to authenticate against `MNB-OpenLDAP`.
- Successfully log in as `helen.ross` and log back out, without ever touching her password hash in IIQ's own tables.
- Keep `spadmin` and persona sessions cleanly separated so you don't accidentally do admin work "as Helen."

## Before you start

- [ ] Lesson 204 complete; `MNB-OpenLDAP` aggregated with Helen's account link present
- [ ] `ldapsearch` available or `docker exec mnb-openldap ldapsearch` as fallback
- [ ] A second browser profile or private/incognito window ready for persona sessions
- [ ] Evidence dir: `mkdir -p ~/iiq-lab-evidence/sandbox/206`

## Do this

1. Prove the bind works at the directory level first: `ldapsearch -x -H ldap://localhost:389 -b ou=people,dc=meridiannb,dc=com -D 'uid=helen.ross,ou=people,dc=meridiannb,dc=com' -w 'LabUser1!' '(uid=helen.ross)' dn`.  
   **Why:** if this fails, the directory itself is the problem; if it succeeds and IIQ login still fails later, you've isolated the variable.  
   **Expect:** returns Helen's `dn:` line.

2. Follow `lab-data/enterprise/PASS-THROUGH-AUTH.md`. In IIQ: **Gear → Global Settings → Login Configuration** → enable authentication against application `MNB-OpenLDAP`, mapping the login field to `uid` (optionally `mail` as fallback).  
   **Why:** this is the toggle that actually makes an already-aggregated app usable as a login source.  
   **Expect:** setting saves without error.

3. Confirm you understand `uid` (login key) vs. `employeeNumber` (correlation key, Lesson 214).  
   **Why:** a real bank workforce types their directory username at login, never their internal employee id.  
   **Expect:** you can state which attribute does which job from memory.

4. Log out of `spadmin` fully, then authenticate as `helen.ross` / `LabUser1!` on the login page.  
   **Why:** a stale spadmin session masquerading as success is the most common false positive here.  
   **Expect:** lands on Helen's own dashboard, not admin menus.

5. If login fails, check in order: the bind DN template IIQ uses resolves to `uid=helen.ross,ou=people,dc=meridiannb,dc=com`, her account isn't disabled, and the auth-search attribute list (`cn`, `uid`, `mail` per the Application XML's `authSearchAttributes`) includes whatever field you typed.  
   **Expect:** one of these three is the actual root cause if step 4 didn't work.

6. Keep spadmin and Helen in **separate browser profiles** (or one normal + one private window) going forward.  
   **Why:** most later lessons need both open side by side — spadmin to configure, Helen to prove it worked — and mixing them in one tab causes constant "wait, why does this look like admin" confusion.  
   **Expect:** two clearly distinct sessions you can flip between without logging out.

7. Repeat step 4 as `priya.wire` / `LabUser1!`.  
   **Why:** confirms pass-through isn't a one-off fluke tied to Helen specifically.  
   **Expect:** Priya's own dashboard loads cleanly.

8. Note what pass-through does **not** do: it doesn't create IIQ capabilities, roles, or workgroup membership out of nowhere — it only answers "is this the right password for this directory account." A persona with no birthright access assigned yet will still log in fine but see a mostly empty workspace.  
   **Why:** separating "can authenticate" from "has access" avoids a common early misdiagnosis where a thin post-login dashboard gets blamed on login config instead of missing birthright provisioning (Lesson 216).  
   **Expect:** you can state this distinction without looking it up.

## If it fails

- **`ldapsearch` bind fails but admin bind worked in Lesson 204** — you likely typo'd the DN; it must be the full `uid=helen.ross,ou=people,dc=meridiannb,dc=com`, not just `helen.ross`.
- **IIQ login page rejects valid credentials** — check whether `MNB-OpenLDAP` is actually enabled as an authentication source, separate from being merely aggregated.
- **Login succeeds but lands on an error page / no capabilities** — needs default workforce capabilities; if testing a brand-new joiner instead of Helen, assign birthright first (Lesson 216) or use an existing seeded persona.
- **Works for `helen.ross` but not `priya.wire`** — compare their `Active`/enabled attribute in phpLDAPadmin.
- **Stuck "logged in as spadmin" no matter what** — clear cookies for `localhost:8080` or use a private window.

## You are done when

You've logged into IIQ as `helen.ross` and separately as `priya.wire`, both via pass-through against `MNB-OpenLDAP`, and you have a dedicated browser profile/window set aside for persona sessions versus spadmin.

## Control note

- **Control:** Workforce authentication — named-user login, no shared local password hashes.
- **Owner:** IAM Ops / Security.
- **SLA (lab):** any new persona must pass-through login the same session their directory account is provisioned.
- **Evidence:** `~/iiq-lab-evidence/sandbox/206/` — `ldapsearch` bind proof, login screenshots for both personas.

## Quick check

1. What login-field attribute does pass-through map to? → `uid` (not `employeeNumber`).
2. What single toggle is separate from aggregation and easy to forget? → enabling the app as a login/authentication source.
3. Why use two browser profiles for the rest of this path? → to avoid stale-session confusion between spadmin and persona work.

## Navigate

- Previous: Lesson 205
- Next: Lesson 207
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
