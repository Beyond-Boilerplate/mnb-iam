"""Phase 1 — Work items (partial OOTB REST; decide is Phase 2 / UIAPI-04)."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from iiq_mcp.client.http import IiqHttpClient, encode_path_segment
from iiq_mcp.errors import map_http_error
from iiq_mcp.shaping import clamp_page, list_envelope, trim_generic
from iiq_mcp.tools.meta import Risk, ToolMeta, run_tool, tool_description

_WI_KEYS = (
    "id",
    "name",
    "type",
    "state",
    "owner",
    "requester",
    "description",
    "level",
    "workflow",
    "targetClass",
    "targetId",
    "targetName",
    "created",
    "modified",
    "expiration",
)


def register(mcp: FastMCP, client: IiqHttpClient, **ctx: Any) -> None:
    audit = ctx.get("audit")

    meta_list = ToolMeta(
        name="list_work_items",
        phase=1,
        risk=Risk.READ,
        implemented=True,
    )

    @mcp.tool(
        name=meta_list.name,
        description=tool_description(
            meta_list,
            "List work-item notifications / open items via OOTB REST (partial surface). "
            "Approve/reject is not available until a plugin verb lands (UIAPI-04).",
        ),
    )
    async def list_work_items(
        owner_id: str | None = None,
        type: str | None = None,
        start: int | None = None,
        count: int | None = None,
        raw: bool = False,
    ) -> dict[str, Any]:
        async def _run() -> dict[str, Any]:
            s, c = clamp_page(start, count)
            items: list[dict[str, Any]] = []
            errors: list[str] = []
            for path in (
                "/workItemNotifications",
                "/workItems",
                "/workitemarchive/workitems",
            ):
                try:
                    payload = await client.rest_get(path)
                    items = _normalize_list(payload)
                    if items:
                        break
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{path}: {exc}")

            if owner_id:
                items = [
                    i
                    for i in items
                    if owner_id.lower()
                    in str(i.get("owner", "")).lower()
                    or owner_id == str((i.get("owner") or {}).get("id", "") if isinstance(i.get("owner"), dict) else "")
                    or owner_id.lower()
                    in str((i.get("owner") or {}).get("name", "") if isinstance(i.get("owner"), dict) else "").lower()
                ]
            if type:
                items = [i for i in items if type.lower() in str(i.get("type", "")).lower()]

            page = items[s : s + c]
            trimmed = [trim_generic(i, keys=_WI_KEYS, raw=raw) for i in page]
            env = list_envelope(trimmed, start=s, count=c, total=len(items), raw=raw)
            if not items and errors:
                env["warnings"] = errors
            return env

        return await run_tool(
            meta_list,
            {"owner_id": owner_id, "type": type, "start": start, "count": count, "raw": raw},
            _run,
            audit=audit,
        )

    meta_detail = ToolMeta(
        name="get_work_item_detail",
        phase=1,
        risk=Risk.READ,
        implemented=True,
    )

    @mcp.tool(
        name=meta_detail.name,
        description=tool_description(
            meta_detail,
            "Fetch work item detail via /rest/workItemDetails/{id} (POST in product; tried as POST then GET).",
        ),
    )
    async def get_work_item_detail(item_id: str, raw: bool = False) -> dict[str, Any]:
        async def _run() -> dict[str, Any]:
            last_err: Exception | None = None
            for method_path in (
                ("POST", f"/workItemDetails/{encode_path_segment(item_id)}"),
                ("GET", f"/workItems/{encode_path_segment(item_id)}"),
                ("GET", f"/workItem/{encode_path_segment(item_id)}"),
            ):
                method, path = method_path
                try:
                    if method == "POST":
                        data = await client.rest_post(path, json_body={})
                    else:
                        data = await client.rest_get(path)
                    return trim_generic(data, keys=_WI_KEYS, raw=raw)
                except Exception as exc:  # noqa: BLE001
                    last_err = exc
            raise map_http_error(
                404,
                {
                    "message": f"Work item not found or unreadable: {item_id}",
                    "detail": str(last_err) if last_err else None,
                },
            )

        return await run_tool(meta_detail, {"item_id": item_id, "raw": raw}, _run, audit=audit)


def _normalize_list(payload: Any) -> list[dict[str, Any]]:
    if payload is None:
        return []
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("objects", "items", "workItems", "notifications", "results"):
            if isinstance(payload.get(key), list):
                return [x for x in payload[key] if isinstance(x, dict)]
        if "id" in payload or "name" in payload:
            return [payload]
    return []
