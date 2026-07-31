# Meridian National Bank — IAM story bank (25)

Seed backlog for Claude Code `/intake` → `/work`. Import CSV into Jira **To Do**, or use fixtures offline.

Corporate domain: `@meridiannb.com` · Personas: `MNB000xx` · Data: `lab-data/`

| # | Key | Type | Title |
| --- | --- | --- | --- |
| 1 | MNB-101 | app-onboarding | Onboard WirePortal delimited feed for Bengaluru wire initiators |
| 2 | MNB-102 | app-onboarding | Salesforce-CRM correlation on email for CRM reps |
| 3 | MNB-103 | app-onboarding | ActiveDirectory health-check + NCD for high-risk OUs |
| 4 | MNB-104 | app-onboarding | Fix SAP-Finance aggregation schedule after CST cutoff |
| 5 | MNB-105 | identity-admin | Unlock Meera Torres (MNB00012) after AD lock cascade |
| 6 | MNB-106 | identity-admin | Reset + expire password for contractor offboarding |
| 7 | MNB-107 | identity-admin | Assign IIQ Administrator capability to secondary SOC analyst (CAB) |
| 8 | MNB-108 | identity-admin | Disable terminated Anita Ross (MNB00010) and verify leaver accounts |
| 9 | MNB-109 | jml-lifecycle | Joiner: ingest HR scenario hire + Identity Refresh |
| 10 | MNB-110 | jml-lifecycle | Mover: Rachel Evans (MNB00005) dept/role birthright deltas |
| 11 | MNB-111 | jml-lifecycle | Same-day leaver: revoke WirePortal + AWS |
| 12 | MNB-112 | jml-lifecycle | Rehire: reactivate previously inactive identity |
| 13 | MNB-113 | access-request | Retail CSR → InternetBanking entitlement (manager approval) |
| 14 | MNB-114 | access-request | Remove orphaned AWS admin after team transfer |
| 15 | MNB-115 | policy-sod | SoD exception: Finance GL + Wire initiator for Deepa Nair delegate |
| 16 | MNB-116 | access-request | Batch access request for new branch cohort (5 users) |
| 17 | MNB-117 | certification | Launch manager certification for Retail Banking population |
| 18 | MNB-118 | certification | Certify + sign-off Christopher Hayes ITP campaign items |
| 19 | MNB-119 | governance-admin | Create population Kathmandu Hub risk reviewers |
| 20 | MNB-120 | governance-admin | Add Chloe Adhikari (MNB00009) to IAM incident responders workgroup |
| 21 | MNB-121 | task-ops | Run Identity Refresh now; triage last TaskResult failure |
| 22 | MNB-122 | automation-rule-workflow | Export CoreBanking Application XML → SSD MNB-Application |
| 23 | MNB-123 | plugin-work | Install/enable study plugin zip; verify toolkit_ping |
| 24 | MNB-124 | automation-rule-workflow | Author SSD Rule for HR userId normalization (no live rule edit) |
| 25 | MNB-125 | task-ops | Schedule daily open-SoD report to Helen Ross |

---

## Stories (acceptance + MCP + lab assets)

### MNB-101 — Onboard WirePortal delimited feed

**Type:** `app-onboarding`  
**Requester:** Rachel Evans (Payments Ops)  
**Acceptance:** Application `MNB-WirePortal` exists; delimiter/header set; account aggregation task completable for `lab-data/apps/MNB-WirePortal*.csv` (or WirePortal extract).  
**MCP:** `create_application`, `update_application_config`, `trigger_aggregation`, `get_task_result`  
**DoR:** file path, delimiter, correlation attr (`userId`/`email`)

### MNB-102 — Salesforce-CRM correlation on email

**Type:** `app-onboarding`  
**Acceptance:** CRM app correlates identities on `email`; sample accounts from `lab-data/apps/MNB-Salesforce-CRM.csv` link to HR users.  
**MCP:** `get_application_config`, `update_application_config`, `trigger_aggregation`, `search_identities`  
**DoR:** app name, correlation attribute

### MNB-103 — AD health + NCD

