# SSD / SSB in this repo

This project is structured as a **SailPoint Services Standard Deployment (SSD)** workspace. Day-to-day builds use the **Services Standard Build (SSB)** Ant tooling that ships at the repo root (`build.xml`, `build.sh`, `lib/ant`).

> SSD = SSB + optional SSF / SST / SSP frameworks.  
> We keep `deploySSF=false` by default so Meridian customizations stay small; flip flags in `build.properties` when you adopt those frameworks.

Official Compass docs (login required):

- [Get Started with the SSD](https://community.sailpoint.com/t5/Services-Standard-Deployment/Get-Started-with-the-SSD/ta-p/73449)
- [Services Standard Build User Guide](https://community.sailpoint.com/t5/Services-Standard-Deployment/Services-Standard-Build-User-Guide-SSB/ta-p/73434)

## Learner setup = build in IIQ, optional export to SSB

CD ships **HelloWorld smoke** only. Learners build Meridian objects in lessons, then optionally export into `config/` for promotion practice.

| Layer | Path | Role |
| --- | --- | --- |
| CSV fixtures | `lab-data/` → `~/iiq-lab-data/` | HR / app extracts (copy before Lesson 04) |
| IIQ objects | Built in UI; export → [`config/`](../config/) | Applications, tasks, rules, roles, workflows, policies |
| Tokens | `*.target.properties` | `%%MNB_HR_FILE%%`, etc. (when you export apps) |
| Inventory | [`config/PACKS.md`](../config/PACKS.md) | What CD ships vs what lessons create |
| Verify | [`tools/iiq-verify/assert-mnb-objects.sh`](../tools/iiq-verify/assert-mnb-objects.sh) | CD smoke (`HelloWorld`) only |

Day-1 (Lesson 03): copy lab-data → confirm SSB layout → see HelloWorld after CD/`importdynamic`. Lessons **04+** create `MNB-HR` and everything else in the UI. Lesson **101** is when exports + promotion/CAB mature.

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

1. Build the control in IIQ (lesson procedure).  
2. Export clean XML → `config/<Type>/MNB-…xml`.  
3. Replace hard-coded env values with `%%TOKENS%%` from `*.target.properties`.  
4. `./build.sh -Dtarget=sandbox clean war`  
5. `./build.sh importdynamic`  
6. `./tools/iiq-verify/assert-mnb-objects.sh local` (CD smoke); verify your new object with Debug/`get`.  
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
