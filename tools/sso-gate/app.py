#!/usr/bin/env python3
"""Meridian SSO gate — OIDC login + required Keycloak group check.

Used for Workstation (:8094), HR Intranet (:8095), Finance Portal (:8096).

Env:
  PORTAL_PORT, PORTAL_PUBLIC_URL, OIDC_CLIENT_ID
  KEYCLOAK_INTERNAL_URL, KEYCLOAK_PUBLIC_URL, KEYCLOAK_REALM
  APP_TITLE, APP_KIND (workstation|hr|finance)
  REQUIRED_GROUPS  comma-separated group names (without leading /)
"""

from __future__ import annotations

import base64
import hashlib
import html as html_lib
import json
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

HOST = os.environ.get("PORTAL_HOST", "0.0.0.0")
PORT = int(os.environ.get("PORTAL_PORT", "8094"))
KEYCLOAK_INTERNAL = (
    os.environ.get("KEYCLOAK_INTERNAL_URL") or os.environ.get("KEYCLOAK_URL") or "http://keycloak:8080"
).rstrip("/")
KEYCLOAK_PUBLIC = os.environ.get("KEYCLOAK_PUBLIC_URL", "http://localhost:8085").rstrip("/")
REALM = os.environ.get("KEYCLOAK_REALM", "meridian")
CLIENT_ID = os.environ.get("OIDC_CLIENT_ID", "workstation-portal")
PORTAL_PUBLIC = os.environ.get("PORTAL_PUBLIC_URL", f"http://localhost:{PORT}").rstrip("/")
APP_TITLE = os.environ.get("APP_TITLE", "Meridian Workstation")
APP_KIND = os.environ.get("APP_KIND", "workstation")
REQUIRED_GROUPS = [
    g.strip().lstrip("/")
    for g in os.environ.get("REQUIRED_GROUPS", "mnb-workstation-users").split(",")
    if g.strip()
]

FAVICON_BY_KIND = {
    "workstation": "data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20viewBox%3D%220%200%2032%2032%22%3E%20%3Crect%20width%3D%2232%22%20height%3D%2232%22%20rx%3D%227%22%20fill%3D%22%235a6577%22/%3E%20%3Ctext%20x%3D%2216%22%20y%3D%2221.5%22%20text-anchor%3D%22middle%22%20font-family%3D%22ui-sans-serif%2Csystem-ui%2C-apple-system%2Csans-serif%22%20font-size%3D%2211%22%20font-weight%3D%22700%22%20fill%3D%22%23ffffff%22%3EWS%3C/text%3E%20%3C/svg%3E",
    "hr": "data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20viewBox%3D%220%200%2032%2032%22%3E%20%3Crect%20width%3D%2232%22%20height%3D%2232%22%20rx%3D%227%22%20fill%3D%22%236b3fa0%22/%3E%20%3Ctext%20x%3D%2216%22%20y%3D%2221.5%22%20text-anchor%3D%22middle%22%20font-family%3D%22ui-sans-serif%2Csystem-ui%2C-apple-system%2Csans-serif%22%20font-size%3D%2211%22%20font-weight%3D%22700%22%20fill%3D%22%23ffffff%22%3EHR%3C/text%3E%20%3C/svg%3E",
    "finance": "data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20viewBox%3D%220%200%2032%2032%22%3E%20%3Crect%20width%3D%2232%22%20height%3D%2232%22%20rx%3D%227%22%20fill%3D%22%230b3d6e%22/%3E%20%3Ctext%20x%3D%2216%22%20y%3D%2221.5%22%20text-anchor%3D%22middle%22%20font-family%3D%22ui-sans-serif%2Csystem-ui%2C-apple-system%2Csans-serif%22%20font-size%3D%2211%22%20font-weight%3D%22700%22%20fill%3D%22%23ffffff%22%3EFN%3C/text%3E%20%3C/svg%3E",
}
FAVICON_HREF = FAVICON_BY_KIND.get(APP_KIND, FAVICON_BY_KIND["workstation"])
FAVICON_LINK = f'<link rel="icon" href="{FAVICON_HREF}" type="image/svg+xml" />'

SESSIONS: dict[str, dict[str, Any]] = {}
PENDING: dict[str, str] = {}

