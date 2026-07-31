"""Identity writes, app writes, provisioning, passwords, tasks, rules, reports."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from iiq_mcp.client.http import IiqHttpClient, encode_path_segment
from iiq_mcp.errors import IiqMcpError, McpErrorBody, ErrorCode, map_http_error
from iiq_mcp.shaping import clamp_page, list_envelope, scim_page_params, scim_resources, scim_total, trim_generic, trim_task_result
from iiq_mcp.tools.agent_helpers import agent_get, agent_post, scim_get_by_id_or_filter, scim_list, scim_mutate
from iiq_mcp.tools.meta import Risk, ToolMeta, run_tool, tool_description
from iiq_mcp.tools.phase1_identity import resolve_user


def register(mcp: FastMCP, client: IiqHttpClient, **ctx: Any) -> None:
    audit = ctx.get("audit")

    # —— Identity writes ——
    meta_uia = ToolMeta(
        name="update_identity_attribute",
        phase=4,
        risk=Risk.PROVISIONING,
        implemented=True,
        requires_confirmation=True,
    )

    @mcp.tool(
        name=meta_uia.name,
        description=tool_description(meta_uia, "PATCH one SCIM User attribute."),
    )
    async def update_identity_attribute(
        id: str, attribute: str, value: Any, justification: str | None = None
    ) -> dict[str, Any]:
        async def _run() -> Any:
            user = await resolve_user(client, id)
            uid = user.get("id") or id
            patch_body = {
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
                "Operations": [{"op": "replace", "path": attribute, "value": value}],
            }
            try:
                return await scim_mutate(
                    client,
                    "PATCH",
                    f"/Users/{encode_path_segment(uid)}",
                    json_body=patch_body,
                )
            except Exception as patch_exc:
                # IIQ 8.5 SCIM Users often returns 405 for PATCH — fall back to PUT merge.
                merged = dict(user)
                merged[attribute] = value
                for drop in ("meta", "password"):
                    merged.pop(drop, None)
                if "schemas" not in merged:
                    merged["schemas"] = ["urn:ietf:params:scim:schemas:core:2.0:User"]
                try:
                    out = await scim_mutate(
                        client,
                        "PUT",
                        f"/Users/{encode_path_segment(uid)}",
                        json_body=merged,
                    )
                    if isinstance(out, dict):
                        out = {
                            **out,
                            "_writeMode": "PUT",
                            "_patchError": str(patch_exc),
                        }
                    return out
                except Exception as put_exc:
                    raise map_http_error(
                        405,
                        {
                            "message": "SCIM User PATCH unsupported; PUT fallback also failed",
                            "detail": f"patch={patch_exc}; put={put_exc}",
                        },
                    )

        return await run_tool(
            meta_uia,
            {"id": id, "attribute": attribute, "value": value, "justification": justification},
            _run,
            audit=audit,
        )

    meta_sip = ToolMeta(
        name="set_identity_password",
        phase=4,
        risk=Risk.PROVISIONING,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-12",
    )

    @mcp.tool(
        name=meta_sip.name,
        description=tool_description(meta_sip, "Set identity password via Meridian agent (passwordResetEnabled)."),
    )
    async def set_identity_password(
        id: str, new_password: str, justification: str | None = None
    ) -> dict[str, Any]:
        async def _run() -> Any:
            user = await resolve_user(client, id)
            name = user.get("userName") or id
            return await agent_post(
                client,
                f"/identities/{encode_path_segment(name)}/password",
                json_body={"op": "set", "password": new_password},
            )

        return await run_tool(
            meta_sip, {"id": id, "new_password": "***", "justification": justification}, _run, audit=audit
        )

    async def _set_active(id: str, active: bool) -> Any:
        user = await resolve_user(client, id)
        uid = user.get("id") or id
        return await scim_mutate(
            client, "PATCH", f"/Users/{encode_path_segment(uid)}", json_body={"active": active}
        )

    meta_di = ToolMeta(
        name="disable_identity", phase=4, risk=Risk.PROVISIONING, implemented=True, requires_confirmation=True
    )

    @mcp.tool(name=meta_di.name, description=tool_description(meta_di, "Disable identity (SCIM active=false)."))
    async def disable_identity(id: str, justification: str | None = None) -> dict[str, Any]:
        async def _run() -> Any:
            return await _set_active(id, False)

        return await run_tool(
            meta_di, {"id": id, "justification": justification}, _run, audit=audit
        )

    meta_ei = ToolMeta(
        name="enable_identity", phase=4, risk=Risk.PROVISIONING, implemented=True, requires_confirmation=True
    )

    @mcp.tool(name=meta_ei.name, description=tool_description(meta_ei, "Enable identity (SCIM active=true)."))
    async def enable_identity(id: str, justification: str | None = None) -> dict[str, Any]:
        async def _run() -> Any:
            return await _set_active(id, True)

        return await run_tool(
            meta_ei, {"id": id, "justification": justification}, _run, audit=audit
        )

    meta_corr = ToolMeta(
        name="correlate_account_to_identity",
        phase=4,
        risk=Risk.PROVISIONING,
        implemented=True,
        requires_confirmation=True,
    )

    @mcp.tool(
        name=meta_corr.name,
        description=tool_description(
            meta_corr, "Manual correlation: PATCH SCIM Account identity reference."
        ),
    )
    async def correlate_account_to_identity(
        account_id: str, identity_id: str, justification: str | None = None
    ) -> dict[str, Any]:
        async def _run() -> Any:
            user = await resolve_user(client, identity_id)
            return await scim_mutate(
                client,
                "PATCH",
                f"/Accounts/{encode_path_segment(account_id)}",
                json_body={
                    "identity": {
                        "value": user.get("id"),
                        "displayName": user.get("displayName") or user.get("userName"),
                    }
                },
            )

        return await run_tool(
            meta_corr,
            {"account_id": account_id, "identity_id": identity_id, "justification": justification},
            _run,
            audit=audit,
        )

    # —— App writes ——
    meta_ta = ToolMeta(
        name="trigger_aggregation",
        phase=2,
        risk=Risk.LOW_WRITE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-01",
    )

    @mcp.tool(
        name=meta_ta.name,
        description=tool_description(
            meta_ta,
            "Trigger aggregation via Meridian tasks/run. Pass task_name or default Account Aggregation.",
        ),
    )
    async def trigger_aggregation(
        app_id: str,
        full_or_delta: str = "full",
        task_name: str | None = None,
        justification: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            name = task_name or "Account Aggregation"
            body = {
                "taskName": name,
                "sync": False,
                "args": {"applications": app_id, "fullOrDelta": full_or_delta},
            }
            data = await client.plugin_post("/mnbToolkit/tasks/run", json_body=body)
            return {
                "app_id": app_id,
                "full_or_delta": full_or_delta,
                "taskName": name,
                "response": data,
                "poll_with": "get_task_result",
                "poll_arg": "task_id",
                "poll_aliases": ["task_id", "task_result_id"],
            }

        return await run_tool(
            meta_ta,
            {
                "app_id": app_id,
                "full_or_delta": full_or_delta,
                "task_name": task_name,
                "justification": justification,
            },
            _run,
            audit=audit,
        )

    meta_uac = ToolMeta(
        name="update_application_config",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-08",
    )

    @mcp.tool(
        name=meta_uac.name,
        description=tool_description(
            meta_uac, "Patch application config via Meridian agent (advancedOpsEnabled)."
        ),
    )
    async def update_application_config(
        app_id: str, config_patch: dict[str, Any], justification: str | None = None
    ) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client,
                f"/applications/{encode_path_segment(app_id)}/config",
                json_body=config_patch,
            )

        return await run_tool(
            meta_uac,
            {"app_id": app_id, "config_patch": config_patch, "justification": justification},
            _run,
            audit=audit,
        )

    # Upgrade get_application_health in place? Already registered in phase1 as stub.
    # Re-register isn't possible easily — update phase1_apps instead later.

    # —— Provisioning ——
    meta_lpt = ToolMeta(name="list_provisioning_transactions", phase=4, risk=Risk.READ, implemented=True)

    @mcp.tool(
        name=meta_lpt.name,
        description=tool_description(meta_lpt, "List provisioning transactions via REST best-effort."),
    )
    async def list_provisioning_transactions(
        identity_id: str | None = None,
        status: str | None = None,
        start: int | None = None,
        count: int | None = None,
        raw: bool = False,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            s, c = clamp_page(start, count)
            items: list[Any] = []
            for path in ("/provisioningTransactions", "/provisioning/transactions", "/provisioning"):
                try:
                    payload = await client.rest_get(path)
                    if isinstance(payload, list):
                        items = payload
                    elif isinstance(payload, dict):
                        for key in ("objects", "items", "transactions", "results"):
                            if isinstance(payload.get(key), list):
                                items = payload[key]
                                break
                    if items:
                        break
                except Exception:
                    continue
            if identity_id:
                items = [i for i in items if isinstance(i, dict) and identity_id in str(i)]
            if status:
                items = [
                    i
                    for i in items
                    if isinstance(i, dict) and status.lower() in str(i.get("status", "")).lower()
                ]
            page = items[s : s + c]
            return list_envelope(
                [trim_generic(i, raw=raw) for i in page if isinstance(i, dict)],
                start=s,
                count=c,
                total=len(items),
                raw=raw,
            )

        return await run_tool(
            meta_lpt,
            {"identity_id": identity_id, "status": status, "start": start, "count": count, "raw": raw},
            _run,
            audit=audit,
        )

    meta_gpt = ToolMeta(name="get_provisioning_transaction_status", phase=4, risk=Risk.READ, implemented=True)

    @mcp.tool(
        name=meta_gpt.name,
        description=tool_description(meta_gpt, "Get one provisioning transaction by id (REST)."),
    )
    async def get_provisioning_transaction_status(transaction_id: str, raw: bool = False) -> dict[str, Any]:
        async def _run() -> Any:
            for path in (
                f"/provisioningTransactions/{encode_path_segment(transaction_id)}",
                f"/provisioning/transactions/{encode_path_segment(transaction_id)}",
            ):
                try:
                    data = await client.rest_get(path)
                    return data if raw else trim_generic(data if isinstance(data, dict) else {"value": data})
                except Exception:
                    continue
            raise map_http_error(404, {"message": f"Provisioning transaction not found: {transaction_id}"})

        return await run_tool(
            meta_gpt, {"transaction_id": transaction_id, "raw": raw}, _run, audit=audit
        )

    meta_ca = ToolMeta(
        name="create_account", phase=4, risk=Risk.PROVISIONING, implemented=True, requires_confirmation=True
    )

    @mcp.tool(name=meta_ca.name, description=tool_description(meta_ca, "Create SCIM Account for an identity/app."))
    async def create_account(
        identity_id: str,
        app_id: str,
        attributes: dict[str, Any] | None = None,
        justification: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            user = await resolve_user(client, identity_id)
            body = {
                "schemas": ["urn:ietf:params:scim:schemas:sailpoint:1.0:Application:Account"],
                "identity": {"value": user.get("id")},
                "application": {"value": app_id, "displayName": app_id},
                **(attributes or {}),
            }
            return await scim_mutate(client, "POST", "/Accounts", json_body=body)

        return await run_tool(
            meta_ca,
            {"identity_id": identity_id, "app_id": app_id, "attributes": attributes, "justification": justification},
            _run,
            audit=audit,
        )

    meta_ma = ToolMeta(
        name="modify_account", phase=4, risk=Risk.PROVISIONING, implemented=True, requires_confirmation=True
    )

    @mcp.tool(name=meta_ma.name, description=tool_description(meta_ma, "PATCH SCIM Account attributes."))
    async def modify_account(
        account_id: str, attribute_changes: dict[str, Any], justification: str | None = None
    ) -> dict[str, Any]:
        async def _run() -> Any:
            return await scim_mutate(
                client,
                "PATCH",
                f"/Accounts/{encode_path_segment(account_id)}",
                json_body=attribute_changes,
            )

        return await run_tool(
            meta_ma,
            {"account_id": account_id, "attribute_changes": attribute_changes, "justification": justification},
            _run,
            audit=audit,
        )

    async def _account_active(account_id: str, active: bool) -> Any:
        return await scim_mutate(
            client, "PATCH", f"/Accounts/{encode_path_segment(account_id)}", json_body={"active": active}
        )

    meta_ena = ToolMeta(
        name="enable_account", phase=4, risk=Risk.PROVISIONING, implemented=True, requires_confirmation=True
    )

    @mcp.tool(
        name=meta_ena.name,
        description=tool_description(meta_ena, "Enable account via SCIM Account.active=true."),
    )
    async def enable_account(account_id: str, justification: str | None = None) -> dict[str, Any]:
        async def _run() -> Any:
            return await _account_active(account_id, True)

        return await run_tool(
            meta_ena, {"account_id": account_id, "justification": justification}, _run, audit=audit
        )

    meta_dis = ToolMeta(
        name="disable_account", phase=4, risk=Risk.PROVISIONING, implemented=True, requires_confirmation=True
    )

    @mcp.tool(
        name=meta_dis.name,
        description=tool_description(meta_dis, "Disable account via SCIM Account.active=false."),
    )
    async def disable_account(account_id: str, justification: str | None = None) -> dict[str, Any]:
        async def _run() -> Any:
            return await _account_active(account_id, False)

        return await run_tool(
            meta_dis, {"account_id": account_id, "justification": justification}, _run, audit=audit
        )

    meta_da = ToolMeta(
        name="delete_account", phase=4, risk=Risk.PROVISIONING, implemented=True, requires_confirmation=True
    )

    @mcp.tool(name=meta_da.name, description=tool_description(meta_da, "DELETE SCIM Account (often irreversible)."))
    async def delete_account(account_id: str, justification: str | None = None) -> dict[str, Any]:
        async def _run() -> Any:
            await scim_mutate(client, "DELETE", f"/Accounts/{encode_path_segment(account_id)}")
            return {"account_id": account_id, "deleted": True}

        return await run_tool(
            meta_da, {"account_id": account_id, "justification": justification}, _run, audit=audit
        )

    meta_ua = ToolMeta(
        name="unlock_account",
        phase=4,
        risk=Risk.PROVISIONING,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-12",
    )

    @mcp.tool(
        name=meta_ua.name,
        description=tool_description(
            meta_ua, "Unlock via identity password agent op=unlock (identity-level) or account PATCH."
        ),
    )
    async def unlock_account(
        account_id: str, identity_id: str | None = None, justification: str | None = None
    ) -> dict[str, Any]:
        async def _run() -> Any:
            if identity_id:
                user = await resolve_user(client, identity_id)
                name = user.get("userName") or identity_id
                return await agent_post(
                    client,
                    f"/identities/{encode_path_segment(name)}/password",
                    json_body={"op": "unlock"},
                )
            return await scim_mutate(
                client,
                "PATCH",
                f"/Accounts/{encode_path_segment(account_id)}",
                json_body={"locked": False, "IIQDisabled": False},
            )

        return await run_tool(
            meta_ua,
            {"account_id": account_id, "identity_id": identity_id, "justification": justification},
            _run,
            audit=audit,
        )

    meta_rfp = ToolMeta(
        name="retry_failed_provisioning",
        phase=4,
        risk=Risk.PROVISIONING,
        implemented=True,
        requires_confirmation=True,
    )

    @mcp.tool(
        name=meta_rfp.name,
        description=tool_description(meta_rfp, "Retry failed provisioning transaction via REST POST."),
    )
    async def retry_failed_provisioning(
        transaction_id: str, justification: str | None = None
    ) -> dict[str, Any]:
        async def _run() -> Any:
            for path in (
                f"/provisioningTransactions/{encode_path_segment(transaction_id)}/retry",
                f"/provisioning/transactions/{encode_path_segment(transaction_id)}/retry",
            ):
                try:
                    return await client.rest_post(path, json_body={})
                except Exception:
                    continue
            raise IiqMcpError(
                McpErrorBody(
                    code=ErrorCode.NOT_IMPLEMENTED,
                    http_status=501,
                    message="Retry endpoint not found; retry from Provisioning Transaction UI.",
                )
            )

        return await run_tool(
            meta_rfp, {"transaction_id": transaction_id, "justification": justification}, _run, audit=audit
        )

    # —— Passwords ——
    meta_gpp = ToolMeta(
        name="get_password_policy", phase=4, risk=Risk.READ, implemented=True, gap_id="UIAPI-12"
    )

    @mcp.tool(
        name=meta_gpp.name,
        description=tool_description(meta_gpp, "Password policy via REST checkPasswordPolicies best-effort."),
    )
    async def get_password_policy(app_id: str | None = None, raw: bool = False) -> dict[str, Any]:
        async def _run() -> Any:
            try:
                data = await client.rest_post(
                    "/policies/checkPasswordPolicies",
                    json_body={"application": app_id} if app_id else {},
                )
                return data if raw else trim_generic(data if isinstance(data, dict) else {"value": data})
            except Exception as exc:
                return {"app_id": app_id, "note": f"password policy probe failed: {exc}"}

        return await run_tool(meta_gpp, {"app_id": app_id, "raw": raw}, _run, audit=audit)

    meta_cps = ToolMeta(
        name="check_password_sync_status", phase=4, risk=Risk.READ, implemented=True, gap_id="UIAPI-12"
    )

    @mcp.tool(
        name=meta_cps.name,
        description=tool_description(
            meta_cps, "Best-effort password sync indicators from identity/accounts cube."
        ),
    )
    async def check_password_sync_status(identity_id: str, raw: bool = False) -> dict[str, Any]:
        async def _run() -> Any:
            user = await resolve_user(client, identity_id)
            sail = user.get("urn:ietf:params:scim:schemas:sailpoint:1.0:User") or {}
            return {
                "identity": user.get("userName"),
                "passwordLastChanged": sail.get("passwordLastChanged") or user.get("passwordLastChanged"),
                "accounts": "use get_identity_accounts for per-app state",
                "raw": user if raw else None,
            }

        return await run_tool(meta_cps, {"identity_id": identity_id, "raw": raw}, _run, audit=audit)

    meta_rp = ToolMeta(
        name="reset_password",
        phase=4,
        risk=Risk.PROVISIONING,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-12",
    )

    @mcp.tool(
        name=meta_rp.name,
        description=tool_description(meta_rp, "Reset password via Meridian agent (set/reset op)."),
    )
    async def reset_password(
        identity_id: str,
        app_id: str | None = None,
        new_password: str | None = None,
        justification: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            if not new_password:
                raise map_http_error(
                    400, {"message": "new_password required in v1 (generate-and-notify not exposed)."}
                )
            user = await resolve_user(client, identity_id)
            name = user.get("userName") or identity_id
            return await agent_post(
                client,
                f"/identities/{encode_path_segment(name)}/password",
                json_body={"op": "reset", "password": new_password, "application": app_id},
            )

        return await run_tool(
            meta_rp,
            {
                "identity_id": identity_id,
                "app_id": app_id,
                "new_password": "***" if new_password else None,
                "justification": justification,
            },
            _run,
            audit=audit,
        )

    meta_ep = ToolMeta(
        name="expire_password",
        phase=4,
        risk=Risk.PROVISIONING,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-12",
    )

    @mcp.tool(
        name=meta_ep.name,
        description=tool_description(
            meta_ep, "Best-effort expire via SCIM User attribute patch (passwordExpired)."
        ),
    )
    async def expire_password(identity_id: str, justification: str | None = None) -> dict[str, Any]:
        async def _run() -> Any:
            user = await resolve_user(client, identity_id)
            uid = user.get("id") or identity_id
            return await scim_mutate(
                client,
                "PATCH",
                f"/Users/{encode_path_segment(uid)}",
                json_body={"passwordExpired": True},
            )

        return await run_tool(
            meta_ep, {"identity_id": identity_id, "justification": justification}, _run, audit=audit
        )

    # —— Tasks ——
    meta_crt = ToolMeta(
        name="cancel_running_task",
        phase=2,
        risk=Risk.LOW_WRITE,
        implemented=True,
        requires_confirmation=True,
    )

    @mcp.tool(
        name=meta_crt.name,
        description=tool_description(meta_crt, "Cancel running TaskResult via REST DELETE/terminate."),
    )
    async def cancel_running_task(task_result_id: str, justification: str | None = None) -> dict[str, Any]:
        async def _run() -> Any:
            for method, path in (
                ("POST", f"/taskResults/{encode_path_segment(task_result_id)}/terminate"),
                ("POST", f"/taskResults/{encode_path_segment(task_result_id)}/cancel"),
                ("DELETE", f"/taskResults/{encode_path_segment(task_result_id)}"),
            ):
                try:
                    if method == "DELETE":
                        _, body = await client.request("DELETE", f"/rest{path}")
                        return body or {"cancelled": True, "task_result_id": task_result_id}
                    return await client.rest_post(path, json_body={})
                except Exception:
                    continue
            raise IiqMcpError(
                McpErrorBody(
                    code=ErrorCode.NOT_IMPLEMENTED,
                    http_status=501,
                    message="Task cancel endpoint unavailable on this IIQ.",
                )
            )

        return await run_tool(
            meta_crt, {"task_result_id": task_result_id, "justification": justification}, _run, audit=audit
        )

    meta_uts = ToolMeta(
        name="update_task_schedule",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-13",
    )

    @mcp.tool(
        name=meta_uts.name,
        description=tool_description(meta_uts, "Create/update schedule via Meridian agent POST /schedules."),
    )
    async def update_task_schedule(
        task_definition_id: str,
        cron_patch: dict[str, Any],
        justification: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body = {
                "name": cron_patch.get("name") or f"mcp-sched-{task_definition_id}",
                "taskDefinition": task_definition_id,
                "cron": cron_patch.get("cron") or cron_patch.get("cronString"),
                **{k: v for k, v in cron_patch.items() if k not in {"name", "cron", "cronString"}},
            }
            return await agent_post(client, "/schedules", json_body=body)

        return await run_tool(
            meta_uts,
            {
                "task_definition_id": task_definition_id,
                "cron_patch": cron_patch,
                "justification": justification,
            },
            _run,
            audit=audit,
        )

    # —— Rules (read) ——
    meta_lr = ToolMeta(name="list_rules", phase=1, risk=Risk.READ, implemented=True)

    @mcp.tool(
        name=meta_lr.name,
        description=tool_description(meta_lr, "List rules via REST /rules or agent objects export."),
    )
    async def list_rules(
        type: str | None = None,
        start: int | None = None,
        count: int | None = None,
        raw: bool = False,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            s, c = clamp_page(start, count)
            items: list[Any] = []
            try:
                payload = await client.rest_get("/rules")
                items = payload if isinstance(payload, list) else []
                if isinstance(payload, dict):
                    for key in ("objects", "items", "rules"):
                        if isinstance(payload.get(key), list):
                            items = payload[key]
                            break
            except Exception:
                try:
                    data = await agent_get(
                        client, "/objects/export", params={"className": "Rule", "limit": c}
                    )
                    items = data if isinstance(data, list) else []
                except Exception as exc:
                    return {"items": [], "note": str(exc)}
            if type:
                items = [
                    i
                    for i in items
                    if isinstance(i, dict) and type.lower() in str(i.get("type", "")).lower()
                ]
            page = items[s : s + c]
            return list_envelope(
                [trim_generic(i, keys=("id", "name", "type", "language", "description"), raw=raw) for i in page if isinstance(i, dict)],
                start=s,
                count=c,
                total=len(items),
                raw=raw,
            )

        return await run_tool(
            meta_lr, {"type": type, "start": start, "count": count, "raw": raw}, _run, audit=audit
        )

    meta_grs = ToolMeta(name="get_rule_source", phase=1, risk=Risk.READ, implemented=True)

    @mcp.tool(
        name=meta_grs.name,
        description=tool_description(meta_grs, "Get rule source via REST /rules/{id} or objects/export."),
    )
    async def get_rule_source(rule_id: str, raw: bool = False) -> dict[str, Any]:
        async def _run() -> Any:
            try:
                data = await client.rest_get(f"/rules/{encode_path_segment(rule_id)}")
                return data if raw else trim_generic(data if isinstance(data, dict) else {"value": data})
            except Exception:
                data = await agent_get(
                    client,
                    "/objects/export",
                    params={"className": "Rule", "name": rule_id},
                )
                return data

        return await run_tool(meta_grs, {"rule_id": rule_id, "raw": raw}, _run, audit=audit)

    # —— Reports ——
    meta_lrd = ToolMeta(
        name="list_report_definitions", phase=2, risk=Risk.READ, implemented=True, gap_id="UIAPI-14"
    )

    @mcp.tool(
        name=meta_lrd.name,
        description=tool_description(meta_lrd, "List report TaskDefinitions via REST /reports best-effort."),
    )
    async def list_report_definitions(
        start: int | None = None, count: int | None = None, raw: bool = False
    ) -> dict[str, Any]:
        async def _run() -> Any:
            s, c = clamp_page(start, count)
            try:
                payload = await client.rest_get("/reports")
            except Exception as exc:
                return {"items": [], "note": str(exc)}
            items = payload if isinstance(payload, list) else []
            if isinstance(payload, dict):
                for key in ("objects", "items", "reports"):
                    if isinstance(payload.get(key), list):
                        items = payload[key]
                        break
            page = items[s : s + c]
            return list_envelope(
                [trim_generic(i, raw=raw) for i in page if isinstance(i, dict)],
                start=s,
                count=c,
                total=len(items),
                raw=raw,
            )

        return await run_tool(
            meta_lrd, {"start": start, "count": count, "raw": raw}, _run, audit=audit
        )

    meta_rr = ToolMeta(
        name="run_report",
        phase=2,
        risk=Risk.LOW_WRITE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-14",
    )

    @mcp.tool(
        name=meta_rr.name,
        description=tool_description(meta_rr, "Run report TaskDefinition via Meridian agent; poll get_task_result."),
    )
    async def run_report(
        report_id: str,
        parameters: dict[str, Any] | None = None,
        justification: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            data = await agent_post(
                client,
                "/reports/run",
                json_body={"taskName": report_id, "args": parameters or {}},
            )
            return {
                **(data if isinstance(data, dict) else {"result": data}),
                "poll_with": "get_report_result",
                "suggested_backoff_seconds": [2, 5, 15, 30],
            }

        return await run_tool(
            meta_rr,
            {"report_id": report_id, "parameters": parameters, "justification": justification},
            _run,
            audit=audit,
        )

    meta_grr = ToolMeta(
        name="get_report_result", phase=2, risk=Risk.READ, implemented=True, gap_id="UIAPI-14"
    )

    @mcp.tool(
        name=meta_grr.name,
        description=tool_description(meta_grr, "Alias of get_task_result for report TaskResults."),
    )
    async def get_report_result(task_result_id: str, raw: bool = False) -> dict[str, Any]:
        async def _run() -> Any:
            try:
                data = await client.scim_get(f"/TaskResults/{encode_path_segment(task_result_id)}")
                return trim_task_result(data, raw=raw)
            except Exception:
                data = await client.rest_get(f"/taskResults/{encode_path_segment(task_result_id)}")
                return trim_task_result(data if isinstance(data, dict) else {"value": data}, raw=raw)

        return await run_tool(
            meta_grr, {"task_result_id": task_result_id, "raw": raw}, _run, audit=audit
        )

    meta_grsc = ToolMeta(name="get_risk_score_config", phase=2, risk=Risk.READ, implemented=True)

    @mcp.tool(
        name=meta_grsc.name,
        description=tool_description(meta_grsc, "Risk score config via agent system/config probe."),
    )
    async def get_risk_score_config(raw: bool = False) -> dict[str, Any]:
        async def _run() -> Any:
            try:
                data = await agent_get(client, "/system/config", params={"key": "RiskScore"})
                return data if raw else trim_generic(data if isinstance(data, dict) else {"value": data})
            except Exception as exc:
                return {"note": f"Risk score config not exposed cleanly: {exc}"}

        return await run_tool(meta_grsc, {"raw": raw}, _run, audit=audit)

    meta_girb = ToolMeta(name="get_identity_risk_breakdown", phase=2, risk=Risk.READ, implemented=True)

    @mcp.tool(
        name=meta_girb.name,
        description=tool_description(meta_girb, "Risk breakdown from SCIM User sailpoint extension fields."),
    )
    async def get_identity_risk_breakdown(
        identity_id: str | None = None,
        raw: bool = False,
        id: str | None = None,
    ) -> dict[str, Any]:
        resolved = (identity_id or id or "").strip()
        if not resolved:
            raise map_http_error(400, {"message": "identity_id (or id) is required"})

        async def _run() -> Any:
            user = await resolve_user(client, resolved)
            sail = user.get("urn:ietf:params:scim:schemas:sailpoint:1.0:User") or {}
            return {
                "id": user.get("id"),
                "userName": user.get("userName"),
                "riskScore": sail.get("riskScore") or sail.get("compositeRiskScore"),
                "riskLevel": sail.get("riskLevel"),
                "contributing": {
                    k: sail.get(k)
                    for k in ("baseScore", "compositeScore", "roleScore", "entitlementScore", "policyScore")
                    if k in sail
                },
                "raw": user if raw else None,
            }

        return await run_tool(
            meta_girb, {"identity_id": resolved, "id": id, "raw": raw}, _run, audit=audit
        )

    meta_sr = ToolMeta(
        name="schedule_report",
        phase=3,
        risk=Risk.COMPLIANCE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-14",
    )

    @mcp.tool(
        name=meta_sr.name,
        description=tool_description(meta_sr, "Schedule a report by creating a TaskSchedule via agent."),
    )
    async def schedule_report(
        report_id: str,
        cron: str,
        parameters: dict[str, Any] | None = None,
        justification: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client,
                "/schedules",
                json_body={
                    "name": f"mcp-report-{report_id}",
                    "taskDefinition": report_id,
                    "cron": cron,
                    "args": parameters or {},
                },
            )

        return await run_tool(
            meta_sr,
            {
                "report_id": report_id,
                "cron": cron,
                "parameters": parameters,
                "justification": justification,
            },
            _run,
            audit=audit,
        )
