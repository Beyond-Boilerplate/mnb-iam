"""High-ROI MCP tools for previously uncovered OOTB REST / SCIM / Custom API surfaces.

Phase-1 reads preferred; Custom API writes stay gated (mutateGovernance / advancedOps).
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from iiq_mcp.client.http import IiqHttpClient, encode_path_segment
from iiq_mcp.shaping import trim_generic
from iiq_mcp.tools.agent_helpers import agent_get, agent_post, scim_list
from iiq_mcp.tools.meta import Risk, ToolMeta, run_tool, tool_description

# Filled at end of register() for tests / introspection.
OPS_EXT_TOOL_NAMES: frozenset[str] = frozenset()


def register(mcp: FastMCP, client: IiqHttpClient, **ctx: Any) -> None:
    global OPS_EXT_TOOL_NAMES
    audit = ctx.get("audit")
    registered: set[str] = set()

    def _collect(name: str) -> str:
        registered.add(name)
        return name

    def rest_get_tool(
        *,
        name: str,
        description: str,
        path: str,
        phase: int = 1,
        gap_id: str | None = None,
        path_keys: tuple[str, ...] = (),
        query_keys: tuple[str, ...] = (),
        defaults: dict[str, Any] | None = None,
    ) -> None:
        tool_name = _collect(name)
        meta = ToolMeta(
            name=tool_name,
            phase=phase,
            risk=Risk.READ,
            implemented=True,
            gap_id=gap_id,
        )
        defaults = defaults or {}

        async def _handler(**kwargs: Any) -> dict[str, Any]:
            async def _run() -> Any:
                resolved = path
                for key in path_keys:
                    val = kwargs.get(key)
                    if val is None or val == "":
                        raise ValueError(f"{key} is required")
                    resolved = resolved.replace("{" + key + "}", encode_path_segment(str(val)))
                params: dict[str, Any] = {}
                for key in query_keys:
                    val = kwargs.get(key, defaults.get(key))
                    if val is not None and val != "":
                        params[key] = val
                return await client.rest_get(resolved, params=params or None)

            return await run_tool(meta, kwargs, _run, audit=audit)

        # Build a callable with explicit optional kwargs for FastMCP schema.
        params_parts: list[str] = []
        for key in path_keys:
            params_parts.append(f"{key}: str")
        for key in query_keys:
            params_parts.append(f"{key}: str | int | bool | None = None")
        sig = ", ".join(params_parts)
        call_args = ", ".join(f"{k}={k}" for k in list(path_keys) + list(query_keys))
        loc: dict[str, Any] = {"_handler": _handler, "Any": Any}
        exec(
            f"async def {name}({sig}) -> dict:\n"
            f"    return await _handler({call_args})\n"
            if sig
            else f"async def {name}() -> dict:\n    return await _handler()\n",
            loc,
        )
        fn = loc[name]
        mcp.tool(name=meta.name, description=tool_description(meta, description))(fn)

    def agent_read_tool(
        *,
        name: str,
        description: str,
        path: str,
        phase: int = 1,
        gap_id: str | None = None,
        path_keys: tuple[str, ...] = (),
        query_keys: tuple[str, ...] = (),
    ) -> None:
        tool_name = _collect(name)
        meta = ToolMeta(
            name=tool_name,
            phase=phase,
            risk=Risk.READ,
            implemented=True,
            gap_id=gap_id,
        )

        async def _handler(**kwargs: Any) -> dict[str, Any]:
            async def _run() -> Any:
                resolved = path
                for key in path_keys:
                    val = kwargs.get(key)
                    if val is None or val == "":
                        raise ValueError(f"{key} is required")
                    resolved = resolved.replace("{" + key + "}", encode_path_segment(str(val)))
                params: dict[str, Any] = {}
                for key in query_keys:
                    val = kwargs.get(key)
                    if val is not None and val != "":
                        params[key] = val
                return await agent_get(client, resolved, params=params or None)

            return await run_tool(meta, kwargs, _run, audit=audit)

        params_parts: list[str] = []
        for key in path_keys:
            params_parts.append(f"{key}: str")
        for key in query_keys:
            params_parts.append(f"{key}: str | int | bool | None = None")
        sig = ", ".join(params_parts)
        call_args = ", ".join(f"{k}={k}" for k in list(path_keys) + list(query_keys))
        loc: dict[str, Any] = {"_handler": _handler, "Any": Any}
        exec(
            f"async def {name}({sig}) -> dict:\n"
            f"    return await _handler({call_args})\n"
            if sig
            else f"async def {name}() -> dict:\n    return await _handler()\n",
            loc,
        )
        fn = loc[name]
        mcp.tool(name=meta.name, description=tool_description(meta, description))(fn)

    # —— 1–8 Health / platform ——
    rest_get_tool(
        name="iiq_ping",
        description="IIQ OOTB REST ping (GET /rest/ping).",
        path="/ping",
    )
    rest_get_tool(
        name="get_iiq_status",
        description="IIQ cluster/status summary (GET /rest/status).",
        path="/status",
    )
    rest_get_tool(
        name="list_iiq_hosts",
        description="List IIQ application-server hosts (GET /rest/hosts).",
        path="/hosts",
    )
    rest_get_tool(
        name="get_iiq_host",
        description="Get one IIQ host by server id (GET /rest/hosts/{serverId}).",
        path="/hosts/{serverId}",
        path_keys=("serverId",),
    )
    rest_get_tool(
        name="list_modules_status",
        description="Module enablement/status map (GET /rest/modules/status).",
        path="/modules/status",
    )
    rest_get_tool(
        name="list_monitoring_statistics",
        description="Monitoring statistics (GET /rest/monitoringStatistics).",
        path="/monitoringStatistics",
    )
    rest_get_tool(
        name="list_server_statistics",
        description="Server statistics (GET /rest/serverStatistics).",
        path="/serverStatistics",
    )
    rest_get_tool(
        name="get_service_definition",
        description="Service definition by name (GET /rest/serviceDefinitions/{name}).",
        path="/serviceDefinitions/{name}",
        path_keys=("name",),
    )

    # —— 9–14 SCIM / object discovery ——
    meta_schemas = ToolMeta(
        name=_collect("list_scim_schemas"),
        phase=1,
        risk=Risk.READ,
        implemented=True,
    )
    registered.add(meta_schemas.name)

    @mcp.tool(
        name=meta_schemas.name,
        description=tool_description(meta_schemas, "List SCIM Schemas (GET /scim/v2/Schemas)."),
    )
    async def list_scim_schemas(
        start: int | None = None,
        count: int | None = None,
        raw: bool = False,
    ) -> dict[str, Any]:
        async def _run() -> dict[str, Any]:
            return await scim_list(client, "/Schemas", start=start, count=count, raw=raw)

        return await run_tool(
            meta_schemas, {"start": start, "count": count, "raw": raw}, _run, audit=audit
        )

    meta_schema = ToolMeta(
        name=_collect("get_scim_schema"),
        phase=1,
        risk=Risk.READ,
        implemented=True,
    )
    registered.add(meta_schema.name)

    @mcp.tool(
        name=meta_schema.name,
        description=tool_description(
            meta_schema, "Get one SCIM Schema by id (e.g. urn:ietf:params:scim:schemas:core:2.0:User)."
        ),
    )
    async def get_scim_schema(id: str, raw: bool = False) -> dict[str, Any]:
        async def _run() -> Any:
            data = await client.scim_get(f"/Schemas/{encode_path_segment(id)}")
            return data if raw else trim_generic(data if isinstance(data, dict) else {"value": data})

        return await run_tool(meta_schema, {"id": id, "raw": raw}, _run, audit=audit)

    meta_rt = ToolMeta(
        name=_collect("list_scim_resource_types"),
        phase=1,
        risk=Risk.READ,
        implemented=True,
    )
    registered.add(meta_rt.name)

    @mcp.tool(
        name=meta_rt.name,
        description=tool_description(meta_rt, "List SCIM ResourceTypes."),
    )
    async def list_scim_resource_types(
        start: int | None = None, count: int | None = None, raw: bool = False
    ) -> dict[str, Any]:
        async def _run() -> dict[str, Any]:
            return await scim_list(client, "/ResourceTypes", start=start, count=count, raw=raw)

        return await run_tool(
            meta_rt, {"start": start, "count": count, "raw": raw}, _run, audit=audit
        )

    meta_spc = ToolMeta(
        name=_collect("get_service_provider_config"),
        phase=1,
        risk=Risk.READ,
        implemented=True,
    )
    registered.add(meta_spc.name)

    @mcp.tool(
        name=meta_spc.name,
        description=tool_description(meta_spc, "SCIM ServiceProviderConfig."),
    )
    async def get_service_provider_config(raw: bool = False) -> dict[str, Any]:
        async def _run() -> Any:
            data = await client.scim_get("/ServiceProviderConfig")
            return data if raw else trim_generic(data if isinstance(data, dict) else {"value": data})

        return await run_tool(meta_spc, {"raw": raw}, _run, audit=audit)

    meta_oc = ToolMeta(
        name=_collect("list_object_configs"),
        phase=1,
        risk=Risk.READ,
        implemented=True,
    )
    registered.add(meta_oc.name)

    @mcp.tool(
        name=meta_oc.name,
        description=tool_description(meta_oc, "List SCIM ObjectConfigs (Identity/Link attribute models)."),
    )
    async def list_object_configs(
        start: int | None = None, count: int | None = None, raw: bool = False
    ) -> dict[str, Any]:
        async def _run() -> dict[str, Any]:
            return await scim_list(client, "/ObjectConfigs", start=start, count=count, raw=raw)

        return await run_tool(
            meta_oc, {"start": start, "count": count, "raw": raw}, _run, audit=audit
        )

    rest_get_tool(
        name="get_object_config_attributes",
        description="ObjectConfig attribute catalog (GET /rest/objectConfig/attributes).",
        path="/objectConfig/attributes",
        query_keys=("className",),
    )

    # —— 15–20 Applications ——
    rest_get_tool(
        name="list_authoritative_applications",
        description="Authoritative applications (GET /rest/applications/authoritativeApps).",
        path="/applications/authoritativeApps",
    )
    rest_get_tool(
        name="list_application_status",
        description="Application status board (GET /rest/applications/status).",
        path="/applications/status",
    )
    rest_get_tool(
        name="discover_application_schema",
        description="Discover schema attributes for an application (GET /rest/applications/configuration/schema/discoverSchemaAttributes).",
        path="/applications/configuration/schema/discoverSchemaAttributes",
        query_keys=("application", "objectType"),
    )
    rest_get_tool(
        name="get_application_correlation_config",
        description="Application correlation config details (GET /rest/applications/correlation/configDetails).",
        path="/applications/correlation/configDetails",
        query_keys=("application",),
    )
    rest_get_tool(
        name="list_application_settings",
        description="Application settings surface (GET /rest/applications/settings).",
        path="/applications/settings",
        query_keys=("application",),
    )
    rest_get_tool(
        name="get_application_extended_attributes",
        description="Application extended attributes (GET /rest/applications/details/extendedAttributes).",
        path="/applications/details/extendedAttributes",
        query_keys=("application",),
    )

    # —— 21–25 Identity / accounts ——
    rest_get_tool(
        name="find_identity_by_account",
        description="Find identity cube by account/native id (GET /rest/identities/findByAccount).",
        path="/identities/findByAccount",
        query_keys=("application", "nativeIdentity", "instance"),
    )
    rest_get_tool(
        name="list_managed_identities",
        description="Managed identities for a manager/identity (GET /rest/identities/{identityId}/managedIdentities).",
        path="/identities/{identityId}/managedIdentities",
        path_keys=("identityId",),
    )
    rest_get_tool(
        name="get_identity_work_item_count",
        description="Open work-item count for identity (GET /rest/identities/{identityId}/workItemCount).",
        path="/identities/{identityId}/workItemCount",
        path_keys=("identityId",),
    )
    rest_get_tool(
        name="list_accounts_grid",
        description="Accounts grid (GET /rest/accountsGrid) — lab account browser.",
        path="/accountsGrid",
        query_keys=("start", "limit", "application"),
    )
    rest_get_tool(
        name="get_account_link",
        description="One account Link by id (GET /rest/accountsGrid/{linkId}).",
        path="/accountsGrid/{linkId}",
        path_keys=("linkId",),
    )

    # —— 26–32 Entitlements / roles (Custom API + OOTB) ——
    agent_read_tool(
        name="list_managed_entitlements",
        description="List ManagedAttributes via Meridian agent (UIAPI-28 GET /agent/entitlements).",
        path="/entitlements",
        gap_id="UIAPI-28",
        query_keys=("application", "attribute", "value", "requestable", "limit"),
    )

    meta_upsert = ToolMeta(
        name=_collect("upsert_entitlement"),
        phase=3,
        risk=Risk.COMPLIANCE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-28",
    )
    registered.add(meta_upsert.name)

    @mcp.tool(
        name=meta_upsert.name,
        description=tool_description(
            meta_upsert,
            "Create/update ManagedAttribute catalog entry (POST /agent/entitlements). "
            "Requires mutateGovernanceEnabled.",
        ),
    )
    async def upsert_entitlement(
        application: str,
        attribute: str,
        value: str,
        display_name: str | None = None,
        description: str | None = None,
        requestable: bool | None = None,
        owner: str | None = None,
        justification: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {
                "application": application,
                "attribute": attribute,
                "value": value,
            }
            if display_name:
                body["displayName"] = display_name
            if description:
                body["description"] = description
            if requestable is not None:
                body["requestable"] = requestable
            if owner:
                body["owner"] = owner
            return await agent_post(client, "/entitlements", json_body=body)

        return await run_tool(
            meta_upsert,
            {
                "application": application,
                "attribute": attribute,
                "value": value,
                "display_name": display_name,
                "description": description,
                "requestable": requestable,
                "owner": owner,
                "justification": justification,
            },
            _run,
            audit=audit,
        )

    agent_read_tool(
        name="list_agent_roles",
        description="List Bundles/roles via Meridian agent (UIAPI-29 GET /agent/roles).",
        path="/roles",
        gap_id="UIAPI-29",
        query_keys=("query", "requestable", "limit"),
    )

    meta_del_role = ToolMeta(
        name=_collect("delete_role"),
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-29",
    )
    registered.add(meta_del_role.name)

    @mcp.tool(
        name=meta_del_role.name,
        description=tool_description(
            meta_del_role,
            "Delete a Bundle/role by name (POST /agent/roles/{name}/delete). Requires advancedOpsEnabled.",
        ),
    )
    async def delete_role(name: str, justification: str | None = None) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(client, f"/roles/{encode_path_segment(name)}/delete")

        return await run_tool(
            meta_del_role, {"name": name, "justification": justification}, _run, audit=audit
        )

    meta_del_pop = ToolMeta(
        name=_collect("delete_population"),
        phase=3,
        risk=Risk.COMPLIANCE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-09",
    )
    registered.add(meta_del_pop.name)

    @mcp.tool(
        name=meta_del_pop.name,
        description=tool_description(
            meta_del_pop,
            "Delete a GroupDefinition/population (POST /agent/populations/{name}/delete).",
        ),
    )
    async def delete_population(name: str, justification: str | None = None) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(client, f"/populations/{encode_path_segment(name)}/delete")

        return await run_tool(
            meta_del_pop, {"name": name, "justification": justification}, _run, audit=audit
        )

    rest_get_tool(
        name="list_assignable_role_permits",
        description="Assignable role permits (GET /rest/roles/assignablePermits).",
        path="/roles/assignablePermits",
        query_keys=("identityId", "roleId"),
    )
    rest_get_tool(
        name="get_identity_role_grid",
        description="Role grid for an identity (GET /rest/roles/grid/{identityId}).",
        path="/roles/grid/{identityId}",
        path_keys=("identityId",),
    )

    # —— 33–43 Governance / work / access ——
    rest_get_tool(
        name="list_work_item_archive",
        description="Work item archive (GET /rest/workitemarchive/workitems).",
        path="/workitemarchive/workitems",
        query_keys=("start", "limit"),
    )
    rest_get_tool(
        name="list_work_item_notifications",
        description="Work item notifications (GET /rest/workItemNotifications).",
        path="/workItemNotifications",
    )
    rest_get_tool(
        name="count_work_item_notifications",
        description="Work item notification count (GET /rest/workItemNotifications/count).",
        path="/workItemNotifications/count",
    )
    rest_get_tool(
        name="list_request_access_types",
        description="LCM request-access types (GET /rest/requestAccess/types).",
        path="/requestAccess/types",
    )
    rest_get_tool(
        name="get_assigned_access",
        description="Assigned access for request flows (GET /rest/requestAccess/assigned).",
        path="/requestAccess/assigned",
        query_keys=("identityId",),
    )
    rest_get_tool(
        name="list_electronic_signature_meanings",
        description="Electronic signature meanings (GET /rest/electronicSignatures/meanings).",
        path="/electronicSignatures/meanings",
    )
    rest_get_tool(
        name="list_exclusions",
        description="Certification/exclusion list (GET /rest/exclusions).",
        path="/exclusions",
    )
    rest_get_tool(
        name="list_dynamic_scopes",
        description="Dynamic scopes (GET /rest/dynamicScopes).",
        path="/dynamicScopes",
    )
    rest_get_tool(
        name="get_cert_entity_summary",
        description="Certification entity summary (GET /rest/certEntity/{entity}/summary).",
        path="/certEntity/{entity}/summary",
        path_keys=("entity",),
    )
    rest_get_tool(
        name="list_cert_entity_violations",
        description="Violations on a certification entity (GET /rest/certEntity/{entity}/violations).",
        path="/certEntity/{entity}/violations",
        path_keys=("entity",),
    )
    rest_get_tool(
        name="list_cert_entity_roles",
        description="Roles on a certification entity (GET /rest/certEntity/{entity}/roles).",
        path="/certEntity/{entity}/roles",
        path_keys=("entity",),
    )

    # —— 44–52 Ops / catalog / toolkit ——
    rest_get_tool(
        name="list_group_factories",
        description="Group factories (GET /rest/groupFactory/list).",
        path="/groupFactory/list",
    )
    rest_get_tool(
        name="get_group_factory_options",
        description="Group factory options (GET /rest/groupFactory/options).",
        path="/groupFactory/options",
    )
    rest_get_tool(
        name="list_notifications",
        description="System notifications (GET /rest/notifications).",
        path="/notifications",
    )
    rest_get_tool(
        name="get_provisioning_status_counts",
        description="Provisioning transaction status counts (GET /rest/provisioningTransactions/statusCounts).",
        path="/provisioningTransactions/statusCounts",
    )
    rest_get_tool(
        name="list_task_result_tab_counts",
        description="Task result tab counts (GET /rest/taskResults/tabCounts).",
        path="/taskResults/tabCounts",
    )
    rest_get_tool(
        name="list_task_schedule_tab_counts",
        description="Task schedule tab counts (GET /rest/taskSchedules/tabCounts).",
        path="/taskSchedules/tabCounts",
    )
    rest_get_tool(
        name="list_workflow_types",
        description="Workflow type catalog (GET /rest/workflows/workflowTypes).",
        path="/workflows/workflowTypes",
    )
    rest_get_tool(
        name="list_callable_workflows",
        description="Callable workflows by type (GET /rest/workflows/callables/{type}).",
        path="/workflows/callables/{type}",
        path_keys=("type",),
    )
    rest_get_tool(
        name="get_message_catalog",
        description="Message catalog entry (GET /rest/messageCatalog/{catKey}).",
        path="/messageCatalog/{catKey}",
        path_keys=("catKey",),
    )
    rest_get_tool(
        name="list_localized_attribute_locales",
        description="Localized attribute locale names (GET /rest/localizedAttribute/localeNames).",
        path="/localizedAttribute/localeNames",
    )

    meta_allowed = ToolMeta(
        name=_collect("list_allowed_toolkit_tasks"),
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-01",
    )
    registered.add(meta_allowed.name)

    @mcp.tool(
        name=meta_allowed.name,
        description=tool_description(
            meta_allowed,
            "Tasks allowlisted for Meridian toolkit run (GET /mnbToolkit/tasks/allowed).",
        ),
    )
    async def list_allowed_toolkit_tasks() -> dict[str, Any]:
        async def _run() -> Any:
            return await client.plugin_get("/mnbToolkit/tasks/allowed")

        return await run_tool(meta_allowed, {}, _run, audit=audit)

    agent_read_tool(
        name="list_agent_capabilities",
        description="Capabilities via Meridian agent (GET /agent/capabilities).",
        path="/capabilities",
        gap_id="UIAPI-11",
        query_keys=("limit",),
    )

    # —— Bonus high-ROI reads (still within ~50+) ——
    rest_get_tool(
        name="get_workflow_summary",
        description="Workflow summary board (GET /rest/workflowSummary).",
        path="/workflowSummary",
    )
    rest_get_tool(
        name="list_workflow_approval_modes",
        description="Workflow approval modes (GET /rest/workflows/approvalModes).",
        path="/workflows/approvalModes",
    )
    rest_get_tool(
        name="get_config_rights",
        description="Config rights for current session (GET /rest/config/rights).",
        path="/config/rights",
    )
    rest_get_tool(
        name="list_form_types",
        description="Form types (GET /rest/form/formTypes).",
        path="/form/formTypes",
    )
    rest_get_tool(
        name="list_partitioned_results",
        description="Partitioned task results (GET /rest/partitionedResults).",
        path="/partitionedResults",
    )
    rest_get_tool(
        name="get_export_status",
        description="Object export job status (GET /rest/export/status).",
        path="/export/status",
    )
    rest_get_tool(
        name="list_managed_attribute_names",
        description="Managed attribute name index (GET /rest/managedAttributes/names).",
        path="/managedAttributes/names",
        query_keys=("application", "attribute"),
    )
    rest_get_tool(
        name="get_managed_attribute",
        description="Managed attribute by id (GET /rest/managedAttributes/{id}).",
        path="/managedAttributes/{id}",
        path_keys=("id",),
    )

    OPS_EXT_TOOL_NAMES = frozenset(registered)