SHELL_CSS = """
:root {
  --navy: #0b1f33; --brass: #c4a35a; --paper: #eef3f8; --ink: #12263a;
  --muted: #5b6b7c; --ok: #1f6b4a; --bad: #8a2f2f;
  --display: "Libre Baskerville", Georgia, serif;
  --sans: "DM Sans", "Segoe UI", sans-serif;
}
* { box-sizing: border-box; }
body {
  margin: 0; min-height: 100%; font-family: var(--sans); color: var(--ink);
  background: linear-gradient(145deg, var(--navy) 0%, #16324f 36%, var(--paper) 36.2%);
}
.shell { max-width: 720px; margin: 0 auto; padding: 1.5rem; }
.panel {
  background: #fff; border-radius: 12px; padding: 1.5rem;
  box-shadow: 0 18px 50px rgba(11,31,51,0.16);
}
h1 { font-family: var(--display); margin: 0 0 0.5rem; font-size: 1.75rem; }
.lede { color: var(--muted); line-height: 1.45; }
.btn {
  display: inline-block; margin-top: 1rem; background: var(--brass); color: var(--navy);
  text-decoration: none; padding: 0.65rem 1.1rem; border-radius: 6px; font-weight: 700;
}
.btn.ghost { background: transparent; border: 1px solid #ccd; color: var(--ink); }
.badge-ok { color: var(--ok); font-weight: 700; }
.badge-bad { color: var(--bad); font-weight: 700; }
code { background: #eef2f7; padding: 0.1rem 0.35rem; border-radius: 4px; }
.meta { margin-top: 1rem; font-size: 0.85rem; color: var(--muted); }
"""


def esc(value: Any) -> str:
    return html_lib.escape("" if value is None else str(value))


