# Lesson 204 — Operate Live OpenLDAP

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~55 minutes  
**Prereq:** Lesson 202  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 58

> **Why (1–2 lines):** Validate the directory bind and search yourself before you ever blame IIQ's aggregation for missing accounts. This lesson also stands in for classic 58 (OpenLDAP connector fundamentals), but against a **live, running** directory instead of a static CSV export.

## What this is

`MNB-OpenLDAP` is a real `OpenLDAP - Direct` connector application (`sailpoint.connector.LDAPConnector`) pointed at the `openldap` container on port `389`, binding as service account `cn=svc-iiq-provision,ou=service,dc=meridiannb,dc=com`. It searches `ou=people,dc=meridiannb,dc=com` for `inetOrgPerson` accounts and `ou=groups,dc=meridiannb,dc=com` for `groupOfUniqueNames` entitlements (`memberOf`/`groups` is `entitlement="true" managed="true"`). This is the same application object type Core Path lessons use, but here the directory is alive and mutable — `phpLDAPadmin` and raw `ldapsearch` let you inspect and change it directly, then watch IIQ's aggregation catch up. That live feedback loop (change directory → aggregate → see cube change) is the whole point of the Enterprise Sandbox Path.

## Know these

- Human debug bind: `cn=admin,dc=meridiannb,dc=com` / `admin` — directory root, for you.
- IIQ's real bind: `cn=svc-iiq-provision,ou=service,dc=meridiannb,dc=com` / `Provision1!` — least-privilege service account, what the Application actually authenticates with.
- Correlation key: `employeeNumber` (e.g. `MNB00001` for Helen) — separate from the login/display attribute `uid`.
- Aggregation runs in two passes: accounts (`inetOrgPerson`), then groups (`groupOfUniqueNames`/`posixgroup`/`nisNetgroup`) — a missed group pass looks like "aggregation ran but no entitlements."
- **Wrong way:** Letting IIQ's Application definition bind as `cn=admin` "because it's easier to test" — real banks never let IIQ authenticate as directory root; that separation is audit-relevant, not just habit.

## Intent

- Read a real LDAP entry two ways — GUI (phpLDAPadmin) and command line (`ldapsearch`) — and get the same answer.
- Run account and group aggregation against `MNB-OpenLDAP` and confirm both accounts and `groupOfUniqueNames` entitlements land.
- Diagnose and fix a missing `employeeNumber`↔`userId` correlation link by hand.
- Know which bind DN is for humans versus the one IIQ actually provisions with.

## Before you start

- [ ] Lessons 201–202 complete; `MNB-OpenLDAP` Application exists in IIQ
- [ ] `ldapsearch` available (`brew install openldap`) or willing to use `docker exec mnb-openldap ldapsearch`
- [ ] phpLDAPadmin reachable at `http://localhost:8090/`
- [ ] Evidence dir: `mkdir -p ~/iiq-lab-evidence/sandbox/204`

## Do this

1. Open phpLDAPadmin at `http://localhost:8090/`, login DN `cn=admin,dc=meridiannb,dc=com` / `admin`, browse to `ou=people,dc=meridiannb,dc=com` → `uid=helen.ross`.  
   **Why:** confirms the GUI view of ground truth before you trust any command-line output.  
   **Expect:** `employeeNumber` reads `MNB00001`, matching the identity master.

2. Reproduce the same lookup: `ldapsearch -x -H ldap://localhost:389 -b ou=people,dc=meridiannb,dc=com -D cn=admin,dc=meridiannb,dc=com -w admin '(uid=helen.ross)'`.  
   **Why:** this is the same query IIQ's connector runs under the hood, just with a different bind identity.  
   **Expect:** `employeeNumber`, `mail`, and `title` match phpLDAPadmin exactly.

