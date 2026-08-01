# Lesson 60 — LDIF Connector

**Level:** Intermediate  
**Track:** Connectors — Directory  
**Time:** 75–90 min  
**Prereq:** Lesson 58 — LDAP / OpenLDAP Connector; Lesson 59 — Azure / Entra ID Connector  

**Lab data:**
- Repo: `lab-data/connectors/ldap/mnb-openldap.ldif` (copy to `~/iiq-lab-data/connectors/ldap/`)
- Contrast app: `MNB-OpenLDAP` from Lesson 58 (live bind path)
- Repo: `lab-data/connectors/features-string-glossary.md`

---

## Learning objectives

You will be able to:

- Explain when Meridian uses an **LDIF connector** (file dump) versus a live LDAP/AD bind, and why banks need both
- Classify a directory dump: DN counts, objectClasses, as-of timestamp, and chain-of-custody hash
- Create and configure **MNB-LDIF-DirectoryDump** against an offline LDIF with create-identities off
- Run Account Aggregation from the dump and reconcile counts against `grep '^dn:'` predictions
- Document connector limitations (`NO_RANDOM_ACCESS`, no password/enable) so JML never targets the LDIF app
- Produce examiner-ready offline evidence when VPN to LDAP is down

---

## Why this matters

**Business.** Last year Meridian’s M&A team received an LDIF export from a regional bank’s wire platform three days before the VPN tunnel to that directory was cut. `priya.wire`-equivalent accounts and `wire-initiators` memberships had to be correlated and certified *from the file*, not from a live bind. Banks also face air-gapped evidence requests, broken VPN weeks, and laptop labs with no network to LDAP. An engineer who only knows Lesson 58’s live OpenLDAP path cannot answer those moments.

**Control / audit.** Examiners ask: *“If VPN to LDAP is down, how do you still evidence last-known directory membership?”* The answer is a labeled **offline evidence** application, a hashed dump with as-of metadata, and an aggregation Task Result — not a spreadsheet someone emailed. Treating the LDIF app as a provisioning target creates false enable/password promises and fails the next exam.

---

## Concepts

### LDIF is a serialization, not a directory

**LDIF (LDAP Data Interchange Format)** is a text encoding of directory entries — the same entries Lesson 58 searched live with `ldapsearch`. Each entry starts with a `dn:` line and lists attributes. An **LDIF connector** in IdentityIQ iterates that file; it does not open TCP 389 and bind. Contrast:

| | Live LDAP / OpenLDAP (Lesson 58) | LDIF connector (this lesson) |
| --- | --- | --- |
| Transport | Bind to server (`ldap://` / `ldaps://`) | Read a file on disk |
| Freshness | Near real-time | As-of dump timestamp |
| Features | Often SEARCH + PROVISIONING + ENABLE | Typically iterate / `NO_RANDOM_ACCESS` |
| Password / disable | Possible if directory supports it | **Never** — no live target |
| Meridian use | BAU directory targets | Offline lab, DR, M&A, air-gapped evidence |

The naive mistake: schedule the LDIF app nightly next to `MNB-OpenLDAP` and treat both as equal sources of truth. That duplicates accounts, fights over correlation, and confuses which app owns JML. Curriculum default: **LDIF aggregate is ad-hoc / evidence**, not nightly BAU, unless Architecture explicitly schedules a controlled dump feed.

### When Meridian reaches for LDIF

Three bank scenarios show up repeatedly:

1. **M&A / vendor extract** — counterparty will not grant bind credentials; they ship an LDIF on a secure share.
2. **DR / evidence window** — live directory is unreachable; last known good dump is still certifiable inventory.
3. **Laptop / air-gapped training** — no Docker LDAP, but the same schema truths as Lesson 58.

In all three, the dump is **non-authoritative**. `MNB-HR` still creates identities; the LDIF app only attaches Links and entitlements for correlation and certification prep.

### Iterate-only and NO_RANDOM_ACCESS

File connectors often lack **random access** — IIQ cannot efficiently “get this one DN by key” the way a live LDAP Get Object can. Aggregation walks the file front to back. That is fine for inventory; it is fatal for password reset and interactive unlock, which need a live target. Record the limitation before anyone asks helpdesk to “reset via the LDIF app.”

```
  Vendor / AD / OpenLDAP export
        │  LDIF dump (as-of timestamp + SHA-256)
        ▼
  MNB-LDIF-DirectoryDump  (LDIF connector type)
        │  iterate file → accounts + groups
        ▼
  Account Aggregation → correlate to HR cubes
        │
        X  no PASSWORD / ENABLE / live provision
```

