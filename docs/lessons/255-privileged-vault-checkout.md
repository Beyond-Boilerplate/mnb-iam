# Lesson 255 — Privileged Vault Checkout (Break-Glass → PAM)

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~95 minutes  
**Prereq:** Lessons 223, 222 (approval / INC pattern); skim 251 optional  
**Stack:** `./tools/lab/docker/up.sh --enterprise --with=pam`

**Maps to classic track:** 86 (control narrative); IIQ emergency path from **223**

> **Why:** Shared root, Domain Admin, cloud break-glass, and payment-switch passwords belong in a vault with checkout controls — not tickets, chat, or a spreadsheet on a jump host.

## What this is

**Lesson 223** taught governed emergency **entitlement** access (INC + accelerated approval + sunset revoke) on Core Banking. This lesson adds **credential custody**:

| Layer | Owns | Meridian lab |
| --- | --- | --- |
| **IIQ** | Request, INC justification, approval, role / membership trigger, sunset revoke | BreakGlass Cloud path |
| **pam-lab** (`:8097`) | Safes, membership, checkout/check-in, session recording **stubs** | CyberArk-shaped facade |
| **Vault** (`:8200`) | Secret storage | HashiCorp Vault KV behind pam-lab |

This is **not** licensed CyberArk PVWA/PSM video. Recording is an audit stub in `/sessions` — same control story as classic Lesson 86 on the local stack.

Nothing is “simulated approve.” You will run a **real** IIQ break-glass request with `INC-LAB-001`, complete Manager→Owner (or documented LCM fallback), then PAM membership → Vault checkout → check-in → sunset revoke.

> **Watch out:** Default `./tools/lab/docker/up.sh --enterprise` does **not** start Vault/PAM. You need `--with=pam` (or `--enterprise-full`). If `:8097` / `:8200` are down, fix the stack before Task 1.

API quick reference (same as [`lab-data/enterprise/pam/README.md`](../../lab-data/enterprise/pam/README.md)):

```bash
curl -s http://localhost:8097/safes | python3 -m json.tool
curl -s -X POST http://localhost:8097/memberships \
  -H 'Content-Type: application/json' \
  -d '{"user":"lab.pam1","safe":"MNB-Safe-CloudBreakGlass","op":"add"}'
curl -s -X POST http://localhost:8097/checkout \
  -H 'Content-Type: application/json' \
  -d '{"safe":"MNB-Safe-CloudBreakGlass","account":"cloud-breakglass","requestedBy":"lab.pam1","incidentId":"INC-LAB-001","ttlMinutes":30}'
curl -s http://localhost:8097/sessions | python3 -m json.tool
```

**Never** paste checkout passwords into tickets, git, or screenshots.

## Know these

```text
Confirm Vault + pam-lab healthy (--with=pam)
  → Create disposable lab.pam1 + manager
  → Ensure requestable MNB-Bundle-BreakGlass-Cloud (seed or create)
  → Confirm LCM → MNB-Workflow-Access-Approval (223/222 pattern)
  → Request with INC-LAB-001 → real Manager + Owner approve
  → POST /memberships add (CloudBreakGlass)
  → Prove non-member 403; member checkout + sessions audit (no password in evidence)
  → POST /checkin → sunset: remove IIQ role + membership remove → checkout 403
```

| Term | Plain English | Meridian example |
| --- | --- | --- |
| **Safe** | Boundary for privileged accounts | `MNB-Safe-CloudBreakGlass` |
| **Membership** | Who may checkout that safe | `POST /memberships` after IIQ approval |
| **Checkout** | Time-bound secret retrieval + session stub | `incidentId` + TTL required |
| **Check-in** | End session; rotate narrative in production | `POST /checkin` with `checkoutId` |
| **Dual failure** | Incomplete control either way | IIQ role without vault **or** vault without IIQ request trail |
| **223 vs 255** | Entitlement drill vs credential custody | 223 = `WIRE_APPR` SQL; 255 = Vault password via PAM |

Seeded safes (from pam README):

| Safe | Purpose |
| --- | --- |
| `MNB-Safe-DomainAdmin` | Shared Domain Admin |
| `MNB-Safe-CloudBreakGlass` | Emergency cloud admin |
| `MNB-Safe-PaymentSwitch` | Payment switch root |
| `MNB-Safe-SharedRoot` | Bastion shared root |

