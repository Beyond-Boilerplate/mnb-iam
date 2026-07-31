# Meridian OpenLDAP (lab backend)

Live directory for **OpenLDAP - Direct** / LDAP connector onboarding (`MNB-OpenLDAP`).

Seed source: `mnb-openldap.ldif` (baked into `mnb-openldap:local` via `docker/Dockerfile.openldap`).
Provision ACLs: applied once by `openldap-provision-acl` (`docker/openldap/apply-provision-acl.sh`).

## Start

Included with the main Meridian Docker stack:

```bash
./tools/lab/docker/up.sh
```

Or connectors-only:

```bash
docker compose -f docker-compose.connectors.yml up -d --build
```

After editing the LDIF, rebuild and wipe LDAP volumes (see below).

## MCP / Teller onboard

Preferred path (lab) — one script seeds **MNB-HR** (authoritative cubes) then **MNB-OpenLDAP**.
After HR aggregation it calls **`rebuild_manager_hierarchy`** (Link.manager → Identity.manager)
then Refresh Identity Cube so Teller/`get_manager_hierarchy` returns direct reports:

```bash
export MCP_API_KEY=mnb-lab-mcp-key
./tools/lab/scripts/seed-mnb-lab-data.sh
# OpenLDAP only (if HR cubes already exist):
./tools/lab/scripts/seed-mnb-lab-data.sh --skip-hr
```

If cubes exist but reports are empty, run:

```text
rebuild_manager_hierarchy  application=MNB-HR  manager_attribute=manager
run_task_now  task_name=Refresh Identity Cube  args={promoteAttributes,refreshManagerStatus}
```

Or call MCP directly:

```text
onboard_application
  name: MNB-OpenLDAP
  type: OpenLDAP - Direct
  attributes:
    host: openldap          # from IIQ container network
    port: 389
    user: cn=svc-iiq-provision,ou=service,dc=meridiannb,dc=com
    password: Provision1!
    searchDN: dc=meridiannb,dc=com
```

Or stepwise: `create_application` → `test_application_connection` → `trigger_aggregation`.

Curriculum note (Lesson 58): keep `MNB-HR` authoritative; correlate LDAP via `employeeNumber` ↔ HR — do not mint cubes from LDAP alone.

## Which bind for IdentityIQ?

The OpenLDAP connector stores **one** bind DN/password. That account is used for Test Connection, aggregation, **and** provisioning.

| Goal | Bind DN | Password | Use when |
| --- | --- | --- | --- |
| Aggregate only (least privilege) | `cn=svc-iiq-read,dc=meridiannb,dc=com` | `Readonly1!` | Lesson 58 aggregation / no create-modify |
| **Aggregate + provision (recommended)** | `cn=svc-iiq-provision,ou=service,dc=meridiannb,dc=com` | `Provision1!` | Joiner/leaver/group membership from IIQ |
| Break-glass lab admin | `cn=admin,dc=meridiannb,dc=com` | `admin` | Debugging only — not for the app long-term |

`svc-iiq-read` **cannot** create accounts or change `member` — provisioning plans will fail with insufficient access. Use **`svc-iiq-provision`** once you enable PROVISIONING on `MNB-OpenLDAP`.

## GUI (phpLDAPadmin)

Started with the Docker lab stack:

```text
http://localhost:8090/
Login DN: cn=admin,dc=meridiannb,dc=com
Password: admin
```

Or CLI / desktop tools (Apache Directory Studio, etc.) against `localhost:389` with the same bind.

## Connection sheet (IIQ)

| Field | Docker IIQ → LDAP | Host / ldapsearch |
| --- | --- | --- |
| Host | `openldap` | `localhost` |
| Port | `389` | `389` |
| Use SSL | No (lab) | No |
| Bind DN (with provisioning) | `cn=svc-iiq-provision,ou=service,dc=meridiannb,dc=com` | same |
| Bind password | `Provision1!` | same |
| Base DN | `dc=meridiannb,dc=com` | same |
| People search | `ou=people,dc=meridiannb,dc=com` | `(objectClass=inetOrgPerson)` |
| Group search | `ou=groups,dc=meridiannb,dc=com` | `(objectClass=groupOfNames)` |
| Account native id | `uid` | |
| Correlation | `employeeNumber` ↔ HR `userId` | |
| Group member attr | `member` | |

## Verify

```bash
# read path
ldapsearch -x -H ldap://localhost:389 \
  -b dc=meridiannb,dc=com \
  -D cn=svc-iiq-read,dc=meridiannb,dc=com -w Readonly1! '(uid=priya.wire)' dn

# provision path (write ACL applied by openldap-provision-acl)
ldapsearch -x -H ldap://localhost:389 \
  -b ou=people,dc=meridiannb,dc=com \
  -D cn=svc-iiq-provision,ou=service,dc=meridiannb,dc=com -w Provision1! '(uid=helen.ross)' dn
```

Reload seed + ACLs after LDIF edits:

```bash
docker compose -f docker-compose.iiq.yml build openldap
docker compose -f docker-compose.iiq.yml stop openldap openldap-provision-acl
docker volume rm mnb-iiq-lab_mnb-openldap-data mnb-iiq-lab_mnb-openldap-config
docker compose -f docker-compose.iiq.yml up -d openldap openldap-provision-acl
```

## Seed summary

| Kind | Count | Notes |
| --- | --- | --- |
| People | 10 | Aligned to `MNB-HR` (`helen.ross` … `samir.hassan`) |
| Groups | 8 | `wire-initiators`, `wire-approvers`, VPN/app admins, dept + `all-employees` |
| Service | 2 | `svc-iiq-read` (suffix) + `svc-iiq-provision` (`ou=service`) |
| Leaver | `samir.hassan` | `description: Inactive`, not in groups |
| Contractor | `raj.external` | In `dept-technology` only |

User passwords for AUTHENTICATE drills: `LabUser1!` on people entries.
