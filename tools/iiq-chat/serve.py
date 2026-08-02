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

import base64
import json
import os
import sys
import threading
import time
import uuid
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError
from urllib.parse import parse_qs, quote, urlencode, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
sys.path.insert(0, str(ROOT))

from cards import build_cards  # noqa: E402
from catalog import CATALOG, FAVORITE_PRESETS, GROUP_ORDER  # noqa: E402
from enrich import enrich_tool_result  # noqa: E402
from feedback_store import store_feedback  # noqa: E402
from llm import LlmCancelled, LlmError, OpenRouterClient  # noqa: E402
from mcp_client import McpClient, McpError  # noqa: E402
from normalize import normalize_tool_args  # noqa: E402
from observability import (  # noqa: E402
    METRICS,
    log_event,
    new_correlation_id,
    timed,
)
from playbooks_loader import playbooks_for_role  # noqa: E402
from safety import is_write_tool  # noqa: E402

HOST = os.environ.get("CHAT_HOST", "127.0.0.1")
PORT = int(os.environ.get("CHAT_PORT", "4180"))
CONFIRM_TIMEOUT_SEC = float(os.environ.get("TELLER_CONFIRM_TIMEOUT", "120"))
IIQ_BASE_URL = os.environ.get("IIQ_BASE_URL", "http://127.0.0.1:8080/identityiq").rstrip("/")
IIQ_USER = os.environ.get("IIQ_USER", "spadmin")
IIQ_PASSWORD = os.environ.get("IIQ_PASSWORD", "admin")

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


def _iiq_basic_headers() -> dict[str, str]:
    token = base64.b64encode(f"{IIQ_USER}:{IIQ_PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {token}", "Accept": "application/json"}


def _scim_get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    q = urlencode({k: v for k, v in (params or {}).items() if v is not None})
    url = f"{IIQ_BASE_URL}/scim/v2{path}"
    if q:
        url = f"{url}?{q}"
    req = Request(url, headers=_iiq_basic_headers())
    with urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def _scim_all_users() -> list[dict[str, Any]]:
    users: list[dict[str, Any]] = []
    start = 1
    while True:
        page = _scim_get("/Users", {"startIndex": start, "count": 100})
        batch = page.get("Resources") or []
        users.extend(batch)
        total = int(page.get("totalResults") or 0)
        if start + len(batch) > total or not batch:
            break
        start += len(batch)
    return users


