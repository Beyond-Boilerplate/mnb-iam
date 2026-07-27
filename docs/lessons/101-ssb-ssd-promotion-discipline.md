# Lesson 101 — SSB/SSD Promotion Discipline

**Level:** Intermediate  
**Track:** Plugins, APIs & SSD  
**Time:** 75–90 min  
**Prereq:** Lesson 100 — IIQ REST & SCIM APIs; Lesson 03 SSB import hygiene; [docs/SSD.md](../SSD.md); [config/PACKS.md](../../config/PACKS.md)  

**Lab data:**
- Repo: `config/`, `sandbox.*.properties`, `build.sh`
- CI hints: [docs/SSD.md](../SSD.md); `.github/workflows/ssb-ci.yml` when present

---

## Learning objectives

You will be able to:

- Explain **SSD** vs **SSB** and where Meridian customizations live (`config/`, `src/`, `web/`, `pluginsrc/`) — building on Lesson 03 import, not first contact
- Promote a change to an existing academy pack (or export a UI delta) with `%%TOKENS%%`
- Run `./build.sh -Dtarget=sandbox clean war` and `importdynamic`, then assert with `tools/iiq-verify/assert-mnb-objects.sh`
- Describe the promotion pipeline: sandbox → dev → prod property files with CAB evidence
- List secrets that must never be committed and how CI injects them
- Decide when `importdynamic` is enough vs when a full WAR redeploy is mandatory

---

## Why this matters

**Business.** Click-ops in production creates snowflake banks. Last quarter someone “quickly imported” a SoD policy XML on prod from a laptop Downloads folder. Two weeks later nobody could find which version was live — and `priya.wire`’s mitigate path behaved differently than lab. SSB makes Meridian IAM rebuildable: same XML, different tokens per environment.

**Control / audit.** Examiners ask how a SoD policy in prod got there — your answer is git SHA + build log + CAB ticket, not “someone imported it.” Change tickets reference commit SHAs. Prod deploys are pipeline-only. Hot console imports in prod require incident/CAB exception (Lesson 99). When the OCC asks *"prove this Policy matches what Risk approved,"* you open the commit, not Debug history.

---

## Concepts

### SSD vs SSB (one sentence each)

| Term | Meaning in this repo |
| --- | --- |
| **SSB** (Services Standard Build) | Ant tooling at repo root (`build.xml`, `build.sh`) that builds `identityiq.war` from GA + your overlays |
| **SSD** (Services Standard Deployment) | SSB plus the services deployment layout/frameworks; Meridian keeps `deploySSF=false` by default so customizations stay small |