**Type:** `app-onboarding` / hybrid investigation  
**Acceptance:** `test_application_connection` / health OK for ActiveDirectory; NCD enabled for agreed high-risk OUs.  
**MCP:** `get_application_health`, `test_application_connection`, `configure_native_change_detection`  
**Lab:** `lab-data/apps/MNB-ActiveDirectory.csv`

### MNB-104 — SAP-Finance schedule after CST

**Type:** `app-onboarding` / `task-ops`  
**Acceptance:** Aggregation schedule for SAP-Finance runs after 18:00 CST; no overlapping Identity Refresh clash documented.  
**MCP:** `list_agent_schedules`, `update_task_schedule`, `list_recent_task_failures`  
**Lab:** `lab-data/apps/MNB-SAP-Finance.csv`

### MNB-105 — Unlock Meera Torres

**Type:** `identity-admin`  
**Persona:** MNB00012 / meera.torres@meridiannb.com  
**Acceptance:** IIQ identity unlockable; identity searchable; AD cascade noted in evidence.  
**MCP:** `search_identities`, `unlock_iiq_identity`, `get_identity_accounts`  
**Fixture:** `jira-stories/fixtures/MNB-105.json`

### MNB-106 — Contractor password reset + expire

**Type:** `identity-admin`  
**Acceptance:** Password set/reset and expire flags applied for named contractor; confirm no lingering interactive sessions needed in lab.  
**MCP:** `set_identity_password` / `reset_password`, `expire_password`, `get_password_policy`

### MNB-107 — Capability for secondary SOC analyst

**Type:** `identity-admin`  
**Persona:** Chloe Adhikari (MNB00009) or designated backup  
**Acceptance:** `assign_identity_capability` grants agreed capability; CAB ref in comment.  
**MCP:** `list_capabilities`, `assign_identity_capability`, `get_identity_capabilities`  
**Note:** never use excluded `grant_capability`

### MNB-108 — Disable Anita Ross leaver

**Type:** `identity-admin` / `jml-lifecycle`  
**Persona:** MNB00010 (Terminated in HR extract)  
**Acceptance:** Identity disabled; linked accounts disabled/verified; audit event present if available.  
**MCP:** `disable_identity`, `get_identity_accounts`, `search_audit_events`  
**Lab:** HR row for Anita Ross

### MNB-109 — Joiner HR ingest

**Type:** `jml-lifecycle`  
**Acceptance:** New hire from `lab-data/scenarios/joiner/` appears after HR agg + Identity Refresh.  
**MCP:** `trigger_aggregation`, `run_task_now`, `search_identities`

### MNB-110 — Mover Rachel Evans

**Type:** `jml-lifecycle`  
**Persona:** MNB00005  
**Acceptance:** Dept/title deltas from mover scenario reflected after refresh; birthright entitlements checked.  
**MCP:** `update_identity_attribute` (if used) / agg + refresh; `get_identity_access`  
**Lab:** `lab-data/scenarios/mover/`

### MNB-111 — Same-day leaver Wire + AWS

**Type:** `jml-lifecycle`  
**Acceptance:** Target leaver inactive; WirePortal + AWS-Cloud access removed or removal requested.  
**MCP:** `disable_identity`, `create_removal_request`, `get_identity_access`  
**Lab:** `lab-data/scenarios/leaver/`, `MNB-AWS-Cloud.csv`, WirePortal extracts

### MNB-112 — Rehire reactivation

**Type:** `jml-lifecycle`  
**Acceptance:** Previously inactive identity re-enabled; HR active flag aligned; accounts re-evaluated.  
**MCP:** `enable_identity`, `search_identities`, `run_task_now`

### MNB-113 — InternetBanking access request

**Type:** `access-request`  
**Persona:** Sofia Andersson (MNB00014) CSR → InternetBanking entitlement  
**Acceptance:** Access request created; pending manager Emily Bennett (or lab manager).  
**MCP:** `get_requestable_items`, `create_access_request`, `get_access_request_status`  
**Lab:** `lab-data/apps/MNB-InternetBanking.csv`

