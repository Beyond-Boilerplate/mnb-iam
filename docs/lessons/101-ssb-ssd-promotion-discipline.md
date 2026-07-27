# Lesson 101 — SSB/SSD Promotion Discipline

| Field | Value |
| --- | --- |
| **Level** | Intermediate |
| **Track** | Plugins, APIs & SSD |
| **Time** | 60–90 minutes |
| **Prereq** | [Lesson 100 — IIQ REST & SCIM APIs](100-iiq-rest-scim-apis.md); [docs/SSD.md](../SSD.md) |
| **Lab data** | Repo `config/`, `sandbox.*.properties`, `build.sh`; CI hints in SSD.md |

## Learning objectives

You will be able to:

- Explain SSD vs SSB and where Meridian customizations live (`config/`, `src/`, `web/`, `pluginsrc/`)
- Export a UI-built object to clean `config/<Type>/MNB-*.xml` with `%%TOKENS%%`
- Run `./build.sh -Dtarget=sandbox clean war` (or document CI equivalent)
- Describe the promotion pipeline: sandbox → dev → prod properties
- List secrets that must never be committed

## Why this matters

Click-ops in production creates snowflake banks. SSB makes Meridian IAM rebuildable: same XML, different tokens per environment. Examiners ask how a SoD policy in prod got there—your answer is git SHA + build log, not “someone imported it.”

**Control / audit:** Change tickets reference commit SHAs. Prod deploys are pipeline-only. Hot console imports in prod require incident/CAB exception.

## Concepts

From [docs/SSD.md](../SSD.md):

| Path | Role |
| --- | --- |
| `config/` | IIQ XML objects (edit here) |
| `src/` | Custom Java |
| `web/` | UI overlays |
| `sandbox.*.properties` / `dev.*.` / `prod.*.` | Env tokens |
| `servers.properties` | Hostname → SPTARGET |
| `./build.sh` | SSB Ant wrapper |

```text
  UI prototype (sandbox)
        |
        v
  Export XML --> config/Type/MNB-....xml  (%%TOKENS%%)
        |
        v
  ./build.sh -Dtarget=sandbox clean war
        |
        +--> deploy / importdynamic
        |
        v
  git commit --> CI war --> higher env with other *.properties
```

**Everyday commands**

```bash
export SPTARGET=sandbox
./build.sh clean
./build.sh war
./build.sh clean war
./build.sh deploy
./build.sh importdynamic
```

**Token rule:** Replace env-specific JDBC URLs, hostnames, and emails with `%%TOKENS%%` defined in `*.target.properties`.

## Before you start

- [ ] Clone builds locally or CI available
- [ ] Read SSD.md layout + everyday commands
- [ ] Identify one Meridian object to promote (workgroup, rule stub, QuickLink)
- [ ] Confirm `build/deploy` is gitignored
- [ ] Vault ready for `console_pass` / DB passwords

## Lab procedure

### Task 1 — Map SPTARGET

1. Open `servers.properties` and sandbox property files.
2. Record which SPTARGET your laptop/homelab uses.
3. Note presence of `dev.*.properties` and `prod.*.properties` even if unused locally.

**Expected result:** One-line “My SPTARGET is …” in binder.

**If it fails:** Default to `sandbox` per SSD.md examples.

### Task 2 — Export object into config/

1. In sandbox UI, finalize a small object (e.g., Workgroup description tweak or Rule stub `MNB-Rule-Console-Smoke`).
2. Debug → export XML.
3. Save as `config/Workgroup/MNB-WG-IAM-Ops.xml` or appropriate type folder (create folder if needed).
4. Strip environment noise; add tokens where host-specific.

**Expected result:** Clean Meridian XML under `config/`.

**If it fails:** Keep file under `~/iiq-lab-data/promotion/` and note “move to config/ before PR.”

### Task 3 — Tokenize one value

1. Pick one env-specific string (mail host, URL, DB name).
2. Replace with `%%MNB_EXAMPLE_TOKEN%%` (or existing project token naming).
3. Add the token to `sandbox.target.properties` (or equivalent) with lab value.
4. Confirm prod property file would use a different value (add placeholder comment if file locked).

**Expected result:** Tokenized XML + sandbox property entry.

### Task 4 — Build WAR

