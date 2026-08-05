#!/usr/bin/env python3
"""Meridian connector mock — Wire Portal, SCIM, Workday-shaped HCM, CRM SCIM, ITSM.

  python3 tools/connector-mock/serve.py
  -> http://127.0.0.1:8091/health
  -> http://127.0.0.1:8091/users
  -> http://127.0.0.1:8091/scim/v2/Users
  -> http://127.0.0.1:8091/hcm/v1/workers
  -> http://127.0.0.1:8091/crm/scim/v2/Users
  -> http://127.0.0.1:8091/itsm/v1/catalog
"""

from __future__ import annotations

import json
import os
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[2]
WS_USERS = ROOT / "lab-data" / "connectors" / "webservices" / "sample-users.json"
SCIM_USERS = ROOT / "lab-data" / "connectors" / "scim" / "Users.json"
HCM_WORKERS = ROOT / "lab-data" / "connectors" / "hcm" / "workers.json"
CRM_USERS = ROOT / "lab-data" / "connectors" / "crm" / "Users.json"
ITSM_DATA = ROOT / "lab-data" / "connectors" / "itsm" / "tickets.json"

ENTRA_USERS = ROOT / "lab-data" / "connectors" / "entra" / "Users.json"

HOST = os.environ.get("MOCK_HOST", "0.0.0.0")
PORT = int(os.environ.get("MOCK_PORT", "8091"))

# Mutable lab state for joiner/leaver demos
_HCM_STATE: dict | None = None
_ITSM_TICKETS: list[dict] = []
_ENTRA_STATE: dict | None = None


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def entra_payload() -> dict:
    global _ENTRA_STATE
    if _ENTRA_STATE is None:
        _ENTRA_STATE = load_json(ENTRA_USERS) or {"Resources": [], "groups": [], "totalResults": 0}
    return _ENTRA_STATE


def hcm_payload() -> dict:
    global _HCM_STATE
    if _HCM_STATE is None:
        _HCM_STATE = load_json(HCM_WORKERS) or {"workers": [], "total": 0}
    return _HCM_STATE