Official Compass entry points (login often required): [Get Started with the SSD](https://community.sailpoint.com/t5/Services-Standard-Deployment/Get-Started-with-the-SSD/ta-p/73449) and [SSB User Guide](https://community.sailpoint.com/t5/Services-Standard-Deployment/Services-Standard-Build-User-Guide-SSB/ta-p/73434).

### Where things live

| Path | Role |
| --- | --- |
| `config/` | **Your** IIQ XML objects (edit here) |
| `src/` | Custom Java |
| `web/` | UI overlays |
| `pluginsrc/` | Plugins (Lessons 97–98) |
| `sandbox.*.properties` / `dev.*.` / `prod.*.` | Env tokens |
| `servers.properties` | Hostname → `SPTARGET` |
| `base/ga/` | GA IdentityIQ zip (not reinvented) |
| `build/` | Output — **never commit** |
| `lab-data/` | Meridian fixtures — not a substitute for `config/` permanence |

### Token rule

Replace env-specific JDBC URLs, hostnames, mail hosts, IQService hosts, and banner text with `%%TOKENS%%` defined in `*.target.properties`. Same XML tree; different values per `SPTARGET`. **Wrong way:** hard-code `localhost` and prod hostnames in two XML copies. **Meridian way:** one `MNB-*.xml`, many property files.

### Real-life Meridian example

A Rule stub for BeforeProvisioning was edited live in prod Debug during a Wire outage. Lab still had the old body. Three days later a CAB “promotion” of lab XML wiped the hotfix. Discipline would have been: emergency export → commit → rebuild → CAB — not eternal prod-only BeanShell.

### Branching model (Meridian recommendation)

```
  feature/MNB-####-short-name
        │
        ▼
  PR --> main (protected)
        │
        ├── CI war (sandbox tokens)
        ├── deploy dev on merge / tag
        └── prod via CAB-approved tag
```

No direct commits to `main` for config XML. PR description lists objects touched and token changes. Reviewer checks secrets and plugin `rightRequired`.

---

## How it works

```
  UI prototype (sandbox)
        │
        ▼
  Export XML --> config/Type/MNB-....xml  (%%TOKENS%%)
        │
        ▼
  ./build.sh -Dtarget=sandbox clean war
        │
        ├── deploy / importdynamic
        │
        ▼
  git commit --> CI war --> higher env with other *.properties
```

**Everyday commands** (from [docs/SSD.md](../SSD.md)):

```bash
export SPTARGET=sandbox
./build.sh clean
./build.sh war
./build.sh clean war
./build.sh deploy
./build.sh importdynamic
```

| Change type | Promote how |
| --- | --- |
| XML-only object | Often `importdynamic` after WAR already contains classes |
| Java / `web/` / plugin binary | Must rebuild and redeploy WAR/image |
| Hybrid | Rebuild always; importdynamic if objects not baked |

**CI shape:**

```
checkout → ./build.sh -Dtarget=<env> clean war → archive identityiq.war
        → stop app → expand/deploy WAR → smoke login
        → optional importdynamic for hot XML
```

Secrets (`console_pass`, DB passwords) belong in the CI secret store, injected into `*.iiq.properties` at build time — never commit prod secrets.

---

## Real-world setup (SSB/SSD pipeline)

### Step 1 — Establish SPTARGET mapping

1. Open `servers.properties` and sandbox property files.
2. Map laptop/homelab hostname → `sandbox` (or your lab target).
3. Confirm `dev.*.properties` and `prod.*.properties` exist even if unused locally.

### Step 2 — Secret injection

1. Identify every secret key: DB password, `console_pass`, mail creds, API client secrets.
2. Put values in vault / CI secrets — not in committed property files.
3. At build/deploy time, inject into the env-specific `iiq.properties` overlay.

### Step 3 — Pipeline gates

1. PR required for `config/`, `src/`, `web/`, `pluginsrc/`.
2. CI must produce WAR from clean checkout (reproducibility proof).
3. Prod deploy requires CAB ticket + git SHA + smoke evidence (Lesson 108).

### Step 4 — Drift control

1. Ban prod click-ops; if emergency console import happens, re-export into `config/` same day.
2. Quarterly: diff property keys across envs for token drift.

---

## Before you start

- [ ] Clone builds locally or CI available
- [ ] Read [docs/SSD.md](../SSD.md) layout + everyday commands
- [ ] Identify one Meridian object to promote (workgroup, rule stub, QuickLink)
- [ ] Confirm `build/deploy` is gitignored
- [ ] Vault ready for `console_pass` / DB passwords (lab placeholders OK)

---

## Lab procedure

### Task 1 — Map SPTARGET

Promotion starts with knowing which property file will token-replace your XML.

1. Open `servers.properties` and sandbox property files.
2. Record which SPTARGET your laptop/homelab uses.
3. Note presence of `dev.*.properties` and `prod.*.properties`.

**Expected result:** One-line “My SPTARGET is …” in binder.

**If it fails:** Default to `sandbox` per SSD.md examples.

### Task 2 — Export object into config/

UI prototypes are temporary. Permanence is `config/MNB-*.xml`.

1. In sandbox UI, finalize a small object (Workgroup description tweak on `MNB-WG-IAM-Ops` or Rule stub `MNB-Rule-Console-Smoke`).
2. Debug → export XML.
3. Save as `config/Workgroup/MNB-WG-IAM-Ops.xml` or appropriate type folder (create folder if needed).
4. Strip environment noise; prepare for tokens.

**Expected result:** Clean Meridian XML under `config/`.

**If it fails:** Keep under `~/iiq-lab-data/promotion/` and note “move to config/ before PR.”

### Task 3 — Tokenize one value

Same XML must survive sandbox and prod without forked copies.

1. Pick one env-specific string (mail host, URL, DB name, banner text).
2. Replace with `%%MNB_EXAMPLE_TOKEN%%` (or existing project token naming).
3. Add the token to `sandbox.target.properties` (or equivalent) with lab value.
4. Confirm prod property file would use a different value (placeholder comment if file locked).

**Expected result:** Tokenized XML + sandbox property entry.

### Task 4 — Build WAR

Reproducibility is the control — “works on my Tomcat” is not.

1. From repo root: `./build.sh -Dtarget=sandbox clean war`.
2. Confirm artifacts under `build/deploy/` (do not commit).
3. Capture build success log snippet (last 30 lines) for binder.

**Expected result:** Successful WAR build evidence.

**If it fails:** Run `./build.sh -version`; fix missing GA zip per README / LOCAL_SETUP.

### Task 5 — importdynamic dry understanding

1. Read what `importdynamic` does in SSD.md (imports config XML via console).
2. In lab, run only if safe: `./build.sh importdynamic`.
3. Otherwise, write the step into a promotion runbook without executing against a shared prod-like DB.

**Expected result:** Executed import **or** explicit dry-run runbook step.

### Task 6 — Promotion discipline checklist

1. Draft checklist: object in `config/` → tokens → build → peer review → CI → deploy target → smoke login → importdynamic if needed → evidence SHA.
2. Add forbidden list: prod secrets, `build/`, local `iiq.properties` passwords, sneaker-net XML to prod.
3. Reference CI shape from SSD.md / `ssb-ci.yml`.

**Expected result:** One-page Meridian promotion checklist.

### Task 7 — importdynamic vs full redeploy decision tree

1. XML-only → `importdynamic` may suffice after WAR already contains classes.
2. Java/`web/`/plugin binary → must rebuild and redeploy WAR/image.
3. Hybrid → rebuild always; importdynamic if objects not baked.
4. Write the decision for your Task 2 object.

**Expected result:** Decision-tree application note for your object.

### Task 8 — Examiner question drill

*"Prove this SoD policy (or workgroup) in prod came from engineering process."*

Write the three-artifact answer: (1) path to `config/.../MNB-*.xml` + git SHA, (2) CI/build log for that SHA, (3) CAB / change ticket referencing the SHA and smoke evidence.

**Expected result:** Written proof steps in the binder.

---

## Acceptance criteria

- [ ] Promotion story uses existing academy packs in `config/` (not first HelloWorld-only contact — that was Lesson 03)
- [ ] CAB-style note cites git path + TaskResult id for one Meridian object change

- [ ] SPTARGET identified
- [ ] At least one `MNB-*.xml` in `config/` (or staged lab-data with move note)
- [ ] One `%%TOKEN%%` demonstrated
- [ ] WAR build success evidence (or CI log)
- [ ] Secrets exclusion list written
- [ ] Promotion checklist + redeploy decision complete
- [ ] Examiner proof steps drafted

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| build fails missing GA | `base/ga` zip absent | Follow README / LOCAL_SETUP |
| Tokens not replaced | Wrong SPTARGET / property file | Align `-Dtarget` and servers.properties |
| importdynamic auth fail | console_pass missing | Inject via secret store into iiq.properties |
| Accidental commit of build/ | gitignore gap | Remove from index; never push WAR |
| XML drifts from UI | Someone click-ops’d prod | Re-export; enforce pipeline-only |
| Hotfix wiped by promote | Prod-only edit never committed | Emergency export same day into `config/` |

---

## Training binder evidence

- Path to `config/.../MNB-*.xml`
- Token example (sandbox vs prod comment)
- Build log snippet
- Promotion checklist + redeploy decision
- Secrets exclusion list
- Examiner proof steps

---

## Knowledge check

1. What is SSD vs SSB in one sentence each?
2. Where do Meridian XML objects belong in-repo?
3. Why use `%%TOKENS%%`?
4. Name two artifacts that must not be committed.
5. What proves a prod object came from engineering process?
6. When must you rebuild the WAR instead of only running importdynamic?

### Answers

1. SSB = build tooling; SSD = SSB plus optional frameworks/layout for services deployment.
2. `config/<Type>/` with `MNB-` names.
3. Same XML, environment-specific values via property files.
4. `build/` outputs; prod passwords / console_pass; local secret property overlays.
5. Git commit SHA + CI build/deploy logs (+ change ticket).
6. When Java, `web/`, or plugin binaries change — not XML-only.

---

## Further reading

- [Get Started with the SSD](https://community.sailpoint.com/t5/Services-Standard-Deployment/Get-Started-with-the-SSD/ta-p/73449) — official Compass entry to Services Standard Deployment.
- [Services Standard Build User Guide](https://community.sailpoint.com/t5/Services-Standard-Deployment/Services-Standard-Build-User-Guide-SSB/ta-p/73434) — SSB targets, tokens, and war/deploy/importdynamic.
- [docs/SSD.md](../SSD.md) — Meridian’s SSD layout and everyday commands.
- [NIST SP 800-53 Rev. 5 — CM-2 / CM-3](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — baseline configuration and change control for IAM platforms.
- [FFIEC IT Handbook — Development and Acquisition](https://ithandbook.ffiec.gov/) — banking expectations for controlled software promotion (search Development and Acquisition booklet).
- [OWASP SAMM — Deployment](https://owasp.org/www-project-samm/) — maturity practices for build provenance and secret handling.

---

## Stretch lab

Compare `sandbox` vs hypothetical `prod` property keys side-by-side; list every key that must differ (DB, mail, URLs, IQService hosts, banner text). File gaps as token debt for Lesson 108.

---

## Summary

- Prototype in UI; permanently store under `config/` with tokens.
- Build and promote through SSB/CI — not sneaker-net XML.
- Secrets stay in secret stores; evidence is SHA + pipeline; choose importdynamic vs full redeploy deliberately.

---

**Previous:** [Lesson 100 — IIQ REST & SCIM APIs](100-iiq-rest-scim-apis.md)  
**Next:** [Lesson 102 — Custom Java Services](102-custom-java-services.md)
