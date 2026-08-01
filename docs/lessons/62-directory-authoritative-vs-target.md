# Lesson 62 — Directory Authoritative vs Target

**Level:** Intermediate  
**Track:** Connectors — Directory  
**Time:** 75–90 min  
**Prereq:** Lessons 56–61; `MNB-HR` authoritative model from foundations (Lessons 06–09)  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv`
- Runtime: `~/iiq-lab-data/connectors/MNB-authoritative-register-62.md` (you create)
- Prior apps: `MNB-HR`, `MNB-ActiveDirectory`, `MNB-EntraID`, `MNB-OpenLDAP`, `MNB-LDIF-DirectoryDump`

---

## Learning objectives

You will be able to:

- Defend Meridian’s rule: **directories are targets; HR is workforce truth**
- Audit create-identities / authoritative flags on every directory-related Application
- Storyboard correlation-first joining so AD/Entra never invent people — and the anti-storyboard when they do
- Produce an examiner one-pager answering *“Is Active Directory authoritative for workforce identity?”*
- Handle contractor/vendor edge cases (`raj.external`) without letting directories fill HR gaps
- Close the directory connector arc before JDBC with a signed authoritative register

---

## Why this matters

**Business.** If `MNB-ActiveDirectory` can create identities, a rogue service account, a mis-typed contractor in AD, or a stale rehire sAMAccountName becomes an Identity cube — bypassing HR joiner controls, background checks, and termination feeds. Meridian saw the near-miss pattern when a duplicated AD account for a departed contractor briefly correlated wrong and almost received `WIRE_INIT` via a birthright glitch. Split-brain (HR says terminated, AD-created cube still “alive” in IIQ) is how banks fail access reviews.

**Control / audit.** Examiners ask: *“Show every Application that can create an identity cube.”* Your answer is a short register: `MNB-HR` (and approved HRIS only). Every directory Application screenshot must show create-identities **off**. “The directory said so” must never override HR termination.

---

## Concepts

### Authoritative source vs account target

An **authoritative application** is allowed to **create and own the lifecycle of Identity cubes** (people). A **target application** holds **accounts** (Links) that correlate to those cubes. Confusing the two is the root of directory split-brain.

| Source | Authoritative? | Creates identities? | Role at Meridian |
| --- | --- | --- | --- |
| `MNB-HR` | Yes | Yes | Workforce truth (hire, term, manager, employeeId) |
| `MNB-ActiveDirectory` | No | No | Workstation / app directory **target** |
| `MNB-EntraID` | No | No | Cloud directory **target** |
| `MNB-OpenLDAP` | No | No | Embedded / midrange directory **target** |
| `MNB-LDIF-DirectoryDump` | No | No | Offline evidence only |
| `MNB-IT-Access` | No | No | Non-authoritative access inventory |

### Split-brain: the failure mode

```
  CORRECT                         WRONG (split-brain)
  ────────                        ──────────────────
  HR hire                         AD aggregate with create ON
    → cube                        → cube named after sAMAccountName
    → provision AD                  (no HR `userId`, no term feed)
    → AD aggregate correlates     → HR later creates SECOND cube
    → one person, one cube        → certifications review ghosts
```

**Real-life Meridian example.** `raj.external` appears in an IT dump and in AD before the HR contractor row is clean. If Entra/AD create-identities is on, IIQ invents a cube. When HR finally loads the contractor, you get duplicates, broken manager hierarchy, and a leaver that disables one cube while the directory-born twin keeps entitlements.

### Exception process

Only **Architecture + HR** can add a second authoritative source (e.g., future Workday co-authoritative — Lesson 77 preview). Never silently via AD, Entra, OpenLDAP, or LDIF. Exceptions are written, time-bounded, and examined.

### Leaver truth

HR termination drives disable/remove plans **to** directories. Directories do not “uncreate” HR identities. A residual AD account after an HR leaver is a **provisioning control failure**, not proof that “AD is authoritative.”

---

## How it works

IdentityIQ’s application flags (authoritative / create identities — labels vary by version) control whether aggregation may spawn Identity objects. Correlation rules attach Links to existing cubes when create is off; failures become **uncorrelated accounts** (Lesson 19), which is the desired fail-closed behavior for directories.

```
  HR event (hire / term)
        │
        ▼
  MNB-HR aggregate → create / update Identity cube
        │
        ▼
  Provision to directory targets (AD / Entra / LDAP)
        │
        ▼
  Directories aggregate → correlate Links back to cube
        │
        X  directories must not create new cubes