### MNB-114 — Remove orphaned AWS admin

**Type:** `access-request`  
**Acceptance:** Removal request for leftover AWS admin entitlement after transfer.  
**MCP:** `create_removal_request`, `get_identity_access`, `get_access_request_status`

### MNB-115 — SoD exception Finance + Wire

**Type:** `policy-sod`  
**Requester:** Deepa Nair delegate  
**Acceptance:** Open SoD documented; time-boxed exception created with business justification.  
**MCP:** `list_open_sod_violations`, `create_policy_violation_exception`

### MNB-116 — Batch branch cohort

**Type:** `access-request`  
**Acceptance:** Batch of 5 retail branch users receives agreed birthright bundle.  
**MCP:** `submit_batch_request`, `get_batch_request_status`  
**DoR:** CSV of userIds + entitlements

### MNB-117 — Retail Banking manager cert

**Type:** `certification`  
**Acceptance:** Campaign launched for Retail Banking population; managers notified / certs visible.  
**MCP:** `list_populations`, `launch_certification_campaign`, `list_certifications`

### MNB-118 — Hayes ITP certify + sign-off

**Type:** `certification`  
**Persona:** Christopher Hayes (MNB00002)  
**Acceptance:** Sample decisions recorded; sign-off completed for assigned cert.  
**MCP:** `make_certification_decision`, `sign_off_certification`, `get_certification_progress`

### MNB-119 — Kathmandu Hub population

**Type:** `governance-admin`  
**Acceptance:** Population “Kathmandu Hub risk reviewers” created; preview membership non-empty for hub identities.  
**MCP:** `create_population`, `preview_population_membership`  
**Lab:** location Kathmandu / Anthony Powell org

### MNB-120 — Workgroup membership Chloe

**Type:** `governance-admin`  
**Persona:** MNB00009  
**Acceptance:** Chloe added to IAM incident responders workgroup.  
**MCP:** `list_workgroups`, `manage_workgroup_members`

### MNB-121 — Identity Refresh triage

**Type:** `task-ops`  
**Acceptance:** Refresh run via toolkit; prior failure explained from TaskResult; evidence saved.  
**MCP:** `run_task_now`, `get_task_result`, `list_recent_task_failures`  
**Fixture:** `jira-stories/fixtures/MNB-121.json`

### MNB-122 — Export CoreBanking to SSD

**Type:** `automation-rule-workflow` / HYBRID  
**Acceptance:** Application XML exported; committed path `config/Application/MNB-Application-CoreBanking.xml` (or agreed name) with tokens.  
**MCP:** `export_sailpoint_object`  
**SSD:** `config/Application/` + later `importdynamic`

### MNB-123 — Study plugin install

**Type:** `plugin-work`  
**Acceptance:** Plugin listed/enabled; `toolkit_ping` returns ok.  
**MCP:** `install_plugin_zip` / `set_plugin_state`, `list_iiq_plugins`, `toolkit_ping`  
**Fixture:** `jira-stories/fixtures/MNB-123.json`

### MNB-124 — HR userId normalization Rule (SSD)

**Type:** `automation-rule-workflow`  
**Acceptance:** Rule XML under `config/Rule/MNB-Rule-HrUserIdNormalize.xml`; **no** `update_rule_source`. Import on confirm.  
**MCP:** `list_rules`, `get_rule_source` (read), `import_sailpoint_object` (optional)

### MNB-125 — Daily SoD report schedule

**Type:** `task-ops`  
**Owner:** Helen Ross (MNB00001)  
**Acceptance:** Report definition runnable; schedule documents daily delivery intent to Helen.  
**MCP:** `list_report_definitions`, `run_report`, `schedule_report` / `update_task_schedule`

---

## Import tips

1. Use `jira-stories/MNB-IAM-backlog.csv` (Jira CSV import or bulk create).
2. Put new issues in **To Do**.
3. Offline: `python3 scripts/jira/todo_poll.py --all --fixture jira-stories/fixtures`
4. Start with `/work MNB-105` (simple unlock) or `/work MNB-123` (toolkit ping).
