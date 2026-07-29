# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Reference

This repository is a **SailPoint IdentityIQ 8.5 Services Standard Deployment (SSD)** workspace. Day-to-day builds use the **Services Standard Build (SSB)** Ant tooling at the repo root (`build.xml`, `build.sh`, `lib/ant`).

> Core commands to remember:
> ```bash
> export SPTARGET=sandbox
> ./build.sh clean war      # produce build/deploy/identityiq.war
> ./build.sh deploy         # sync into IIQHome
> ./build.sh importdynamic  # import config XML
> ```

## Repository Architecture

### Primary Directories

| Path | Purpose |
| --- | --- |
| `base/ga/` | **DO NOT EDIT** - GA binary (`identityiq-8.5.zip`) from GitHub Container Registry. Must exist for builds. |
| `base/patch/` | Optional patch jars (`identityiq-8.5pN.jar`) |
| `base/efix/` | Optional e-fixes |
| `config/` | **YOUR** IIQ XML objects (Applications, Rules, Workflows, Policies, etc.) |  
| `src/` | Custom Java source code |
| `web/` | UI overlays and customizations |
| `lib/` | SailPoint SSB Ant + helper jars (tools, copy these, don't reinvent) |
| `scripts/` | SSB Ant includes and checks (SailPoint-provided build fragments) |
| `sandbox.*/dev.*/prod.*/properties/` | Environment tokens (`iiq.properties` + `.target.properties`) |
| `docker/` | Tomcat 9 image for Docker setup |
| `tools/lab/` | Greenfield laptop bootstrap for Tomcat+MySQL or Docker |
| `lab-data/` | HR/Employee sample files for lessons |
| `docs/` | Human documentation (`SSD.md`, `LOCAL_SETUP.md`, lesson curriculum) |
| `docs/lessons/` | 50-lesson IdentityIQ curriculum (Markdown) |
| `learn/` | Static site builder for lessons.lmsapp.us/learn |

### Build System

- **Ant** is the primary build tool with custom SailPoint targets
- **Bundled Ant**: `./lib/ant/bin/ant` (no system Ant required)
- **Wrapper script**: `./build.sh` (executes Ant with correct environment)
- **Build.xml**: Main Ant build file; imports from `scripts/` subdirectories
- **build.properties**: SSB knobs (IIQ version, LCM, SSF flags)

## Common Development Tasks

### 1. Setting Up Local Lab Environment

**Choose one:**

**A. Docker (simpler, faster):**
```bash
./tools/lab/docker/up.sh
# Academy → http://localhost:4173/
# IIQ     → http://localhost:8080/identityiq
```

**B. Tomcat + MySQL (recommended for learning):**
```bash
./tools/lab/up.sh
# Academy → http://localhost:4173/
# IIQ     → http://localhost:8080/identityiq
```

### 2. Building & Deploying Customizations

1. **Determine target environment** (usually `sandbox` for lab):
```bash
export SPTARGET=sandbox
```

2. **Build WAR file with customizations:**
```bash
./build.sh clean war
```

3. **Deploy to your IIQ instance:**
```bash
./build.sh deploy
```

4. **Import XML objects (SSB/SSD):**** (if you have config XML):
```bash
./build.sh importdynamic
```

### 3. Adding a New Feature

**Happy path (based on SSD.md):**

1. **Build the control in IIQ** using lesson procedures
2. **Export clean XML** → `config/<Type>/MNB-<Type>-<BusinessName>.xml`
3. **Replace hard-coded values** with `%%TOKENS%%` from `*.target.properties`
4. **Build and import:**
```bash
./build.sh -Dtarget=sandbox clean war
./build.sh importdynamic
```

5. **Verify with CD smoke test:**
```bash
./tools/iiq-verify/assert-mnb-objects.sh local
```

6. **Commit XML + property token changes** (not build artifacts)

### 4. Running Tests/Verification

**CD smoke test (checks HelloWorld objects only):**
```bash
./tools/iiq-verify/assert-mnb-objects.sh local
```

**Lesson verification:**
```bash
# Run specific lesson verifier or all lessons
# Refer to docs/LESSON_VERIFY.md
```

## Key Files and Their Roles

### build.xml
- Main Ant build script
- Imports from: `scripts/build.filelayout.xml`, `scripts/build.java.xml`, `scripts/build.config.xml`, `scripts/build.dev.xml`
- Handles: binary extraction, Java compilation, WAR packaging, deployment

### build.sh  
```sh
#!/bin/sh
set -eu
exec ./lib/ant/bin/ant "$@"
```
- Simple wrapper that uses bundled Ant
- Sets strict exit on error (`set -eu`)

### build.properties
- Master configuration for SSB build
- Contains: IIQ version, LCM settings, SSF flags (`deploySSF=false`)
- Can be overridden by `${hostname}.build.properties` or `${target}.build.properties`

### config/README.md
- **How to add a feature** workflow
- **Folder map** (Application/, Bundle/, Rule/, Workflow/, Policy/, etc.)
- **Token replacement rules** using `%%TOKENS%%` pattern

### servers.properties  
Maps hostnames to build targets (sandbox/dev/prod). Used when SPTARGET environment variable is not set.

### .github/workflows/ssb-ci.yml
- CI/CD GitHub Actions workflow
- Runs: `./build.sh -Dtarget=sandbox clean war` for PRs/develop
- Skips full builds on main when only publish paths changed (reuses thin Docker image)

## Environment Management

### SPTARGET Environments

| SPTARGET | Property files |
| --- | --- |
| `sandbox` | `sandbox.iiq.properties`, `sandbox.target.properties`, `sandbox.ignorefiles.properties` |
| `dev` | `dev.*` (deploy/prod equivalents) |
| `prod` | `prod.*` |

### Property File Patterns

- `*.iiq.properties` – IIQ application properties (database connection, etc.)
- `*.target.properties` – environment-specific tokens for config XML replacement
- `*.ignorefiles.properties` – lists XML files to ignore during build
- `*.build.properties` – overrides defaults for specific hosts/targets

## Code Structure

### Java Source Layout

```
/src
  /com/meridianbank/iiq/               ← Meridian customizations
    /package-info.java                ← Package declaration
    /... various components ...
```

### Generated Build Output

```
/build/
  /extract/                         ← Unpacked identityiq.war contents
  /classes/                         ← Compiled *.class files
  /deploy/                          ← Final identityiq.war
  /doc/                             ← Technical documentation (from document target)
  /buildChecks/                     ← Build check logs
```

## Common Gotchas

1. **Never edit `base/ga/identityiq-8.5.zip`** – it lives in Git LFS/GHCR
2. **Always use `./build.sh`** – directly invokes bundled Ant, not system Ant
3. **Config XML files must** use `MNB-<Type>-<BusinessName>.xml` naming convention
4. **Tokens in config XML** must use `%%TOKEN_NAME%%` format for property replacement
5. **Share `SPTARGET=sandbox`** across commands to avoid target guessing confusion
6. **Don't modify `lib/`** – these are SailPoint-provided SSB Ant components, copy them, don't reinvent
7. **Commit config/ + property files**, not `build/` artifacts (see `.gitignore`)

## Development Workflow

### Day-1 (Lesson 03)
1. Setup lab using `./tools/lab/up.sh`
2. Confirm SSB layout exists
3. See HelloWorld after CD/`importdynamic`

### Lessons 04-100
1. Build Meridian objects in IIQ UI
2. Export clean XML → `config/`
3. Replace tokens → add to property files
4. Build with `./build.sh -Dtarget=sandbox clean war`
5. Deploy with `./build.sh deploy`
6. Import dynamic config with `./build.sh importdynamic`

### Lesson 101
1. Mature promotion/CAB workflow with exports + imports

## Next Steps for New Features

1. **Start in lessons** – build controls in IIQ UI
2. **Export clean XML** – use Debug → export or Object Exporter  
3. **Place in config/<Type>/** with MNB- prefix
4. **Tokenize** – replace hardcoded values with `%%TOKENS%%`
5. **Build & import** – use standard SSB commands
6. **Smoke test** – run `./tools/iiq-verify/assert-mnb-objects.sh local`
7. **Commit** – XML + property token changes only

## References

- [SSD.md](docs/SSD.md) – Detailed SSD/SSB explanation
- [LOCAL_SETUP.md](docs/LOCAL_SETUP.md) – Local setup (Docker vs Tomcat)  
- [config/README.md](config/README.md) – Adding features workflow
- [PACKS.md](config/PACKS.md) – What CI ships vs what lessons create
- [.github/workflows/ssb-ci.yml](.github/workflows/ssb-ci.yml) – CI pipeline
- [tools/lab/](tools/lab/) – Laptop bootstrap scripts for setup/teardown