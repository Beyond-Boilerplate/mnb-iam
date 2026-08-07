# Lesson 217 — Joiner LCM End-to-End

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~95 minutes  
**Prereq:** Lessons 207, 211–212, 216  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 29–34b

> **Why:** A joiner only counts as done when the new hire has real accounts **and** can sign in to a real app — not when a cube merely exists. Capture where the pipeline stalls: HR → cube → birthright LDAP → IdP user → Portal.

## What this is

Joiner automation is two objects you wire yourself (they are often missing after a wipe / partial seed):

| Object | Type | Job |
| --- | --- | --- |
| `MNB-Workflow-Joiner` | Workflow (`IdentityLifecycle`) | Logs the hire, then `refreshIdentity` with promote + provision + correlate |
| `MNB-IdentityTrigger-Joiner` | IdentityTrigger (`create`) | Fires that workflow when a new cube is created |

With `MNB-Workday` authoritative, cube create happens when a fresh HCM worker aggregates and refreshes. The workflow materializes Lesson 216 birthright onto **OpenLDAP** and **Keycloak** (`MNB-Keycloak-IdP` → `mnb-employees` + `portal-users`).

Employee Portal SSO (Lesson 212) should work **from birthright** after provisioning completes — not from a hand-built Keycloak user. CRM/Wire stay request-only.

Classic 29 taught joiner on CSV; here day-one proof is LDAP account + IdP Portal groups + Portal SSO.


## Know these

```text
You create: MNB-Workflow-Joiner + MNB-IdentityTrigger-Joiner
                │
HCM POST worker
  → Aggregate MNB-Workday → cube create
  → Identity Refresh with **Process events**
  → IdentityTrigger → MNB-Workflow-Joiner
  → birthright (OpenLDAP + Keycloak IdP packs)
  → **OpenLDAP Create Form** if policy has no Field scripts
  → OpenLDAP account + all-employees
  → Keycloak user + mnb-employees + portal-users   ← from birthright
  → Employee Portal SSO                            ← done
```

| Layer | What joiner automation does | Manual only if |
| --- | --- | --- |
| Cube | Workday agg + refresh | — |
| Birthright LDAP | Role + provision plan | Complete Create **Form** when OpenLDAP policy has no scripts |
| Birthright IdP | `MNB-IT-IdP-Portal` → Keycloak via `MNB-Keycloak-IdP` | Lesson 216 IdP pack missing / `/idp/health` down |
| Welcome email | — | Nothing — no email step yet (Lesson 232) |

| Workflow step | What it does |
| --- | --- |
| `Log Joiner` | Script log — proves the case ran (`MNB Joiner workflow for …`) |
| `Refresh` | `call:refreshIdentity` with `promoteAttributes`, `provision`, `correlateEntitlements` |

- **Wrong way:** Expecting Portal login before birthright IdP pack exists (finish Lesson 216 Task 1c / 2b first).
- **Wrong way:** Treating a Pending `Refresh identity …` as “IIQ is slow” — usually an OpenLDAP Create Form.
- **Wrong way:** Hand-creating the Keycloak user when birthright already owns `portal-users` — that fights the control model.
- **Wrong way:** Aggregating Workday without **Process events** — cube appears, joiner workflow never starts.

## Intent

- Create `MNB-Workflow-Joiner` and `MNB-IdentityTrigger-Joiner` in the live estate.
- Hire via live HCM; fire the joiner path (or manual fallback).
- Complete OpenLDAP Create provisioning (form) when presented.
- **Verify** Keycloak user + Portal groups came from birthright (not Admin console).
- Prove Portal SSO; document that welcome mail is out of scope today.

## Before you start

