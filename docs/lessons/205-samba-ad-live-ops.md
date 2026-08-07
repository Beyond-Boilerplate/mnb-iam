# Lesson 205 — Operate Samba AD

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~65 minutes  
**Prereq:** Lesson **207** (204 strongly recommended — dual-link cube proof)  
**Stack:** `./tools/lab/docker/up.sh --enterprise --with=ad`

**Maps to classic track:** 56–57

> **Why:** AD-shaped login and group membership, proven live, without requiring IQService. Document exactly what this AD integration does **not** do — ops and Lesson 206 will hit those gaps hard if you leave them as a shrug.

## What this is

`samba-ad` (`nowsci/samba-domain`) is a real Samba Active Directory domain controller for domain **`MERIDIANNB.COM`**. It speaks genuine LDAP and Kerberos — not a CSV pretending to be AD.

IIQ connects through **`MNB-ActiveDirectory-Live`**, an **OpenLDAP - Direct** connector bound as:

| Setting | Value |
| --- | --- |
| Bind | `CN=Administrator,CN=Users,DC=meridiannb,DC=com` / `Password1!` |
| People | `OU=People,DC=meridiannb,DC=com` |
| Groups | `CN=Users,DC=meridiannb,DC=com` (`memberOf` managed) |
| Host LDAP port | **`3890`** (IIQ uses Docker-internal `samba-ad:389`) |

This is deliberately **not** the native **Active Directory - Direct** connector. That path needs **IQService** for password operations, which this local sandbox intentionally does not run. You get real AD-shaped account/group aggregation and enable/disable. You do **not** get IQService-mediated password reset — that gap is intentional, not a bug.

## Know these

| Idea | Detail |
| --- | --- |
| Ready signal | `docker inspect -f '{{.State.Health.Status}}' mnb-samba-ad` must read **`healthy`** |
| Seeded groups | `MNB-Employees`, `MNB-Managers`, `Wire-Initiators`, `Wire-Approvers` |
| Correlation | AD `employeeNumber` → identity `userId` |
| Login key | `sAMAccountName` → identity `name` |
| `userAccountControl` | `512` = normal active; `514` = disabled (terminated personas) |
| Admin password | `Password1!` (`DOMAINPASS`) — must match Application XML |

- Aggregation tasks (same pattern as Lesson 204): create under **Setup → Tasks** if seed left them missing.
- **Wrong way:** Assuming native Active Directory - Direct belongs in this lab — it needs IQService; `MNB-ActiveDirectory-Live` is the deliberate LDAP stand-in.

## Intent

- Wait for a real DC to finish bootstrapping and confirm **healthy**, not just “container running.”
- Seed Samba users/groups from the same identity master, knowing the seed is best-effort.
- Aggregate `MNB-ActiveDirectory-Live` and correlate to Helen’s cube alongside OpenLDAP.
- State precisely what this stand-in can and cannot do vs production AD + IQService.

## Before you start

- [ ] Lesson **207** complete — Warehouse has `helen.ross` (Workday cube)
- [ ] Lesson 202 seed complete (generator + `seed-enterprise.sh` already run)
- [ ] Lesson 204 done if you want the dual-link cube proof (Helen already has `MNB-OpenLDAP`)
- [ ] `mnb-samba-ad` present (`docker ps | grep samba`)
- [ ] Patience for a **2+ minute** first-boot domain bootstrap
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/205
```

## Do this

### Task 1 — Wait for Samba healthy

First boot can take 2+ minutes to initialize a domain. “Container running” is not “ready.”

```bash
docker inspect -f '{{.State.Health.Status}}' mnb-samba-ad
```

- **Why:** aggregation against a half-bootstrapped DC fails in confusing ways.
- **Expect:** output reads `healthy` before you continue.

> **Watch out:** On Apple Silicon, the image often needs `platform: linux/amd64` emulation. Give it the full healthcheck `start_period` before troubleshooting.

### Task 2 — Seed users and groups

Creates `OU=People` and four groups via `samba-tool`, then loops the CSV from Lesson 202’s generator. Best-effort — keep going on benign errors.

```bash
./tools/lab/enterprise/seed-samba.sh
```

- **Why:** IIQ can only aggregate what the DC actually has.
- **Expect:** script completes; a few “already exists” lines are normal.

### Task 3 — Prove Helen exists on the DC (independent of IIQ)

Split the problem: DC seed vs IIQ aggregate. If the DC is empty, don’t debug the Application yet.

First via Samba’s own tool:

```bash
docker exec mnb-samba-ad samba-tool user show helen.ross
```

Then the same person over LDAP on the **Samba** host port (not OpenLDAP’s `:389`):

```bash
ldapsearch -x -H ldap://localhost:3890 \
  -b 'OU=People,DC=meridiannb,DC=com' \
  -D 'CN=Administrator,CN=Users,DC=meridiannb,DC=com' -w 'Password1!' \
  '(sAMAccountName=helen.ross)' dn sAMAccountName mail employeeNumber
```

- **Why:** proves the seed reached Samba and exercises the same Administrator bind IIQ will use.
- **Expect:**
  - `samba-tool` shows `sAMAccountName`, `mail`, and `userAccountControl` (`512` = normal active)
  - `ldapsearch` returns `CN=Helen Ross,OU=People,DC=meridiannb,DC=com`

> **Watch out:** `ldap://localhost:389` is **OpenLDAP**. Samba is **`3890`**. Do not bind as `uid=helen.ross,...` / `LabUser1!` here — that is the OpenLDAP person DN.