```

| Flag audit outcome | Meaning | Action |
| --- | --- | --- |
| HR = create on | Expected | Keep |
| Directory = create on | Finding | Disable immediately; hunt orphans |
| Directory = create off, uncorrelated accounts | Healthy fail-closed | Remediate via Lesson 19 |
| Dual authoritative HR + AD | Severe misconfig | Remove AD authoritative; incident note |

---

## Real-world setup (outside IIQ)

### Step 1 — Architecture decision record

1. Write (or confirm) Meridian’s authoritative-source ADR: HRIS extract / Workday is workforce truth; directories are targets.
2. Name approvers: HR data steward + IAM architecture (`helen.ross` in lab).

### Step 2 — Inventory every identity-creating app

1. List all Applications in the lab (and eventually prod) that can create identities.
2. For each non-HR entry, require a written exception or disable create.

### Step 3 — Joiner sequencing SLA

1. HR file lands and aggregates **before** directory create provisioning runs.
2. Directory aggregation runs **after** cubes exist so correlation succeeds.
3. Document the schedule dependency (same pattern as Lesson 58: nightly after HR).

### Step 4 — Orphan cleanup playbook

1. If create was ever left on, have a named cleanup: find identities with no HR link, freeze entitlements, merge or delete per HR confirmation.
2. Examiners will ask whether that playbook exists — not whether you promise it never happens.

---

## Before you start

- [ ] List all directory-related Applications from Lessons 56–60
- [ ] IIQ access to Application settings (or design notes for shells)
- [ ] Lesson 09 IT Access non-authoritative discipline recalled
- [ ] IIQ up at `http://localhost:8080/identityiq`

---

## Lab procedure

### Task 1 — Authoritative source register

Every exam starts with “who can create a person?” Build the register first.

1. Create `~/iiq-lab-data/connectors/MNB-authoritative-register-62.md`:

| Application | Auth? | Create IDs? | Owner |
| --- | --- | --- | --- |
| `MNB-HR` | Y | Y | HR / IAM |
| `MNB-ActiveDirectory` | N | N | Technology |
| `MNB-EntraID` | N | N | Cloud IAM |
| `MNB-OpenLDAP` | N | N | Lab / platform |
| `MNB-LDIF-DirectoryDump` | N | N | IAM evidence |
| `MNB-IT-Access` | N | N | Technology |

2. Sign the statement: *“No directory creates identities at Meridian.”*

**Expected result:** Register file complete with signed statement.

### Task 2 — Flag audit (UI and/or notes)

Design notes are acceptable for shells; live flags must match.

1. For each directory app that exists in IIQ, open settings and confirm authoritative / create-identities flags.
2. For notes-only shells, audit the design notes — mark “verified in notes.”
3. Screenshot or quote the create-identities setting for at least `MNB-ActiveDirectory` (or its design card).
4. If any directory has create on: **disable immediately** and file an incident note if orphan cubes appeared.

**Expected result:** Audit table with Verified-in-UI or Verified-in-notes per app; all N/N except HR.

### Task 3 — Correlation-first joiner storyboard

Teach the happy path with `nina.joiner`.

| Step | System | Outcome |
| --- | --- | --- |
| 1 | HR file aggregate | Cube created with employeeId |
| 2 | Provision AD | Account created for **existing** cube |
| 3 | Aggregate AD | Link correlates; no second cube |

Anti-storyboard: AD aggregated first with create on → orphan cube named after sAMAccountName → HR later creates a duplicate → certifications and leavers diverge.

**Expected result:** Both storyboards in the register file.

### Task 4 — Leaver truth paragraph

1. Write: HR termination drives disable plans to directories; directories do not uncreate HR identities.
2. Add: residual AD account after HR leaver = provisioning control failure, not “AD authoritative.”
3. Tie to Lesson 61: password/disable operations target directory apps; they do not redefine who the person is.