1. From repo root: `./build.sh -Dtarget=sandbox clean war` (or `export SPTARGET=sandbox` first).
2. Confirm artifacts under `build/deploy/` (do not commit).
3. Capture build success log snippet (last 30 lines) for binder.

**Expected result:** Successful WAR build evidence.

**If it fails:** Run `./build.sh -version`; fix missing GA zip per README; do not commit binary fixes without team process.

### Task 5 — importdynamic dry understanding

1. Read what `importdynamic` does in SSD.md.
2. In lab, run only if safe: `./build.sh importdynamic`.
3. Otherwise, write the step into a promotion runbook without executing against a shared prod-like DB.

**Expected result:** Executed import **or** explicit dry-run runbook step.

### Task 6 — Promotion discipline checklist

1. Draft checklist: object in `config/` → tokens → build → peer review → CI → deploy target → smoke login → importdynamic if needed → evidence SHA.
2. Add forbidden list: prod secrets, `build/`, local `iiq.properties` passwords.
3. Reference CI shape from SSD.md (`ssb-ci.yml` mention).

**Expected result:** One-page Meridian promotion checklist.

## Acceptance criteria

- [ ] SPTARGET identified
- [ ] At least one `MNB-*.xml` in `config/` (or staged lab-data with move note)
- [ ] One `%%TOKEN%%` demonstrated
- [ ] WAR build success evidence (or CI log)
- [ ] Secrets exclusion list written
- [ ] Promotion checklist complete

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| build fails missing GA | `base/ga` zip absent | Follow README / LOCAL_SETUP |
| Tokens not replaced | Wrong SPTARGET / property file | Align `-Dtarget` and servers.properties |
| importdynamic auth fail | console_pass missing | Inject via secret store into iiq.properties |
| Accidental commit of build/ | gitignore gap | Remove from index; never push WAR |
| XML drifts from UI | Someone click-ops’d prod | Re-export; enforce pipeline-only |

## Training binder evidence

- Path to `config/.../MNB-*.xml`  
- Token example  
- Build log snippet  
- Promotion checklist  

## Knowledge check

1. What is SSD vs SSB in one sentence each?
2. Where do Meridian XML objects belong in-repo?
3. Why use `%%TOKENS%%`?
4. Name two artifacts that must not be committed.
5. What proves a prod object came from engineering process?

### Answers

1. SSB = build tooling; SSD = SSB plus optional frameworks/layout for services deployment.  
2. `config/<Type>/` with `MNB-` names.  
3. Same XML, environment-specific values via property files.  
4. `build/` outputs; prod passwords / console_pass; local secret property overlays.  
5. Git commit SHA + CI build/deploy logs (+ change ticket).

## Stretch lab

Compare `sandbox` vs hypothetical `prod` property keys side-by-side; list every key that must differ (DB, mail, URLs, IQService hosts).

## Summary

- Prototype in UI; permanently store under `config/` with tokens.
- Build and promote through SSB/CI—not sneaker-net XML.
- Secrets stay in secret stores; evidence is SHA + pipeline.

## Branching model (Meridian recommendation)

```text
  feature/MNB-####-short-name
        |
        v
  PR --> main (protected)
        |
        +--> CI war (sandbox tokens)
        +--> deploy dev on merge / tag
        +--> prod via CAB-approved tag
```

1. No direct commits to `main` for config XML.
2. PR description lists objects touched and token changes.
3. Reviewer checks secrets and `rightRequired` on plugins.

### Task 7 — Impordynamic vs full redeploy decision tree

1. XML-only object change → `importdynamic` may suffice after WAR already contains classes.
2. Java/`web/`/plugin binary change → must rebuild and redeploy WAR/image.
3. Hybrid → rebuild always; importdynamic if objects not baked.
4. Write the decision for your Task 2 object.

**Expected result:** Decision-tree application note.

### CI secret injection reminder

From SSD.md: secrets (`console_pass`, DB passwords) belong in the CI secret store, injected into `*.iiq.properties` at build time — never commit prod secrets.

---

**Previous:** [Lesson 100 — IIQ REST & SCIM APIs](100-iiq-rest-scim-apis.md)  
**Next:** [Lesson 102 — Custom Java Services](102-custom-java-services.md)
