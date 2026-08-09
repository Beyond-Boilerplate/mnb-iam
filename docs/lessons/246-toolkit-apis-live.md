# Lesson 246 — Toolkit / MCP Operator APIs

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~85 minutes  
**Prereq:** Lessons 201, 221–222, 245  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 97–100

> **Why:** APIs are how you automate what you just clicked. Automation must hit the same guardrails a human would — a feature flag that does not actually deny a call is a control gap.

## What this is

Lessons 201–245 were mostly UI clicks. The Meridian plugin **`mnb_iam_toolkit`** (display name **Meridian Custom APIs**) exposes the same estate over REST under `/identityiq/plugin/rest/mnbToolkit/…`, and the `identityiq` MCP server wraps those endpoints as tools (`docs/api/MCP-TOOLS.md`).

| Layer | Entry | Auth / gate |
| --- | --- | --- |
| Plugin REST | `http://localhost:8080/identityiq/plugin/rest/mnbToolkit/...` | Basic `spadmin:admin` + SPRights |
| Feature flags | Plugin Settings | `agentApiEnabled`, `mutateGovernanceEnabled`, `taskRunEnabled`, … |
| MCP tools | Cursor / Teller MCP `identityiq` | Same flags; call **tools**, not empty resources |

Nothing assumes the plugin is healthy. You will:

1. Verify-or-install the plugin  
2. Enable settings with concrete curls  
3. Hit `ping`, `enterprise/status`, `enterprise/jml`  
4. List work items + run a safe aggregation  
5. Submit one governance write, then **deny** it by flipping `mutateGovernanceEnabled`  
6. Re-enable and save JSON evidence  

> **Watch out:** MCP **resources** for IIQ are empty by design. Always call **tools** (or raw REST). Never “debug” empty resources as a plugin outage.

## Know these

```text
Confirm/install mnb_iam_toolkit
  → enable-settings (agentApiEnabled + mutateGovernance + taskRun)
  → GET ping → GET enterprise/status → GET enterprise/jml?identity=helen.ross
  → GET agent/workItems (+ MCP list_agent_work_items if configured)
  → POST tasks/run Account Aggregation (allowlisted) on MNB-OpenLDAP
  → POST agent/access/grant for disposable lab.toolkit1 (flag ON)
  → Set mutateGovernanceEnabled=false → same grant → explicit deny
  → Re-enable flag → evidence JSON pack
```

| Term | Plain English | Meridian example |
| --- | --- | --- |
| **`mnb_iam_toolkit`** | Plugin id (underscores only) | Install name in Plugins UI |
| **`MNBToolkitAccess` / `MNBToolkitAgent`** | Rights for ping vs agent APIs | Granted to `spadmin` after install |
| **`agentApiEnabled`** | Master switch for `/mnbToolkit/agent/*` | Must be `true` or every agent call 403s |
| **`mutateGovernanceEnabled`** | Kill switch for writes (access/cert/SoD/…) | Deny must be loud |
| **`taskRunEnabled` + allowlist** | Who may launch tasks via API | Patterns like `Account Aggregation*` |
| **UIAPI gap id** | Register row in `docs/api/UI-VS-API-GAPS.md` | UIAPI-03 = access request |

- **Wrong way:** Calling MCP resources and declaring IIQ down.  
- **Wrong way:** A flag flip that still returns HTTP 200 with an empty success body.  
- **Wrong way:** Running destructive leaver/joiner APIs against Helen / Priya / Marcus.  
- **Wrong way:** Skipping plugin install because “enterprise stack usually has it.”

## Intent

- Prove plugin liveness independent of MCP.  
- Prove enterprise pack presence (`applications` / `workflows` flags).  
- Prove JML snapshot matches a real cube.  
- Prove a write path succeeds, then is **explicitly denied** when its flag is off.

## Before you start

Complete every checkbox. Do not skip into Task 1 until these are true.

