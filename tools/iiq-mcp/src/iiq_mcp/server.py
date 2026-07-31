"""FastMCP HTTP server entrypoint for IdentityIQ."""

from __future__ import annotations

import logging
import os
from typing import Any

from fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from iiq_mcp.audit_log import WriteAuditLog
from iiq_mcp.client.http import IiqHttpClient
from iiq_mcp.config import Settings, get_settings
from iiq_mcp.idempotency import IdempotencyStore
from iiq_mcp.tools import register_all

logger = logging.getLogger("iiq_mcp")


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Require ``Authorization: Bearer <MCP_API_KEY>`` or ``X-API-Key`` when configured.

    When ``MCP_API_KEY`` is empty and host is loopback, auth is skipped (lab convenience).
    Non-loopback without a key is refused at startup.
    """

    def __init__(self, app: Any, api_key: str) -> None:
        super().__init__(app)
        self.api_key = api_key

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        if not self.api_key:
            return await call_next(request)
        # Allow unauthenticated health for load balancers
        if request.url.path in ("/healthz", "/health"):
            return await call_next(request)
        provided = request.headers.get("x-api-key")
        auth = request.headers.get("authorization") or ""
        if not provided and auth.lower().startswith("bearer "):
            provided = auth[7:].strip()
        if provided != self.api_key:
            return JSONResponse(
                {"error": "unauthorized", "message": "Invalid or missing MCP_API_KEY"},
                status_code=401,
            )
        return await call_next(request)


def build_server(settings: Settings | None = None) -> tuple[FastMCP, IiqHttpClient, Settings]:
    cfg = settings or get_settings()
    mcp = FastMCP(
        name="identityiq",
        instructions=(
            "SailPoint IdentityIQ MCP server. This server exposes TOOLS only "
            "(resource lists are empty by design — always use tools). "
            "For live app/identity/ops: call toolkit_ping, list_uiapi_gaps, create_application, "
            "search_identities, run_task_now, etc. Writes are implemented behind phases and "
            "IIQ plugin flags; respect [REQUIRES_CONFIRMATION], poll TaskResults with backoff. "
            "Never use /ui/rest. Prefer tools over SSB lab bootstrap for live localhost IIQ."
        ),
    )
    client = IiqHttpClient(cfg)
    audit = WriteAuditLog(cfg.iiq_mcp_audit_log)
    idem = IdempotencyStore(cfg.iiq_mcp_idempotency_db)
    register_all(mcp, client, audit=audit, idempotency=idem, settings=cfg)

    @mcp.custom_route("/healthz", methods=["GET"])
    async def healthz(_request: Request) -> JSONResponse:
        return JSONResponse(
            {
                "status": "ok",
                "iiq_base_url": cfg.iiq_base_url,
                "enabled_phases": sorted(cfg.enabled_phases()),
            }
        )

    return mcp, client, cfg


def main() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    cfg = get_settings()
    host = cfg.mcp_host
    is_loopback = host in {"127.0.0.1", "localhost", "::1"}
    if not cfg.mcp_api_key and not is_loopback:
        raise SystemExit(
            "MCP_API_KEY is required when MCP_HOST is not loopback. "
            "Refusing to start an open MCP HTTP listener."
        )
    if not cfg.iiq_password:
        logger.warning("IIQ_PASSWORD is empty — IIQ calls will likely fail auth")

    mcp, _client, cfg = build_server(cfg)
    from starlette.middleware import Middleware

    asgi_middleware = [Middleware(ApiKeyMiddleware, api_key=cfg.mcp_api_key)]

    logger.info(
        "Starting IIQ MCP on http://%s:%s%s (phases=%s)",
        cfg.mcp_host,
        cfg.mcp_port,
        cfg.mcp_path,
        sorted(cfg.enabled_phases()),
    )
    mcp.run(
        transport="http",
        host=cfg.mcp_host,
        port=cfg.mcp_port,
        path=cfg.mcp_path,
        middleware=asgi_middleware,
    )


if __name__ == "__main__":
    main()
