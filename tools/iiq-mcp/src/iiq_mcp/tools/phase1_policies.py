"""Phase 1 — Policies & SoD violations (SCIM PolicyViolations)."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from iiq_mcp.client.http import IiqHttpClient, encode_path_segment
from iiq_mcp.errors import map_http_error
from iiq_mcp.shaping import (
    clamp_page,
    list_envelope,
    scim_page_params,
    scim_resources,
    scim_total,
    trim_generic,
    trim_policy_violation,
)
from iiq_mcp.tools.meta import Risk, ToolMeta, run_tool, tool_description


def register(mcp: FastMCP, client: IiqHttpClient, **ctx: Any) -> None:
    audit = ctx.get("audit")

    meta_list_pol = ToolMeta(
        name="list_policies",
        phase=1,
        risk=Risk.READ,
        implemented=True,
    )

    @mcp.tool(
        name=meta_list_pol.name,
        description=tool_description(
            meta_list_pol,
            "List policies via OOTB /rest best-effort; SCIM has no Policy collection. "
            "Falls back to distinct policyName values from PolicyViolations if needed.",
        ),
    )
    async def list_policies(
        type: str | None = None,
        start: int | None = None,
        count: int | None = None,
        raw: bool = False,
    ) -> dict[str, Any]:
        async def _run() -> dict[str, Any]:
            s, c = clamp_page(start, count)
            items: list[dict[str, Any]] = []
            # Probe common REST paths; tolerate 404
            for path in ("/policies", "/policy"):
                try:
                    payload = await client.rest_get(path)
                    if isinstance(payload, list):
                        items = [x for x in payload if isinstance(x, dict)]
                    elif isinstance(payload, dict):
                        for key in ("objects", "items", "policies"):
                            if isinstance(payload.get(key), list):
                                items = [x for x in payload[key] if isinstance(x, dict)]
                                break
                    if items:
                        break
                except Exception:
                    continue

            if not items:
                # Derive from violations
                payload = await client.scim_get(
                    "/PolicyViolations", params={**scim_page_params(0, 100)}
                )
                names: dict[str, dict[str, Any]] = {}
                for v in scim_resources(payload):
                    pname = v.get("policyName") or v.get("name")
                    if pname and pname not in names:
                        names[pname] = {"name": pname, "source": "derived_from_policy_violations"}
                items = list(names.values())

            if type:
                items = [
                    i
                    for i in items
                    if type.lower() in str(i.get("type", "")).lower()
                    or type.lower() in str(i.get("name", "")).lower()
                ]
            page = items[s : s + c]
            trimmed = [
                trim_generic(i, keys=("id", "name", "type", "description", "state", "source"), raw=raw)
                for i in page
            ]
            return list_envelope(trimmed, start=s, count=c, total=len(items), raw=raw)

        return await run_tool(
            meta_list_pol, {"type": type, "start": start, "count": count, "raw": raw}, _run, audit=audit
        )

    meta_pol = ToolMeta(
        name="get_policy_detail",
        phase=1,
        risk=Risk.READ,
        implemented=True,
    )

    @mcp.tool(
        name=meta_pol.name,
        description=tool_description(
            meta_pol,
            "Get policy detail by id/name (REST best-effort).",
        ),
    )
    async def get_policy_detail(policy_id: str, raw: bool = False) -> dict[str, Any]:
        async def _run() -> dict[str, Any]:
            for path in (
                f"/policies/{encode_path_segment(policy_id)}",
                f"/policy/{encode_path_segment(policy_id)}",
            ):
                try:
                    data = await client.rest_get(path)
                    return trim_generic(data, raw=raw)
                except Exception:
                    continue
            raise map_http_error(
                404,
                {
                    "message": (
                        f"Policy '{policy_id}' not found via OOTB REST. "
                        "Use list_policy_violations for SoD conflict reads."
                    )
                },
            )

        return await run_tool(meta_pol, {"policy_id": policy_id, "raw": raw}, _run, audit=audit)

    meta_viol = ToolMeta(
        name="list_policy_violations",
        phase=1,
        risk=Risk.READ,
        implemented=True,
    )

    @mcp.tool(
        name=meta_viol.name,
        description=tool_description(
            meta_viol,
            "List SoD/policy violations via SCIM PolicyViolations.",
        ),
    )
    async def list_policy_violations(
        identity_id: str | None = None,
        status: str | None = None,
        start: int | None = None,
        count: int | None = None,
        raw: bool = False,
    ) -> dict[str, Any]:
        async def _run() -> dict[str, Any]:
            page = scim_page_params(start, count)
            params: dict[str, Any] = {**page}
            filters: list[str] = []
            if identity_id:
                filters.append(
                    f'identity.userName eq "{identity_id}" or identity.value eq "{identity_id}"'
                )
            if status:
                filters.append(f'status eq "{status}"')
            if filters:
                params["filter"] = " and ".join(f"({f})" for f in filters)
            payload = await client.scim_get("/PolicyViolations", params=params)
            items = [trim_policy_violation(v, raw=raw) for v in scim_resources(payload)]
            return list_envelope(
                items, start=page["startIndex"] - 1, count=page["count"], total=scim_total(payload), raw=raw
            )

        return await run_tool(
            meta_viol,
            {
                "identity_id": identity_id,
                "status": status,
                "start": start,
                "count": count,
                "raw": raw,
            },
            _run,
            audit=audit,
        )

    meta_vd = ToolMeta(
        name="get_violation_detail",
        phase=1,
        risk=Risk.READ,
        implemented=True,
    )

    @mcp.tool(
        name=meta_vd.name,
        description=tool_description(meta_vd, "Get one SCIM PolicyViolation by id."),
    )
    async def get_violation_detail(violation_id: str, raw: bool = False) -> dict[str, Any]:
        async def _run() -> dict[str, Any]:
            data = await client.scim_get(f"/PolicyViolations/{encode_path_segment(violation_id)}")
            return trim_policy_violation(data, raw=raw)

        return await run_tool(
            meta_vd, {"violation_id": violation_id, "raw": raw}, _run, audit=audit
        )
