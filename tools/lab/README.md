# Scripts

Automation for the local IdentityIQ 8.5 lab.

**Prefer Docker instead?** See [`docker/README.md`](docker/README.md) (`docker-compose.iiq.yml`). Both paths stay supported.

## Seed lab data (Docker stack)

After IIQ + MCP + OpenLDAP are up and Meridian Custom APIs flags are enabled:

```bash
export MCP_API_KEY=mnb-lab-mcp-key
./tools/lab/scripts/seed-mnb-lab-data.sh
```

**Default:** overlay seed for **MNB-HR** and **MNB-OpenLDAP** (keeps live `MNB-*`).  
Destructive reset: `./tools/lab/docker/up.sh --wipe` or `./tools/lab/scripts/seed-mnb-lab-data.sh --wipe`.

Details: `lab-data/connectors/ldap/README.md`.

## Sync UI changes back to `config/`

After editing apps/tasks in the IIQ UI:

```bash
export MCP_API_KEY=mnb-lab-mcp-key
./tools/lab/scripts/sync-iiq-config.sh           # diff only
./tools/lab/scripts/sync-iiq-config.sh --write   # update config/
git diff -- config/
```

Tracked objects are listed in `tools/lab/scripts/sync_iiq_config.py` (`MANIFEST`). Use `--discover` to pick up extra `MNB-*` Applications.

## Platform support (Tomcat + MySQL host install)

| OS | Entry point | Notes |
| --- | --- | --- |
| **macOS** | `./tools/lab/up.sh` | Installs (via setup-local) then Academy; JDK 11 + mysql@8.4 |
| **Linux / WSL2** | `./tools/lab/up.sh` | Same; apt/dnf or portable Temurin + MySQL tarball |
| **Windows** | `.\tools\lab\setup-local.ps1` or `setup-local.cmd` | Native PowerShell; winget Temurin when possible + portable MySQL/Tomcat |
| Git Bash on Windows | ❌ redirected | Use PowerShell or WSL2 (script exits with instructions) |

### Will it work on Windows?

**Yes — via the PowerShell scripts**, not the `.sh` files.

```powershell
cd path\to\Sailpoint
powershell -ExecutionPolicy Bypass -File .\tools\lab\setup-local.ps1
. $PROFILE
iiq-status
iiq-open
```

Or double-click / run:

```bat
scripts\setup-local.cmd
```

Teardown:

```powershell
.\tools\lab\teardown-local.ps1 -Yes
```

WSL2 Ubuntu is also fully supported with the bash scripts.

---

## What a greenfield setup does

1. Detect OS / CPU  
2. Ensure `curl` / base tools  
3. Install **JDK 11** (Homebrew / apt / winget / portable Temurin download)  
4. Install **MySQL 8.4** binaries (package or portable) and start a **lab instance on port 3307**  
5. Download **Tomcat 9** into `~/iiq-lab` (or `%USERPROFILE%\iiq-lab`)  
6. Explode `identityiq.war`, configure `iiq.properties`  
7. Import `init.xml` + `init-lcm.xml`  
8. Wire shell aliases / PowerShell profile helpers  
9. Start Tomcat and wait for the login page  

Your existing system MySQL on **:3306** (if any) is left alone.

---

## Commands

### macOS / Linux / WSL

```bash
./tools/lab/up.sh --check              # preflight only
./tools/lab/up.sh                      # IIQ (setup or start) + OpenAPI + MCP + Academy
# Academy → http://localhost:4173/  |  IIQ → http://localhost:8080/identityiq
# Lab hub → http://localhost:9000/  |  DB viewer → http://localhost:9001/
# OpenAPI → http://localhost:8765/swagger/  |  MCP → http://127.0.0.1:8766/mcp

./tools/lab/up.sh --force-db           # rebuild schemas + re-import, then sidecars + Academy
./tools/lab/up.sh --sidecars-only      # OpenAPI + MCP only
./tools/lab/setup-local.sh             # install-only (no Academy)
source ~/.zshrc   # or ~/.bashrc
iiq-help
iiq-status

./tools/lab/teardown-local.sh --yes
./tools/lab/teardown-local.sh --yes --purge-mysql
```

### Windows

```powershell
.\tools\lab\setup-local.ps1 -Check
.\tools\lab\setup-local.ps1
. $PROFILE
iiq-help

.\tools\lab\teardown-local.ps1 -Yes
```

---

## Files

| File | Purpose |
| --- | --- |
| `up.sh` | **One command:** ensure IIQ + OpenAPI + MCP + start Academy |
| `start-sidecars.sh` | OpenAPI (:8765) + MCP (:8766) only |
| `setup-local.sh` / `teardown-local.sh` | Install-only / teardown (Unix / WSL) |
| `start-academy.sh` | Wrapper → `up.sh --academy-only` |
| `setup-local.ps1` / `teardown-local.ps1` | Windows native |
| `setup-local.cmd` / `teardown-local.cmd` | Windows launchers |
| `iiq-aliases.sh` / `iiq-aliases.ps1` | Day-2 helpers |
| `lib/common.sh` | Shared Unix helpers |
| `lib/bootstrap.sh` | Greenfield package/portable installs |

---

## Lab layout

| Path | Contents |
| --- | --- |
| `~/iiq-lab/tomcat` or `%USERPROFILE%\iiq-lab\tomcat` | Tomcat 9 + exploded IIQ |
| `…/mysql` | Lab MySQL datadir (+ portable dist if used) |
| `…/jdk` | Portable JDK (only if package install unavailable) |
| `…/data` | Sample CSV copies |
| `~/.iiq-lab/env` or `%USERPROFILE%\.iiq-lab\env.ps1` | Environment for aliases |

Default login: `http://localhost:8080/identityiq` → `spadmin` / `admin`

---

## Prerequisites you still need

Even on a “blank” sandbox, you need:

1. **This repo** including `base/ga/identityiq-8.5.zip` (large; not auto-downloaded — it is licensed SailPoint media)  
2. **Network** to download Temurin / Tomcat / MySQL / Homebrew bottles  
3. On macOS first run: **Xcode Command Line Tools** may prompt once (`xcode-select --install`) before Homebrew can finish  
4. On Linux package installs: **sudo** (portable JDK/MySQL fallbacks avoid sudo when packages fail)  
5. On Windows: **PowerShell 5.1+** (built into Windows 10/11)

---

## Notes

- Lab MySQL uses **caching_sha2_password** (MySQL 8.4 disables `mysql_native_password` by default).  
- Prefer JDK **11** (17 also OK). Newer JDKs trigger an automatic JDK 11 install attempt.  
- `--check` / `-Check` never changes the machine — safe on a locked-down laptop.
