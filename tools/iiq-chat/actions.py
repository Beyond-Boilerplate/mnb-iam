"""Compatibility shim — rail actions come from live MCP via catalog.py.

Kept so older imports (`from actions import …`) do not break. Prefer `catalog`.
"""

from __future__ import annotations

from typing import Any

from catalog import CATALOG, FAVORITE_PRESETS, GROUP_ORDER

# Deprecated: empty stand-in. Live list is CATALOG.actions_public() after MCP refresh.
ACTIONS: list[dict[str, Any]] = []

# Explicitly removed — LLM routing uses MCP tools/list only.
LLM_TOOL_CATALOG: list[dict[str, Any]] = []


def get_action(action_id: str) -> dict[str, Any] | None:
    for a in CATALOG.actions_public():
        if a["id"] == action_id:
            return a
    return None


def actions_public() -> list[dict[str, Any]]:
    return CATALOG.actions_public()


__all__ = [
    "ACTIONS",
    "LLM_TOOL_CATALOG",
    "FAVORITE_PRESETS",
    "GROUP_ORDER",
    "get_action",
    "actions_public",
]
