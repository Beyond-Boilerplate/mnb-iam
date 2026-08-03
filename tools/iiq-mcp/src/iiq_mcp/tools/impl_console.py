"""MCP tools for Meridian Console composites (UIAPI-60..72).

Wraps ``MnbConsoleResource`` under ``/plugin/rest/mnbToolkit/agent/console/*``.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from iiq_mcp.client.http import IiqHttpClient, encode_path_segment
from iiq_mcp.tools.agent_helpers import agent_get
from iiq_mcp.tools.meta import Risk, ToolMeta, run_tool, tool_description


def register(mcp: FastMCP, client: IiqHttpClient, **ctx: Any) -> None:
    audit = ctx.get("audit")

    async def _console(
        meta: ToolMeta, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_get(client, path, params=params)

        return await run_tool(meta, params or {}, _run, audit=audit)

    meta_menu = ToolMeta(
        name="get_console_menu",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-60",
    )

    @mcp.tool(
        name=meta_menu.name,
        description=tool_description(
            meta_menu,
            "Meridian Console menu groups (ops/business/control/explore desks).",
        ),
    )
    async def get_console_menu() -> dict[str, Any]:
        return await _console(meta_menu, "/console/menu")

    meta_sum = ToolMeta(
        name="get_console_summary",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-60",
    )

    @mcp.tool(
        name=meta_sum.name,
        description=tool_description(
            meta_sum,
            "Console command-hub counts: orphans, pipeline fails, inbox, certs, SoD, provisioning.",
        ),
    )
    async def get_console_summary() -> dict[str, Any]:
        return await _console(meta_sum, "/console/summary")

    meta_orph = ToolMeta(
        name="console_orphans",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-60",
    )

    @mcp.tool(
        name=meta_orph.name,
        description=tool_description(
            meta_orph,
            "Orphan desk: login-named cubes + uncorrelated accounts. Optional limit.",
        ),
    )
    async def console_orphans(limit: int | None = None) -> dict[str, Any]:
        params = {"limit": limit} if limit is not None else None
        return await _console(meta_orph, "/console/orphans", params)

    meta_pipe = ToolMeta(
        name="console_pipeline",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-61",
    )

    @mcp.tool(
        name=meta_pipe.name,
        description=tool_description(
            meta_pipe,
            "Aggregation/refresh pipeline stop-go board (recent TaskResults).",
        ),
    )
    async def console_pipeline(limit: int | None = None) -> dict[str, Any]:
        params = {"limit": limit} if limit is not None else None
        return await _console(meta_pipe, "/console/pipeline", params)

    meta_inbox = ToolMeta(
        name="console_inbox",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-62",
    )

    @mcp.tool(
        name=meta_inbox.name,
        description=tool_description(
            meta_inbox, "Approval inbox composite (open work items for decide)."
        ),
    )
    async def console_inbox(limit: int | None = None) -> dict[str, Any]:
        params = {"limit": limit} if limit is not None else None
        return await _console(meta_inbox, "/console/inbox", params)

    meta_cat = ToolMeta(
        name="console_catalog",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-63",
    )

    @mcp.tool(
        name=meta_cat.name,
        description=tool_description(
            meta_cat, "Access catalog composite (roles/entitlements snapshot)."
        ),
    )
    async def console_catalog(limit: int | None = None) -> dict[str, Any]:
        params = {"limit": limit} if limit is not None else None
        return await _console(meta_cat, "/console/catalog", params)

    meta_certs = ToolMeta(
        name="console_certs",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-64",
    )

    @mcp.tool(
        name=meta_certs.name,
        description=tool_description(
            meta_certs, "Cert console campaign list with completion hints."
        ),
    )
    async def console_certs(limit: int | None = None) -> dict[str, Any]:
        params = {"limit": limit} if limit is not None else None
        return await _console(meta_certs, "/console/certs", params)

    meta_cd = ToolMeta(
        name="console_cert_detail",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-64",
    )

    @mcp.tool(
        name=meta_cd.name,
        description=tool_description(
            meta_cd,
            "Cert console detail for one campaign. Args: id; optional limit.",
        ),
    )
    async def console_cert_detail(id: str, limit: int | None = None) -> dict[str, Any]:
        params = {"limit": limit} if limit is not None else None
        return await _console(
            meta_cd, f"/console/certs/{encode_path_segment(id)}", params
        )

    meta_sod = ToolMeta(
        name="console_sod",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-65",
    )

    @mcp.tool(
        name=meta_sod.name,
        description=tool_description(
            meta_sod, "SoD war room: open violations grouped by policy."
        ),
    )
    async def console_sod(limit: int | None = None) -> dict[str, Any]:
        params = {"limit": limit} if limit is not None else None
        return await _console(meta_sod, "/console/sod", params)

    meta_i360 = ToolMeta(
        name="console_identity360",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-66",
    )

    @mcp.tool(
        name=meta_i360.name,
        description=tool_description(
            meta_i360,
            "Identity 360 helpdesk workbench. Args: q (name, email, or display).",
        ),
    )
    async def console_identity360(q: str) -> dict[str, Any]:
        return await _console(meta_i360, "/console/identity360", {"q": q})

    meta_jml = ToolMeta(
        name="console_jml",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-67",
    )

    @mcp.tool(
        name=meta_jml.name,
        description=tool_description(
            meta_jml, "JML timeline composite for joiner/mover/leaver personas."
        ),
    )
    async def console_jml(limit: int | None = None) -> dict[str, Any]:
        params = {"limit": limit} if limit is not None else None
        return await _console(meta_jml, "/console/jml", params)

    meta_ev = ToolMeta(
        name="console_evidence",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-68",
    )

    @mcp.tool(
        name=meta_ev.name,
        description=tool_description(
            meta_ev, "Exam-ready evidence pack JSON binder."
        ),
    )
    async def console_evidence(limit: int | None = None) -> dict[str, Any]:
        params = {"limit": limit} if limit is not None else None
        return await _console(meta_ev, "/console/evidence", params)

    meta_prov = ToolMeta(
        name="console_provisioning",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-69",
    )

    @mcp.tool(
        name=meta_prov.name,
        description=tool_description(
            meta_prov, "Provisioning debugger: failed/pending transactions."
        ),
    )
    async def console_provisioning(limit: int | None = None) -> dict[str, Any]:
        params = {"limit": limit} if limit is not None else None
        return await _console(meta_prov, "/console/provisioning", params)

    meta_wg = ToolMeta(
        name="console_workgroups",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-70",
    )

    @mcp.tool(
        name=meta_wg.name,
        description=tool_description(
            meta_wg, "Workgroups desk: membership + capability snapshot."
        ),
    )
    async def console_workgroups(limit: int | None = None) -> dict[str, Any]:
        params = {"limit": limit} if limit is not None else None
        return await _console(meta_wg, "/console/workgroups", params)

    meta_heat = ToolMeta(
        name="console_heatmap",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-71",
    )

    @mcp.tool(
        name=meta_heat.name,
        description=tool_description(
            meta_heat, "Risk heatmap: privileged entitlements by application."
        ),
    )
    async def console_heatmap(limit: int | None = None) -> dict[str, Any]:
        params = {"limit": limit} if limit is not None else None
        return await _console(meta_heat, "/console/heatmap", params)

    meta_aud = ToolMeta(
        name="console_audit",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-72",
    )

    @mcp.tool(
        name=meta_aud.name,
        description=tool_description(
            meta_aud, "Recent AuditEvent stream for the console audit desk."
        ),
    )
    async def console_audit(limit: int | None = None) -> dict[str, Any]:
        params = {"limit": limit} if limit is not None else None
        return await _console(meta_aud, "/console/audit", params)
