# Lesson 246 — Toolkit / MCP Operator APIs

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~60 minutes  
**Prereq:** Lesson 201  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 97–100

> **Why:** APIs are how you automate what you just clicked. Automation must hit the same guardrails a human clicking through the UI would — a feature flag that doesn't actually deny a call is a control gap.

## What this is

Everything in Lessons 201–245 was done by hand in the IIQ UI. `pluginsrc/mnb-iam-toolkit` exposes those operations as REST — `mnbToolkit/ping`, `mnbToolkit/enterprise/status`, `mnbToolkit/enterprise/jml` — plus the larger `agent/*` surface behind the `identityiq` MCP server (`create_access_request`, `make_certification_decision`, `run_jml_event`, and 60+ more per `docs/api/MCP-TOOLS.md`). You exercise the plugin's REST endpoints directly, then the equivalent through MCP, and prove a feature-flag toggle actually denies a call.

## Know these

| Layer | Entry point |
| --- | --- |
| Plugin REST | `/plugin/rest/mnbToolkit/...` (Basic auth, `spadmin`) |
| MCP tools | `create_access_request`, `make_certification_decision`, `run_jml_event`, etc. |
| Feature flag | Per-tool gate, e.g. `mutateGovernanceEnabled` |

**Wrong way:** Calling MCP **resources** for live IIQ data — per the `iiq-mcp-first` rule, resources are empty by design; always call **tools**.

## Intent

- Confirm the toolkit plugin is alive with a REST ping.
- Pull enterprise pack status and confirm your live apps/workflows show as present.
- Pull one identity's JML snapshot via the API.
- Use the MCP tool layer to list work items and run a safe aggregation.
- Disable a plugin feature flag and confirm the corresponding call is denied, not silently ignored.

## Before you start

- [ ] IIQ up with `mnb_iam_toolkit` plugin installed
- [ ] `spadmin:admin` Basic auth working
- [ ] MCP client configured per `docs/api/MCP-TOOLS.md`
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/246`

## Do this

1. `curl -s -u spadmin:admin http://localhost:8080/identityiq/plugin/rest/mnbToolkit/ping | python3 -m json.tool`.  
   **Expect:** Success — if this fails, nothing downstream works; it's independent of MCP.
2. `curl -s -u spadmin:admin http://localhost:8080/identityiq/plugin/rest/mnbToolkit/enterprise/status | python3 -m json.tool`.  
   **Expect:** `applications` lists `MNB-Workday`, `MNB-ActiveDirectory-Live`, `MNB-Okta`, `MNB-CoreBanking`, `MNB-Salesforce-CRM-Live`, `MNB-ServiceNow`, `MNB-OpenLDAP` `present:true`; `workflows` lists `MNB-Workflow-Joiner`, `MNB-Workflow-Leaver`, `MNB-Workflow-Access-Approval` similarly present. Any `present:false` means go fix that lesson first.
3. `curl -s -u spadmin:admin "http://localhost:8080/identityiq/plugin/rest/mnbToolkit/enterprise/jml?identity=helen.ross" | python3 -m json.tool`.  
   **Expect:** `found:true`, her `manager`, `inactive:false`, non-zero `linkCount` matching her correlated apps.
4. Via your MCP client, call `list_agent_work_items`.  
   **Expect:** Returns real pending work items matching **My Work Items** for the same identity.
5. Call `trigger_aggregation` (or `run_task_now`) against a low-risk app, e.g. `MNB-OpenLDAP`.  
   **Expect:** Task result matches what a UI-triggered aggregation would show in **Monitor → Tasks**.
6. Use one governance write tool — `make_certification_decision` or `create_access_request` — against a small, disposable target.  
   **Expect:** Write path succeeds through the API exactly as it would through the UI.
7. Disable one relevant plugin feature flag (e.g. `mutateGovernanceEnabled=false` under **Setup → Plugins → mnb_iam_toolkit → Settings**, or `update_plugin_settings`), repeat step 6.  
   **Expect:** Denied with an explicit error, not silently accepted and ignored.
8. Re-enable the flag, repeat step 6.  
   **Expect:** Succeeds again.
9. Save the ping, status, and jml JSON responses plus the before/after flag-toggle proof under `~/iiq-lab-evidence/sandbox/246/`.

## If it fails

- **401/403 on plugin REST calls** — use Basic auth with a capability that has `MNBToolkitAgent`'s required right, or `spadmin`.
- **`present:false` for an app/workflow you built earlier** — re-check that lesson's object was saved under its exact name; the status endpoint does an exact `getObjectByName` lookup.
- **MCP tools return empty where resources would** — expected per the `iiq-mcp-first` rule; always call tools.
- **Flag toggle has no effect** — confirm you disabled the flag that actually gates that specific tool per `docs/api/MCP-TOOLS.md`'s table.

## You are done when

The status endpoint lists your live apps/workflows as present, a JML snapshot resolves for a real identity, an MCP write tool succeeds, and the same tool is denied once its feature flag is off.

## Control note

- **Control:** Automation-layer parity with UI guardrails (feature-flag enforcement).  
- **Owner:** IAM Engineering / Platform.  
- **SLA (lab):** Gated write tools deny explicitly, never silently no-op.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/246/` — ping/status/jml JSON, flag toggle before/after.

## Quick check

1. Should you call MCP resources or tools for live IIQ data? → Tools — resources are empty by design.  
2. What does a denied (flag-off) write call look like? → An explicit error, not a silent no-op.  
3. Which endpoint is the plugin's own liveness check? → `mnbToolkit/ping`.

## Navigate

- Previous: Lesson 245
- Next: Lesson 247
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
