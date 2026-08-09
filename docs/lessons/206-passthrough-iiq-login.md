# Lesson 206 — Pass-Through Login to IIQ

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~50 minutes  
**Prereq:** Lesson **207** + Lesson **204** (Helen cube + OpenLDAP account link)  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 61 / auth

> **Why:** Operators should authenticate to IIQ as themselves against a real directory, not live forever as `spadmin`. Shared `spadmin` sessions make access logs and persona debugging useless — you need named-user logins to prove who did what. Examiners ask how workforce login is bound to the SoR directory, not a local password hash file.

## What this is

**Pass-through authentication** lets IIQ delegate the login bind to a source application instead of checking a local password hash.

Up to now every lesson has used `spadmin` / `admin` because that is the only account guaranteed to exist before Workday cubes and directory aggregation. From here on, you log in as `helen.ross` against **`MNB-OpenLDAP`** — the same live directory validated in Lesson 204 — using her real LDAP bind DN and password (`LabUser1!`).

Nothing about login configuration is guaranteed to be correct after a wipe or partial seed. This lesson is **verify-or-configure**: prove bind → prove cube + link → inspect Login Configuration → enable/fix if needed → prove persona login.

Full runbook companion: [`lab-data/enterprise/PASS-THROUGH-AUTH.md`](../../lab-data/enterprise/PASS-THROUGH-AUTH.md).

## Know these

```text
ldapsearch bind as helen.ross (directory truth)
  → Confirm Helen cube + MNB-OpenLDAP Link in IIQ
  → Gear → Global Settings → Login Configuration
       verify-or-enable authentication against MNB-OpenLDAP
       login field = uid (not employeeNumber)
  → Clean browser session → login helen.ross / LabUser1!
  → Repeat as priya.wire
```

| Idea | Detail |
| --- | --- |
| Login field | Maps to `uid` (what a human types) — **not** `employeeNumber` (correlation key) |
| Aggregation ≠ login source | Aggregating accounts does **not** automatically make the app a login source — enable pass-through separately |
| Auth-search attributes | App attrs IIQ tries when resolving the typed username (`uid`, `mail`, …) |
| Personas | `helen.ross` / `LabUser1!` and `priya.wire` / `LabUser1!` |
| Bind DN (Helen) | `uid=helen.ross,ou=people,dc=meridiannb,dc=com` |

- **Wrong way:** Testing persona logins in the same browser tab/profile as `spadmin` — session cookies persist aggressively.  
- **Wrong way:** Mapping login to `employeeNumber` — humans type `helen.ross`, not `MNB00001`.  
- **Wrong way:** Debugging the login page before `ldapsearch` bind succeeds.  
- **Wrong way:** Assuming Login Configuration survived a wipe — **verify** every time.

## Intent

- Confirm Helen’s directory bind works with `ldapsearch` *before* trusting IIQ’s login page.
- Verify Helen’s cube and OpenLDAP Link exist (or rebuild from 204/207).
- Verify-or-configure IIQ pass-through against `MNB-OpenLDAP` with exact UI steps.
- Successfully log in as `helen.ross` and `priya.wire` in a clean session.
- Keep `spadmin` and persona sessions cleanly separated.

## Before you start

Complete every checkbox. Do not skip into Task 1 until these are true.

