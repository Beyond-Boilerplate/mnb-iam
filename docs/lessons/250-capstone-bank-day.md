# Lesson 250 — Capstone: Full Bank Day E2E

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~110 minutes  
**Prereq:** Lessons 201–249 (especially 206, 217, 222, 226–229, 233, 248)  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 50 / 110 / DoD

> **Why:** If you can run a bank day unassisted — hire → SSO → request → cert revoke → terminate with dead SSO — you own the platform.

## What this is

The Enterprise Lab **Definition of Done**: one **fresh** identity through a full operational day. You are not learning new features — you are proving Lessons 201–249 compose.

Use disposable name **`marcy.day`** (or another unused `lab.*` / unique hire). Never Helen / Priya / Marcus as the capstone subject.

## Know these

```text
Preflight smoke green
  → Pass-through login (Helen)
  → HCM joiner marcy.day → Workday agg → Refresh → Joiner WF → birthright
  → Portal + Gitea SSO
  → Access request → Manager+Owner → Mailpit → provision
  → Manager cert + app-owner cert → revoke hits target
  → Leaver → Portal/Gitea FAIL
  → SSD export touch + smoke
  → Toolkit/MCP JML status
```

| DoD # | Proof |
| --- | --- |
| 1 | Pass-through login |
| 2 | Joiner accounts on live targets |
| 3 | Portal + Gitea SSO |
| 4 | Request → approval → Mailpit → provision |
| 5 | Leaver → SSO dead |
| 6 | Cert revoke hits target |
| 7 | Config export / smoke |
| 8 | Toolkit/MCP smoke |

- **Wrong way:** Starting with a red `e2e-smoke.sh` — fix the stack first.
- **Wrong way:** Skipping SSO-dead proof after leaver — Terminated badge alone is not security.
- **Wrong way:** Using a shared persona — you will break later add-ons.

## Intent

- Green preflight; one new hire through joiner → SSO → request → cert → leaver.
- Bag evidence `01`–`08` under `~/iiq-lab-evidence/sandbox/250/`.
- Optional: induce and fix one failure with no notes (Lesson 230 reflexes).

## Before you start

- [ ] `./tools/lab/enterprise/e2e-smoke.sh` green (fix red items first)
- [ ] Uninterrupted ~110 minutes
- [ ] Lessons 217/219 workflows and 222 LCM map known (verify-or-create if wiped)
- [ ] Evidence:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/250
```

## Do this

### Task 0 — Preflight (10 min)

1. Run:

```bash
./tools/lab/enterprise/e2e-smoke.sh
```

- **Expect:** PASS (or intentional SKIP only). Fix red before continuing.

2. Hire:

```bash
./tools/lab/enterprise/hcm-scenario.sh joiner marcy.day Marcy Day \
  marcy.day@meridiannb.com 'Commercial Banking'
