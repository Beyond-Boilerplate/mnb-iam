# Lesson 58 — LDAP / OpenLDAP Connector

| Field | Value |
| --- | --- |
| **Level** | Intermediate |
| **Track** | Connectors — Directory |
| **Time** | 75–90 minutes |
| **Prereq** | Lesson 57; connector matrix OpenLDAP row |
| **Lab data** | `~/iiq-lab-data/connectors/ldap/mnb-openldap.ldif`; optional `docker-compose.connectors.yml` |

## Learning objectives

You will be able to:

- Inspect Meridian OpenLDAP LDIF (`inetOrgPerson` + `groupOfNames`)
- Create Application `MNB-OpenLDAP` as OpenLDAP Direct or LDAP type per lab build
- Map `uid` / `employeeNumber` / `mail` for correlation
- Complete lab-without-live-LDAP using LDIF as schema truth
- Define aggregate task and group membership expectations for `priya.wire`

## Why this matters

Not every Meridian directory is Active Directory. Lab and midrange systems often use OpenLDAP/FreeIPA. Engineers who only know AD Direct mis-map `sAMAccountName` onto `uid` and break correlation.

**Control / audit:** LDAP apps remain non-authoritative unless Architecture explicitly designates otherwise. Evidence is LDIF + Application schema maps.

## Concepts

| LDIF / LDAP | IIQ role |
| --- | --- |
| `uid` | Native account id candidate |
| `employeeNumber` | Correlate to `employeeId` |
| `mail` | Secondary correlate / quality |
| `groupOfNames` / `member` | Entitlements |
| Base DN | `dc=meridiannb,dc=com` |

```text
  mnb-openldap.ldif
        |
        v
  Optional Docker OpenLDAP
        |
        v
  MNB-OpenLDAP Application
        |
        v
  Aggregate MNB-OpenLDAP → correlate to HR cubes
```

Fixture personas in LDIF include `helen.ross`, `priya.wire`, and group `wire-initiators`.

## Before you start

- [ ] Copy LDIF: confirm `~/iiq-lab-data/connectors/ldap/mnb-openldap.ldif`
- [ ] Optional: review `docker-compose.connectors.yml` for OpenLDAP service
- [ ] IIQ up; Lesson 52 preferred connector OpenLDAP - Direct

## Lab procedure

### Task 1 — Inspect the LDIF fixture

1. Read structure:

```bash
grep -E '^dn:|^uid:|^employeeNumber:|^cn:|^member:' ~/iiq-lab-data/connectors/ldap/mnb-openldap.ldif
```

2. Confirm base `dc=meridiannb,dc=com`, `ou=people`, `ou=groups`.
3. Note `priya.wire` membership in `cn=wire-initiators`.

**Expected result:** Notebook lists people DNs + wire-initiators member DN.

**If it fails:** Re-copy from `lab-data/connectors/ldap/`.

### Task 2 — Lab without live target — schema worksheet from LDIF

1. Create `~/iiq-lab-data/connectors/ldap/MNB-OpenLDAP-schema-58.md`:

| LDAP attribute | Schema use |
| --- | --- |
| `uid` | Account identity attribute |
| `cn`, `sn` | Identity sync optional |
| `mail` | email |
| `employeeNumber` | Correlation to `employeeId` |
| `member` on groups | Entitlement |

2. Correlation: `employeeNumber`↔`employeeId`; fallback `uid`↔`userName`.
3. Create-identities: **No**.
4. Search DN people: `ou=people,dc=meridiannb,dc=com`; groups: `ou=groups,dc=meridiannb,dc=com`.

**Expected result:** Schema file complete without needing LDAP bind.

### Task 3 — Create Application MNB-OpenLDAP

1. Applications → Add New → **OpenLDAP - Direct** (or **LDAP** if Direct unavailable—document which).
2. Name: `MNB-OpenLDAP`. Owner lab `spadmin`.
3. Host/port/bind DN: use Docker values if running; else placeholders `ldap://mnb-openldap:389` and bind `cn=admin,dc=meridiannb,dc=com` (fictional password in secrets store—not in git).
4. Base DN: `dc=meridiannb,dc=com`.
5. Save.

**Expected result:** Application object exists (Test Connection optional).

