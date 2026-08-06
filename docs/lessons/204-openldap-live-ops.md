# Lesson 204 — Operate Live OpenLDAP

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~55 minutes  
**Prereq:** Lesson **207** (Workday cubes — Warehouse must have `helen.ross`)  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 58

> **Why:** Validate the directory bind and search yourself before you ever blame IIQ’s aggregation for missing accounts. This stands in for classic 58 (OpenLDAP connector fundamentals), but against a **live, mutable** directory instead of a static CSV.

## What this is

`MNB-OpenLDAP` is a real **OpenLDAP - Direct** connector (`sailpoint.connector.LDAPConnector`) pointed at the `openldap` container on port `389`.

| Setting | Value |
| --- | --- |
| Service bind | `cn=svc-iiq-provision,ou=service,dc=meridiannb,dc=com` / `Provision1!` |
| People search | `ou=people,dc=meridiannb,dc=com` (`inetOrgPerson`) |
| Groups search | `ou=groups,dc=meridiannb,dc=com` (`groupOfUniqueNames`) |

Same Application *type* as Core Path — but here the directory is alive. **phpLDAPadmin** and raw **`ldapsearch`** let you inspect and change it, then watch IIQ’s aggregation catch up. That loop (change directory → aggregate → see cube change) is the point of the Enterprise Sandbox Path.

## Know these

| Who | Bind DN | Password | Purpose |
| --- | --- | --- | --- |
| You (debug) | `cn=admin,dc=meridiannb,dc=com` | `admin` | Directory root — humans only |
| IIQ (real) | `cn=svc-iiq-provision,ou=service,dc=meridiannb,dc=com` | `Provision1!` | Least-privilege service account |

| Lab object | Name | Notes |
| --- | --- | --- |
| Application | `MNB-OpenLDAP` | Live OpenLDAP - Direct |
| Account Aggregation task | `MNB-Acct-Aggregation` | Create if missing; apps = `MNB-HR`, `MNB-OpenLDAP` |
| Account Group Aggregation task | `MNB-OpenLDAP-Group-Aggregation` | Create if missing; app = `MNB-OpenLDAP` only |

- **Correlation key:** LDAP `employeeNumber` (e.g. `MNB00001` for Helen) → identity `userId`. Separate from login/display attribute `uid`.
- Aggregation runs in **two passes**: accounts, then groups. A missed group pass looks like “aggregation ran but no entitlements.”
- Aggregation lives under **Setup → Tasks**. Application Definition only has **Test Connection** — it does **not** create or list those tasks.
- Seed *should* import the tasks, but a wipe often leaves **Tasks → search `MNB` = empty**. If empty, **create both before Run Now**.
- **Wrong way:** Letting IIQ bind as `cn=admin` “because it’s easier” — real banks never give IIQ directory root.

## Intent

- Read a real LDAP entry two ways (GUI + `ldapsearch`) and get the same answer.
- Run account **and** group aggregation against `MNB-OpenLDAP`.
- Diagnose and fix a missing `employeeNumber`↔`userId` correlation link by hand.
- Know which bind DN is for humans vs what IIQ actually uses.

## Before you start

- [ ] Lesson **207** complete — Warehouse has `helen.ross` (Workday cube)
- [ ] `MNB-OpenLDAP` Application exists (definition from seed; you aggregate in this lesson)
- [ ] **Setup → Tasks** → search `MNB`. If empty (“No data to display”), you will create tasks in Task 4
- [ ] `ldapsearch` available (`brew install openldap`) **or** use `docker exec mnb-openldap ldapsearch`
- [ ] phpLDAPadmin at http://localhost:8090/
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/204
```

## Do this

### Task 1 — Read Helen in phpLDAPadmin

GUI ground truth before you trust any CLI output or IIQ aggregation.

1. Open http://localhost:8090/
2. Login DN `cn=admin,dc=meridiannb,dc=com` / `admin`
3. Browse `ou=people,dc=meridiannb,dc=com` → `uid=helen.ross`

- **Why:** validate the directory yourself before blaming IIQ for missing accounts.
- **Expect:** `employeeNumber` reads `MNB00001`, matching the identity master.

### Task 2 — Reproduce the same lookup with ldapsearch

Same kind of query IIQ’s connector runs under the hood — different bind identity later.

```bash
ldapsearch -x -H ldap://localhost:389 \
  -b ou=people,dc=meridiannb,dc=com \
  -D cn=admin,dc=meridiannb,dc=com -w admin \
  '(uid=helen.ross)'
```

- **Why:** CLI and GUI must agree — if they don’t, stop and fix the directory before aggregating.
- **Expect:** `employeeNumber`, `mail`, and `title` match phpLDAPadmin exactly.

> **Tip:** No host `ldapsearch`? Prefix with `docker exec mnb-openldap` and drop `-H ldap://localhost:389` (search inside the container).

### Task 3 — Confirm the Application’s real bind DN

Least privilege limits blast radius if the connector credential leaks. Banks never give IIQ directory root.

1. **Applications → Application Definition → MNB-OpenLDAP**
2. Open connection / bind settings and confirm IIQ uses the **service** DN — not admin

| Who | Bind DN | Password | Purpose |
| --- | --- | --- | --- |
| You (debug) | `cn=admin,dc=meridiannb,dc=com` | `admin` | Directory root — humans only |
| IIQ (real) | `cn=svc-iiq-provision,ou=service,dc=meridiannb,dc=com` | `Provision1!` | Least-privilege service account |

