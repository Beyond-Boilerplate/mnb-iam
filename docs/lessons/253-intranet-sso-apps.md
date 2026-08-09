# Lesson 253 — Intranet SSO Apps (HR + Finance)

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~70 minutes  
**Prereq:** Lesson 251  
**Stack:** `./tools/lab/docker/up.sh --enterprise --with=sso`

**Maps to classic track:** logical apps / SSO estate (classic 73 narrative)

> **Why:** A bank has many internal websites; each needs its own grant and the same revoke proof. If HR and Finance share one group, you cannot prove least privilege between them.

## What this is

Two more SSO gates share the Workstation (Lesson 251) code path (`mnb-sso-gate:local`). Same OIDC pattern, **different** required Keycloak groups:

| App | URL | OIDC client | Required group | IIQ role (catalog) |
| --- | --- | --- | --- | --- |
| HR Self-Service | [http://localhost:8095/](http://localhost:8095/) | `hr-intranet` | `mnb-hr-intranet` | `MNB-Bundle-HR-Intranet` |
| Finance Portal | [http://localhost:8096/](http://localhost:8096/) | `finance-portal` | `mnb-finance-portal` | `MNB-Bundle-Finance-Portal` |

```text
Browser → HR (:8095) or Finance (:8096)
       → Keycloak meridian login
       → groups claim must include THAT app's required group
       → Signed in  OR  Access denied
```

Default `--enterprise` does **not** start these ports. You need **`--with=sso`**.

Nothing for this drill’s subject is pre-granted. You will:

1. Create disposable **`lab.intranet1`** without HR/Finance groups  
2. Prove **denied on both** apps  
3. Grant **HR only** → HR works, Finance still denies  
4. Grant Finance → both work  
5. Revoke Finance → Finance denies, HR still works  
6. Confirm Employee Portal tiles (Helen control) land on the right ports  

> **Watch out:** Granting `mnb-hr-intranet` must **not** open Finance. If it does, the apps are misconfigured — stop and fix `REQUIRED_GROUPS` / health JSON before continuing.

## Know these

```text
Stack: --enterprise --with=sso
  → curl :8095/health and :8096/health → distinct requiredGroups
  → Create lab.intranet1 + Keycloak user (no HR/Finance groups)
  → Deny on both apps
  → Join mnb-hr-intranet only → HR Signed in; Finance Access denied
  → Join mnb-finance-portal → both Signed in
  → Leave mnb-finance-portal → Finance denied; HR still Signed in
  → Helen Portal tiles → correct ports (control)
```

| Term | Plain English | Meridian example |
| --- | --- | --- |
| **Independent gate** | Each app checks its own group | HR ≠ Finance entitlement |
| **requiredGroups** | Exact strings in `/health` JSON | Must match Keycloak group **name** (no leading `/`) |
| **Shared image** | Same container image, different env | `mnb-sso-gate:local` |
| **Least privilege** | Grant only what the job needs | HR-only before Finance |

- **Wrong way:** Assuming one intranet group opens every internal site.  
- **Wrong way:** Using Helen/Priya as the grant/revoke subject (Helen is control-only here).  
- **Wrong way:** Matching Keycloak path `/mnb-hr-intranet` including the slash in evidence when the app checks `mnb-hr-intranet`.  
- **Wrong way:** Skipping the HR-only middle state — that state is the whole point.

## Intent

- Prove independent deny/grant/revoke on HR vs Finance for `lab.intranet1`.  
- Show HR-only access does not leak to Finance.  
- Leave four login-state screenshots + health JSON in evidence.

## Before you start

Complete every checkbox. Do not skip into Task 1 until these are true.

- [ ] Stack with SSO pack:

```bash
./tools/lab/docker/up.sh --enterprise --with=sso
```

- [ ] Lesson 251 pattern understood (authn vs `groups` authz on `mnb-sso-gate`)
- [ ] IIQ: [http://localhost:8080/identityiq](http://localhost:8080/identityiq) — `spadmin` / `admin`
- [ ] Keycloak Admin: [http://localhost:8085/admin/](http://localhost:8085/admin/) — `admin` / `admin` — realm **`meridian`**
- [ ] Both gates healthy:

```bash
curl -sf http://127.0.0.1:8095/health | python3 -m json.tool
curl -sf http://127.0.0.1:8096/health | python3 -m json.tool
```

  - **Expect:** HR `"requiredGroups": ["mnb-hr-intranet"]`, `"clientId": "hr-intranet"`  
  - **Expect:** Finance `"requiredGroups": ["mnb-finance-portal"]`, `"clientId": "finance-portal"`

- [ ] Employee Portal up (tile check): [http://localhost:8092/](http://localhost:8092/)
- [ ] Evidence dir:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/253
```

## Do this

### Task 1 — Capture health JSON (exact group strings)

```bash
curl -sf http://127.0.0.1:8095/health | python3 -m json.tool \
  | tee ~/iiq-lab-evidence/sandbox/253/health-hr.json
curl -sf http://127.0.0.1:8096/health | python3 -m json.tool \
  | tee ~/iiq-lab-evidence/sandbox/253/health-finance.json
```

- **Why:** `/health` is the source of truth for the string the app checks — not memory, not a wiki guess.
- **Expect:** two different `requiredGroups` values.

### Task 2 — Create disposable `lab.intranet1`

Never use Helen, Priya, or Marcus as the intranet subject.

1. HCM joiner:

```bash
./tools/lab/enterprise/hcm-scenario.sh joiner lab.intranet1 Lab Intranet \
  lab.intranet1@meridiannb.com 'Human Resources'
```

2. Confirm HCM + create IIQ cube (Aggregate **`MNB-Workday`** → Refresh Identity Cube).

3. Keycloak user **without** intranet groups:

- Birthright IdP OK for `portal-users` / `mnb-employees`  
- Keycloak Admin → `lab.intranet1` → **Groups** must **not** list `mnb-hr-intranet` or `mnb-finance-portal`  
- Password `LabUser1!`, Temporary OFF  
- If user missing: Add user on realm **`meridian`** with email `lab.intranet1@meridiannb.com`

- **Why:** baseline must be deny-on-both.
- **Expect:** IdP user exists; HR/Finance groups absent.

### Task 3 — Baseline: denied on both apps

Use a private window; prefer `localhost` over `127.0.0.1`.

1. Open [http://localhost:8095/](http://localhost:8095/) → sign in as `lab.intranet1` / `LabUser1!`  
   - **Expect:** **Access denied** after IdP login.  
   - Screenshot `01-hr-denied.png`

2. Sign out fully / new private window  
3. Open [http://localhost:8096/](http://localhost:8096/) → same credentials  
   - **Expect:** **Access denied**.  
   - Screenshot `02-finance-denied.png`

- **Why:** without dual deny, later “Finance still denied” is meaningless.
- **Expect:** both apps deny before any grant.

### Task 4 — Verify-or-import IIQ catalog roles

1. **Setup → Roles** → confirm `MNB-Bundle-HR-Intranet` and `MNB-Bundle-Finance-Portal` exist and are **requestable**  
2. If missing:

```bash
./tools/lab/enterprise/seed-enterprise.sh
```

Or import:

- `config/Bundle/MNB-Bundle-HR-Intranet.xml`  
- `config/Bundle/MNB-Bundle-Finance-Portal.xml`

- **Why:** production story is requestable catalog items per app — not one mega “intranet” role.
- **Expect:** two distinct requestable roles.

> **Tip:** Login proof still requires the matching Keycloak group (same honesty as Lesson 251). Use IIQ requests for audit trail if LCM works; Tasks 5–7 require the groups either way.

### Task 5 — Grant HR only (least-privilege middle state)

#### 5a — Optional IIQ request for HR

As `spadmin`, Request Access on behalf of `lab.intranet1` → `MNB-Bundle-HR-Intranet` → justification `LAB-253 HR only` → complete approvals if mapped. Set Manager `sanjay.kapoor` if Manager Approval stalls.

#### 5b — Keycloak group (required)

1. Keycloak → Users → `lab.intranet1` → **Groups** → Join **`mnb-hr-intranet` only**  
2. Do **not** join `mnb-finance-portal` yet  

API option:

```bash
TOKEN=$(curl -s -X POST 'http://localhost:8085/realms/master/protocol/openid-connect/token' \
  -d 'client_id=admin-cli' -d 'username=admin' -d 'password=admin' -d 'grant_type=password' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

USER_ID=$(curl -s -H "Authorization: Bearer $TOKEN" \
  'http://localhost:8085/admin/realms/meridian/users?username=lab.intranet1&exact=true' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)[0]["id"])')

HR_GID=$(curl -s -H "Authorization: Bearer $TOKEN" \
  'http://localhost:8085/admin/realms/meridian/groups?search=mnb-hr-intranet' \
  | python3 -c 'import sys,json; print([g for g in json.load(sys.stdin) if g["name"]=="mnb-hr-intranet"][0]["id"])')

curl -s -o /dev/null -w 'HR join %{http_code}\n' -X PUT \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8085/admin/realms/meridian/users/${USER_ID}/groups/${HR_GID}"
```

3. Fresh private window → HR `:8095` as `lab.intranet1`  
   - **Expect:** **Signed in**  
   - Screenshot `03-hr-only-signed-in.png`

4. Fresh window → Finance `:8096` as `lab.intranet1`  
   - **Expect:** still **Access denied**  
   - Screenshot `04-finance-still-denied-hr-only.png`

- **Why:** this pair of screenshots is the least-privilege proof.
- **Expect:** HR yes, Finance no — same user, same session window of time.

> **Watch out:** If Finance also opens after HR-only grant, stop — clients may be sharing a group mapper bug or wrong `REQUIRED_GROUPS`. Fix before granting Finance.

### Task 6 — Grant Finance; prove both work

1. Join Keycloak group **`mnb-finance-portal`** (optional IIQ request for `MNB-Bundle-Finance-Portal`)  

```bash
FIN_GID=$(curl -s -H "Authorization: Bearer $TOKEN" \
  'http://localhost:8085/admin/realms/meridian/groups?search=mnb-finance-portal' \
  | python3 -c 'import sys,json; print([g for g in json.load(sys.stdin) if g["name"]=="mnb-finance-portal"][0]["id"])')

curl -s -o /dev/null -w 'FIN join %{http_code}\n' -X PUT \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8085/admin/realms/meridian/users/${USER_ID}/groups/${FIN_GID}"
```

2. Fresh logins to `:8095` and `:8096` as `lab.intranet1`  
   - **Expect:** **Signed in** on both  
   - Screenshots `05-hr-both-ok.png`, `06-finance-both-ok.png`

- **Why:** proves Finance grant is additive, not a replacement for HR.
- **Expect:** both gates green.

### Task 7 — Revoke Finance only; HR remains

1. Remove **`mnb-finance-portal`** from `lab.intranet1` (leave `mnb-hr-intranet`)  

```bash
curl -s -o /dev/null -w 'FIN leave %{http_code}\n' -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8085/admin/realms/meridian/users/${USER_ID}/groups/${FIN_GID}"
```

2. If you assigned the IIQ Finance role, remove it from the cube  
3. Fresh Finance login → **Access denied** (`07-finance-revoked.png`)  
4. Fresh HR login → still **Signed in** (`08-hr-still-ok-after-fin-revoke.png`)

- **Why:** revoke must be per-app; a global “remove all intranet” would fail least privilege.
- **Expect:** Finance locked out; HR unaffected.

### Task 8 — Employee Portal tiles (Helen control)

1. Sign in to [http://localhost:8092/](http://localhost:8092/) as `helen.ross` / `LabUser1!`  
2. Open Workstation / HR / Finance tiles if present  
3. Confirm they target `:8094`, `:8095`, `:8096` respectively (hover or landing URL)

- **Why:** operators discover apps from Portal; wrong links are an access defect.
- **Expect:** each tile lands on the matching gate port. Note gaps honestly if a tile is missing in your build.

Write `~/iiq-lab-evidence/sandbox/253/SUMMARY.txt`:

```text
Lesson 253
Subject: lab.intranet1
01/02 deny both
03/04 HR-only (HR ok, Finance denied)
05/06 both granted
07/08 Finance revoked (Finance denied, HR ok)
Helen tiles: OK / GAP ________
```

## If it fails

| Symptom | Fix |
| --- | --- |
| `:8095` / `:8096` down | `--with=sso`; `docker compose -f docker-compose.iiq.yml -f docker-compose.enterprise.yml --profile enterprise --profile enterprise-sso up -d --build hr-intranet finance-portal` |
| Wrong `requiredGroups` | Health JSON wins — fix compose env `REQUIRED_GROUPS`; recreate containers |
| Always denied after group join | Groups mapper on clients `hr-intranet` / `finance-portal`; fresh login after join; realm `meridian` |
| Finance opens after HR-only grant | Misconfiguration — compare both `/health` outputs; confirm Keycloak memberships; do not continue |
| Redirect URI errors | Use `http://localhost:8095/` and `http://localhost:8096/` (not `127.0.0.1`) |
| Realm missing clients | Reimport `lab-data/enterprise/keycloak/meridian-realm.json` (wipe Keycloak volume only if you accept persona reset) |
| Used Priya as subject | Stop — create `lab.intranet1` and restart from Task 2 |

## You are done when

- [ ] Health JSON shows distinct HR vs Finance groups  
- [ ] `lab.intranet1` denied on both before grant  
- [ ] HR-only state proven (HR ok, Finance denied)  
- [ ] Both granted, then Finance-only revoke proven (HR still ok)  
- [ ] Evidence has health files + state screenshots + SUMMARY  

## Control note

- **Control:** Independent least-privilege gates across intranet apps  
- **Owner:** IAM Engineering + HR/Finance App Owners  
- **SLA (lab):** Grant/revoke on one app never leaks entitlement to the other  
- **Evidence:** `~/iiq-lab-evidence/sandbox/253/`  
- **Related:** Lesson [251](251-workstation-grant-revoke.md) (same gate pattern, workstation group)

## Quick check

1. Does the HR group grant Finance? → **No** — independent `requiredGroups`  
2. Where is the exact group string documented at runtime? → Each app’s `/health` JSON  
3. What image do both apps share? → `mnb-sso-gate:local` (different env/config)  
4. Which middle state is mandatory? → HR granted, Finance still denied  
5. Stack flag for `:8095`/`:8096`? → `--with=sso`  

## Feedback

Could you prove HR-only access (and Finance still denied) for a new `lab.intranet*` user from memory?

If something failed, note the **task number**, both `/health` `requiredGroups`, and which Keycloak groups were on the user when you captured the screenshot.

## Navigate

- Previous: [Lesson 252](252-entra-shaped-lifecycle.md)
- Next: [Lesson 254](254-password-reset-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