class Handler(BaseHTTPRequestHandler):
    server_version = "MNBConnectorMock/2.0"

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

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return {}

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, PATCH, POST, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path in ("/health", "/healthz"):
            return self._send(
                200,
                {
                    "ok": True,
                    "service": "mnb-connector-mock",
                    "port": PORT,
                    "apis": ["wire", "scim", "hcm", "crm", "itsm", "entra"],
                },
            )

        # --- Wire Portal ---
        if path == "/users":
            return self._send(200, load_json(WS_USERS))

        if path.startswith("/users/"):
            uid = path.split("/")[-1]
            data = load_json(WS_USERS)
            for u in data.get("users", []):
                if u.get("id") == uid or u.get("username") == uid:
                    return self._send(200, u)
            return self._send(404, {"error": "not_found", "id": uid})

        # --- Wire SCIM ---
        if path in ("/scim/v2/Users", "/scim/v2/Users/"):
            data = load_json(SCIM_USERS)
            qs = parse_qs(parsed.query)
            filt = (qs.get("filter") or [""])[0]
            resources = list(data.get("Resources") or [])
            if "userName eq" in filt:
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

        # --- Workday-shaped HCM ---
        if path in ("/hcm/v1/workers", "/hcm/v1/workers/"):
            data = hcm_payload()
            qs = parse_qs(parsed.query)
            workers = list(data.get("workers") or [])
            if (qs.get("active") or [""])[0].lower() == "true":
                workers = [w for w in workers if w.get("active")]
            return self._send(200, {"total": len(workers), "workers": workers})

        if path.startswith("/hcm/v1/workers/"):
            wid = path.rsplit("/", 1)[-1]
            for w in hcm_payload().get("workers") or []:
                if w.get("id") == wid or w.get("workerId") == wid or w.get("userName") == wid:
                    return self._send(200, w)
            return self._send(404, {"error": "not_found", "id": wid})

        if path == "/hcm/v1/org":
            depts = sorted(
                {
                    w.get("department")
                    for w in (hcm_payload().get("workers") or [])
                    if w.get("department")
                }
            )
            return self._send(200, {"departments": [{"name": d} for d in depts]})

        # --- CRM SCIM ---
        if path in ("/crm/scim/v2/Users", "/crm/scim/v2/Users/"):
            data = load_json(CRM_USERS) or {"Resources": [], "totalResults": 0}
            return self._send(200, data)

        if path.startswith("/crm/scim/v2/Users/"):
            rid = path.rsplit("/", 1)[-1]
            data = load_json(CRM_USERS)
            for r in data.get("Resources") or []:
                if r.get("id") == rid or r.get("userName") == rid:
                    return self._send(200, r)
            return self._send(404, {"error": "not_found", "id": rid})

        # --- ITSM ---
        if path in ("/itsm/v1/catalog", "/itsm/v1/catalog/"):
            data = load_json(ITSM_DATA)
            return self._send(200, {"catalog": data.get("catalog") or []})

        if path in ("/itsm/v1/tickets", "/itsm/v1/tickets/"):
            data = load_json(ITSM_DATA)
            tickets = list(data.get("tickets") or []) + _ITSM_TICKETS
            return self._send(200, {"tickets": tickets})

        # --- Entra-shaped (Graph + SCIM) — not a real Entra tenant ---
        if path in ("/entra/v1/users", "/entra/v1/users/"):
            data = entra_payload()
            users = [
                {
                    "id": r.get("id"),
                    "userPrincipalName": f"{r.get('userName')}@meridiannb.com",
                    "mail": (r.get("emails") or [{}])[0].get("value"),
                    "displayName": r.get("displayName"),
                    "accountEnabled": r.get("active", True),
                    "employeeId": r.get("externalId"),
                }
                for r in (data.get("Resources") or [])
            ]
            return self._send(200, {"value": users, "@odata.count": len(users)})

        if path in ("/entra/v1/groups", "/entra/v1/groups/"):
            data = entra_payload()
            return self._send(200, {"value": data.get("groups") or []})

        if path in ("/entra/scim/v2/Users", "/entra/scim/v2/Users/"):
            data = entra_payload()
            qs = parse_qs(parsed.query)
            filt = (qs.get("filter") or [""])[0]
            resources = list(data.get("Resources") or [])
            if "userName eq" in filt and '"' in filt:
                name = filt.split('"')[1]
                resources = [r for r in resources if r.get("userName") == name]
            return self._send(
                200,
                {
                    "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
                    "totalResults": len(resources),
                    "Resources": resources,
                },
            )

        if path.startswith("/entra/scim/v2/Users/"):
            rid = path.rsplit("/", 1)[-1]
            for r in entra_payload().get("Resources") or []:
                if r.get("id") == rid or r.get("userName") == rid:
                    return self._send(200, r)
            return self._send(404, {"error": "not_found", "id": rid})

        if path in ("/entra/scim/v2/Groups", "/entra/scim/v2/Groups/"):
            groups = entra_payload().get("groups") or []
            resources = [
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                    "id": g.get("id"),
                    "displayName": g.get("displayName"),
                }
                for g in groups
            ]
            return self._send(
                200,
                {
                    "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
                    "totalResults": len(resources),
                    "Resources": resources,
                },
            )

        return self._send(404, {"error": "not_found", "path": path})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        body = self._read_json()

        # Joiner: create/update worker in HCM mock
        if path == "/hcm/v1/workers":
            data = hcm_payload()
            workers = list(data.get("workers") or [])
            wid = body.get("id") or body.get("workerId") or f"MNB{uuid.uuid4().hex[:5].upper()}"
            worker = {
                "id": wid,
                "workerId": wid,
                "userName": body.get("userName") or body.get("username"),
                "firstName": body.get("firstName"),
                "lastName": body.get("lastName"),
                "email": body.get("email"),
                "department": body.get("department"),
                "title": body.get("title"),
                "managerId": body.get("managerId"),
                "employeeType": body.get("employeeType") or "Employee",
                "active": body.get("active", True),
                "hireDate": body.get("hireDate"),
                "status": body.get("status") or "Active",
            }
            workers = [w for w in workers if w.get("id") != wid]
            workers.append(worker)
            data["workers"] = workers
            data["total"] = len(workers)
            return self._send(201, worker)

        if path == "/itsm/v1/tickets":
            ticket = {
                "id": f"INC{uuid.uuid4().hex[:6].upper()}",
                "shortDescription": body.get("shortDescription") or "Access request",
                "requestedFor": body.get("requestedFor"),
                "catalogId": body.get("catalogId"),
                "state": "open",
            }
            _ITSM_TICKETS.append(ticket)
            return self._send(201, ticket)

        return self._send(404, {"error": "not_found", "path": path})

    def do_PATCH(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        body = self._read_json()

        if path.startswith("/hcm/v1/workers/"):
            wid = path.rsplit("/", 1)[-1]
            data = hcm_payload()
            for w in data.get("workers") or []:
                if w.get("id") == wid or w.get("workerId") == wid or w.get("userName") == wid:
                    if "active" in body:
                        w["active"] = bool(body["active"])
                        w["status"] = "Active" if w["active"] else "Terminated"
                    for k in ("department", "title", "managerId", "status", "email"):
                        if k in body:
                            w[k] = body[k]
                    return self._send(200, w)
            return self._send(404, {"error": "not_found", "id": wid})

        if path.startswith("/entra/scim/v2/Users/"):
            rid = path.rsplit("/", 1)[-1]
            data = entra_payload()
            user = next(
                (r for r in data.get("Resources") or [] if r.get("id") == rid or r.get("userName") == rid),
                None,
            )
            if not user:
                return self._send(404, {"error": "not_found", "id": rid})
            active = user.get("active", True)
            for op in body.get("Operations") or []:
                val = op.get("value")
                if op.get("path") == "active" or (isinstance(val, dict) and "active" in val):
                    if isinstance(val, dict) and "active" in val:
                        active = bool(val["active"])
                    elif isinstance(val, bool):
                        active = val
                if op.get("path") == "groups" and isinstance(val, list):
                    user["groups"] = val
            if "active" in body:
                active = bool(body["active"])
            user["active"] = active
            return self._send(200, user)

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
    print("  GET  /users | /scim/v2/Users")
    print("  GET  /hcm/v1/workers | POST /hcm/v1/workers | PATCH /hcm/v1/workers/{id}")
    print("  GET  /crm/scim/v2/Users")
    print("  GET  /itsm/v1/catalog | POST /itsm/v1/tickets")
    print("  GET  /entra/v1/users | /entra/scim/v2/Users | PATCH /entra/scim/v2/Users/{id}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
