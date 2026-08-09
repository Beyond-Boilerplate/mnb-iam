#!/usr/bin/env python3
"""Meridian connector mock — Wire Portal, SCIM, Workday-shaped HCM, CRM SCIM, ITSM.

  python3 tools/connector-mock/serve.py
  -> http://127.0.0.1:8091/health
  -> http://127.0.0.1:8091/users                 (GET/POST/PATCH — mutable)
  -> http://127.0.0.1:8091/scim/v2/Users         (GET/PATCH — mutable)
  -> http://127.0.0.1:8091/hcm/ui              (MNB Workday helper UI)
  -> http://127.0.0.1:8091/hcm/v1/workers
  -> http://127.0.0.1:8091/crm/scim/v2/Users     (GET/POST/PATCH + filter)
  -> http://127.0.0.1:8091/itsm/v1/catalog
  -> http://127.0.0.1:8091/itsm/v1/tickets
"""

from __future__ import annotations

import json
import os
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

try:
    from keycloak_idp import (  # type: ignore
        create_user_scim as idp_create_user,
        get_group_scim as idp_get_group,
        get_user_scim as idp_get_user,
        health as idp_health,
        list_groups_scim as idp_list_groups,
        list_users_scim as idp_list_users,
        patch_group_scim as idp_patch_group,
        patch_user_scim as idp_patch_user,
        put_group_scim as idp_put_group,
    )
except ImportError:  # container layout: same directory as serve.py
    import sys
    from pathlib import Path as _P

    sys.path.insert(0, str(_P(__file__).resolve().parent))
    from keycloak_idp import (  # type: ignore
        create_user_scim as idp_create_user,
        get_group_scim as idp_get_group,
        get_user_scim as idp_get_user,
        health as idp_health,
        list_groups_scim as idp_list_groups,
        list_users_scim as idp_list_users,
        patch_group_scim as idp_patch_group,
        patch_user_scim as idp_patch_user,
        put_group_scim as idp_put_group,
    )

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
_WS_STATE: dict | None = None
_SCIM_STATE: dict | None = None
_CRM_STATE: dict | None = None
_ITSM_TICKETS: list[dict] = []
_ENTRA_STATE: dict | None = None

_HCM_PATCH_FIELDS = (
    "userName",
    "firstName",
    "lastName",
    "email",
    "department",
    "title",
    "managerId",
    "employeeType",
    "status",
    "hireDate",
)

_WS_PATCH_FIELDS = (
    "username",
    "email",
    "employeeId",
    "active",
    "entitlements",
)


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


def ws_payload() -> dict:
    """Wire Portal REST /users — mutable so Create/Update/Disable survive re-GET."""
    global _WS_STATE
    if _WS_STATE is None:
        _WS_STATE = load_json(WS_USERS) or {"users": []}
        if "users" not in _WS_STATE:
            _WS_STATE = {"users": []}
    return _WS_STATE


def scim_payload() -> dict:
    """Wire SCIM /scim/v2/Users — separate store from REST (Lesson 209/237)."""
    global _SCIM_STATE
    if _SCIM_STATE is None:
        _SCIM_STATE = load_json(SCIM_USERS) or {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "totalResults": 0,
            "Resources": [],
        }
    return _SCIM_STATE


def crm_payload() -> dict:
    """CRM SCIM /crm/scim/v2/Users — mutable for filter + PATCH drills (Lesson 238)."""
    global _CRM_STATE
    if _CRM_STATE is None:
        _CRM_STATE = load_json(CRM_USERS) or {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "totalResults": 0,
            "Resources": [],
        }
    return _CRM_STATE


def _scim_filter_resources(resources: list, filt: str) -> list:
    if not filt:
        return list(resources)
    if "userName eq" in filt and '"' in filt:
        name = filt.split('"')[1]
        return [r for r in resources if r.get("userName") == name]
    if "externalId eq" in filt and '"' in filt:
        eid = filt.split('"')[1]
        return [r for r in resources if r.get("externalId") == eid]
    return list(resources)


