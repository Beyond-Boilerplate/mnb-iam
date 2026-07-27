# Lesson 108 — Multi-Environment Promotion

| Field | Value |
| --- | --- |
| **Level** | Advanced |
| **Track** | Enterprise Hardening & Mastery |
| **Time** | 75–90 minutes |
| **Prereq** | [Lesson 107 — Backup, DR & Object Recovery](107-backup-dr-object-recovery.md); Lesson 101 SSB discipline |
| **Lab data** | `sandbox.*.properties`, `dev.*.properties`, `prod.*.properties`; [docs/SSD.md](../SSD.md); [docs/HOMELAB-CD.md](../HOMELAB-CD.md) |

## Learning objectives

You will be able to:

- Draw Meridian’s env chain: sandbox → dev → (uat/stage) → prod
- Explain what promotes (WAR/XML/plugins) vs what must never copy (prod identities, prod secrets)
- Build a promotion checklist with smoke tests and backout
- Use property tokens so one `config/` tree serves all envs
- Map homelab CD workflow roles to enterprise promotion gates

## Why this matters

Copying a sandbox database into prod copies test SoD exceptions and fake managers into the bank’s system of record. Promotion is artifact movement, not DB cloning.

**Control / audit:** Each higher environment deploy cites git SHA, change ticket, smoke evidence, and approvers. Hotfixes still enter git—no eternal prod-only XML.

## Concepts

```text
  Developer laptop / sandbox
        |  export + PR
        v
  git main (config/src/web/plugins)
        |  CI: ./build.sh -Dtarget=<env> clean war
        v
  dev  -->  uat/stage  -->  prod
        ^ smoke       ^ CAB     ^ dual control
```

| Moves up | Stays local / secret store |
| --- | --- |
| `MNB-*.xml` | DB passwords, console_pass |
| Compiled Java / plugins | Prod API client secrets |
| UI branding tokens (values differ) | Prod identity cubes |
| Helm/image tags | Raw prod `iiq.properties` |

**Homelab parallel:** `publish-ghcr.yml` + `deploy-homelab.yml` approximate CI→deploy; enterprise adds CAB and multi-stage targets.

## Before you start

- [ ] Lesson 101 promotion checklist available to extend
- [ ] Identify which envs exist in your property files
- [ ] Pick one object ready to “promote” on paper (or real sandbox→dev if available)
- [ ] Banner standards from Lesson 103

## Lab procedure

### Task 1 — Draw the chain

1. Document Meridian env names and URLs (localhost sandbox; homelab URL; hypothetical prod).
2. Mark who may deploy each (IAM engineer, CAB, break-glass).
3. Note SPTARGET values per env.

**Expected result:** One architecture diagram (ASCII OK).

### Task 2 — Diff property keys

1. Compare sandbox vs prod (or dev) property files for keys that must differ.
2. List ≥ 8 keys: DB URL, mail host, IQService, external URLs, banner text, API endpoints, etc.
3. Confirm corresponding `%%TOKENS%%` exist or file gaps.

**Expected result:** Key-diff table with gap flags.

**If it fails:** Use SSD.md examples and invent Meridian-proposed keys—label as proposed.

### Task 3 — Promotion package definition

1. For object `MNB-WG-IAM-Ops` (or your chosen object), define package:
   - git path
   - SHA
   - target env
   - importdynamic required? yes/no
   - smoke tests
2. Attach change ticket ID placeholder `CHG-MNB-108`.

**Expected result:** One promotion package sheet.

### Task 4 — Smoke test battery

1. Write smoke tests for post-deploy:
   - Login page loads; env banner correct
   - `spadmin`/break-glass auth works
   - One identity search
   - One task list page
   - Plugin toolkit ping if installed
   - Aggregation schedule still present
2. Define fail criteria → automatic backout.

**Expected result:** Smoke checklist with fail→backout links.

### Task 5 — Backout plan