- [ ] IIQ up: [http://localhost:8080/identityiq](http://localhost:8080/identityiq) — `spadmin` / `admin`
- [ ] From repo root, plugin sources/helpers exist:

```bash
ls pluginsrc/mnb-iam-toolkit/install.sh pluginsrc/mnb-iam-toolkit/enable-settings.sh
```

- [ ] Basic auth works against IIQ (any simple page or later ping)
- [ ] Optional: MCP client configured per [`docs/api/MCP-TOOLS.md`](../api/MCP-TOOLS.md) — REST alone is enough to finish
- [ ] Evidence dir:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/246
```

## Do this

### Task 1 — Verify-or-install `mnb_iam_toolkit`

1. As `spadmin`: **Gear → Plugins** (or **Setup → Plugins**)  
2. Look for **`mnb_iam_toolkit`** / **Meridian Custom APIs**  

**If installed:** note version ≥ **1.3.x** under evidence.

**If missing:**

```bash
cd /Users/alishaghatane/Documents/Sailpoint
./pluginsrc/mnb-iam-toolkit/ensure-plugin-zip.sh
./pluginsrc/mnb-iam-toolkit/install.sh
```

3. Refresh Plugins UI until the plugin shows **Installed** / enabled  
4. Confirm rights landed (Debug → Capability / Identity `spadmin` should include toolkit rights after install — or assign Capability that carries `MNBToolkitAgent` if ping returns 403 in Task 3)

- **Why:** every later curl is meaningless without the plugin WAR in IIQ.  
- **Expect:** plugin row visible and enabled.

### Task 2 — Enable plugin feature flags

Install resets settings to defaults (`false`). Turn the lab switches on:

```bash
cd /Users/alishaghatane/Documents/Sailpoint
./pluginsrc/mnb-iam-toolkit/enable-settings.sh
```

Or equivalent UI: **Plugins → Meridian Custom APIs → Settings** — set:

| Setting | Value |
| --- | --- |
| `agentApiEnabled` | `true` |
| `taskRunEnabled` | `true` |
| `mutateGovernanceEnabled` | `true` |
| `passwordResetEnabled` | `true` (optional for this lesson) |
| `advancedOpsEnabled` | `true` (optional; needed for settings API itself on some paths) |
| `allowedTaskNames` | `Account Aggregation*,Refresh Identity Cube*,Refresh*,Aggregate *,Identity Refresh*` |

Save settings JSON under evidence as `plugin-settings-on.json` (copy from script output or UI).

- **Why:** defaults deny agent APIs — “403 forever” is usually flags, not code.  
- **Expect:** settings show `true` for agent + mutate + taskRun.

### Task 3 — `GET` ping (liveness)

```bash
curl -sS -u 'spadmin:admin' \
  'http://localhost:8080/identityiq/plugin/rest/mnbToolkit/ping' \
  | tee ~/iiq-lab-evidence/sandbox/246/ping.json \
  | python3 -m json.tool
```

- **Why:** ping proves plugin REST + Basic auth before you debug MCP.  
- **Expect:** JSON with plugin/bank/status fields (not HTML login page, not 401/404).

If **401/403**: fix password or assign toolkit Capability/rights to `spadmin`, then retry.  
If **404**: plugin not installed (Task 1).

### Task 4 — `GET` enterprise status

```bash
curl -sS -u 'spadmin:admin' \
  'http://localhost:8080/identityiq/plugin/rest/mnbToolkit/enterprise/status' \
  | tee ~/iiq-lab-evidence/sandbox/246/enterprise-status.json \
  | python3 -m json.tool
```

Check `applications` and `workflows` arrays. For each row you care about, note `present: true|false`.

Minimum you should recognize from earlier lessons:

| Name | Kind |
| --- | --- |
| `MNB-Workday`, `MNB-CoreBanking`, `MNB-OpenLDAP` | applications |
| `MNB-Workflow-Joiner`, `MNB-Workflow-Leaver`, `MNB-Workflow-Access-Approval` | workflows |

- **Why:** status does exact `getObjectByName` — `present:false` means go fix that lesson’s object name, not the API.  
- **Expect:** core apps/workflows you built show `present: true`. Honest `false` with a fix note is OK for apps you skipped.

### Task 5 — `GET` JML snapshot for Helen

```bash
curl -sS -u 'spadmin:admin' \
  'http://localhost:8080/identityiq/plugin/rest/mnbToolkit/enterprise/jml?identity=helen.ross' \
  | tee ~/iiq-lab-evidence/sandbox/246/jml-helen.json \
  | python3 -m json.tool
```

Cross-check **Identities → Identity Warehouse → helen.ross**:

| API field | Must match UI |
| --- | --- |
| `found` | `true` |
| `inactive` | Helen not terminated |
| `manager` | Same manager name (or null both sides) |
| `linkCount` / `links[]` | Correlated applications |

- **Why:** automation that disagrees with Warehouse is worse than no automation.  
- **Expect:** `found:true` and link list plausible.

### Task 6 — List work items (REST + optional MCP)

REST:

```bash
curl -sS -u 'spadmin:admin' \
  'http://localhost:8080/identityiq/plugin/rest/mnbToolkit/agent/workItems' \
  | tee ~/iiq-lab-evidence/sandbox/246/workitems.json \
  | python3 -m json.tool | head -80
```

Optional MCP (if your client has `identityiq` tools): call **`list_agent_work_items`** (or the UIAPI-04 equivalent from `MCP-TOOLS.md`). Compare count/shape to **My Work Items** / Manage Work Items for the same filter.

- **Why:** read path proves agent APIs with `agentApiEnabled` before you test the mutate kill switch.  
- **Expect:** JSON envelope with items (may be empty list — empty is success if UI also empty).

### Task 7 — Run a safe aggregation via toolkit tasks API

```bash
curl -sS -u 'spadmin:admin' \
  -H 'Content-Type: application/json' \
  -d '{"taskName":"Account Aggregation","sync":false,"args":{"applications":"MNB-OpenLDAP"}}' \
  'http://localhost:8080/identityiq/plugin/rest/mnbToolkit/tasks/run' \
  | tee ~/iiq-lab-evidence/sandbox/246/task-run.json \
  | python3 -m json.tool
```

If your lab’s task is named differently (e.g. a dedicated `MNB-OpenLDAP` aggregation task), pass that exact **TaskDefinition** name instead — and ensure it matches `allowedTaskNames`.

1. **Monitor → Tasks → Task Results** (or Setup → Tasks results)  
2. Confirm a new result for the aggregation you launched  

Optional MCP: `trigger_aggregation` / `run_task_now` with the same task.

- **Why:** task launch is the other gated surface (`taskRunEnabled` + allowlist).  
- **Expect:** API accepted; Task Result appears (Complete or running).

> **Watch out:** If the API returns allowlist denial, widen `allowedTaskNames` (Task 2) to include your exact task name pattern.

### Task 8 — Create disposable subject for a write call

Do **not** grant random access to Helen/Priya/Marcus.

```bash
./tools/lab/enterprise/hcm-scenario.sh joiner lab.toolkit1 Lab Toolkit \
  lab.toolkit1@meridiannb.com 'Bank Operations'
```

1. Aggregate **`MNB-Workday`** → Refresh Identity Cube for `lab.toolkit1` (create cube)  
2. Confirm cube exists in Identity Warehouse  

- **Why:** API write tests leave IdentityRequests — keep shared personas clean.  
- **Expect:** `lab.toolkit1` cube present.

### Task 9 — Governance write with flag ON (`access/grant`)

Requires `mutateGovernanceEnabled=true` (Task 2). Use a **requestable** role you already have (e.g. `MNB-Bundle-Wire-Initiator` from 216/221). If missing, create/requestable-enable per Lesson 221 before continuing.

```bash
curl -sS -u 'spadmin:admin' \
  -H 'Content-Type: application/json' \
  -d '{
    "identityName": "lab.toolkit1",
    "accessName": "MNB-Bundle-Wire-Initiator",
    "accessType": "role",
    "justification": "Lesson 246 toolkit API drill — disposable",
    "workflowName": "MNB-Workflow-Access-Approval"
  }' \
  'http://localhost:8080/identityiq/plugin/rest/mnbToolkit/agent/access/grant' \
  | tee ~/iiq-lab-evidence/sandbox/246/access-grant-on.json \
  | python3 -m json.tool