### Task 4 — Test Connection on MNB-ActiveDirectory-Live

1. **Applications → Application Definition → MNB-ActiveDirectory-Live → Test Connection**

- **Why:** exercises the Administrator bind over LDAP against `samba-ad:389` inside Docker.
- **Expect:** connection succeeds.

### Task 5 — Create aggregation tasks if missing, then run both

AD-shaped directories separate account and group iteration the same way OpenLDAP did.

1. **Setup → Tasks** → search for AD / `MNB-ActiveDirectory` / `ActiveDirectory-Live`
2. If missing, create:
   - **Account Aggregation** → select `MNB-ActiveDirectory-Live` → **Save** → **Run Now**
   - **Account Group Aggregation** → select `MNB-ActiveDirectory-Live` → **Save** → **Run Now**
3. Wait for both Task Results

- **Why:** Test Connection does not refresh cubes — tasks do.
- **Expect:** both Task Results succeed.

> **Tip:** Prefer exact names your seed imported if present; if the grid is empty after wipe, creating the two tasks yourself is the fix.

### Task 6 — Prove dual-link correlation on Helen’s cube

Same human, two directories, one cube — the correlation standard in action.

1. **Identities → Identity Warehouse → helen.ross**
2. Confirm **`MNB-ActiveDirectory-Live`** under Application Accounts
3. Confirm **`MNB-OpenLDAP`** from Lesson 204 still present

| Link | Correlation keys |
| --- | --- |
| OpenLDAP | `employeeNumber` → `userId` |
| AD-Live | `employeeNumber` → `userId`, `sAMAccountName` → `name` |

- **Why:** dual links prove you did not confuse Samba port `3890` with OpenLDAP `389`.
- **Expect:** both links visible.

### Task 7 — Refresh and check group entitlements

1. On Helen’s cube → **Refresh**
2. Confirm group-based entitlements (e.g. `MNB-Managers`) under her entitlements

- **Why:** group pass + refresh is what makes `memberOf` governable.
- **Expect:** entitlements from the group pass are visible post-refresh.

> **Watch out:** This lab deliberately does **not** prove IQService-mediated password set/reset against real AD. Account/group read, enable/disable, and attribute provisioning work because Samba is genuine LDAP underneath — password ops are the documented gap.

### Task 8 — Close with asserts

```bash
./tools/lab/enterprise/verify-lesson.sh 205
```

- **Why:** hard checks catch an unhealthy DC or missing Live app before Lesson 206.
- **Expect:** hard asserts PASS.

## If it fails

| Symptom | Fix |
| --- | --- |
| Samba never `healthy` (common on Apple Silicon) | Wait full 120s `start_period`; or fall back to OpenLDAP pass-through (Lesson 206) and keep Core CSV AD per `lab-data/enterprise/samba/README.md` |
| `seed-samba.sh` says “already exists” but nothing works | CSV stale after master edit — re-run `python3 tools/lab/enterprise/generate-identity-artifacts.py` first |
| Test Connection: `LDAP: error code 8` / `Transport encryption required` | Re-run `./tools/lab/enterprise/seed-samba.sh` (sets `ldap server require strong auth = no`), then Test Connection again |
| Test Connection bind/auth error (other) | Admin password is `Password1!` — confirm Application XML matches `DOMAINPASS` |
| Aggregation: `schema for objectType: group is not configured` | App had `group.searchDNs` but no group Schema — re-import / reopen `MNB-ActiveDirectory-Live`; then re-run Account Group Aggregation |
| `ldapsearch` on `:389` finds nothing / wrong directory | Samba is host port **`3890`**; `:389` is OpenLDAP (Lesson 204) |
| Aggregation returns zero accounts | `docker exec mnb-samba-ad samba-tool user list` — empty means seed never ran or failed silently |
| `memberOf` not managed | Refresh Entitlement Catalog for this app’s group object type (same as Lesson 204) |
| No OpenLDAP link on Helen | Finish Lesson 204 first, or re-run OpenLDAP aggregation |

## You are done when

- [ ] `mnb-samba-ad` reports **healthy**
- [ ] Helen has both an `MNB-OpenLDAP` and an `MNB-ActiveDirectory-Live` account link
- [ ] You can state the IQService boundary from memory
- [ ] `./tools/lab/enterprise/verify-lesson.sh 205` hard asserts PASS

## Control note

- **Control:** AD-shaped account/group lifecycle within a documented feasibility boundary
- **Owner:** IAM Ops / AD team
- **SLA (lab):** the IQService gap must be documented before any design based on this lab is promoted toward real AD
- **Evidence:** `~/iiq-lab-evidence/sandbox/205/` — `samba-tool` output, Task Result ids, dual-link cube screenshot

## Quick check

1. What proves Samba is ready, not just running? → `Health.Status` = `healthy`
2. What does `userAccountControl 514` mean? → disabled account (terminated persona)
3. What does this lab intentionally **not** prove about AD? → IQService-mediated password set/reset

## Feedback

Could you explain why this lab uses OpenLDAP-Direct against Samba instead of Active Directory-Direct? If aggregation returned zero users, note whether `samba-tool user list` was empty — that split (DC seed vs IIQ aggregate) is the lesson.

## Navigate

- Previous: [Lesson 204](204-openldap-live-ops.md)
- Next: [Lesson 206](206-passthrough-iiq-login.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
