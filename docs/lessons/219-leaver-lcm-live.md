# Lesson 219 — Leaver LCM End-to-End

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~85 minutes  
**Prereq:** Lessons 216–217  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 31 / 34

> **Why:** A leaver is only done when SSO fails and accounts are disabled everywhere — a Terminated badge alone is a paper trail, not security. Prove disable on directory and IdP, not just IIQ status.

## What this is

A **leaver** is someone who leaves the bank (termination). In IIQ, that usually means:

1. HR marks the worker inactive / Terminated  
2. Aggregation flips cube attributes (`active`, `status`, `inactive`, …)  
3. An **IdentityTrigger** of type `attributeChange` launches a **leaver workflow**  
4. The workflow refreshes with `provision=true` and `disable=true` — a **disable plan** across linked applications  

Like the joiner (Lesson 217), the workflow and trigger are often **missing after a wipe / partial seed**. You create them (or import shipped XML), then terminate a **disposable** identity — never Helen or Priya.

**Multi-store reality:** Disabling OpenLDAP does **not** automatically disable Keycloak. Portal SSO authenticates against the IdP. If birthright provisioned `MNB-Keycloak-IdP` (Lesson 216–217), the disable plan should hit Keycloak too; if not, you disable IdP manually and record the gap.

Classic 31/34 taught rapid offboarding on CSV; here proof is failed Portal login + directory/IdP disable.

## Know these

```text
You create (if missing): MNB-Workflow-Leaver + MNB-IdentityTrigger-Leaver
                │
HCM PATCH active=false / Terminated
  → Aggregate MNB-Workday → cube inactive/status flip
  → Identity Refresh with **Process events**
  → attributeChange trigger → MNB-Workflow-Leaver
  → refreshIdentity(provision=true, disable=true)
  → disable plan → OpenLDAP / Wire / CRM / Keycloak IdP
  → Portal SSO must FAIL
```

| Object | Type | Job |
| --- | --- | --- |
| `MNB-Workflow-Leaver` | Workflow (`IdentityLifecycle`) | Log + `refreshIdentity` with disable + provision |
| `MNB-IdentityTrigger-Leaver` | IdentityTrigger (`attributeChange`) | Fires that workflow when watched attributes change |

| Surface | How you prove disable |
| --- | --- |
| OpenLDAP / Samba | `ldapsearch` / failed pass-through (Lesson 206) |
| Keycloak | User **Enabled** = false |
| Portal / Gitea | Login attempt **fails** |

| Workflow step | What it does |
| --- | --- |
| `Log Leaver` | Script log — proves the case ran (`MNB Leaver workflow for …`) |
| `Refresh` | `call:refreshIdentity` with `provision=true`, `disable=true` |

- **Wrong way:** Marking inactive in IIQ Debug without HCM termination — no source-of-truth trail, and the leaver trigger may never fire.
- **Wrong way:** Terminating Helen / Priya — shared personas break later certs and SSO lessons.
- **Wrong way:** Declaring victory after LDAP disable while Portal still works — Keycloak is a separate store.
- **Wrong way:** Aggregating Workday without **Process events** — cube flips inactive, leaver workflow never starts.

## Intent

- Create `MNB-Workflow-Leaver` and `MNB-IdentityTrigger-Leaver` if missing.
- Use a disposable identity only; prove Portal login works **before** terminate.
- Terminate via live HCM; fire the leaver path (auto or manual fallback).
- Prove disable on ≥1 directory **and** failed Portal login.
- Record Mailpit termination mail presence or honest gap (welcome/term mail often arrives in Lesson 232).

## Before you start

