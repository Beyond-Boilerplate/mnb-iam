# Lesson 107 — Backup, DR & Object Recovery

| Field | Value |
| --- | --- |
| **Level** | Advanced |
| **Track** | Enterprise Hardening & Mastery |
| **Time** | 75–90 minutes |
| **Prereq** | [Lesson 106 — Performance Tuning IIQ](106-performance-tuning-iiq.md); [docs/SSD.md](../SSD.md) |
| **Lab data** | `config/` XML; DB backup tooling per LOCAL_SETUP / CNPG notes in HOMELAB-CD |

## Learning objectives

You will be able to:

- Separate **object recovery** (XML/git) from **data recovery** (database)
- Perform an object-level restore drill for one `MNB-*` configuration object
- Document DB backup RPO/RTO targets for Meridian IAM
- List what git does *not* protect (cubes, cert decisions, audit rows)
- Write a DR runbook outline for sandbox loss vs prod loss

## Why this matters

Losing IIQ is losing the bank’s access truth and certification history. Git saves your SoD policy XML; it does not save yesterday’s cert decisions unless the DB is backed up.

**Control / audit:** Examiners ask for restore evidence, not only backup job green lights. Meridian needs periodic restore drills with dated proof.

## Concepts

| Asset | Protected by | Restore method |
| --- | --- | --- |
| Roles, policies, apps, workflows | git `config/` + SSB | Rebuild WAR + importdynamic |
| Plugins / Java | git `pluginsrc` / `src` | Rebuild image/WAR |
| Identity cubes, links, requests | Database backups | DB restore / PITR |
| Audit events | DB + SIEM | DB and/or SIEM rehydrate |
| Task Results | Database | DB restore |

```text
  Incident: deleted MNB SoD policy
        |
        +--> Preferred: git checkout + importdynamic
        |
  Incident: corrupted DB / site loss
        |
        +--> Restore DB to RPO --> start app --> smoke --> reconcile connectors
```

**RPO/RTO lab starters:** RPO ≤ 24h lab / ≤ 15–60m prod DB; RTO ≤ 8h lab / per business IAM tier.

## Before you start

- [ ] Identify DB engine (MySQL lab / Postgres CNPG homelab)
- [ ] Confirm `config/` has at least one Meridian object committed or local
- [ ] Spare file path for export drills: `~/iiq-lab-data/dr/`
- [ ] Know who owns DB backups (platform) vs IIQ objects (IAM)

## Lab procedure

### Task 1 — Asset classification

1. Create table: Asset | git? | DB? | SIEM? | Owner.
2. Include: SoD policy, birthright role, identity `helen.ross`, open cert, AuditConfig, plugin toolkit.
3. Mark each restore path.

**Expected result:** Classification table complete.

### Task 2 — Object export insurance

1. Debug-export Workgroup `MNB-WG-IAM-Ops` (or substitute Meridian object).
2. Save `~/iiq-lab-data/dr/MNB-WG-IAM-Ops-YYYY-MM-DD.xml`.
3. Confirm identical content exists under `config/` or schedule adding it (Lesson 101).

**Expected result:** Dated cold copy outside the running server.

**If it fails:** Any `MNB-*` object export counts.

### Task 3 — Object recovery drill

1. In UI, change the workgroup description to `DR-DRILL-TEMP`.
2. Re-import the dated XML via console or UI import (Lesson 99).
3. Confirm description restored.
4. Log drill: time started/ended, operator, ticket `LAB-DR-107`.

**Expected result:** Successful object restore with timing.

**If it fails:** Re-import from `config/` copy; still record lessons learned.

### Task 4 — DB backup evidence (platform)

1. Locate how lab DB backups run (mysqldump cron, CNPG scheduled backup, volume snapshot).
2. Capture proof: last successful backup timestamp (screenshot/log).
3. If none exist, file **critical** residual risk and propose a backup job—do not pretend.

**Expected result:** Backup proof **or** explicit critical gap.