```

- **Expect:** JSON shows the new worker.

### Task 1 — Pass-through login — DoD #1 (10 min)

1. Confirm pass-through source (Lesson 206): OpenLDAP or Samba  
2. Log out of `spadmin`  
3. Log in as `helen.ross` / `LabUser1!` via directory credentials  

- **Expect:** successful IIQ session  
- Save `250/01-passthrough-login.png`

### Task 2 — Joiner → accounts — DoD #2 (20 min)

1. Aggregate **`MNB-Workday`** → Complete  
2. **Refresh Identity Cube** with **Process events** (so joiner trigger can fire)  
3. Confirm `MNB-Workflow-Joiner` ran (or launch manually for `marcy.day` per Lesson 217)  
4. If Lesson 242 added manager approval on joiner, approve it  
5. Run Lesson **233** aggregation order for targets (directories → JDBC → Wire/CRM → IdP → Refresh)  
6. Open `marcy.day` → Application Accounts  

- **Expect:** LDAP/AD + IdP + expected birthright links  
- Save `250/02-joiner-accounts.png`

> **Watch out:** Targets before Workday create orphans — HR first (233).

### Task 3 — Portal + Gitea SSO — DoD #3 (15 min)

1. Confirm Keycloak user + `portal-users` from birthright IdP pack (217) — do **not** hand-build unless pack missing  
2. Employee Portal [http://localhost:8092](http://localhost:8092/) as `marcy.day`  
3. Gitea [http://localhost:8093](http://localhost:8093/) via OIDC  

- **Expect:** both authenticated  
- Save `250/03-portal-sso.png` and `250/03-gitea-sso.png`

### Task 4 — Request → approval → Mailpit → provision — DoD #4 (20 min)

1. As `marcy.day` (or on-behalf): **Request Access** for CRM or Wire item she lacks  
2. Justification ≥ 20 chars (Lesson 243 validation if enabled)  
3. Note **IdentityRequest** id  
4. Approve Manager → Owner (`MNB-Workflow-Access-Approval` / Lesson 222)  
5. Mailpit [http://localhost:8025](http://localhost:8025) — assignment/completion trail  
6. Prove entitlement on live target (cube + curl/psql)  

- **Expect:** provisioned access tied to this request  
- Save `250/04-request-approval-*.png` + Mailpit + target proof

### Task 5 — Manager + app-owner certs — DoD #6 (20 min)

1. Manager cert (226) scoped to include `marcy.day` — **Revoke** at least one item  
2. App-owner cert (227) on the app from Task 4 — **Revoke** if appropriate  
3. Prove revokes (229): Provisioning Transaction + live query  

- **Expect:** target reflects revoke  
- Save `250/05-certs-*.png`

### Task 6 — Leaver → SSO dead — DoD #5 (15 min)

```bash
./tools/lab/enterprise/hcm-scenario.sh leaver marcy.day
```

1. Aggregate Workday → Refresh with **Process events** → `MNB-Workflow-Leaver` (219)  
2. Disable IdP if plan missed it (document gap)  
3. Attempt Portal + Gitea as `marcy.day`  

- **Expect:** **both fail**  
- Save `250/06-leaver-sso-dead-*.png`  
- Remediate any residual (ITSM manual entitlement, etc.)

### Task 7 — SSD export + smoke — DoD #7 (15 min)

1. Export any object you touched this session into `config/` (248 checklist pattern)  
2. `./build.sh importdynamic` (or your promote path) if you changed durable XML  
3. Re-run:

```bash
./tools/lab/enterprise/e2e-smoke.sh
./tools/lab/enterprise/contract-tests.sh
```

- **Expect:** green after the bank day  

### Task 8 — Toolkit / MCP smoke — DoD #8 (5 min)

```bash
curl -s -u spadmin:admin \
  'http://localhost:8080/identityiq/plugin/rest/mnbToolkit/enterprise/jml?identity=marcy.day' \
  | python3 -m json.tool
```

- **Expect:** inactive / leaver-aligned link list  

Via MCP (if available): list work items — no orphaned open items for `marcy.day`.

### Task 9 — Optional stretch (no notes)

Induce one failure (bad bind password, bogus attribute — Lesson 230) and fix from the error text alone.

## If it fails

| Symptom | Fix |
| --- | --- |
| Preflight red | Fix stack before Task 1 |
| Joiner never correlates | 233 order — Workday + Refresh before targets |
| Portal SSO fails for new hire | Birthright IdP pack / Keycloak groups (216–217) |
| Leaver doesn’t kill SSO | Disable Keycloak / `MNB-Keycloak-IdP` — LDAP alone is not enough |
| DoD item unprovable | Return to the owning lesson (217/222/226–229) and redo — do not skip |

## You are done when

- [ ] All eight DoD evidence files under `~/iiq-lab-evidence/sandbox/250/`  
- [ ] One identity, one sitting  
- [ ] SSO dead after leaver  

## Control note

- **Control:** End-to-end operational readiness (JML + request + cert + SSO + config-as-code)  
- **Owner:** IAM Engineering lead / capstone reviewer  
- **SLA (lab):** All eight DoD items same session  
- **Evidence:** `~/iiq-lab-evidence/sandbox/250/01`–`08`

## Quick check

1. Why HR before targets? → Avoid orphans (233)  
2. What proves leaver security? → Failed Portal/Gitea SSO, not only IIQ status  
3. Why a fresh identity? → Shared personas break add-ons and certs  

## Feedback

Could you run the eight DoD blocks from memory on a new name next week? Note which Task number broke and expected vs actual before asking for help.

## Navigate

- Previous: [Lesson 249](249-hardening-perf-lite.md)
- Next: [Lesson 251](251-workstation-grant-revoke.md)
- Theory (anytime after live apps): [256](256-connector-registry-theory.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