- [ ] Disposable cube with LDAP + Portal access (reuse `lab.joiner1` from 217, or create `lab.leaver1`)
- [ ] Confirm Portal login works **before** terminate (baseline)
- [ ] Lesson 216 birthright IdP pack understood (`MNB-Keycloak-IdP` / `MNB-IT-IdP-Portal`)
- [ ] HCM + Keycloak + Portal reachable
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/219
```

## Do this

### Task 1 — Create `MNB-Workflow-Leaver` (if missing)

1. **Debug** → Object Browser → type **`Workflow`** → search `MNB-Workflow-Leaver`  
   Or **Setup → Business Processes**
2. If it exists with steps `Log Leaver` → `Refresh`, skip to Task 2

#### Option A — Import shipped XML (preferred)

1. Open `config/Workflow/MNB-Workflow-Leaver.xml`
2. **Debug → Import** → paste → **Import**
3. Confirm name `MNB-Workflow-Leaver`, type `IdentityLifecycle`

- **Expect:** Business Processes lists Log Leaver then Refresh (`provision` + `disable`).

#### Option B — Build in Business Processes

| Step | Kind | Key args / script |
| --- | --- | --- |
| `Start` | Start | → `Log Leaver` |
| `Log Leaver` | Script | log line below |
| `Refresh` | `call:refreshIdentity` | `identity=ref:identityName`, `provision=true`, `disable=true` |
| `Stop` | Stop | — |

```java
import org.apache.commons.logging.LogFactory;
LogFactory.getLog("meridian.lcm").warn("MNB Leaver workflow for " + identityName);
```

> **Watch out:** Save the workflow **before** wiring the IdentityTrigger.

### Task 2 — Create `MNB-IdentityTrigger-Leaver` (if missing)

1. Debug → **`IdentityTrigger`** → search `MNB-IdentityTrigger-Leaver`
2. If missing: Import `config/IdentityTrigger/MNB-IdentityTrigger-Leaver.xml`, **or** create:
   - Type **`attributeChange`**
   - Handler `sailpoint.api.WorkflowTriggerHandler`
   - Workflow name exactly **`MNB-Workflow-Leaver`**
   - Not disabled; owner `spadmin`
3. Confirm the workflow field is exact (not a typo’d name)

- **Why:** aggregation updates the cube; the trigger starts LCM.
- **Expect:** enabled trigger bound to `MNB-Workflow-Leaver`.

> **Tip:** If your trigger has an attribute filter, make sure it matches what Workday promotes for termination (`inactive`, `status`, `active`, etc.). A filter that never matches = silent non-fire → use Task 8 manual launch.

### Task 3 — Ensure a disposable identity exists

Reuse Lesson 217’s joiner, or create fresh:

```bash
./tools/lab/enterprise/hcm-scenario.sh joiner lab.leaver1 Lab Leaver \
  lab.leaver1@meridiannb.com 'Bank Operations'
```

Then aggregate / refresh with Process events / birthright / Portal steps as in Lesson 217 until Portal login works.

- **Why:** shared personas break later certs and SSO lessons — never terminate Helen.
- **Expect:** Portal login succeeds for the disposable user.

### Task 4 — Capture the “before” baseline

Sign into Employee Portal as the disposable user: [http://localhost:8092/](http://localhost:8092/)

Screenshot under evidence (no passwords).

- **Why:** without a working baseline, a failed post-terminate login proves nothing.
- **Expect:** successful login proof saved.

### Task 5 — Terminate in live HCM

```bash
./tools/lab/enterprise/hcm-scenario.sh leaver lab.leaver1
```

(`PATCH` sets `active: false`, `status: Terminated`.)

- **Why:** leavers must start at the authoritative source — same as production HR terminate.
- **Expect:** script success.

### Task 6 — Confirm the source

```bash
curl -s http://localhost:8091/hcm/v1/workers/lab.leaver1 \
  | python3 -m json.tool | grep -E 'active|status|userName'
