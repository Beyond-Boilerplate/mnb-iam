#!/usr/bin/env python3
"""IdentityIQ MCP JSON-RPC client for the Meridian chatbot."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


class McpError(RuntimeError):
    pass


class McpClient:
    def __init__(
        self,
        url: str | None = None,
        api_key: str | None = None,
        timeout: float = 90.0,
    ) -> None:
        self.url = (url or os.environ.get("IIQ_MCP_URL") or "http://127.0.0.1:8766/mcp").rstrip(
            "/"
        )
        self.api_key = (
            api_key
            if api_key is not None
            else os.environ.get("MCP_API_KEY") or os.environ.get("IIQ_MCP_API_KEY") or ""
        )
        self.timeout = timeout
        self.sid: str | None = None
        self._id = 0

    def _headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if self.sid:
            headers["mcp-session-id"] = self.sid
        return headers

    def _req(self, payload: dict[str, Any]) -> tuple[dict[str, str], dict[str, Any]]:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(self.url, data=data, headers=self._headers(), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                hdrs = {k.lower(): v for k, v in resp.headers.items()}
                body = resp.read().decode()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:500]
            raise McpError(f"MCP HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise McpError(f"MCP unreachable at {self.url}: {exc}") from exc

        msg: dict[str, Any] = {}
        for line in body.splitlines():
            if line.startswith("data: "):
                msg = json.loads(line[6:])
                break
        if not msg and body.strip().startswith("{"):
            msg = json.loads(body)
        return hdrs, msg

    def _rpc(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.sid and method != "initialize":
            self.init()
        self._id += 1
        _, msg = self._req(
            {
                "jsonrpc": "2.0",
                "id": self._id,
                "method": method,
                "params": params or {},
            }
        )
        if "error" in msg:
            raise McpError(str(msg["error"]))
        result = msg.get("result")
        return result if isinstance(result, dict) else {"value": result}

    def init(self) -> None:
        hdrs, _ = self._req(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "iiq-chat", "version": "2.0"},
                },
            }
        )
        self.sid = hdrs.get("mcp-session-id")
        self._req({"jsonrpc": "2.0", "method": "notifications/initialized"})
        if not self.sid:
            raise McpError("MCP did not return mcp-session-id")

    def list_tools(self) -> list[dict[str, Any]]:
        """Return all MCP tools (paginated tools/list)."""
        if not self.sid:
            self.init()
        tools: list[dict[str, Any]] = []
        cursor: str | None = None
        for _ in range(50):
            params: dict[str, Any] = {}
            if cursor:
                params["cursor"] = cursor
            result = self._rpc("tools/list", params)
            batch = result.get("tools") or []
            if isinstance(batch, list):
                tools.extend(t for t in batch if isinstance(t, dict) and t.get("name"))
            cursor = result.get("nextCursor") or result.get("cursor")
            if not cursor:
                break
        return tools

    def call(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        if not self.sid:
            self.init()
        self._id += 1
        _, msg = self._req(
            {
                "jsonrpc": "2.0",
                "id": self._id,
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments or {}},
            }
        )
        if "error" in msg:
            raise McpError(str(msg["error"]))
        return self.unwrap_text(msg)

    @staticmethod
    def unwrap_text(msg: dict[str, Any]) -> Any:
        result = msg.get("result") or {}
        content = result.get("content") or []
        if not content:
            return result
        text = content[0].get("text") if isinstance(content[0], dict) else None
        if not text:
            return result
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw_text": text}

    def healthz(self) -> dict[str, Any]:
        base = self.url.rsplit("/mcp", 1)[0]
        url = f"{base}/healthz"
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