def _orgchart_from_scim(params: dict[str, str]) -> dict[str, Any]:
    include_inactive = str(params.get("includeInactive", "false")).lower() in ("1", "true", "yes")
    mode = (params.get("mode") or "company").lower()
    root_key = (params.get("root") or "").strip()
    max_depth = max(1, min(int(params.get("depth") or 14), 20))

    users = _scim_all_users()
    by_id: dict[str, dict[str, Any]] = {}
    for u in users:
        uid = u.get("id")
        uname = u.get("userName") or ""
        if not uid or not uname:
            continue
        if uname.lower() in {"spadmin"} or uname.lower().startswith("iiq"):
            continue
        if not include_inactive and u.get("active") is False:
            continue
        sail = u.get("urn:ietf:params:scim:schemas:sailpoint:1.0:User") or {}
        ent = u.get("urn:ietf:params:scim:schemas:extension:enterprise:2.0:User") or {}
        mgr = ent.get("manager") or {}
        email = None
        for e in u.get("emails") or []:
            if e.get("value"):
                email = e["value"]
                break
        by_id[uid] = {
            "id": uid,
            "name": uname,
            "displayName": u.get("displayName") or uname,
            "email": email,
            "inactive": u.get("active") is False,
            "isManager": sail.get("isManager"),
            "title": sail.get("jobCode") or None,
            "department": None,
            "jobCode": sail.get("jobCode"),
            "userId": sail.get("userId") or uname,
            "employeeType": sail.get("employeeType"),
            "location": None,
            "managerId": mgr.get("value"),
            "children": [],
        }

    children: dict[str, list[str]] = {i: [] for i in by_id}
    for node in by_id.values():
        mid = node.get("managerId")
        if mid and mid in by_id:
            children[mid].append(node["id"])

    def build(nid: str, depth: int, stack: set[str]) -> dict[str, Any]:
        n = dict(by_id[nid])
        kids = sorted(children.get(nid) or [], key=lambda i: (by_id[i]["displayName"] or "").lower())
        n["directReports"] = len(kids)
        n["depth"] = depth
        out_kids = []
        if depth < max_depth and nid not in stack:
            stack.add(nid)
            out_kids = [build(k, depth + 1, stack) for k in kids]
            stack.remove(nid)
        n["children"] = out_kids
        n["truncated"] = depth >= max_depth and bool(kids)
        n.pop("managerId", None)
        return n

    def count_nodes(n: dict[str, Any]) -> int:
        return 1 + sum(count_nodes(c) for c in n.get("children") or [])

    forest: list[dict[str, Any]] = []
    if mode == "subtree" or root_key:
        root_id = None
        for nid, n in by_id.items():
            if n["name"] == root_key or n.get("userId") == root_key or n["displayName"] == root_key:
                root_id = nid
                break
        if not root_id:
            raise ValueError(f"root not found: {root_key}")
        tree = build(root_id, 0, set())
        forest = [tree]
    else:
        roots = []
        for nid, n in by_id.items():
            mid = n.get("managerId")
            if mid and mid in by_id:
                continue
            if children.get(nid):
                roots.append(nid)
        roots.sort(key=lambda i: (-len(children.get(i) or []), (by_id[i]["displayName"] or "").lower()))
        forest = [build(r, 0, set()) for r in roots]

    node_count = sum(count_nodes(t) for t in forest)
    return {
        "mode": "subtree" if (mode == "subtree" or root_key) else "company",
        "root": root_key or None,
        "maxDepth": max_depth,
        "includeInactive": include_inactive,
        "includeTechnical": False,
        "forestCount": len(forest),
        "nodeCount": node_count,
        "identityUniverse": len(by_id),
        "forest": forest,
        "source": "SCIM Users manager links (fallback)",
    }