- [ ] IIQ up: [http://localhost:8080/identityiq](http://localhost:8080/identityiq)
- [ ] Lesson 207 done — workforce cubes exist (at least `helen.ross`)
- [ ] Lesson 204 pattern — OpenLDAP aggregated at least once (you will **re-check** the Link)
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

No host `ldapsearch`? Use:

```bash
docker exec mnb-openldap ldapsearch -x \
  -b ou=people,dc=meridiannb,dc=com \
  -D 'uid=helen.ross,ou=people,dc=meridiannb,dc=com' \
  -w 'LabUser1!' \
  '(uid=helen.ross)' dn
```

- **Why:** never debug the login page before the bind works at LDAP.
- **Expect:** returns Helen’s `dn:` line.

> **Tip:** Result `32 No such object` usually means a typo’d bind DN or search base — copy the DN exactly. Save the command output under evidence.

### Task 2 — Verify Helen’s cube and OpenLDAP Link (assume nothing)

Pass-through authenticates a directory account and maps it to an **existing** Identity cube. No cube / no Link → confusing login failures.

1. As `spadmin`: **Identities → Identity Warehouse** → open `helen.ross`
2. Confirm the cube exists (if missing → finish Lesson 207 Workday aggregate + refresh first)
3. Open **Application Accounts** (or equivalent Links view)
4. Confirm a Link for **`MNB-OpenLDAP`**
5. Note the native identity / `uid` value (`helen.ross`)

If the Link is missing:

1. **Applications → Application Definition → MNB-OpenLDAP** → **Test Connection**
2. **Setup → Tasks** → run **Account Aggregation** for `MNB-OpenLDAP` (create the task if wipe left Tasks empty)
3. Re-open Helen → confirm the Link

- **Why:** Login Configuration alone cannot invent a cube or Link.
- **Expect:** `helen.ross` cube with an `MNB-OpenLDAP` account link before you touch Login Configuration.

### Task 3 — Inspect current Login Configuration (verify before change)

Do not assume pass-through is already on.

1. **Gear → Global Settings → Login Configuration**
2. Open the **LDAP / Directory** (wording varies by build) section for pass-through / authentication sources
3. Record under evidence what you see **now**:

| Check | Your observation |
| --- | --- |
| Pass-through / directory auth enabled? | yes / no |
| Application listed | `MNB-OpenLDAP` / other / empty |
| Login / username attribute | `uid` / `mail` / other / blank |

- **Why:** wipe/overlay can leave this empty or pointed at the wrong app.
- **Expect:** you know the current state before editing.

### Task 4 — Configure pass-through against MNB-OpenLDAP

If Task 3 already shows `MNB-OpenLDAP` enabled with login field `uid` (and optionally `mail`), skip to the confirmation at the end of this Task — still **Save** only if you changed something.

Otherwise, set exactly:

1. Still on **Gear → Global Settings → Login Configuration → LDAP/Directory**
2. Enable authentication against application **`MNB-OpenLDAP`**
3. Map the login / username field to **`uid`**
4. Optionally add **`mail`** as a fallback search attribute
5. **Save**
6. Re-open the page and confirm the values stuck

| Attribute | Job |
| --- | --- |
| `uid` | Login key — what a human types |
| `employeeNumber` | Correlation key (Lesson 214) — **not** the login field |

#### 4b — Confirm app auth-search attributes (if login still fails later)

1. **Applications → Application Definition → MNB-OpenLDAP**
2. Check Configuration / Attributes for auth-search style settings (XML key often `authSearchAttributes`)
3. Confirm values include at least `uid` (and `mail` if you use email login)

If the Application object itself is missing: import / re-seed from Lesson 202 / `config/Application/` for OpenLDAP — do not invent a second directory app name.

- **Why:** a real bank workforce types their directory username at login, never their internal employee id.
- **Expect:** Login Configuration shows `MNB-OpenLDAP` + `uid`; setting survives reopen.

> **Watch out:** Aggregating accounts does **not** flip this toggle. Aggregation and authentication source are separate.

### Task 5 — Log in as helen.ross (clean session)

A stale spadmin session masquerading as success is the most common false positive here.

1. Log out of `spadmin` fully  
   **or** open a **private/incognito** window (preferred going forward)
2. Go to [http://localhost:8080/identityiq](http://localhost:8080/identityiq)
3. Authenticate as `helen.ross` / `LabUser1!`
4. Screenshot Home (no password) under evidence

- **Why:** operators should authenticate as themselves against a real directory, not live forever as `spadmin`.
- **Expect:** lands on Helen’s own dashboard / Home — not full System Admin menus (unless she was granted them).

> **Watch out:** Keep spadmin and personas in **separate browser profiles** (or one normal + one private window) going forward — most later lessons need both open side by side.

### Task 6 — If login fails, check in this order

Stop guessing. Walk the table top to bottom.

| # | Check | What “good” looks like | Fix |
| --- | --- | --- | --- |
| 1 | `ldapsearch` bind | Task 1 returns `dn:` | Fix DN / password / OpenLDAP up |
| 2 | Cube + Link | Task 2 | Aggregate `MNB-OpenLDAP`; finish 207 if no cube |
| 3 | Login Configuration | App = `MNB-OpenLDAP`, field = `uid` | Re-do Task 4; Save; reopen |
| 4 | Auth-search attrs | Include the field you typed | Add `uid` / `mail` on the app |
| 5 | Account enabled | Not disabled in OpenLDAP / phpLDAPadmin | Re-enable entry |
| 6 | Browser session | Private window, no `spadmin` cookie | Clear cookies for `localhost:8080` |

- **Why:** one of these is usually the root cause — don’t re-aggregate blindly.
- **Expect:** login succeeds after fixing the matching row.

### Task 7 — Repeat as priya.wire

Confirms pass-through isn’t a one-off fluke tied to Helen.

1. Confirm `priya.wire` has an `MNB-OpenLDAP` Link (same pattern as Task 2). If missing, aggregate OpenLDAP again.
2. In the persona browser profile, log out
3. Authenticate as `priya.wire` / `LabUser1!`

- **Why:** later lessons say “as Priya, request…” and assume this works.
- **Expect:** Priya’s own dashboard loads cleanly.

> **Tip:** Pass-through only answers “is this the right password for this directory account?” It does **not** create IIQ capabilities, roles, or workgroup membership. A persona with no birthright yet (Lesson 216) still logs in but may see a mostly empty workspace — that is auth succeeding, not access failing.

### Task 8 — Optional Samba source (only if AD profile is up)

If `mnb-samba-ad` is healthy and you aggregated `MNB-ActiveDirectory-Live`:

1. Login Configuration → add **`MNB-ActiveDirectory-Live`** as an additional (or alternate) pass-through source
2. Username attribute = `sAMAccountName` (same as Meridian `name`, e.g. `helen.ross`)
3. Prove login once, then return primary lab path to **OpenLDAP** unless a later lesson says otherwise

If Samba is not healthy (common on Apple Silicon), skip this Task — OpenLDAP pass-through is enough for the path.

- **Why:** real estates often have more than one directory auth source; know the second path exists.
- **Expect:** either a successful AD pass-through note, or an explicit “Samba skipped” line under evidence.

### Task 9 — Close with asserts

```bash
./tools/lab/enterprise/verify-lesson.sh 206
```

- **Why:** hard checks cover `MNB-OpenLDAP` exists and login page reachable.
- **Expect:** hard asserts PASS.

## If it fails

| Symptom | Fix |
| --- | --- |
| `ldapsearch` bind fails but admin bind worked in Lesson 204 | Typo’d DN — must be full `uid=helen.ross,ou=people,dc=meridiannb,dc=com`, not just `helen.ross` |
| No Helen cube | Finish Lesson 207 (Workday aggregate + create identities refresh) before this lesson |
| Cube exists, no OpenLDAP Link | Task 2 — Test Connection + Account Aggregation on `MNB-OpenLDAP` |
| IIQ login page rejects valid credentials | Confirm `MNB-OpenLDAP` is enabled as an **authentication source**, separate from being merely aggregated |
| Login succeeds but lands on an error page / no capabilities | Needs default workforce capabilities; for a brand-new joiner, assign birthright first (Lesson 216) or use a seeded persona |
| Works for `helen.ross` but not `priya.wire` | Compare Active/enabled in phpLDAPadmin; confirm Priya’s Link exists |
| Stuck “logged in as spadmin” no matter what | Clear cookies for `localhost:8080` or use a private window |

## You are done when

- [ ] `ldapsearch` bind for Helen succeeded before any IIQ login attempt
- [ ] Helen cube + `MNB-OpenLDAP` Link verified (or repaired)
- [ ] Login Configuration verified-or-set: `MNB-OpenLDAP` + `uid`
- [ ] Logged into IIQ as `helen.ross` via pass-through
- [ ] Logged in separately as `priya.wire`
- [ ] Dedicated browser profile/window set aside for persona sessions vs spadmin
- [ ] `./tools/lab/enterprise/verify-lesson.sh 206` hard asserts PASS

## Control note

- **Control:** Workforce authentication — named-user login, no shared local password hashes
- **Owner:** IAM Ops / Security
- **SLA (lab):** any new persona must pass-through login the same session their directory account is provisioned
- **Evidence:** `~/iiq-lab-evidence/sandbox/206/` — `ldapsearch` bind proof, Login Configuration notes, login screenshots for both personas

## Quick check

1. What login-field attribute does pass-through map to? → `uid` (not `employeeNumber`)  
2. What single toggle is separate from aggregation and easy to forget? → enabling the app as a login/authentication source  
3. Why use two browser profiles for the rest of this path? → to avoid stale-session confusion between spadmin and persona work  
4. What do you verify before touching Login Configuration? → directory bind **and** cube + OpenLDAP Link

## Feedback

Could you re-enable pass-through from a wiped Login Configuration and log in as Helen from memory? If bind or login failed, note **Task number**, the exact DN you used, whether `ldapsearch` succeeded, and whether Helen had an OpenLDAP Link before the IIQ attempt.

## Navigate

- Previous: [Lesson 205](205-samba-ad-live-ops.md)
- Next: [Lesson 208](208-jdbc-core-banking.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md) · Theory: [256 Connector Registry](256-connector-registry-theory.md)
