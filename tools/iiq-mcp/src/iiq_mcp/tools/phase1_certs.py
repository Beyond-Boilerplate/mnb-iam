"""Phase 1 — Certifications (OOTB /rest; experimental schemas)."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from iiq_mcp.client.http import IiqHttpClient, encode_path_segment
from iiq_mcp.errors import map_http_error
from iiq_mcp.shaping import clamp_page, list_envelope, trim_generic
from iiq_mcp.tools.meta import Risk, ToolMeta, run_tool, tool_description

_CERT_KEYS = (
    "id",
    "name",
    "type",
    "phase",
    "status",
    "signed",
    "certificationGroups",
    "certifiers",
    "expiration",
    "activated",
    "finished",
    "totalEntities",
    "completedEntities",
    "percentComplete",
    "tags",
)


def register(mcp: FastMCP, client: IiqHttpClient, **ctx: Any) -> None:
    audit = ctx.get("audit")

    meta_list = ToolMeta(
        name="list_certifications",
        phase=1,
        risk=Risk.READ,
        implemented=True,
    )

    @mcp.tool(
        name=meta_list.name,
        description=tool_description(
            meta_list,
            "List certifications via OOTB /rest/certifications (schemas experimental). "
            "Optional status/identity_id filters applied client-side when server ignores them.",
        ),
    )
    async def list_certifications(
        status: str | None = None,
        identity_id: str | None = None,
        campaign: str | None = None,
        start: int | None = None,
        count: int | None = None,
        raw: bool = False,
    ) -> dict[str, Any]:
        async def _run() -> dict[str, Any]:
            s, c = clamp_page(start, count)
            payload: Any = None
            # Prefer search POST when available; fall back to GET list
            try:
                body: dict[str, Any] = {"start": s, "limit": c}
                if status:
                    body["status"] = status
                if identity_id:
                    body["identityId"] = identity_id
                if campaign:
                    body["certificationGroup"] = campaign
                payload = await client.rest_post("/certifications/search", json_body=body)
            except Exception:
                payload = await client.rest_get("/certifications")

            items = _normalize_list(payload)
            if status:
                items = [i for i in items if str(i.get("status", "")).lower() == status.lower()]
            if campaign:
                items = [
                    i
                    for i in items
                    if campaign.lower() in str(i.get("name", "")).lower()
                    or campaign.lower() in str(i.get("certificationGroups", "")).lower()
                ]
            page = items[s : s + c]
            trimmed = [trim_generic(i, keys=_CERT_KEYS, raw=raw) for i in page]
            return list_envelope(trimmed, start=s, count=c, total=len(items), raw=raw)

        return await run_tool(
            meta_list,
            {
                "status": status,
                "identity_id": identity_id,
                "campaign": campaign,
                "start": start,
                "count": count,
                "raw": raw,
            },
            _run,
            audit=audit,
        )

    meta_detail = ToolMeta(
        name="get_certification_detail",
        phase=1,
        risk=Risk.READ,
        implemented=True,
    )

    @mcp.tool(
        name=meta_detail.name,
        description=tool_description(
            meta_detail,
            "Get certification detail by id (OOTB /rest/certifications/{id} best-effort).",
        ),
    )
    async def get_certification_detail(cert_id: str, raw: bool = False) -> dict[str, Any]:
        async def _run() -> dict[str, Any]:
            try:
                data = await client.rest_get(f"/certifications/{encode_path_segment(cert_id)}")
            except Exception:
                # Some installs expose locator-style paths
                data = await client.rest_get(f"/certification/{encode_path_segment(cert_id)}")
            if not data:
                raise map_http_error(404, {"message": f"Certification not found: {cert_id}"})
            return trim_generic(data, keys=_CERT_KEYS, raw=raw)

        return await run_tool(meta_detail, {"cert_id": cert_id, "raw": raw}, _run, audit=audit)

    meta_campaigns = ToolMeta(
        name="list_certification_campaigns",
        phase=1,
        risk=Risk.READ,
        implemented=True,
    )

    @mcp.tool(
        name=meta_campaigns.name,
        description=tool_description(
            meta_campaigns,
            "List certification groups/campaigns via /rest/certificationGroups (best-effort).",
        ),
    )
    async def list_certification_campaigns(
        start: int | None = None,
        count: int | None = None,
        raw: bool = False,
    ) -> dict[str, Any]:
        async def _run() -> dict[str, Any]:
            s, c = clamp_page(start, count)
            try:
                payload = await client.rest_get("/certificationGroups")
            except Exception as exc:
                return {
                    "warning": "certificationGroups endpoint unavailable",
                    "detail": str(exc),
                    "items": [],
                }
            items = _normalize_list(payload)
            page = items[s : s + c]
            keys = ("id", "name", "type", "status", "totalCertifications", "completedCertifications")
            trimmed = [trim_generic(i, keys=keys, raw=raw) for i in page]
            return list_envelope(trimmed, start=s, count=c, total=len(items), raw=raw)

        return await run_tool(
            meta_campaigns, {"start": start, "count": count, "raw": raw}, _run, audit=audit
        )

    meta_prog = ToolMeta(
        name="get_certification_progress",
        phase=1,
        risk=Risk.READ,
        implemented=True,
    )

    @mcp.tool(
        name=meta_prog.name,
        description=tool_description(
            meta_prog,
            "Best-effort campaign progress from certificationGroups or aggregated cert list.",
        ),
    )
    async def get_certification_progress(campaign_id: str, raw: bool = False) -> dict[str, Any]:
        async def _run() -> dict[str, Any]:
            try:
                data = await client.rest_get(
                    f"/certificationGroups/{encode_path_segment(campaign_id)}"
                )
                return trim_generic(data, raw=raw)
            except Exception:
                listed = await list_certifications(campaign=campaign_id, count=100, raw=raw)
                items = (listed.get("data") or {}).get("items") if listed.get("ok") else []
                return {
                    "campaign_id": campaign_id,
                    "certifications": items,
                    "note": "Derived from list_certifications; group endpoint unavailable.",
                }

        return await run_tool(
            meta_prog, {"campaign_id": campaign_id, "raw": raw}, _run, audit=audit
        )


def _normalize_list(payload: Any) -> list[dict[str, Any]]:
    if payload is None:
        return []
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("objects", "items", "certifications", "Resources", "results"):
            if isinstance(payload.get(key), list):
                return [x for x in payload[key] if isinstance(x, dict)]
        # Single object
        if "id" in payload or "name" in payload:
            return [payload]
    return []
