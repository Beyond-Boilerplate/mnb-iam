"""Meridian agent + governance write tools (access, certs, SoD, work items, populations, audit, batch, admin reads)."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from iiq_mcp.client.http import IiqHttpClient, encode_path_segment
from iiq_mcp.errors import IiqMcpError, McpErrorBody, ErrorCode, map_http_error
from iiq_mcp.shaping import clamp_page, list_envelope, trim_generic
from iiq_mcp.tools.agent_helpers import agent_get, agent_post
from iiq_mcp.tools.meta import Risk, ToolMeta, run_tool, tool_description


def register(mcp: FastMCP, client: IiqHttpClient, **ctx: Any) -> None:
    audit = ctx.get("audit")

    # —— Access requests ——
    meta_car = ToolMeta(
        name="create_access_request",
        phase=2,
        risk=Risk.LOW_WRITE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-03",
    )

    @mcp.tool(
        name=meta_car.name,
        description=tool_description(
            meta_car,
            "Create access/role request via Meridian agent (launches LCM workflow). Pass items in variables.plan.",
        ),
    )
    async def create_access_request(
        identity_id: str,
        items: list[dict[str, Any]] | None = None,
        justification: str | None = None,
        requested_for: str | None = None,
        workflow_name: str = "LCM Provisioning",
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            if not items and not (variables or {}).get("requestedItems") and not (variables or {}).get("plan"):
                raise IiqMcpError(
                    McpErrorBody(
                        code=ErrorCode.VALIDATION,
                        http_status=400,
                        message="create_access_request requires non-empty items (or variables.requestedItems/plan)",
                        gap_id="UIAPI-03",
                        iiq_detail={
                            "hint": "Lab has no requestable Roles/Entitlements until those apps are onboarded; "
                            "pass at least one role/entitlement item.",
                        },
                    )
                )
            vars_ = dict(variables or {})
            if items is not None:
                vars_.setdefault("requestedItems", items)
            if justification:
                vars_.setdefault("comments", justification)
            target = requested_for or identity_id
            data = await agent_post(
                client,
                "/accessRequests",
                json_body={
                    "identityName": target,
                    "workflowName": workflow_name,
                    "variables": vars_,
                },
            )
            if isinstance(data, dict) and str(data.get("launchStatus", "")).lower() in {
                "failed",
                "error",
                "failure",
            }:
                raise IiqMcpError(
                    McpErrorBody(
                        code=ErrorCode.DOWNSTREAM,
                        http_status=502,
                        message=f"Access request launch failed (launchStatus={data.get('launchStatus')})",
                        gap_id="UIAPI-03",
                        iiq_detail=data if isinstance(data, dict) else {"data": data},
                    )
                )
            return data

        return await run_tool(
            meta_car,
            {
                "identity_id": identity_id,
                "items": items,
                "justification": justification,
                "requested_for": requested_for,
                "workflow_name": workflow_name,
                "variables": variables,
            },
            _run,
            audit=audit,
        )

    meta_grant = ToolMeta(
        name="grant_access",
        phase=2,
        risk=Risk.LOW_WRITE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-03",
    )

    @mcp.tool(
        name=meta_grant.name,
        description=tool_description(
            meta_grant,
            "Give a person access by name: resolves identity + role/entitlement, then launches LCM. "
            "Args: identity (userName or display name), access_name (role or entitlement), "
            "optional access_type=role|entitlement. Prefer this over create_access_request for "
            "NL like 'give Anita Rao the Wire Initiator role'.",
        ),
    )
    async def grant_access(
        identity: str,
        access_name: str,
        access_type: str | None = None,
        justification: str | None = None,
        workflow_name: str = "LCM Provisioning",
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {
                "identityName": identity,
                "accessName": access_name,
                "workflowName": workflow_name,
            }
            if access_type:
                body["accessType"] = access_type
            if justification:
                body["justification"] = justification
            return await agent_post(client, "/access/grant", json_body=body)

        return await run_tool(
            meta_grant,
            {
                "identity": identity,
                "access_name": access_name,
                "access_type": access_type,
                "justification": justification,
                "workflow_name": workflow_name,
            },
            _run,
            audit=audit,
        )

    meta_revoke = ToolMeta(
        name="revoke_access",
        phase=2,
        risk=Risk.LOW_WRITE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-03",
    )

    @mcp.tool(
        name=meta_revoke.name,
        description=tool_description(
            meta_revoke,
            "Revoke a role/entitlement by name via LCM RemoveAccess. Same args as grant_access.",
        ),
    )
    async def revoke_access(
        identity: str,
        access_name: str,
        access_type: str | None = None,
        justification: str | None = None,
        workflow_name: str = "LCM Provisioning",
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {
                "identityName": identity,
                "accessName": access_name,
                "workflowName": workflow_name,
            }
            if access_type:
                body["accessType"] = access_type
            if justification:
                body["justification"] = justification
            return await agent_post(client, "/access/revoke", json_body=body)

        return await run_tool(
            meta_revoke,
            {
                "identity": identity,
                "access_name": access_name,
                "access_type": access_type,
                "justification": justification,
                "workflow_name": workflow_name,
            },
            _run,
            audit=audit,
        )

    meta_crr = ToolMeta(
        name="create_removal_request",
        phase=2,
        risk=Risk.LOW_WRITE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-03",
    )

    @mcp.tool(
        name=meta_crr.name,
        description=tool_description(meta_crr, "Launch removal/revoke LCM flow via agent accessRequests."),
    )
    async def create_removal_request(
        identity_id: str,
        items: list[dict[str, Any]],
        justification: str | None = None,
        workflow_name: str = "LCM Provisioning",
    ) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client,
                "/accessRequests",
                json_body={
                    "identityName": identity_id,
                    "workflowName": workflow_name,
                    "variables": {
                        "requestedItems": items,
                        "flow": "RemoveAccess",
                        "comments": justification,
                    },
                },
            )

        return await run_tool(
            meta_crr,
            {
                "identity_id": identity_id,
                "items": items,
                "justification": justification,
                "workflow_name": workflow_name,
            },
            _run,
            audit=audit,
        )

    meta_ars = ToolMeta(
        name="get_access_request_status", phase=2, risk=Risk.READ, implemented=True, gap_id="UIAPI-03"
    )

    @mcp.tool(
        name=meta_ars.name,
        description=tool_description(
            meta_ars, "Poll access request / workflow launch status (SCIM TaskResult or LaunchedWorkflow)."
        ),
    )
    async def get_access_request_status(request_id: str, raw: bool = False) -> dict[str, Any]:
        async def _run() -> Any:
            for path in (
                f"/scim/v2/TaskResults/{encode_path_segment(request_id)}",
                f"/scim/v2/LaunchedWorkflows/{encode_path_segment(request_id)}",
                f"/rest/identityRequests/{encode_path_segment(request_id)}",
            ):
                try:
                    if path.startswith("/rest/"):
                        data = await client.rest_get(path[len("/rest") :])
                    else:
                        _, data = await client.request("GET", path, accept="application/scim+json, application/json")
                    return data if raw else trim_generic(data if isinstance(data, dict) else {"value": data})
                except Exception:
                    continue
            raise map_http_error(404, {"message": f"Access request / launch not found: {request_id}"})

        return await run_tool(meta_ars, {"request_id": request_id, "raw": raw}, _run, audit=audit)

    meta_lar = ToolMeta(
        name="list_access_requests", phase=2, risk=Risk.READ, implemented=True, gap_id="UIAPI-03"
    )

    @mcp.tool(
        name=meta_lar.name,
        description=tool_description(meta_lar, "Best-effort list identity requests via OOTB REST."),
    )
    async def list_access_requests(
        identity_id: str | None = None,
        status: str | None = None,
        start: int | None = None,
        count: int | None = None,
        raw: bool = False,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            s, c = clamp_page(start, count)
            items: list[dict[str, Any]] = []
            for path in ("/identityRequests", "/accessRequests", "/requests"):
                try:
                    payload = await client.rest_get(path)
                    if isinstance(payload, list):
                        items = [x for x in payload if isinstance(x, dict)]
                    elif isinstance(payload, dict):
                        for key in ("objects", "items", "identityRequests", "results"):
                            if isinstance(payload.get(key), list):
                                items = [x for x in payload[key] if isinstance(x, dict)]
                                break
                    if items:
                        break
                except Exception:
                    continue
            if identity_id:
                items = [
                    i
                    for i in items
                    if identity_id in str(i.get("identity", ""))
                    or identity_id in str(i.get("targetId", ""))
                    or identity_id in str(i.get("name", ""))
                ]
            if status:
                items = [i for i in items if status.lower() in str(i.get("status", "")).lower()]
            page = items[s : s + c]
            trimmed = [trim_generic(i, raw=raw) for i in page]
            env = list_envelope(trimmed, start=s, count=c, total=len(items), raw=raw)
            if not items:
                env["note"] = "No OOTB identityRequests list; use get_access_request_status with launch id."
            return env

        return await run_tool(
            meta_lar,
            {"identity_id": identity_id, "status": status, "start": start, "count": count, "raw": raw},
            _run,
            audit=audit,
        )

    meta_gri = ToolMeta(
        name="get_requestable_items", phase=2, risk=Risk.READ, implemented=True, gap_id="UIAPI-03"
    )

    @mcp.tool(
        name=meta_gri.name,
        description=tool_description(
            meta_gri, "Best-effort requestable catalog via SCIM Roles/Entitlements (requestable=true)."
        ),
    )
    async def get_requestable_items(
        identity_id: str,
        start: int | None = None,
        count: int | None = None,
        raw: bool = False,
    ) -> dict[str, Any]:
        from iiq_mcp.tools.agent_helpers import scim_list

        def _client_filter_requestable(envelope: dict[str, Any]) -> dict[str, Any]:
            items = envelope.get("items") or []
            filtered = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                flag = item.get("requestable")
                if flag is True or str(flag).lower() in {"true", "1", "yes"}:
                    filtered.append(item)
            # If IIQ omits the attribute entirely, keep unfiltered catalog (lab often empty).
            if not filtered and items:
                return {**envelope, "requestableFilterApplied": False}
            return {
                **envelope,
                "items": filtered,
                "returned": len(filtered),
                "requestableFilterApplied": True,
            }

        async def _run() -> Any:
            note = (
                "IIQ SCIM often rejects 'requestable eq true'; listing then client-filter when present."
            )
            roles: dict[str, Any]
            ents: dict[str, Any]
            try:
                roles = await scim_list(
                    client, "/Roles", filter="requestable eq true", start=start, count=count, raw=raw
                )
                ents = await scim_list(
                    client,
                    "/Entitlements",
                    filter="requestable eq true",
                    start=start,
                    count=count,
                    raw=raw,
                )
                note = "Filtered server-side by requestable=true."
            except Exception:
                roles = _client_filter_requestable(
                    await scim_list(client, "/Roles", start=start, count=count, raw=raw)
                )
                ents = _client_filter_requestable(
                    await scim_list(client, "/Entitlements", start=start, count=count, raw=raw)
                )
            # Agent ManagedAttribute / Bundle catalog (SCIM Entitlements is often empty in this lab).
            role_n = len((roles or {}).get("items") or []) if isinstance(roles, dict) else 0
            ent_n = len((ents or {}).get("items") or []) if isinstance(ents, dict) else 0
            if role_n == 0 or ent_n == 0:
                try:
                    s, c = clamp_page(start, count)
                    if role_n == 0:
                        agent_roles = await agent_get(
                            client, "/roles", params={"requestable": "true", "limit": c}
                        )
                        items = []
                        if isinstance(agent_roles, dict):
                            items = agent_roles.get("items") or []
                        elif isinstance(agent_roles, list):
                            items = agent_roles
                        roles = list_envelope(
                            [trim_generic(i, raw=raw) for i in items if isinstance(i, dict)],
                            start=s,
                            count=c,
                            total=len(items),
                            raw=raw,
                        )
                        roles["source"] = "agent"
                    if ent_n == 0:
                        agent_ents = await agent_get(
                            client,
                            "/entitlements",
                            params={"requestable": "true", "limit": c},
                        )
                        items = []
                        if isinstance(agent_ents, dict):
                            items = agent_ents.get("items") or []
                        elif isinstance(agent_ents, list):
                            items = agent_ents
                        ents = list_envelope(
                            [trim_generic(i, raw=raw) for i in items if isinstance(i, dict)],
                            start=s,
                            count=c,
                            total=len(items),
                            raw=raw,
                        )
                        ents["source"] = "agent"
                    note = "SCIM catalog empty/partial; filled from Meridian agent entitlements/roles."
                except Exception as exc:
                    note = f"{note} Agent fallback failed: {exc}"
            return {
                "identity_id": identity_id,
                "roles": roles,
                "entitlements": ents,
                "note": note,
            }

        return await run_tool(
            meta_gri, {"identity_id": identity_id, "start": start, "count": count, "raw": raw}, _run, audit=audit
        )

    meta_can = ToolMeta(
        name="cancel_access_request",
        phase=2,
        risk=Risk.LOW_WRITE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-03",
    )

    @mcp.tool(
        name=meta_can.name,
        description=tool_description(
            meta_can, "Cancel by terminating associated workflow case / task when IIQ allows DELETE."
        ),
    )
    async def cancel_access_request(request_id: str, justification: str | None = None) -> dict[str, Any]:
        async def _run() -> Any:
            try:
                _, _ = await client.request(
                    "DELETE",
                    f"/scim/v2/LaunchedWorkflows/{encode_path_segment(request_id)}",
                    accept="application/scim+json, application/json",
                )
                return {"request_id": request_id, "cancelled": True, "via": "LaunchedWorkflows"}
            except Exception as exc:
                raise IiqMcpError(
                    McpErrorBody(
                        code=ErrorCode.DOWNSTREAM,
                        message=f"Cancel failed — terminate via terminate_workflow_case or UI. detail={exc}",
                        gap_id="UIAPI-03",
                    )
                )

        return await run_tool(
            meta_can, {"request_id": request_id, "justification": justification}, _run, audit=audit
        )

    # —— Work item writes ——
    meta_cwi = ToolMeta(
        name="complete_work_item",
        phase=2,
        risk=Risk.LOW_WRITE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-04",
    )

    @mcp.tool(
        name=meta_cwi.name,
        description=tool_description(meta_cwi, "Approve/reject work item via Meridian agent decide."),
    )
    async def complete_work_item(
        item_id: str,
        decision: str,
        form_data: dict[str, Any] | None = None,
        comment: str | None = None,
        justification: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {"decision": decision, "comment": comment or justification}
            if form_data:
                body["formData"] = form_data
            return await agent_post(client, f"/workItems/{encode_path_segment(item_id)}/decide", json_body=body)

        return await run_tool(
            meta_cwi,
            {
                "item_id": item_id,
                "decision": decision,
                "form_data": form_data,
                "comment": comment,
                "justification": justification,
            },
            _run,
            audit=audit,
        )

    meta_fwi = ToolMeta(
        name="forward_work_item",
        phase=2,
        risk=Risk.LOW_WRITE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-42",
    )

    @mcp.tool(
        name=meta_fwi.name,
        description=tool_description(
            meta_fwi, "Forward a work item to a new owner via Meridian agent Custom API."
        ),
    )
    async def forward_work_item(
        item_id: str, new_owner: str, justification: str | None = None
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {"newOwner": new_owner}
            if justification:
                body["comment"] = justification
            return await agent_post(
                client,
                f"/workItems/{encode_path_segment(item_id)}/forward",
                json_body=body,
            )

        return await run_tool(
            meta_fwi,
            {"item_id": item_id, "new_owner": new_owner, "justification": justification},
            _run,
            audit=audit,
        )

    meta_ewi = ToolMeta(
        name="escalate_work_item",
        phase=2,
        risk=Risk.LOW_WRITE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-04",
    )

    @mcp.tool(
        name=meta_ewi.name,
        description=tool_description(meta_ewi, "Escalate work item via OOTB REST (best-effort)."),
    )
    async def escalate_work_item(item_id: str, justification: str | None = None) -> dict[str, Any]:
        async def _run() -> Any:
            for path in (
                f"/workItems/{encode_path_segment(item_id)}/escalate",
                f"/workitem/{encode_path_segment(item_id)}/escalate",
            ):
                try:
                    return await client.rest_post(path, json_body={"comment": justification})
                except Exception:
                    continue
            raise IiqMcpError(
                McpErrorBody(
                    code=ErrorCode.NOT_IMPLEMENTED,
                    http_status=501,
                    message="Escalate endpoint not available on this IIQ build.",
                    gap_id="UIAPI-04",
                )
            )

        return await run_tool(
            meta_ewi, {"item_id": item_id, "justification": justification}, _run, audit=audit
        )

    # —— Cert writes ——
    meta_mcd = ToolMeta(
        name="make_certification_decision",
        phase=3,
        risk=Risk.COMPLIANCE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-05",
    )

    @mcp.tool(
        name=meta_mcd.name,
        description=tool_description(
            meta_mcd, "Decide certification item (approve|revoke|mitigate|acknowledge) via Meridian agent."
        ),
    )
    async def make_certification_decision(
        cert_id: str,
        item_id: str,
        decision: str,
        comment: str | None = None,
        justification: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            data = await agent_post(
                client,
                f"/certifications/items/{encode_path_segment(item_id)}/decide",
                json_body={"decision": decision, "comment": comment or justification},
            )
            return {"cert_id": cert_id, **(data if isinstance(data, dict) else {"result": data})}

        return await run_tool(
            meta_mcd,
            {
                "cert_id": cert_id,
                "item_id": item_id,
                "decision": decision,
                "comment": comment,
                "justification": justification,
            },
            _run,
            audit=audit,
        )

    meta_soc = ToolMeta(
        name="sign_off_certification",
        phase=3,
        risk=Risk.COMPLIANCE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-05",
    )

    @mcp.tool(name=meta_soc.name, description=tool_description(meta_soc, "Sign off certification via agent."))
    async def sign_off_certification(cert_id: str, justification: str | None = None) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client, f"/certifications/{encode_path_segment(cert_id)}/sign", json_body={}
            )

        return await run_tool(
            meta_soc, {"cert_id": cert_id, "justification": justification}, _run, audit=audit
        )

    meta_lcc = ToolMeta(
        name="launch_certification_campaign",
        phase=3,
        risk=Risk.COMPLIANCE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-31",
    )

    @mcp.tool(
        name=meta_lcc.name,
        description=tool_description(
            meta_lcc,
            "Alias for create_certification_campaign: create CertificationDefinition from template; "
            "optional generate_now. Prefer create_certification_campaign for new callers.",
        ),
    )
    async def launch_certification_campaign(
        name: str | None = None,
        definition: dict[str, Any] | None = None,
        template: str | None = None,
        description: str | None = None,
        generate_now: bool = False,
        justification: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = dict(definition or {})
            campaign_name = name or body.get("name") or body.get("campaignName")
            if not campaign_name:
                raise IiqMcpError(
                    McpErrorBody(
                        code=ErrorCode.VALIDATION,
                        http_status=400,
                        message="launch_certification_campaign requires name (or definition.name)",
                        gap_id="UIAPI-31",
                    )
                )
            body["name"] = campaign_name
            if template:
                body["template"] = template
            elif "template" not in body and body.get("templateName"):
                body["template"] = body.get("templateName")
            if description:
                body["description"] = description
            body["generateNow"] = generate_now or bool(body.get("generateNow"))
            return await agent_post(client, "/certifications/campaigns", json_body=body)

        return await run_tool(
            meta_lcc,
            {
                "name": name,
                "definition": definition,
                "template": template,
                "description": description,
                "generate_now": generate_now,
                "justification": justification,
            },
            _run,
            audit=audit,
        )

    meta_ec = ToolMeta(
        name="escalate_certification",
        phase=3,
        risk=Risk.COMPLIANCE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-05",
    )

    @mcp.tool(
        name=meta_ec.name,
        description=tool_description(meta_ec, "Escalate / reassign certification owner via REST best-effort."),
    )
    async def escalate_certification(
        cert_id: str, new_owner: str, justification: str | None = None
    ) -> dict[str, Any]:
        async def _run() -> Any:
            for path in (
                f"/certifications/{encode_path_segment(cert_id)}/escalate",
                f"/certification/{encode_path_segment(cert_id)}/forward",
            ):
                try:
                    return await client.rest_post(
                        path, json_body={"owner": new_owner, "newOwner": new_owner, "comment": justification}
                    )
                except Exception:
                    continue
            raise IiqMcpError(
                McpErrorBody(
                    code=ErrorCode.NOT_IMPLEMENTED,
                    http_status=501,
                    message="Certification escalate REST path not found on this IIQ.",
                    gap_id="UIAPI-05",
                )
            )

        return await run_tool(
            meta_ec,
            {"cert_id": cert_id, "new_owner": new_owner, "justification": justification},
            _run,
            audit=audit,
        )

    # —— SoD / policy ——
    meta_cpve = ToolMeta(
        name="create_policy_violation_exception",
        phase=3,
        risk=Risk.COMPLIANCE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-06",
    )

    @mcp.tool(
        name=meta_cpve.name,
        description=tool_description(meta_cpve, "Mitigate SoD violation via Meridian agent."),
    )
    async def create_policy_violation_exception(
        violation_id: str,
        justification: str,
        expiration: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client,
                f"/sod/violations/{encode_path_segment(violation_id)}/mitigate",
                json_body={"comment": justification, "expiration": expiration},
            )

        return await run_tool(
            meta_cpve,
            {"violation_id": violation_id, "justification": justification, "expiration": expiration},
            _run,
            audit=audit,
        )

    meta_up = ToolMeta(
        name="update_policy",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
    )

    @mcp.tool(
        name=meta_up.name,
        description=tool_description(
            meta_up, "Update policy via objects/import XML when provided; otherwise REST PATCH best-effort."
        ),
    )
    async def update_policy(
        policy_id: str, patch: dict[str, Any], justification: str | None = None
    ) -> dict[str, Any]:
        async def _run() -> Any:
            if patch.get("xml"):
                return await agent_post(client, "/objects/import", json_body={"xml": patch["xml"]})
            for path in (
                f"/policies/{encode_path_segment(policy_id)}",
                f"/policy/{encode_path_segment(policy_id)}",
            ):
                try:
                    _, body = await client.request("PUT", f"/rest{path}", json_body=patch)
                    return body
                except Exception:
                    continue
            raise map_http_error(501, {"message": "Policy update requires XML import or UI/SSB."})

        return await run_tool(
            meta_up,
            {"policy_id": policy_id, "patch": patch, "justification": justification},
            _run,
            audit=audit,
        )

    # —— Populations ——
    meta_lp = ToolMeta(
        name="list_populations", phase=2, risk=Risk.READ, implemented=True, gap_id="UIAPI-09"
    )

    @mcp.tool(name=meta_lp.name, description=tool_description(meta_lp, "List populations (GroupDefinition) via agent."))
    async def list_populations(start: int | None = None, count: int | None = None, raw: bool = False) -> dict[str, Any]:
        async def _run() -> Any:
            _, c = clamp_page(start, count)
            data = await agent_get(client, "/populations", params={"limit": c})
            items = data if isinstance(data, list) else []
            return list_envelope(items, start=start or 0, count=c, total=len(items), raw=raw)

        return await run_tool(
            meta_lp, {"start": start, "count": count, "raw": raw}, _run, audit=audit
        )

    meta_gpd = ToolMeta(
        name="get_population_definition", phase=2, risk=Risk.READ, implemented=True, gap_id="UIAPI-09"
    )

    @mcp.tool(name=meta_gpd.name, description=tool_description(meta_gpd, "Get population filter via agent."))
    async def get_population_definition(pop_id: str, raw: bool = False) -> dict[str, Any]:
        async def _run() -> Any:
            data = await agent_get(client, f"/populations/{encode_path_segment(pop_id)}")
            return data if raw else trim_generic(data if isinstance(data, dict) else {"value": data})

        return await run_tool(meta_gpd, {"pop_id": pop_id, "raw": raw}, _run, audit=audit)

    meta_ppm = ToolMeta(
        name="preview_population_membership", phase=2, risk=Risk.READ, implemented=True, gap_id="UIAPI-09"
    )

    @mcp.tool(
        name=meta_ppm.name,
        description=tool_description(
            meta_ppm,
            "Preview who matches: returns population filter text; membership expansion not always available.",
        ),
    )
    async def preview_population_membership(
        pop_id: str, start: int | None = None, count: int | None = None, raw: bool = False
    ) -> dict[str, Any]:
        async def _run() -> Any:
            lim = count if count is not None else 25
            try:
                members = await agent_get(
                    client,
                    f"/populations/{encode_path_segment(pop_id)}/members",
                    params={"limit": lim},
                )
                return members if raw else members
            except Exception as exc:
                definition = await agent_get(client, f"/populations/{encode_path_segment(pop_id)}")
                return {
                    "population": definition,
                    "members": [],
                    "note": f"Membership expansion unavailable ({exc}); filter definition returned only.",
                    "start": start,
                    "count": count,
                    "raw": raw,
                }

        return await run_tool(
            meta_ppm, {"pop_id": pop_id, "start": start, "count": count, "raw": raw}, _run, audit=audit
        )

    meta_cp = ToolMeta(
        name="create_population",
        phase=3,
        risk=Risk.COMPLIANCE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-09",
    )

    @mcp.tool(name=meta_cp.name, description=tool_description(meta_cp, "Create/update population via agent."))
    async def create_population(
        name: str,
        filter_definition: str | None = None,
        filter: str | None = None,
        description: str | None = None,
        justification: str | None = None,
    ) -> dict[str, Any]:
        resolved_filter = filter_definition or filter

        async def _run() -> Any:
            body: dict[str, Any] = {"name": name, "filter": resolved_filter}
            if description:
                body["description"] = description
            return await agent_post(client, "/populations", json_body=body)

        return await run_tool(
            meta_cp,
            {
                "name": name,
                "filter_definition": resolved_filter,
                "description": description,
                "justification": justification,
            },
            _run,
            audit=audit,
        )

    meta_upp = ToolMeta(
        name="update_population",
        phase=3,
        risk=Risk.COMPLIANCE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-09",
    )

    @mcp.tool(
        name=meta_upp.name,
        description=tool_description(meta_upp, "Update population by re-POSTing name+filter to agent."),
    )
    async def update_population(
        pop_id: str, filter_definition: str, justification: str | None = None
    ) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client, "/populations", json_body={"name": pop_id, "filter": filter_definition}
            )

        return await run_tool(
            meta_upp,
            {"pop_id": pop_id, "filter_definition": filter_definition, "justification": justification},
            _run,
            audit=audit,
        )

    # —— Audit ——
    meta_sae = ToolMeta(
        name="search_audit_events", phase=1, risk=Risk.READ, implemented=True, gap_id="UIAPI-18"
    )

    @mcp.tool(name=meta_sae.name, description=tool_description(meta_sae, "Search audit events via Meridian agent."))
    async def search_audit_events(
        identity_id: str | None = None,
        action: str | None = None,
        start: int | None = None,
        count: int | None = None,
        raw: bool = False,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            _, c = clamp_page(start, count)
            params: dict[str, Any] = {"limit": c}
            if action:
                params["action"] = action
            rows = await agent_get(client, "/audit/events", params=params)
            items = rows if isinstance(rows, list) else []
            if identity_id:
                items = [
                    r
                    for r in items
                    if identity_id in str(r.get("target", "")) or identity_id in str(r.get("source", ""))
                ]
            s = start or 0
            return list_envelope(items[s : s + c] if not identity_id else items[:c], start=s, count=c, total=len(items), raw=raw)

        return await run_tool(
            meta_sae,
            {"identity_id": identity_id, "action": action, "start": start, "count": count, "raw": raw},
            _run,
            audit=audit,
        )

    meta_gae = ToolMeta(
        name="get_audit_event_detail", phase=1, risk=Risk.READ, implemented=True, gap_id="UIAPI-18"
    )

    @mcp.tool(
        name=meta_gae.name,
        description=tool_description(meta_gae, "Fetch one audit event by id from agent search results."),
    )
    async def get_audit_event_detail(event_id: str, raw: bool = False) -> dict[str, Any]:
        async def _run() -> Any:
            rows = await agent_get(client, "/audit/events", params={"limit": 200})
            items = rows if isinstance(rows, list) else []
            for r in items:
                if str(r.get("id")) == event_id:
                    return r if raw else trim_generic(r)
            raise map_http_error(404, {"message": f"Audit event not found in recent window: {event_id}"})

        return await run_tool(meta_gae, {"event_id": event_id, "raw": raw}, _run, audit=audit)

    # —— Batch ——
    meta_sbr = ToolMeta(
        name="submit_batch_request",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-19",
    )

    @mcp.tool(
        name=meta_sbr.name,
        description=tool_description(
            meta_sbr,
            "Create BatchRequest object via agent. Always prefer dry_run=true first — does not execute rows until task runs.",
        ),
    )
    async def submit_batch_request(
        type: str,
        csv_payload: str,
        dry_run: bool = True,
        name: str | None = None,
        justification: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            if dry_run:
                lines = [ln for ln in csv_payload.splitlines() if ln.strip()]
                return {
                    "dry_run": True,
                    "type": type,
                    "row_count": max(0, len(lines) - 1) if lines else 0,
                    "sample_header": lines[0] if lines else None,
                    "note": "Re-call with dry_run=false to create BatchRequest object.",
                }
            return await agent_post(
                client,
                "/batchRequests",
                json_body={"name": name or f"mcp-batch-{type}", "payload": csv_payload, "type": type},
            )

        return await run_tool(
            meta_sbr,
            {
                "type": type,
                "csv_payload": csv_payload[:500],
                "dry_run": dry_run,
                "name": name,
                "justification": justification,
            },
            _run,
            audit=audit,
        )

    meta_lbr = ToolMeta(
        name="list_batch_requests", phase=4, risk=Risk.READ, implemented=True, gap_id="UIAPI-19"
    )

    @mcp.tool(
        name=meta_lbr.name,
        description=tool_description(meta_lbr, "Best-effort list BatchRequest via REST or objects export probe."),
    )
    async def list_batch_requests(
        start: int | None = None, count: int | None = None, raw: bool = False
    ) -> dict[str, Any]:
        async def _run() -> Any:
            s, c = clamp_page(start, count)
            try:
                payload = await client.rest_get("/batchRequests")
                items = payload if isinstance(payload, list) else []
                if isinstance(payload, dict):
                    for key in ("objects", "items", "results"):
                        if isinstance(payload.get(key), list):
                            items = payload[key]
                            break
                page = items[s : s + c]
                return list_envelope([trim_generic(i, raw=raw) for i in page if isinstance(i, dict)], start=s, count=c, total=len(items), raw=raw)
            except Exception as exc:
                return {"items": [], "note": f"batchRequests list unavailable: {exc}"}

        return await run_tool(
            meta_lbr, {"start": start, "count": count, "raw": raw}, _run, audit=audit
        )

    meta_gbr = ToolMeta(
        name="get_batch_request_status", phase=4, risk=Risk.READ, implemented=True, gap_id="UIAPI-19"
    )

    @mcp.tool(name=meta_gbr.name, description=tool_description(meta_gbr, "Get BatchRequest by id via REST best-effort."))
    async def get_batch_request_status(batch_id: str, raw: bool = False) -> dict[str, Any]:
        async def _run() -> Any:
            data = await client.rest_get(f"/batchRequests/{encode_path_segment(batch_id)}")
            return data if raw else trim_generic(data if isinstance(data, dict) else {"value": data})

        return await run_tool(meta_gbr, {"batch_id": batch_id, "raw": raw}, _run, audit=audit)

    # —— Admin reads ——
    meta_lc = ToolMeta(
        name="list_capabilities", phase=1, risk=Risk.READ, implemented=True, gap_id="UIAPI-11"
    )

    @mcp.tool(
        name=meta_lc.name,
        description=tool_description(
            meta_lc, "List IIQ Capability objects (names for assign_identity_capability)."
        ),
    )
    async def list_capabilities(
        start: int | None = None, count: int | None = None, raw: bool = False, limit: int | None = None
    ) -> dict[str, Any]:
        async def _run() -> Any:
            lim = limit if limit is not None else (count if count is not None else 100)
            data = await agent_get(client, "/capabilities", params={"limit": lim})
            if raw:
                return data
            items = data if isinstance(data, list) else []
            if isinstance(data, dict):
                items = data.get("items") or data.get("capabilities") or []
                if not items and data.get("name"):
                    items = [data]
            s, c = clamp_page(start, lim)
            # agent returns bare list already limited
            if isinstance(data, list):
                return list_envelope(
                    [trim_generic(i, raw=False) for i in data if isinstance(i, dict)],
                    start=0,
                    count=lim,
                    total=len(data),
                    raw=raw,
                )
            return list_envelope(
                [trim_generic(i, raw=False) for i in items if isinstance(i, dict)],
                start=s,
                count=c,
                total=len(items),
                raw=raw,
            )

        return await run_tool(
            meta_lc, {"start": start, "count": count, "limit": limit, "raw": raw}, _run, audit=audit
        )

    meta_pe = ToolMeta(
        name="promote_entitlements",
        phase=3,
        risk=Risk.COMPLIANCE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-28",
    )

    @mcp.tool(
        name=meta_pe.name,
        description=tool_description(
            meta_pe,
            "Promote Link entitlement values into ManagedAttribute catalog via Meridian agent.",
        ),
    )
    async def promote_entitlements(
        application: str,
        attribute: str | None = None,
        justification: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {"application": application}
            if attribute:
                body["attribute"] = attribute
            return await agent_post(client, "/entitlements/promote", json_body=body)

        return await run_tool(
            meta_pe,
            {
                "application": application,
                "attribute": attribute,
                "justification": justification,
            },
            _run,
            audit=audit,
        )

    meta_arp = ToolMeta(
        name="attach_role_profile",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-29",
    )

    @mcp.tool(
        name=meta_arp.name,
        description=tool_description(
            meta_arp,
            "Attach entitlement Profile(s) to a Bundle role (application + attribute/value constraints).",
        ),
    )
    async def attach_role_profile(
        role_name: str,
        profiles: list[dict[str, Any]] | None = None,
        application: str | None = None,
        attribute: str | None = None,
        value: str | None = None,
        replace: bool = False,
        justification: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {"replace": replace}
            if profiles:
                body["profiles"] = profiles
            else:
                if not application or not value:
                    raise IiqMcpError(
                        McpErrorBody(
                            code=ErrorCode.VALIDATION,
                            http_status=400,
                            message="attach_role_profile requires profiles[] or application+value",
                            gap_id="UIAPI-29",
                        )
                    )
                body["application"] = application
                body["attribute"] = attribute or "itAccess"
                body["value"] = value
            return await agent_post(
                client, f"/roles/{encode_path_segment(role_name)}/profiles", json_body=body
            )

        return await run_tool(
            meta_arp,
            {
                "role_name": role_name,
                "profiles": profiles,
                "application": application,
                "attribute": attribute,
                "value": value,
                "replace": replace,
                "justification": justification,
            },
            _run,
            audit=audit,
        )

    meta_gic = ToolMeta(
        name="get_identity_capabilities", phase=1, risk=Risk.READ, implemented=True, gap_id="UIAPI-11"
    )

    @mcp.tool(
        name=meta_gic.name,
        description=tool_description(meta_gic, "Read capabilities from SCIM User sailpoint extension."),
    )
    async def get_identity_capabilities(
        identity_id: str | None = None,
        raw: bool = False,
        id: str | None = None,
    ) -> dict[str, Any]:
        from iiq_mcp.tools.phase1_identity import resolve_user

        resolved = (identity_id or id or "").strip()
        if not resolved:
            raise map_http_error(400, {"message": "identity_id (or id) is required"})

        async def _run() -> Any:
            user = await resolve_user(client, resolved)
            sail = user.get("urn:ietf:params:scim:schemas:sailpoint:1.0:User") or {}
            caps = sail.get("capabilities") or user.get("capabilities") or []
            return {
                "id": user.get("id"),
                "userName": user.get("userName"),
                "capabilities": caps,
                "rawUser": user if raw else None,
            }

        return await run_tool(
            meta_gic, {"identity_id": resolved, "id": id, "raw": raw}, _run, audit=audit
        )

    meta_ls = ToolMeta(name="list_scopes", phase=1, risk=Risk.READ, implemented=True)

    @mcp.tool(name=meta_ls.name, description=tool_description(meta_ls, "List scopes via REST /scopes best-effort."))
    async def list_scopes(
        start: int | None = None, count: int | None = None, raw: bool = False
    ) -> dict[str, Any]:
        async def _run() -> Any:
            s, c = clamp_page(start, count)
            try:
                payload = await client.rest_get("/scopes")
            except Exception as exc:
                return {"items": [], "note": str(exc)}
            items = payload if isinstance(payload, list) else []
            if isinstance(payload, dict):
                for key in ("objects", "items", "scopes"):
                    if isinstance(payload.get(key), list):
                        items = payload[key]
                        break
            page = items[s : s + c]
            return list_envelope([trim_generic(i, raw=raw) for i in page if isinstance(i, dict)], start=s, count=c, total=len(items), raw=raw)

        return await run_tool(
            meta_ls, {"start": start, "count": count, "raw": raw}, _run, audit=audit
        )

    meta_gsc = ToolMeta(
        name="get_system_config", phase=1, risk=Risk.READ, implemented=True, gap_id="UIAPI-24"
    )

    @mcp.tool(name=meta_gsc.name, description=tool_description(meta_gsc, "Read system config via Meridian agent (redacted)."))
    async def get_system_config(key: str | None = None, raw: bool = False) -> dict[str, Any]:
        async def _run() -> Any:
            params = {"key": key} if key else None
            data = await agent_get(client, "/system/config", params=params)
            return data if raw else trim_generic(data if isinstance(data, dict) else {"value": data})

        return await run_tool(meta_gsc, {"key": key, "raw": raw}, _run, audit=audit)
