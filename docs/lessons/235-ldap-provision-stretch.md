# Lesson 235 — OpenLDAP Provision Stretch

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~50 minutes  
**Prereq:** Lesson 204  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 58

> **Why:** Reads without writes teach half a connector. If provisioning was never exercised, an ACL denial in production is the first time anyone finds out.

## What this is

Lesson 204 operated `MNB-OpenLDAP` read-only — aggregation, correlation, pass-through auth. The `MNB-Application-OpenLDAP.xml` definition already lists `PROVISIONING` in its `featuresString`, meaning IIQ can write, but you've never made it. This lesson closes that gap: create a brand-new `ou=people` entry for a joiner directly from an IIQ plan, then add/remove a group membership, and if a write is denied, fix the actual ACL on the OpenLDAP server rather than routing around it.

## Know these

| Operation | Proof command |
| --- | --- |
| Account create | `ldapsearch ... '(uid=<user>)'` |
| Group member add/remove | `ldapsearch ... '(cn=<group>)' member` |
| ACL denial | Provisioning Transaction / bind error text |

**Wrong way:** "Fixing" an ACL denial by disabling the provisioning feature in IIQ — that hides the gap instead of closing it.

## Intent

- Provision a create-account plan against `MNB-OpenLDAP` for a joiner and confirm the entry lands.
- Provision a group member add and a group member remove, confirming both with `ldapsearch`.
- Deliberately trigger an ACL denial and fix the OpenLDAP ACL instead of disabling the check.
- Re-aggregate and confirm no drift between IIQ's cube and the directory.

## Before you start

- [ ] `MNB-OpenLDAP` (204) aggregating and pass-through auth working
- [ ] Admin bind DN known: `cn=admin,dc=meridiannb,dc=com` / `admin`
- [ ] A fresh joiner slot available via `hcm-scenario.sh joiner`
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/235`

## Do this

1. Get a fresh joiner: reuse a Lesson 217 joiner without an OpenLDAP link, or run `./tools/lab/enterprise/hcm-scenario.sh joiner lab.ldaptest LDAP Test lab.ldaptest@meridiannb.com`, then aggregate `MNB-Workday` + Refresh.  
   **Expect:** Identity exists in IIQ, no OpenLDAP link yet.
2. Trigger LCM provisioning for OpenLDAP via the joiner's birthright plan (216/217) or a manual **Manage Existing Access → Request Access** account creation. Approve and let it provision.  
   **Expect:** Provisioning Transaction shows success.
3. Confirm on the real server: `ldapsearch -x -H ldap://localhost:389 -b ou=people,dc=meridiannb,dc=com -D 'cn=admin,dc=meridiannb,dc=com' -w admin '(uid=lab.ldaptest)'`.  
   **Expect:** New `dn` with `cn`, `mail`, `employeeNumber` populated by IIQ.
4. Provision a group membership add: assign an OpenLDAP-backed entitlement/role, or seed a group first with `ldapadd -x -H ldap://localhost:389 -D 'cn=admin,dc=meridiannb,dc=com' -w admin` (minimal `groupOfNames` under `ou=groups,dc=meridiannb,dc=com`), then request/approve.  
   **Expect:** Provisioning succeeds.
5. Confirm: `ldapsearch -x -H ldap://localhost:389 -b ou=groups,dc=meridiannb,dc=com -D 'cn=admin,dc=meridiannb,dc=com' -w admin '(cn=<group>)' member`.  
   **Expect:** New joiner's DN listed.
6. Remove the assignment in IIQ, let it provision the remove, re-run the same `ldapsearch`.  
   **Expect:** Member entry gone.
7. Trigger an ACL denial on purpose: edit `MNB-Application-OpenLDAP`'s bind DN to a read-only account, attempt another write.  
   **Expect:** Bind/insufficient-access error visible on the Provisioning Transaction — copy the exact text.
8. Fix the actual ACL on the OpenLDAP side (restore `cn=admin` bind, or add write access for the DN in `slapd.conf`/`olcAccess` inside the container).  
   **Expect:** Do not fix by disabling the provisioning feature in IIQ — that only hides the gap.
9. Retry the write, confirm success, then **Aggregate** once more.  
   **Expect:** IIQ's OpenLDAP link matches the directory with no drift.
10. Save the `ldapsearch` outputs for create, group-add, group-remove, and the before/after ACL fix under `~/iiq-lab-evidence/sandbox/235/`.

## If it fails

- **Create succeeds in IIQ but `ldapsearch` shows nothing** — check base DN and bind as `cn=admin`, not anonymously.
- **Group entry rejected as malformed** — `groupOfNames` needs at least one `member` at creation; seed with the admin DN, then have IIQ add/remove the real member.
- **ACL fix doesn't take effect** — OpenLDAP often needs a `slapd` restart or `ldapmodify` against `cn=config`; check `docker logs mnb-openldap` for the actual refusal reason.

## You are done when

Account create, group add, and group remove all succeed on the live OpenLDAP server, and the ACL denial you triggered is genuinely fixed and retried to success.

## Control note

- **Control:** Directory write-path proof (provisioning, not just aggregation).  
- **Owner:** IAM Engineering / Directory Ops.  
- **SLA (lab):** ACL denials fixed at the source, never bypassed in IIQ.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/235/` — create/add/remove `ldapsearch` output, ACL error + fix.

## Quick check

1. What proves a write, not just a UI success message? → `ldapsearch` against the live server.  
2. What's the wrong fix for an ACL denial? → Disabling provisioning in IIQ instead of fixing the ACL.  
3. What object type needs at least one member at creation? → `groupOfNames`.

## Navigate

- Previous: Lesson 234
- Next: Lesson 236
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
