"""Helpers for Meridian agent envelope + common SCIM list shaping."""

from __future__ import annotations

from typing import Any

from iiq_mcp.client.http import IiqHttpClient, encode_path_segment
from iiq_mcp.errors import map_http_error
from iiq_mcp.shaping import list_envelope, scim_page_params, scim_resources, scim_total, trim_generic


def unwrap_agent(payload: Any) -> Any:
    """Extract ``data`` from Meridian ``{status, gapId, data}`` envelopes."""
    if isinstance(payload, dict) and "data" in payload and payload.get("status") == "ok":
        return payload["data"]
    return payload


async def agent_get(
    client: IiqHttpClient, path: str, *, params: dict[str, Any] | None = None
) -> Any:
    raw = await client.plugin_get(f"/mnbToolkit/agent{path}", params=params)
    return unwrap_agent(raw)


async def agent_post(client: IiqHttpClient, path: str, *, json_body: Any = None) -> Any:
    raw = await client.plugin_post(f"/mnbToolkit/agent{path}", json_body=json_body or {})
    return unwrap_agent(raw)


async def scim_list(
    client: IiqHttpClient,
    resource: str,
    *,
    filter: str | None = None,
    start: int | None = None,
    count: int | None = None,
    raw: bool = False,
    keys: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    page = scim_page_params(start, count)
    params: dict[str, Any] = {**page}
    if filter:
        params["filter"] = filter
    path = resource if resource.startswith("/") else f"/{resource}"
    payload = await client.scim_get(path, params=params)
    items = scim_resources(payload)
    if keys and not raw:
        items = [trim_generic(i, keys=keys, raw=False) for i in items]
    elif raw:
        items = [dict(i) if isinstance(i, dict) else i for i in items]
    else:
        items = [trim_generic(i, raw=False) for i in items]
    return list_envelope(
        items,
        start=page["startIndex"] - 1,
        count=page["count"],
        total=scim_total(payload),
        raw=raw,
    )


async def scim_get_by_id_or_filter(
    client: IiqHttpClient,
    resource: str,
    id_or_name: str,
    *,
    name_attr: str = "name",
) -> dict[str, Any]:
    path = resource if resource.startswith("/") else f"/{resource}"
    try:
        data = await client.scim_get(f"{path}/{encode_path_segment(id_or_name)}")
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    payload = await client.scim_get(
        path,
        params={"filter": f'{name_attr} eq "{id_or_name}"', "count": 1},
    )
    resources = scim_resources(payload)
    if not resources:
        raise map_http_error(404, {"message": f"{resource} not found: {id_or_name}"})
    return resources[0]


async def scim_mutate(
    client: IiqHttpClient,
    method: str,
    path: str,
    *,
    json_body: Any = None,
) -> Any:
    full = path if path.startswith("/scim/") else f"/scim/v2{path if path.startswith('/') else '/' + path}"
    _, body = await client.request(
        method,
        full,
        json_body=json_body,
        accept="application/scim+json, application/json",
    )
    return body
