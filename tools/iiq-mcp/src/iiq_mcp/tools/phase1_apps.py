"""Phase 1 — Applications (SCIM Applications)."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from iiq_mcp.client.http import IiqHttpClient, encode_path_segment
from iiq_mcp.errors import map_http_error
from iiq_mcp.shaping import list_envelope, scim_page_params, scim_resources, scim_total, trim_application
from iiq_mcp.tools.meta import Risk, ToolMeta, run_tool, tool_description


def register(mcp: FastMCP, client: IiqHttpClient, **ctx: Any) -> None:
    audit = ctx.get("audit")

    meta_list = ToolMeta(
        name="list_applications",
        phase=1,
        risk=Risk.READ,
        implemented=True,
    )

    @mcp.tool(
        name=meta_list.name,
        description=tool_description(
            meta_list,
            "List connected applications/sources via SCIM Applications.",
        ),
    )
    async def list_applications(
        query: str | None = None,
        start: int | None = None,
        count: int | None = None,
        raw: bool = False,
    ) -> dict[str, Any]:
        async def _run() -> dict[str, Any]:
            page = scim_page_params(start, count)
            params: dict[str, Any] = {**page}
            if query:
                q = query.replace('"', '\\"')
                # IIQ SCIM Applications supports ``name`` only (not displayName).
                params["filter"] = f'name co "{q}"'
            payload = await client.scim_get("/Applications", params=params)
            items = [trim_application(a, raw=raw) for a in scim_resources(payload)]
            # SCIM often emits broken Java array toString for features — enrich from agent when empty.
            if not raw:
                from iiq_mcp.tools.agent_helpers import agent_get

                for item in items:
                    feats = item.get("features") or []
                    if feats:
                        continue
                    name = item.get("name")
                    if not name:
                        continue
                    try:
                        cfg = await agent_get(client, f"/applications/{encode_path_segment(name)}/config")
                        fs = (cfg or {}).get("featuresString") if isinstance(cfg, dict) else None
                        if isinstance(fs, str) and fs.strip():
                            item["features"] = [p.strip() for p in fs.split(",") if p.strip()]
                            item["featuresString"] = fs
                        if isinstance(cfg, dict) and cfg.get("authoritative") is not None:
                            item["authoritative"] = cfg.get("authoritative")
                    except Exception:  # noqa: BLE001
                        pass
            return list_envelope(
                items, start=page["startIndex"] - 1, count=page["count"], total=scim_total(payload), raw=raw
            )

        return await run_tool(
            meta_list, {"query": query, "start": start, "count": count, "raw": raw}, _run, audit=audit
        )

    meta_detail = ToolMeta(
        name="get_application_detail",
        phase=1,
        risk=Risk.READ,
        implemented=True,
    )

    @mcp.tool(
        name=meta_detail.name,
        description=tool_description(meta_detail, "Get one SCIM Application by id or name."),
    )
    async def get_application_detail(app_id: str, raw: bool = False) -> dict[str, Any]:
        async def _run() -> dict[str, Any]:
            try:
                app = await client.scim_get(f"/Applications/{encode_path_segment(app_id)}")
                return trim_application(app, raw=raw)
            except Exception:
                payload = await client.scim_get(
                    "/Applications",
                    params={"filter": f'name eq "{app_id}"', "count": 1},
                )
                resources = scim_resources(payload)
                if not resources:
                    raise map_http_error(404, {"message": f"Application not found: {app_id}"})
                return trim_application(resources[0], raw=raw)

        return await run_tool(meta_detail, {"app_id": app_id, "raw": raw}, _run, audit=audit)

    meta_health = ToolMeta(
        name="get_application_health",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-21",
        description="Connector test + config probe via Meridian agent.",
    )

    @mcp.tool(
        name=meta_health.name,
        description=tool_description(
            meta_health,
            "Application health: Meridian testConnection + config GET when agentApiEnabled.",
        ),
    )
    async def get_application_health(app_id: str) -> dict[str, Any]:
        from iiq_mcp.errors import ErrorCode, IiqMcpError, McpErrorBody
        from iiq_mcp.tools.agent_helpers import agent_get, agent_post

        async def _run() -> dict[str, Any]:
            out: dict[str, Any] = {"app_id": app_id, "healthy": False}
            try:
                out["config"] = await agent_get(
                    client, f"/applications/{encode_path_segment(app_id)}/config"
                )
            except Exception as exc:  # noqa: BLE001
                out["config_error"] = str(exc)
            try:
                out["connectivity"] = await agent_post(
                    client,
                    "/connectors/testConnection",
                    json_body={"application": app_id},
                )
            except Exception as exc:  # noqa: BLE001
                out["connectivity_error"] = str(exc)
            cfg_ok = "config" in out and "config_error" not in out
            conn = out.get("connectivity") if isinstance(out.get("connectivity"), dict) else {}
            conn_ok = bool(conn.get("success")) if conn else "connectivity_error" not in out
            out["healthy"] = bool(cfg_ok and conn_ok)
            if not cfg_ok and not conn_ok:
                err = str(out.get("config_error") or out.get("connectivity_error") or "")
                if "agentApiEnabled" in err or "agent_api_disabled" in err:
                    raise IiqMcpError(
                        McpErrorBody(
                            code=ErrorCode.UNAUTHORIZED,
                            http_status=403,
                            message="agentApiEnabled=false — enable Meridian Custom APIs plugin settings",
                            gap_id="UIAPI-21",
                            iiq_detail=out,
                        )
                    )
            return out

        return await run_tool(meta_health, {"app_id": app_id}, _run, audit=audit)
