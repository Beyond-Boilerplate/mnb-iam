# Lesson 205 — Operate Samba AD

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~65 minutes  
**Prereq:** Lesson 202  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 56–57

> **Why (1–2 lines):** AD-shaped login and group membership, proven live, without requiring IQService. An examiner asking "what exactly does your AD integration NOT do" gets a precise, documented answer here instead of a shrug.

## What this is

`samba-ad` (`nowsci/samba-domain`) is a real Samba Active Directory domain controller for domain `MERIDIANNB.COM` — it speaks genuine LDAP and Kerberos, not a CSV pretending to be AD. IIQ connects through `MNB-ActiveDirectory-Live`, an `OpenLDAP - Direct` connector (`sailpoint.connector.LDAPConnector`) bound as `CN=Administrator,CN=Users,DC=meridiannb,DC=com`, searching `OU=People,DC=meridiannb,DC=com` for `person`/`user` objects and `CN=Users,DC=meridiannb,DC=com` for `group` objects (`memberOf` is the managed entitlement). This is deliberately **not** the native "Active Directory - Direct" connector — that requires IQService for password operations, explicitly out of scope for this local sandbox (see the Feasibility Boundaries table in [`ENTERPRISE-LAB-V2.md`](../ENTERPRISE-LAB-V2.md)). You get real AD-shaped account/group aggregation and enable/disable; you do not get IQService-mediated password reset — that gap is intentional, not a bug.

## Know these

- Domain controller readiness: `docker inspect -f '{{.State.Health.Status}}' mnb-samba-ad` must read `healthy` — its healthcheck runs `samba-tool domain info` internally, a stronger signal than "container running."
- Groups seeded: `MNB-Employees`, `MNB-Managers`, `Wire-Initiators`, `Wire-Approvers`.
- Correlation: AD `employeeNumber` → identity `userId`; login key is `sAMAccountName` → identity `name`.
- `userAccountControl` `512` = normal active account; `514` = disabled (terminated personas seed this way).
- **Wrong way:** Assuming the native "Active Directory - Direct" connector belongs in this lab — it needs IQService for password ops, which this sandbox intentionally doesn't run; `MNB-ActiveDirectory-Live` is the deliberate LDAP-based stand-in instead.

## Intent

- Wait for a real domain controller to finish bootstrapping and confirm it's actually healthy, not just "container running."
- Seed Samba users/groups from the same identity master used everywhere else, and know why that seed step is best-effort.
- Aggregate `MNB-ActiveDirectory-Live` and correlate `sAMAccountName`/`employeeNumber` to identity `name`/`userId`.
- State precisely what this stand-in AD can and cannot do compared to a real production AD + IQService pair.

## Before you start

- [ ] Lesson 202 seed complete; `identity-master.json` generator has run at least once
- [ ] `mnb-samba-ad` container present (`docker ps | grep samba`)
- [ ] Patience for a 2+ minute first-boot domain bootstrap
- [ ] Evidence dir: `mkdir -p ~/iiq-lab-evidence/sandbox/205`

## Do this

1. Check Samba's health before doing anything else: `docker inspect -f '{{.State.Health.Status}}' mnb-samba-ad`.  
   **Why:** first boot can take 2+ minutes to initialize a domain; "running" is not "ready."  
   **Expect:** output reads `healthy` before you continue.

2. Seed users and groups: `./tools/lab/enterprise/seed-samba.sh`.  
   **Why:** creates an `OU=People` unit and four groups via `samba-tool`, then loops `lab-data/enterprise/generated/samba-users.csv` (from Lesson 202's generator) creating or updating each user — every `|| true` in it means "best-effort, keep going."  
   **Expect:** script completes; a few benign "already exists" lines are normal.

3. Confirm at least one user landed directly against the DC: `docker exec mnb-samba-ad samba-tool user show helen.ross`.  
   **Why:** proves the seed reached the DC itself, independent of IIQ.  
   **Expect:** `sAMAccountName`, `mail`, and `userAccountControl` (`512` = normal active) shown.

4. In IIQ, open **Applications → Application Definition → MNB-ActiveDirectory-Live**, click **Test Connection**.  
   **Why:** exercises the `CN=Administrator,CN=Users,DC=meridiannb,DC=com` bind over LDAP against `samba-ad:389` inside the Docker network (host-exposed as `3890`, but IIQ uses the internal hostname/port).  
   **Expect:** connection succeeds.

5. Run **Account Aggregation**, then **Group Aggregation** for the `memberOf`/group object type.  
   **Why:** AD-shaped directories separate account and group iteration the same way OpenLDAP did in Lesson 204.  
   **Expect:** both Task Results succeed.

6. Open Helen's cube and confirm an `MNB-ActiveDirectory-Live` link now appears under Application Accounts, alongside her `MNB-OpenLDAP` link from Lesson 204.  
   **Why:** same human, two directories, one cube — the correlation standard in action.  
   **Expect:** both links visible; correlation key is `employeeNumber`→`userId`, login key `sAMAccountName`→`name`.

7. Refresh Helen (**Identities → Identity Warehouse → helen.ross → Refresh**) and confirm both directory links persist and group-based entitlements (e.g. `MNB-Managers`) show under her entitlements.  
   **Expect:** entitlements from step 5's group pass are visible post-refresh.

8. Write down, in one sentence, what stays out of scope: IQService-mediated password set/reset against real AD.  
   **Why:** account/group read, enable/disable, and attribute provisioning all work here because Samba is genuine LDAP underneath — password ops are the one documented gap.  
   **Expect:** you can state this boundary without looking it up.

## If it fails

- **Samba never reports healthy (common on Apple Silicon)** — the image needs `platform: linux/amd64` emulation; give it the full 120s `start_period` before troubleshooting, or fall back to OpenLDAP pass-through (Lesson 206) and keep `MNB-ActiveDirectory` on Core CSV per `lab-data/enterprise/samba/README.md`.
- **`seed-samba.sh` reports everyone "already exists" but nothing works** — CSV wasn't regenerated after an `identity-master.json` edit; re-run `python3 tools/lab/enterprise/generate-identity-artifacts.py` first.
- **Test Connection fails with a bind error** — Samba's admin password is `Password1!` (`DOMAINPASS` env var); confirm the Application XML's password matches.
- **Aggregation returns zero accounts** — `docker exec mnb-samba-ad samba-tool user list`; empty means the seed step never ran or failed silently.
- **`memberOf` not showing as managed entitlement** — refresh the Entitlement Catalog for this application's group object type, same fix as Lesson 204.

## You are done when

`mnb-samba-ad` reports healthy, Helen has both an `MNB-OpenLDAP` and an `MNB-ActiveDirectory-Live` account link on her cube, and you can state the IQService boundary from memory without looking it up.

## Control note

- **Control:** AD-shaped account/group lifecycle within a documented feasibility boundary.
- **Owner:** IAM Ops / AD team.
- **SLA (lab):** the IQService gap must be documented before any design based on this lab is promoted toward real AD.
- **Evidence:** `~/iiq-lab-evidence/sandbox/205/` — `samba-tool` output, aggregation Task Result ids, dual-link cube screenshot.

## Quick check

1. What proves Samba is actually ready, not just running? → `docker inspect ... Health.Status` = `healthy`.
2. What does `userAccountControl 514` mean? → disabled account (terminated persona).
3. What does this lab intentionally NOT prove about AD? → IQService-mediated password set/reset.

## Navigate

- Previous: Lesson 204
- Next: Lesson 206
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
