# Lesson 108 — Multi-Environment Promotion

**Level:** Advanced  
**Track:** Enterprise Hardening & Mastery  
**Time:** 75–90 min  
**Prereq:** Lesson 107 — Backup, DR & Object Recovery; Lesson 101 SSB discipline  

**Lab data:**
- `sandbox.*.properties`, `dev.*.properties`, `prod.*.properties`
- [docs/SSD.md](../SSD.md); [docs/HOMELAB-CD.md](../HOMELAB-CD.md)

---

## Learning objectives

You will be able to:

- Draw Meridian’s env chain: sandbox → dev → (uat/stage) → prod
- Explain what promotes (WAR/XML/plugins) vs what must never copy (prod identities, prod secrets)
- Build a promotion checklist with smoke tests and backout
- Use property tokens so one `config/` tree serves all envs
- Map homelab CD workflow roles to enterprise promotion gates
- Attest against DB-clone contamination between environments

---

## Why this matters

**Business.** Copying a sandbox database into prod copies test SoD exceptions and fake managers into the bank’s system of record. Promoting `nina.joiner`’s synthetic cube into production is not “helpful test data” — it is contamination. Promotion is **artifact movement**, not DB cloning.

**Control / audit.** Each higher environment deploy cites git SHA, change ticket, smoke evidence, and approvers. Hotfixes still enter git — no eternal prod-only XML. When the examiner asks *"how did this Policy reach prod,"* you show `CHG-MNB-108` + SHA + smoke screenshots — not a USB stick story.

---

## Concepts

### Env chain