**If it fails:** Notes-only shell file acceptable when type missing from image.

### Task 4 — Optional live Docker path

1. If compose profile available, start OpenLDAP per `docker-compose.connectors.yml` comments.
2. Load LDIF into the container (follow compose README / learn track).
3. Test Connection from IIQ; run Account Aggregation `Aggregate MNB-OpenLDAP`.
4. Spot-check `helen.ross` and `priya.wire` links + `wire-initiators`.

**Expected result:** Live path: accounts > 0 and group visible. Offline path: skip with deferred note.

**If it fails:** Capture bind error; continue offline worksheets as primary.

### Task 5 — Entitlement expectation

1. Write Expected result: After aggregate+correlate, `priya.wire` shows entitlement/group `wire-initiators` (or CN equivalent).
2. If it fails: check group search DN, `member` attribute mapping, and correlation on `priya.wire`.

**Expected result:** Expectation block in schema file.

### Task 6 — TLS / LDAPS design note

1. Prefer `ldaps://` for Meridian non-lab; document cert trust store ownership.
2. Lab may use plain LDAP on Docker—label clearly **lab only**.
3. Expected result: TLS note in schema file. If it fails (prod on plain LDAP): finding—require LDAPS ADR exception.

**Expected result:** TLS/lab-only label written.

### Task 7 — Runbook + CHANGELOG

1. Add `Aggregate MNB-OpenLDAP` after HR in conceptual order (before Refresh).
2. CHANGELOG: “Lesson 58 MNB-OpenLDAP shell + LDIF schema maps.”

**Expected result:** Runbook row + CHANGELOG.

## Acceptance criteria

- [ ] LDIF inspected; wire group membership noted
- [ ] Lab-without-live-target schema/correlation file saved
- [ ] `MNB-OpenLDAP` created or notes shell equivalent
- [ ] Create-identities disabled documented
- [ ] Live aggregate optional; deferred note OK
- [ ] TLS / lab-only LDAP note written
- [ ] Runbook + CHANGELOG updated

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Bind failed | Bad DN/password/TLS | Fix secrets; try ldap vs ldaps |
| 0 accounts | Wrong people OU | Use `ou=people,dc=meridiannb,dc=com` |
| No groups | Group objectClass filter | Include `groupOfNames` |
| Orphans | Create-identities on | Disable |
| AD attrs on LDAP | Wrong mental model | Use `uid` not `sAMAccountName` |

## Training binder evidence

- LDIF grep output or screenshot
- `MNB-OpenLDAP-schema-58.md`
- Application definition screenshot or shell notes
- Aggregate result **or** deferred-no-target note

**Examiner question:** “Show the non-AD directory application and how employeeNumber correlates to HR.”

## Knowledge check

1. What file bootstraps Meridian OpenLDAP lab data?
2. Which attribute is the preferred account id in the LDIF?
3. How does `priya.wire` relate to `wire-initiators`?
4. Is `MNB-OpenLDAP` authoritative?
5. Must Docker be running to finish acceptance criteria?
6. Why prefer LDAPS for non-lab Meridian LDAP?

### Answers

1. `ldap/mnb-openldap.ldif`.
2. `uid`.
3. She is a `member` of the `groupOfNames` `cn=wire-initiators`.
4. No—unless Architecture explicitly changes that (curriculum default: non-authoritative).
5. No—LDIF-based lab-without-live-target worksheets suffice.
6. Encrypt directory binds in transit; plain LDAP is lab-only unless exceptioned.

## Stretch lab

- Extend LDIF with `marcus.approve` and an approvers group; re-import.
- Compare OpenLDAP Direct vs generic LDAP feature strings in registry.
- Add TLS LDAPS design notes mirroring IQService TLS discipline.

## Summary

- OpenLDAP labs use Meridian LDIF as schema truth.
- `MNB-OpenLDAP` maps `uid`/`employeeNumber`, not AD attributes.
- Live Docker is optional; offline maps complete the lesson.

---

**Previous:** [Lesson 57 — AD Groups, OUs & Exchange](57-ad-groups-ous-exchange.md)  
**Next:** [Lesson 59 — Azure / Entra ID Connector](59-azure-entra-id-connector.md)