Reuse the Lesson 58 fixture `mnb-openldap.ldif` as the dump — same two people, same `wire-initiators` group — so you can contrast live vs file against identical content.

---

## How it works

The SailPoint **LDIF** application type reads entries from a path visible to the IIQ host (or container). Schema mapping mirrors LDAP (`uid`, `inetOrgPerson`, `groupOfNames` / `member`) because the *data model* is LDAP; only the *transport* changed.

```
IdentityIQ (MNB-LDIF-DirectoryDump)
        │  file: ~/iiq-lab-data/connectors/ldap/mnb-openldap.ldif
        ▼
LDIF parser iterates dn: blocks
        ├── inetOrgPerson → account Links (uid = native identity)
        ├── groupOfNames  → ManagedAttributes
        └── member DNs    → entitlement memberships on accounts
```

| Operation | LDIF behavior | IIQ behavior |
| --- | --- | --- |
| Account aggregation | Parse people entries in file order | One Link per `inetOrgPerson` |
| Group aggregation | Parse `groupOfNames` entries | Entitlements + memberships |
| Get Object / SEARCH | Often unsupported or full rescan | Expect `NO_RANDOM_ACCESS` limits |
| Password / ENABLE | Impossible | Must route to live AD/LDAP apps |
| Provisioning | Not a production pattern | Keep features off; document |

| LDIF attribute | Schema use (same as Lesson 58) |
| --- | --- |
| `uid` | Account native identity |
| `employeeNumber` | Correlation to identity `userId` |
| `mail` | Email quality check |
| `member` on groups | Entitlement membership |

---

## Real-world setup (outside IIQ)

Even when the “server” is a file, production engineers still do work outside IIQ before the dump is trustworthy.

### Step 1 — Obtain the dump under change control

1. Ticket/CRQ: who requested the extract, which directory, which subtree, and why (M&A, DR drill, exam evidence).
2. Producer: directory owner or vendor contact — never an anonymous USB drop.
3. Transfer: secure share or encrypted media; record intake time.

### Step 2 — Integrity and as-of metadata

1. Record file mtime (or producer’s stated export time) as the **as-of** timestamp.
2. Hash on intake:

```bash
shasum -a 256 ~/iiq-lab-data/connectors/ldap/mnb-openldap.ldif
```

3. Store hash + producer + ticket ID with the dump. If the hash changes later without a new intake ticket, treat the file as untrusted for exam evidence.

### Step 3 — Validate LDIF before IIQ

1. Count DNs: `grep -c '^dn:' mnb-openldap.ldif`.
2. Spot-check objectClasses (`inetOrgPerson`, `groupOfNames`) — same discipline as predicting Lesson 58 aggregation from LDIF.
3. Confirm IIQ’s runtime can **read** the absolute path (host path vs Docker volume mount). Path/permissions failures look like “0 accounts,” not parse errors.

### Step 4 — Label the application

