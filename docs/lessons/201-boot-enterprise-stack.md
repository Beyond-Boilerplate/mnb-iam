# Lesson 201 — Boot the Enterprise Sandbox

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~40 minutes  
**Prereq:** Docker Desktop (≥16 GB RAM recommended), classic Lessons 01–110 or Capstone 50  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** N+4 infra

> **Why (1–2 lines):** One command brings up the bank's production-like estate; Core stays CSV-light so Academy never carries this weight. An examiner who asks "how do you know your evidence isn't from a half-broken lab" gets answered by a green smoke test, not a screenshot.

## What this is

The Core stack (`./tools/lab/docker/up.sh`) gives you IIQ + Postgres + OpenLDAP + Academy + MCP + Teller — enough for CSV-first lessons 01–110. The `--enterprise` profile layers a second Compose file (`docker-compose.enterprise.yml`) on top: **Samba AD** (a real LDAP-speaking domain controller standing in for corporate AD), **Keycloak** (an Okta-shaped OIDC/SCIM identity provider), **Employee Portal** and **Gitea** (two real OIDC relying-party apps you SSO into), and **Mailpit** (a catch-all SMTP sink). Nothing about Core changes — this is strictly additive, gated behind the Compose `enterprise` profile, so you can always fall back to `up.sh` without the extra RAM cost. From this lesson forward, every lesson assumes `--enterprise` is running.

## Know these

- `up.sh` (Core) = IIQ + Postgres + OpenLDAP + Academy + MCP + Teller — 6 services, CSV-first.
- `up.sh --enterprise` = Core + `docker-compose.enterprise.yml` overlay = 11 services (adds `samba-ad`, `keycloak`, `keycloak-http-relax`, `employee-portal`, `mailpit`, `gitea`).
- New ports: IIQ `:8080`, Mailpit `:8025`, Portal `:8092`, Keycloak `:8085`, Gitea `:8093`, HCM mock `:8091`, Samba LDAP `:3890`.
- Preflight checks 17 host ports before touching Docker — it refuses to start a half-broken stack on purpose.
- **Wrong way:** Calling the stack "up" because `docker ps` shows containers running — Keycloak and Samba report `running` long before their healthcheck (and real usability) flips to `healthy`.

## Intent

- Prove the enterprise Compose profile starts cleanly on top of Core (11 services, not 6).
- Confirm every new host port is reachable.
- Run the automated smoke test and get every check to PASS, not just "mostly green."
- Know where to look (`docker compose ... logs`) when a container never reaches healthy.

## Before you start

- [ ] Docker Desktop running; memory limit raised toward ≥16 GB (Settings → Resources → Memory)
- [ ] Repo root shell — `ls tools/lab/docker/up.sh` resolves
- [ ] No stray process bound to `8080/8085/8090-8093/3890/8025/1026` (`lsof -nP -iTCP -sTCP:LISTEN`)
- [ ] Evidence dir: `mkdir -p ~/iiq-lab-evidence/sandbox/201`

## Do this

1. From the repo root, run `./tools/lab/docker/up.sh --enterprise`.  
   **Why:** superset of Core `up.sh` — still boots Postgres/IIQ/OpenLDAP/Academy/MCP/Teller, then brings up `samba-ad`, `keycloak`, `keycloak-http-relax`, `employee-portal`, `mailpit`, `gitea` under Compose profile `enterprise`, and regenerates enterprise identity artifacts first.  
   **Expect:** script output lists every enterprise service starting, in addition to the Core six.

2. Watch the preflight port check at the top of the output.  
   **Why:** it fails fast, before touching Docker, if any of the 17 host ports it checks (including `8085`, `8091`, `8092`, `3890`, `8025`, `1026`, `8093`) are already bound.  
   **Expect:** "ports clear" before any container action; if not, free the port or `./tools/lab/docker/down.sh` first.

