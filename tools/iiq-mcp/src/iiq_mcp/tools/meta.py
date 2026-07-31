"""Tool metadata helpers: phase, risk, confirmation annotations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

from iiq_mcp.audit_log import WriteAuditLog
from iiq_mcp.config import Settings, get_settings
from iiq_mcp.errors import IiqMcpError, not_implemented, phase_disabled


class Risk(str, Enum):
    READ = "read"
    LOW_WRITE = "low_write"
    COMPLIANCE = "compliance"
    PROVISIONING = "provisioning"
    ADMIN = "admin"
    EXCLUDED = "excluded"


@dataclass(frozen=True)
class ToolMeta:
    name: str
    phase: int
    risk: Risk
    implemented: bool
    requires_confirmation: bool = False
    gap_id: str | None = None
    description: str = ""


def tool_description(meta: ToolMeta, body: str) -> str:
    bits = [body.strip()]
    bits.append(f"[phase={meta.phase} risk={meta.risk.value} implemented={meta.implemented}]")
    if meta.requires_confirmation:
        bits.insert(0, "[REQUIRES_CONFIRMATION]")
    if meta.gap_id:
        bits.append(f"[gap={meta.gap_id}]")
    if not meta.implemented:
        bits.append("Returns structured not_implemented until a later phase or plugin lands.")
    return " ".join(bits)


def guard_phase(meta: ToolMeta, settings: Settings | None = None) -> None:
    cfg = settings or get_settings()
    if not cfg.phase_enabled(meta.phase):
        raise phase_disabled(meta.name, meta.phase)


def stub_result(meta: ToolMeta, message: str | None = None) -> dict[str, Any]:
    err = not_implemented(
        meta.name,
        phase=meta.phase,
        gap_id=meta.gap_id,
        message=message,
    )
    return {"ok": False, "error": err.to_dict()}


async def run_tool(
    meta: ToolMeta,
    params: dict[str, Any],
    fn: Callable[..., Any],
    *,
    audit: WriteAuditLog | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Execute an implemented tool or return stub/phase errors uniformly."""
    cfg = settings or get_settings()
    try:
        guard_phase(meta, cfg)
        if not meta.implemented:
            if audit and meta.risk != Risk.READ:
                audit.record(
                    tool=meta.name,
                    parameters=params,
                    risk=meta.risk.value,
                    error="not_implemented",
                )
            return stub_result(meta)
        result = await fn()
        if audit and meta.risk != Risk.READ:
            audit.record(
                tool=meta.name,
                parameters=params,
                result=result if isinstance(result, dict) else {"value": result},
                risk=meta.risk.value,
                justification=params.get("justification"),
            )
        if isinstance(result, dict) and "ok" in result:
            return result
        return {"ok": True, "data": result}
    except IiqMcpError as exc:
        if audit and meta.risk != Risk.READ:
            audit.record(
                tool=meta.name,
                parameters=params,
                error=exc.to_dict(),
                risk=meta.risk.value,
            )
        return {"ok": False, "error": exc.to_dict()}
    except Exception as exc:  # noqa: BLE001 — surface unexpected errors to agent
        body = {
            "code": "internal",
            "message": str(exc),
            "tool": meta.name,
        }
        if audit and meta.risk != Risk.READ:
            audit.record(tool=meta.name, parameters=params, error=body, risk=meta.risk.value)
        return {"ok": False, "error": body}
