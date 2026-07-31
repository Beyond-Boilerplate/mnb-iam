# Meridian National Bank — IdentityIQ 8.5 (SSD)

SailPoint **Services Standard Deployment (SSD)** project for IdentityIQ **8.5**, with Meridian National Bank lab content and a laptop bootstrap for greenfield machines.

Day-to-day customization uses **SSB** (Services Standard Build) — do not reinvent Ant packaging; use `./build.sh`.

## Quick start (Docker — IIQ + Academy + MCP + OpenAPI)

```bash
./tools/lab/docker/up.sh
# Academy → http://localhost:4173/
# IIQ     → http://localhost:8080/identityiq  (spadmin / admin)
# OpenAPI → http://localhost:8765/swagger/
# MCP     → http://127.0.0.1:8766/mcp  (Bearer mnb-lab-mcp-key)
# Teller  → http://localhost:4180/  (chatbot; OPENROUTER_API_KEY for free-text)
# LDAP UI → http://localhost:8090/  (phpLDAPadmin; cn=admin,dc=meridiannb,dc=com / admin)
```

Tomcat host path (one command):

```bash
./tools/lab/up.sh
# Academy → http://localhost:4173/
# IIQ     → http://localhost:8080/identityiq  (spadmin / admin)
# OpenAPI → http://localhost:8765/swagger/
# MCP     → http://127.0.0.1:8766/mcp
# Teller  → http://localhost:4180/
```
---

## Quick links

| Doc | Purpose |
| --- | --- |
| [docs/SSD.md](docs/SSD.md) | How SSD/SSB works in this repo + CI/CD path |
| [docs/REPO_LAYOUT.md](docs/REPO_LAYOUT.md) | Live paths vs `archive/` (cleanup map) |
| [docs/HOMELAB-CD.md](docs/HOMELAB-CD.md) | GHCR + Helm + Tailscale → `sailpoint.lmsapp.us` |
| [config/README.md](config/README.md) | Where to add XML features |
| [config/PACKS.md](config/PACKS.md) | What CD ships (HelloWorld) vs what learners build |
| [docs/LOCAL_SETUP.md](docs/LOCAL_SETUP.md) | Local IIQ: **Docker or Tomcat** dual path |
| [docs/LESSON_VERIFY.md](docs/LESSON_VERIFY.md) | Lesson pass/fail verifier + learn-site progress |
| [docs/INFRASTRUCTURE.md](docs/INFRASTRUCTURE.md) | Beginner architecture |
| [docs/lessons/README.md](docs/lessons/README.md) | Progressive Meridian lessons |
| [tools/lab/README.md](tools/lab/README.md) | Tomcat laptop bootstrap |
| [tools/lab/docker/README.md](tools/lab/docker/README.md) | **One-command** Docker: IIQ + Academy + MCP + OpenAPI |

---

## Repo map (SSD)

```text
base/ga/                     ← GA zip from GHCR OCI (mnb-iam-ga:8.5), not committed
config/                      ← edit IIQ XML here (Applications, Rules, …)
src/  web/                   ← Java / UI customizations
docker/                      ← Tomcat 9 image + runtime iiq.properties injection
deploy/helm/                 ← umbrella sailpoint (CNPG + IIQ × 2)
build.properties             ← SSB knobs (IIQ 8.5, LCM, SSF flags)
sandbox.* / homelab.*        ← SPTARGET property sets
servers.properties           ← hostname → SPTARGET
scripts/                     ← SailPoint SSB Ant scripts (do not fork lightly)
tools/lab/                   ← Docker (preferred) + host Tomcat bootstrap
tools/iiq-mcp/  iiq-chat/    ← MCP + Teller
lab-data/                    ← HR / OpenLDAP sample files
archive/                     ← parked SSD samples (not runtime) — see docs/REPO_LAYOUT.md
docs/                        ← lessons, LOCAL_SETUP, INFRASTRUCTURE, HOMELAB-CD, vendor
.github/workflows/           ← SSB CI, publish GA OCI, publish image, deploy-homelab
```

---

## 1) First-time laptop (runtime)

Bootstrap Tomcat + lab MySQL + Academy (once, or day-2 restart):

```bash
./tools/lab/up.sh
# Academy → http://localhost:4173/  |  IIQ → http://localhost:8080/identityiq
```

Install-only (no Academy): `./tools/lab/setup-local.sh` then `source ~/.zshrc`.

Windows: `.\tools\lab\setup-local.ps1`

Login: `http://localhost:8080/identityiq` → `spadmin` / `admin`

---

## 2) Build & deploy customizations (SSD/SSB)

```bash
export SPTARGET=sandbox
./build.sh clean war          # uses bundled Ant in lib/ant
./build.sh deploy             # syncs into IIQHome from build.properties
# or import XML only:
./build.sh importdynamic
```

Add features under `config/` following [config/README.md](config/README.md).

---

## 3) CI / CD (next step — scaffold ready)

GitHub Actions workflow [`.github/workflows/ssb-ci.yml`](.github/workflows/ssb-ci.yml) already runs:

```text
./build.sh -Dtarget=sandbox clean war  →  upload identityiq.war
```

**CD follow-ups** (when you are ready):

1. Store `base/ga/identityiq-8.5.zip` in Git LFS or an artifact store (too large for normal git).  
2. Add a deploy job: download WAR → stop Tomcat → expand to `IIQHome` → start → smoke `login.jsf`.  
3. Inject secrets into `*.iiq.properties` from CI secret store.  
4. Promote with `SPTARGET=dev|test|prod` using matching `*.target.properties`.

---

## Environments

| SPTARGET | Property files |
| --- | --- |
| `sandbox` | `sandbox.iiq.properties`, `sandbox.target.properties`, `sandbox.ignorefiles.properties` |
| `dev` | `dev.*` |
| `prod` | `prod.*` |

Map machine hostnames in `servers.properties`.

---

## Removed / relocated from earlier layout

| Old | New |
| --- | --- |
| `identityiq-8.5/identityiq.war` | `base/ga/identityiq-8.5.zip` |
| `identityiq-8.5/doc`, `database` | `docs/vendor/iiq-8.5/` |
| `scripts/` (lab bootstrap) | `tools/lab/` (SSB owns `scripts/`) |
| Root `*.txt` samples | `lab-data/` |
| Root markdown / lessons | `docs/` |

---

## License note

IdentityIQ binaries and SSD/SSB tooling are SailPoint intellectual property. Use under your organization’s Compass entitlements. Prefer refreshing `build.xml` / `lib/` from the official SSD package on Compass when your team standardizes on a specific SSD version.