def _http_json(url: str, data: bytes | None = None, headers: dict | None = None) -> dict:
    req = urllib.request.Request(url, data=data, headers=headers or {}, method="POST" if data else "GET")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def discovery() -> dict:
    url = f"{KEYCLOAK_INTERNAL}/realms/{REALM}/.well-known/openid-configuration"
    with urllib.request.urlopen(url, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def browser_auth_url(authorization_endpoint: str) -> str:
    url = authorization_endpoint
    for internal in (KEYCLOAK_INTERNAL, "http://keycloak:8080", "http://host.docker.internal:8085"):
        if internal and internal in url:
            url = url.replace(internal, KEYCLOAK_PUBLIC)
    return url


def pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


def jwt_claims(token: str) -> dict[str, Any]:
    try:
        part = token.split(".")[1]
        part += "=" * (-len(part) % 4)
        return json.loads(base64.urlsafe_b64decode(part.encode("ascii")))
    except Exception:  # noqa: BLE001
        return {}


def groups_from_claims(claims: dict[str, Any]) -> list[str]:
    raw = claims.get("groups") or claims.get("group") or []
    if isinstance(raw, str):
        raw = [raw]
    out = []
    for g in raw:
        name = str(g).lstrip("/")
        out.append(name)
    return out


def authorized(claims: dict[str, Any]) -> tuple[bool, list[str]]:
    have = groups_from_claims(claims)
    if not REQUIRED_GROUPS:
        return True, have
    ok = all(g in have for g in REQUIRED_GROUPS)
    return ok, have


def html_page(title: str, body: str) -> bytes:
    doc = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{esc(title)} · {esc(APP_TITLE)}</title>
{FAVICON_LINK}
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&family=Libre+Baskerville:wght@700&display=swap" rel="stylesheet"/>
<style>{SHELL_CSS}</style>
</head><body><div class="shell"><div class="panel">{body}</div>
<p class="meta">Enterprise Lab SSO gate · IdP realm <code>{esc(REALM)}</code> · requires {esc(", ".join(REQUIRED_GROUPS) or "(none)")}</p>
</div></body></html>"""
    return doc.encode("utf-8")


def page_home(claims: dict[str, Any]) -> bytes:
    user = claims.get("preferred_username") or claims.get("email") or "user"
    ok, have = authorized(claims)
    if not ok:
        body = f"""
        <p class="badge-bad">Access denied</p>
        <h1>{esc(APP_TITLE)}</h1>
        <p class="lede">You authenticated to Meridian IdP as <code>{esc(user)}</code>, but you are missing required group(s):
        <code>{esc(", ".join(REQUIRED_GROUPS))}</code>.</p>
        <p class="lede">Your groups: <code>{esc(", ".join(have) or "(none)")}</code>.</p>
        <p class="lede">Grant the entitlement in IdentityIQ, provision the Keycloak group, then sign in again. After revoke, this deny page is the expected proof.</p>
        <a class="btn ghost" href="/logout">Sign out</a>
        """
        return html_page("Denied", body)

    kind_copy = {
        "workstation": "Workstation session established. This stands in for laptop login: if you can see this, IIQ granted workstation access.",
        "hr": "HR Self-Service unlocked. Group gate passed.",
        "finance": "Finance Portal unlocked. Group gate passed.",
    }.get(APP_KIND, "Access granted.")

    body = f"""
    <p class="badge-ok">Signed in</p>
    <h1>{esc(APP_TITLE)}</h1>
    <p class="lede">{esc(kind_copy)}</p>
    <p class="lede">User <code>{esc(user)}</code> · groups <code>{esc(", ".join(have))}</code></p>
    <a class="btn ghost" href="/logout">Sign out</a>
    """
    return html_page("Home", body)


def page_signed_out() -> bytes:
    body = f"""
    <h1>{esc(APP_TITLE)}</h1>
    <p class="lede">Sign in with Meridian IdP. Access is granted only when your account holds:
    <code>{esc(", ".join(REQUIRED_GROUPS))}</code>.</p>
    <a class="btn" href="/login">Sign in with Meridian IdP</a>
    <p class="meta">Lab users: <code>helen.ross</code> / <code>LabUser1!</code> (seeded with workstation + intranet groups).</p>
    """
    return html_page("Sign in", body)


class Handler(BaseHTTPRequestHandler):
    server_version = "MNBSsoGate/1.0"

    def log_message(self, fmt: str, *args) -> None:
        print("%s - %s" % (self.address_string(), fmt % args))

    def _send(self, code: int, body: bytes, content_type: str = "text/html; charset=utf-8") -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _redirect(self, loc: str) -> None:
        self.send_response(302)
        self.send_header("Location", loc)
        self.end_headers()

    def _session(self) -> dict | None:
        cookie = self.headers.get("Cookie") or ""
        for part in cookie.split(";"):
            part = part.strip()
            if part.startswith("mnb_session="):
                return SESSIONS.get(part.split("=", 1)[1])
        return None

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        qs = urllib.parse.parse_qs(parsed.query)

        if path == "/health":
            return self._send(
                200,
                json.dumps(
                    {
                        "ok": True,
                        "service": f"sso-gate-{APP_KIND}",
                        "requiredGroups": REQUIRED_GROUPS,
                        "clientId": CLIENT_ID,
                    }
                ).encode(),
                "application/json",
            )

        if path == "/login":
            try:
                conf = discovery()
            except Exception as e:  # noqa: BLE001
                return self._send(503, html_page("IdP unavailable", f"<p><code>{esc(e)}</code></p>"))
            state = secrets.token_urlsafe(16)
            verifier, challenge = pkce_pair()
            PENDING[state] = verifier
            params = {
                "client_id": CLIENT_ID,
                "response_type": "code",
                "scope": "openid profile email",
                "redirect_uri": f"{PORTAL_PUBLIC}/callback",
                "state": state,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            }
            url = browser_auth_url(conf["authorization_endpoint"]) + "?" + urllib.parse.urlencode(params)
            return self._redirect(url)

        if path == "/callback":
            err = (qs.get("error") or [""])[0]
            if err:
                detail = (qs.get("error_description") or [err])[0]
                return self._send(400, html_page("Login failed", f"<p><code>{esc(detail)}</code></p>"))
            code = (qs.get("code") or [""])[0]
            state = (qs.get("state") or [""])[0]
            if not code or state not in PENDING:
                return self._send(400, html_page("Login failed", "<p>Missing OIDC state/code.</p>"))
            verifier = PENDING.pop(state)
            try:
                conf = discovery()
                token_endpoint = conf["token_endpoint"]
                if KEYCLOAK_PUBLIC in token_endpoint:
                    token_endpoint = token_endpoint.replace(KEYCLOAK_PUBLIC, KEYCLOAK_INTERNAL)
                tokens = _http_json(
                    token_endpoint,
                    data=urllib.parse.urlencode(
                        {
                            "grant_type": "authorization_code",
                            "code": code,
                            "redirect_uri": f"{PORTAL_PUBLIC}/callback",
                            "client_id": CLIENT_ID,
                            "code_verifier": verifier,
                        }
                    ).encode(),
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                userinfo = jwt_claims(tokens.get("id_token") or "")
                if not userinfo.get("preferred_username"):
                    userinfo = jwt_claims(tokens.get("access_token") or "")
            except Exception as e:  # noqa: BLE001
                return self._send(502, html_page("Token exchange failed", f"<p><code>{esc(e)}</code></p>"))
            sid = secrets.token_urlsafe(24)
            SESSIONS[sid] = userinfo
            self.send_response(302)
            self.send_header("Location", "/")
            self.send_header("Set-Cookie", f"mnb_session={sid}; Path=/; HttpOnly; SameSite=Lax")
            self.end_headers()
            return

        if path == "/logout":
            self.send_response(302)
            self.send_header("Location", "/")
            self.send_header("Set-Cookie", "mnb_session=; Path=/; Max-Age=0")
            self.end_headers()
            return

        if path == "/":
            sess = self._session()
            if not sess:
                return self._send(200, page_signed_out())
            return self._send(200, page_home(sess))

        return self._send(404, html_page("Not found", f"<p>No route <code>{esc(path)}</code></p>"))


def main() -> None:
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(
        f"sso-gate kind={APP_KIND} on http://{HOST}:{PORT} "
        f"client={CLIENT_ID} required={REQUIRED_GROUPS} idp={KEYCLOAK_INTERNAL}"
    )
    httpd.serve_forever()


if __name__ == "__main__":
    main()
