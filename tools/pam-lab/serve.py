#!/usr/bin/env python3
"""Meridian PAM lab facade — CyberArk-shaped safes over HashiCorp Vault.

  GET  /health
  GET  /safes
  GET  /safes/{safe}/accounts
  POST /checkout   { "safe", "account", "requestedBy", "incidentId", "ttlMinutes" }
  POST /checkin    { "checkoutId" }
  GET  /sessions
  GET  /scim/v2/Users   (safe memberships as entitlements for IIQ aggregation)

Secrets live in Vault KV; this service enforces checkout controls + audit log.
Never prints secret values to stdout.
"""

from __future__ import annotations

import json
import os
import secrets
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib import error, request
from urllib.parse import parse_qs, urlparse

HOST = os.environ.get("PAM_HOST", "0.0.0.0")
PORT = int(os.environ.get("PAM_PORT", "8097"))
VAULT_ADDR = os.environ.get("VAULT_ADDR", "http://vault:8200").rstrip("/")
VAULT_TOKEN = os.environ.get("VAULT_TOKEN", "mnb-lab-vault-root")
SEED_FILE = Path(os.environ.get("PAM_SEED", "/opt/mnb/pam-seed.json"))

# In-memory checkout + session audit (lab). Secrets stay in Vault.
_CHECKOUTS: dict[str, dict[str, Any]] = {}
_SESSIONS: list[dict[str, Any]] = []
_MEMBERSHIPS: dict[str, set[str]] = {}  # username -> set of safe names


def vault_req(method: str, path: str, body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body).encode()
    req = request.Request(
        f"{VAULT_ADDR}{path}",
        data=data,
        method=method,
        headers={
            "X-Vault-Token": VAULT_TOKEN,
            "Content-Type": "application/json",
        },
    )
    try:
        with request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:400]
        raise RuntimeError(f"Vault {method} {path} → HTTP {e.code}: {detail}") from e


def load_seed() -> dict:
    if SEED_FILE.is_file():
        return json.loads(SEED_FILE.read_text(encoding="utf-8"))
    return {"safes": []}


def ensure_seed() -> None:
    """Write KV secrets and membership stubs if missing."""
    seed = load_seed()
    for safe in seed.get("safes") or []:
        name = safe["name"]
        for acct in safe.get("accounts") or []:
            path = f"/v1/secret/data/mnb/safes/{name}/{acct['name']}"
            try:
                vault_req("GET", path)
            except RuntimeError:
                vault_req(
                    "POST",
                    path,
                    {
                        "data": {
                            "username": acct.get("username") or acct["name"],
                            "password": acct.get("password") or secrets.token_urlsafe(18),
                            "platform": acct.get("platform") or "UnixSSH",
                            "address": acct.get("address") or "lab-only",
                            "safe": name,
                            "rotationHours": acct.get("rotationHours") or 24,
                            "notes": acct.get("notes") or "",
                        }
                    },
                )
        for member in safe.get("members") or []:
            _MEMBERSHIPS.setdefault(member, set()).add(name)


def list_safes() -> list[dict]:
    seed = load_seed()
    out = []
    for safe in seed.get("safes") or []:
        out.append(
            {
                "name": safe["name"],
                "description": safe.get("description"),
                "dualControl": safe.get("dualControl", True),
                "sessionRecording": safe.get("sessionRecording", True),
                "accountCount": len(safe.get("accounts") or []),
                "members": [
                    u for u, safes in _MEMBERSHIPS.items() if safe["name"] in safes
                ],
            }
        )
    return out


def get_secret(safe: str, account: str) -> dict:
    path = f"/v1/secret/data/mnb/safes/{safe}/{account}"
    data = vault_req("GET", path)
    return (data.get("data") or {}).get("data") or {}