3. Note the two credentials you now know: `cn=admin,...` (human debug) vs. `cn=svc-iiq-provision,ou=service,dc=meridiannb,dc=com` / `Provision1!` (IIQ's actual bind).  
   **Why:** real banks never let IIQ bind as directory root — least privilege matters for audits, not just habit.  
   **Expect:** you can state which DN IIQ's Application XML actually uses.

4. In IIQ, open **Applications → Application Definition → MNB-OpenLDAP**, click **Test Connection**, then run **Account Aggregation**, then **Group Aggregation**.  
   **Why:** `MNB-OpenLDAP` aggregates `groupOfUniqueNames`, `posixgroup`, and `nisNetgroup` as separate object types — skipping the group pass silently leaves entitlements missing.  
   **Expect:** both Task Results succeed.

5. Open Helen's identity cube (**Identities → Identity Warehouse → helen.ross**) and confirm an `MNB-OpenLDAP` account link exists under Application Accounts.  
   **Why:** a missing link here is a correlation failure, not an aggregation failure — the account aggregated into an *uncorrelated* link instead.  
   **Expect:** link present, or you proceed to step 6 to fix it.

6. If missing, confirm LDAP `employeeNumber` (`MNB00001`) matches identity attribute `userId`, then re-run Identity Refresh with "correlate accounts" enabled, or manually correlate from **Identities → Uncorrelated Accounts**.  
   **Why:** Lesson 214 formalizes this with rules — doing it by hand once here means you understand what the rule will later automate.  
   **Expect:** the link now appears on Helen's cube.

7. Change one thing in phpLDAPadmin (add Helen to a group, or edit her `title`), then re-run account/group aggregation.  
   **Why:** proves the live feedback loop every later lesson in this path depends on.  
   **Expect:** the change lands on her cube after re-aggregation.

8. Revert your test change in phpLDAPadmin and re-aggregate once more.  
   **Why:** leaves the directory in its seeded state for whoever (including future-you) runs the next lesson against it — a stray test edit left in place is a common source of "why does my aggregation look different from the docs" confusion two lessons later.  
   **Expect:** Helen's cube reflects the reverted value after the final aggregation pass.

## If it fails

- **Test Connection fails with invalid credentials** — service account password/DN out of sync; re-run `./tools/lab/enterprise/seed-enterprise.sh` to reset both from the same source.
- **Account aggregation runs clean but zero accounts land** — confirm the search base has entries: `ldapsearch -x -H ldap://localhost:389 -b ou=people,dc=meridiannb,dc=com -D cn=admin,dc=meridiannb,dc=com -w admin '(objectClass=inetOrgPerson)' dn`.
- **Groups aggregate but show as unmanaged** — refresh **Setup → Entitlement Catalog** for the `group` object type on this application.
- **Helen's link looks stale** — you're viewing cached data; re-run Account Aggregation, Test Connection doesn't refresh it.
- **`ldapsearch: command not found`** — `brew install openldap` or run via `docker exec mnb-openldap ldapsearch ...`.

## You are done when

`ldapsearch` and phpLDAPadmin agree on Helen's LDAP attributes, `MNB-OpenLDAP` account **and** group aggregation both complete, Helen's cube shows an `MNB-OpenLDAP` account link, and a manual attribute change you made in phpLDAPadmin shows up on her cube after re-aggregation.

## Control note

- **Control:** Directory aggregation and correlation accuracy.
- **Owner:** IAM Ops / Directory team.
- **SLA (lab):** correlation gaps fixed same session; production target is same-day orphan triage.
- **Evidence:** `~/iiq-lab-evidence/sandbox/204/` — `ldapsearch` output, aggregation Task Result ids, before/after cube screenshot.

## Quick check

1. Which bind does IIQ actually use for aggregation? → `cn=svc-iiq-provision,ou=service,dc=meridiannb,dc=com`.
2. Which attribute is the correlation key, and which is login/display? → `employeeNumber` correlates; `uid` is login/display.
3. Why can group entitlements look "unmanaged" after a clean aggregation? → the Entitlement Catalog for that object type wasn't refreshed.

## Navigate

- Previous: Lesson 203
- Next: Lesson 205
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
