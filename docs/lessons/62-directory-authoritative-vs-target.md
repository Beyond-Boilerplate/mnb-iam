# Lesson 62 — Directory Authoritative vs Target

| Field | Value |
| --- | --- |
| **Level** | Intermediate |
| **Track** | Connectors — Directory |
| **Time** | 60–75 minutes |
| **Prereq** | Lessons 56–61; `MNB-HR` authoritative model from foundations |
| **Lab data** | Selection matrix; AD/Entra/OpenLDAP/LDIF app notes |

## Learning objectives

You will be able to:

- Defend Meridian’s rule: directories are targets; HR is workforce truth
- Configure or verify create-identities / authoritative flags on all directory apps
- Design correlation-first onboarding so AD/Entra never invent people
- Produce an examiner one-pager on authoritative sources
- Complete lab-without-live-target flag audits across `MNB-*` directory apps

## Why this matters

If `MNB-ActiveDirectory` can create identities, a rogue or mis-correlated AD account becomes a cube—bypassing HR joiner controls. Banks fail audits when “the directory said so” overrides HR termination.

**Control / audit:** Show authoritative source list: `MNB-HR` (and approved HRIS only). Every directory Application screenshot must show create-identities off.

## Concepts

| Source | Authoritative? | Creates identities? | Role |
| --- | --- | --- | --- |
| `MNB-HR` | Yes | Yes | Workforce truth |
| `MNB-ActiveDirectory` | No | No | Account target |
| `MNB-EntraID` | No | No | Cloud directory target |
| `MNB-OpenLDAP` | No | No | Lab/midrange directory |
| `MNB-LDIF-DirectoryDump` | No | No | Offline evidence |

```text
  HR event (hire/term)
        |
        v
  MNB-HR aggregate → create/update cube
        |
        v
  Provision to directory targets (AD/Entra/LDAP)
        |
        v
  Directories aggregate → correlate back to cube
        |
        X  directories must not create new cubes
```

**Exception process:** Only Architecture + HR can add a second authoritative source (e.g. future Workday)—never silently via AD.

## Before you start

- [ ] List all directory-related Applications from Lessons 56–60
- [ ] IIQ access to Application settings
- [ ] Lesson 09 IT Access non-authoritative discipline recalled

## Lab procedure

### Task 1 — Authoritative source register

1. Create `~/iiq-lab-data/connectors/MNB-authoritative-register-62.md`:

| Application | Auth? | Create IDs? | Owner |
| --- | --- | --- | --- |
| `MNB-HR` | Y | Y | HR / IAM |
| `MNB-ActiveDirectory` | N | N | Technology |
| `MNB-EntraID` | N | N | Cloud IAM |
| `MNB-OpenLDAP` | N | N | Lab |
| `MNB-LDIF-DirectoryDump` | N | N | IAM evidence |
| `MNB-IT-Access` | N | N | Technology |

2. Sign statement: “No directory creates identities at Meridian.”

**Expected result:** Register file complete.

### Task 2 — Lab without live target — flag audit

1. For each directory app that exists in IIQ, open settings and confirm authoritative/create flags.
2. For apps that are notes-only shells, audit the design notes instead—mark “verified in notes.”
3. Screenshot or quote the create-identities setting for at least `MNB-ActiveDirectory` design.
4. Expected result: all N/N except HR. If it fails: disable create immediately and file incident note if orphans appeared.

**Expected result:** Audit table with Verified-in-UI or Verified-in-notes per app.

### Task 3 — Correlation-first joiner storyboard

1. Storyboard `nina.joiner`:

| Step | System | Outcome |
| --- | --- | --- |
| 1 | HR file | Cube created |
| 2 | Provision AD | Account created for existing cube |
| 3 | Aggregate AD | Link correlates; no second cube |

2. Anti-storyboard: AD aggregated first with create on → orphan cube named after sAMAccountName.

**Expected result:** Both storyboards in register file.

### Task 4 — Leaver truth

1. Write: HR termination drives disable plans to directories; directories do not “uncreate” HR identities.
2. Residual AD account after HR leaver = control failure (provisioning), not “AD authoritative.”

**Expected result:** Leaver truth paragraph.

### Task 5 — Examiner one-pager

1. Half-page answer to: “Is Active Directory authoritative for workforce identity?”
2. Include register table excerpt and one screenshot/note reference.
3. Store in binder.

**Expected result:** One-pager ready.

### Task 6 — Contractor / vendor edge case

1. `raj.external` may appear in IT dumps or directories before HR contractor feed is clean.
2. Write control: contractors still require an approved authoritative path (HR contractor row or Architecture exception)—directories must not fill the gap by creating cubes.
3. Expected result: edge-case paragraph. If it fails: orphan `raj.external` cube → disable create + remediation.

**Expected result:** Contractor edge case in register file.

### Task 7 — CHANGELOG

1. “Lesson 62 authoritative register confirmed for directory apps.”

**Expected result:** CHANGELOG line.

## Acceptance criteria

- [ ] Authoritative register includes HR + all directory apps
- [ ] Lab-without-live-target flag audit completed (UI and/or notes)
- [ ] Joiner correlation storyboard written
- [ ] Leaver truth paragraph written
- [ ] Examiner one-pager produced
- [ ] Contractor/vendor edge case documented
- [ ] CHANGELOG updated

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Orphan cubes from AD | Create-identities on | Disable; cleanup process |
| Dual authoritative HR+AD | Misconfig | Remove AD authoritative |
| Contractors only in AD | Process gap | HR must source contractors or approved exception |
| Entra guests invent cubes | Create on | Disable; separate B2B process |
| LDIF created identities | Flag error | Disable; treat as evidence only |

## Training binder evidence

- `MNB-authoritative-register-62.md`
- Flag audit results
- Examiner one-pager
- Joiner storyboard

**Examiner question:** “Show every Application that can create an identity cube.”

## Knowledge check

1. Which Meridian app is authoritative for workforce identity in this curriculum?
2. Should `MNB-ActiveDirectory` create identities?
3. What happens in the anti-storyboard when AD creates identities?
4. Do directory aggregates update HR truth for termination?
5. Can LDIF dumps be authoritative?
6. How should `raj.external` gain a cube if not via directory create-identities?

### Answers

1. `MNB-HR` (approved HRIS extract).
2. No.
3. Orphan cubes appear from directory accounts, bypassing HR.
4. No—HR drives termination; directories receive disable/provisioning.
5. No—offline evidence only.
6. Via an approved authoritative path (HR contractor row or Architecture exception)—not AD/Entra create.

## Stretch lab

- Draft Architecture exception form for adding Workday as co-authoritative (Lesson 77 preview).
- Search IIQ for any Application with create-identities enabled; remediate non-HR.
- Tie register to SoD: toxic entitlements never invent people.

## Summary

- Directories are targets; HR is truth.
- Flag audits are mandatory lab-without-live-target work.
- Examiner one-pagers close the directory connector arc before JDBC.
- Contractors and vendors still need an approved authoritative path—not directory invent.

---

**Previous:** [Lesson 61 — Password Management & Interceptor](61-password-management-interceptor.md)  
**Next:** [Lesson 63 — JDBC Connector Fundamentals](63-jdbc-connector-fundamentals.md)