- [ ] Lesson 216 birthright includes **both** `MNB-IT-OpenLDAP-Employees` and `MNB-IT-IdP-Portal`
- [ ] `curl -s http://localhost:8091/idp/health` shows `"ok": true`
- [ ] Keycloak `meridian` up; Employee Portal: [http://localhost:8092/](http://localhost:8092/)
- [ ] HCM mock healthy: `curl -sf http://localhost:8091/health`
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/217
```

## Do this

### Task 1 — Create `MNB-Workflow-Joiner`

Confirm it’s missing before you build:

1. **Debug** → Object Browser → type **`Workflow`** → search `MNB-Workflow-Joiner`
2. Or **Setup → Business Processes** → search the same name

If it already exists with steps `Log Joiner` → `Refresh`, skip to Task 2.

#### Option A — Import the shipped workflow (preferred)

1. Open repo file `config/Workflow/MNB-Workflow-Joiner.xml`
2. **Debug → Import** → paste the XML → **Import**
3. Confirm name `MNB-Workflow-Joiner`, type `IdentityLifecycle`

- **Why:** same Start → Log → Refresh → Stop shape Lesson 242 will customize later.
- **Expect:** Business Processes lists the workflow with `Log Joiner` then `Refresh`.

#### Option B — Build it in Business Processes

1. **Setup → Business Processes → New**
2. **Name:** `MNB-Workflow-Joiner` · **Type:** `IdentityLifecycle`
3. Input variables: `identityName`, `identity` (`transient` = true if shown)
4. Steps:

   | Step | Kind | Transition to |
   | --- | --- | --- |
   | `Start` | Start | `Log Joiner` |
   | `Log Joiner` | Script (below) | `Refresh` |
   | `Refresh` | `call:refreshIdentity` (args below) | `Stop` |
   | `Stop` | Stop | — |

```java
import org.apache.commons.logging.LogFactory;
LogFactory.getLog("meridian.lcm").warn("MNB Joiner workflow for " + identityName);
```

| Refresh arg | Value |
| --- | --- |
| `identity` | `ref:identityName` |
| `promoteAttributes` | `true` |
| `provision` | `true` |
| `correlateEntitlements` | `true` |

5. **Save**.

> **Watch out:** Save the workflow **before** wiring the IdentityTrigger.

### Task 2 — Create `MNB-IdentityTrigger-Joiner`

1. Debug → **`IdentityTrigger`** (or Lifecycle Events) → search `MNB-IdentityTrigger-Joiner`
2. If missing: Import `config/IdentityTrigger/MNB-IdentityTrigger-Joiner.xml`, **or** create:
   - Type **`create`**
   - Handler `sailpoint.api.WorkflowTriggerHandler`
   - Workflow name exactly **`MNB-Workflow-Joiner`**
   - Not disabled; owner `spadmin`
3. Re-open and confirm the workflow field still says `MNB-Workflow-Joiner` (not `MNB-Joiner-Workflow`)

- **Why:** aggregation creates the cube; the trigger starts LCM.
- **Expect:** enabled trigger bound to the workflow you just saved.

### Task 3 — Create the joiner in live HCM

```bash
./tools/lab/enterprise/hcm-scenario.sh joiner lab.joiner1 Lab Joiner \
  lab.joiner1@meridiannb.com 'Identity & Access'
```

Or hire in the UI: [http://localhost:8091/hcm/ui](http://localhost:8091/hcm/ui)

- **Why:** production joiners arrive as HR creates — not Debug cube inserts.
- **Expect:** script exits 0; note the returned **worker id** (you need it for Keycloak `employeeId` later).

### Task 4 — Confirm the worker at the source

```bash
curl -s http://localhost:8091/hcm/v1/workers \
  | python3 -m json.tool | grep -A8 lab.joiner1
```

- **Why:** if the worker isn’t in HCM, aggregation cannot invent them.
- **Expect:** active worker; copy `id` / `workerId` (e.g. `MNBD7A78`).

### Task 5 — Aggregate Workday, then Refresh with **Process events**

Lifecycle Events do **not** fire on aggregation alone.

1. **Account Aggregation** on `MNB-Workday`
2. **Setup → Tasks → Refresh Identity Cube**
3. Enable **Process events** (`processTriggers=true`) — plus promote / create identities if needed
4. Optionally filter to `lab.joiner1` → **Save** → **Run Now**

- **Why:** without Process events, Create triggers stay idle.
- **Expect:** cube `lab.joiner1` **and** a joiner workflow launch (Task 6).

> **Watch out:** Re-agg of an existing cube will **not** re-fire Create. Use Task 7 or a new username.

### Task 6 — Watch the joiner workflow

```bash
docker logs mnb-identityiq 2>&1 | grep -i "MNB Joiner workflow"
```

Also check Task Results / Monitor for `MNB-Workflow-Joiner`.

- **Expect:** log line for `lab.joiner1`, or go to Task 7.

### Task 7 — Manual fallback if trigger didn’t fire

1. **Setup → Business Processes → MNB-Workflow-Joiner** → Run / Launch
2. `identityName` = `lab.joiner1`
3. Confirm the case starts (it may still pause on a Form — that is Task 9)

- **Expect:** workflow started; treat missed auto-fire as a finding.

### Task 8 — Confirm birthright **assigned** on the cube

Open `lab.joiner1` → **Roles**:

- `MNB-Bundle-Birthright-Employee` present

OpenLDAP under **Application Accounts** may still be missing — that is normal until the Create Form is completed.

- **Why:** role assignment and account create are sequential; the form is the gate between them.
- **Expect:** birthright role yes; LDAP link maybe not yet.

### Task 9 — Complete the OpenLDAP Create provisioning Form

When birthright needs a **new** OpenLDAP account and the Create policy has no FieldValue scripts, IIQ opens a **Form** work item and leaves `Refresh identity lab.joiner1` in **Pending**.

1. Check the bell / **My Work → Work Items** for  
   `Automatic provisioning form for lab.joiner1`  
   (or “Complete provisioning form for Lab”).
2. Fill **MNB-OpenLDAP** required fields with lab-standard values:

   | Field | Value |
   | --- | --- |
   | User DN | `uid=lab.joiner1,ou=people,dc=meridiannb,dc=com` |
   | Password | `LabUser1!` |
   | Full Name | `Lab Joiner` |
   | First Name | `Lab` |
   | Last Name | `Joiner` |

3. **Complete** / Submit the work item.
4. Confirm Task Result leaves Pending (Success).

- **Why:** without this form, provisioning never creates the LDAP entry — birthright stays metadata-only.
- **Expect:** work item gone; refresh completes.

> **Watch out:** Pending with empty Host/Result is usually **waiting on you**, not a hung server. Workflow summary step name is often `Do Provisioning Forms`.

### Task 10 — Prove the OpenLDAP account (not Keycloak)

```bash
docker exec mnb-openldap ldapsearch -x -H ldap://localhost \
  -D 'cn=admin,dc=meridiannb,dc=com' -w admin \
  -b 'ou=people,dc=meridiannb,dc=com' '(uid=lab.joiner1)' dn cn memberOf
```

Optional: re-run OpenLDAP account (+ group) aggregation, then confirm the link on the cube.

- **Why:** this is what birthright actually provisioned.
- **Expect:** DN present; ideally `memberOf: cn=all-employees,…`.

### Task 11 — Prove Keycloak came from birthright (not Admin console)

Do **not** hand-create the user in Keycloak Admin unless Task 1c/2b from Lesson 216 were skipped.

1. Cube `lab.joiner1` → Application Accounts → confirm **`MNB-Keycloak-IdP`** link with `mnb-employees` and `portal-users`.
2. Or query the facade:

```bash
curl -s 'http://localhost:8091/idp/scim/v2/Users?filter=userName%20eq%20%22lab.joiner1%22' \
  | python3 -m json.tool
```

3. Optional: Keycloak Admin → realm `meridian` → Users → `lab.joiner1` → Groups tab (read-only proof).

- **Why:** Portal SSO must be attributable to birthright IdP packs — the control Lesson 216 built.
- **Expect:** user exists with both groups; password is `LabUser1!` from the Create policy default.

> **Watch out:** If the IdP account is missing, fix Lesson 216 (`MNB-IT-IdP-Portal` on birthright, `/idp/health` ok, refresh with provisioning) — don’t paper over it with a manual Keycloak user unless you are documenting a temporary workaround.

### Task 12 — Portal SSO acceptance test

Only after Task 10 (LDAP) and Task 11 (IdP):

1. Open [http://localhost:8092/](http://localhost:8092/)
2. Sign in as `lab.joiner1` / `LabUser1!`
3. Screenshot under `~/iiq-lab-evidence/sandbox/217/` (no passwords)

- **Why:** end-to-end acceptance — cube + LDAP + IdP birthright + app.
- **Expect:** successful Portal session.

### Task 13 — Mailpit: confirm **no** welcome mail (honest gap)

Open [http://localhost:8025](http://localhost:8025).

`MNB-Workflow-Joiner` today is only Log → Refresh. There is **no** email step.

- **Why:** empty Mailpit is not a joiner failure — document for Lesson 232.
- **Expect:** **no** joiner welcome message. Note: `no email step in MNB-Workflow-Joiner`.

## If it fails

| Symptom | Fix |
| --- | --- |
| `Refresh identity …` Pending forever | **My Work** → Complete OpenLDAP Create Form (Task 9) |
| Form fields unknown | DN `uid=<username>,ou=people,dc=meridiannb,dc=com`, password `LabUser1!` |
| No Keycloak user after joiner | Lesson 216: `MNB-IT-IdP-Portal` on birthright; `/idp/health` ok; refresh with provisioning |
| `/idp/health` ok:false | `./tools/lab/enterprise/keycloak-enable-iiq-provisioner.sh` + rebuild connector-mock |
| Portal login fails | Missing `portal-users` on IdP link; or OpenLDAP Form never completed |
| Portal auth OK but access denied | Birthright IdP pack missing `portal-users` |
| Zero workflow launches | Process events off; wrong trigger workflow name; Task 7 |
| Looking for welcome mail | Task 13 — expect none |

## You are done when

- [ ] `MNB-Workflow-Joiner` + `MNB-IdentityTrigger-Joiner` in place
- [ ] `lab.joiner1` cube from live HCM
- [ ] OpenLDAP account proven (`ldapsearch`)
- [ ] Keycloak user + `portal-users` / `mnb-employees` from **birthright** (Task 11)
- [ ] Employee Portal SSO succeeds
- [ ] Evidence notes: no welcome mail in Mailpit

## Control note

- **Control:** Joiner LCM (HR → identity → directory + IdP birthright → usable app access)
- **Owners:** HR Ops + IAM Ops (trigger/workflow) + IdP provisioner (`MNB-Keycloak-IdP`)
- **SLA (lab):** same session
- **Evidence:** `~/iiq-lab-evidence/sandbox/217/` — HCM worker id, LDAP dn, IdP SCIM/groups proof, Portal screenshot, Mailpit gap note

## Quick check

1. What must never be birthright on day one? → Wire / CRM elevated / BreakGlass
2. Why is a Pending `Refresh identity lab.joiner1` often not “slow”? → waiting on OpenLDAP Create **Form**
3. Does joiner still require hand-creating a Keycloak user? → **No** — if Lesson 216 IdP birthright pack is in place
4. Which Application provisions live Keycloak for birthright? → `MNB-Keycloak-IdP` (not `MNB-Okta`)
5. Should Mailpit show a joiner welcome after this workflow? → **No** — Lesson 232

## Feedback

Could you explain the three gates (Process events → LDAP Form → IdP birthright provision) without opening this file? If Portal failed, note whether LDAP, IdP groups, or `portal-users` was the miss.

## Navigate

- Previous: [Lesson 216](216-birthright-roles-live.md)
- Next: [Lesson 218](218-mover-lcm-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