3. If `identityiq` exits or restarts with code 137 (OOM-killed), quit other memory-heavy apps, raise Docker Desktop's memory limit, and re-run.  
   **Why:** `up.sh` is idempotent — it resumes rather than duplicating services.  
   **Expect:** stack completes on retry without a full teardown.

4. Expect first boot to **build** the `employee-portal` image (`docker/Dockerfile.employee-portal`) and pull/build Samba, Keycloak, Mailpit, and Gitea images.  
   **Why:** first run always costs more than a bare `up.sh`; subsequent runs skip rebuilds unless you pass `--rebuild`.  
   **Expect:** noticeably longer first-run time, faster on repeat.

5. Once the script prints `Ready.`, open each new surface once: IIQ `http://localhost:8080/identityiq` (spadmin/admin), Mailpit `http://localhost:8025/`, Employee Portal `http://localhost:8092/`, Keycloak admin `http://localhost:8085/admin/` (admin/admin), Gitea `http://localhost:8093/`, HCM mock `http://localhost:8091/hcm/v1/workers`.  
   **Why:** you need to know what "up" looks like before later lessons depend on it silently working.  
   **Expect:** all six load without error in a browser.

6. Run the automated end-to-end smoke test: `./tools/lab/enterprise/e2e-smoke.sh`.  
   **Why:** it checks connector-mock health, the HCM/CRM/ITSM mock endpoints, an OpenLDAP `ldapsearch` for `helen.ross`, the Keycloak `meridian` realm, Employee Portal `/health`, Mailpit's API, Gitea's API, IIQ reachability, and a live HCM joiner POST round-trip in one pass.  
   **Expect:** every line reads `PASS`; `SKIP` only appears without `--enterprise`.

7. If anything reads `FAIL`, fix it now — don't move on.  
   **Why:** the rest of this path assumes a fully green stack; a silent gap here compounds into confusing failures three lessons later.  
   **Expect:** re-running prints `Result: N passed, 0 failed`.

8. Save the smoke test output under evidence.  
   **Expect:** `~/iiq-lab-evidence/sandbox/201/` holds your first "green stack" proof for later reference.

## If it fails

- **Preflight port conflict** — `lsof -nP -iTCP:<port> -sTCP:LISTEN` to identify it, or `./tools/lab/docker/down.sh` to fully tear down first.
- **`identityiq` exit 137** — OOM; raise Docker Desktop memory, close other containers/VMs, re-run.
- **Keycloak never healthy** — `docker compose -f docker-compose.iiq.yml -f docker-compose.enterprise.yml logs --tail=100 keycloak`; first-boot realm import can take 60+ seconds, matching the healthcheck's `start_period`.
- **Gitea shows "Install" page** — force-recreate: `docker compose -f docker-compose.iiq.yml -f docker-compose.enterprise.yml --profile enterprise up -d --force-recreate gitea`.
- **`e2e-smoke.sh` FAILs on OpenLDAP** — install `ldapsearch` (`brew install openldap`) or run the query via `docker exec mnb-openldap ldapsearch ...`.
- **Ports don't respond after a Mac sleep/resume** — `docker compose ... restart` the specific service.

## You are done when

`./tools/lab/enterprise/e2e-smoke.sh` prints `Result: N passed, 0 failed`, and you have personally loaded IIQ, Mailpit, Portal, Keycloak, and Gitea in a browser at least once.

## Control note

- **Control:** Environment provisioning / stack readiness gate.
- **Owner:** IAM Ops / Platform engineering.
- **SLA (lab):** Green smoke test required same session before any dependent lesson starts.
- **Evidence:** `~/iiq-lab-evidence/sandbox/201/` — smoke test output, one screenshot per new surface.

## Quick check

1. What Compose flag gates every enterprise-only service? → profile `enterprise`.
2. Why can `docker ps` lie about readiness? → "running" ≠ "healthy" — Keycloak/Samba need their own healthcheck to pass.
3. What's the one command that proves the whole stack, not just one container? → `./tools/lab/enterprise/e2e-smoke.sh`.

## Navigate

- Previous: — (start of path)
- Next: Lesson 202
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