- **Why:** you need both credentials in your head for the rest of this path — admin for debug, service for the connector.
- **Expect:** Application bind matches the service row above.

### Task 4 — Test Connection, create tasks if missing, run both

Test Connection only proves bind/search config. Accounts and groups need separate TaskDefinitions.

1. **Applications → Application Definition → MNB-OpenLDAP → Test Connection**
   - **Expect:** connection succeeds (service bind works)
2. **Setup → Tasks**, search `MNB`
   - If you see `MNB-Acct-Aggregation` and `MNB-OpenLDAP-Group-Aggregation` → skip to step 4
   - If the grid is empty → create both **before** Run Now:
     - **New Task → Account Aggregation** → name `MNB-Acct-Aggregation` → select `MNB-OpenLDAP` (and `MNB-HR` if listed) → **Save**
     - **New Task → Account Group Aggregation** → name `MNB-OpenLDAP-Group-Aggregation` → select `MNB-OpenLDAP` → **Save**
3. Refresh the Tasks list and confirm both names appear
4. Open each task → **Run Now** → wait for both Task Results

- **Why:** skipping the group task leaves entitlements missing even when accounts look fine.
- **Expect:** both Task Results succeed.

> **Watch out:** There is no “Run Aggregation” button on the Application page. Aggregation lives under **Setup → Tasks**.

### Task 5 — Confirm Helen’s OpenLDAP link on her cube

1. **Identities → Identity Warehouse → helen.ross**
2. Check Application Accounts for `MNB-OpenLDAP`

- **Why:** a missing link here is usually a **correlation** failure, not aggregation — the account may have landed as an *uncorrelated* link.
- **Expect:** link present, or continue to Task 6.

### Task 6 — Fix correlation if the link is missing

Lesson 214 formalizes this with rules — doing it by hand once shows what the rule will later automate.

1. Confirm LDAP `employeeNumber` (`MNB00001`) matches identity `userId`
2. Re-run Identity Refresh with “correlate accounts” enabled, **or**
3. Manually correlate from **Identities → Uncorrelated Accounts**

- **Why:** aggregation creates the account; correlation attaches it to the cube.
- **Expect:** `MNB-OpenLDAP` link now appears on Helen’s cube.

### Task 7 — Change something live, then re-aggregate

Proves the feedback loop every later lesson depends on: change directory → aggregate → see cube change.

1. In phpLDAPadmin: add Helen to a group, **or** edit her `title`
2. Re-run account **and** group aggregation
3. Refresh Helen’s cube

- **Why:** live mutable directory is the point of this path vs static CSV.
- **Expect:** the change lands on her cube after re-aggregation.

### Task 8 — Revert the test change

A stray edit is a common source of “why does my aggregation look different from the docs” two lessons later.

1. Revert the phpLDAPadmin change
2. Re-aggregate once more

- **Why:** leave the directory in its seeded state.
- **Expect:** Helen’s cube reflects the reverted value.

### Task 9 — Close with asserts

```bash
./tools/lab/enterprise/verify-lesson.sh 204
```

- **Why:** hard checks catch a dead directory or missing app before you move on.
- **Expect:** hard asserts PASS.

## If it fails

| Symptom | Fix |
| --- | --- |
| Test Connection: invalid credentials | Service DN/password out of sync — re-run `./tools/lab/enterprise/seed-enterprise.sh` |
| Can’t find Aggregation under the Application | Those are TaskDefinitions — **Setup → Tasks**; create per Task 4 if missing |
| Account aggregation clean but zero accounts | Confirm search base has entries: `ldapsearch … '(objectClass=inetOrgPerson)' dn` |
| Groups aggregate but look unmanaged | Refresh **Setup → Entitlement Catalog** for this app’s group object type |
| Helen’s link looks stale | Re-run `MNB-Acct-Aggregation` (and group task if entitlements moved) — Test Connection does not refresh cubes |
| `ldapsearch: command not found` | `brew install openldap` or `docker exec mnb-openldap ldapsearch …` |

## You are done when

- [ ] `ldapsearch` and phpLDAPadmin agree on Helen’s LDAP attributes
- [ ] Both account and group aggregation Task Results succeed
- [ ] Helen’s cube shows an `MNB-OpenLDAP` account link
- [ ] A manual phpLDAPadmin change appeared after re-aggregation (then you reverted it)
- [ ] `./tools/lab/enterprise/verify-lesson.sh 204` hard asserts PASS

## Control note

- **Control:** Directory aggregation and correlation accuracy
- **Owner:** IAM Ops / Directory team
- **SLA (lab):** correlation gaps fixed same session; production target is same-day orphan triage
- **Evidence:** `~/iiq-lab-evidence/sandbox/204/` — `ldapsearch` output, Task Result ids, before/after cube screenshot

## Quick check

1. Which bind does IIQ actually use? → `cn=svc-iiq-provision,ou=service,dc=meridiannb,dc=com`
2. Which attribute is correlation vs login/display? → `employeeNumber` correlates; `uid` is login/display
3. Why can group entitlements look “unmanaged” after a clean aggregation? → Entitlement Catalog for that object type wasn’t refreshed

## Feedback

Could you explain admin bind vs service bind, and where aggregation tasks live, without looking? If aggregation “worked” but Helen had no link, note whether the account was under **Uncorrelated Accounts** — that distinction is the lesson.

## Navigate

- Previous: [Lesson 207](207-hcm-workday-shaped.md) (required cubes) · [Lesson 203](203-mailpit-iiq-email.md) if you did mail first
- Next: [Lesson 205](205-samba-ad-live-ops.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