def _orgchart_search_scim(q: str, limit: int) -> list[dict[str, Any]]:
    if len(q) < 2:
        return []
    ql = q.lower()
    hits = []
    for u in _scim_all_users():
        uname = u.get("userName") or ""
        display = u.get("displayName") or ""
        email = ""
        for e in u.get("emails") or []:
            if e.get("value"):
                email = e["value"]
                break
        blob = f"{uname} {display} {email}".lower()
        if ql not in blob:
            continue
        sail = u.get("urn:ietf:params:scim:schemas:sailpoint:1.0:User") or {}
        ent = u.get("urn:ietf:params:scim:schemas:extension:enterprise:2.0:User") or {}
        mgr = ent.get("manager") or {}
        hits.append(
            {
                "id": u.get("id"),
                "name": uname,
                "displayName": display,
                "email": email or None,
                "userId": sail.get("userId") or uname,
                "managerName": None,
                "managerDisplayName": mgr.get("displayName"),
            }
        )
        if len(hits) >= limit:
            break
    return hits


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

    def _correlation_id(self) -> str:
        hdr = (self.headers.get("X-Correlation-Id") or self.headers.get("X-Request-Id") or "").strip()
        return hdr or new_correlation_id()

    def _user_id(self, body: dict[str, Any] | None = None) -> str:
        if body and body.get("userId"):
            return str(body.get("userId"))[:128]
        hdr = (self.headers.get("X-User-Id") or "").strip()
        return hdr[:128] if hdr else "anonymous"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        if path in ("/api/health", "/healthz"):
            return self._health(path)
        if path == "/api/actions":
            return self._actions()
        if path == "/api/config":
            return self._config()
        if path == "/api/playbooks":
            return self._playbooks(parse_qs(parsed.query))
        if path == "/api/metrics":
            return self._metrics()
        if path == "/api/suggest":
            return self._suggest(parse_qs(parsed.query))
        if path == "/api/orgchart":
            return self._orgchart(parse_qs(parsed.query))
        if path == "/api/orgchart/search":
            return self._orgchart_search(parse_qs(parsed.query))
        if path.startswith("/api/console/"):
            return self._console_get(path, parse_qs(parsed.query))
        if path in ("/", "/index.html"):
            return self._serve_index()
        if path in ("/orgchart", "/orgchart.html"):
            return self._serve_static_file("orgchart.html", "text/html; charset=utf-8")
        if path in ("/console", "/console.html"):
            return self._serve_static_file("console.html", "text/html; charset=utf-8")
        # Deep links into Teller Inspect (/identity/anita.rao, /cert/..., /app/...)
        if path.startswith(("/identity/", "/cert/", "/app/", "/entitlement/")):
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
        if path == "/api/feedback":
            return self._feedback(body)
        if path == "/api/tools/refresh":
            return self._refresh_tools()
        if path.startswith("/api/console/"):
            return self._console_post(path, body)
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
        return self._serve_static_file("index.html", "text/html; charset=utf-8")

    def _serve_static_file(self, name: str, content_type: str) -> None:
        path = STATIC / name
        if not path.is_file():
            return self.send_error(404, "Not found")
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self._security_headers()
        self._cors()
        self.end_headers()
        self.wfile.write(data)

    def _iiq_plugin_get(self, plugin_path: str, params: dict[str, str] | None = None) -> tuple[int, Any]:
        """GET IdentityIQ plugin REST; returns (status, json_or_text)."""
        import base64
        import urllib.error
        import urllib.parse
        import urllib.request

        q = urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v is not None and v != ""})
        url = f"{IIQ_BASE_URL}/plugin/rest{plugin_path}"
        if q:
            url = f"{url}?{q}"
        req = urllib.request.Request(url)
        token = base64.b64encode(f"{IIQ_USER}:{IIQ_PASSWORD}".encode()).decode()
        req.add_header("Authorization", f"Basic {token}")
        req.add_header("Accept", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read().decode()
                try:
                    return resp.status, json.loads(raw) if raw else {}
                except json.JSONDecodeError:
                    return resp.status, {"raw": raw[:2000]}
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode(errors="replace")
            try:
                return exc.code, json.loads(raw) if raw else {"error": str(exc)}
            except json.JSONDecodeError:
                return exc.code, {"error": str(exc), "raw": raw[:2000]}
        except Exception as exc:  # noqa: BLE001
            return 502, {"error": str(exc)}

    def _orgchart(self, qs: dict[str, list[str]]) -> None:
        params = {
            "mode": (qs.get("mode") or ["company"])[0],
            "root": (qs.get("root") or [""])[0],
            "depth": (qs.get("depth") or ["14"])[0],
            "includeInactive": (qs.get("includeInactive") or ["false"])[0],
            "includeTechnical": (qs.get("includeTechnical") or ["false"])[0],
        }
        status, body = self._iiq_plugin_get("/mnbToolkit/agent/orgchart", params)
        if status < 300 and isinstance(body, dict) and body.get("status") == "ok":
            return self._json(200, {"ok": True, "source": "toolkit", **body})
        # Fallback: assemble from SCIM (works before plugin upgrade)
        try:
            forest_payload = _orgchart_from_scim(params)
            return self._json(200, {"ok": True, "source": "scim-fallback", "status": "ok", "data": forest_payload})
        except Exception as exc:  # noqa: BLE001
            return self._json(
                status if status >= 400 else 502,
                {
                    "ok": False,
                    "error": (body.get("detail") if isinstance(body, dict) else None)
                    or (body.get("error") if isinstance(body, dict) else None)
                    or str(exc),
                    "toolkitStatus": status,
                    "toolkitBody": body if isinstance(body, dict) else {"raw": str(body)[:500]},
                },
            )

    def _orgchart_search(self, qs: dict[str, list[str]]) -> None:
        q = (qs.get("q") or [""])[0].strip()
        limit = (qs.get("limit") or ["20"])[0]
        status, body = self._iiq_plugin_get("/mnbToolkit/agent/orgchart/search", {"q": q, "limit": limit})
        if status < 300 and isinstance(body, dict) and body.get("status") == "ok":
            return self._json(200, {"ok": True, "source": "toolkit", **body})
        try:
            results = _orgchart_search_scim(q, int(limit))
            return self._json(
                200,
                {"ok": True, "source": "scim-fallback", "status": "ok", "data": {"q": q, "count": len(results), "results": results}},
            )
        except Exception as exc:  # noqa: BLE001
            return self._json(502, {"ok": False, "error": str(exc), "toolkitStatus": status})

    def _iiq_plugin_post(self, plugin_path: str, payload: dict[str, Any] | None = None) -> tuple[int, Any]:
        import base64
        import urllib.error
        import urllib.request

        url = f"{IIQ_BASE_URL}/plugin/rest{plugin_path}"
        data = json.dumps(payload or {}).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        token = base64.b64encode(f"{IIQ_USER}:{IIQ_PASSWORD}".encode()).decode()
        req.add_header("Authorization", f"Basic {token}")
        req.add_header("Accept", "application/json")
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                raw = resp.read().decode()
                try:
                    return resp.status, json.loads(raw) if raw else {}
                except json.JSONDecodeError:
                    return resp.status, {"raw": raw[:2000]}
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode(errors="replace")
            try:
                return exc.code, json.loads(raw) if raw else {"error": str(exc)}
            except json.JSONDecodeError:
                return exc.code, {"error": str(exc), "raw": raw[:2000]}
        except Exception as exc:  # noqa: BLE001
            return 502, {"error": str(exc)}

    def _console_get(self, path: str, qs: dict[str, list[str]]) -> None:
        name = path.removeprefix("/api/console/").strip("/")
        allowed = {
            "summary",
            "orphans",
            "pipeline",
            "inbox",
            "catalog",
            "certs",
            "sod",
            "identity360",
            "jml",
            "evidence",
            "provisioning",
            "workgroups",
            "heatmap",
            "audit",
            "menu",
        }
        # Nested: certs/{id}
        plugin_tail = name
        if name.startswith("certs/") and len(name) > len("certs/"):
            plugin_tail = name
        elif name not in allowed:
            return self._json(404, {"ok": False, "error": f"unknown console route: {name}"})
        params = {k: (v[0] if v else "") for k, v in qs.items()}
        status, body = self._iiq_plugin_get(f"/mnbToolkit/agent/console/{plugin_tail}", params)
        if status < 300 and isinstance(body, dict) and body.get("status") == "ok":
            return self._json(200, {"ok": True, "source": "toolkit", **body})
        return self._json(
            status if status >= 400 else 502,
            {
                "ok": False,
                "error": (body.get("detail") if isinstance(body, dict) else None)
                or (body.get("error") if isinstance(body, dict) else None)
                or f"toolkit HTTP {status}",
                "toolkitBody": body if isinstance(body, dict) else {"raw": str(body)[:500]},
            },
        )

    def _console_post(self, path: str, body: dict[str, Any] | None) -> None:
        name = path.removeprefix("/api/console/").strip("/")
        payload = body if isinstance(body, dict) else {}
        if name == "merge":
            orphan = str(payload.get("orphan") or "").strip()
            into = str(payload.get("into") or "").strip()
            if not orphan or not into:
                return self._json(400, {"ok": False, "error": "orphan and into required"})
            status, resp = self._iiq_plugin_post(
                f"/mnbToolkit/agent/identities/{quote(orphan, safe='')}/merge",
                {"into": into},
            )
        elif name == "correlate":
            status, resp = self._iiq_plugin_post("/mnbToolkit/agent/accounts/correlate", payload)
        elif name == "decide-workitem":
            wid = str(payload.get("id") or "").strip()
            if not wid:
                return self._json(400, {"ok": False, "error": "id required"})
            status, resp = self._iiq_plugin_post(
                f"/mnbToolkit/agent/workItems/{quote(wid, safe='')}/decide",
                {"decision": payload.get("decision"), "comment": payload.get("comment")},
            )
        elif name == "mitigate-sod":
            vid = str(payload.get("id") or "").strip()
            if not vid:
                return self._json(400, {"ok": False, "error": "id required"})
            status, resp = self._iiq_plugin_post(
                f"/mnbToolkit/agent/sod/violations/{quote(vid, safe='')}/mitigate",
                {"comment": payload.get("comment")},
            )
        elif name == "retry-prov":
            tid = str(payload.get("id") or "").strip()
            if not tid:
                return self._json(400, {"ok": False, "error": "id required"})
            status, resp = self._iiq_plugin_post(
                f"/mnbToolkit/agent/provisioning/{quote(tid, safe='')}/retry",
                {},
            )
        elif name == "decide-cert":
            iid = str(payload.get("id") or "").strip()
            if not iid:
                return self._json(400, {"ok": False, "error": "id required"})
            status, resp = self._iiq_plugin_post(
                f"/mnbToolkit/agent/certifications/items/{quote(iid, safe='')}/decide",
                {"decision": payload.get("decision"), "comment": payload.get("comment")},
            )
        elif name == "sign-cert":
            cid = str(payload.get("id") or "").strip()
            if not cid:
                return self._json(400, {"ok": False, "error": "id required"})
            status, resp = self._iiq_plugin_post(
                f"/mnbToolkit/agent/certifications/{quote(cid, safe='')}/sign",
                {},
            )
        elif name == "grant-access":
            status, resp = self._iiq_plugin_post(
                "/mnbToolkit/agent/access/grant",
                {
                    "identityName": payload.get("identityName") or payload.get("identity"),
                    "accessName": payload.get("accessName") or payload.get("access"),
                    "accessType": payload.get("accessType") or payload.get("type"),
                },
            )
        elif name == "identity-password":
            iname = str(payload.get("identity") or payload.get("name") or "").strip()
            if not iname:
                return self._json(400, {"ok": False, "error": "identity required"})
            status, resp = self._iiq_plugin_post(
                f"/mnbToolkit/agent/identities/{quote(iname, safe='')}/password",
                {"op": payload.get("op"), "password": payload.get("password")},
            )
        elif name == "bulk-decide-workitems":
            ids = payload.get("ids") or []
            decision = payload.get("decision")
            if not isinstance(ids, list) or not ids or not decision:
                return self._json(400, {"ok": False, "error": "ids[] and decision required"})
            results = []
            ok_n = 0
            for wid in ids:
                st, resp = self._iiq_plugin_post(
                    f"/mnbToolkit/agent/workItems/{quote(str(wid), safe='')}/decide",
                    {"decision": decision, "comment": payload.get("comment")},
                )
                results.append({"id": wid, "status": st, "ok": st < 300, "body": resp})
                if st < 300:
                    ok_n += 1
            return self._json(
                200,
                {
                    "ok": ok_n == len(ids),
                    "source": "toolkit",
                    "status": "ok",
                    "data": {"decided": ok_n, "total": len(ids), "results": results},
                },
            )
        else:
            return self._json(404, {"ok": False, "error": f"unknown console action: {name}"})
        if status < 300 and isinstance(resp, dict) and resp.get("status") == "ok":
            return self._json(200, {"ok": True, "source": "toolkit", **resp})
        return self._json(
            status if status >= 400 else 502,
            {
                "ok": False,
                "error": (resp.get("detail") if isinstance(resp, dict) else None)
                or (resp.get("error") if isinstance(resp, dict) else None)
                or f"toolkit HTTP {status}",
                "toolkitBody": resp if isinstance(resp, dict) else {"raw": str(resp)[:500]},
            },
        )

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
        mcp_ok = False
        try:
            tools = _ensure_catalog(force=True)
            tool_count = len(tools)
            mcp_ok = True
        except Exception:  # noqa: BLE001
            reset_mcp()
        METRICS.set_mcp(mcp_ok)
        pb = playbooks_for_role()
        llm_ok = bool(llm_auth and llm_auth.get("ok"))
        degraded = []
        if not mcp_ok:
            degraded.append("mcp")
        if not _llm.configured or not llm_ok:
            degraded.append("llm")
        return self._json(
            200,
            {
                "ok": True,
                "llmConfigured": _llm.configured,
                "llmAuthOk": llm_ok,
                "llmAuth": llm_auth,
                "model": _llm.model,
                "mcpUrl": os.environ.get("IIQ_MCP_URL", "http://127.0.0.1:8766/mcp"),
                "mcpOk": mcp_ok,
                "actionCount": tool_count,
                "toolCount": tool_count,
                "agentMode": "native-tools",
                "maxAgentSteps": int(os.environ.get("TELLER_MAX_AGENT_STEPS", "5")),
                "playbookRole": pb.get("role"),
                "degraded": degraded,
                "toolsOnly": (not _llm.configured) or (not llm_ok),
            },
        )

    def _playbooks(self, qs: dict[str, list[str]]) -> None:
        role = (qs.get("role") or [None])[0]
        return self._json(200, playbooks_for_role(role))

    def _metrics(self) -> None:
        snap = METRICS.snapshot()
        return self._json(200, {"ok": True, **snap})

    def _feedback(self, body: dict[str, Any]) -> None:
        rating = str(body.get("rating") or "").strip().lower()
        if rating not in ("up", "down"):
            return self._json(400, {"ok": False, "error": "rating must be up or down"})
        reason = body.get("reason")
        if reason is not None:
            reason = str(reason).strip().lower()
            if reason not in ("wrong_tool", "wrong_answer", "incomplete", "other", ""):
                return self._json(400, {"ok": False, "error": "invalid reason"})
        cid = self._correlation_id()
        record = store_feedback(
            {
                **body,
                "rating": rating,
                "reason": reason or None,
                "correlationId": body.get("correlationId") or cid,
                "userId": self._user_id(body),
            }
        )
        METRICS.inc(f"feedback.{rating}")
        if reason:
            METRICS.inc(f"feedback.reason.{reason}")
        log_event(
            "feedback",
            correlation_id=cid,
            user_id=self._user_id(body),
            run_id=str(body.get("runId") or "") or None,
            outcome=rating,
            reason=reason,
        )
        return self._json(200, record)

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
        METRICS.set_mcp(mcp_ok)
        llm_ok = False
        if _llm.configured:
            try:
                llm_ok = bool((_llm.validate_key() or {}).get("ok"))
            except Exception:  # noqa: BLE001
                llm_ok = False
        payload = {
            "ok": mcp_ok,
            "mcp": mcp_detail,
            "llmConfigured": _llm.configured,
            "llmAuthOk": llm_ok,
            "actionCount": tool_count,
            "toolCount": tool_count,
            "degraded": (["mcp"] if not mcp_ok else []) + (["llm"] if not llm_ok else []),
            "toolsOnly": not llm_ok,
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
        correlation_id: str | None = None,
        user_id: str | None = None,
    ) -> Callable[[str, dict[str, Any]], Any]:
        def call_tool(name: str, args: dict[str, Any]) -> Any:
            if is_cancelled and is_cancelled():
                raise LlmCancelled("Stopped by operator")
            fixed = normalize_tool_args(name, args, search_fn=search_fn)
            # Stash normalized args for the just-executed call (read by agent loop via wrapper)
            call_tool.last_fixed = fixed  # type: ignore[attr-defined]
            write = is_write_tool(name)
            if read_only and write:
                METRICS.inc("tool.blocked.readOnly")
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
                    METRICS.inc("confirm.timeout")
                    return {
                        "ok": False,
                        "error": f"Timed out waiting for approval of `{name}`",
                        "blocked": "confirmTimeout",
                    }
                if not decision:
                    log_event(
                        "tool_confirm",
                        correlation_id=correlation_id,
                        user_id=user_id,
                        run_id=run_id,
                        tool=name,
                        outcome="denied",
                    )
                    return {
                        "ok": False,
                        "error": f"Operator denied `{name}`",
                        "blocked": "denied",
                    }
            with timed(
                "tool.latency_ms",
                event="mcp_tool",
                correlation_id=correlation_id,
                run_id=run_id,
                tool=name,
                user_id=user_id,
                write=write,
            ) as ctx:
                try:
                    raw = get_mcp().call(name, fixed)
                    mcp = get_mcp()
                    result = enrich_tool_result(name, raw, mcp.call)
                    ok = not (isinstance(result, dict) and result.get("ok") is False)
                    ctx["outcome"] = "success" if ok else "error"
                    METRICS.inc("tool.ok" if ok else "tool.error")
                    return result
                except Exception:
                    METRICS.inc("tool.error")
                    ctx["outcome"] = "error"
                    raise

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
        cid = self._correlation_id()
        uid = self._user_id(body)
        prepared = self._chat_prepare(body, default_confirm_writes=False)
        if isinstance(prepared, dict):
            status = int(prepared.pop("status", 400))
            METRICS.inc("chat.error")
            return self._json(status, {**prepared, "correlationId": cid})

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
            correlation_id=cid,
            user_id=uid,
        )

        try:
            with timed(
                "chat.latency_ms",
                event="chat",
                correlation_id=cid,
                user_id=uid,
                mode="json",
            ) as ctx:
                outcome = _llm.run_agent(
                    message,
                    openai_tools,
                    call_tool,
                    history=history,
                    allowed_names=allowed,
                )
                if outcome.get("fallbackUsed"):
                    METRICS.inc("llm.fallback")
                ctx["outcome"] = "success"
        except LlmCancelled as exc:
            METRICS.inc("chat.cancelled")
            return self._json(
                499,
                {
                    "ok": False,
                    "error": str(exc),
                    "mode": "llm",
                    "cancelled": True,
                    "correlationId": cid,
                },
            )
        except LlmError as exc:
            METRICS.inc("chat.error")
            METRICS.inc("llm.error")
            return self._json(
                503,
                {
                    "ok": False,
                    "error": str(exc),
                    "mode": "llm",
                    "hint": "Use the tools rail for MCP without an LLM, or set OPENROUTER_API_KEY.",
                    "correlationId": cid,
                    "toolsOnly": True,
                },
            )

        steps = self._enrich_steps(list(outcome.get("steps") or []), search_fn)
        cards = build_cards(steps)
        METRICS.inc("chat.ok")
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
                "cards": cards,
                "toolCount": len(tools),
                "readOnly": flags["readOnly"],
                "correlationId": cid,
                "fallbackUsed": bool(outcome.get("fallbackUsed")),
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
        if ok:
            METRICS.inc("confirm.approved" if approve else "confirm.denied")
        return self._json(
            200 if ok else 404,
            {"ok": ok, "runId": run_id, "id": confirm_id, "approve": approve},
        )

    def _chat_stream(self, body: dict[str, Any]) -> None:
        cid = self._correlation_id()
        uid = self._user_id(body)
        prepared = self._chat_prepare(body, default_confirm_writes=True)
        if isinstance(prepared, dict):
            status = int(prepared.pop("status", 400))
            METRICS.inc("chat.error")
            # Still use SSE so the UI parser stays uniform
            self._begin_sse()
            self._sse("error", {**prepared, "httpStatus": status, "correlationId": cid})
            return

        message, history, openai_tools, allowed, flags = prepared
        search_fn = flags["search_fn"]
        tools = flags["tools"]
        run_id = _new_run()
        run = _get_run(run_id)
        assert run is not None
        cancel_event: threading.Event = run["cancel"]
        client_gone = {"v": False}
        started = time.perf_counter()

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
                "correlationId": cid,
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
            correlation_id=cid,
            user_id=uid,
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
            METRICS.inc("chat.cancelled")
            emit(
                "error",
                {
                    "ok": False,
                    "error": str(exc),
                    "mode": "llm",
                    "cancelled": True,
                    "correlationId": cid,
                },
            )
            return
        except LlmError as exc:
            METRICS.inc("chat.error")
            METRICS.inc("llm.error")
            emit(
                "error",
                {
                    "ok": False,
                    "error": str(exc),
                    "mode": "llm",
                    "hint": "Use the tools rail for MCP without an LLM, or set OPENROUTER_API_KEY.",
                    "correlationId": cid,
                    "toolsOnly": True,
                },
            )
            return
        finally:
            _finish_run(run_id)

        if is_cancelled():
            METRICS.inc("chat.cancelled")
            emit(
                "error",
                {
                    "ok": False,
                    "error": "Stopped by operator",
                    "mode": "llm",
                    "cancelled": True,
                    "correlationId": cid,
                },
            )
            return

        steps = self._enrich_steps(list(outcome.get("steps") or []), search_fn)
        cards = build_cards(steps)
        ms = (time.perf_counter() - started) * 1000.0
        METRICS.observe("chat.latency_ms", ms)
        METRICS.inc("chat.ok")
        if outcome.get("fallbackUsed"):
            METRICS.inc("llm.fallback")
        log_event(
            "chat",
            correlation_id=cid,
            user_id=uid,
            run_id=run_id,
            latency_ms=ms,
            outcome="success",
            mode="stream",
            model=outcome.get("model"),
            tools=len(steps),
            fallbackUsed=bool(outcome.get("fallbackUsed")),
        )
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
                "cards": cards,
                "toolCount": len(tools),
                "runId": run_id,
                "correlationId": cid,
                "readOnly": flags["readOnly"],
                "fallbackUsed": bool(outcome.get("fallbackUsed")),
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
