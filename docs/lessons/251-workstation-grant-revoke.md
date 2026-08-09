# Lesson 251 — Workstation Grant → Login → Revoke Lockout

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~80 minutes  
**Prereq:** Lessons 211–212, 221–222; Capstone 250 recommended  
**Stack:** `./tools/lab/docker/up.sh --enterprise --with=sso`

**Maps to classic track:** access + login proof (DoD #3/#4); Unix/workstation narrative 83–84

> **Why:** Laptop access is only real if the user can sign in after grant and cannot after revoke. A green role checkbox without a denied login after sunset is theater.

## What this is

**Workstation Portal** is an OIDC relying party on this estate — the lab stand-in for “can this person unlock a workstation session?”

| Piece | Value |
| --- | --- |
| URL | [http://localhost:8094/](http://localhost:8094/) |
| OIDC client | `workstation-portal` (realm `meridian`) |
| Gate claim | ID token `groups` must contain **`mnb-workstation-users`** |
| Image | `mnb-sso-gate:local` (shared with HR/Finance in Lesson 253) |

Flow:

```text
Browser → Workstation (:8094)
       → Keycloak meridian login (authn)
       → groups claim check for mnb-workstation-users (authz)
       → Signed in  OR  Access denied
```

Default `--enterprise` does **not** start Workstation. You need **`--with=sso`** (or `--enterprise-full`).

Nothing for this drill is pre-built for *your* subject. You will:

1. Create disposable **`lab.ws1`** (never Helen / Priya / Marcus as the subject)  
2. Ensure a Keycloak user exists **without** `mnb-workstation-users`  
3. Prove **Access denied** after successful IdP login  
4. Grant (Keycloak group + optional IIQ requestable role)  
5. Prove **Signed in**  
6. Revoke → prove **Access denied** again  
7. Confirm seeded Helen still works (scoped revoke, not global outage)

**Credential custody** (vault passwords) is Lesson 255. Here the proof is the **group gate**.

> **Watch out:** A successful Keycloak password screen is **not** workstation access. Authn ≠ authz. This app enforces both.

## Know these

```text
Stack: --enterprise --with=sso
  → Create lab.ws1 (HCM) + Keycloak user without mnb-workstation-users
  → curl :8094/health → requiredGroups includes mnb-workstation-users
  → Login as lab.ws1 → Access denied (baseline)
  → Grant: add Keycloak group (+ optional IIQ MNB-Bundle-Workstation-Access request)
  → Login again → Signed in
  → Revoke group (+ remove IIQ role if assigned)
  → Login again → Access denied
  → Control: helen.ross still Signed in
```

| Term | Plain English | Meridian example |
| --- | --- | --- |
| **Authn** | Proving who you are | Keycloak accepts `lab.ws1` / password |
| **Authz** | What you may do after login | App requires `mnb-workstation-users` |
| **SSO gate** | App that checks IdP groups after OIDC | Workstation Portal `:8094` |
| **Grant** | Put the user in the required group | Keycloak Groups → Join |
| **Revoke lockout** | Remove group; next login denied | Same user, Access denied again |
| **IIQ role** | Requestable catalog item for the grant story | `MNB-Bundle-Workstation-Access` (seed) |

- **Wrong way:** Treating Keycloak login success as proof of workstation access.  
- **Wrong way:** Using Helen / Priya / Marcus as the grant/revoke subject — keep them for control/certs.  
- **Wrong way:** Starting only `--enterprise` and wondering why `:8094` is down.  
- **Wrong way:** Leaving the group after the drill — temporary that never ends is permanent.  
- **Wrong way:** Expecting the IIQ Bundle alone to mutate Keycloak without you confirming group membership.

## Intent

- Prove deny → grant → allow → revoke → deny on Workstation for `lab.ws1`.  
- Separate authentication (Keycloak) from entitlement (`groups` claim).  
- Leave three login-state screenshots an examiner could follow.  
- Confirm Helen’s control path still works after your revoke.

## Before you start

Complete every checkbox. Do not skip into Task 1 until these are true.

- [ ] Stack with SSO pack:

```bash
./tools/lab/docker/up.sh --enterprise --with=sso
```

- [ ] IIQ up: [http://localhost:8080/identityiq](http://localhost:8080/identityiq) — `spadmin` / `admin`
- [ ] Keycloak Admin: [http://localhost:8085/admin/](http://localhost:8085/admin/) — `admin` / `admin` — realm **`meridian`**
- [ ] Workstation healthy:

```bash
curl -sf http://127.0.0.1:8094/health | python3 -m json.tool
```

  - **Expect:** `"ok": true`, `"requiredGroups": ["mnb-workstation-users"]`, `"clientId": "workstation-portal"`.

- [ ] HCM mock healthy:

```bash
curl -sf http://localhost:8091/health
```

- [ ] You know Lesson 212’s OIDC idea (Portal → Keycloak → groups). You will **re-prove** the workstation gate from scratch.
- [ ] Evidence dir:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/251
```

## Do this

### Task 1 — Create disposable identity `lab.ws1`

Never use Helen, Priya, Marcus, or Sanjay as the workstation subject.

1. From the **repo root** on your Mac:

```bash
./tools/lab/enterprise/hcm-scenario.sh joiner lab.ws1 Lab Workstation \
  lab.ws1@meridiannb.com 'Bank Operations'
```

2. Confirm HCM:

```bash
curl -s http://localhost:8091/hcm/v1/workers/lab.ws1 \
  | python3 -m json.tool | grep -E 'userName|email|active|status|department'
```

- **Expect:** `userName` `lab.ws1`, `active` true.

3. In IIQ as `spadmin`:
   - Aggregate **`MNB-Workday`** → Task Result **Complete**
   - **Refresh Identity Cube** including `lab.ws1` (promote attributes / correlate as shown)
   - Wait **Complete**

4. **Identities → Identity Warehouse** → open `lab.ws1`

- **Why:** grant/revoke needs a throwaway subject so shared personas stay intact.
- **Expect:** cube `lab.ws1` exists.

Screenshot the identity header under evidence.

### Task 2 — Ensure Keycloak user exists **without** workstation group

Workstation authz is Keycloak-group based. Create or verify the IdP user with a password, and confirm the gate group is **absent**.

#### 2a — Prefer birthright IdP (if Lesson 216/217 pack is live)

1. Open cube `lab.ws1` → Application Accounts  
2. If **`MNB-Keycloak-IdP`** link exists with `portal-users` / `mnb-employees`, open Keycloak Admin → Users → `lab.ws1` → **Groups**  
3. Confirm **`mnb-workstation-users` is not listed**

If the IdP link is missing, use 2b.

#### 2b — Manual Keycloak user (lab fallback)

1. Keycloak Admin → realm **`meridian`** (not `master`)  
2. **Users → Add user**

| Field | Value |
| --- | --- |
| Username | `lab.ws1` |
| Email | `lab.ws1@meridiannb.com` |
| First / Last | `Lab` / `Workstation` |
| Email verified | ON |
| Enabled | ON |

3. **Credentials → Set password** → `LabUser1!` → **Temporary** OFF → Save  
4. **Groups** → Join **`portal-users`** only if you also want Employee Portal later — **do not** join `mnb-workstation-users` yet  

- **Why:** baseline must be authenticated-but-not-entitled.
- **Expect:** user `lab.ws1` exists; Groups tab has **no** `mnb-workstation-users`.

> **Watch out:** Creating the user on realm `master` makes `:8094` look broken. Always switch to **`meridian`**.

### Task 3 — Baseline deny (grant has not happened)

1. Open a private/incognito window (clean cookies)  
2. Go to [http://localhost:8094/](http://localhost:8094/)  
3. Sign in as `lab.ws1` / `LabUser1!`  
4. Use `localhost`, not `127.0.0.1` (redirect URIs are `http://localhost:8094/*`)

- **Why:** this is the “before” control evidence — without it, grant looks like a lucky first try.
- **Expect:** Keycloak accepts the password, then Workstation shows **Access denied** (missing `mnb-workstation-users`).

Save screenshot as `~/iiq-lab-evidence/sandbox/251/01-denied-before-grant.png`.

Write under evidence:

```text
Subject: lab.ws1
Baseline: Access denied (no mnb-workstation-users)
Time: ________
```

### Task 4 — Verify-or-import requestable IIQ role

The catalog item for the production story is `MNB-Bundle-Workstation-Access`. Confirm it exists; import if missing.

1. As `spadmin`: **Setup → Roles** → search `MNB-Bundle-Workstation-Access`  
2. If missing, import from repo (MCP `import_sailpoint_object` or seed):

```bash
# from repo root — re-runs enterprise XML import including Workstation bundle
./tools/lab/enterprise/seed-enterprise.sh
```

Or import only `config/Bundle/MNB-Bundle-Workstation-Access.xml` via Debug → Import.

3. Re-open the role and confirm:

| Field | Expect |
| --- | --- |
| Name | `MNB-Bundle-Workstation-Access` |
| Requestable | ON / true |
| Description | mentions `mnb-workstation-users` / `:8094` |

- **Why:** auditors want a requestable catalog item for workstation access, not only a silent IdP click.
- **Expect:** role searchable for Access Request.

> **Tip:** On this estate the **live login gate** is still the Keycloak group. The Bundle is the IIQ request story; Task 5 mirrors the group so login actually changes.

### Task 5 — Grant workstation access

Do **both** tracks when you can: IIQ request trail + Keycloak group that the app actually checks.

#### 5a — Optional IIQ Access Request (audit trail)

1. As `spadmin`, open **Request Access** on behalf of **`lab.ws1`**  
2. Select **`MNB-Bundle-Workstation-Access`**  
3. Justification:

```text
LAB-251 — workstation grant for disposable lab.ws1
```

4. Submit → complete approvals if your LCM map requires Manager/Owner (Lesson 222 pattern). If Manager is empty on `lab.ws1`, set Manager to `sanjay.kapoor` first (same as Lesson 223 Task 2).  
5. Note IdentityRequest id under evidence.

If Request Access / approvals are broken in your session, document the gap and continue with 5b — **login proof still requires the Keycloak group**.

#### 5b — Keycloak group grant (required for login proof)

1. Keycloak Admin → realm `meridian` → **Users** → `lab.ws1` → **Groups**  
2. **Join Group** → select **`mnb-workstation-users`**  
3. Confirm the Groups tab lists `mnb-workstation-users`

Alternatively via Admin API:

```bash
TOKEN=$(curl -s -X POST 'http://localhost:8085/realms/master/protocol/openid-connect/token' \
  -d 'client_id=admin-cli' -d 'username=admin' -d 'password=admin' -d 'grant_type=password' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

USER_ID=$(curl -s -H "Authorization: Bearer $TOKEN" \
  'http://localhost:8085/admin/realms/meridian/users?username=lab.ws1&exact=true' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)[0]["id"])')

GROUP_ID=$(curl -s -H "Authorization: Bearer $TOKEN" \
  'http://localhost:8085/admin/realms/meridian/groups?search=mnb-workstation-users' \
  | python3 -c 'import sys,json; print([g for g in json.load(sys.stdin) if g["name"]=="mnb-workstation-users"][0]["id"])')

curl -s -o /dev/null -w '%{http_code}\n' -X PUT \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8085/admin/realms/meridian/users/${USER_ID}/groups/${GROUP_ID}"
```

- **Expect:** HTTP `204` (or UI shows the group).

- **Why:** Workstation reads the `groups` claim from the IdP token — not the IIQ Roles tab.
- **Expect:** `lab.ws1` is a member of `mnb-workstation-users` before Task 6.

### Task 6 — Prove grant (Signed in)

1. Sign out of Workstation fully (and clear Keycloak session / use a fresh private window)  
2. Open [http://localhost:8094/](http://localhost:8094/)  
3. Sign in as `lab.ws1` / `LabUser1!`

- **Why:** sticky OIDC sessions can show a stale deny page if you only refresh.
- **Expect:** **Signed in** / workstation session established (not Access denied).

Save screenshot `02-granted-signed-in.png`.

### Task 7 — Revoke and prove lockout

1. Keycloak Admin → `lab.ws1` → **Groups** → leave / remove **`mnb-workstation-users`**  

API leave (same `TOKEN` / ids as Task 5b):

```bash
curl -s -o /dev/null -w '%{http_code}\n' -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8085/admin/realms/meridian/users/${USER_ID}/groups/${GROUP_ID}"
```

2. If you assigned the IIQ role: open `lab.ws1` → remove **`MNB-Bundle-Workstation-Access`** → Refresh Identity Cube with provisioning if your build expects it  
3. Fresh private window → [http://localhost:8094/](http://localhost:8094/) → sign in as `lab.ws1` / `LabUser1!`

- **Why:** revoke without a denied login is incomplete — same failure class as “temporary forever.”
- **Expect:** **Access denied** again (Keycloak password still works; gate fails).

Save screenshot `03-denied-after-revoke.png`.

### Task 8 — Control check (Helen still works)

1. Fresh window → Workstation → sign in as `helen.ross` / `LabUser1!`  
2. Confirm she is still in Keycloak group `mnb-workstation-users` if needed (seeded)

- **Why:** proves your revoke was scoped to `lab.ws1`, not a broken IdP or deleted group.
- **Expect:** Helen **Signed in**.

Save screenshot `04-helen-control-ok.png`.

### Task 9 — Evidence pack

Write `~/iiq-lab-evidence/sandbox/251/SUMMARY.txt`:

```text
Lesson 251
Subject: lab.ws1
Stack: --enterprise --with=sso
01 Access denied (no group)
02 Signed in (mnb-workstation-users present)
03 Access denied (group removed)
04 Helen control: Signed in
IdentityRequest id (if used): ________
Gate group: mnb-workstation-users
App: http://localhost:8094/
```

- **Expect:** four screenshots + SUMMARY an IR lead can follow without asking you.

## If it fails

| Symptom | Fix |
| --- | --- |
| `:8094` connection refused | Start with `--with=sso`; `docker ps` for `mnb-workstation-portal`; rebuild: `docker compose -f docker-compose.iiq.yml -f docker-compose.enterprise.yml --profile enterprise --profile enterprise-sso up -d --build workstation-portal` |
| Health missing `mnb-workstation-users` | Check compose env `REQUIRED_GROUPS`; recreate workstation-portal container |
| Keycloak login works, always Access denied after grant | Client `workstation-portal` needs `oidc-group-membership-mapper`; wipe/reimport Keycloak volume or add mapper; confirm Groups tab membership **before** new login |
| Redirect / PKCE errors | Use `http://localhost:8094/` not `127.0.0.1`; confirm client redirect `http://localhost:8094/*` |
| User created but login unknown | Realm must be **`meridian`**; password Temporary OFF |
| IIQ role assigned, still denied | Bundle does not magically join Keycloak — complete Task 5b |
| Helen also denied after revoke | You removed the **group object** or broke the mapper — restore group `mnb-workstation-users` and Helen’s membership from realm import |
| Used Helen/Priya/Marcus as subject | Stop — create `lab.ws1` and restart from Task 1 |

## You are done when

- [ ] Stack includes `--with=sso`; `:8094/health` shows `mnb-workstation-users`  
- [ ] `lab.ws1` denied without the group  
- [ ] `lab.ws1` Signed in after grant  
- [ ] `lab.ws1` denied again after revoke  
- [ ] Helen control still Signed in  
- [ ] Evidence folder has three subject states + Helen control + SUMMARY  

## Control note

- **Control:** Workstation entitlement gate (grant → login → revoke lockout)  
- **Owner:** IAM Engineering + Endpoint / Workstation Ops  
- **SLA (lab):** Revoke reflected on next full sign-in (same session after sign-out)  
- **Evidence:** `~/iiq-lab-evidence/sandbox/251/`  
- **Out of scope:** Intune enrollment, PAM laptop admin passwords (Lesson 255)

## Quick check

1. Does a successful Keycloak password prove workstation access? → **No** — app still checks `groups` for `mnb-workstation-users`  
2. Which stack flag starts `:8094`? → `--with=sso` (or `--enterprise-full`)  
3. What proves revoke for real? → Fresh login shows **Access denied** after group removal  
4. Why keep Helen’s control login? → Proves revoke was scoped, not a global IdP outage  
5. Why disposable `lab.ws1`? → Avoid breaking seeded personas used by certs/SoD/other lessons  

## Feedback

Could you reproduce deny → grant → allow → revoke → deny on `:8094` for a brand-new `lab.ws*` user without this page?

If something failed, note the **task number**, whether Keycloak Groups showed `mnb-workstation-users`, and whether you used a fresh private window after grant/revoke.

## Navigate

- Previous: [Lesson 250](250-capstone-bank-day.md)
- Next: [Lesson 252](252-entra-shaped-lifecycle.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
