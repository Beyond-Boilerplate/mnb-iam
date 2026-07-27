# Lesson 60 — LDIF Connector

| Field | Value |
| --- | --- |
| **Level** | Intermediate |
| **Track** | Connectors — Directory |
| **Time** | 60–75 minutes |
| **Prereq** | Lesson 58–59; LDIF fixture familiarity |
| **Lab data** | `~/iiq-lab-data/connectors/ldap/mnb-openldap.ldif` |

## Learning objectives

You will be able to:

- Explain when Meridian uses an LDIF connector vs live LDAP/AD
- Create Application `MNB-LDIF-DirectoryDump` pointed at offline LDIF
- Configure iterate-only aggregation from directory dumps
- Use LDIF for DR evidence, vendor extracts, and laptop labs without bind
- Document limitations (`NO_RANDOM_ACCESS`, limited provisioning)

## Why this matters

Banks receive directory dumps for M&A, air-gapped evidence, or broken VPN weeks. LDIF connectors let IAM continue correlation and certification prep when live LDAP is unavailable. Treating LDIF as a full provisioning target creates false enable/password promises.

**Control / audit:** Label LDIF apps as **evidence / offline** sources. Examiners should see why live OpenLDAP/AD apps still own provisioning.

## Concepts

| Mode | Live LDAP/AD | LDIF connector |
| --- | --- | --- |
| Transport | Bind to server | Read file |
| Features | Often SEARCH + PROVISIONING | Typically iterate / limited |
| Freshness | Near real-time | As-of dump timestamp |
| Meridian use | BAU targets | Offline lab, DR, M&A |

```text
  Export / vendor LDIF dump
        |
        v
  MNB-LDIF-DirectoryDump (Delimited? No — LDIF type)
        |
        v
  Aggregate → correlate → certify prep
        |
        X  (no live password/enable)
```

Reuse `mnb-openldap.ldif` as the dump file for training.

## Before you start

- [ ] Absolute path to `mnb-openldap.ldif` recorded
- [ ] `MNB-OpenLDAP` design from Lesson 58 available for contrast
- [ ] Feature glossary: expect `NO_RANDOM_ACCESS` style limits
- [ ] IIQ up

## Lab procedure

### Task 1 — Classify the dump

1. `wc -l` and `grep '^dn:'` count on the LDIF.
2. Record dump “as-of” date in notes (file mtime OK).
3. Confirm people + groups present.

**Expected result:** DN count and as-of timestamp in notebook.

### Task 2 — Create MNB-LDIF-DirectoryDump

1. Applications → Add New → **LDIF** connector type (or equivalent menu path).
2. Name: `MNB-LDIF-DirectoryDump`.
3. File path: absolute path to `~/iiq-lab-data/connectors/ldap/mnb-openldap.ldif`.
4. Non-authoritative; create-identities **off**.
5. Save.

**Expected result:** Application listed with file path set.

**If it fails:** If LDIF type absent, document maps using Lesson 58 schema file and create a **notes-only** app design—still complete lab-without-live-target below; optionally use DelimitedFile only if you first convert attributes (not preferred).

### Task 3 — Lab without live target — maps & limitations

1. Reuse correlation: `uid`↔`userName`, `employeeNumber`↔`employeeId`.
2. Write limitations block:

| Capability | On LDIF app? |
| --- | --- |
| Aggregate accounts/groups | Yes |
| Random search account | Usually no |
| Password reset | No |
| Live disable | No |

3. Save `~/iiq-lab-data/connectors/ldap/MNB-LDIF-limits-60.md`.

**Expected result:** Limits file states no password/enable on LDIF app.

### Task 4 — Aggregate the dump

1. Create Account Aggregation task `Aggregate MNB-LDIF-DirectoryDump`.
2. Run Now.
3. Spot-check `helen.ross`, `priya.wire` account links if correlation works; else confirm accounts exist on application.

**Expected result:** Task success; accounts ≥ people DNs in LDIF (or documented schema gap).

**If it fails:** Path/permissions; confirm IIQ container can read host path (Docker volume mounts).

### Task 5 — Contrast with MNB-OpenLDAP

1. Table: when to use LDIF dump vs live OpenLDAP.
2. Runbook: LDIF aggregate is **ad-hoc / evidence**, not nightly BAU unless Architecture says otherwise.

**Expected result:** Contrast paragraph + runbook note.

### Task 6 — Chain of custody for dumps

1. Record who produced the LDIF, ticket/CRQ number, and hash:

```bash
shasum -a 256 ~/iiq-lab-data/connectors/ldap/mnb-openldap.ldif
```

2. Expected result: hash + producer noted. If it fails (unknown producer): mark dump untrusted for exam evidence until sourced.

**Expected result:** Chain-of-custody block in limits file.

### Task 7 — CHANGELOG + binder label

1. CHANGELOG: “Lesson 60 offline LDIF application for directory dumps.”
2. Label binder tab: OFFLINE EVIDENCE — not production provisioning.

**Expected result:** CHANGELOG + label.

## Acceptance criteria

- [ ] LDIF DN count / as-of recorded
- [ ] `MNB-LDIF-DirectoryDump` created or equivalent design
- [ ] Lab-without-live-target limits file saved
- [ ] Aggregate task run **or** blocked only by path with documented fix attempt
- [ ] Contrast vs live OpenLDAP written
- [ ] LDIF hash / chain-of-custody recorded
- [ ] Binder labeled offline evidence

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| 0 accounts | Path not visible to IIQ | Fix absolute path / volume mount |
| Parse errors | Bad LDIF | Validate with `ldap` tools or re-copy fixture |
| Provision button tempting | Wrong app | Use live directory apps for JML |
| Duplicate with OpenLDAP | Dual aggregate | Don’t schedule both nightly without purpose |
| Create identities | Default flag | Disable |

## Training binder evidence

- Application path screenshot
- Aggregate task result
- `MNB-LDIF-limits-60.md`
- As-of dump timestamp

**Examiner question:** “If VPN to LDAP is down, how do you still evidence last-known directory membership?”

## Knowledge check

1. What Meridian file is used as the LDIF dump in this lesson?
2. Should LDIF apps perform password reset?
3. Typical access pattern feature for file/LDIF sources?
4. Is the LDIF app authoritative?
5. Nightly BAU vs ad-hoc—what’s the curriculum default?
6. Why record a SHA-256 hash of the LDIF dump?

### Answers

1. `ldap/mnb-openldap.ldif`.
2. No.
3. Iterate / `NO_RANDOM_ACCESS` style behavior.
4. No.
5. Ad-hoc / evidence unless Architecture schedules otherwise.
6. Chain of custody—prove the examiner evidence file was not altered after intake.

## Stretch lab

- Produce a second “stale” LDIF with `samir.hassan` removed and diff aggregates.
- Script export instructions for Windows AD LDIF dumps (external) into Meridian naming.
- Map LDIF group members into a certification preview population.

## Summary

- LDIF connectors unlock offline directory evidence and laptop labs.
- `MNB-LDIF-DirectoryDump` aggregates; it does not replace live AD/LDAP provisioning.
- Limits documentation prevents false JML promises.
- Hash and as-of metadata make dump evidence examiner-ready.

---

**Previous:** [Lesson 59 — Azure / Entra ID Connector](59-azure-entra-id-connector.md)  
**Next:** [Lesson 61 — Password Management & Interceptor](61-password-management-interceptor.md)