```

If `MNB-Workflow-Access-Approval` is missing, omit `workflowName` (defaults to `LCM Provisioning`) or import the workflow from Lesson 222.

- **Why:** write path must succeed under the same LCM rules as UI Request Access.  
- **Expect:** success envelope / launched request — **not** silent empty 200 with no IdentityRequest.

Optional MCP: `create_access_request` / `grant_access` with the same identity + role.

Leave approvals unfinished if you like — the point is API acceptance. Cancel later as `spadmin` if you do not want a dangling WI.

### Task 10 — Flip `mutateGovernanceEnabled=false` and prove deny

UI: **Plugins → Meridian Custom APIs → Settings** → `mutateGovernanceEnabled` = **false** → Save  

Or API (needs advanced/settings access):

```bash
curl -sS -u 'spadmin:admin' \
  -H 'Content-Type: application/json' \
  -d '{"settings":{"mutateGovernanceEnabled":"false"}}' \
  'http://localhost:8080/identityiq/plugin/rest/mnbToolkit/agent/plugins/mnb_iam_toolkit/settings' \
  | tee ~/iiq-lab-evidence/sandbox/246/settings-mutate-off.json \
  | python3 -m json.tool
```

Retry the **same** grant curl; save as `access-grant-off.json`:

```bash
curl -sS -u 'spadmin:admin' \
  -H 'Content-Type: application/json' \
  -d '{
    "identityName": "lab.toolkit1",
    "accessName": "MNB-Bundle-Wire-Initiator",
    "accessType": "role",
    "justification": "Lesson 246 flag-off proof"
  }' \
  'http://localhost:8080/identityiq/plugin/rest/mnbToolkit/agent/access/grant' \
  | tee ~/iiq-lab-evidence/sandbox/246/access-grant-off.json \
  | python3 -m json.tool