class Handler(BaseHTTPRequestHandler):
    server_version = "MnbPamLab/1.0"

    def log_message(self, fmt: str, *args) -> None:
        print("%s - %s" % (self.address_string(), fmt % args))

    def _send(self, code: int, body: object) -> None:
        raw = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(raw)

    def _read(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode())

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self) -> None:
        path = urlparse(self.path).path.rstrip("/") or "/"

        if path in ("/health", "/healthz"):
            vault_ok = False
            try:
                vault_req("GET", "/v1/sys/health")
                vault_ok = True
            except Exception:  # noqa: BLE001
                try:
                    # Dev vault health may 429/501 — probe KV
                    vault_req("LIST", "/v1/secret/metadata/mnb/safes")
                    vault_ok = True
                except Exception:  # noqa: BLE001
                    vault_ok = False
            return self._send(
                200,
                {
                    "ok": True,
                    "service": "mnb-pam-lab",
                    "vaultAddr": VAULT_ADDR,
                    "vaultReachable": vault_ok,
                    "safes": [s["name"] for s in list_safes()],
                },
            )

        if path == "/safes":
            return self._send(200, {"safes": list_safes()})

        if path.startswith("/safes/") and path.endswith("/accounts"):
            safe = path.split("/")[2]
            seed = load_seed()
            match = next((s for s in seed.get("safes") or [] if s["name"] == safe), None)
            if not match:
                return self._send(404, {"error": "safe_not_found", "safe": safe})
            accounts = [
                {
                    "name": a["name"],
                    "username": a.get("username") or a["name"],
                    "platform": a.get("platform"),
                    "address": a.get("address"),
                    "checkedOut": any(
                        c["safe"] == safe and c["account"] == a["name"] and c["status"] == "active"
                        for c in _CHECKOUTS.values()
                    ),
                }
                for a in (match.get("accounts") or [])
            ]
            return self._send(200, {"safe": safe, "accounts": accounts})

        if path == "/sessions":
            return self._send(200, {"sessions": list(reversed(_SESSIONS[-100:]))})

        if path == "/checkouts":
            return self._send(200, {"checkouts": list(_CHECKOUTS.values())})

        # SCIM-ish membership view for IIQ aggregation
        if path in ("/scim/v2/Users", "/scim/v2/Users/"):
            resources = []
            for user, safes in sorted(_MEMBERSHIPS.items()):
                resources.append(
                    {
                        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                        "id": f"pam-{user}",
                        "userName": user,
                        "active": True,
                        "entitlements": [{"value": f"SAFE:{s}", "display": s} for s in sorted(safes)],
                    }
                )
            return self._send(
                200,
                {
                    "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
                    "totalResults": len(resources),
                    "Resources": resources,
                },
            )

        if path.startswith("/ui") or path == "/":
            html = UI_HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
            return

        return self._send(404, {"error": "not_found", "path": path})

    def do_POST(self) -> None:
        path = urlparse(self.path).path.rstrip("/") or "/"
        body = self._read()

        if path == "/memberships":
            user = body.get("user") or body.get("username")
            safe = body.get("safe")
            op = (body.get("op") or "add").lower()
            if not user or not safe:
                return self._send(400, {"error": "user_and_safe_required"})
            if op == "remove":
                _MEMBERSHIPS.get(user, set()).discard(safe)
            else:
                _MEMBERSHIPS.setdefault(user, set()).add(safe)
            _SESSIONS.append(
                {
                    "id": str(uuid.uuid4()),
                    "type": "membership",
                    "op": op,
                    "user": user,
                    "safe": safe,
                    "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
            )
            return self._send(200, {"user": user, "safes": sorted(_MEMBERSHIPS.get(user, set()))})

        if path == "/checkout":
            safe = body.get("safe")
            account = body.get("account")
            who = body.get("requestedBy") or body.get("user") or "unknown"
            incident = body.get("incidentId") or body.get("ticket") or ""
            ttl = int(body.get("ttlMinutes") or 60)
            if not safe or not account:
                return self._send(400, {"error": "safe_and_account_required"})
            if who not in _MEMBERSHIPS or safe not in _MEMBERSHIPS[who]:
                return self._send(
                    403,
                    {
                        "error": "not_a_safe_member",
                        "hint": "IIQ BreakGlass / privileged role must add safe membership first",
                        "user": who,
                        "safe": safe,
                    },
                )
            # One active checkout per account
            for c in _CHECKOUTS.values():
                if c["safe"] == safe and c["account"] == account and c["status"] == "active":
                    if c["requestedBy"] != who:
                        return self._send(409, {"error": "already_checked_out", "by": c["requestedBy"]})
            try:
                secret = get_secret(safe, account)
            except RuntimeError as e:
                return self._send(502, {"error": "vault_read_failed", "detail": str(e)})
            cid = str(uuid.uuid4())
            exp = int(time.time()) + ttl * 60
            rec = {
                "checkoutId": cid,
                "safe": safe,
                "account": account,
                "requestedBy": who,
                "incidentId": incident,
                "status": "active",
                "expiresAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(exp)),
                "expiresEpoch": exp,
                # Returned once to the requester — not logged
                "username": secret.get("username"),
                "password": secret.get("password"),
                "sessionRecording": True,
            }
            _CHECKOUTS[cid] = {k: v for k, v in rec.items() if k != "password"}
            _CHECKOUTS[cid]["passwordRedacted"] = True
            _SESSIONS.append(
                {
                    "id": str(uuid.uuid4()),
                    "type": "checkout",
                    "checkoutId": cid,
                    "safe": safe,
                    "account": account,
                    "requestedBy": who,
                    "incidentId": incident,
                    "ttlMinutes": ttl,
                    "recording": "started",
                    "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
            )
            return self._send(201, rec)

        if path == "/checkin":
            cid = body.get("checkoutId")
            if not cid or cid not in _CHECKOUTS:
                return self._send(404, {"error": "checkout_not_found"})
            _CHECKOUTS[cid]["status"] = "checked_in"
            _SESSIONS.append(
                {
                    "id": str(uuid.uuid4()),
                    "type": "checkin",
                    "checkoutId": cid,
                    "safe": _CHECKOUTS[cid]["safe"],
                    "account": _CHECKOUTS[cid]["account"],
                    "requestedBy": _CHECKOUTS[cid]["requestedBy"],
                    "recording": "closed",
                    "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
            )
            return self._send(200, {"checkoutId": cid, "status": "checked_in"})

        return self._send(404, {"error": "not_found", "path": path})


UI_HTML = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"/><title>Meridian PAM Lab</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20viewBox%3D%220%200%2032%2032%22%3E%20%3Crect%20width%3D%2232%22%20height%3D%2232%22%20rx%3D%227%22%20fill%3D%22%238b1e1e%22/%3E%20%3Ctext%20x%3D%2216%22%20y%3D%2221.5%22%20text-anchor%3D%22middle%22%20font-family%3D%22ui-sans-serif%2Csystem-ui%2C-apple-system%2Csans-serif%22%20font-size%3D%229%22%20font-weight%3D%22700%22%20fill%3D%22%23ffffff%22%3EPAM%3C/text%3E%20%3C/svg%3E" type="image/svg+xml" />
<style>
body{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem;color:#12263a}
code,pre{background:#eef2f7;padding:.2rem .4rem;border-radius:4px}
.card{border:1px solid #ccd;border-radius:8px;padding:1rem;margin:1rem 0}
h1{font-size:1.5rem}
</style></head><body>
<h1>Meridian PAM Lab</h1>
<p>CyberArk-shaped facade over HashiCorp Vault. Secrets stay in Vault; this UI is for operators.</p>
<div class="card">
<strong>API</strong>
<ul>
<li><code>GET /safes</code></li>
<li><code>POST /memberships</code> — add user to safe (IIQ BreakGlass result)</li>
<li><code>POST /checkout</code> — time-bound password retrieval + session recording stub</li>
<li><code>POST /checkin</code></li>
<li><code>GET /sessions</code> — audit trail</li>
<li><code>GET /scim/v2/Users</code> — safe memberships for IIQ</li>
</ul>
</div>
<p>Vault UI: <a href="http://localhost:8200/ui">http://localhost:8200/ui</a> (token in lab docs — never commit production tokens).</p>
</body></html>
"""


def main() -> None:
    # Wait for Vault
    for _ in range(40):
        try:
            vault_req("GET", "/v1/sys/health")
            break
        except Exception:  # noqa: BLE001
            try:
                vault_req("GET", "/v1/sys/seal-status")
                break
            except Exception:  # noqa: BLE001
                time.sleep(1)
    # Enable KV if needed (dev may already have secret/)
    try:
        vault_req("POST", "/v1/sys/mounts/secret", {"type": "kv", "options": {"version": "2"}})
    except Exception:  # noqa: BLE001
        pass
    try:
        ensure_seed()
    except Exception as e:  # noqa: BLE001
        print(f"WARN seed: {e}")
    # Default memberships from seed
    for safe in load_seed().get("safes") or []:
        for member in safe.get("members") or []:
            _MEMBERSHIPS.setdefault(member, set()).add(safe["name"])
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"mnb-pam-lab on http://{HOST}:{PORT} vault={VAULT_ADDR}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
