#!/usr/bin/env python3
"""Thin Meridian connector mock for Lessons 68–69 (Wire Portal REST + SCIM 2.0).

  python3 tools/connector-mock/serve.py
  -> http://127.0.0.1:8091/health
  -> http://127.0.0.1:8091/users
  -> http://127.0.0.1:8091/scim/v2/Users
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[2]
WS_USERS = ROOT / "lab-data" / "connectors" / "webservices" / "sample-users.json"
SCIM_USERS = ROOT / "lab-data" / "connectors" / "scim" / "Users.json"

HOST = os.environ.get("MOCK_HOST", "0.0.0.0")
PORT = int(os.environ.get("MOCK_PORT", "8091"))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Handler(BaseHTTPRequestHandler):
    server_version = "MNBConnectorMock/1.0"

    def log_message(self, fmt: str, *args) -> None:
        print("%s - %s" % (self.address_string(), fmt % args))

    def _send(self, code: int, body: object, content_type: str = "application/json") -> None:
        if isinstance(body, (bytes, bytearray)):
            raw = body
        else:
            raw = json.dumps(body, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, PATCH, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path in ("/health", "/healthz"):
            return self._send(200, {"ok": True, "service": "mnb-connector-mock", "port": PORT})

        if path == "/users":
            data = load_json(WS_USERS)
            return self._send(200, data)

        if path.startswith("/users/"):
            uid = path.split("/")[-1]
            data = load_json(WS_USERS)
            for u in data.get("users", []):
                if u.get("id") == uid or u.get("username") == uid:
                    return self._send(200, u)
            return self._send(404, {"error": "not_found", "id": uid})

        if path in ("/scim/v2/Users", "/scim/v2/Users/"):
            data = load_json(SCIM_USERS)
            qs = parse_qs(parsed.query)
            # Minimal filter: userName eq "priya.wire"
            filt = (qs.get("filter") or [""])[0]
            resources = list(data.get("Resources") or [])
            if "userName eq" in filt:
                # crude parse
                name = filt.split('"')[1] if '"' in filt else ""
                resources = [r for r in resources if r.get("userName") == name]
                data = {
                    "schemas": data.get("schemas"),
                    "totalResults": len(resources),
                    "Resources": resources,
                }
            return self._send(200, data)

        if path.startswith("/scim/v2/Users/"):
            rid = path.rsplit("/", 1)[-1]
            data = load_json(SCIM_USERS)
            for r in data.get("Resources") or []:
                if r.get("id") == rid or r.get("userName") == rid:
                    return self._send(200, r)
            return self._send(
                404,
                {
                    "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
                    "detail": f"Resource {rid} not found",
                    "status": "404",
                },
            )

        if path == "/scim/v2/ServiceProviderConfig":
            return self._send(
                200,
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
                    "patch": {"supported": True},
                    "filter": {"supported": True, "maxResults": 100},
                    "bulk": {"supported": False},
                },
            )

        return self._send(404, {"error": "not_found", "path": path})

    def do_PATCH(self) -> None:
        """Minimal SCIM disable: PATCH /scim/v2/Users/{id} with active=false (lab echo)."""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return self._send(400, {"error": "invalid_json"})

        if not path.startswith("/scim/v2/Users/"):
            return self._send(404, {"error": "not_found", "path": path})

        rid = path.rsplit("/", 1)[-1]
        data = load_json(SCIM_USERS)
        user = next(
            (r for r in data.get("Resources") or [] if r.get("id") == rid or r.get("userName") == rid),
            None,
        )
        if not user:
            return self._send(404, {"error": "not_found", "id": rid})

        # Honor Operations-style or direct active
        active = user.get("active", True)
        for op in body.get("Operations") or []:
            if op.get("path") == "active" or (op.get("op") or "").lower() in {"replace", "add"}:
                val = op.get("value")
                if isinstance(val, dict) and "active" in val:
                    active = bool(val["active"])
                elif isinstance(val, bool):
                    active = val
        if "active" in body:
            active = bool(body["active"])

        updated = dict(user)
        updated["active"] = active
        return self._send(200, updated)


def main() -> None:
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"mnb-connector-mock listening on http://{HOST}:{PORT}")
    print("  GET  /health")
    print("  GET  /users                  (Lesson 68 Wire Portal)")
    print("  GET  /scim/v2/Users          (Lesson 69 SCIM)")
    print("  PATCH /scim/v2/Users/{{id}}  (disable echo)")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