```

- **Why:** kill switches that no-op are theater.  
- **Expect:** **explicit** error (HTTP 403 or JSON error mentioning mutate/governance/flag) — **not** another successful launch.

### Task 11 — Re-enable flag + pack evidence

```bash
cd /Users/alishaghatane/Documents/Sailpoint
./pluginsrc/mnb-iam-toolkit/enable-settings.sh
```

Confirm one more successful ping. Evidence folder should include:

- `ping.json`, `enterprise-status.json`, `jml-helen.json`  
- `workitems.json`, `task-run.json`  
- `access-grant-on.json`, `access-grant-off.json`, settings snippets  

- **Why:** leave the lab usable for Lessons 247–250.  
- **Expect:** mutate/agent flags on again; evidence complete.

## If it fails

| Symptom | Fix |
| --- | --- |
| 404 on `/mnbToolkit/ping` | Task 1 install; confirm plugin enabled |
| 401 Basic | `spadmin` / `admin` (Lesson 201); no SSO redirect in curl |
| 403 on agent/* with flags on | Missing `MNBToolkitAgent` right / Capability on caller |
| 403 mentioning flag / mutate | Expected in Task 10; unexpected in Task 9 → re-run enable-settings |
| `present:false` for an app | Object name mismatch — open Application Definition; fix spelling |
| Task run allowlist deny | Add exact task name pattern to `allowedTaskNames` |
| `access/grant` 400 workflow | Import `MNB-Workflow-Access-Approval` or use `LCM Provisioning` |
| MCP empty | You hit **resources** — call **tools** or use the curls above |
| Helen used for write | Stop — move write tests to `lab.toolkit1` |

## You are done when

- [ ] Plugin installed; flags enabled (and restored after the deny test)  
- [ ] `ping` + `enterprise/status` + `jml` JSON saved  
- [ ] Work items list + one task run proven  
- [ ] `access/grant` succeeded with mutate **on**  
- [ ] Same call **explicitly denied** with mutate **off**  
- [ ] Evidence under `~/iiq-lab-evidence/sandbox/246/`  

## Control note

- **Control:** Automation-layer parity with UI guardrails (feature-flag enforcement)  
- **Owner:** IAM Engineering / Platform  
- **SLA (lab):** Gated write tools deny explicitly — never silent no-op  
- **Evidence:** `~/iiq-lab-evidence/sandbox/246/`  
- **Out of scope:** OOTB IIQ SCIM/REST without the plugin (Lesson 247)

## Quick check

1. MCP resources or tools for live IIQ? → **Tools** (resources empty by design)  
2. Which endpoint is plugin liveness? → `GET /mnbToolkit/ping`  
3. Which flag gates access/cert writes? → `mutateGovernanceEnabled`  
4. What does a good deny look like? → Explicit 403/error JSON, not success  
5. Why `lab.toolkit1` for writes? → Keep Helen/Priya/Marcus clean for certs/SoD  

## Feedback

Could you reinstall the toolkit, enable flags, and prove ping → status → jml → grant-on → grant-off deny without this page?

If something failed, note the **task number**, HTTP status, and whether flags were on or off.

## Navigate

- Previous: [Lesson 245](245-workgroups-scopes-live.md)
- Next: [Lesson 247](247-iiq-rest-scim-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md) · API map: [MCP-TOOLS.md](../api/MCP-TOOLS.md)
