# Lesson 201 — Boot the Enterprise Sandbox

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~50 minutes  
**Prereq:** Docker Desktop (≥16 GB RAM recommended); classic Lessons 01–110 helpful but not required  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** N+4 infra · **103** (wrong-env banner / branding cue)

> **Why:** One command should bring up a bank-shaped estate you can trust. A green `docker ps` does not prove services answer — and “stack is up” does **not** mean Identity Warehouse already has Helen and peers. Examiners also ask how you prevent wrong-system administration: an unmistakable **SANDBOX** cue (classic 103) is cheaper than hoping operators notice the URL.

## What this is

`./tools/lab/docker/up.sh --enterprise` is the single entry point. Internally it layers Compose Core + `docker-compose.enterprise.yml` (`--profile enterprise`), then plugin install, then seed. Seed imports **Application definitions** and enterprise XML — it does **not** mint workforce identity cubes.

```text
up.sh --enterprise
        │
        ├─ 1. Infra     Docker services (healthy ≠ "all apps aggregated")
        ├─ 2. Bootstrap IIQ init + MNB-Rule-Hello-World
        ├─ 3. Plugin    Meridian toolkit → agentReady
        ├─ 4. Reset     backup → wipe (default; keeps spadmin + HelloWorld)
        ├─ 5. App defs  MNB-HR (non-authoritative) + MNB-OpenLDAP — no aggregation
        └─ 6. Ent seed  enterprise XML (MNB-Workday authoritative definition, …)
                          Warehouse: spadmin only until Lesson 207
```

> **Watch out:** After boot, **Identities → Identity Warehouse** should show `spadmin` — not `helen.ross`. People exist in HCM / LDAP / Keycloak backends; IIQ cubes wait for you to aggregate **MNB-Workday** in Lesson 207.

## Know these

| Term | Plain English | Meridian example |
| --- | --- | --- |
| **Enterprise boot** | One script: infra + plugin + definition-only seed | `./tools/lab/docker/up.sh --enterprise` → `Ready.` |
| **Definition-only seed** | App XML / tasks / workflows imported; **no** workforce cubes | `MNB-Workday` exists; Helen does not |
| **Surface vs container** | Browser/API answer ≠ “container running” | Portal `:8092` must load, not only `docker ps` |
| **Wrong-env banner** | Visible SANDBOX / PROD cue so ops never edit the wrong host (classic **103**) | `Meridian National Bank — SANDBOX` on login/home |
| **Lite vs full** | `--enterprise` may omit Samba/SSO/PAM until `--with=` | Add `--with=ad,sso,pam` or `--enterprise-full` when a lesson needs them |

### What bootstrap already stood up

After a successful `Ready.` (default seed, not `--skip-seed`), treat this as your starting inventory.

**Infra (Docker — answering on the host)**

| Surface | URL / port | Creds / notes |
| --- | --- | --- |
| IIQ | http://localhost:8080/identityiq | `spadmin` / `admin` |
| Academy | http://localhost:4173/ | Lessons + Verify |
| MCP | http://127.0.0.1:8766/mcp | Bearer `mnb-lab-mcp-key` |
| Teller | http://localhost:4180/ | IIQ chatbot |
| OpenLDAP | `:389` · UI `:8090` | admin bind `cn=admin,dc=meridiannb,dc=com` / `admin` |
| connector-mock | `:8091` | HCM API + **MNB Workday** UI `/hcm/ui` |
| Keycloak | http://localhost:8085/ | `admin` / `admin` · realm `meridian` |
| Employee Portal | http://localhost:8092/ | Keycloak personas (`helen.ross` / `LabUser1!`) |
| Mailpit | http://localhost:8025/ | UI only until Lesson 203 wires IIQ SMTP |
| Gitea | http://localhost:8093/ | OIDC later (Lesson 213) |
| Samba AD | `:3890` | LDAP/Kerberos DC (users best-effort seeded) |
| Vault / PAM | `:8200` / `:8097` | lab token / CyberArk-shaped checkout |
| Extra portals | `:8094`–`:8096` | Workstation / HR Intranet / Finance |

Also regenerated on enterprise boot: artifacts under `lab-data/enterprise/generated/` from `identity-master.json` (~41 personas).

**IdentityIQ — created / imported**

| Kind | What you get | Aggregated / cubes? |
| --- | --- | --- |
| **Kept through wipe** | `spadmin`, `MNB-Rule-Hello-World` | N/A |
| **Applications (defs)** | `MNB-HR` (**not** authoritative), `MNB-OpenLDAP` | **No** — definitions + Test Connection only |
| **Applications (Enterprise)** | `MNB-Workday` (authoritative flag on app), AD-Live, Okta, CoreBanking, CRM-Live, ServiceNow, Entra, PAM, … | **No** — XML only; you aggregate starting Lesson 207 |
| **TaskDefinitions** | `MNB-Acct-Aggregation`, `MNB-Daily-Aggr`, `MNB-OpenLDAP-Group-Aggregation` (may need UI create if wipe left Tasks empty) | Imported templates — not a finished Workday agg task |
| **Identities** | **`spadmin` only** | Workforce cubes = Lesson **207** |
| **Workflows / roles / QuickLinks** | Joiner/Leaver/Access-Approval; birthright bundles; … | Present; Triggers often soft-fail (Lesson 202) |