```
  Developer laptop / sandbox
        │  export + PR
        ▼
  git main (config/src/web/plugins)
        │  CI: ./build.sh -Dtarget=<env> clean war
        ▼
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

### Data classification for lower environments

| Data class | Sandbox/dev | Prod |
| --- | --- | --- |
| Synthetic Meridian personas | Required | N/A (real) |
| Production entitlements mirrored | Masked / subset | Full |
| Real SSN/account numbers | Forbidden | Per bank policy vaulting |
| Admin passwords | Lab vault | Prod vault dual control |

### Real-life Meridian example

Someone cloned prod DB to “fix a cert bug” in sandbox. PII and open Wire entitlements landed on a laptop. The incident dwarfed the bug. Meridian’s rule: synthetic personas only downward; artifacts only upward.

### Wrong way vs Meridian way

| Wrong way | Why it fails | Meridian way |
| --- | --- | --- |
| DB clone sandbox→prod | Contaminates system of record | Artifact + token promotion |
| Same banner all envs | Wrong-env edits (Lesson 103) | Tokenize banner per SPTARGET |
| CAB bypass forever | Uncontrolled prod | Same-day retro ticket minimum |
| Fix forward without SHA | Unrebuildable | Backout to previous tag |

---

## How it works

| Gate | Who | Evidence |
| --- | --- | --- |
| PR to main | Peer review | Diff of `config/` + tokens |
| CI war | Pipeline | Build log from clean checkout |
| Dev deploy | IAM engineer | Smoke pack |
| Stage/UAT | IAM + app owners | Extended smoke |
| Prod | CAB + dual control | SHA + smoke + backout ready |

Smoke evidence naming:

- `MNB-Smoke-<env>-login-YYYY-MM-DD.png`
- `MNB-Smoke-<env>-search-YYYY-MM-DD.png`
- `MNB-Smoke-<env>-tasklist-YYYY-MM-DD.png`

Failed smoke keeps previous tag running — do not “fix forward” without new SHA.

Quarterly: diff all `*.target.properties` keys across envs; fail review if prod lacks a key present in sandbox without justification (token drift).

---

## Real-world setup (promotion as controlled change)

### Step 1 — Draw envs and owners

1. Names, URLs, SPTARGET, who may deploy.

### Step 2 — Diff property keys

1. ≥8 keys that must differ; file token gaps.

### Step 3 — Package + smoke + backout

1. One object package with CHG id; fail→backout within 30 minutes.

### Step 4 — Attest forbidden promotions

1. No prod DB to lower without masking; no sandbox cubes to prod.

---

## Before you start

- [ ] Lesson 101 promotion checklist available to extend
- [ ] Identify which envs exist in your property files
- [ ] Pick one object ready to “promote” on paper (or real sandbox→dev if available)
- [ ] Banner standards from Lesson 103
- [ ] Binder: `ops/promotion/`

---

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

**If it fails:** Use SSD.md examples and invent Meridian-proposed keys — label as proposed.

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

### Task 7 — Promotion calendar + Lesson 50 mapping

1. Propose weekly promotion window for non-urgent IAM config.
2. Emergency path: same checklist, compressed approvals, still git SHA.
3. Freeze windows before exams/quarter-end certs.
4. Note: Part I go-live checklist (Lesson 50) remains necessary; Part II adds connector fidelity, plugin rights, and hardening gates — union them in Lesson 110.

**Expected result:** Calendar paragraph + Lesson 50/110 pointer in runbook.

### Task 8 — Homelab CD mapping

1. Map what you automate today (GHCR publish / homelab deploy) vs enterprise gates still missing (CAB, multi-stage, secret injection maturity).
2. One paragraph honesty check for Lesson 110 residual risks.

**Expected result:** Homelab vs enterprise gates note.

### Task 9 — Examiner question drill

*"How did this Policy reach prod?"*

Write the three-artifact answer: (1) promotion package with git path + SHA + `CHG-MNB-108`, (2) smoke screenshots with env banner correct, (3) attestation / property diff proving secrets and cubes were not cloned.

**Expected result:** Written proof steps in the binder.

---

## Acceptance criteria

- [ ] Env chain diagram complete
- [ ] Property key-diff table (≥8 keys)
- [ ] Promotion package sheet for one object
- [ ] Smoke battery + backout written
- [ ] Forbidden DB-clone attestation recorded
- [ ] Homelab CD mapping noted
- [ ] Promotion calendar + Lesson 50/110 pointer
- [ ] Examiner proof steps drafted

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Works in sandbox fails in dev | Missing token / secret | Diff properties; check secret injection |
| Banner shows SANDBOX in prod | Token not overridden | Fix prod properties immediately |
| importdynamic wiped manual prod fix | Prod drift | Ban click-ops; reconcile into git |
| Smoke pass but plugin 404 | Image missing plugins layer | Rebuild with plugins flag |
| CAB bypassed | Emergency culture | Convert hotfix to retroactive ticket same day |
| Token drift | Keys missing across envs | Quarterly key diff |

---

## Training binder evidence

- Env diagram
- Property diff table
- Package + smoke + backout
- Attestation
- Calendar / CD mapping notes
- Examiner proof steps

---

## Knowledge check

1. What moves through environments vs what must not?
2. Why is DB clone sandbox→prod forbidden?
3. What SHA belongs on a change ticket?
4. Name three post-deploy smokes.
5. How does homelab CD relate to enterprise gates?
6. What should you do when smoke fails?

### Answers

1. Built artifacts/config move; secrets and runtime identity data do not casually copy upward.
2. Contaminates system of record with test access/cert history and breaks confidentiality.
3. The git commit (and image tag) actually deployed.
4. Login/banner, search, tasks, plugin ping, schedule presence (any three+).
5. Homelab automates build→deploy; enterprise adds multi-stage approvals/CAB and stricter secrets.
6. Keep previous tag running; backout within the timebox — do not fix forward without a new SHA.

---

## Further reading

- [docs/SSD.md](../SSD.md) — Meridian SSD layout, tokens, and CI shape.
- [Get Started with the SSD](https://community.sailpoint.com/t5/Services-Standard-Deployment/Get-Started-with-the-SSD/ta-p/73449) — official Compass SSD entry.
- [Services Standard Build User Guide](https://community.sailpoint.com/t5/Services-Standard-Deployment/Services-Standard-Build-User-Guide-SSB/ta-p/73434) — multi-target builds and property files.
- [NIST SP 800-53 Rev. 5 — CM-3 / CM-4](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — configuration change control and impact analysis for promotions.
- [FFIEC IT Handbook — Development and Acquisition](https://ithandbook.ffiec.gov/) — controlled promotion of software into production banking environments.
- [OWASP SAMM — Deployment](https://owasp.org/www-project-samm/) — maturity for staged releases, secrets, and provenance.

---

## Stretch lab

Write a GitHub Actions outline with `workflow_dispatch` inputs `target=dev|stage|prod` and required reviewers for prod. Include smoke artifact upload names matching this lesson’s convention.

---

## Summary

- Promote artifacts with tokens — not databases.
- Smoke and backout are part of the change, not afterthoughts.
- Attest against env contamination; map homelab automation honestly to enterprise gates.

---

**Previous:** [Lesson 107 — Backup, DR & Object Recovery](107-backup-dr-object-recovery.md)  
**Next:** [Lesson 109 — Hardening spadmin & Capabilities](109-hardening-spadmin-capabilities.md)