Production naming and binder tabs must say **OFFLINE EVIDENCE**. Live OpenLDAP/AD apps still own provisioning. Architecture must approve any rare case where a scheduled dump feed becomes BAU inventory.

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq` as `spadmin`; Lesson 58 `MNB-OpenLDAP` design available for contrast
- [ ] `mnb-openldap.ldif` copied to `~/iiq-lab-data/connectors/ldap/`
- [ ] Absolute path to the LDIF recorded (IIQ/container must see it)
- [ ] Feature glossary open — expect iterate / `NO_RANDOM_ACCESS` style limits
- [ ] `MNB-HR` identities exist so correlation has targets

---

## Lab procedure

### Task 1 — Classify the dump

Before creating an application, know what the file contains — the same prediction discipline as Lesson 58, applied to a file instead of a live search.

1. From the lab copy:

```bash
wc -l ~/iiq-lab-data/connectors/ldap/mnb-openldap.ldif
grep -c '^dn:' ~/iiq-lab-data/connectors/ldap/mnb-openldap.ldif
grep '^dn:' ~/iiq-lab-data/connectors/ldap/mnb-openldap.ldif
```

2. Record as-of date (file mtime is acceptable for lab).
3. Confirm people + groups: expect DNs for suffix, `ou=people`, `ou=groups`, `helen.ross`, `priya.wire`, `wire-initiators` (6 `dn:` lines).
4. Write the aggregation prediction: **2 accounts, 1 group, Priya in `wire-initiators`.**

**Expected result:** DN count, as-of timestamp, and prediction card in your notebook.

**If it fails:** Re-copy from `lab-data/connectors/ldap/mnb-openldap.ldif`.

### Task 2 — Chain of custody

Offline evidence is only as strong as its provenance. Hash and producer notes turn a random file into examiner material.

1. Run `shasum -a 256` on the LDIF; paste the hash into notes.
2. Record producer as *Meridian lab fixture / Lesson 58 bootstrap* (in production: ticket ID + directory owner name).
3. Start `~/iiq-lab-data/connectors/ldap/MNB-LDIF-limits-60.md` with a chain-of-custody block (hash, as-of, producer, ticket).

**Expected result:** Custody block present before the app exists.

**If it fails (unknown producer in a real dump):** Mark dump untrusted for exam evidence until sourced.

### Task 3 — Create MNB-LDIF-DirectoryDump

In production this consumes the intake path from Step 1; here it points at the Lesson 58 fixture used as an offline dump.

1. Applications → Add New → **LDIF** connector type (or equivalent menu path).
2. Name: `MNB-LDIF-DirectoryDump`. Owner: `helen.ross` (lab session as `spadmin`).
3. File path: absolute path to `~/iiq-lab-data/connectors/ldap/mnb-openldap.ldif`.
4. Non-authoritative; **create-identities OFF**.
5. Save.

**Expected result:** Application listed with file path set; not marked authoritative.

**If it fails:** If LDIF type is absent from your build, document the full design in the limits file and complete Tasks 4–7 as notes-only — do **not** quietly convert to DelimitedFile unless you first transform attributes (not preferred).

### Task 4 — Schema, correlation, and hard limitations

Governance can only see what the schema exposes; limitations prevent false JML promises.

1. Account schema: native identity `uid`; attributes `cn`, `sn`, `mail`, `employeeNumber` — same map as Lesson 58.
2. Groups: `groupOfNames` / `member` as entitlement attribute.
3. Correlation: `employeeNumber` ↔ `employeeId` primary; `uid` ↔ `userName` fallback. Create-identities remains **No**.
4. Complete the limitations table in `MNB-LDIF-limits-60.md`:

| Capability | On LDIF app? |
| --- | --- |
| Aggregate accounts/groups | Yes |
| Random search / Get Object | Usually no (`NO_RANDOM_ACCESS`) |
| Password reset | **No** |
| Live disable / ENABLE | **No** |
| Nightly BAU (curriculum default) | **No** — ad-hoc / evidence |

**Expected result:** Limits file states no password/enable; correlation matches Lesson 58.

### Task 5 — Aggregate the dump

Aggregation is the inventory proof — reconcile against Task 1’s prediction, not against “task green.”

1. Tasks → New → Account Aggregation: `Aggregate MNB-LDIF-DirectoryDump` (alias `MNB-LDIF-DirectoryDump-Account-Aggregation`).
2. Run Now. Record accounts scanned/created/updated.
3. Spot-check: `helen.ross` and `priya.wire` Links; Priya carries `wire-initiators` if group aggregation is configured.
4. Confirm zero new identity cubes — HR remains authoritative.

**Expected result:** Task success; account count matches people DNs (2); prediction reconciled.

**If it fails:** Path/permissions or Docker volume mount — IIQ cannot read the host path; fix absolute path / mounts and re-run.

### Task 6 — Contrast with MNB-OpenLDAP

Write the decision table you will reuse in architecture reviews.

1. In the limits file, add:

| Situation | Use |
| --- | --- |
| BAU nightly inventory + provisioning | `MNB-OpenLDAP` (live bind) |
| VPN down / M&A dump / air-gapped evidence | `MNB-LDIF-DirectoryDump` |
| Helpdesk password / disable | Live AD/LDAP apps only |

2. Runbook note: *LDIF aggregate is ad-hoc / evidence unless Architecture schedules a controlled dump feed.*
3. Dual-aggregate warning: do not schedule both apps nightly against the same logical directory without a written purpose.

**Expected result:** Contrast paragraph + runbook note in the limits file.

### Task 7 — Binder label and CHANGELOG

1. Label the binder tab: **OFFLINE EVIDENCE — not production provisioning.**
2. CHANGELOG: “Lesson 60 offline LDIF application for directory dumps.”
3. Examiner one-liner ready: last-known membership = hashed dump + aggregation Task Result on `MNB-LDIF-DirectoryDump`.

**Expected result:** CHANGELOG + binder label.

### Task 8 — Residual risk

Record `RR-LDIF-STALE-01`: *Offline dumps go stale; certifications from LDIF inventory must state the as-of timestamp and must not be treated as live revocation proof.* Owner: `helen.ross`.

**Expected result:** Residual risk logged with owner.

---

## Acceptance criteria

- [ ] LDIF DN count / as-of / prediction recorded before aggregation
- [ ] SHA-256 chain-of-custody block saved
- [ ] `MNB-LDIF-DirectoryDump` created (or equivalent design if type missing)
- [ ] Limits file documents no password/enable and ad-hoc scheduling
- [ ] Aggregate task run **or** path failure documented with fix attempt
- [ ] Contrast vs live OpenLDAP written; binder labeled offline evidence
- [ ] `RR-LDIF-STALE-01` recorded

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| 0 accounts | Path not visible to IIQ | Fix absolute path / Docker volume mount |
| Parse errors | Corrupt or truncated LDIF | Re-copy fixture; validate `dn:` lines |
| Provision / password UI tempting | Wrong application selected | Use live directory apps for JML |
| Duplicate Links with OpenLDAP | Dual nightly aggregate | Unschedule LDIF or document deliberate dual-feed |
| Create identities spawned cubes | Flag left on | Disable immediately; remediate orphans (Lesson 19) |
| Counts ≠ prediction | Wrong file or filter | Re-run Task 1 classification on the path the app uses |

---

## Training binder evidence

- Application path screenshot (password N/A; path visible)
- Aggregate Task Result reconciled to DN prediction
- `MNB-LDIF-limits-60.md` (limits, custody hash, contrast, residual risk)
- As-of dump timestamp and binder **OFFLINE EVIDENCE** label

**Examiner question:** *“If VPN to LDAP is down, how do you still evidence last-known directory membership?”*

---

## Knowledge check

1. What Meridian file is used as the LDIF dump in this lesson?
2. Should LDIF apps perform password reset?
3. Typical access-pattern feature for file/LDIF sources?
4. Is the LDIF app authoritative for workforce identity?
5. Nightly BAU vs ad-hoc — what is the curriculum default?
6. Why record a SHA-256 hash of the LDIF dump?

### Answers

1. `lab-data/connectors/ldap/mnb-openldap.ldif` (runtime under `~/iiq-lab-data/connectors/ldap/`).
2. No — there is no live directory to set a password on.
3. Iterate / `NO_RANDOM_ACCESS` style behavior.
4. No — offline evidence only; `MNB-HR` remains authoritative.
5. Ad-hoc / evidence unless Architecture schedules otherwise.
6. Chain of custody — prove the examiner evidence file was not altered after intake.

---

## Further reading

- [RFC 2849 — The LDAP Data Interchange Format (LDIF)](https://datatracker.ietf.org/doc/html/rfc2849) — the wire format you are aggregating; skim entry and change-record sections.
- [OpenLDAP Admin Guide — LDIF](https://www.openldap.org/doc/admin26/dbtools.html) — how real directories export/import LDIF; useful when a vendor’s dump looks “almost” valid.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “LDIF connector” for version-specific application settings and feature limits.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — search “LDIF aggregation” for path/mount and parse issues in containerized IIQ.
- [NIST SP 800-53 AU-10 / AU family overview](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — integrity and non-repudiation themes behind hashing dumps for evidence (search AU controls in the PDF).

---

## Stretch lab

Produce a second “stale” LDIF with `samir.hassan` removed (or add him then remove him) and diff two aggregation Task Results — practice explaining as-of drift to an examiner. Script export instructions for a Windows AD LDIF dump into Meridian naming (`MNB-*-DirectoryDump-YYYYMMDD.ldif`). Map LDIF group members into a certification preview population for `wire-initiators`.

---

## Summary

- LDIF connectors unlock offline directory evidence and laptop labs when live bind is impossible.
- `MNB-LDIF-DirectoryDump` aggregates the same schema truths as Lesson 58; it does not replace live AD/LDAP provisioning.
- Hash, as-of metadata, and explicit no-password/enable limits make dump evidence examiner-ready.

---

**Previous:** [Lesson 59 — Azure / Entra ID Connector](59-azure-entra-id-connector.md)  
**Next:** [Lesson 61 — Password Management & Interceptor](61-password-management-interceptor.md)
