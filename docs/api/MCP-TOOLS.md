# MCP tool map — Meridian Custom APIs

Maps **UIAPI** gaps → MCP tools → OpenAPI ops in
[`openapi/openapi-meridian-agent.yaml`](openapi/openapi-meridian-agent.yaml).

**IIQ flags** (plugin settings): `agentApiEnabled`, `mutateGovernanceEnabled`, `passwordResetEnabled`, `advancedOpsEnabled`, `taskRunEnabled` + allowlist.

**MCP phases** (`IIQ_MCP_ENABLED_PHASES`): use `1,2,3,4` to unlock Custom API write tools.

## Gap → tool

| Gap | MCP tool(s) | Custom API |
| --- | --- | --- |
| META | `list_uiapi_gaps` | `GET /agent/gaps` |
| UIAPI-01/02 | `run_task_now`, `trigger_aggregation`, **`list_allowed_toolkit_tasks`** | `/mnbToolkit/tasks/*` |
| UIAPI-03 | `create_access_request`, **`grant_access`**, **`revoke_access`**, … | `/agent/accessRequests`, `/agent/access/grant`, `/agent/access/revoke` |
| UIAPI-04 | `complete_work_item`, `list_agent_work_items`, `get_agent_work_item` | `/agent/workItems/*` |
| UIAPI-05 | `make_certification_decision`, `sign_off_certification` | `/agent/certifications/*` |
| UIAPI-06 | `count_open_sod_violations`, `list_open_sod_violations`, `create_policy_violation_exception` | `/agent/sod/*` |
| UIAPI-07 | **`create_application`**, **`onboard_application`** | `/agent/applications/wizard` (+ test + aggregate composite) — clones ConnectorRegistry template; DelimitedFile needs `file`, `delimiter`, `hasHeader`; OpenLDAP needs `host`, `port`, `user`, `password`, `searchDN` |
| UIAPI-08 | `get_application_config`, `update_application_config` | `/agent/applications/{name}/config` |
| UIAPI-09 | `list_populations`, `create_population`, **`delete_population`**, … | `/agent/populations` |
| UIAPI-10 | **`list_workgroups`**, **`manage_workgroup_members`** | `/agent/workgroups/*` |
| UIAPI-11 | **`assign_identity_capability`**, **`list_agent_capabilities`** (not excluded `grant_capability`) | `/agent/identities/.../capabilities`, `/agent/capabilities` |
| UIAPI-12 | `set_identity_password`, `reset_password`, **`unlock_iiq_identity`** | `/agent/identities/.../password` |
| UIAPI-13 | `list_agent_schedules`, `update_task_schedule` | `/agent/schedules` |
| UIAPI-14 | `run_report`, `list_report_definitions` | `/agent/reports/run` |
| UIAPI-15 | **`list_forms`**, **`get_form`** | `/agent/forms` |
| UIAPI-16 | **`list_quicklinks`** | `/agent/quicklinks` |
| UIAPI-17 | **`list_email_templates`**, **`get_email_template`** | `/agent/emailTemplates` |
| UIAPI-18 | `search_audit_events` | `/agent/audit/events` |
| UIAPI-19 | `submit_batch_request` | `/agent/batchRequests` |
| UIAPI-20 | **`get_access_history_status`** | `/agent/accessHistory/status` |
| UIAPI-21 | **`test_application_connection`**, `get_application_health` | `/agent/connectors/testConnection` |
| UIAPI-22 | **`configure_native_change_detection`** | `/agent/applications/.../nativeChangeDetection` |
| UIAPI-23 | **`list_iiq_plugins`**, **`set_plugin_state`**, **`install_plugin_zip`**, **`update_plugin_settings`** | `/agent/plugins*` |
| UIAPI-24 | `get_system_config`, **`update_system_config`** | `/agent/system/config` |
| UIAPI-25 | **`export_sailpoint_object`**, **`import_sailpoint_object`**, **`delete_sailpoint_object`** | `/agent/objects/*` |
| UIAPI-26 | **`get_study_plugin_catalog`** | `/agent/study/catalog` |
| UIAPI-27 | **`toolkit_ping`** | `GET /mnbToolkit/ping` |
| UIAPI-28 | **`list_managed_entitlements`**, **`upsert_entitlement`**, `promote_entitlements` | `/agent/entitlements*` |
| UIAPI-29 | **`list_agent_roles`**, `create_role`, `attach_role_profile`, **`delete_role`** | `/agent/roles*` |
| UIAPI-30 | **`run_jml_event`** | `/agent/jml/{event}` |
| UIAPI-31 | **`create_certification_campaign`**, `launch_certification_campaign` | `/agent/certifications/campaigns` |
| UIAPI-32 | **`create_sod_policy`** | `/agent/policies/sod` |
| UIAPI-33 | **`reset_target_password`** | `/agent/applications/{app}/accounts/{id}/password` |
| UIAPI-34 | **`download_report_result`** | `/agent/reports/{id}/download` |
| UIAPI-35 | **`get_executive_digest`** | `/agent/executive/digest` |
| UIAPI-36 | **`execute_batch_request`** | `/agent/batchRequests/{id}/execute` |
| UIAPI-37 | **`correlate_account`** | `/agent/accounts/correlate` |
| UIAPI-38 | **`preview_access_request`** | `/agent/accessRequests/preview` |
| UIAPI-39 | **`mine_business_roles`** | `/agent/roles/mine` |
| UIAPI-40 | **`classify_entitlements`** | `/agent/entitlements/classify` |
| UIAPI-41 | **`trigger_group_aggregation`** | `/agent/connectors/aggregate/groups` |
| UIAPI-42 | **`forward_work_item`** | `/agent/workItems/{id}/forward` |
| UIAPI-43 | **`submit_form`** | `/agent/forms/{name}/submit` |
| UIAPI-44 | **`send_email_template`** | `/agent/emailTemplates/{name}/send` |
| UIAPI-45 | **`export_audit_events`** | `/agent/audit/export` |
| UIAPI-46 | **`create_capability`** | `/agent/capabilities` |
| UIAPI-47 | **`validate_sailpoint_object`** | `/agent/objects/validate` |
| UIAPI-48 | **`resume_workflow_case`** | `/agent/workflows/cases/{id}/resume` |
| UIAPI-49 | **`recalculate_risk_scores`** | `/agent/risk/recalculate` |
| UIAPI-50 | **`list_transitive_reports`** | `/agent/identities/{id}/reports/transitive` |
| UIAPI-51 | **`directory_account_op`** | `/agent/applications/{app}/directory/ops` |
| UIAPI-52 | **`merge_identities`** | `/agent/identities/{id}/merge` |
| UIAPI-53 | **`bulk_onboard_applications`** | `/agent/applications/bulk/onboard` |
| UIAPI-54 | **`retry_provisioning_transaction`** | `/agent/provisioning/{id}/retry` |
| UIAPI-55 | **`configure_alert_rule`** | `/agent/alerts/rules` |
| UIAPI-56 | **`restart_iiq_service`** | `/agent/system/services/{name}/restart` |
| UIAPI-57 | **`assign_identity_scope`** | `/agent/scopes/assign` |
| UIAPI-58 | **`rebuild_manager_hierarchy`** | `/agent/identities/managers/rebuild` |
| UIAPI-59 | **`get_orgchart`** | `/agent/orgchart` (+ `/orgchart/search`) |
| UIAPI-60 | Console orphans / summary / menu | `/agent/console/{orphans,summary,menu}` |
| UIAPI-61 | Console aggregation pipeline | `/agent/console/pipeline` |
| UIAPI-62 | Console approval inbox | `/agent/console/inbox` |
| UIAPI-63 | Console access catalog | `/agent/console/catalog` |
| UIAPI-64 | Console cert campaigns + items | `/agent/console/certs`, `/certs/{id}` |
| UIAPI-65 | Console SoD war room | `/agent/console/sod` |
| UIAPI-66 | Console Identity 360 | `/agent/console/identity360` |
| UIAPI-67 | Console JML timeline | `/agent/console/jml` |
| UIAPI-68 | Console evidence pack | `/agent/console/evidence` |
| UIAPI-69 | Console provisioning debugger | `/agent/console/provisioning` |
| UIAPI-70 | Console workgroups | `/agent/console/workgroups` |
| UIAPI-71 | Console risk heatmap | `/agent/console/heatmap` |
| UIAPI-72 | Console audit activity | `/agent/console/audit` |

