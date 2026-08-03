"""IIQ MCP client wrapper with dry-run, denylist, and ledger hooks."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Callable

from .redact import redact

# Reuse Teller MCP client
_IIQ_CHAT = Path(__file__).resolve().parents[2] / "tools" / "iiq-chat"
if str(_IIQ_CHAT) not in sys.path:
    sys.path.insert(0, str(_IIQ_CHAT))

from mcp_client import McpClient, McpError  # noqa: E402
from safety import is_write_tool  # noqa: E402


class WrappedMcp:
    def __init__(
        self,
        *,
        url: str,
        api_key: str = "",
        dry_run: bool = True,
        denylist: list[str] | None = None,
        read_only: bool = False,
        timeout: float = 45.0,
        on_call: Callable[[str, dict[str, Any]], None] | None = None,
        on_result: Callable[[str, dict[str, Any], Any, float, bool], None] | None = None,
    ) -> None:
        self.client = McpClient(url=url, api_key=api_key or None, timeout=timeout)
        self.dry_run = dry_run
        self.denylist = set(denylist or [])
        self.read_only = read_only
        self.on_call = on_call
        self.on_result = on_result
        self._tools_cache: list[dict[str, Any]] | None = None

    def list_tools(self) -> list[dict[str, Any]]:
        if self._tools_cache is None:
            self._tools_cache = self.client.list_tools()
        return self._tools_cache

    def openai_tools(self, *, allow_writes: bool = False) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for t in self.list_tools():
            name = str(t.get("name") or "")
            if not name or name in self.denylist:
                continue
            if not allow_writes and is_write_tool(name):
                continue
            schema = t.get("inputSchema") or t.get("input_schema") or {"type": "object", "properties": {}}
            if not isinstance(schema, dict):
                schema = {"type": "object", "properties": {}}
            if schema.get("type") != "object":
                schema = {"type": "object", "properties": {}}
            out.append(
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": str(t.get("description") or name),
                        "parameters": schema,
                    },
                }
            )
        return out

    def call(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        args = arguments or {}
        safe_args = redact(args)
        if self.on_call:
            self.on_call(name, safe_args if isinstance(safe_args, dict) else {"_": safe_args})

        if name in self.denylist:
            result = {"ok": False, "error": f"Tool denylisted: {name}"}
            if self.on_result:
                self.on_result(name, safe_args if isinstance(safe_args, dict) else {}, result, 0.0, False)
            return result

        write = is_write_tool(name)
        if self.read_only and write:
            result = {"ok": False, "error": f"Read-only mode blocked write tool: {name}"}
            if self.on_result:
                self.on_result(name, safe_args if isinstance(safe_args, dict) else {}, result, 0.0, False)
            return result

        if self.dry_run and write:
            result = {
                "ok": True,
                "dry_run": True,
                "tool": name,
                "arguments": safe_args,
                "message": "Skipped mutating MCP call (dry_run=true). Pass --live to execute.",
            }
            if self.on_result:
                self.on_result(name, safe_args if isinstance(safe_args, dict) else {}, result, 0.0, True)
            return result

        t0 = time.perf_counter()
        try:
            raw = self.client.call(name, args)
            ok = not (isinstance(raw, dict) and raw.get("ok") is False)
            result = redact(raw)
        except McpError as exc:
            ok = False
            result = {"ok": False, "error": str(exc)}
        elapsed = time.perf_counter() - t0
        if self.on_result:
            self.on_result(
                name,
                safe_args if isinstance(safe_args, dict) else {},
                result,
                elapsed,
                ok,
            )
        return result


def brief_result(result: Any) -> str:
    if isinstance(result, dict):
        if result.get("dry_run"):
            return f"dry_run skip {result.get('tool')}"
        if result.get("ok") is False:
            return f"error: {str(result.get('error'))[:160]}"
        return json.dumps(result, default=str)[:200]
    return str(result)[:200]
