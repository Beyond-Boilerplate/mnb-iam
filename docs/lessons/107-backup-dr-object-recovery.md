# Lesson 107 — Backup, DR & Object Recovery

**Level:** Advanced  
**Track:** Enterprise Hardening & Mastery  
**Time:** 75–90 min  
**Prereq:** Lesson 106 — Performance Tuning IIQ; [docs/SSD.md](../SSD.md)  

**Lab data:**
- `config/` XML
- DB backup tooling per LOCAL_SETUP / CNPG notes in HOMELAB-CD

---

## Learning objectives

You will be able to:

- Separate **object recovery** (XML/git) from **data recovery** (database)
- Perform an object-level restore drill for one `MNB-*` configuration object
- Document DB backup RPO/RTO targets for Meridian IAM
- List what git does *not* protect (cubes, cert decisions, audit rows)
- Write a DR runbook outline for sandbox loss vs prod loss
- Assemble an evidence pack examiners accept (restore proof, not only backup green lights)

---

## Why this matters

**Business.** Losing IIQ is losing the bank’s access truth and certification history. Git saves your SoD policy XML; it does not save yesterday’s cert decisions for `marcus.approve`’s campaign unless the DB is backed up. When someone deletes `MNB-SOD-Wire-DualControl` at 16:00 Friday, object restore from `config/` saves the weekend — if you practiced.

**Control / audit.** Examiners ask for **restore evidence**, not only backup job green lights. Meridian needs periodic restore drills with dated proof (`LAB-DR-107`). “We have backups” without a timed restore is a finding waiting to happen.

---

## Concepts

### Two recovery planes

| Asset | Protected by | Restore method |
| --- | --- | --- |
| Roles, policies, apps, workflows | git `config/` + SSB | Rebuild WAR + importdynamic |
| Plugins / Java | git `pluginsrc` / `src` | Rebuild image/WAR |
| Identity cubes, links, requests | Database backups | DB restore / PITR |
| Audit events | DB + SIEM | DB and/or SIEM rehydrate |
| Task Results | Database | DB restore |
| Cert decisions / history | Database | DB restore (config-only cannot recreate) |

```
  Incident: deleted MNB SoD policy
        │
        +--> Preferred: git checkout + importdynamic
        │
  Incident: corrupted DB / site loss
        │
        +--> Restore DB to RPO --> start app --> smoke --> reconcile connectors
```

### Restore tiers

| Tier | Scenario | Action |
| --- | --- | --- |
| T0 | Single object deleted | XML import from git/DR folder |
| T1 | Bad importdynamic batch | Revert SHA + re-import known good set |
| T2 | App corruption / bad deploy | Redeploy previous WAR/image tag |
| T3 | Site / DB loss | DB PITR + WAR align + smoke + connector reconcile |

**RPO/RTO lab starters:** RPO ≤ 24h lab / ≤ 15–60m prod DB; RTO ≤ 8h lab / per business IAM tier.

### Real-life Meridian example

Ops restored a week-old DB “to fix a bad role import” without realizing it rewound open certification decisions. Managers re-approved work already done. Lesson: config-only recovery does **not** restore in-flight cert state — and DB restore rewrites it. Align WAR SHA to DB vintage.

### Wrong way vs Meridian way

| Wrong way | Why it fails | Meridian way |
| --- | --- | --- |
| Git-only DR story | Cubes/certs/audit gone | Classify assets; DB backups mandatory |
| Backup green, never restore | Untested | Timed object + DB evidence |
| WAR/DB version skew | Schema/object ghosts | Align SHA to restore point |
| Writable-only backup folder | Silent overwrite | Prefer immutable object store in prod |

---

## How it works

| Role | Owns |
| --- | --- |
| IAM | Object export drills, `config/` hygiene, runbook content |
| Platform | DB backups (mysqldump / CNPG / snapshots), restore mechanics |
| SOC | SIEM retention cross-check (Lesson 104) |
| CAB | Approve T2/T3 restores in prod |

Communication tree: `helen.ross`, platform on-call, SOC.

---

## Real-world setup (DR you can demonstrate)

### Step 1 — Classify assets

1. Table: Asset | git? | DB? | SIEM? | Owner | restore path.

### Step 2 — Object insurance

1. Dated cold copies under `~/iiq-lab-data/dr/` plus `config/`.

### Step 3 — Prove restore (not only backup)

1. Object drill with ticket `LAB-DR-107`.
2. Capture DB backup proof or file critical gap.

### Step 4 — Runbook + evidence pack

1. RPO/RTO, steps, contacts, known-good WAR SHAs.
2. Prefer immutable backup storage in prod; call out lab residual risk.

---

## Before you start

- [ ] Identify DB engine (MySQL lab / Postgres CNPG homelab)
- [ ] Confirm `config/` has at least one Meridian object committed or local
- [ ] Spare file path for export drills: `~/iiq-lab-data/dr/`
- [ ] Know who owns DB backups (platform) vs IIQ objects (IAM)
- [ ] Sandbox-only for destructive drills

---

## Lab procedure

### Task 1 — Asset classification

1. Create table: Asset | git? | DB? | SIEM? | Owner.
2. Include: SoD policy, birthright role, identity `helen.ross`, open cert, AuditConfig, plugin toolkit.
3. Mark each restore path (T0–T3).

**Expected result:** Classification table complete.

### Task 2 — Object export insurance

1. Debug-export Workgroup `MNB-WG-IAM-Ops` (or substitute Meridian object).
2. Save `~/iiq-lab-data/dr/MNB-WG-IAM-Ops-YYYY-MM-DD.xml`.
3. Confirm identical content exists under `config/` or schedule adding it (Lesson 101).

**Expected result:** Dated cold copy outside the running server.

