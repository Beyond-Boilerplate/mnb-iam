"""SCIM-backed roles, entitlements, alerts, workflows (formerly stubs)."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from iiq_mcp.client.http import IiqHttpClient, encode_path_segment
from iiq_mcp.errors import IiqMcpError, McpErrorBody, ErrorCode, map_http_error
from iiq_mcp.shaping import trim_generic
from iiq_mcp.tools.agent_helpers import agent_post, scim_get_by_id_or_filter, scim_list, scim_mutate
from iiq_mcp.tools.meta import Risk, ToolMeta, run_tool, tool_description

_ROLE_KEYS = ("id", "name", "displayName", "type", "description", "owner", "active", "meta")
_ENT_KEYS = ("id", "displayName", "type", "application", "attribute", "value", "description", "requestable", "owner")
_ALERT_KEYS = ("id", "name", "type", "level", "status", "target", "created", "description")
_WF_KEYS = ("id", "name", "description", "type", "meta")


def register(mcp: FastMCP, client: IiqHttpClient, **ctx: Any) -> None:
    audit = ctx.get("audit")

    # —— Roles ——
    meta = ToolMeta(name="search_roles", phase=2, risk=Risk.READ, implemented=True)

    @mcp.tool(name=meta.name, description=tool_description(meta, "Search SCIM Roles (IT/business)."))
    async def search_roles(
        query: str | None = None,
        type: str | None = None,
        start: int | None = None,
        count: int | None = None,
        raw: bool = False,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            filters = []
            if query:
                q = query.replace('"', '\\"')
                filters.append(f'name co "{q}" or displayName co "{q}"')
            if type:
                filters.append(f'type eq "{type}"')
            filt = " and ".join(f"({f})" for f in filters) if filters else None
            return await scim_list(
                client, "/Roles", filter=filt, start=start, count=count, raw=raw, keys=_ROLE_KEYS
            )

        return await run_tool(
            meta, {"query": query, "type": type, "start": start, "count": count, "raw": raw}, _run, audit=audit
        )

    meta_rd = ToolMeta(name="get_role_detail", phase=2, risk=Risk.READ, implemented=True)

    @mcp.tool(name=meta_rd.name, description=tool_description(meta_rd, "Get one SCIM Role by id or name."))
    async def get_role_detail(role_id: str, raw: bool = False) -> dict[str, Any]:
        async def _run() -> Any:
            role = await scim_get_by_id_or_filter(client, "/Roles", role_id)
            return role if raw else trim_generic(role, keys=_ROLE_KEYS, raw=False)

        return await run_tool(meta_rd, {"role_id": role_id, "raw": raw}, _run, audit=audit)

    meta_rm = ToolMeta(name="get_role_membership", phase=2, risk=Risk.READ, implemented=True)

    @mcp.tool(
        name=meta_rm.name,
        description=tool_description(
            meta_rm,
            "Best-effort role holders via SCIM Users filter on roles (attribute names vary by install).",
        ),
    )
    async def get_role_membership(
        role_id: str, start: int | None = None, count: int | None = None, raw: bool = False
    ) -> dict[str, Any]:
        async def _run() -> Any:
            role = await scim_get_by_id_or_filter(client, "/Roles", role_id)
            rname = role.get("name") or role.get("displayName") or role_id
            for filt in (
                f'roles.value eq "{role_id}"',
                f'roles.display eq "{rname}"',
                f'assignedRoles eq "{rname}"',
            ):
                try:
                    return await scim_list(
                        client,
                        "/Users",
                        filter=filt,
                        start=start,
                        count=count,
                        raw=raw,
                        keys=("id", "userName", "displayName", "active"),
                    )
                except Exception:
                    continue
            return {
                "role_id": role_id,
                "role_name": rname,
                "items": [],
                "note": "Could not resolve membership filters on this IIQ SCIM build.",
            }

        return await run_tool(
            meta_rm, {"role_id": role_id, "start": start, "count": count, "raw": raw}, _run, audit=audit
        )

    meta_mine = ToolMeta(
        name="get_role_mining_suggestions",
        phase=2,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-20",
    )

    @mcp.tool(
        name=meta_mine.name,
        description=tool_description(
            meta_mine,
            "Probe Access History / AI config presence (role mining module); not full mining results.",
        ),
    )
    async def get_role_mining_suggestions() -> dict[str, Any]:
        from iiq_mcp.tools.agent_helpers import agent_get

        async def _run() -> Any:
            try:
                status = await agent_get(client, "/accessHistory/status")
                return {"role_mining": "probe_only", "module_status": status}
            except Exception as exc:
                raise IiqMcpError(
                    McpErrorBody(
                        code=ErrorCode.NOT_IMPLEMENTED,
                        http_status=501,
                        message="Role mining suggestions unavailable; Access History/AI module not exposed.",
                        gap_id="UIAPI-20",
                        iiq_detail=str(exc),
                    )
                )

        return await run_tool(meta_mine, {}, _run, audit=audit)

    meta_cr = ToolMeta(
        name="create_role", phase=4, risk=Risk.ADMIN, implemented=True, requires_confirmation=True
    )

    @mcp.tool(name=meta_cr.name, description=tool_description(meta_cr, "Create Bundle role via Meridian agent (SCIM Roles POST is often 405)."))
    async def create_role(definition: dict[str, Any], justification: str | None = None) -> dict[str, Any]:
        async def _run() -> Any:
            body = dict(definition or {})
            try:
                return await agent_post(client, "/roles", json_body=body)
            except Exception as scim_exc:
                # Fallback: SCIM if agent unavailable
                try:
                    scim_body = {
                        "schemas": ["urn:ietf:params:scim:schemas:sailpoint:1.0:Role"],
                        **body,
                    }
                    return await scim_mutate(client, "POST", "/Roles", json_body=scim_body)
                except Exception:
                    raise scim_exc from None

        return await run_tool(
            meta_cr, {"definition": definition, "justification": justification}, _run, audit=audit
        )

    meta_ur = ToolMeta(
        name="update_role", phase=4, risk=Risk.ADMIN, implemented=True, requires_confirmation=True
    )

    @mcp.tool(name=meta_ur.name, description=tool_description(meta_ur, "PUT/PATCH SCIM Role."))
    async def update_role(
        role_id: str, patch: dict[str, Any], justification: str | None = None
    ) -> dict[str, Any]:
        async def _run() -> Any:
            try:
                return await scim_mutate(
                    client, "PATCH", f"/Roles/{encode_path_segment(role_id)}", json_body=patch
                )
            except Exception:
                current = await scim_get_by_id_or_filter(client, "/Roles", role_id)
                merged = {**current, **patch}
                rid = current.get("id") or role_id
                return await scim_mutate(
                    client, "PUT", f"/Roles/{encode_path_segment(rid)}", json_body=merged
                )

        return await run_tool(
            meta_ur, {"role_id": role_id, "patch": patch, "justification": justification}, _run, audit=audit
        )

    meta_dr = ToolMeta(
        name="deprecate_role", phase=4, risk=Risk.ADMIN, implemented=True, requires_confirmation=True
    )

    @mcp.tool(
        name=meta_dr.name,
        description=tool_description(meta_dr, "Soft-deprecate role (active=false) via SCIM."),
    )
    async def deprecate_role(role_id: str, justification: str | None = None) -> dict[str, Any]:
        async def _run() -> Any:
            try:
                return await agent_post(client, f"/roles/{encode_path_segment(role_id)}/delete")
            except Exception:
                return await scim_mutate(
                    client,
                    "PATCH",
                    f"/Roles/{encode_path_segment(role_id)}",
                    json_body={"active": False, "deprecated": True},
                )

        return await run_tool(
            meta_dr, {"role_id": role_id, "justification": justification}, _run, audit=audit
        )

    # —— Entitlements ——
    meta_se = ToolMeta(name="search_entitlements", phase=2, risk=Risk.READ, implemented=True)

    @mcp.tool(name=meta_se.name, description=tool_description(meta_se, "Search SCIM Entitlements."))
    async def search_entitlements(
        app: str | None = None,
        attribute: str | None = None,
        query: str | None = None,
        start: int | None = None,
        count: int | None = None,
        raw: bool = False,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            filters = []
            if app:
                filters.append(f'application eq "{app}" or application.displayName eq "{app}"')
            if attribute:
                filters.append(f'attribute eq "{attribute}"')
            if query:
                q = query.replace('"', '\\"')
                # IIQ SCIM Entitlements often lack displayName as a filterable attr —
                # value/type only. Fall through to agent catalog if SCIM errors.
                filters.append(f'value co "{q}" or type co "{q}"')
            filt = " and ".join(f"({f})" for f in filters) if filters else None
            try:
                listed = await scim_list(
                    client, "/Entitlements", filter=filt, start=start, count=count, raw=raw, keys=_ENT_KEYS
                )
            except Exception:
                listed = {"items": [], "totalResults": 0}
            if (listed.get("totalResults") or listed.get("returned") or 0) or listed.get("items"):
                if listed.get("items"):
                    return listed
                # empty success — still try agent catalog below when query present
                if not query and not app:
                    return listed
            # Agent ManagedAttribute catalog
            from iiq_mcp.tools.agent_helpers import agent_get
            from iiq_mcp.shaping import clamp_page, list_envelope

            s, c = clamp_page(start, count)
            params: dict[str, Any] = {"limit": c}
            if app:
                params["application"] = app
            if attribute:
                params["attribute"] = attribute
            if query:
                params["value"] = query
            data = await agent_get(client, "/entitlements", params=params)
            items = (data or {}).get("items") if isinstance(data, dict) else data
            items = items if isinstance(items, list) else []
            env = list_envelope(
                [trim_generic(i, keys=_ENT_KEYS, raw=raw) for i in items if isinstance(i, dict)],
                start=s,
                count=c,
                total=len(items),
                raw=raw,
            )
            env["source"] = "agent"
            return env

        return await run_tool(
            meta_se,
            {"app": app, "attribute": attribute, "query": query, "start": start, "count": count, "raw": raw},
            _run,
            audit=audit,
        )

    meta_ed = ToolMeta(name="get_entitlement_detail", phase=2, risk=Risk.READ, implemented=True)

    @mcp.tool(
        name=meta_ed.name,
        description=tool_description(meta_ed, "Get entitlement by app+attribute+value or SCIM id."),
    )
    async def get_entitlement_detail(
        app: str | None = None,
        attribute: str | None = None,
        value: str | None = None,
        entitlement_id: str | None = None,
        raw: bool = False,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            if entitlement_id:
                data = await scim_get_by_id_or_filter(client, "/Entitlements", entitlement_id, name_attr="displayName")
            elif app and attribute and value:
                filt = (
                    f'application eq "{app}" and attribute eq "{attribute}" and value eq "{value}"'
                )
                listed = await scim_list(client, "/Entitlements", filter=filt, count=1, raw=True)
                items = listed.get("items") or []
                if not items:
                    raise map_http_error(404, {"message": "Entitlement not found"})
                data = items[0]
            else:
                raise map_http_error(
                    400, {"message": "Provide entitlement_id or app+attribute+value"}
                )
            return data if raw else trim_generic(data, keys=_ENT_KEYS, raw=False)

        return await run_tool(
            meta_ed,
            {"app": app, "attribute": attribute, "value": value, "entitlement_id": entitlement_id, "raw": raw},
            _run,
            audit=audit,
        )

    meta_em = ToolMeta(name="get_entitlement_membership", phase=2, risk=Risk.READ, implemented=True)

    @mcp.tool(
        name=meta_em.name,
        description=tool_description(
            meta_em, "Best-effort who holds an entitlement via SCIM Users/Accounts filters."
        ),
    )
    async def get_entitlement_membership(
        app: str,
        attribute: str,
        value: str,
        start: int | None = None,
        count: int | None = None,
        raw: bool = False,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            for filt in (
                f'entitlements.value eq "{value}"',
                f'entitlements eq "{value}"',
            ):
                try:
                    return await scim_list(
                        client,
                        "/Users",
                        filter=filt,
                        start=start,
                        count=count,
                        raw=raw,
                        keys=("id", "userName", "displayName"),
                    )
                except Exception:
                    continue
            return {"app": app, "attribute": attribute, "value": value, "items": [], "note": "membership filter unsupported"}

        return await run_tool(
            meta_em,
            {"app": app, "attribute": attribute, "value": value, "start": start, "count": count, "raw": raw},
            _run,
            audit=audit,
        )

    meta_ag = ToolMeta(name="list_account_groups", phase=2, risk=Risk.READ, implemented=True)

    @mcp.tool(
        name=meta_ag.name,
        description=tool_description(meta_ag, "List group-type entitlements for an application."),
    )
    async def list_account_groups(
        app: str, start: int | None = None, count: int | None = None, raw: bool = False
    ) -> dict[str, Any]:
        async def _run() -> Any:
            filt = f'application eq "{app}" and (type eq "group" or attribute eq "memberOf" or attribute eq "groups")'
            return await scim_list(
                client, "/Entitlements", filter=filt, start=start, count=count, raw=raw, keys=_ENT_KEYS
            )

        return await run_tool(
            meta_ag, {"app": app, "start": start, "count": count, "raw": raw}, _run, audit=audit
        )

    meta_ue = ToolMeta(
        name="update_entitlement_metadata",
        phase=3,
        risk=Risk.COMPLIANCE,
        implemented=True,
        requires_confirmation=True,
    )

    @mcp.tool(
        name=meta_ue.name,
        description=tool_description(meta_ue, "PATCH entitlement metadata (description/owner/requestable)."),
    )
    async def update_entitlement_metadata(
        app: str,
        attribute: str,
        value: str,
        patch: dict[str, Any],
        justification: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            from iiq_mcp.tools.agent_helpers import agent_post

            body = {
                "application": app,
                "attribute": attribute,
                "value": value,
                **(patch or {}),
            }
            try:
                return await agent_post(client, "/entitlements", json_body=body)
            except Exception:
                filt = (
                    f'application eq "{app}" and attribute eq "{attribute}" and value eq "{value}"'
                )
                listed = await scim_list(client, "/Entitlements", filter=filt, count=1, raw=True)
                items = listed.get("items") or []
                if not items:
                    raise map_http_error(404, {"message": "Entitlement not found"})
                eid = items[0].get("id")
                if not eid:
                    raise map_http_error(404, {"message": "Entitlement id unresolved"})
                return await scim_mutate(
                    client, "PATCH", f"/Entitlements/{encode_path_segment(eid)}", json_body=patch
                )

        return await run_tool(
            meta_ue,
            {
                "app": app,
                "attribute": attribute,
                "value": value,
                "patch": patch,
                "justification": justification,
            },
            _run,
            audit=audit,
        )

    # —— Alerts ——
    meta_la = ToolMeta(name="list_alerts", phase=2, risk=Risk.READ, implemented=True)

    @mcp.tool(name=meta_la.name, description=tool_description(meta_la, "List SCIM Alerts."))
    async def list_alerts(
        identity_id: str | None = None,
        type: str | None = None,
        status: str | None = None,
        start: int | None = None,
        count: int | None = None,
        raw: bool = False,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            filters = []
            if identity_id:
                filters.append(f'target eq "{identity_id}" or identity eq "{identity_id}"')
            if type:
                filters.append(f'type eq "{type}"')
            if status:
                filters.append(f'status eq "{status}"')
            filt = " and ".join(f"({f})" for f in filters) if filters else None
            return await scim_list(
                client, "/Alerts", filter=filt, start=start, count=count, raw=raw, keys=_ALERT_KEYS
            )

        return await run_tool(
            meta_la,
            {
                "identity_id": identity_id,
                "type": type,
                "status": status,
                "start": start,
                "count": count,
                "raw": raw,
            },
            _run,
            audit=audit,
        )

    meta_aa = ToolMeta(
        name="acknowledge_alert",
        phase=2,
        risk=Risk.LOW_WRITE,
        implemented=True,
        requires_confirmation=True,
    )

    @mcp.tool(
        name=meta_aa.name,
        description=tool_description(meta_aa, "Acknowledge/close an alert via SCIM PATCH when supported."),
    )
    async def acknowledge_alert(alert_id: str, justification: str | None = None) -> dict[str, Any]:
        async def _run() -> Any:
            return await scim_mutate(
                client,
                "PATCH",
                f"/Alerts/{encode_path_segment(alert_id)}",
                json_body={"status": "Acknowledged", "acknowledged": True},
            )

        return await run_tool(
            meta_aa, {"alert_id": alert_id, "justification": justification}, _run, audit=audit
        )

    meta_car = ToolMeta(
        name="configure_alert_rule",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-55",
    )

    @mcp.tool(
        name=meta_car.name,
        description=tool_description(
            meta_car,
            "Configure an alert monitoring rule via Meridian agent (name/threshold/channel), "
            "or pass definition.xml to import via objects/import.",
        ),
    )
    async def configure_alert_rule(
        name: str | None = None,
        threshold: int | None = None,
        channel: str | None = None,
        enabled: bool = True,
        definition: dict[str, Any] | None = None,
        justification: str | None = None,
    ) -> dict[str, Any]:
        from iiq_mcp.tools.agent_helpers import agent_post

        async def _run() -> Any:
            xml = (definition or {}).get("xml")
            if xml:
                return await agent_post(client, "/objects/import", json_body={"xml": xml})
            rule_name = name or (definition or {}).get("name")
            if not rule_name:
                raise IiqMcpError(
                    McpErrorBody(
                        code=ErrorCode.VALIDATION,
                        http_status=400,
                        message="Pass name (and optional threshold/channel) or definition.xml",
                        gap_id="UIAPI-55",
                    )
                )
            body: dict[str, Any] = {"name": rule_name, "enabled": enabled}
            if threshold is not None:
                body["threshold"] = threshold
            elif definition and definition.get("threshold") is not None:
                body["threshold"] = definition["threshold"]
            ch = channel or (definition or {}).get("channel")
            if ch:
                body["channel"] = ch
            return await agent_post(client, "/alerts/rules", json_body=body)

        return await run_tool(
            meta_car,
            {
                "name": name,
                "threshold": threshold,
                "channel": channel,
                "enabled": enabled,
                "definition": definition,
                "justification": justification,
            },
            _run,
            audit=audit,
        )

    # —— Workflows (SCIM) ——
    meta_lwd = ToolMeta(name="list_workflow_definitions", phase=2, risk=Risk.READ, implemented=True)

    @mcp.tool(name=meta_lwd.name, description=tool_description(meta_lwd, "List SCIM Workflows."))
    async def list_workflow_definitions(
        start: int | None = None, count: int | None = None, raw: bool = False
    ) -> dict[str, Any]:
        async def _run() -> Any:
            return await scim_list(
                client, "/Workflows", start=start, count=count, raw=raw, keys=_WF_KEYS
            )

        return await run_tool(
            meta_lwd, {"start": start, "count": count, "raw": raw}, _run, audit=audit
        )

    meta_gwc = ToolMeta(name="get_workflow_case_status", phase=2, risk=Risk.READ, implemented=True)

    @mcp.tool(
        name=meta_gwc.name,
        description=tool_description(meta_gwc, "Get LaunchedWorkflow / case by id (SCIM)."),
    )
    async def get_workflow_case_status(case_id: str, raw: bool = False) -> dict[str, Any]:
        async def _run() -> Any:
            try:
                data = await client.scim_get(f"/LaunchedWorkflows/{encode_path_segment(case_id)}")
            except Exception:
                data = await scim_get_by_id_or_filter(
                    client, "/LaunchedWorkflows", case_id, name_attr="name"
                )
            return data if raw else trim_generic(data, raw=False)

        return await run_tool(meta_gwc, {"case_id": case_id, "raw": raw}, _run, audit=audit)

    meta_law = ToolMeta(name="list_active_workflow_cases", phase=2, risk=Risk.READ, implemented=True)

    @mcp.tool(
        name=meta_law.name,
        description=tool_description(meta_law, "List SCIM LaunchedWorkflows (optionally by workflow name)."),
    )
    async def list_active_workflow_cases(
        workflow_name: str | None = None,
        start: int | None = None,
        count: int | None = None,
        raw: bool = False,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            filt = f'name co "{workflow_name}"' if workflow_name else None
            return await scim_list(
                client, "/LaunchedWorkflows", filter=filt, start=start, count=count, raw=raw
            )

        return await run_tool(
            meta_law,
            {"workflow_name": workflow_name, "start": start, "count": count, "raw": raw},
            _run,
            audit=audit,
        )

    meta_lw = ToolMeta(
        name="launch_workflow",
        phase=2,
        risk=Risk.LOW_WRITE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-03",
    )

    @mcp.tool(
        name=meta_lw.name,
        description=tool_description(
            meta_lw,
            "Launch workflow via Meridian accessRequests agent (LCM-style) or SCIM Workflows POST.",
        ),
    )
    async def launch_workflow(
        workflow_name: str,
        input_variables: dict[str, Any] | None = None,
        identity_name: str | None = None,
        justification: str | None = None,
    ) -> dict[str, Any]:
        from iiq_mcp.tools.agent_helpers import agent_post

        async def _run() -> Any:
            if identity_name:
                return await agent_post(
                    client,
                    "/accessRequests",
                    json_body={
                        "workflowName": workflow_name,
                        "identityName": identity_name,
                        "variables": input_variables or {},
                    },
                )
            return await scim_mutate(
                client,
                "POST",
                "/LaunchedWorkflows",
                json_body={
                    "schemas": ["urn:ietf:params:scim:schemas:sailpoint:1.0:LaunchedWorkflow"],
                    "workflowName": workflow_name,
                    "input": input_variables or {},
                },
            )

        return await run_tool(
            meta_lw,
            {
                "workflow_name": workflow_name,
                "input_variables": input_variables,
                "identity_name": identity_name,
                "justification": justification,
            },
            _run,
            audit=audit,
        )

    meta_tw = ToolMeta(
        name="terminate_workflow_case",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
    )

    @mcp.tool(
        name=meta_tw.name,
        description=tool_description(meta_tw, "Terminate/delete launched workflow case via SCIM DELETE."),
    )
    async def terminate_workflow_case(case_id: str, justification: str | None = None) -> dict[str, Any]:
        async def _run() -> Any:
            await scim_mutate(client, "DELETE", f"/LaunchedWorkflows/{encode_path_segment(case_id)}")
            return {"case_id": case_id, "terminated": True}

        return await run_tool(
            meta_tw, {"case_id": case_id, "justification": justification}, _run, audit=audit
        )