**Explicitly not done at boot**

- IIQ → Mailpit SMTP (Lesson **203**)
- First workforce cubes from **MNB-Workday** (Lesson **207**)
- Aggregation of directories / other live apps (Lessons **204–210+**)
- Pass-through login as `helen.ross` (Lesson **206** — needs cubes from 207)
- Durable wrong-env banner promotion (Lesson **248** / classic **103**) — you still **spot-check** the cue in this lesson

**Escape hatch:** Seed **overlays** by default (keeps `MNB-*`). Pass `--wipe` for backup→reset. `--skip-seed` starts infra + plugin only. Lite `--enterprise` omits Samba/SSO/PAM — add with `--with=ad,sso,pam` or use `--enterprise-full`.

- **Wrong way:** Searching Warehouse for Helen right after `Ready.` and assuming seed failed — empty workforce is the contract.  
- **Wrong way:** Treating “container Up” as “service answers” — always open the URL.  
- **Wrong way:** Editing lab IIQ without a **SANDBOX** mental (and preferably visible) cue — classic 103 wrong-env incident.  
- **Wrong way:** Using `--wipe` casually when you only meant to restart a container.

## Intent

- Boot the estate with one command and reach `Ready.`
- Prove key surfaces load in a browser (not just “container running”).
- Spot the wrong-env / branding cue (or record the gap for Lesson 248).
- Confirm Warehouse has **no** workforce cubes yet; apps exist as definitions.
- Pass smoke + lesson asserts before Lesson 202.

## Before you start

