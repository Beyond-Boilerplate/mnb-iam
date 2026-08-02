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
import time
import uuid
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
sys.path.insert(0, str(ROOT))

from catalog import CATALOG, FAVORITE_PRESETS, GROUP_ORDER  # noqa: E402
from enrich import enrich_tool_result  # noqa: E402
from llm import LlmCancelled, LlmError, OpenRouterClient  # noqa: E402
from mcp_client import McpClient, McpError  # noqa: E402
from normalize import normalize_tool_args  # noqa: E402
from safety import is_write_tool  # noqa: E402

HOST = os.environ.get("CHAT_HOST", "127.0.0.1")
PORT = int(os.environ.get("CHAT_PORT", "4180"))
CONFIRM_TIMEOUT_SEC = float(os.environ.get("TELLER_CONFIRM_TIMEOUT", "120"))

_mcp_lock = threading.Lock()
_mcp: McpClient | None = None
_llm = OpenRouterClient()

# Active stream runs: runId → {cancel: Event, confirms: {id: {event, decision}}}
_runs_lock = threading.Lock()
_runs: dict[str, dict[str, Any]] = {}


def _new_run() -> str:
    run_id = uuid.uuid4().hex
    with _runs_lock:
        _runs[run_id] = {
            "cancel": threading.Event(),
            "confirms": {},
            "created": time.time(),
        }
    return run_id


def _get_run(run_id: str) -> dict[str, Any] | None:
    with _runs_lock:
        return _runs.get(run_id)


def _finish_run(run_id: str) -> None:
    with _runs_lock:
        _runs.pop(run_id, None)


def _cancel_run(run_id: str) -> bool:
    run = _get_run(run_id)
    if not run:
        return False
    run["cancel"].set()
    # Unblock any waiting confirms as denied
    for conf in list(run.get("confirms", {}).values()):
        conf["decision"] = False
        conf["event"].set()
    return True


def _await_confirm(run_id: str, confirm_id: str, timeout: float) -> bool | None:
    """Return True approve, False deny, None timeout/missing."""
    run = _get_run(run_id)
    if not run:
        return None
    conf = {"event": threading.Event(), "decision": None}
    with _runs_lock:
        if run_id not in _runs:
            return None
        _runs[run_id]["confirms"][confirm_id] = conf
    ok = conf["event"].wait(timeout=timeout)
    with _runs_lock:
        if run_id in _runs:
            _runs[run_id]["confirms"].pop(confirm_id, None)
    if not ok:
        return None
    return bool(conf["decision"])