**Expected result:** Leaver truth paragraph in the register.

### Task 5 — Examiner one-pager

1. Half-page answer to: *“Is Active Directory authoritative for workforce identity?”*
2. Include register table excerpt and one screenshot/note reference.
3. Store in binder as `MNB-authoritative-examiner-62.md` (or a section of the register).

**Expected result:** One-pager ready for exam simulation.

### Task 6 — Contractor / vendor edge case (`raj.external`)

Contractors are where teams are tempted to “just let AD create the cube.”

1. Scenario: `raj.external` appears in IT dumps or directories before HR contractor feed is clean.
2. Control: contractors still require an approved authoritative path (HR contractor row or Architecture exception) — directories must not fill the gap by creating cubes.
3. If an orphan `raj.external` cube already exists: disable create + Lesson 19-style remediation.

**Expected result:** Edge-case paragraph in the register file.

### Task 7 — Entra guest / B2B note

1. Write one paragraph: Entra guest accounts must not invent workforce cubes via create-identities; B2B has a separate process.
2. Flag risk: guest UPNs that look like `@meridiannb.com` aliases still are not HR hires.

**Expected result:** B2B note added.

### Task 8 — CHANGELOG

1. “Lesson 62 authoritative register confirmed for directory apps.”

**Expected result:** CHANGELOG line.

---

## Acceptance criteria

- [ ] Authoritative register includes HR + all directory apps
- [ ] Flag audit completed (UI and/or notes); directories N/N
- [ ] Joiner correlation storyboard + anti-storyboard written
- [ ] Leaver truth + contractor edge case + Entra guest note documented
- [ ] Examiner one-pager produced
- [ ] CHANGELOG updated

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Orphan cubes from AD | Create-identities on | Disable; cleanup process |
| Dual authoritative HR+AD | Misconfig | Remove AD authoritative |
| Contractors only in AD | Process gap | HR must source contractors or approved exception |
| Entra guests invent cubes | Create on | Disable; separate B2B process |
| LDIF created identities | Flag error | Disable; treat as evidence only |
| Uncorrelated directory accounts | Create off (good) + bad correlation | Fix correlation; do **not** enable create |

---

## Training binder evidence

- `MNB-authoritative-register-62.md`
- Flag audit results (UI quotes / screenshots)
- Examiner one-pager
- Joiner / anti-joiner storyboards

**Examiner question:** *“Show every Application that can create an identity cube.”*

---

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
4. No — HR drives termination; directories receive disable/provisioning.
5. No — offline evidence only.
6. Via an approved authoritative path (HR contractor row or Architecture exception) — not AD/Entra create.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “authoritative application” and “create identities” for version-specific flag names and aggregation behavior.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — threads on orphan identities and authoritative source misconfiguration.
- [NIST SP 800-63A — Enrollment and Identity Proofing](https://pages.nist.gov/800-63-3/sp800-63a.html) — why workforce identity proofing belongs with HR/IdP enrollment, not directory account discovery.
- [FFIEC Information Security Booklet](https://ithandbook.ffiec.gov/it-booklets/information-security.aspx) — examiner-oriented expectations for access control and lifecycle (search identity and access management themes).
- [CIS Controls v8 — Control 5 Account Management](https://www.cisecurity.org/controls/account-management) — inventory and lifecycle of accounts tied to authoritative personnel processes.

---

## Stretch lab

Draft an Architecture exception form for adding Workday as co-authoritative (Lesson 77 preview): scope, conflict resolution (HR vs Workday attribute wins), and rollback. Search IIQ for any Application with create-identities enabled; remediate non-HR. Tie the register to SoD: toxic entitlements must never invent people.

---

## Summary

- Directories are targets; HR is workforce truth — create-identities off on every directory app.
- Flag audits and joiner storyboards prevent split-brain before JDBC and SaaS connectors multiply account sources.
- Examiner one-pagers and contractor edge cases close the directory connector arc with evidence, not slogans.

---

**Previous:** [Lesson 61 — Password Management & Interceptor](61-password-management-interceptor.md)  
**Next:** [Lesson 63 — JDBC Connector Fundamentals](63-jdbc-connector-fundamentals.md)
