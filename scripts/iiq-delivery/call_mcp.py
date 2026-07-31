#!/usr/bin/env python3
"""Minimal IdentityIQ MCP JSON-RPC client for deterministic scripts."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import MCP_URL  # noqa: E402


class McpError(RuntimeError):
    pass


class McpClient:
    def __init__(self, url: str | None = None, timeout: float = 60.0) -> None:
        self.url = (url or os.environ.get("IIQ_MCP_URL") or MCP_URL).rstrip("/")
        self.timeout = timeout
        self.sid: str | None = None
        self._id = 0

    def _req(self, payload: dict[str, Any]) -> tuple[dict[str, str], dict[str, Any]]:
        data = json.dumps(payload).encode()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.sid:
            headers["mcp-session-id"] = self.sid
        req = urllib.request.Request(self.url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                hdrs = {k.lower(): v for k, v in resp.headers.items()}
                body = resp.read().decode()
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

    def init(self) -> None:
        hdrs, _ = self._req(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "iiq-delivery", "version": "1.0"},
                },
            }
        )
        self.sid = hdrs.get("mcp-session-id")
        self._req({"jsonrpc": "2.0", "method": "notifications/initialized"})
        if not self.sid:
            raise McpError("MCP did not return mcp-session-id")

    def call(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
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
        return msg

    @staticmethod
    def unwrap_text(msg: dict[str, Any]) -> Any:
        """Parse tool result content[0].text JSON if present."""
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


def main() -> int:
    import argparse

    p = argparse.ArgumentParser(description="Call an identityiq MCP tool")
    p.add_argument("tool")
    p.add_argument("--args", default="{}", help="JSON object of tool arguments")
    p.add_argument("--url", default=None)
    p.add_argument("--raw", action="store_true", help="Print full JSON-RPC message")
    args = p.parse_args()
    try:
        client = McpClient(args.url)
        client.init()
        msg = client.call(args.tool, json.loads(args.args))
    except (McpError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    if args.raw:
        print(json.dumps(msg, indent=2))
    else:
        print(json.dumps(client.unwrap_text(msg), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