**If it fails:** Any `MNB-*` object export counts.

### Task 3 — Object recovery drill

Practice beats theory. Use sandbox only.

1. In UI, change the workgroup description to `DR-DRILL-TEMP`.
2. Re-import the dated XML via console or UI import (Lesson 99).
3. Confirm description restored.
4. Log drill: time started/ended, operator, ticket `LAB-DR-107`.

**Expected result:** Successful object restore with timing.

**If it fails:** Re-import from `config/` copy; still record lessons learned.

### Task 4 — DB backup evidence (platform)

1. Locate how lab DB backups run (mysqldump cron, CNPG scheduled backup, volume snapshot).
2. Capture proof: last successful backup timestamp (screenshot/log).
3. If none exist, file **critical** residual risk and propose a backup job — do not pretend.

**Expected result:** Backup proof **or** explicit critical gap.

### Task 5 — RPO/RTO + runbook outline

1. Write RPO/RTO for lab and proposed prod.
2. Outline steps: declare incident → freeze changes → restore DB → deploy known-good WAR (git SHA) → importdynamic if needed → smoke login → aggregation health → notify SOC.
3. Include communication tree: `helen.ross`, platform on-call, SOC.

**Expected result:** Two-page runbook outline.

### Task 6 — What git cannot save

1. List five object types only in DB.
2. State Meridian policy: certifications and audit retained per records schedule even after role XML rebuild.
3. Add SIEM retention cross-check (Lesson 104).

**Expected result:** Written “git limits” list in binder.

### Task 7 — Cert history awareness drill

1. Explain to a peer why restoring DB from last week rewrites certification state.
2. Document: config-only recovery does **not** restore in-flight cert decisions.
3. Add RR note if backups untested.

**Expected result:** Peer explanation notes signed/dated.

### Task 8 — Evidence pack assembly

Examiners often ask for the last successful **restore** — not the last successful backup. Keep:

1. Object drill log (`LAB-DR-107`) with timestamps
2. DB backup job screenshot/log
3. Runbook outline with contacts
4. List of git SHAs known-good for WAR rebuild

Store under `~/iiq-lab-data/dr/evidence/YYYY-MM-DD/`. Note immutable backups preference for prod.

**Expected result:** Evidence pack folder populated.

### Task 9 — Examiner question drill

*"Show evidence you can restore, not only that you back up."*

Write the three-artifact answer: (1) `LAB-DR-107` timed object restore log, (2) DB backup proof or critical RR-ID, (3) runbook outline with WAR SHA alignment step.

**Expected result:** Written proof steps in the binder.

---

## Acceptance criteria

- [ ] Asset classification table done
- [ ] Dated object export stored
- [ ] Object restore drill timed and logged
- [ ] DB backup proof or critical risk filed
- [ ] RPO/RTO + runbook outline written
- [ ] Git limitation list completed
- [ ] Cert history peer note signed
- [ ] Evidence pack assembled
- [ ] Examiner proof steps drafted

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Import won’t overwrite | Name/id mismatch | Use exact object name; check created/modified |
| Restore old XML loses newer needed changes | Wrong version | Restore from git SHA that matches last good prod |
| DB restore orphans WAR | Version skew | Align WAR SHA to DB vintage |
| No backups | Gap | Escalate platform immediately |
| Drill skipped “too risky” | Culture | Use sandbox only — drills are mandatory |
| Cert confusion after DB restore | Expected side effect | Communicate; avoid DB restore for config-only incidents |

---

## Training binder evidence

- Classification table
- Export path + restore timing log (`LAB-DR-107`)
- Backup proof or risk ID
- Runbook outline
- Git limits list + cert peer note
- Evidence pack path
- Examiner proof steps

---

## Knowledge check

1. What does git protect vs the database?
2. What is RPO vs RTO?
3. Why align WAR SHA with DB restore point?
4. Name two assets SIEM might retain longer than IIQ DB.
5. What ticket style should DR drills use?
6. Why can’t config-only recovery restore in-flight cert decisions?

### Answers

1. git: configuration/code; DB: runtime identities, requests, certs, audits, task history.
2. RPO = how much data loss acceptable; RTO = how fast service must return.
3. Prevent schema/object incompatibilities and phantom config.
4. Audit/auth events (and detection context).
5. Named drill tickets (e.g. `LAB-DR-107`) with times and operators.
6. Cert decisions live in the database, not in `config/` XML.

---

## Further reading

- [docs/SSD.md](../SSD.md) — rebuild WAR from git; importdynamic for object recovery.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “console import” and “backup” for object export/import patterns.
- [NIST SP 800-34 Rev. 1 — Contingency Planning Guide](https://csrc.nist.gov/publications/detail/sp/800-34/rev-1/final) — RPO/RTO and restore testing discipline.
- [NIST SP 800-53 Rev. 5 — CP-9 / CP-10](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — system backup and recovery / reconstitution.
- [FFIEC IT Handbook — Business Continuity Management](https://ithandbook.ffiec.gov/) — banking BCM expectations including tested recovery (search Business Continuity booklet).

---

## Stretch lab

Script a weekly export of all `MNB-*` Configuration/Policy objects to dated DR folders (console or SSB). If using CloudNativePG, record where backup schedules live and who operates them (platform).

---

## Summary

- Practice object restore from XML; demand DB backup proof for cubes/certs.
- Runbooks beat tribal restore knowledge; evidence packs beat green backup lights.
- Git is necessary and insufficient — know the boundary and the restore tiers.

---

**Previous:** [Lesson 106 — Performance Tuning IIQ](106-performance-tuning-iiq.md)  
**Next:** [Lesson 108 — Multi-Environment Promotion](108-multi-env-promotion.md)
