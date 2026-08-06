#!/usr/bin/env python3
"""Meridian Employee Portal — OIDC login proof for Enterprise Lab v2.

  KEYCLOAK_URL=http://localhost:8085
  PORTAL_URL=http://localhost:8092
  python3 tools/employee-portal/app.py
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
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

HOST = os.environ.get("PORTAL_HOST", "0.0.0.0")
PORT = int(os.environ.get("PORTAL_PORT", "8092"))
# Container→Keycloak (compose DNS). Browser must use KEYCLOAK_PUBLIC_URL instead.
KEYCLOAK_INTERNAL = (
    os.environ.get("KEYCLOAK_INTERNAL_URL") or os.environ.get("KEYCLOAK_URL") or "http://keycloak:8080"
).rstrip("/")
KEYCLOAK_PUBLIC = os.environ.get("KEYCLOAK_PUBLIC_URL", "http://localhost:8085").rstrip("/")
REALM = os.environ.get("KEYCLOAK_REALM", "meridian")
CLIENT_ID = os.environ.get("OIDC_CLIENT_ID", "employee-portal")
PORTAL_PUBLIC = os.environ.get("PORTAL_PUBLIC_URL", f"http://localhost:{PORT}").rstrip("/")

IIQ_URL = os.environ.get("IIQ_PUBLIC_URL", "http://localhost:8080/identityiq")
WIRE_URL = os.environ.get("WIRE_PUBLIC_URL", "http://localhost:8091/users")
ACADEMY_URL = os.environ.get("ACADEMY_PUBLIC_URL", "http://localhost:4173/")
TELLER_URL = os.environ.get("TELLER_PUBLIC_URL", "http://localhost:4180/")
GITEA_URL = os.environ.get("GITEA_PUBLIC_URL", "http://localhost:8093/")
MAILPIT_URL = os.environ.get("MAILPIT_PUBLIC_URL", "http://localhost:8025/")
WORKSTATION_URL = os.environ.get("WORKSTATION_PUBLIC_URL", "http://localhost:8094/")
HR_INTRANET_URL = os.environ.get("HR_INTRANET_PUBLIC_URL", "http://localhost:8095/")
FINANCE_URL = os.environ.get("FINANCE_PUBLIC_URL", "http://localhost:8096/")

# In-memory session store (lab only)
SESSIONS: dict[str, dict[str, Any]] = {}
# state -> code_verifier (PKCE)
PENDING: dict[str, str] = {}

# Lightweight directory for lab realism (username → org context)
PERSONAS: dict[str, dict[str, str]] = {
    "helen.ross": {
        "title": "Head of Identity & Access",
        "department": "Identity & Access",
        "location": "New York HQ",
        "employee_id": "MNB00001",
        "manager": "—",
    },
    "priya.wire": {
        "title": "Payments Analyst",
        "department": "Treasury & Payments",
        "location": "Bengaluru GCC",
        "employee_id": "MNB00090",
        "manager": "Rachel Evans",
    },
    "marcus.approve": {
        "title": "Wire Approver",
        "department": "Treasury & Payments",
        "location": "Charlotte Ops",
        "employee_id": "MNB00091",
        "manager": "Rachel Evans",
    },
}


def _http_json(url: str, data: bytes | None = None, headers: dict | None = None) -> dict:
    req = urllib.request.Request(url, data=data, headers=headers or {}, method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code} from {url}: {body[:500]}") from e


def discovery() -> dict:
    """OIDC discovery via server-side Keycloak URL (host.docker.internal in Docker)."""
    url = f"{KEYCLOAK_INTERNAL}/realms/{REALM}/.well-known/openid-configuration"
    with urllib.request.urlopen(url, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def browser_auth_url(authorization_endpoint: str) -> str:
    """Rewrite IdP host so the user's browser hits localhost, not Docker DNS."""
    url = authorization_endpoint
    for internal in (
        KEYCLOAK_INTERNAL,
        "http://keycloak:8080",
        "http://host.docker.internal:8085",
        "http://127.0.0.1:8085",
    ):
        if internal and internal in url:
            url = url.replace(internal, KEYCLOAK_PUBLIC)
    return url