### Task 5 — RPO/RTO + runbook outline

1. Write RPO/RTO for lab and proposed prod.
2. Outline steps: declare incident → freeze changes → restore DB → deploy known-good WAR (git SHA) → importdynamic if needed → smoke login → aggregation health → notify SOC.
3. Include communication tree: `helen.ross`, platform on-call, SOC.

**Expected result:** Two-page runbook outline.

### Task 6 — What git cannot save (quiz yourself)

1. List five object types only in DB.
2. State Meridian policy: certifications and audit retained per records schedule even after role XML rebuild.
3. Add SIEM retention cross-check (Lesson 104).

**Expected result:** Written “git limits” list in binder.

## Acceptance criteria

- [ ] Asset classification table done
- [ ] Dated object export stored
- [ ] Object restore drill timed and logged
- [ ] DB backup proof or critical risk filed
- [ ] RPO/RTO + runbook outline written
- [ ] Git limitation list completed

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Import won’t overwrite | Name/id mismatch | Use exact object name; check created/modified |
| Restore old XML loses newer needed changes | Wrong version | Restore from git SHA that matches last good prod |
| DB restore orphans WAR | Version skew | Align WAR SHA to DB vintage |
| No backups | Gap | Escalate platform immediately |
| Drill skipped “too risky” | Culture | Use sandbox only—drills are mandatory |

## Training binder evidence

- Classification table  
- Export path + restore timing log  
- Backup proof or risk ID  
- Runbook outline  

## Knowledge check

1. What does git protect vs the database?
2. What is RPO vs RTO?
3. Why align WAR SHA with DB restore point?
4. Name two assets SIEM might retain longer than IIQ DB.
5. What ticket style should DR drills use?

### Answers

1. git: configuration/code; DB: runtime identities, requests, certs, audits, task history.  
2. RPO = how much data loss acceptable; RTO = how fast service must return.  
3. Prevent schema/object incompatibilities and phantom config.  
4. Audit/auth events (and detection context).  
5. Named drill tickets (e.g., `LAB-DR-107`) with times and operators.

## Stretch lab

Script a weekly export of all `MNB-*` Configuration/Policy objects to dated DR folders (console or SSB).

## Summary

- Practice object restore from XML; demand DB backup proof for cubes/certs.
- Runbooks beat tribal restore knowledge.
- Git is necessary and insufficient—know the boundary.

## Restore tiers

| Tier | Scenario | Action |
| --- | --- | --- |
| T0 | Single object deleted | XML import from git/DR folder |
| T1 | Bad importdynamic batch | Revert SHA + re-import known good set |
| T2 | App corruption / bad deploy | Redeploy previous WAR/image tag |
| T3 | Site / DB loss | DB PITR + WAR align + smoke + connector reconcile |

### Task 7 — Cert history awareness drill

1. Explain to a peer why restoring DB from last week rewrites certification state.
2. Document: config-only recovery does **not** restore in-flight cert decisions.
3. Add RR note if backups untested.

**Expected result:** Peer explanation notes signed/dated.

### Homelab CNPG

If using CloudNativePG, record where backup schedules live and who operates them (platform). IAM still owns object export drills.

## Evidence pack for DR exams

Examiners often ask for the last successful restore—not the last successful backup. Keep:

1. Object drill log (`LAB-DR-107`) with timestamps
2. DB backup job screenshot/log
3. Runbook outline with contacts
4. List of git SHAs known-good for WAR rebuild

Store under `~/iiq-lab-data/dr/evidence/YYYY-MM-DD/`.

### Immutable backups note

Prefer backup storage that operators cannot silently overwrite. If lab uses writable folders only, call out residual risk for prod object-store immutability.

---

**Previous:** [Lesson 106 — Performance Tuning IIQ](106-performance-tuning-iiq.md)  
**Next:** [Lesson 108 — Multi-Environment Promotion](108-multi-env-promotion.md)