- **Wrong way:** Slack DM / shared spreadsheet password on a jump host.  
- **Wrong way:** `POST /memberships` **before** a real IIQ INC approval (“simulated approve”).  
- **Wrong way:** Leaving membership after the incident — temporary that never ends is permanent.  
- **Wrong way:** Using Helen / Priya / Marcus / `jordan.reed` as the only subject — use disposable `lab.pam1`.  
- **Wrong way:** Storing checkout passwords in `~/iiq-lab-evidence/`.

## Intent

- Bring up PAM pack; prove Vault + pam-lab health.  
- Run a real IIQ BreakGlass Cloud request with `INC-LAB-001` (223 concepts).  
- Add safe membership only after approval; prove 403 for non-members.  
- Checkout / check-in with session audit (redacted).  
- Sunset: revoke IIQ role + remove membership; prove further checkout fails.

## Before you start

Complete every checkbox. Do not skip into Task 1 until these are true.

- [ ] Start (or extend) the stack with PAM:

```bash
cd /Users/alishaghatane/Documents/Sailpoint
./tools/lab/docker/up.sh --enterprise --with=pam
```

- [ ] IIQ up: [http://localhost:8080/identityiq](http://localhost:8080/identityiq) — `spadmin` / `admin`
- [ ] Pam-lab health:

```bash
curl -sf http://127.0.0.1:8097/health | python3 -m json.tool
```

- [ ] Vault unsealed / reachable:

```bash
curl -sf http://127.0.0.1:8200/v1/sys/seal-status | python3 -m json.tool
```

  - **Expect:** pam-lab shows `vaultReachable: true` (or equivalent); Vault `sealed: false`.

- [ ] You understand Lesson **223**: INC justification, accelerated Manager→Owner, written sunset, revoke proof. Credential custody is the new piece here.
- [ ] Read [`lab-data/enterprise/pam/README.md`](../../lab-data/enterprise/pam/README.md) once
- [ ] Evidence dir (**no passwords**):

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/255
```

## Do this

### Task 1 — Confirm PAM estate and safes

1. Open pam UI: [http://localhost:8097/](http://localhost:8097/)  
2. Open Vault UI: [http://localhost:8200/ui](http://localhost:8200/ui) — lab token `mnb-lab-vault-root` (**lab only**)  
3. List safes:

```bash
curl -sf http://localhost:8097/safes | python3 -m json.tool
```

- **Expect:** `MNB-Safe-DomainAdmin`, `MNB-Safe-CloudBreakGlass`, `MNB-Safe-PaymentSwitch`, `MNB-Safe-SharedRoot`.

4. If unhealthy:

```bash
docker compose -f docker-compose.iiq.yml -f docker-compose.enterprise.yml --profile enterprise up -d --build vault pam-lab
```

   Or re-run `./tools/lab/docker/up.sh --enterprise --with=pam`.

- **Why:** checkout against a missing PAM pack wastes the whole IIQ path.
- **Expect:** health + four safes before any identity work.

Save redacted health/safes JSON under evidence.

### Task 2 — Create disposable identity `lab.pam1`

Never use Helen, Priya, Marcus, Sanjay, or seeded `jordan.reed` as the break-glass subject for this drill.

1. From repo root:

```bash
./tools/lab/enterprise/hcm-scenario.sh joiner lab.pam1 Lab Pam \
  lab.pam1@meridiannb.com 'Bank Operations'
```

2. Confirm HCM:

```bash
curl -s http://localhost:8091/hcm/v1/workers/lab.pam1 \
  | python3 -m json.tool | grep -E 'userName|email|active|status|department'
```

3. Aggregate **`MNB-Workday`** → Complete  
4. **Refresh Identity Cube** for `lab.pam1` (promote attributes) → Complete  
5. Open cube → set **Manager** = **`sanjay.kapoor`** → Save → confirm

- **Why:** same disposable-subject rule as Lesson 223; Manager Approval needs a real manager.
- **Expect:** cube `lab.pam1` with manager `sanjay.kapoor`.

### Task 3 — Ensure requestable `MNB-Bundle-BreakGlass-Cloud`

Seed may already import `config/Bundle/MNB-Bundle-BreakGlass-Cloud.xml` (PAM-oriented IT role). **Verify** — do not assume.

1. **Setup → Roles** → search `MNB-Bundle-BreakGlass-Cloud`  
2. If **missing**, create:

| Field | Value |
| --- | --- |
| **Name** | `MNB-Bundle-BreakGlass-Cloud` |
| **Type** | **it** (or business + IT pack if your estate requires Required Roles — match seed: requestable IT is OK for this PAM drill) |
| **Owner** | `spadmin` |
| **Description** | `Time-bound emergency cloud admin — PAM safe MNB-Safe-CloudBreakGlass. INC required. Checkout via pam-lab — never Slack.` |
| **Requestable** | **ON** |
| **Assignment Rule** | empty |

3. Re-open and confirm **Requestable** is on  
4. Optional: Aggregate **`MNB-PAM-CyberArk`** (`http://pam-lab:8097/scim/v2`) so `SAFE:*` entitlements exist if you will map them later

- **Why:** Request Access only shows requestable roles; this pack is the IIQ half of Cloud BreakGlass (223 used Wire — different entitlement story).
- **Expect:** role searchable in Request Access.

> **Tip:** Lesson 223 told you **not** to use this pack for Core Banking SQL proof. Here it is the correct IIQ object — PAM safe membership is the proof surface.

### Task 4 — Confirm LCM map (assume nothing)

Same control as Lessons 222–223.

1. Gear → **Lifecycle Manager** → **Business Processes**  
2. Set both rows to **`MNB-Workflow-Access-Approval`** (create/fix from 222 if missing):

| Row | Must show |
| --- | --- |
| **Access Request** | `MNB-Workflow-Access-Approval` |
| **Roles Request** | `MNB-Workflow-Access-Approval` |

3. **Save** → re-open  

**Fallback:** `LCM Provisioning` with `approvalScheme=manager,owner`, `approvalMode=serial`. Record which path under evidence.

- **Why:** without the map, “break-glass” never creates Sanjay’s work item — and you must not skip to PAM membership.
- **Expect:** LCM confirmed before Task 5.

### Task 5 — Document sunset **before** grant

```bash
date '+Sunset start: %H:%M:%S'
```

Save `~/iiq-lab-evidence/sandbox/255/sunset.txt`:

```text
Sunset window: 15 minutes
Start time: <paste>
Incident: INC-LAB-001
Subject: lab.pam1
IIQ role: MNB-Bundle-BreakGlass-Cloud
PAM safe: MNB-Safe-CloudBreakGlass
Revoke method:
  1) Remove MNB-Bundle-BreakGlass-Cloud from lab.pam1 + Identity Refresh (provision)
  2) POST /memberships op=remove
  3) Prove checkout → 403
```

- **Why:** written sunset is the 223 discipline — credentials without reclaim are standing privilege.
- **Expect:** file saved before any request submit.

### Task 6 — Real IIQ break-glass request (INC required)

**Do not** call membership APIs yet.

1. As `spadmin`, **Request Access** on behalf of **`lab.pam1`**  
2. Select **`MNB-Bundle-BreakGlass-Cloud`**  
3. Justification — copy exactly:

```text
INC-LAB-001 — emergency cloud break-glass; PAM checkout required for on-call incident
```

4. Submit → note **IdentityRequest** id  

Write under evidence:

```text
IdentityRequest id: _______________
Subject: lab.pam1
Role: MNB-Bundle-BreakGlass-Cloud
Justification includes: INC-LAB-001
PAM membership yet: NO
```

- **Expect:** request accepted; **no** pam-lab membership for `lab.pam1` yet.
- **Why:** IIQ trail first — vault-without-request is the dual-failure half.

> **Watch out:** Soft text without `INC-LAB-001` fails this control — cancel and resubmit.

### Task 7 — Accelerated approval (real work items)

#### 7a — Manager as Sanjay

1. Log in as `sanjay.kapoor` / `LabUser1!` **or** Manage Work Items filtered to him  
2. Open Manager Approval for `lab.pam1` / BreakGlass Cloud  
3. **Approve** with:

```text
INC-LAB-001 — emergency approval, PAM sunset 15 minutes
```

- **Expect:** request moves to Owner Approval.

#### 7b — Owner as spadmin

1. Open Owner Approval  
2. **Approve** with:

```text
INC-LAB-001 — owner ack, time-boxed CloudBreakGlass
```

- **Expect:** workflow completes / provisions the BreakGlass Cloud role on `lab.pam1`.

Screenshot both approval comments (no secrets). Timestamps minutes apart = accelerated (223 language).

Confirm on the cube: **`MNB-Bundle-BreakGlass-Cloud`** assigned / detected.

- **Why:** this is the non-simulated gate — membership comes **after**.
- **Expect:** IdentityRequest shows both approvals + INC.

### Task 8 — PAM membership only after approval

1. Prove `lab.pam1` is not yet a safe member (optional list/membership GET if your pam-lab exposes it; otherwise proceed and rely on checkout 403 in Task 9 for a clean deny if you add the wrong user first).  
2. Add membership with the **exact** pam README shape (user = disposable subject):

```bash
curl -sf -X POST http://localhost:8097/memberships \
  -H 'Content-Type: application/json' \
  -d '{"user":"lab.pam1","safe":"MNB-Safe-CloudBreakGlass","op":"add"}' \
  | python3 -m json.tool
```

- **Expect:** JSON lists `MNB-Safe-CloudBreakGlass` under `lab.pam1`.
- **Why:** IIQ approved the emergency; PAM now allows checkout for that safe only.

Save redacted membership response under evidence.

### Task 9 — Deny non-member, then checkout as member

#### 9a — Non-member must fail

```bash
curl -s -o /tmp/pam-deny.json -w "%{http_code}\n" -X POST http://localhost:8097/checkout \
  -H 'Content-Type: application/json' \
  -d '{"safe":"MNB-Safe-CloudBreakGlass","account":"cloud-breakglass","requestedBy":"priya.wire","incidentId":"INC-LAB-001","ttlMinutes":15}'
python3 -m json.tool < /tmp/pam-deny.json
```

- **Expect:** HTTP **403** with `not_a_safe_member` (or equivalent). Save body under evidence (**still no password**).

#### 9b — Member checkout with INC

```bash
curl -s -o /tmp/pam-checkout.json -w "%{http_code}\n" -X POST http://localhost:8097/checkout \
  -H 'Content-Type: application/json' \
  -d '{"safe":"MNB-Safe-CloudBreakGlass","account":"cloud-breakglass","requestedBy":"lab.pam1","incidentId":"INC-LAB-001","ttlMinutes":30}'
python3 -m json.tool < /tmp/pam-checkout.json | sed -E 's/("password"\s*:\s*")[^"]*/\1***REDACTED***/'
```

1. Note `checkoutId`  
2. Confirm `incidentId` = `INC-LAB-001`, TTL present, `sessionRecording` true (or stub equivalent)  
3. **Do not** screenshot or commit the password field  

- **Expect:** HTTP **201** (or 200) with checkout metadata; password shown once in terminal only.
- **Why:** INC on checkout ties the secret retrieval to the same incident as the IIQ request.

If **409** `already_checked_out`: check in the prior checkout (Task 10) and retry.

### Task 10 — Session audit (no secrets) + check-in

```bash
curl -sf http://localhost:8097/sessions | python3 -m json.tool | head -60
```

- **Expect:** checkout event with recording started / INC; **no** password fields in the log.

Check in:

```bash
curl -sf -X POST http://localhost:8097/checkin \
  -H 'Content-Type: application/json' \
  -d '{"checkoutId":"<paste-checkoutId>"}' \
  | python3 -m json.tool
```

- **Expect:** `status: checked_in` (or equivalent); sessions show recording closed.

Save redacted `/sessions` excerpt under evidence.

> **Tip:** Expecting CyberArk PSM video here is wrong — stub audit is enough for lab Lesson 86 narrative.

### Task 11 — Optional SCIM view via `MNB-PAM-CyberArk`

1. **Applications → MNB-PAM-CyberArk** → Test Connection  
2. Run Account Aggregation  
3. Confirm SCIM user / entitlements mention `lab.pam1` and/or `SAFE:MNB-Safe-CloudBreakGlass` while membership is active  

- **Expect:** connector sees membership-shaped data **or** you record an honest gap if SCIM Users list lags the REST membership API.
- **Why:** some estates provision `SAFE:*` entitlements from IIQ; this lab still accepts direct `/memberships` after approval.

### Task 12 — Sunset revoke (IIQ + PAM)

When your sunset window ends (or reach T+window on purpose):

#### 12a — IIQ role remove

1. Open `lab.pam1` → remove **`MNB-Bundle-BreakGlass-Cloud`**  
2. **Refresh Identity Cube** with **provisioning** enabled → Complete  

#### 12b — PAM membership remove

```bash
curl -sf -X POST http://localhost:8097/memberships \
  -H 'Content-Type: application/json' \
  -d '{"user":"lab.pam1","safe":"MNB-Safe-CloudBreakGlass","op":"remove"}' \
  | python3 -m json.tool
```

#### 12c — Prove reclaim

```bash
curl -s -o /tmp/pam-after-revoke.json -w "%{http_code}\n" -X POST http://localhost:8097/checkout \
  -H 'Content-Type: application/json' \
  -d '{"safe":"MNB-Safe-CloudBreakGlass","account":"cloud-breakglass","requestedBy":"lab.pam1","incidentId":"INC-LAB-001","ttlMinutes":15}'
python3 -m json.tool < /tmp/pam-after-revoke.json
```

- **Expect:** HTTP **403** (not a member).  
- **Why:** 223 revoked SQL entitlement; here you revoke **credential eligibility**.

Final evidence note:

```text
INC-LAB-001
IdentityRequest: ________
IIQ approvals: Manager + Owner at <times>
Membership add: after approvals
CheckoutId: ________ (password not stored)
Check-in: yes
Sunset revoke: IIQ role removed + membership remove + checkout 403
LCM path: MNB-Workflow-Access-Approval | OOTB manager,owner
```

## If it fails

| Symptom | Fix |
| --- | --- |
| `:8097` / `:8200` down | `./tools/lab/docker/up.sh --enterprise --with=pam` or compose up `vault` + `pam-lab` |
| `vaultReachable: false` | Start/unseal Vault; recheck seal-status |
| No Manager work item | Task 2 manager + Task 4 LCM map; **resubmit** request (old requests do not re-route) |
| BreakGlass Cloud not in Request Access | Task 3 — Requestable ON; exact name |
| 403 after membership add | Username spelling must match `lab.pam1`; safe name exact `MNB-Safe-CloudBreakGlass` |
| 409 already_checked_out | Task 10 check-in, then retry checkout |
| Expecting PSM video | Recording is a stub audit event — use `/sessions` |
| Membership before IdentityRequest approvals | Stop — that is simulated approve; restart from Task 6 |
| Used Helen/Priya/Marcus/jordan.reed only | Create `lab.pam1` and restart from Task 2 |
| Password in evidence folder | Delete it; keep redacted JSON only |

## You are done when

- [ ] Stack includes PAM (`--with=pam`); safes list OK  
- [ ] Real IdentityRequest for `lab.pam1` with **`INC-LAB-001`** and Manager + Owner approvals  
- [ ] Membership added **after** approvals  
- [ ] Non-member checkout **403**; member checkout + check-in with `/sessions` audit (no passwords stored)  
- [ ] Sunset: IIQ role removed + membership removed + checkout **403**  
- [ ] Evidence under `~/iiq-lab-evidence/sandbox/255/` explains IIQ-without-vault vs vault-without-IIQ  

## Control note

- **Control:** Privileged credential custody (PAM checkout) bound to BreakGlass request + INC + sunset  
- **Owners:** Security (approval) + PAM Ops (safes) + IAM (role / membership)  
- **SLA (lab):** Membership minutes after approval; checkout TTL short (15–30 min in curls)  
- **Evidence:** `~/iiq-lab-evidence/sandbox/255/` — IdentityRequest id, approval screenshots, 403 bodies, redacted sessions, membership add/remove — **never** passwords  
- **Related:** Lesson [223](223-break-glass-live.md) (INC / accelerated approve / sunset on entitlements)

## Quick check

1. Who stores the password — IIQ or Vault? → **Vault** (via pam-lab)  
2. What must ride on every checkout? → **Incident id** (`INC-…`)  
3. Name the dual failure. → IIQ role without vault / vault access without IIQ request trail  
4. What stack flag starts PAM? → `--with=pam` (or `--enterprise-full`)  
5. How does this differ from Lesson 223? → 223 proves entitlement grant/revoke (e.g. SQL); 255 proves **credential** checkout after the same INC governance pattern  

## Feedback

Could you replay INC → real dual approve → membership → checkout → check-in → sunset revoke from memory, and explain why “simulated approve then curl membership” fails an examiner question?

If something failed, note the **task number**, HTTP status/body (redact secrets), and whether IIQ approvals existed before `/memberships`.

## Navigate

- Previous: [Lesson 254](254-password-reset-live.md)
- Next: [Lesson 256](256-connector-registry-theory.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md) · PAM: [pam/README.md](../../lab-data/enterprise/pam/README.md) · Break-glass concepts: [223](223-break-glass-live.md) · Classic: [86](86-pam-cyberark-module.md)
