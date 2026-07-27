# SSD / SSB in this repo

This project is structured as a **SailPoint Services Standard Deployment (SSD)** workspace. Day-to-day builds use the **Services Standard Build (SSB)** Ant tooling that ships at the repo root (`build.xml`, `build.sh`, `lib/ant`).

> SSD = SSB + optional SSF / SST / SSP frameworks.  
> We keep `deploySSF=false` by default so Meridian customizations stay small; flip flags in `build.properties` when you adopt those frameworks.

Official Compass docs (login required):

- [Get Started with the SSD](https://community.sailpoint.com/t5/Services-Standard-Deployment/Get-Started-with-the-SSD/ta-p/73449)
- [Services Standard Build User Guide](https://community.sailpoint.com/t5/Services-Standard-Deployment/Services-Standard-Build-User-Guide-SSB/ta-p/73434)

## Learner setup = scoped bank setup

The Meridian academy and a forward-deployed IAM team use the **same** SSB layout:

| Layer | Path | Role |
| --- | --- | --- |
| CSV fixtures | `lab-data/` → `~/iiq-lab-data/` | HR / app extracts |
| IIQ objects | [`config/`](../config/) | Applications, tasks, rules, roles, workflows, policies |
| Tokens | `*.target.properties` | `%%MNB_HR_FILE%%`, etc. |
| Pack inventory | [`config/PACKS.md`](../config/PACKS.md) | What is seeded vs lesson-extended |
| Verify | [`tools/iiq-verify/assert-mnb-objects.sh`](../tools/iiq-verify/assert-mnb-objects.sh) | Post-import allowlist |

Day-1 for learners (Lesson 03): copy lab-data → set tokens → `./build.sh importdynamic` → confirm `MNB-Rule-Hello-World` / `MNB-HR`. Lessons 04+ teach UI craft against that product layer; durable changes re-export to `config/`. Lesson **101** is promotion/CAB maturity, not first contact with SSB.

## Layout

| Path | Role |
| --- | --- |
| `base/ga/identityiq-8.5.zip` | GA binary (must contain `identityiq.war`) |
| `base/patch/` | Optional patch jars `identityiq-8.5pN.jar` |
| `base/efix/` | Optional e-fixes |
| `config/` | **Your** IIQ XML objects (edit here) |
| `src/` | Custom Java |
| `web/` | UI overlays |
| `lib/` | SSB Ant + helper jars (do not reinvent) |
| `scripts/` | SSB Ant includes / checks (SailPoint) |
| `sandbox.*.properties` | Local lab env tokens + `iiq.properties` |
| `dev.*.properties` / `prod.*.properties` | Higher environments |
| `servers.properties` | Hostname → `SPTARGET` mapping |
| `tools/lab/` | Greenfield laptop bootstrap (Tomcat/MySQL) |
| `lab-data/` | Meridian bank lab fixtures (HR, apps, SoD, JML scenarios) |
| `docs/lessons/` | 50-lesson IdentityIQ curriculum (Markdown) |
| `learn/` | Static site builder for `iam.lmsapp.us/learn` |
| `docs/` | Human docs + lessons + vendor PDFs |

## Everyday commands

```bash
# Prefer SPTARGET matching servers.properties / -Dtarget=
export SPTARGET=sandbox

./build.sh clean          # wipe build/
./build.sh war            # produce build/deploy/identityiq.war + extract
./build.sh clean war
./build.sh deploy         # sync built app into IIQHome (see build.properties)
./build.sh importdynamic  # import config XML via console
```

Bundled Ant (no system Ant required):

```bash
./build.sh -version
```

## Adding a feature (happy path)

1. Prefer **extend a seeded pack** from [`config/PACKS.md`](../config/PACKS.md); use UI create only for first-principles lessons.  
2. Export clean XML → `config/<Type>/MNB-…xml` (or edit the seed in place).  
3. Replace hard-coded env values with `%%TOKENS%%` from `*.target.properties`.  
4. `./build.sh -Dtarget=sandbox clean war`  
5. `./build.sh importdynamic` (or wait for homelab CD import).  
6. `./tools/iiq-verify/assert-mnb-objects.sh local` (or `k8s`).  
7. Commit XML + property token changes (not `build/`).  
8. CI builds the same way (see `.github/workflows/ssb-ci.yml`).

## CI / CD next step (ready)

Pipeline shape used by most IIQ teams:

```text
checkout → ./build.sh -Dtarget=<env> clean war → archive identityiq.war
        → (deploy job) stop app → expand/deploy WAR → smoke login
        → optional importdynamic for hot XML
```

Secrets (`console_pass`, DB passwords) belong in the CI secret store, injected into `*.iiq.properties` at build time — never commit prod secrets.

See root [README.md](../README.md) and [docs/LOCAL_SETUP.md](LOCAL_SETUP.md).