1. Backout options: redeploy previous image/WAR tag; re-importdynamic previous XML SHA; DB restore only if data migration involved (rare for config-only).
2. Timebox: decide backout within 30 minutes of failed smoke.
3. Communication: notify `helen.ross` + platform.

**Expected result:** Backout section on package sheet.

### Task 6 — Forbidden promotions attestation

1. Sign (lab) attestation: “I will not clone prod DB to lower envs without masking; I will not copy sandbox cubes to prod.”
2. List data allowed in lower envs: synthetic Meridian personas (`nina.joiner`, `priya.wire`, …).
3. Reference Lesson 107 for restore vs promote confusion.

**Expected result:** Signed attestation page in binder.

## Acceptance criteria

- [ ] Env chain diagram complete
- [ ] Property key-diff table (≥8 keys)
- [ ] Promotion package sheet for one object
- [ ] Smoke battery + backout written
- [ ] Forbidden DB-clone attestation recorded
- [ ] Homelab CD mapping noted

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Works in sandbox fails in dev | Missing token / secret | Diff properties; check secret injection |
| Banner shows SANDBOX in prod | Token not overridden | Fix prod properties immediately |
| importdynamic wiped manual prod fix | Prod drift | Ban click-ops; reconcile into git |
| Smoke pass but plugin 404 | Image missing plugins layer | Rebuild with plugins flag |
| CAB bypassed | Emergency culture | Convert hotfix to retroactive ticket same day |

## Training binder evidence

- Env diagram  
- Property diff table  
- Package + smoke + backout  
- Attestation  

## Knowledge check

1. What moves through environments vs what must not?
2. Why is DB clone sandbox→prod forbidden?
3. What SHA belongs on a change ticket?
4. Name three post-deploy smokes.
5. How does homelab CD relate to enterprise gates?

### Answers

1. Built artifacts/config move; secrets and runtime identity data do not casually copy upward.  
2. Contaminates system of record with test access/cert history and breaks confidentiality.  
3. The git commit (and image tag) actually deployed.  
4. Login/banner, search, tasks, plugin ping, schedule presence (any three+).  
5. Homelab automates build→deploy; enterprise adds multi-stage approvals/CAB and stricter secrets.

## Stretch lab

Write a GitHub Actions outline with `workflow_dispatch` inputs `target=dev|stage|prod` and required reviewers for prod.

## Summary

- Promote artifacts with tokens—not databases.
- Smoke and backout are part of the change, not afterthoughts.
- Attest against env contamination.

## Data classification for lower environments

| Data class | Sandbox/dev | Prod |
| --- | --- | --- |
| Synthetic Meridian personas | Required | N/A (real) |
| Production entitlements mirrored | Masked / subset | Full |
| Real SSN/account numbers | Forbidden | Per bank policy vaulting |
| Admin passwords | Lab vault | Prod vault dual control |

### Task 7 — Promotion calendar

1. Propose weekly promotion window for non-urgent IAM config.
2. Emergency path: same checklist, compressed approvals, still git SHA.
3. Freeze windows before exams/quarter-end certs.

**Expected result:** Calendar paragraph in runbook.

### Mapping to Lesson 50 gates

Part I go-live checklist remains necessary; Part II adds connector fidelity, plugin rights, and hardening gates—union them in Lesson 110.

## Smoke test evidence naming

Save post-deploy proofs as:

- `MNB-Smoke-<env>-login-YYYY-MM-DD.png`
- `MNB-Smoke-<env>-search-YYYY-MM-DD.png`
- `MNB-Smoke-<env>-tasklist-YYYY-MM-DD.png`

Attach to change ticket `CHG-MNB-108` (or real CHG). Failed smoke keeps previous tag running—do not “fix forward” without new SHA.

### Token drift detection

Once per quarter, diff all `*.target.properties` keys across envs; fail review if prod lacks a key present in sandbox or vice versa without justification.

---

**Previous:** [Lesson 107 — Backup, DR & Object Recovery](107-backup-dr-object-recovery.md)  
**Next:** [Lesson 109 — Hardening spadmin & Capabilities](109-hardening-spadmin-capabilities.md)
