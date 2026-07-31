#!/usr/bin/env python3
"""Meridian IIQ Teller — LLM agent over live MCP tools.

  python3 tools/iiq-chat/serve.py
  -> http://localhost:4180/

Env:
  IIQ_MCP_URL          default http://127.0.0.1:8766/mcp
  MCP_API_KEY          Bearer for Docker MCP
  OPENROUTER_API_KEY   required for free-text LLM chat
  OPENROUTER_MODEL     default openrouter/free
  TELLER_TOOL_CACHE_TTL  seconds (default 60)
  TELLER_MAX_AGENT_STEPS default 5
  CHAT_HOST / CHAT_PORT
"""

from __future__ import annotations

import json
import os
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
sys.path.insert(0, str(ROOT))

from catalog import CATALOG, FAVORITE_PRESETS, GROUP_ORDER  # noqa: E402
from llm import LlmError, OpenRouterClient  # noqa: E402
from mcp_client import McpClient, McpError  # noqa: E402
from normalize import normalize_tool_args  # noqa: E402

HOST = os.environ.get("CHAT_HOST", "127.0.0.1")
PORT = int(os.environ.get("CHAT_PORT", "4180"))

_mcp_lock = threading.Lock()
_mcp: McpClient | None = None
_llm = OpenRouterClient()


def get_mcp() -> McpClient:
    global _mcp
    with _mcp_lock:
        if _mcp is None:
            _mcp = McpClient()
        return _mcp


def reset_mcp() -> None:
    global _mcp
    with _mcp_lock:
        _mcp = None
    CATALOG.invalidate()


def _ensure_catalog(*, force: bool = False) -> list[dict[str, Any]]:
    return CATALOG.get(lambda: get_mcp().list_tools(), force=force)


def _resolve_action(action_id: str) -> dict[str, Any] | None:
    """Resolve rail click: fav:<tool> or bare tool name."""
    _ensure_catalog()
    actions = CATALOG.actions_public()
    for a in actions:
        if a["id"] == action_id:
            return a
    # Direct tool name
    if CATALOG.has(action_id):
        return {
            "id": action_id,
            "label": action_id,
            "tool": action_id,
            "args": {},
            "needsArgs": False,
        }
    # Favorite preset by tool
    if action_id.startswith("fav:"):
        tool = action_id[4:]
        for fav in FAVORITE_PRESETS:
            if fav["tool"] == tool:
                return {
                    "id": action_id,
                    "label": fav.get("label") or tool,
                    "tool": tool,
                    "args": fav.get("args") or {},
                    "needsArgs": False,
                }
    return None


class ChatHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC), **kwargs)

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in ("/api/health", "/healthz"):
            return self._health(path)
        if path == "/api/actions":
            return self._actions()
        if path == "/api/config":
            return self._config()
        if path in ("/", "/index.html"):
            return self._serve_index()
        return super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        body = self._read_json()
        if path == "/api/action":
            return self._run_action(body)
        if path == "/api/chat":
            return self._chat(body)
        if path == "/api/tools/refresh":
            return self._refresh_tools()
        self.send_error(404, "Not found")

    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _security_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "base-uri 'self'; "
            "frame-ancestors 'self'",
        )

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self._security_headers()
        self._cors()
        self.end_headers()
        self.wfile.write(data)

    def _text(self, status: int, text: str) -> None:
        data = text.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self._security_headers()
        self._cors()
        self.end_headers()
        self.wfile.write(data)

    def _serve_index(self) -> None:
        index = STATIC / "index.html"
        data = index.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self._security_headers()
        self._cors()
        self.end_headers()
        self.wfile.write(data)

    def end_headers(self) -> None:
        path = urlparse(self.path).path
        if path.endswith((".js", ".css", ".svg", ".png", ".ico", ".woff2")):
            try:
                self._security_headers()
                self.send_header("Cache-Control", "no-cache")
            except Exception:  # noqa: BLE001
                pass
        super().end_headers()

    def _actions(self) -> None:
        try:
            _ensure_catalog()
            actions = CATALOG.actions_public()
        except McpError as exc:
            reset_mcp()
            return self._json(502, {"ok": False, "error": str(exc), "actions": [], "count": 0})
        return self._json(
            200,
            {
                "ok": True,
                "actions": actions,
                "count": len(actions),
                "groups": GROUP_ORDER,
                "source": "mcp:tools/list",
            },
        )

    def _config(self) -> None:
        llm_auth = None
        if _llm.configured:
            llm_auth = _llm.validate_key()
        tool_count = 0
        try:
            tools = _ensure_catalog(force=True)
            tool_count = len(tools)
        except Exception:  # noqa: BLE001
            reset_mcp()
        return self._json(
            200,
            {
                "ok": True,
                "llmConfigured": _llm.configured,
                "llmAuthOk": bool(llm_auth and llm_auth.get("ok")),
                "llmAuth": llm_auth,
                "model": _llm.model,
                "mcpUrl": os.environ.get("IIQ_MCP_URL", "http://127.0.0.1:8766/mcp"),
                "actionCount": tool_count,
                "toolCount": tool_count,
                "agentMode": "native-tools",
                "maxAgentSteps": int(os.environ.get("TELLER_MAX_AGENT_STEPS", "5")),
            },
        )

    def _refresh_tools(self) -> None:
        try:
            tools = _ensure_catalog(force=True)
        except McpError as exc:
            reset_mcp()
            return self._json(502, {"ok": False, "error": str(exc)})
        return self._json(200, {"ok": True, "toolCount": len(tools)})

    def _health(self, path: str) -> None:
        mcp_ok = False
        mcp_detail: Any = None
        tool_count = 0
        try:
            mcp_detail = get_mcp().healthz()
            mcp_ok = True
            tool_count = len(_ensure_catalog())
        except Exception as exc:  # noqa: BLE001
            mcp_detail = str(exc)
            reset_mcp()
        payload = {
            "ok": mcp_ok,
            "mcp": mcp_detail,
            "llmConfigured": _llm.configured,
            "actionCount": tool_count,
            "toolCount": tool_count,
        }
        if path == "/healthz":
            return self._text(200 if mcp_ok else 503, "ok" if mcp_ok else "degraded")
        return self._json(200 if mcp_ok else 503, payload)

    def _run_action(self, body: dict[str, Any]) -> None:
        action_id = str(body.get("id") or "").strip()
        action = _resolve_action(action_id)
        if not action:
            return self._json(404, {"ok": False, "error": f"Unknown action: {action_id}"})
        if action.get("needsArgs") and not (body.get("args") or action.get("args")):
            return self._json(
                200,
                {
                    "ok": False,
                    "mode": "prebaked",
                    "needsArgs": True,
                    "tool": action["tool"],
                    "error": (
                        f"Tool `{action['tool']}` needs arguments — ask in chat, "
                        "e.g. describe what you want done."
                    ),
                },
            )
        args = body.get("args") if isinstance(body.get("args"), dict) else (action.get("args") or {})
        try:
            result = get_mcp().call(action["tool"], args)
        except McpError as exc:
            reset_mcp()
            return self._json(502, {"ok": False, "error": str(exc), "mode": "prebaked"})
        return self._json(
            200,
            {
                "ok": True,
                "mode": "prebaked",
                "action": {
                    "id": action["id"],
                    "label": action.get("label") or action["tool"],
                    "tool": action["tool"],
                },
                "result": result,
            },
        )

    def _chat(self, body: dict[str, Any]) -> None:
        message = str(body.get("message") or "").strip()
        if not message:
            return self._json(400, {"ok": False, "error": "message is required"})
        history = body.get("history") if isinstance(body.get("history"), list) else []

        try:
            tools = _ensure_catalog()
        except McpError as exc:
            reset_mcp()
            return self._json(502, {"ok": False, "error": str(exc), "mode": "llm"})

        openai_tools = CATALOG.openai_tools()
        allowed = CATALOG.names()

        def _search(query: str) -> Any:
            return get_mcp().call("search_identities", {"query": query, "count": 10})

        def call_tool(name: str, args: dict[str, Any]) -> Any:
            fixed = normalize_tool_args(name, args, search_fn=_search)
            return get_mcp().call(name, fixed)

        try:
            outcome = _llm.run_agent(
                message,
                openai_tools,
                call_tool,
                history=history,
                allowed_names=allowed,
            )
        except LlmError as exc:
            return self._json(
                503,
                {
                    "ok": False,
                    "error": str(exc),
                    "mode": "llm",
                    "hint": "Use the tools rail for MCP without an LLM, or set OPENROUTER_API_KEY.",
                },
            )

        steps = outcome.get("steps") or []
        # Attach normalized args view for UI
        for step in steps:
            if "normalizedArguments" not in step and isinstance(step.get("arguments"), dict):
                step["normalizedArguments"] = normalize_tool_args(
                    str(step["tool"]), step["arguments"], search_fn=_search
                )

        return self._json(
            200,
            {
                "ok": True,
                "mode": "llm",
                "model": outcome.get("model"),
                "reply": outcome.get("reply"),
                "tool": outcome.get("tool"),
                "result": outcome.get("result"),
                "steps": steps,
                "toolCount": len(tools),
            },
        )

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode() or "{}")
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}


def main() -> int:
    if not STATIC.is_dir():
        print(f"Missing static dir: {STATIC}", file=sys.stderr)
        return 1
    httpd = ThreadingHTTPServer((HOST, PORT), ChatHandler)
    print("Meridian IIQ Teller (native MCP tool agent)")
    print(f"  UI:      http://{HOST}:{PORT}/")
    print(f"  LLM:     {'OpenRouter ready' if _llm.configured else 'set OPENROUTER_API_KEY for chat'}")
    print(f"  MCP:     {os.environ.get('IIQ_MCP_URL', 'http://127.0.0.1:8766/mcp')}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
