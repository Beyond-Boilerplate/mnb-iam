"""MCP tools for Meridian Custom APIs that were not yet exposed.

Covers remaining UIAPI gaps wired to ``/plugin/rest/mnbToolkit/agent/*``
(and toolkit ping). Tools that already exist elsewhere are not duplicated.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from iiq_mcp.client.http import IiqHttpClient, encode_path_segment
from iiq_mcp.tools.agent_helpers import agent_get, agent_post, unwrap_agent
from iiq_mcp.tools.meta import Risk, ToolMeta, run_tool, tool_description


def register(mcp: FastMCP, client: IiqHttpClient, **ctx: Any) -> None:
    audit = ctx.get("audit")

    # —— Meta / health ——
    meta_gaps = ToolMeta(
        name="list_uiapi_gaps",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-META",
    )

    @mcp.tool(
        name=meta_gaps.name,
        description=tool_description(
            meta_gaps,
            "Gap matrix + feature flags from Meridian Custom APIs GET /agent/gaps.",
        ),
    )
    async def list_uiapi_gaps() -> dict[str, Any]:
        return await run_tool(meta_gaps, {}, lambda: agent_get(client, "/gaps"), audit=audit)

    meta_ping = ToolMeta(
        name="toolkit_ping",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-27",
    )

    @mcp.tool(
        name=meta_ping.name,
        description=tool_description(meta_ping, "Meridian toolkit health ping GET /mnbToolkit/ping."),
    )
    async def toolkit_ping() -> dict[str, Any]:
        async def _run() -> Any:
            raw = await client.plugin_get("/mnbToolkit/ping")
            return unwrap_agent(raw) if isinstance(raw, dict) and "data" in raw else raw

        return await run_tool(meta_ping, {}, _run, audit=audit)

    # —— UIAPI-07 Application wizard ——
    meta_ca = ToolMeta(
        name="create_application",
        phase=2,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-07",
    )

    @mcp.tool(
        name=meta_ca.name,
        description=tool_description(
            meta_ca,
            "Create/update Application via Custom APIs wizard. "
            "Clones ConnectorRegistry template by type. "
            "DelimitedFile: attributes.file, delimiter, hasHeader; optional identityAttribute/displayAttribute; "
            "authoritative=true to mint cubes. "
            "OpenLDAP - Direct / LDAP: attributes.host, port, user (bind DN), password, searchDN; "
            "optional useSSL, authType; for Meridian lab use host=openldap, port=389, "
            "user=cn=svc-iiq-provision,ou=service,dc=meridiannb,dc=com, password=Provision1!, "
            "searchDN=dc=meridiannb,dc=com. "
            "Does NOT import users — follow with test_application_connection then trigger_aggregation "
            "(or use onboard_application for create+test+aggregate).",
        ),
    )
    async def create_application(
        name: str,
        type: str = "DelimitedFile",
        description: str | None = None,
        owner: str | None = None,
        attributes: dict[str, Any] | None = None,
        features_string: str | None = None,
        overwrite: bool = False,
        authoritative: bool | None = None,
        justification: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {"name": name, "type": type, "overwrite": overwrite}
            if description:
                body["description"] = description
            if owner:
                body["owner"] = owner
            if attributes:
                body["attributes"] = attributes
            if features_string:
                body["featuresString"] = features_string
            if authoritative is not None:
                body["authoritative"] = authoritative
            return await agent_post(client, "/applications/wizard", json_body=body)

        return await run_tool(
            meta_ca,
            {
                "name": name,
                "type": type,
                "description": description,
                "owner": owner,
                "attributes": attributes,
                "features_string": features_string,
                "overwrite": overwrite,
                "authoritative": authoritative,
                "justification": justification,
            },
            _run,
            audit=audit,
        )

    # —— Composite onboard (wizard → test → aggregate) ——
    meta_onboard = ToolMeta(
        name="onboard_application",
        phase=2,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-07",
    )

    @mcp.tool(
        name=meta_onboard.name,
        description=tool_description(
            meta_onboard,
            "One-shot app onboard: create_application (wizard) → test_application_connection → "
            "trigger_aggregation. Pass connector type + attributes (see create_application). "
            "For Meridian OpenLDAP lab: type='OpenLDAP - Direct', attributes with host/port/user/"
            "password/searchDN. Set run_aggregate=false to stop after test connection.",
        ),
    )
    async def onboard_application(
        name: str,
        type: str = "OpenLDAP - Direct",
        attributes: dict[str, Any] | None = None,
        description: str | None = None,
        owner: str | None = None,
        overwrite: bool = False,
        run_aggregate: bool = True,
        full_or_delta: str = "full",
        justification: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {"name": name, "type": type, "overwrite": overwrite}
            if description:
                body["description"] = description
            if owner:
                body["owner"] = owner
            if attributes:
                body["attributes"] = attributes
            created = await agent_post(client, "/applications/wizard", json_body=body)
            tested = await agent_post(
                client, "/connectors/testConnection", json_body={"application": name}
            )
            agg: Any = None
            if run_aggregate:
                agg_body = {
                    "taskName": "Account Aggregation",
                    "sync": False,
                    "args": {"applications": name, "fullOrDelta": full_or_delta},
                }
                agg = await client.plugin_post("/mnbToolkit/tasks/run", json_body=agg_body)
            return {
                "application": name,
                "type": type,
                "created": created,
                "testConnection": tested,
                "aggregation": agg,
                "poll_with": "get_task_result" if agg else None,
            }

        return await run_tool(
            meta_onboard,
            {
                "name": name,
                "type": type,
                "attributes": attributes,
                "description": description,
                "owner": owner,
                "overwrite": overwrite,
                "run_aggregate": run_aggregate,
                "full_or_delta": full_or_delta,
                "justification": justification,
            },
            _run,
            audit=audit,
        )

    # —— UIAPI-08 get config (update_application_config already in impl_lifecycle) ——
    meta_gac = ToolMeta(
        name="get_application_config",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-08",
    )

    @mcp.tool(
        name=meta_gac.name,
        description=tool_description(
            meta_gac, "GET Application attributes/config via Custom APIs (secrets redacted)."
        ),
    )
    async def get_application_config(app_name: str) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_get(client, f"/applications/{encode_path_segment(app_name)}/config")

        return await run_tool(meta_gac, {"app_name": app_name}, _run, audit=audit)

    # —— UIAPI-10 Workgroups ——
    meta_lwg = ToolMeta(
        name="list_workgroups", phase=1, risk=Risk.READ, implemented=True, gap_id="UIAPI-10"
    )

    @mcp.tool(
        name=meta_lwg.name,
        description=tool_description(meta_lwg, "List Identity workgroups via Custom APIs."),
    )
    async def list_workgroups(limit: int | None = 50) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_get(client, "/workgroups", params={"limit": limit})

        return await run_tool(meta_lwg, {"limit": limit}, _run, audit=audit)

    meta_mwg = ToolMeta(
        name="manage_workgroup_members",
        phase=2,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-10",
    )

    @mcp.tool(
        name=meta_mwg.name,
        description=tool_description(
            meta_mwg, "Add or remove a member on a workgroup (op=add|remove)."
        ),
    )
    async def manage_workgroup_members(
        workgroup: str,
        member: str,
        op: str,
        justification: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client,
                f"/workgroups/{encode_path_segment(workgroup)}/members",
                json_body={"op": op, "member": member},
            )

        return await run_tool(
            meta_mwg,
            {"workgroup": workgroup, "member": member, "op": op, "justification": justification},
            _run,
            audit=audit,
        )

    # —— UIAPI-11 Capability assign (grant_capability stays excluded; this is gated agent verb) ——
    meta_aic = ToolMeta(
        name="assign_identity_capability",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-11",
    )

    @mcp.tool(
        name=meta_aic.name,
        description=tool_description(
            meta_aic,
            "Assign or revoke a Capability on an identity via Custom APIs "
            "(requires mutateGovernanceEnabled). op=assign|revoke.",
        ),
    )
    async def assign_identity_capability(
        identity_name: str,
        capability: str,
        op: str = "assign",
        justification: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client,
                f"/identities/{encode_path_segment(identity_name)}/capabilities",
                json_body={"op": op, "capability": capability},
            )

        return await run_tool(
            meta_aic,
            {
                "identity_name": identity_name,
                "capability": capability,
                "op": op,
                "justification": justification,
            },
            _run,
            audit=audit,
        )

    # —— UIAPI-12 unlock via agent password API ——
    meta_ui = ToolMeta(
        name="unlock_iiq_identity",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-12",
    )

    @mcp.tool(
        name=meta_ui.name,
        description=tool_description(
            meta_ui,
            "Clear IIQ login lock (failedLoginAttempts) via Custom APIs password unlock "
            "(requires passwordResetEnabled).",
        ),
    )
    async def unlock_iiq_identity(
        identity_name: str, justification: str | None = None
    ) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client,
                f"/identities/{encode_path_segment(identity_name)}/password",
                json_body={"op": "unlock"},
            )

        return await run_tool(
            meta_ui,
            {"identity_name": identity_name, "justification": justification},
            _run,
            audit=audit,
        )

    # —— UIAPI-13 schedules list (create covered by update_task_schedule) ——
    meta_las = ToolMeta(
        name="list_agent_schedules",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-13",
    )

    @mcp.tool(
        name=meta_las.name,
        description=tool_description(meta_las, "List TaskSchedule objects via Custom APIs."),
    )
    async def list_agent_schedules(limit: int | None = 50) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_get(client, "/schedules", params={"limit": limit})

        return await run_tool(meta_las, {"limit": limit}, _run, audit=audit)

    # —— UIAPI-15 Forms ——
    meta_lf = ToolMeta(name="list_forms", phase=1, risk=Risk.READ, implemented=True, gap_id="UIAPI-15")

    @mcp.tool(name=meta_lf.name, description=tool_description(meta_lf, "List Form objects."))
    async def list_forms(limit: int | None = 50) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_get(client, "/forms", params={"limit": limit})

        return await run_tool(meta_lf, {"limit": limit}, _run, audit=audit)

    meta_gf = ToolMeta(name="get_form", phase=1, risk=Risk.READ, implemented=True, gap_id="UIAPI-15")

    @mcp.tool(name=meta_gf.name, description=tool_description(meta_gf, "Get a Form by name."))
    async def get_form(name: str) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_get(client, f"/forms/{encode_path_segment(name)}")

        return await run_tool(meta_gf, {"name": name}, _run, audit=audit)

    # —— UIAPI-16 QuickLinks ——
    meta_lql = ToolMeta(
        name="list_quicklinks", phase=1, risk=Risk.READ, implemented=True, gap_id="UIAPI-16"
    )

    @mcp.tool(
        name=meta_lql.name, description=tool_description(meta_lql, "List QuickLink objects.")
    )
    async def list_quicklinks(limit: int | None = 50) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_get(client, "/quicklinks", params={"limit": limit})

        return await run_tool(meta_lql, {"limit": limit}, _run, audit=audit)

    # —— UIAPI-17 Email templates ——
    meta_let = ToolMeta(
        name="list_email_templates",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-17",
    )

    @mcp.tool(
        name=meta_let.name,
        description=tool_description(meta_let, "List EmailTemplate objects (edit via SSB)."),
    )
    async def list_email_templates(limit: int | None = 50) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_get(client, "/emailTemplates", params={"limit": limit})

        return await run_tool(meta_let, {"limit": limit}, _run, audit=audit)

    meta_get = ToolMeta(
        name="get_email_template",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-17",
    )

    @mcp.tool(
        name=meta_get.name, description=tool_description(meta_get, "Get EmailTemplate by name.")
    )
    async def get_email_template(name: str) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_get(client, f"/emailTemplates/{encode_path_segment(name)}")

        return await run_tool(meta_get, {"name": name}, _run, audit=audit)

    # —— UIAPI-06 SoD open count (list/mitigate already covered) ——
    meta_soc = ToolMeta(
        name="count_open_sod_violations",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-06",
    )

    @mcp.tool(
        name=meta_soc.name,
        description=tool_description(
            meta_soc, "Count open PolicyViolations; optional policyName prefix."
        ),
    )
    async def count_open_sod_violations(policy_prefix: str | None = None) -> dict[str, Any]:
        async def _run() -> Any:
            params = {}
            if policy_prefix:
                params["policyPrefix"] = policy_prefix
            return await agent_get(client, "/sod/openCount", params=params or None)

        return await run_tool(meta_soc, {"policy_prefix": policy_prefix}, _run, audit=audit)

    meta_lsod = ToolMeta(
        name="list_open_sod_violations",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-06",
    )

    @mcp.tool(
        name=meta_lsod.name,
        description=tool_description(meta_lsod, "List open SoD/PolicyViolations via Custom APIs."),
    )
    async def list_open_sod_violations(limit: int | None = 50) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_get(client, "/sod/violations", params={"limit": limit})

        return await run_tool(meta_lsod, {"limit": limit}, _run, audit=audit)

    # —— UIAPI-04 agent work items ——
    meta_law = ToolMeta(
        name="list_agent_work_items",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-04",
    )

    @mcp.tool(
        name=meta_law.name,
        description=tool_description(meta_law, "List work items via Custom APIs agent surface."),
    )
    async def list_agent_work_items(limit: int | None = 50) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_get(client, "/workItems", params={"limit": limit})

        return await run_tool(meta_law, {"limit": limit}, _run, audit=audit)

    meta_gawi = ToolMeta(
        name="get_agent_work_item",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-04",
    )

    @mcp.tool(
        name=meta_gawi.name,
        description=tool_description(meta_gawi, "Get one work item via Custom APIs."),
    )
    async def get_agent_work_item(work_item_id: str) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_get(client, f"/workItems/{encode_path_segment(work_item_id)}")

        return await run_tool(meta_gawi, {"work_item_id": work_item_id}, _run, audit=audit)

    # —— UIAPI-20 ——
    meta_ahs = ToolMeta(
        name="get_access_history_status",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-20",
    )

    @mcp.tool(
        name=meta_ahs.name,
        description=tool_description(
            meta_ahs, "Probe Access History / IdentityAI Configuration presence."
        ),
    )
    async def get_access_history_status() -> dict[str, Any]:
        return await run_tool(
            meta_ahs, {}, lambda: agent_get(client, "/accessHistory/status"), audit=audit
        )

    # —— UIAPI-21 explicit test connection ——
    meta_tac = ToolMeta(
        name="test_application_connection",
        phase=2,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-21",
    )

    @mcp.tool(
        name=meta_tac.name,
        description=tool_description(
            meta_tac,
            "Run ConnectorFactory.testConfiguration for an Application "
            "(returns success false on connector errors — does not fake OK).",
        ),
    )
    async def test_application_connection(
        application: str | None = None,
        app_name: str | None = None,
    ) -> dict[str, Any]:
        """Test connector config. Accepts ``application`` or alias ``app_name``."""
        resolved = (application or app_name or "").strip()
        if not resolved:
            from iiq_mcp.errors import map_http_error

            raise map_http_error(
                400,
                {
                    "message": "application (or app_name) is required",
                    "detail": "Pass the Application name, e.g. MNB-HR",
                },
            )

        async def _run() -> Any:
            return await agent_post(
                client,
                "/connectors/testConnection",
                json_body={"application": resolved},
            )

        return await run_tool(
            meta_tac, {"application": resolved, "app_name": app_name}, _run, audit=audit
        )

    # —— UIAPI-22 NCD ——
    meta_ncd = ToolMeta(
        name="configure_native_change_detection",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-22",
    )

    @mcp.tool(
        name=meta_ncd.name,
        description=tool_description(
            meta_ncd,
            "Enable/configure native change detection on an Application "
            "(requires advancedOpsEnabled).",
        ),
    )
    async def configure_native_change_detection(
        app_name: str,
        enabled: bool = True,
        operations: list[str] | None = None,
        attributes: list[str] | None = None,
        attribute_scope: str | None = None,
        justification: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {"enabled": enabled}
            if operations is not None:
                body["operations"] = operations
            if attributes is not None:
                body["attributes"] = attributes
            if attribute_scope:
                body["attributeScope"] = attribute_scope
            return await agent_post(
                client,
                f"/applications/{encode_path_segment(app_name)}/nativeChangeDetection",
                json_body=body,
            )

        return await run_tool(
            meta_ncd,
            {
                "app_name": app_name,
                "enabled": enabled,
                "operations": operations,
                "attributes": attributes,
                "attribute_scope": attribute_scope,
                "justification": justification,
            },
            _run,
            audit=audit,
        )

    # —— UIAPI-23 Plugins ——
    meta_lp = ToolMeta(
        name="list_iiq_plugins", phase=1, risk=Risk.READ, implemented=True, gap_id="UIAPI-23"
    )

    @mcp.tool(
        name=meta_lp.name,
        description=tool_description(meta_lp, "List installed IIQ plugins via Custom APIs."),
    )
    async def list_iiq_plugins() -> dict[str, Any]:
        return await run_tool(meta_lp, {}, lambda: agent_get(client, "/plugins"), audit=audit)

    meta_ups = ToolMeta(
        name="update_plugin_settings",
        phase=2,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-23",
    )

    @mcp.tool(
        name=meta_ups.name,
        description=tool_description(
            meta_ups,
            "Update Meridian/IIQ plugin setting values (e.g. agentApiEnabled=true). "
            "Does not require advancedOpsEnabled — used to bootstrap Custom APIs after install.",
        ),
    )
    async def update_plugin_settings(
        plugin_name: str = "mnb_iam_toolkit",
        settings: dict[str, Any] | None = None,
        justification: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body = {"settings": settings or {}}
            # Prefer agent API (works even when agentApiEnabled is currently false).
            try:
                return await agent_post(
                    client,
                    f"/plugins/{encode_path_segment(plugin_name)}/settings",
                    json_body=body,
                )
            except Exception as exc:
                # Fallback hint for older plugin builds
                raise type(exc)(
                    f"{exc} — upgrade mnb_iam_toolkit ≥1.3.2 or set settings in Plugins UI"
                ) from exc

        return await run_tool(
            meta_ups,
            {"plugin_name": plugin_name, "settings": settings, "justification": justification},
            _run,
            audit=audit,
        )

    meta_sps = ToolMeta(
        name="set_plugin_state",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-23",
    )

    @mcp.tool(
        name=meta_sps.name,
        description=tool_description(
            meta_sps, "Enable/disable a plugin (disabled=true|false); requires advancedOpsEnabled."
        ),
    )
    async def set_plugin_state(
        plugin_name: str, disabled: bool, justification: str | None = None
    ) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client,
                f"/plugins/{encode_path_segment(plugin_name)}/state",
                json_body={"disabled": disabled},
            )

        return await run_tool(
            meta_sps,
            {"plugin_name": plugin_name, "disabled": disabled, "justification": justification},
            _run,
            audit=audit,
        )

    meta_ip = ToolMeta(
        name="install_plugin_zip",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-23",
    )

    @mcp.tool(
        name=meta_ip.name,
        description=tool_description(
            meta_ip,
            "Install plugin from Base64 ZIP via Custom APIs (prefer install.sh for labs).",
        ),
    )
    async def install_plugin_zip(
        file_name: str, zip_base64: str, justification: str | None = None
    ) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client,
                "/plugins/install",
                json_body={"fileName": file_name, "zipBase64": zip_base64},
            )

        return await run_tool(
            meta_ip,
            {
                "file_name": file_name,
                "zip_base64": "[redacted]",
                "justification": justification,
            },
            _run,
            audit=audit,
        )

    # —— UIAPI-24 system config write (read already get_system_config) ——
    meta_usc = ToolMeta(
        name="update_system_config",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-24",
    )

    @mcp.tool(
        name=meta_usc.name,
        description=tool_description(
            meta_usc,
            "Merge keys into SystemConfiguration (requires advancedOpsEnabled). "
            "Prefer change tickets; not for routine automation.",
        ),
    )
    async def update_system_config(
        attributes: dict[str, Any], justification: str | None = None
    ) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client, "/system/config", json_body={"attributes": attributes}
            )

        return await run_tool(
            meta_usc,
            {"attributes": attributes, "justification": justification},
            _run,
            audit=audit,
        )

    # —— UIAPI-25 object XML ——
    meta_eso = ToolMeta(
        name="export_sailpoint_object",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-25",
    )

    @mcp.tool(
        name=meta_eso.name,
        description=tool_description(
            meta_eso,
            "Export a sailpoint.object.* instance as XML (class_name + name).",
        ),
    )
    async def export_sailpoint_object(class_name: str, name: str) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_get(
                client,
                "/objects/export",
                params={"className": class_name, "name": name},
            )

        return await run_tool(
            meta_eso, {"class_name": class_name, "name": name}, _run, audit=audit
        )

    meta_iso = ToolMeta(
        name="import_sailpoint_object",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-25",
    )

    @mcp.tool(
        name=meta_iso.name,
        description=tool_description(
            meta_iso,
            "Import SailPoint object XML via Custom APIs (requires advancedOpsEnabled).",
        ),
    )
    async def import_sailpoint_object(
        xml: str, scrub_ids: bool = False, justification: str | None = None
    ) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client,
                "/objects/import",
                json_body={"xml": xml, "scrubIds": scrub_ids},
            )

        return await run_tool(
            meta_iso,
            {"xml_len": len(xml), "scrub_ids": scrub_ids, "justification": justification},
            _run,
            audit=audit,
        )

    meta_dso = ToolMeta(
        name="delete_sailpoint_object",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-25",
    )

    @mcp.tool(
        name=meta_dso.name,
        description=tool_description(
            meta_dso,
            "Delete a SailPoint object by className+name (Identity uses Terminator). Requires advancedOpsEnabled.",
        ),
    )
    async def delete_sailpoint_object(
        class_name: str, name: str, justification: str | None = None
    ) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client,
                "/objects/delete",
                json_body={"className": class_name, "name": name},
            )

        return await run_tool(
            meta_dso,
            {"class_name": class_name, "name": name, "justification": justification},
            _run,
            audit=audit,
        )

    # —— UIAPI-26 study catalog ——
    meta_sc = ToolMeta(
        name="get_study_plugin_catalog",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-26",
    )

    @mcp.tool(
        name=meta_sc.name,
        description=tool_description(
            meta_sc,
            "Study-plugin catalog + installed matches (not a production contract).",
        ),
    )
    async def get_study_plugin_catalog() -> dict[str, Any]:
        return await run_tool(
            meta_sc, {}, lambda: agent_get(client, "/study/catalog"), audit=audit
        )