- [ ] Docker Desktop running; memory toward **≥16 GB**
- [ ] Repo root: `ls tools/lab/docker/up.sh`
- [ ] Ports free (or owned by this stack): `8080`, `8085`, `8090–8097`, `3890`, `8025`, `1026`, `8200`, …
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/201
```

## Do this

### Task 1 — Boot the estate

One command starts Core + enterprise Compose, installs the plugin, and runs the seed contract. Skipping this leaves every later lesson without a live target.

```bash
./tools/lab/docker/up.sh --enterprise
```

- **Why:** this is the single entry point — infra, bootstrap, and definition-only seed in one place.
- **Expect:**
  - Preflight ports clear (or owned by `mnb-iiq-lab`)
  - Script ends with `Ready.`
  - Seed lines say **definitions only** / no workforce cubes (unless leftovers from an older wipe-heavy seed)

> **Tip:** First boot may **build** images (slow). Later runs skip rebuild unless you pass `--rebuild`. Seed overlays by default — use `--wipe` only when you want a clean Meridian reset.

### Task 2 — Open each surface in a browser

A healthy container can still hide a broken UI path. Click through once so later lessons aren’t debugging “was this ever up?”

| Surface | URL | Creds |
| --- | --- | --- |
| IIQ | http://localhost:8080/identityiq | `spadmin` / `admin` |
| Mailpit | http://localhost:8025/ | — |
| Employee Portal | http://localhost:8092/ | — |
| Keycloak admin | http://localhost:8085/ | `admin` / `admin` |
| Gitea | http://localhost:8093/ | — |
| MNB Workday UI | http://localhost:8091/hcm/ui | — |

- **Why:** browser load is your personal baseline before mail, SSO, and HCM lessons depend on these quietly.
- **Expect:** all six load without error. Workday UI already lists Helen — that is the *HCM source*, not an IIQ cube yet.

### Task 3 — Wrong-env banner / branding cue (classic 103)

Before you explore menus, prove you know **which estate** you are on. In production, wrong-environment logins are incident tickets.

1. On the IIQ **login** page (logged out or private window), look for:
   - Product / welcome text that includes **SANDBOX**, **Meridian**, or lab wording  
   - Header / footer hostname cue (`localhost:8080`)
2. After login as `spadmin`, glance at home / header for the same cue
3. Optional contrast: open Academy [http://localhost:4173/](http://localhost:4173/) — lab training surface, not a second IIQ
4. Under evidence, write one line:

```text
Env cue visible: YES/NO — where: _____ — banner text (or "missing; treat localhost:8080 as SANDBOX until Lesson 248")
```

If `web/WEB-INF/classes/sailpoint/web/messages/iiqCustom.properties` still has only the commented `login_ui_welcome` example, a missing banner is **expected** until Lesson **248** tokens it. Do **not** invent a prod-looking UI.

- **Why:** classic 103 — color alone is insufficient; the word **SANDBOX** (or unmistakable lab hostname discipline) prevents irreversible edits on a look-alike host.
- **Expect:** either a visible SANDBOX/Meridian cue **or** an explicit evidence note that the durable banner lands in 248 — and you still treat this session as lab-only.

> **Watch out:** A QuickLink labeled “sandbox tools” is **not** a substitute for a global login/home banner. Hostname `localhost` helps locally; production twins need the banner.

### Task 4 — Spot-check bootstrap inventory in IIQ

Boot hands you infra + app *definitions*, not a Warehouse full of Meridian employees. Prove that contract now.

1. **Applications → Application Definition**
   - Confirm `MNB-HR`, `MNB-OpenLDAP`, plus enterprise defs (`MNB-Workday`, `MNB-ActiveDirectory-Live`, `MNB-Okta`, `MNB-CoreBanking`, …)
   - Open `MNB-HR` → confirm it is **not** marked authoritative
2. **Setup → Tasks** → search `MNB` for imported task templates (create later if empty after a bad wipe)
3. **Identities → Identity Warehouse** → search `helen.ross`
   - **Expect:** no workforce hit (or leftovers only if you never wiped). `spadmin` is fine.

- **Why:** empty workforce search is success here — cubes start in Lesson 207 from `MNB-Workday`.
- **Expect:** inventory matches the Know these tables.

> **Watch out:** Searching Warehouse for Helen and assuming seed failed is the wrong diagnosis — empty workforce is the contract.

### Task 5 — Run smoke + lesson asserts

```bash
./tools/lab/enterprise/e2e-smoke.sh
./tools/lab/enterprise/verify-lesson.sh 201
```

- **Why:** smoke checks HTTP/LDAP surfaces; `verify-lesson.sh` prints every assert as `PASS`/`FAIL`.
- **Expect:** smoke `PASS` (documented `SKIP` only when not on `--enterprise`); hard asserts PASS.

Save output under `~/iiq-lab-evidence/sandbox/201/`.

## If it fails

| Symptom | Fix |
| --- | --- |
| Preflight port conflict | `lsof -nP -iTCP:<port> -sTCP:LISTEN` or `./tools/lab/docker/down.sh` |
| `identityiq` exit 137 | Raise Docker Desktop memory; close heavy apps; re-run (`up.sh` is idempotent) |
| Keycloak never healthy | Wait for healthcheck `start_period`; `docker compose … logs keycloak` |
| Gitea “Install” page | First-boot race — `--force-recreate gitea` (see [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)) |
| Smoke FAIL on OpenLDAP | Install host `ldapsearch` (`brew install openldap`) or `docker exec mnb-openldap ldapsearch …` |
| Re-`up` wiped my apps | Default is **overlay** — wipe only with `--wipe`; restore from `lab-data/backups/iiq-*/` if you wiped by mistake |
| Warehouse empty of Helen | **Expected** — create cubes in Lesson 207 from `MNB-Workday` |
| `/hcm/ui` 404 | Rebuild `connector-mock`: `docker compose -f docker-compose.iiq.yml up -d --build --force-recreate connector-mock` |
| No SANDBOX string anywhere | Expected until Lesson 248 — record the gap; do not treat the UI as production |

## You are done when

- [ ] `up.sh --enterprise` reached `Ready.`
- [ ] Browser check of IIQ, Mailpit, Portal, Keycloak, Gitea, and MNB Workday UI succeeded
- [ ] Wrong-env / branding cue checked (visible **or** gap noted for Lesson 248)
- [ ] You can state: seed imports definitions; **no** workforce cubes until Workday aggregation
- [ ] `e2e-smoke.sh` → `Result: N passed, 0 failed`
- [ ] `./tools/lab/enterprise/verify-lesson.sh 201` hard asserts PASS
- [ ] Evidence saved under `~/iiq-lab-evidence/sandbox/201/`

## Control note

- **Control:** Environment provisioning / readiness gate + wrong-env identification
- **Owner:** IAM Ops / Platform
- **SLA (lab):** green smoke + env cue check before any dependent enterprise lesson
- **Evidence:** `~/iiq-lab-evidence/sandbox/201/` — smoke log + empty workforce screenshot + banner/cue note

## Quick check

1. Does `up.sh --enterprise` create Helen’s identity cube? → **No** — only app definitions; cubes start in Lesson 207.  
2. Is `MNB-HR` authoritative after enterprise seed? → **No** — CSV contrast only; `MNB-Workday` is the authoritative HCM app.  
3. How do you **wipe** existing `MNB-*` objects before re-seed? → `--wipe` (or `./tools/lab/scripts/backup-and-reset-lab.sh`).  
4. Why care about a SANDBOX banner on day one (classic 103)? → Prevents irreversible changes on a look-alike host; durable tokens land in Lesson 248.

## Feedback

Could you redo the boot and explain why Warehouse is empty — and what wrong-env cue you looked for — from memory? If something tripped you up, note the **Task number**, what you expected, and what you saw (paste the failing `verify-lesson.sh` line if you have it).

## Navigate

- Previous: — (start of Enterprise Sandbox Path)
- Next: [Lesson 202 — Identity Master & Enterprise Seed](202-identity-master-and-seed.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md) · Branding classic: [103](103-ui-customization-branding.md) · Durable banner: [248](248-ssd-promote-live.md)