def _decide_confirm(run_id: str, confirm_id: str, approve: bool) -> bool:
    run = _get_run(run_id)
    if not run:
        return False
    conf = run.get("confirms", {}).get(confirm_id)
    if not conf:
        return False
    conf["decision"] = bool(approve)
    conf["event"].set()
    return True


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
        parsed = urlparse(self.path)
        path = parsed.path
        if path in ("/api/health", "/healthz"):
            return self._health(path)
        if path == "/api/actions":
            return self._actions()
        if path == "/api/config":
            return self._config()
        if path == "/api/suggest":
            return self._suggest(parse_qs(parsed.query))
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
        if path == "/api/chat/stream":
            return self._chat_stream(body)
        if path == "/api/chat/cancel":
            return self._chat_cancel(body)
        if path == "/api/chat/decision":
            return self._chat_decision(body)
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

    def _suggest(self, qs: dict[str, list[str]]) -> None:
        """Autocomplete for @mentions — identities + applications via MCP."""
        q = (qs.get("q") or qs.get("query") or [""])[0].strip()
        kind = ((qs.get("kind") or ["all"])[0] or "all").strip().lower()
        if len(q) < 1:
            return self._json(200, {"ok": True, "query": q, "items": []})

        items: list[dict[str, Any]] = []
        try:
            mcp = get_mcp()
            if kind in ("all", "identity", "identities", "people"):
                raw = mcp.call("search_identities", {"query": q, "count": 8})
                data = (raw or {}).get("data") if isinstance(raw, dict) else None
                rows = []
                if isinstance(data, dict):
                    rows = data.get("items") or []
                elif isinstance(data, list):
                    rows = data
                seen_ids: set[str] = set()
                for row in rows[:12]:
                    if not isinstance(row, dict):
                        continue
                    uname = str(row.get("userName") or "").strip()
                    name = str(row.get("name") or "").strip()
                    display = str(row.get("displayName") or "").strip()
                    # Prefer login-style usernames (anita.rao) over employee ids when both exist
                    candidates = [c for c in (uname, name) if c]
                    key = next(
                        (
                            c
                            for c in candidates
                            if "." in c or (c[:1].islower() and not c.upper().startswith("MNB"))
                        ),
                        None,
                    ) or next(iter(candidates), "") or display
                    if not key:
                        continue
                    dedupe = key.lower()
                    if dedupe in seen_ids:
                        continue
                    seen_ids.add(dedupe)
                    label = display or key
                    # Keep human name + stable key in the chat text so the model
                    # does not treat bare MNB##### values as ticket numbers.
                    if display and display.lower() != key.lower():
                        insert_text = f"{display} ({key})"
                        subtitle = key
                    else:
                        insert_text = key
                        subtitle = "identity"
                    items.append(
                        {
                            "type": "identity",
                            "id": key,
                            "label": label,
                            "subtitle": subtitle,
                            "insert": insert_text,
                        }
                    )
            if kind in ("all", "app", "apps", "application", "applications"):
                raw = mcp.call("list_applications", {"query": q, "count": 8})
                data = (raw or {}).get("data") if isinstance(raw, dict) else None
                rows = []
                if isinstance(data, dict):
                    rows = data.get("items") or data.get("applications") or []
                elif isinstance(data, list):
                    rows = data
                for row in rows[:8]:
                    if not isinstance(row, dict):
                        continue
                    name = str(
                        row.get("name") or row.get("applicationName") or row.get("id") or ""
                    ).strip()
                    if not name:
                        continue
                    app_id = str(row.get("id") or name).strip()
                    items.append(
                        {
                            "type": "app",
                            "id": app_id,
                            "label": name,
                            "subtitle": "application",
                            "insert": name,
                        }
                    )
        except McpError as exc:
            reset_mcp()
            return self._json(502, {"ok": False, "error": str(exc), "items": []})
        except Exception as exc:  # noqa: BLE001
            return self._json(502, {"ok": False, "error": str(exc), "items": []})

        # Prefer login-style inserts, then prefix matches
        ql = q.lower()

        def _loginish(value: str) -> bool:
            s = (value or "").strip()
            return bool(s) and ("." in s or (s[:1].islower() and not s.upper().startswith("MNB")))

        items.sort(
            key=lambda it: (
                0 if _loginish(str(it.get("insert") or "")) else 1,
                0
                if str(it.get("label") or "").lower().startswith(ql)
                or str(it.get("insert") or "").lower().startswith(ql)
                else 1,
                str(it.get("label") or "").lower(),
            )
        )
        return self._json(200, {"ok": True, "query": q, "items": items[:12]})

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
        tool = str(action["tool"])
        write = is_write_tool(tool)
        if body.get("readOnly") and write:
            return self._json(
                403,
                {
                    "ok": False,
                    "error": f"Read-only mode: blocked write tool `{tool}`",
                    "mode": "prebaked",
                    "write": True,
                },
            )
        # Client should confirm writes; require explicit ack for defense in depth
        if write and not body.get("confirmed"):
            return self._json(
                200,
                {
                    "ok": False,
                    "needsConfirm": True,
                    "write": True,
                    "tool": tool,
                    "args": body.get("args")
                    if isinstance(body.get("args"), dict)
                    else (action.get("args") or {}),
                    "error": f"Confirm required before running write tool `{tool}`",
                    "mode": "prebaked",
                },
            )
        args = body.get("args") if isinstance(body.get("args"), dict) else (action.get("args") or {})
        try:
            result = get_mcp().call(tool, args)
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
                    "label": action.get("label") or tool,
                    "tool": tool,
                },
                "result": result,
                "write": write,
            },
        )

    def _make_call_tool(
        self,
        *,
        read_only: bool,
        confirm_writes: bool,
        run_id: str | None,
        on_event: Callable[[str, dict[str, Any]], None] | None,
        search_fn: Callable[[str], Any],
        is_cancelled: Callable[[], bool] | None = None,
    ) -> Callable[[str, dict[str, Any]], Any]:
        def call_tool(name: str, args: dict[str, Any]) -> Any:
            if is_cancelled and is_cancelled():
                raise LlmCancelled("Stopped by operator")
            fixed = normalize_tool_args(name, args, search_fn=search_fn)
            # Stash normalized args for the just-executed call (read by agent loop via wrapper)
            call_tool.last_fixed = fixed  # type: ignore[attr-defined]
            write = is_write_tool(name)
            if read_only and write:
                return {
                    "ok": False,
                    "error": f"Read-only mode: blocked write tool `{name}`",
                    "blocked": "readOnly",
                }
            if confirm_writes and write and run_id and on_event:
                confirm_id = uuid.uuid4().hex
                on_event(
                    "tool_confirm",
                    {
                        "id": confirm_id,
                        "runId": run_id,
                        "tool": name,
                        "arguments": fixed,
                        "write": True,
                    },
                )
                decision = _await_confirm(run_id, confirm_id, CONFIRM_TIMEOUT_SEC)
                if is_cancelled and is_cancelled():
                    raise LlmCancelled("Stopped by operator")
                if decision is None:
                    return {
                        "ok": False,
                        "error": f"Timed out waiting for approval of `{name}`",
                        "blocked": "confirmTimeout",
                    }
                if not decision:
                    return {
                        "ok": False,
                        "error": f"Operator denied `{name}`",
                        "blocked": "denied",
                    }
            raw = get_mcp().call(name, fixed)
            mcp = get_mcp()
            return enrich_tool_result(name, raw, mcp.call)

        call_tool.last_fixed = {}  # type: ignore[attr-defined]
        return call_tool

    def _chat_prepare(
        self,
        body: dict[str, Any],
        *,
        default_confirm_writes: bool = False,
    ) -> tuple[str, list[Any], list[dict[str, Any]], set[str], Any] | dict[str, Any]:
        """Shared prep for /api/chat and /api/chat/stream. Returns err dict on failure."""
        message = str(body.get("message") or "").strip()
        if not message:
            return {"ok": False, "error": "message is required", "status": 400}
        history = body.get("history") if isinstance(body.get("history"), list) else []
        read_only = bool(body.get("readOnly"))
        # Stream defaults to confirmWrites=True; JSON /api/chat defaults False (evals/automation)
        confirm_writes = body.get("confirmWrites")
        if confirm_writes is None:
            confirm_writes = default_confirm_writes
        else:
            confirm_writes = bool(confirm_writes)

        try:
            tools = _ensure_catalog()
        except McpError as exc:
            reset_mcp()
            return {"ok": False, "error": str(exc), "mode": "llm", "status": 502}

        openai_tools = CATALOG.openai_tools()
        allowed = CATALOG.names()
        if read_only:
            openai_tools = [
                t
                for t in openai_tools
                if not is_write_tool(str((t.get("function") or {}).get("name") or ""))
            ]
            allowed = {
                str((t.get("function") or {}).get("name") or "")
                for t in openai_tools
                if (t.get("function") or {}).get("name")
            }

        def _search(query: str) -> Any:
            return get_mcp().call("search_identities", {"query": query, "count": 10})

        flags = {
            "readOnly": read_only,
            "confirmWrites": confirm_writes,
            "search_fn": _search,
            "tools": tools,
        }
        return message, history, openai_tools, allowed, flags

    def _enrich_steps(
        self, steps: list[dict[str, Any]], search_fn: Any = None
    ) -> list[dict[str, Any]]:
        """Attach a display copy of arguments. Do not re-run identity search here —
        that used to add seconds after the model had already finished answering."""
        del search_fn  # kept for call-site compatibility
        for step in steps:
            if "normalizedArguments" not in step and isinstance(step.get("arguments"), dict):
                step["normalizedArguments"] = dict(step["arguments"])
        return steps

    def _chat(self, body: dict[str, Any]) -> None:
        prepared = self._chat_prepare(body, default_confirm_writes=False)
        if isinstance(prepared, dict):
            status = int(prepared.pop("status", 400))
            return self._json(status, prepared)

        message, history, openai_tools, allowed, flags = prepared
        search_fn = flags["search_fn"]
        tools = flags["tools"]
        # JSON chat has no confirm UI — if confirmWrites requested, force read-only writes block
        call_tool = self._make_call_tool(
            read_only=flags["readOnly"] or flags["confirmWrites"],
            confirm_writes=False,
            run_id=None,
            on_event=None,
            search_fn=search_fn,
        )

        try:
            outcome = _llm.run_agent(
                message,
                openai_tools,
                call_tool,
                history=history,
                allowed_names=allowed,
            )
        except LlmCancelled as exc:
            return self._json(499, {"ok": False, "error": str(exc), "mode": "llm", "cancelled": True})
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

        steps = self._enrich_steps(list(outcome.get("steps") or []), search_fn)
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
                "readOnly": flags["readOnly"],
            },
        )

    def _begin_sse(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self._security_headers()
        self._cors()
        self.end_headers()

    def _sse(self, event: str, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, default=str)
        frame = f"event: {event}\ndata: {data}\n\n".encode()
        try:
            self.wfile.write(frame)
            self.wfile.flush()
        except BrokenPipeError:
            pass

    def _chat_cancel(self, body: dict[str, Any]) -> None:
        run_id = str(body.get("runId") or "").strip()
        if not run_id:
            return self._json(400, {"ok": False, "error": "runId is required"})
        ok = _cancel_run(run_id)
        return self._json(200 if ok else 404, {"ok": ok, "runId": run_id, "cancelled": ok})

    def _chat_decision(self, body: dict[str, Any]) -> None:
        run_id = str(body.get("runId") or "").strip()
        confirm_id = str(body.get("id") or body.get("confirmId") or "").strip()
        if not run_id or not confirm_id:
            return self._json(400, {"ok": False, "error": "runId and id are required"})
        approve = bool(body.get("approve"))
        ok = _decide_confirm(run_id, confirm_id, approve)
        return self._json(
            200 if ok else 404,
            {"ok": ok, "runId": run_id, "id": confirm_id, "approve": approve},
        )

    def _chat_stream(self, body: dict[str, Any]) -> None:
        prepared = self._chat_prepare(body, default_confirm_writes=True)
        if isinstance(prepared, dict):
            status = int(prepared.pop("status", 400))
            # Still use SSE so the UI parser stays uniform
            self._begin_sse()
            self._sse("error", {**prepared, "httpStatus": status})
            return

        message, history, openai_tools, allowed, flags = prepared
        search_fn = flags["search_fn"]
        tools = flags["tools"]
        run_id = _new_run()
        run = _get_run(run_id)
        assert run is not None
        cancel_event: threading.Event = run["cancel"]
        client_gone = {"v": False}

        def is_cancelled() -> bool:
            return cancel_event.is_set() or client_gone["v"]

        def emit(event: str, payload: dict[str, Any]) -> None:
            data = json.dumps(payload, default=str)
            frame = f"event: {event}\ndata: {data}\n\n".encode()
            try:
                self.wfile.write(frame)
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                client_gone["v"] = True
                cancel_event.set()

        self._begin_sse()
        emit(
            "run",
            {
                "runId": run_id,
                "readOnly": flags["readOnly"],
                "confirmWrites": flags["confirmWrites"],
            },
        )
        emit("status", {"message": "Connected…", "phase": "start"})

        def on_event(event_type: str, payload: dict[str, Any]) -> None:
            emit(event_type, payload)

        call_tool = self._make_call_tool(
            read_only=flags["readOnly"],
            confirm_writes=flags["confirmWrites"],
            run_id=run_id,
            on_event=on_event,
            search_fn=search_fn,
            is_cancelled=is_cancelled,
        )

        try:
            outcome = _llm.run_agent(
                message,
                openai_tools,
                call_tool,
                history=history,
                allowed_names=allowed,
                on_event=on_event,
                is_cancelled=is_cancelled,
            )
        except LlmCancelled as exc:
            emit(
                "error",
                {"ok": False, "error": str(exc), "mode": "llm", "cancelled": True},
            )
            return
        except LlmError as exc:
            emit(
                "error",
                {
                    "ok": False,
                    "error": str(exc),
                    "mode": "llm",
                    "hint": "Use the tools rail for MCP without an LLM, or set OPENROUTER_API_KEY.",
                },
            )
            return
        finally:
            _finish_run(run_id)

        if is_cancelled():
            emit(
                "error",
                {"ok": False, "error": "Stopped by operator", "mode": "llm", "cancelled": True},
            )
            return

        steps = self._enrich_steps(list(outcome.get("steps") or []), search_fn)
        emit(
            "done",
            {
                "ok": True,
                "mode": "llm",
                "model": outcome.get("model"),
                "reply": outcome.get("reply"),
                "tool": outcome.get("tool"),
                "result": outcome.get("result"),
                "steps": steps,
                "toolCount": len(tools),
                "runId": run_id,
                "readOnly": flags["readOnly"],
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