Teller Console UI: `http://localhost:4180/console.html` (Waves 1–3 central menu). Org chart risk badges: inactive / brokenManager / privileged.

These tools cover the 300 Teller NL scenarios (domain map in canvas `teller-gap-scenarios-300`), plus manager rebuild for HR hierarchy.

Platform: `iiq_ping`, `get_iiq_status`, `list_iiq_hosts`, `list_modules_status`, `list_monitoring_statistics`, `list_server_statistics`, `get_service_definition`, `get_config_rights`.

Discovery: `list_scim_schemas`, `get_scim_schema`, `list_scim_resource_types`, `get_service_provider_config`, `list_object_configs`, `get_object_config_attributes`.

Apps/identity: `list_authoritative_applications`, `list_application_status`, `discover_application_schema`, `find_identity_by_account`, `list_managed_identities`, `list_accounts_grid`, …

Governance/ops: `list_work_item_archive`, `list_electronic_signature_meanings`, `list_dynamic_scopes`, `get_provisioning_status_counts`, `list_workflow_types`, …

**Still excluded (no Custom API / unsafe):** `update_rule_source`, `update_scope`, legacy name `grant_capability`.

Teller UI (`tools/iiq-chat/`, :4180) discovers tools via live MCP `tools/list` + native OpenRouter tool-calling (no static catalog).

_Regenerate OpenAPI:_ `python3 tools/iiq-api-mine/generate_meridian_agent_openapi.py`