def pkce_pair() -> tuple[str, str]:
    """Return (code_verifier, code_challenge) for S256 PKCE."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


def jwt_claims(token: str) -> dict[str, Any]:
    """Decode JWT payload without verification (lab UI only)."""
    try:
        part = token.split(".")[1]
        part += "=" * (-len(part) % 4)
        return json.loads(base64.urlsafe_b64decode(part.encode("ascii")))
    except Exception:  # noqa: BLE001
        return {}


def esc(value: Any) -> str:
    return html_lib.escape("" if value is None else str(value))


def persona_for(username: str) -> dict[str, str]:
    return PERSONAS.get(
        username,
        {
            "title": "Meridian Associate",
            "department": "Workforce",
            "location": "Meridian National Bank",
            "employee_id": "—",
            "manager": "—",
        },
    )


def entitlements_for(username: str) -> list[tuple[str, str, str]]:
    """Return (name, status, note) entitlement rows."""
    base = [
        ("Employee Portal", "Active", "OIDC via Meridian IdP"),
        ("Corporate Directory", "Active", "OpenLDAP / Samba login eligible"),
        ("IdentityIQ self-service", "Active", "Access requests & work items"),
    ]
    if username == "helen.ross":
        base += [
            ("IIQ Admin capabilities", "Active", "IAM leadership desk"),
            ("Policy & SoD console", "Active", "Wire dual-control oversight"),
        ]
    if "wire" in username or username == "priya.wire":
        base.append(("Wire Portal — Initiate", "Active", "High-risk entitlement"))
    if "approve" in username or username == "marcus.approve":
        base.append(("Wire Portal — Approve", "Active", "Dual-control approver"))
    return base


SHELL_CSS = """
:root {
  --navy: #0b1f33;
  --navy-2: #16324f;
  --brass: #c4a35a;
  --brass-deep: #9a7a3a;
  --paper: #eef3f8;
  --ink: #12263a;
  --muted: #5b6b7c;
  --line: rgba(11, 31, 51, 0.12);
  --ok: #1f6b4a;
  --warn: #8a5a12;
  --shadow: 0 18px 50px rgba(11, 31, 51, 0.16);
  --display: "Libre Baskerville", Georgia, serif;
  --sans: "DM Sans", "Segoe UI", sans-serif;
}
* { box-sizing: border-box; }
html, body { margin: 0; min-height: 100%; }
body {
  font-family: var(--sans);
  color: var(--ink);
  background:
    radial-gradient(1200px 600px at 10% -10%, rgba(196,163,90,0.18), transparent 55%),
    linear-gradient(145deg, var(--navy) 0%, var(--navy-2) 38%, var(--paper) 38.2%);
  background-attachment: fixed;
}
a { color: inherit; }
@keyframes rise {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; transition: none !important; }
}
.shell { max-width: 1100px; margin: 0 auto; padding: 1.25rem 1.25rem 2.5rem; }
.topbar {
  display: flex; align-items: center; justify-content: space-between; gap: 1rem;
  color: #f4efe4; padding: 0.5rem 0 1.5rem;
  animation: rise 0.5s ease both;
}
.brand-mark { display: flex; align-items: center; gap: 0.85rem; }
.crest {
  width: 42px; height: 42px; border: 1.5px solid var(--brass);
  display: grid; place-items: center; font-family: var(--display);
  font-size: 0.85rem; color: var(--brass); letter-spacing: 0.08em;
}
.brand-text strong {
  display: block; font-family: var(--display); font-weight: 700;
  font-size: 1.15rem; letter-spacing: 0.02em;
}
.brand-text span { font-size: 0.78rem; opacity: 0.78; }
.userchip {
  display: flex; align-items: center; gap: 0.7rem;
  background: rgba(255,255,255,0.08); border: 1px solid rgba(196,163,90,0.35);
  padding: 0.35rem 0.55rem 0.35rem 0.4rem; border-radius: 999px;
}
.avatar {
  width: 34px; height: 34px; border-radius: 50%;
  background: linear-gradient(145deg, var(--brass), var(--brass-deep));
  color: var(--navy); font-weight: 700; display: grid; place-items: center;
  font-size: 0.85rem;
}
.userchip .who { line-height: 1.15; font-size: 0.82rem; }
.userchip .who em { display: block; font-style: normal; opacity: 0.7; font-size: 0.72rem; }
.panel {
  background: rgba(255,255,255,0.96);
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
  border-radius: 14px;
  overflow: hidden;
  animation: rise 0.65s ease both;
}
.hero {
  padding: 1.6rem 1.6rem 1.25rem;
  border-bottom: 1px solid var(--line);
  background:
    linear-gradient(90deg, rgba(196,163,90,0.12), transparent 42%),
    #fff;
}
.eyebrow {
  font-size: 0.72rem; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--brass-deep); font-weight: 700; margin: 0 0 0.45rem;
}
.hero h1 {
  font-family: var(--display); font-size: clamp(1.6rem, 3vw, 2.15rem);
  margin: 0 0 0.35rem; font-weight: 700; letter-spacing: -0.01em;
}
.hero .lede { margin: 0; color: var(--muted); max-width: 40rem; line-height: 1.45; }
.grid {
  display: grid; grid-template-columns: 1.3fr 1fr; gap: 0;
}
@media (max-width: 860px) {
  .grid { grid-template-columns: 1fr; }
  .topbar { flex-direction: column; align-items: flex-start; }
}
.section { padding: 1.25rem 1.5rem 1.5rem; }
.section + .section { border-left: 1px solid var(--line); }
@media (max-width: 860px) {
  .section + .section { border-left: 0; border-top: 1px solid var(--line); }
}
.section h2 {
  margin: 0 0 0.9rem; font-size: 0.78rem; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--muted); font-weight: 700;
}
.apps { display: grid; gap: 0.65rem; }
.app {
  display: flex; align-items: center; justify-content: space-between; gap: 0.75rem;
  text-decoration: none; padding: 0.85rem 0.95rem;
  border: 1px solid var(--line); border-radius: 10px;
  transition: border-color 0.15s ease, transform 0.15s ease, background 0.15s ease;
}
.app:hover { border-color: var(--brass); background: #fbf8f1; transform: translateY(-1px); }
.app strong { display: block; font-size: 0.95rem; }
.app span { display: block; color: var(--muted); font-size: 0.8rem; margin-top: 0.15rem; }
.app .go { color: var(--brass-deep); font-weight: 700; font-size: 0.85rem; white-space: nowrap; }
.facts { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 1rem; }
.fact {
  border: 1px solid var(--line); border-radius: 10px; padding: 0.75rem 0.85rem;
  background: #f8fafc;
}
.fact label { display: block; font-size: 0.68rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); margin-bottom: 0.2rem; }
.fact b { font-size: 0.92rem; font-weight: 600; }
.table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
.table th, .table td { text-align: left; padding: 0.55rem 0.35rem; border-bottom: 1px solid var(--line); vertical-align: top; }
.table th { color: var(--muted); font-size: 0.68rem; letter-spacing: 0.08em; text-transform: uppercase; font-weight: 700; }
.badge {
  display: inline-block; padding: 0.15rem 0.45rem; border-radius: 999px;
  font-size: 0.72rem; font-weight: 700; background: #e5f3ec; color: var(--ok);
}
.notice {
  border-left: 3px solid var(--brass); padding: 0.65rem 0.85rem;
  background: #fbf8f1; border-radius: 0 8px 8px 0; margin-bottom: 0.65rem;
  font-size: 0.88rem; line-height: 1.4;
}
.notice strong { display: block; margin-bottom: 0.15rem; }
.proof {
  display: flex; flex-wrap: wrap; gap: 0.5rem 1rem; align-items: center;
  margin-top: 1rem; padding-top: 0.9rem; border-top: 1px dashed var(--line);
  font-size: 0.8rem; color: var(--muted);
}
.proof code { background: #eef2f7; padding: 0.1rem 0.35rem; border-radius: 4px; color: var(--ink); }
.actions { display: flex; flex-wrap: wrap; gap: 0.6rem; margin-top: 1rem; }
.btn {
  display: inline-flex; align-items: center; justify-content: center;
  background: var(--brass); color: var(--navy); text-decoration: none;
  padding: 0.65rem 1.05rem; border-radius: 6px; font-weight: 700; border: 0;
  transition: background 0.15s ease;
}
.btn:hover { background: #d4b56a; }
.btn.ghost {
  background: transparent; border: 1px solid var(--line); color: var(--ink); font-weight: 600;
}
.signin-wrap { max-width: 460px; }
.signin-wrap p { color: var(--muted); line-height: 1.5; }
.footer-note {
  margin-top: 1rem; color: rgba(244,239,228,0.72); font-size: 0.78rem;
  animation: rise 0.8s ease both;
}
"""


def html_shell(title: str, body: str, *, signed_in: bool = False, username: str = "") -> bytes:
    chip = ""
    if signed_in and username:
        initials = "".join(p[0].upper() for p in username.split(".")[:2]) or "M"
        given = username.split(".")[0].title()
        chip = f"""
        <div class="userchip">
          <div class="avatar">{esc(initials)}</div>
          <div class="who"><strong>{esc(given)}</strong><em>{esc(username)}</em></div>
        </div>"""
    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{esc(title)} · Meridian Employee Portal</title>
  <link rel="icon" href="data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20viewBox%3D%220%200%2032%2032%22%3E%20%3Crect%20width%3D%2232%22%20height%3D%2232%22%20rx%3D%227%22%20fill%3D%22%230b5cab%22/%3E%20%3Ctext%20x%3D%2216%22%20y%3D%2221.5%22%20text-anchor%3D%22middle%22%20font-family%3D%22ui-sans-serif%2Csystem-ui%2C-apple-system%2Csans-serif%22%20font-size%3D%2211%22%20font-weight%3D%22700%22%20fill%3D%22%23ffffff%22%3EEP%3C/text%3E%20%3C/svg%3E" type="image/svg+xml" />
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,600;0,9..40,700;1,9..40,400&family=Libre+Baskerville:wght@400;700&display=swap" rel="stylesheet"/>
  <style>{SHELL_CSS}</style>
</head>
<body>
  <div class="shell">
    <header class="topbar">
      <div class="brand-mark">
        <div class="crest">MNB</div>
        <div class="brand-text">
          <strong>Meridian National Bank</strong>
          <span>Employee Portal · Workforce SSO</span>
        </div>
      </div>
      {chip}
    </header>
    {body}
    <p class="footer-note">Enterprise Lab · OIDC via Keycloak realm <code style="color:#c4a35a">meridian</code> · Not a production bank system</p>
  </div>
</body>
</html>"""
    return doc.encode("utf-8")


def page_signed_out() -> bytes:
    body = f"""
    <div class="panel signin-wrap">
      <div class="hero">
        <p class="eyebrow">Workforce access</p>
        <h1>Sign in to your Meridian desk</h1>
        <p class="lede">Verify joiner/mover provisioning by logging in with your corporate IdP account after IIQ completes lifecycle.</p>
        <div class="actions">
          <a class="btn" href="/login">Sign in with Meridian IdP</a>
        </div>
        <div class="proof">Lab users: <code>helen.ross</code> / <code>LabUser1!</code></div>
      </div>
    </div>"""
    return html_shell("Sign in", body)


def page_home(sess: dict[str, Any]) -> bytes:
    preferred = sess.get("preferred_username") or sess.get("email") or "user"
    given = sess.get("given_name") or preferred.split(".")[0].title()
    email = sess.get("email") or "—"
    sub = sess.get("sub") or "—"
    persona = persona_for(str(preferred))
    ents = entitlements_for(str(preferred))
    now = datetime.now(timezone.utc).strftime("%d %b %Y · %H:%M UTC")
    rows = "".join(
        f"<tr><td>{esc(n)}</td><td><span class='badge'>{esc(s)}</span></td><td>{esc(note)}</td></tr>"
        for n, s, note in ents
    )
    body = f"""
    <div class="panel">
      <div class="hero">
        <p class="eyebrow">My workstation</p>
        <h1>Welcome back, {esc(given)}</h1>
        <p class="lede">{esc(persona['title'])} · {esc(persona['department'])} · {esc(persona['location'])}</p>
        <div class="proof">
          <span>Session verified by Meridian IdP</span>
          <span>Signed in as <code>{esc(preferred)}</code></span>
          <span>Employee ID <code>{esc(persona['employee_id'])}</code></span>
          <span>{esc(now)}</span>
        </div>
        <div class="actions">
          <a class="btn" href="{esc(IIQ_URL)}" target="_blank" rel="noopener">Open IdentityIQ</a>
          <a class="btn ghost" href="/logout">Sign out</a>
        </div>
      </div>
      <div class="grid">
        <section class="section">
          <h2>Applications</h2>
          <div class="apps">
            <a class="app" href="{esc(IIQ_URL)}" target="_blank" rel="noopener">
              <div><strong>IdentityIQ</strong><span>Request access, approvals, certifications</span></div>
              <div class="go">Open →</div>
            </a>
            <a class="app" href="{esc(WIRE_URL)}" target="_blank" rel="noopener">
              <div><strong>Wire Portal API</strong><span>Connector-mock account directory</span></div>
              <div class="go">Open →</div>
            </a>
            <a class="app" href="{esc(ACADEMY_URL)}" target="_blank" rel="noopener">
              <div><strong>Meridian Academy</strong><span>Lessons and Verify now</span></div>
              <div class="go">Open →</div>
            </a>
            <a class="app" href="{esc(TELLER_URL)}" target="_blank" rel="noopener">
              <div><strong>Teller console</strong><span>Operator desks &amp; org chart</span></div>
              <div class="go">Open →</div>
            </a>
            <a class="app" href="{esc(GITEA_URL)}" target="_blank" rel="noopener">
              <div><strong>Gitea (dev portal)</strong><span>Second SSO app via Meridian IdP</span></div>
              <div class="go">Open →</div>
            </a>
            <a class="app" href="{esc(MAILPIT_URL)}" target="_blank" rel="noopener">
              <div><strong>Mailpit</strong><span>Catch-all lab email for approvals &amp; certs</span></div>
              <div class="go">Open →</div>
            </a>
            <a class="app" href="{esc(WORKSTATION_URL)}" target="_blank" rel="noopener">
              <div><strong>Workstation</strong><span>Laptop login gate — grant/revoke proof</span></div>
              <div class="go">Open →</div>
            </a>
            <a class="app" href="{esc(HR_INTRANET_URL)}" target="_blank" rel="noopener">
              <div><strong>HR Self-Service</strong><span>Intranet SSO · mnb-hr-intranet</span></div>
              <div class="go">Open →</div>
            </a>
            <a class="app" href="{esc(FINANCE_URL)}" target="_blank" rel="noopener">
              <div><strong>Finance Portal</strong><span>Intranet SSO · mnb-finance-portal</span></div>
              <div class="go">Open →</div>
            </a>
          </div>
          <h2 style="margin-top:1.35rem">Today at Meridian</h2>
          <div class="notice">
            <strong>Access review window</strong>
            Manager certifications for Treasury entitlements open this week. Complete decisions in IdentityIQ before Friday close.
          </div>
          <div class="notice">
            <strong>Provisioning proof</strong>
            This portal session confirms Keycloak SSO after IIQ/HCM lifecycle. Leaver disable should revoke this login.
          </div>
        </section>
        <section class="section">
          <h2>Identity profile</h2>
          <div class="facts">
            <div class="fact"><label>Email</label><b>{esc(email)}</b></div>
            <div class="fact"><label>Manager</label><b>{esc(persona['manager'])}</b></div>
            <div class="fact"><label>Department</label><b>{esc(persona['department'])}</b></div>
            <div class="fact"><label>Location</label><b>{esc(persona['location'])}</b></div>
          </div>
          <h2>Entitlements</h2>
          <table class="table">
            <thead><tr><th>Access</th><th>Status</th><th>Notes</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
          <div class="proof" style="border-top:0;margin-top:0.75rem;padding-top:0">
            OIDC <code>sub={esc(sub)}</code>
          </div>
        </section>
      </div>
    </div>"""
    return html_shell("Home", body, signed_in=True, username=str(preferred))


def html_page(title: str, body: str) -> bytes:
    """Simple panel wrapper for error / utility pages."""
    wrapped = f'<div class="panel"><div class="hero">{body}</div></div>'
    return html_shell(title, wrapped)


class Handler(BaseHTTPRequestHandler):
    server_version = "MNBEmployeePortal/1.0"

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
            return self._send(200, json.dumps({"ok": True, "service": "employee-portal"}).encode(), "application/json")

        if path == "/login":
            try:
                conf = discovery()
            except Exception as e:  # noqa: BLE001
                body = html_page("IdP unavailable", f"<p>Keycloak discovery failed: <code>{esc(e)}</code></p><p><a class='btn' href='/'>Back</a></p>")
                return self._send(503, body)
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
                return self._send(
                    400,
                    html_page("Login failed", f"<p>IdP error: <code>{esc(detail)}</code></p><p><a class='btn' href='/login'>Try again</a></p>"),
                )
            code = (qs.get("code") or [""])[0]
            state = (qs.get("state") or [""])[0]
            if not code or state not in PENDING:
                return self._send(400, html_page("Login failed", "<p>Missing or invalid OIDC state/code.</p><p><a class='btn' href='/login'>Try again</a></p>"))
            verifier = PENDING.pop(state)
            try:
                conf = discovery()
                token_endpoint = conf["token_endpoint"]
                if KEYCLOAK_PUBLIC in token_endpoint:
                    token_endpoint = token_endpoint.replace(KEYCLOAK_PUBLIC, KEYCLOAK_INTERNAL)
                data = urllib.parse.urlencode(
                    {
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": f"{PORTAL_PUBLIC}/callback",
                        "client_id": CLIENT_ID,
                        "code_verifier": verifier,
                    }
                ).encode()
                tokens = _http_json(
                    token_endpoint,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                userinfo = jwt_claims(tokens.get("id_token") or "")
                if not userinfo.get("preferred_username") and not userinfo.get("email"):
                    userinfo = jwt_claims(tokens.get("access_token") or "")
                if not userinfo:
                    access = tokens.get("access_token")
                    req = urllib.request.Request(
                        conf["userinfo_endpoint"].replace(KEYCLOAK_PUBLIC, KEYCLOAK_INTERNAL),
                        headers={"Authorization": f"Bearer {access}"},
                    )
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        userinfo = json.loads(resp.read().decode("utf-8"))
            except Exception as e:  # noqa: BLE001
                return self._send(502, html_page("Token exchange failed", f"<p><code>{esc(e)}</code></p><p><a class='btn' href='/login'>Try again</a></p>"))
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

        return self._send(404, html_page("Not found", f"<p>No route <code>{esc(path)}</code></p><p><a class='btn' href='/'>Home</a></p>"))


def main() -> None:
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"employee-portal on http://{HOST}:{PORT} (IdP internal={KEYCLOAK_INTERNAL} public={KEYCLOAK_PUBLIC} realm={REALM})")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
