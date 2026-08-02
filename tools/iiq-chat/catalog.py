"""Live MCP tool catalog cache for Teller (no static tool routing lists)."""

from __future__ import annotations

import os
import threading
import time
from typing import Any, Callable

from safety import is_write_tool

# Optional one-click presets: MCP tool name → default args (rail shortcuts only).
# These are NOT an LLM routing catalog — free-text always uses live tools/list.
FAVORITE_PRESETS: list[dict[str, Any]] = [
    {"tool": "toolkit_ping", "label": "Toolkit ping", "group": "Health", "args": {}},
    {"tool": "iiq_ping", "label": "IIQ ping", "group": "Health", "args": {}},
    {"tool": "list_uiapi_gaps", "label": "API gaps", "group": "Health", "args": {}},
    {"tool": "get_iiq_status", "label": "IIQ status", "group": "Health", "args": {}},
    {"tool": "list_applications", "label": "Applications", "group": "Apps", "args": {"count": 25}},
    {"tool": "list_iiq_plugins", "label": "Plugins", "group": "Apps", "args": {}},
    {
        "tool": "search_identities",
        "label": "Search people",
        "group": "Identities",
        "args": {"query": "*", "count": 15},
    },
    {
        "tool": "search_profiles",
        "label": "Search profiles",
        "group": "Identities",
        "args": {"query": "Paris", "count": 25},
    },
    {"tool": "list_work_items", "label": "Work items", "group": "Work items", "args": {"count": 25}},
    {"tool": "list_certifications", "label": "Certifications", "group": "Certifications", "args": {"count": 25}},
    {"tool": "count_open_sod_violations", "label": "SoD open count", "group": "Policies", "args": {}},
    {"tool": "list_open_sod_violations", "label": "SoD violations", "group": "Policies", "args": {}},
    {"tool": "list_allowed_toolkit_tasks", "label": "Allowed tasks", "group": "Tasks", "args": {}},
    {"tool": "get_system_config", "label": "System config", "group": "Admin", "args": {}},
]

GROUP_ORDER = [
    "Favorites",
    "Health",
    "Identities",
    "Apps",
    "Access",
    "Work items",
    "Certifications",
    "Policies",
    "Tasks",
    "Admin",
    "Catalog",
    "Other",
]

_TTL = float(os.environ.get("TELLER_TOOL_CACHE_TTL", "60"))


def _group_for_tool(name: str) -> str:
    n = name.lower()
    if any(x in n for x in ("ping", "status", "host", "module", "monitoring", "gaps", "toolkit")):
        return "Health"
    if any(x in n for x in ("identity", "profile", "manager", "account", "password", "unlock", "capability")):
        return "Identities"
    if any(x in n for x in ("application", "aggregat", "connector", "schema", "native_change")):
        return "Apps"
    if any(x in n for x in ("access_request", "role", "entitlement", "requestable", "provision")):
        return "Access"
    if "work_item" in n:
        return "Work items"
    if "certif" in n:
        return "Certifications"
    if any(x in n for x in ("policy", "sod", "violation", "alert")):
        return "Policies"
    if any(x in n for x in ("task", "schedule", "report", "batch")):
        return "Tasks"
    if any(x in n for x in ("plugin", "system", "object", "import", "export", "config", "population", "workgroup")):
        return "Admin"
    if any(x in n for x in ("scim", "form", "email", "quicklink", "workflow", "audit", "rule")):
        return "Catalog"
    return "Other"


def _required_props(schema: dict[str, Any] | None) -> list[str]:
    if not isinstance(schema, dict):
        return []
    req = schema.get("required")
    return [str(x) for x in req] if isinstance(req, list) else []


def _truncate(text: str, limit: int = 280) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


class ToolCatalog:
    """TTL-cached view of MCP tools/list."""

    def __init__(self, ttl: float | None = None) -> None:
        self.ttl = _TTL if ttl is None else ttl
        self._lock = threading.Lock()
        self._tools: list[dict[str, Any]] = []
        self._by_name: dict[str, dict[str, Any]] = {}
        self._fetched_at = 0.0

    def invalidate(self) -> None:
        with self._lock:
            self._tools = []
            self._by_name = {}
            self._fetched_at = 0.0

    def refresh(self, list_fn: Callable[[], list[dict[str, Any]]]) -> list[dict[str, Any]]:
        tools = list_fn()
        with self._lock:
            self._tools = tools
            self._by_name = {str(t["name"]): t for t in tools if t.get("name")}
            self._fetched_at = time.time()
        return tools

    def get(
        self,
        list_fn: Callable[[], list[dict[str, Any]]],
        *,
        force: bool = False,
    ) -> list[dict[str, Any]]:
        with self._lock:
            fresh = self._tools and (time.time() - self._fetched_at) < self.ttl
            if fresh and not force:
                return list(self._tools)
        return self.refresh(list_fn)

    def names(self) -> set[str]:
        with self._lock:
            return set(self._by_name)

    def has(self, name: str) -> bool:
        with self._lock:
            return name in self._by_name

    def openai_tools(self) -> list[dict[str, Any]]:
        """OpenAI/OpenRouter function-calling tool definitions from MCP schemas."""
        out: list[dict[str, Any]] = []
        with self._lock:
            tools = list(self._tools)
        for t in tools:
            name = str(t.get("name") or "")
            if not name:
                continue
            schema = t.get("inputSchema") or t.get("input_schema") or {"type": "object", "properties": {}}
            if not isinstance(schema, dict):
                schema = {"type": "object", "properties": {}}
            # Ensure object schema
            if schema.get("type") != "object":
                schema = {"type": "object", "properties": schema if isinstance(schema, dict) else {}}
            out.append(
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": _truncate(str(t.get("description") or name)),
                        "parameters": schema,
                    },
                }
            )
        return out

    def actions_public(self) -> list[dict[str, Any]]:
        """Rail actions: favorites with presets + live MCP tools."""
        with self._lock:
            by_name = dict(self._by_name)

        actions: list[dict[str, Any]] = []
        seen: set[str] = set()

        for fav in FAVORITE_PRESETS:
            tool = str(fav["tool"])
            if tool not in by_name:
                continue
            meta = by_name[tool]
            actions.append(
                {
                    "id": f"fav:{tool}",
                    "label": fav.get("label") or tool,
                    "group": "Favorites",
                    "description": _truncate(str(meta.get("description") or fav.get("label") or tool)),
                    "tool": tool,
                    "args": fav.get("args") or {},
                    "needsArgs": False,
                    "favorite": True,
                    "llm": False,
                    "write": is_write_tool(tool),
                }
            )
            seen.add(tool)

        for name, meta in sorted(by_name.items()):
            schema = meta.get("inputSchema") or meta.get("input_schema") or {}
            required = _required_props(schema if isinstance(schema, dict) else {})
            needs_args = bool(required)
            actions.append(
                {
                    "id": name,
                    "label": name,
                    "group": _group_for_tool(name),
                    "description": _truncate(str(meta.get("description") or name)),
                    "tool": name,
                    "args": {},
                    "needsArgs": needs_args,
                    "favorite": name in seen,
                    "llm": False,
                    "write": is_write_tool(name),
                }
            )
        return actions


# Process-wide catalog
CATALOG = ToolCatalog()