def _apply_scim_patch(user: dict, body: dict) -> dict:
    updated = dict(user)
    active = updated.get("active", True)
    for op in body.get("Operations") or []:
        path = (op.get("path") or "").strip()
        val = op.get("value")
        if path == "active" or (isinstance(val, dict) and "active" in val):
            if isinstance(val, dict) and "active" in val:
                active = bool(val["active"])
            elif isinstance(val, bool):
                active = val
        if path == "groups" and isinstance(val, list):
            updated["groups"] = val
        if path in {"emails", "userName", "externalId"} and val is not None:
            updated[path.split(".")[0] if "." not in path else path] = val
        if (op.get("op") or "").lower() in {"replace", "add"} and path == "" and isinstance(val, dict):
            if "active" in val:
                active = bool(val["active"])
            for k in ("userName", "externalId", "emails", "groups", "name"):
                if k in val:
                    updated[k] = val[k]
    if "active" in body:
        active = bool(body["active"])
    updated["active"] = active
    return updated


def hcm_ui_html() -> bytes:
    """Self-contained MNB Workday admin UI (browse / add / edit / terminate)."""
    return _HCM_UI_HTML.encode("utf-8")


_HCM_UI_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>MNB Workday</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20viewBox%3D%220%200%2032%2032%22%3E%20%3Crect%20width%3D%2232%22%20height%3D%2232%22%20rx%3D%227%22%20fill%3D%22%230875e1%22/%3E%20%3Ctext%20x%3D%2216%22%20y%3D%2221.5%22%20text-anchor%3D%22middle%22%20font-family%3D%22ui-sans-serif%2Csystem-ui%2C-apple-system%2Csans-serif%22%20font-size%3D%2211%22%20font-weight%3D%22700%22%20fill%3D%22%23ffffff%22%3EWD%3C/text%3E%20%3C/svg%3E" type="image/svg+xml" />
<style>
  :root {
    --navy: #0b2a4a;
    --teal: #0d7377;
    --teal-dark: #095456;
    --sand: #f4f7f9;
    --line: #d5dee6;
    --text: #1a2330;
    --muted: #5a6b7d;
    --danger: #9b2c2c;
    --ok: #1a6b3c;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: "Segoe UI", system-ui, sans-serif;
    color: var(--text);
    background: linear-gradient(165deg, #e8eef4 0%, var(--sand) 45%, #eef5f5 100%);
    min-height: 100vh;
  }
  header {
    background: var(--navy);
    color: #fff;
    padding: 1.1rem 1.5rem;
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 0.75rem 1.5rem;
    border-bottom: 3px solid var(--teal);
  }
  header h1 {
    margin: 0;
    font-size: 1.35rem;
    font-weight: 650;
    letter-spacing: 0.02em;
  }
  header .sub { color: #a8c0d8; font-size: 0.9rem; }
  main { max-width: 1100px; margin: 0 auto; padding: 1.25rem 1.25rem 3rem; }
  .toolbar {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    align-items: center;
    margin-bottom: 1rem;
  }
  .toolbar input[type="search"] {
    flex: 1 1 220px;
    padding: 0.55rem 0.75rem;
    border: 1px solid var(--line);
    border-radius: 4px;
    font-size: 0.95rem;
  }
  .meta { color: var(--muted); font-size: 0.85rem; }
  button, .btn {
    appearance: none;
    border: none;
    border-radius: 4px;
    padding: 0.5rem 0.9rem;
    font-size: 0.9rem;
    cursor: pointer;
    background: var(--teal);
    color: #fff;
    font-weight: 600;
  }
  button:hover, .btn:hover { background: var(--teal-dark); }
  button.secondary { background: #fff; color: var(--navy); border: 1px solid var(--line); }
  button.secondary:hover { background: #f0f4f8; }
  button.danger { background: var(--danger); }
  button.danger:hover { background: #7a2020; }
  button:disabled { opacity: 0.5; cursor: not-allowed; }
  .flash {
    display: none;
    margin-bottom: 1rem;
    padding: 0.65rem 0.9rem;
    border-radius: 4px;
    font-size: 0.9rem;
  }
  .flash.ok { display: block; background: #e6f4ea; color: var(--ok); border: 1px solid #b7dfc4; }
  .flash.err { display: block; background: #fde8e8; color: var(--danger); border: 1px solid #f0b4b4; }
  table {
    width: 100%;
    border-collapse: collapse;
    background: #fff;
    border: 1px solid var(--line);
    border-radius: 6px;
    overflow: hidden;
    font-size: 0.88rem;
  }
  th, td { text-align: left; padding: 0.55rem 0.65rem; border-bottom: 1px solid var(--line); vertical-align: middle; }
  th { background: #f0f4f8; color: var(--navy); font-weight: 650; white-space: nowrap; }
  tr:last-child td { border-bottom: none; }
  tr.term { opacity: 0.65; }
  .badge {
    display: inline-block;
    padding: 0.12rem 0.45rem;
    border-radius: 3px;
    font-size: 0.75rem;
    font-weight: 650;
  }
  .badge.active { background: #e6f4ea; color: var(--ok); }
  .badge.term { background: #fde8e8; color: var(--danger); }
  .actions { display: flex; gap: 0.35rem; flex-wrap: wrap; }
  .actions button { padding: 0.3rem 0.55rem; font-size: 0.8rem; }
  dialog {
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 0;
    width: min(520px, 94vw);
    box-shadow: 0 12px 40px rgba(11, 42, 74, 0.2);
  }
  dialog::backdrop { background: rgba(11, 42, 74, 0.35); }
  .dlg-head {
    background: var(--navy);
    color: #fff;
    padding: 0.85rem 1.1rem;
    font-weight: 650;
  }
  .dlg-body { padding: 1.1rem; }
  .dlg-foot {
    padding: 0.75rem 1.1rem 1.1rem;
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
  }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.65rem 0.75rem; }
  label { display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.8rem; color: var(--muted); font-weight: 600; }
  label.span2 { grid-column: 1 / -1; }
  input, select {
    padding: 0.45rem 0.55rem;
    border: 1px solid var(--line);
    border-radius: 4px;
    font-size: 0.9rem;
    color: var(--text);
  }
  footer.note {
    margin-top: 1.25rem;
    color: var(--muted);
    font-size: 0.8rem;
    line-height: 1.45;
  }
  code { font-size: 0.85em; background: #eef2f6; padding: 0.05em 0.3em; border-radius: 3px; }
  @media (max-width: 640px) {
    .grid { grid-template-columns: 1fr; }
    table { font-size: 0.8rem; }
    .hide-sm { display: none; }
  }
</style>
</head>
<body>
<header>
  <h1>MNB Workday</h1>
  <span class="sub">Meridian HCM lab helper — browse, hire, edit, terminate</span>
</header>
<main>
  <div id="flash" class="flash" role="status"></div>
  <div class="toolbar">
    <input type="search" id="q" placeholder="Search id, userName, name, email, department…" autocomplete="off"/>
    <button type="button" id="btnRefresh" class="secondary">Refresh</button>
    <button type="button" id="btnAdd">Add worker</button>
    <span class="meta" id="count"></span>
  </div>
  <div style="overflow-x:auto">
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>User</th>
          <th>Name</th>
          <th class="hide-sm">Department</th>
          <th class="hide-sm">Manager</th>
          <th>Status</th>
          <th></th>
        </tr>
      </thead>
      <tbody id="rows"></tbody>
    </table>
  </div>
  <footer class="note">
    Lab only — drives the same in-memory feed IIQ aggregates at <code>GET /hcm/v1/workers</code>.
    Terminate sets <code>active: false</code> / <code>status: Terminated</code> (no hard delete).
    Changes are lost when <code>connector-mock</code> restarts.
  </footer>
</main>

<dialog id="dlg">
  <form method="dialog" id="form">
    <div class="dlg-head" id="dlgTitle">Add worker</div>
    <div class="dlg-body">
      <input type="hidden" id="f_id"/>
      <div class="grid">
        <label>userName <input id="f_userName" required autocomplete="off"/></label>
        <label>employeeType
          <select id="f_employeeType">
            <option>Employee</option>
            <option>Contingent Worker</option>
            <option>Contractor</option>
          </select>
        </label>
        <label>firstName <input id="f_firstName" required/></label>
        <label>lastName <input id="f_lastName" required/></label>
        <label class="span2">email <input id="f_email" type="email" required/></label>
        <label>department <input id="f_department"/></label>
        <label>title <input id="f_title"/></label>
        <label class="span2">managerId <input id="f_managerId" placeholder="e.g. MNB00001 (optional)"/></label>
      </div>
    </div>
    <div class="dlg-foot">
      <button type="button" class="secondary" id="btnCancel">Cancel</button>
      <button type="submit" id="btnSave">Save</button>
    </div>
  </form>
</dialog>

<script>
(function () {
  const API = "/hcm/v1/workers";
  let workers = [];
  let mode = "create";

  const $ = (id) => document.getElementById(id);
  const flash = $("flash");
  const rows = $("rows");
  const dlg = $("dlg");
  const form = $("form");

  function showFlash(msg, ok) {
    flash.textContent = msg;
    flash.className = "flash " + (ok ? "ok" : "err");
    if (ok) setTimeout(() => { flash.className = "flash"; }, 4000);
  }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  async function api(method, path, body) {
    const opts = { method, headers: { "Accept": "application/json" } };
    if (body !== undefined) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
    const res = await fetch(path, opts);
    const text = await res.text();
    let data = null;
    try { data = text ? JSON.parse(text) : null; } catch (_) { data = { raw: text }; }
    if (!res.ok) {
      const detail = (data && (data.error || data.detail || data.message)) || res.statusText;
      throw new Error(detail || ("HTTP " + res.status));
    }
    return data;
  }

  function filtered() {
    const q = ($("q").value || "").trim().toLowerCase();
    if (!q) return workers.slice();
    return workers.filter((w) => {
      const blob = [
        w.id, w.workerId, w.userName, w.firstName, w.lastName,
        w.email, w.department, w.title, w.managerId, w.status, w.employeeType
      ].join(" ").toLowerCase();
      return blob.includes(q);
    });
  }

  function render() {
    const list = filtered();
    $("count").textContent = list.length + " of " + workers.length + " workers";
    rows.innerHTML = list.map((w) => {
      const active = w.active !== false && String(w.status || "").toLowerCase() !== "terminated";
      const name = [w.firstName, w.lastName].filter(Boolean).join(" ") || "—";
      return (
        "<tr class=\"" + (active ? "" : "term") + "\">" +
        "<td><code>" + esc(w.id) + "</code></td>" +
        "<td>" + esc(w.userName) + "</td>" +
        "<td>" + esc(name) + "</td>" +
        "<td class=\"hide-sm\">" + esc(w.department || "—") + "</td>" +
        "<td class=\"hide-sm\">" + esc(w.managerId || "—") + "</td>" +
        "<td><span class=\"badge " + (active ? "active" : "term") + "\">" +
          esc(w.status || (active ? "Active" : "Terminated")) + "</span></td>" +
        "<td><div class=\"actions\">" +
          "<button type=\"button\" class=\"secondary\" data-edit=\"" + esc(w.id) + "\">Edit</button>" +
          (active
            ? "<button type=\"button\" class=\"danger\" data-term=\"" + esc(w.id) + "\">Terminate</button>"
            : "") +
        "</div></td></tr>"
      );
    }).join("") || "<tr><td colspan=\"7\">No workers match.</td></tr>";
  }

  async function load() {
    const data = await api("GET", API);
    workers = data.workers || [];
    render();
  }

  function openCreate() {
    mode = "create";
    $("dlgTitle").textContent = "Add worker";
    $("f_id").value = "";
    $("f_userName").value = "";
    $("f_userName").disabled = false;
    $("f_firstName").value = "";
    $("f_lastName").value = "";
    $("f_email").value = "";
    $("f_department").value = "Identity & Access";
    $("f_title").value = "";
    $("f_managerId").value = "";
    $("f_employeeType").value = "Employee";
    dlg.showModal();
    $("f_userName").focus();
  }

  function openEdit(id) {
    const w = workers.find((x) => x.id === id || x.workerId === id);
    if (!w) return;
    mode = "edit";
    $("dlgTitle").textContent = "Edit worker — " + (w.id || id);
    $("f_id").value = w.id || "";
    $("f_userName").value = w.userName || "";
    $("f_userName").disabled = false;
    $("f_firstName").value = w.firstName || "";
    $("f_lastName").value = w.lastName || "";
    $("f_email").value = w.email || "";
    $("f_department").value = w.department || "";
    $("f_title").value = w.title || "";
    $("f_managerId").value = w.managerId || "";
    $("f_employeeType").value = w.employeeType || "Employee";
    dlg.showModal();
  }

  function formBody() {
    const managerId = ($("f_managerId").value || "").trim() || null;
    return {
      userName: ($("f_userName").value || "").trim(),
      firstName: ($("f_firstName").value || "").trim(),
      lastName: ($("f_lastName").value || "").trim(),
      email: ($("f_email").value || "").trim(),
      department: ($("f_department").value || "").trim() || null,
      title: ($("f_title").value || "").trim() || null,
      managerId: managerId,
      employeeType: $("f_employeeType").value || "Employee",
    };
  }

  $("btnRefresh").addEventListener("click", () => {
    load().then(() => showFlash("Refreshed from API.", true)).catch((e) => showFlash(e.message, false));
  });
  $("btnAdd").addEventListener("click", openCreate);
  $("btnCancel").addEventListener("click", () => dlg.close());
  $("q").addEventListener("input", render);

  rows.addEventListener("click", async (ev) => {
    const t = ev.target;
    if (!(t instanceof HTMLElement)) return;
    const editId = t.getAttribute("data-edit");
    const termId = t.getAttribute("data-term");
    if (editId) {
      openEdit(editId);
      return;
    }
    if (termId) {
      const w = workers.find((x) => x.id === termId);
      const label = w ? (w.userName || termId) : termId;
      if (!confirm("Terminate " + label + "? Sets active=false / status=Terminated.")) return;
      try {
        await api("PATCH", API + "/" + encodeURIComponent(termId), { active: false });
        showFlash("Terminated " + label + ".", true);
        await load();
      } catch (e) {
        showFlash(e.message, false);
      }
    }
  });

  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const body = formBody();
    if (!body.userName || !body.firstName || !body.lastName || !body.email) {
      showFlash("userName, firstName, lastName, and email are required.", false);
      return;
    }
    try {
      if (mode === "create") {
        const created = await api("POST", API, body);
        showFlash("Created worker " + (created.id || body.userName) + ".", true);
      } else {
        const id = $("f_id").value;
        await api("PATCH", API + "/" + encodeURIComponent(id), body);
        showFlash("Updated " + id + ".", true);
      }
      dlg.close();
      await load();
    } catch (e) {
      showFlash(e.message, false);
    }
  });

  load().catch((e) => showFlash("Failed to load workers: " + e.message, false));
})();
</script>
</body>
</html>
"""


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
                    "apis": ["wire", "scim", "hcm", "crm", "itsm", "entra", "idp"],
                },
            )

        if path in ("/idp/health", "/idp/scim/v2/ServiceProviderConfig"):
            if path.endswith("health"):
                return self._send(200, idp_health())
            return self._send(
                200,
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
                    "patch": {"supported": True},
                    "filter": {"supported": True, "maxResults": 100},
                    "bulk": {"supported": False},
                },
            )

        if path in ("/idp/scim/v2/Users", "/idp/scim/v2/Users/"):
            qs = parse_qs(parsed.query)
            filt = (qs.get("filter") or [""])[0]
            try:
                return self._send(200, idp_list_users(filt))
            except Exception as e:  # noqa: BLE001
                return self._send(502, {"error": "idp_upstream", "detail": str(e)})

        if path.startswith("/idp/scim/v2/Users/"):
            rid = path.rsplit("/", 1)[-1]
            try:
                user = idp_get_user(rid)
            except Exception as e:  # noqa: BLE001
                return self._send(502, {"error": "idp_upstream", "detail": str(e)})
            if not user:
                return self._send(
                    404,
                    {
                        "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
                        "detail": f"Resource {rid} not found",
                        "status": "404",
                    },
                )
            return self._send(200, user)

        if path in ("/idp/scim/v2/Groups", "/idp/scim/v2/Groups/"):
            try:
                return self._send(200, idp_list_groups())
            except Exception as e:  # noqa: BLE001
                return self._send(502, {"error": "idp_upstream", "detail": str(e)})

        if path.startswith("/idp/scim/v2/Groups/"):
            rid = path.rsplit("/", 1)[-1]
            try:
                group = idp_get_group(rid)
            except Exception as e:  # noqa: BLE001
                return self._send(502, {"error": "idp_upstream", "detail": str(e)})
            if not group:
                return self._send(
                    404,
                    {
                        "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
                        "detail": f"Resource {rid} not found",
                        "status": "404",
                    },
                )
            return self._send(200, group)

        # --- Wire Portal ---
        if path == "/users":
            return self._send(200, ws_payload())

        if path.startswith("/users/"):
            uid = path.split("/")[-1]
            for u in ws_payload().get("users", []):
                if u.get("id") == uid or u.get("username") == uid:
                    return self._send(200, u)
            return self._send(404, {"error": "not_found", "id": uid})

        # --- Wire SCIM ---
        if path in ("/scim/v2/Users", "/scim/v2/Users/"):
            data = scim_payload()
            qs = parse_qs(parsed.query)
            filt = (qs.get("filter") or [""])[0]
            resources = _scim_filter_resources(list(data.get("Resources") or []), filt)
            return self._send(
                200,
                {
                    "schemas": data.get("schemas")
                    or ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
                    "totalResults": len(resources),
                    "Resources": resources,
                },
            )

        if path.startswith("/scim/v2/Users/"):
            rid = path.rsplit("/", 1)[-1]
            for r in scim_payload().get("Resources") or []:
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

        # --- Workday-shaped HCM (UI + API) ---
        if path == "/hcm/ui":
            return self._send(200, hcm_ui_html(), content_type="text/html; charset=utf-8")

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
            data = crm_payload()
            qs = parse_qs(parsed.query)
            filt = (qs.get("filter") or [""])[0]
            resources = _scim_filter_resources(list(data.get("Resources") or []), filt)
            return self._send(
                200,
                {
                    "schemas": data.get("schemas")
                    or ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
                    "totalResults": len(resources),
                    "Resources": resources,
                },
            )

        if path.startswith("/crm/scim/v2/Users/"):
            rid = path.rsplit("/", 1)[-1]
            for r in crm_payload().get("Resources") or []:
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
            catalog_id = body.get("catalogId") or body.get("item") or body.get("catalogItem")
            ticket = {
                "id": f"INC{uuid.uuid4().hex[:6].upper()}",
                "shortDescription": body.get("shortDescription") or "Access request",
                "requestedFor": body.get("requestedFor") or body.get("requester"),
                "requester": body.get("requester") or body.get("requestedFor"),
                "catalogId": catalog_id,
                "item": body.get("item") or catalog_id,
                "identityRequestId": body.get("identityRequestId")
                or body.get("identityRequest")
                or body.get("requestId"),
                "state": "open",
            }
            if not ticket.get("requestedFor") and not catalog_id:
                return self._send(
                    400,
                    {
                        "error": "bad_request",
                        "detail": "requester/requestedFor and catalogId/item are required",
                    },
                )
            _ITSM_TICKETS.append(ticket)
            return self._send(201, ticket)

        # Wire Portal create
        if path == "/users":
            data = ws_payload()
            users = list(data.get("users") or [])
            uid = body.get("id") or f"wp-{uuid.uuid4().hex[:6]}"
            username = body.get("username") or body.get("userName")
            if not username:
                return self._send(400, {"error": "bad_request", "detail": "username required"})
            user = {
                "id": uid,
                "username": username,
                "email": body.get("email") or f"{username}@meridiannb.com",
                "employeeId": body.get("employeeId") or body.get("externalId") or "",
                "active": body.get("active", True),
                "entitlements": body.get("entitlements") or [],
            }
            users = [u for u in users if u.get("id") != uid and u.get("username") != username]
            users.append(user)
            data["users"] = users
            return self._send(201, user)

        # CRM SCIM create (lab disposable users)
        if path in ("/crm/scim/v2/Users", "/crm/scim/v2/Users/"):
            data = crm_payload()
            resources = list(data.get("Resources") or [])
            uname = body.get("userName") or body.get("username")
            if not uname:
                return self._send(400, {"error": "bad_request", "detail": "userName required"})
            rid = body.get("id") or f"crm-{uname}"
            user = {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "id": rid,
                "userName": uname,
                "name": body.get("name")
                or {
                    "givenName": body.get("givenName") or uname.split(".")[0].title(),
                    "familyName": body.get("familyName") or "Lab",
                },
                "emails": body.get("emails")
                or [{"value": body.get("email") or f"{uname}@meridiannb.com", "primary": True}],
                "active": body.get("active", True),
                "externalId": body.get("externalId") or body.get("employeeId") or "",
                "groups": body.get("groups") or [{"display": "CRM-Users"}],
            }
            resources = [r for r in resources if r.get("id") != rid and r.get("userName") != uname]
            resources.append(user)
            data["Resources"] = resources
            data["totalResults"] = len(resources)
            return self._send(201, user)

        if path in ("/idp/scim/v2/Users", "/idp/scim/v2/Users/"):
            try:
                created = idp_create_user(body)
                return self._send(201, created)
            except Exception as e:  # noqa: BLE001
                return self._send(502, {"error": "idp_upstream", "detail": str(e)})

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
                    for k in _HCM_PATCH_FIELDS:
                        if k in body:
                            w[k] = body[k]
                    if "status" in body and "active" not in body:
                        st = str(body.get("status") or "")
                        if st.lower() == "terminated":
                            w["active"] = False
                        elif st.lower() == "active":
                            w["active"] = True
                    return self._send(200, w)
            return self._send(404, {"error": "not_found", "id": wid})

        if path.startswith("/idp/scim/v2/Users/"):
            rid = path.rsplit("/", 1)[-1]
            try:
                return self._send(200, idp_patch_user(rid, body))
            except Exception as e:  # noqa: BLE001
                return self._send(502, {"error": "idp_upstream", "detail": str(e)})

        if path.startswith("/idp/scim/v2/Groups/"):
            rid = path.rsplit("/", 1)[-1]
            try:
                return self._send(200, idp_patch_group(rid, body))
            except Exception as e:  # noqa: BLE001
                return self._send(502, {"error": "idp_upstream", "detail": str(e)})

        if path.startswith("/entra/scim/v2/Users/"):
            rid = path.rsplit("/", 1)[-1]
            data = entra_payload()
            user = next(
                (r for r in data.get("Resources") or [] if r.get("id") == rid or r.get("userName") == rid),
                None,
            )
            if not user:
                return self._send(404, {"error": "not_found", "id": rid})
            patched = _apply_scim_patch(user, body)
            user.clear()
            user.update(patched)
            return self._send(200, user)

        # Wire Portal update / disable
        if path.startswith("/users/"):
            uid = path.rsplit("/", 1)[-1]
            data = ws_payload()
            for i, u in enumerate(data.get("users") or []):
                if u.get("id") == uid or u.get("username") == uid:
                    updated = dict(u)
                    for k in _WS_PATCH_FIELDS:
                        if k in body:
                            updated[k] = body[k]
                    # Allow SCIM-ish or plan-shaped aliases
                    if "userName" in body and "username" not in body:
                        updated["username"] = body["userName"]
                    if "active" in body:
                        updated["active"] = bool(body["active"])
                    data["users"][i] = updated
                    return self._send(200, updated)
            return self._send(404, {"error": "not_found", "id": uid})

        # CRM SCIM PATCH
        if path.startswith("/crm/scim/v2/Users/"):
            rid = path.rsplit("/", 1)[-1]
            data = crm_payload()
            resources = list(data.get("Resources") or [])
            for i, r in enumerate(resources):
                if r.get("id") == rid or r.get("userName") == rid:
                    patched = _apply_scim_patch(r, body)
                    resources[i] = patched
                    data["Resources"] = resources
                    data["totalResults"] = len(resources)
                    return self._send(200, patched)
            return self._send(404, {"error": "not_found", "id": rid})

        if not path.startswith("/scim/v2/Users/"):
            return self._send(404, {"error": "not_found", "path": path})

        rid = path.rsplit("/", 1)[-1]
        data = scim_payload()
        resources = list(data.get("Resources") or [])
        for i, r in enumerate(resources):
            if r.get("id") == rid or r.get("userName") == rid:
                patched = _apply_scim_patch(r, body)
                resources[i] = patched
                data["Resources"] = resources
                data["totalResults"] = len(resources)
                return self._send(200, patched)
        return self._send(
            404,
            {
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
                "detail": f"Resource {rid} not found",
                "status": "404",
            },
        )

    def do_PUT(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        body = self._read_json()

        if path.startswith("/idp/scim/v2/Groups/"):
            rid = path.rsplit("/", 1)[-1]
            try:
                return self._send(200, idp_put_group(rid, body))
            except Exception as e:  # noqa: BLE001
                return self._send(502, {"error": "idp_upstream", "detail": str(e)})

        if path.startswith("/idp/scim/v2/Users/"):
            # Full replace — reuse patch merge semantics
            rid = path.rsplit("/", 1)[-1]
            try:
                return self._send(200, idp_patch_user(rid, body))
            except Exception as e:  # noqa: BLE001
                return self._send(502, {"error": "idp_upstream", "detail": str(e)})

        return self._send(404, {"error": "not_found", "path": path})


def main() -> None:
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"mnb-connector-mock listening on http://{HOST}:{PORT}")
    print("  GET  /health")
    print("  GET/POST/PATCH /users | GET/PATCH /scim/v2/Users")
    print("  GET  /hcm/ui  (MNB Workday helper UI)")
    print("  GET  /hcm/v1/workers | POST /hcm/v1/workers | PATCH /hcm/v1/workers/{id}")
    print("  GET/POST/PATCH /crm/scim/v2/Users  (filter + active)")
    print("  GET  /itsm/v1/catalog | GET/POST /itsm/v1/tickets")
    print("  GET  /entra/v1/users | /entra/scim/v2/Users | PATCH /entra/scim/v2/Users/{id}")
    print("  GET/POST/PATCH/PUT /idp/scim/v2/Users|Groups  (Keycloak birthright)")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
