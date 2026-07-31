"""Register permanently excluded stub tools only; discover implemented names from MCP."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Awaitable, Callable

import yaml
from fastmcp import FastMCP

from iiq_mcp.client.http import IiqHttpClient
from iiq_mcp.tools.meta import Risk, ToolMeta, run_tool, tool_description

CATALOG_PATH = Path(__file__).with_name("catalog.yaml")

# Populated by refresh_implemented_from_mcp() after register_all (or tests).
IMPLEMENTED_TOOL_NAMES: frozenset[str] = frozenset()
PHASE1_IMPLEMENTED_NAMES = IMPLEMENTED_TOOL_NAMES


def load_catalog(path: Path = CATALOG_PATH) -> list[dict[str, Any]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    tools = data.get("tools") or []
    if not isinstance(tools, list):
        raise ValueError("catalog.yaml: tools must be a list")
    return [t for t in tools if isinstance(t, dict) and t.get("name")]


def excluded_tool_names() -> frozenset[str]:
    return frozenset(str(t["name"]) for t in load_catalog())


def all_catalog_names() -> set[str]:
    """Implemented (discovered) ∪ YAML exclusions."""
    return set(IMPLEMENTED_TOOL_NAMES) | set(excluded_tool_names())


def refresh_implemented_from_mcp(mcp: FastMCP) -> frozenset[str]:
    """Derive implemented tool names from live FastMCP registration (minus YAML stubs)."""
    global IMPLEMENTED_TOOL_NAMES, PHASE1_IMPLEMENTED_NAMES
    tools = asyncio.run(mcp.list_tools())
    excluded = excluded_tool_names()
    names = frozenset(t.name for t in tools) - excluded
    IMPLEMENTED_TOOL_NAMES = names
    PHASE1_IMPLEMENTED_NAMES = names
    return names


def _make_stub_fn(
    meta: ToolMeta, audit: Any
) -> Callable[..., Awaitable[dict[str, Any]]]:
    async def stub(justification: str | None = None) -> dict[str, Any]:
        return await run_tool(
            meta, {"justification": justification}, lambda: None, audit=audit
        )

    stub.__name__ = meta.name
    stub.__doc__ = meta.description
    return stub


def register(mcp: FastMCP, client: IiqHttpClient, **ctx: Any) -> None:
    """Register excluded stubs only (everything else is implemented in Python modules)."""
    del client
    audit = ctx.get("audit")

    for entry in load_catalog():
        name = str(entry["name"])
        meta = ToolMeta(
            name=name,
            phase=int(entry.get("phase") or 99),
            risk=Risk(str(entry.get("risk") or "excluded")),
            implemented=False,
            requires_confirmation=bool(entry.get("requires_confirmation")),
            gap_id=entry.get("gap_id"),
            description=str(entry.get("description") or ""),
        )
        desc = tool_description(
            meta,
            meta.description or f"Excluded tool {name}.",
        )
        mcp.tool(name=name, description=desc)(_make_stub_fn(meta, audit))
