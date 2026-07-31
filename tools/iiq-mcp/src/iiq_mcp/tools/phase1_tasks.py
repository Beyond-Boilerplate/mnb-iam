"""Phase 1 — Tasks / TaskResults (+ Meridian toolkit run)."""

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
    trim_task_result,
)
from iiq_mcp.tools.meta import Risk, ToolMeta, run_tool, tool_description


def register(mcp: FastMCP, client: IiqHttpClient, **ctx: Any) -> None:
    audit = ctx.get("audit")

    meta_sched = ToolMeta(
        name="list_task_schedules",
        phase=1,
        risk=Risk.READ,
        implemented=True,
    )

    @mcp.tool(
        name=meta_sched.name,
        description=tool_description(
            meta_sched,
            "List task schedules via OOTB /rest/taskSchedules (best-effort).",
        ),
    )
    async def list_task_schedules(
        start: int | None = None,
        count: int | None = None,
        raw: bool = False,
    ) -> dict[str, Any]:
        async def _run() -> dict[str, Any]:
            s, c = clamp_page(start, count)
            try:
                payload = await client.rest_get("/taskSchedules")
            except Exception as exc:
                return {"items": [], "warning": str(exc)}
            items = _normalize_list(payload)
            page = items[s : s + c]
            keys = ("id", "name", "nextExecution", "lastExecution", "enabled", "cronString", "taskDefinition")
            trimmed = [trim_generic(i, keys=keys, raw=raw) for i in page]
            return list_envelope(trimmed, start=s, count=c, total=len(items), raw=raw)

        return await run_tool(
            meta_sched, {"start": start, "count": count, "raw": raw}, _run, audit=audit
        )

    meta_tr = ToolMeta(
        name="get_task_result",
        phase=1,
        risk=Risk.READ,
        implemented=True,
    )

    @mcp.tool(
        name=meta_tr.name,
        description=tool_description(
            meta_tr,
            "Poll a TaskResult by id (SCIM preferred, REST fallback). "
            "Pass task_id or alias task_result_id (from run_task_now / trigger_aggregation). "
            "Recommended poll backoff: 2s → 5s → 15s; do not tight-loop.",
        ),
    )
    async def get_task_result(
        task_id: str | None = None,
        raw: bool = False,
        task_result_id: str | None = None,
    ) -> dict[str, Any]:
        """Poll TaskResult. Accepts ``task_id`` or alias ``task_result_id`` (from run_task_now)."""
        resolved = (task_id or task_result_id or "").strip()
        if not resolved:
            raise map_http_error(
                400,
                {
                    "message": "task_id (or task_result_id) is required",
                    "detail": "run_task_now / trigger_aggregation return taskResultId — pass it as task_id",
                },
            )

        async def _run() -> dict[str, Any]:
            try:
                data = await client.scim_get(f"/TaskResults/{encode_path_segment(resolved)}")
                return trim_task_result(data, raw=raw)
            except Exception:
                try:
                    data = await client.rest_get(f"/taskResults/{encode_path_segment(resolved)}")
                    return trim_task_result(data if isinstance(data, dict) else {"value": data}, raw=raw)
                except Exception as exc:
                    raise map_http_error(
                        404, {"message": f"TaskResult not found: {resolved}", "detail": str(exc)}
                    )

        return await run_tool(
            meta_tr,
            {"task_id": resolved, "task_result_id": task_result_id, "raw": raw},
            _run,
            audit=audit,
        )

    meta_fail = ToolMeta(
        name="list_recent_task_failures",
        phase=1,
        risk=Risk.READ,
        implemented=True,
    )

    @mcp.tool(
        name=meta_fail.name,
        description=tool_description(
            meta_fail,
            "List recent TaskResults that look failed/terminated (SCIM filter best-effort).",
        ),
    )
    async def list_recent_task_failures(
        start: int | None = None,
        count: int | None = None,
        raw: bool = False,
    ) -> dict[str, Any]:
        async def _run() -> dict[str, Any]:
            page = scim_page_params(start, count)
            params: dict[str, Any] = {**page}
            # IIQ SCIM attribute names vary; try filter then client-side filter
            items: list[dict[str, Any]] = []
            payload: Any = None
            try:
                params["filter"] = (
                    'completionStatus eq "Error" or completionStatus eq "Terminated"'
                )
                payload = await client.scim_get("/TaskResults", params=params)
                items = scim_resources(payload)
            except Exception:
                payload = await client.scim_get("/TaskResults", params=page)
                items = [
                    t
                    for t in scim_resources(payload)
                    if str(t.get("completionStatus", "")).lower()
                    in {"error", "terminated", "failed", "incomplete"}
                ]
            trimmed = [trim_task_result(t, raw=raw) for t in items]
            return list_envelope(
                trimmed,
                start=page["startIndex"] - 1,
                count=page["count"],
                total=scim_total(payload),
                raw=raw,
            )

        return await run_tool(
            meta_fail, {"start": start, "count": count, "raw": raw}, _run, audit=audit
        )

    meta_run = ToolMeta(
        name="run_task_now",
        phase=1,
        risk=Risk.LOW_WRITE,
        implemented=True,
        requires_confirmation=True,
    )

    @mcp.tool(
        name=meta_run.name,
        description=tool_description(
            meta_run,
            "Launch an allowlisted task via Meridian mnbToolkit (async). "
            "Returns taskResultId — poll with get_task_result. Requires plugin install + rights.",
        ),
    )
    async def run_task_now(
        task_name: str,
        args: dict[str, Any] | None = None,
        sync: bool = False,
        justification: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> dict[str, Any]:
            body = {
                "taskName": task_name,
                "sync": sync,
                "args": args or {},
            }
            data = await client.plugin_post("/mnbToolkit/tasks/run", json_body=body)
            # Normalize common shapes
            if isinstance(data, dict):
                tr_id = (
                    data.get("taskResultId")
                    or data.get("id")
                    or (data.get("data") or {}).get("taskResultId")
                    or (data.get("result") or {}).get("id")
                )
                return {
                    "async": not sync,
                    "taskName": task_name,
                    "taskResultId": tr_id,
                    "rawResponse": data,
                    "poll_with": "get_task_result",
                    "poll_arg": "task_id",
                    "poll_aliases": ["task_id", "task_result_id"],
                    "suggested_backoff_seconds": [2, 5, 15, 30],
                }
            return {"taskName": task_name, "rawResponse": data}

        return await run_tool(
            meta_run,
            {
                "task_name": task_name,
                "args": args,
                "sync": sync,
                "justification": justification,
            },
            _run,
            audit=audit,
        )


def _normalize_list(payload: Any) -> list[dict[str, Any]]:
    if payload is None:
        return []
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("objects", "items", "taskSchedules", "results"):
            if isinstance(payload.get(key), list):
                return [x for x in payload[key] if isinstance(x, dict)]
        if "id" in payload or "name" in payload:
            return [payload]
    return []