```

- **Why:** wrong worker id terminates the wrong person.
- **Expect:** `active: false`, status Terminated.

### Task 7 — Aggregate Workday, then Refresh with **Process events**

Lifecycle Events do **not** fire on aggregation alone.

1. **Account Aggregation** on `MNB-Workday`
2. **Setup → Tasks → Refresh Identity Cube**
3. Enable **Process events** (`processTriggers=true`) — plus promote attributes
4. Optionally filter to `lab.leaver1` → **Save** → **Run Now**

- **Why:** cube inactive/status flip is the `attributeChange` the Leaver trigger watches — but only if Process events is on.
- **Expect:** cube shows inactive / Terminated **and** a leaver workflow launch (Task 8).

### Task 8 — Confirm leaver workflow (or manual fallback)

```bash
docker logs mnb-identityiq 2>&1 | grep -i "MNB Leaver workflow"
```

Also check Task Results / Monitor for `MNB-Workflow-Leaver`.

If missing:

1. **Setup → Business Processes → MNB-Workflow-Leaver** → Run / Launch  
2. `identityName` = `lab.leaver1`

- **Why:** auto-fire is preferred; manual launch still completes the disable plan.
- **Expect:** workflow ran; disable provisioning attempted.

### Task 9 — Directory proof

```bash
ldapsearch -x -H ldap://localhost:389 \
  -b ou=people,dc=meridiannb,dc=com \
  -D cn=admin,dc=meridiannb,dc=com -w admin \
  '(uid=lab.leaver1)'
```

Look for a disabled flag / account status — **or** attempt pass-through login (Lesson 206) as that user and confirm it fails.

- **Why:** IIQ “disabled” without a directory change leaves residual bind access.
- **Expect:** observable disable or failed directory login.

### Task 10 — Keycloak / IdP disable

Keycloak Admin → realm `meridian` → Users → disposable user — confirm **Enabled** = false.

- If birthright IdP provisioning ran, disable may already be there from the plan.
- If not, disable manually and note “IdP hop not in disable plan” as a finding.

- **Why:** Portal authenticates against Keycloak — LDAP disable alone does not kill SSO.
- **Expect:** IdP cannot authenticate; note auto vs manual.

### Task 11 — Portal login must fail

Attempt Employee Portal login as the leaver.

- **Why:** this is the acceptance test — Terminated badge without failed SSO is incomplete.
- **Expect:** **login fails**. If it succeeds, trace HCM → cube → plan → target until you find the open hop — that gap *is* the lesson outcome.

### Task 12 — Mailpit termination notice

Check [http://localhost:8025](http://localhost:8025).

- **Why:** termination mail may be missing from the workflow XML — honest gap, not an SMTP bug (Lesson 232 often owns templates).
- **Expect:** mail present, **or** note “leaver workflow has no email step.”

## If it fails

| Symptom | Fix |
| --- | --- |
| Trigger never fires | Process events off; or watched attribute/filter doesn’t match — name the attribute or use manual launch |
| Plan computes, no target disable | Refresh without effective `provision`, or app lacks disable features |
| LDAP disabled, Portal still works | Keycloak is separate — disable IdP or ensure `MNB-Keycloak-IdP` is on the disable plan |
| Wrong identity terminated | `hcm-scenario.sh leaver` arg must match the disposable user, not Helen/Priya |
| No mail | Known limitation if workflow has no email step — don’t debug SMTP for that gap alone |
| Workflow / trigger missing | Complete Tasks 1–2 — same wipe gap as Lesson 217 joiner objects |

## You are done when

- [ ] Disposable identity disabled on at least one directory (raw proof)
- [ ] Portal login as the leaver **fails**
- [ ] You can name any remaining hop where access still works
- [ ] Workflow + trigger exist for the next leaver (not a one-off Debug disable)

## Control note

- **Control:** Leaver / rapid offboarding (terminate → disable all surfaces)
- **Owners:** HR Ops + IAM Ops + IdP owner
- **SLA (lab):** same session; production often same-day / hours for privileged
- **Evidence:** `~/iiq-lab-evidence/sandbox/219/` — HCM PATCH proof, ldap/IdP disable, failed Portal attempt

## Quick check

1. Does LDAP disable alone kill Portal SSO? → **No** — Keycloak is a separate store unless provisioned  
2. What IIQ flags drive disable plans? → `disable=true` with `provision=true` on refresh  
3. Why use a disposable identity? → Shared personas break later certs/SSO lessons  
4. What Refresh option must be on for the leaver trigger to fire? → **Process events**  

## Feedback

Could you name every store that must be disabled for SSO to fail? If Portal still worked after LDAP disable, that multi-store gap is the finding — write it down before moving on.

## Navigate

- Previous: [Lesson 218](218-mover-lcm-live.md)
- Next: [Lesson 220](220-contractor-loa-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
