"""Thin async httpx client for IdentityIQ SCIM / REST / plugin surfaces."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote

import httpx

from iiq_mcp.config import Settings, get_settings
from iiq_mcp.errors import IiqMcpError, McpErrorBody, ErrorCode, map_http_error
from iiq_mcp.rate_limit import RateLimiter


class IiqHttpClient:
    """Basic-auth HTTP client with rate limiting and OpenAPI path helpers."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        limiter: RateLimiter | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.limiter = limiter or RateLimiter(
            self.settings.iiq_mcp_max_rps,
            self.settings.iiq_mcp_max_concurrent,
        )
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=self.settings.iiq_base_url,
            auth=(self.settings.iiq_user, self.settings.iiq_password),
            timeout=self.settings.iiq_mcp_http_timeout_seconds,
            headers={"X-Requested-With": "XMLHttpRequest"},
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
        accept: str | None = None,
        content_type: str | None = None,
        raise_for_status: bool = True,
    ) -> tuple[int, Any]:
        headers: dict[str, str] = {}
        if accept:
            headers["Accept"] = accept
        if content_type:
            headers["Content-Type"] = content_type
        elif json_body is not None:
            headers["Content-Type"] = "application/json"

        async with self.limiter.slot():
            try:
                resp = await self._client.request(
                    method.upper(),
                    path,
                    params=params,
                    json=json_body,
                    headers=headers or None,
                )
            except httpx.TimeoutException as exc:
                raise IiqMcpError(
                    McpErrorBody(
                        code=ErrorCode.DOWNSTREAM,
                        http_status=504,
                        message=f"IIQ request timed out: {method} {path}",
                    )
                ) from exc
            except httpx.HTTPError as exc:
                raise IiqMcpError(
                    McpErrorBody(
                        code=ErrorCode.DOWNSTREAM,
                        message=f"IIQ transport error: {exc}",
                    )
                ) from exc

        body: Any
        ctype = resp.headers.get("content-type", "")
        text = resp.text
        if "json" in ctype or text[:1] in "{[":
            try:
                body = resp.json()
            except json.JSONDecodeError:
                body = text
        else:
            body = text

        if raise_for_status and resp.status_code >= 400:
            raise map_http_error(resp.status_code, body)
        return resp.status_code, body

    async def scim_get(
        self,
        resource_path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        path = resource_path if resource_path.startswith("/") else f"/{resource_path}"
        if not path.startswith("/scim/"):
            path = f"/scim/v2{path}"
        _, body = await self.request(
            "GET",
            path,
            params=params,
            accept="application/scim+json, application/json",
        )
        return body

    async def rest_get(
        self,
        resource_path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        path = resource_path if resource_path.startswith("/") else f"/{resource_path}"
        if not path.startswith("/rest/"):
            path = f"/rest{path}"
        _, body = await self.request("GET", path, params=params, accept="application/json")
        return body

    async def rest_post(
        self,
        resource_path: str,
        *,
        json_body: Any = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        path = resource_path if resource_path.startswith("/") else f"/{resource_path}"
        if not path.startswith("/rest/"):
            path = f"/rest{path}"
        _, body = await self.request(
            "POST",
            path,
            params=params,
            json_body=json_body,
            accept="application/json",
        )
        return body

    async def plugin_get(self, resource_path: str, *, params: dict[str, Any] | None = None) -> Any:
        path = resource_path if resource_path.startswith("/") else f"/{resource_path}"
        if not path.startswith("/plugin/"):
            path = f"/plugin/rest{path if path.startswith('/') else '/' + path}"
        _, body = await self.request("GET", path, params=params, accept="application/json")
        return body

    async def plugin_post(self, resource_path: str, *, json_body: Any = None) -> Any:
        path = resource_path if resource_path.startswith("/") else f"/{resource_path}"
        if not path.startswith("/plugin/"):
            path = f"/plugin/rest{path if path.startswith('/') else '/' + path}"
        _, body = await self.request(
            "POST",
            path,
            json_body=json_body,
            accept="application/json",
        )
        return body


def encode_path_segment(value: str) -> str:
    return quote(str(value), safe="")
