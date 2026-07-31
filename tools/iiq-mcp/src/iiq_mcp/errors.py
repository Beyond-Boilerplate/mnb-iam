"""Normalized MCP / IIQ error taxonomy."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    NOT_FOUND = "not_found"
    UNAUTHORIZED = "unauthorized"
    VALIDATION = "validation"
    DOWNSTREAM = "downstream"
    RATE_LIMITED = "rate_limited"
    NOT_IMPLEMENTED = "not_implemented"
    PHASE_DISABLED = "phase_disabled"
    ASYNC_PENDING = "async_pending"
    CONFLICT = "conflict"
    INTERNAL = "internal"


class McpErrorBody(BaseModel):
    """Stable error shape returned inside tool results (and raised as ToolError)."""

    code: ErrorCode
    http_status: int | None = None
    message: str
    iiq_detail: Any | None = None
    gap_id: str | None = None
    tool: str | None = None
    phase: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)


class IiqMcpError(Exception):
    """Domain exception carrying a structured body."""

    def __init__(self, body: McpErrorBody) -> None:
        self.body = body
        super().__init__(body.message)

    def to_dict(self) -> dict[str, Any]:
        return self.body.to_dict()


def map_http_error(status: int, body: Any, *, default_message: str | None = None) -> IiqMcpError:
    """Map an IIQ HTTP status into the MCP error taxonomy."""
    text = _summarize_body(body)
    message = default_message or text or f"IIQ HTTP {status}"
    if status == 404:
        code = ErrorCode.NOT_FOUND
    elif status in (401, 403):
        code = ErrorCode.UNAUTHORIZED
    elif status == 409:
        code = ErrorCode.CONFLICT
    elif status == 429:
        code = ErrorCode.RATE_LIMITED
    elif 400 <= status < 500:
        code = ErrorCode.VALIDATION
    else:
        code = ErrorCode.DOWNSTREAM
    return IiqMcpError(
        McpErrorBody(
            code=code,
            http_status=status,
            message=message,
            iiq_detail=body if not isinstance(body, str) or len(body) < 4000 else body[:4000],
        )
    )


def not_implemented(
    tool: str,
    *,
    phase: int | None = None,
    gap_id: str | None = None,
    message: str | None = None,
) -> IiqMcpError:
    return IiqMcpError(
        McpErrorBody(
            code=ErrorCode.NOT_IMPLEMENTED,
            http_status=501,
            message=message
            or f"Tool '{tool}' is registered but not implemented in this MCP build.",
            tool=tool,
            phase=phase,
            gap_id=gap_id,
        )
    )


def phase_disabled(tool: str, phase: int) -> IiqMcpError:
    return IiqMcpError(
        McpErrorBody(
            code=ErrorCode.PHASE_DISABLED,
            http_status=403,
            message=(
                f"Tool '{tool}' requires phase {phase}, which is not enabled "
                f"(set IIQ_MCP_ENABLED_PHASES)."
            ),
            tool=tool,
            phase=phase,
        )
    )


def rate_limited(message: str = "MCP→IIQ rate limit exceeded; back off and retry.") -> IiqMcpError:
    return IiqMcpError(
        McpErrorBody(code=ErrorCode.RATE_LIMITED, http_status=429, message=message)
    )


def _summarize_body(body: Any) -> str:
    if body is None:
        return ""
    if isinstance(body, str):
        return body[:500]
    if isinstance(body, dict):
        for key in ("message", "detail", "error", "status", "statusMessage"):
            if key in body and body[key]:
                return str(body[key])[:500]
        return str(body)[:500]
    return str(body)[:500]
