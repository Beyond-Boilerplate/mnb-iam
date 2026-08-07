"""Keycloak Admin API helpers exposed as a thin SCIM facade for IIQ birthright.

Lab only: connector-mock calls Keycloak with the iiq-scim client credentials.
Enable roles via tools/lab/enterprise/keycloak-enable-iiq-provisioner.sh
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

KC_BASE = os.environ.get("KEYCLOAK_URL", "http://keycloak:8080").rstrip("/")
KC_REALM = os.environ.get("KEYCLOAK_REALM", "meridian")
KC_CLIENT_ID = os.environ.get("KEYCLOAK_IIQ_CLIENT_ID", "iiq-scim")
KC_CLIENT_SECRET = os.environ.get("KEYCLOAK_IIQ_CLIENT_SECRET", "mnb-iiq-scim-secret")
DEFAULT_PASSWORD = os.environ.get("KEYCLOAK_JOINER_PASSWORD", "LabUser1!")

_token_cache: dict[str, Any] = {"access_token": None}


def _http(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    body: dict | list | None = None,
    form: dict[str, str] | None = None,
) -> tuple[int, Any, dict[str, str]]:
    data = None
    hdrs = dict(headers or {})
    if form is not None:
        data = urllib.parse.urlencode(form).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/x-www-form-urlencoded")
    elif body is not None:
        data = json.dumps(body).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            payload: Any = {}
            if raw:
                try:
                    payload = json.loads(raw.decode("utf-8"))
                except json.JSONDecodeError:
                    payload = raw.decode("utf-8", errors="replace")
            return resp.status, payload, {k.lower(): v for k, v in resp.headers.items()}
    except urllib.error.HTTPError as e:
        raw = e.read()
        payload = {}
        if raw:
            try:
                payload = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                payload = raw.decode("utf-8", errors="replace")
        return e.code, payload, {k.lower(): v for k, v in e.headers.items()}


def get_token(force: bool = False) -> str:
    if _token_cache.get("access_token") and not force:
        return str(_token_cache["access_token"])
    code, payload, _ = _http(
        "POST",
        f"{KC_BASE}/realms/{KC_REALM}/protocol/openid-connect/token",
        form={
            "grant_type": "client_credentials",
            "client_id": KC_CLIENT_ID,
            "client_secret": KC_CLIENT_SECRET,
        },
    )
    if code >= 400 or not isinstance(payload, dict) or not payload.get("access_token"):
        raise RuntimeError(f"Keycloak token failed ({code}): {payload}")
    _token_cache["access_token"] = payload["access_token"]
    return str(payload["access_token"])


def _admin(method: str, path: str, body: dict | list | None = None) -> tuple[int, Any, dict[str, str]]:
    token = get_token()
    code, payload, headers = _http(
        method,
        f"{KC_BASE}/admin/realms/{KC_REALM}{path}",
        headers={"Authorization": f"Bearer {token}"},
        body=body,
    )
    if code == 401:
        token = get_token(force=True)
        code, payload, headers = _http(
            method,
            f"{KC_BASE}/admin/realms/{KC_REALM}{path}",
            headers={"Authorization": f"Bearer {token}"},
            body=body,
        )
    return code, payload, headers


def _group_index() -> dict[str, str]:
    """name -> id for top-level groups."""
    code, payload, _ = _admin("GET", "/groups?max=200")
    if code >= 400 or not isinstance(payload, list):
        return {}
    out: dict[str, str] = {}
    for g in payload:
        name = g.get("name")
        gid = g.get("id")
        if name and gid:
            out[str(name)] = str(gid)
    return out


def _user_to_scim(u: dict, groups: list[str] | None = None) -> dict:
    attrs = u.get("attributes") or {}
    emp = attrs.get("employeeId") or attrs.get("employeeNumber") or []
    if isinstance(emp, list):
        emp = emp[0] if emp else None
    email = None
    for e in u.get("email", []) if isinstance(u.get("email"), list) else [u.get("email")]:
        if e:
            email = e
            break
    return {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "id": u.get("id"),
        "userName": u.get("username"),
        "active": bool(u.get("enabled", True)),
        "emails": email,
        "externalId": emp,
        "name": {
            "givenName": u.get("firstName"),
            "familyName": u.get("lastName"),
            "formatted": " ".join(
                x for x in [u.get("firstName"), u.get("lastName")] if x
            ),
        },
        "groups": groups if groups is not None else [],
    }


def list_users_scim(filter_expr: str = "") -> dict:
    q = "/users?max=200"
    if 'userName eq "' in filter_expr:
        uname = filter_expr.split('userName eq "')[1].split('"')[0]
        q = f"/users?username={urllib.parse.quote(uname)}&exact=true&max=20"
    code, payload, _ = _admin("GET", q)
    if code >= 400:
        raise RuntimeError(f"list users failed ({code}): {payload}")
    users = payload if isinstance(payload, list) else []
    resources = [_user_to_scim(u) for u in users]
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": len(resources),
        "Resources": resources,
    }


def get_user_scim(rid: str) -> dict | None:
    code, payload, _ = _admin("GET", f"/users/{urllib.parse.quote(rid)}")
    if code == 404:
        # try username
        code2, payload2, _ = _admin(
            "GET", f"/users?username={urllib.parse.quote(rid)}&exact=true&max=5"
        )
        if code2 >= 400 or not isinstance(payload2, list) or not payload2:
            return None
        payload = payload2[0]
        rid = str(payload.get("id"))
    elif code >= 400 or not isinstance(payload, dict):
        return None
    gcode, gpayload, _ = _admin("GET", f"/users/{urllib.parse.quote(str(payload.get('id')))}/groups")
    groups: list[str] = []
    if gcode < 400 and isinstance(gpayload, list):
        groups = [str(g.get("name")) for g in gpayload if g.get("name")]
    return _user_to_scim(payload, groups)


def list_groups_scim() -> dict:
    idx = _group_index()
    resources = [
        {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "id": gid,
            "displayName": name,
            "externalId": name,
        }
        for name, gid in sorted(idx.items())
    ]
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": len(resources),
        "Resources": resources,
    }


def _normalize_groups(value: Any) -> list[str]:
    names: list[str] = []
    if value is None:
        return names
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                names.append(item)
            elif isinstance(item, dict):
                names.append(
                    str(
                        item.get("displayName")
                        or item.get("value")
                        or item.get("externalId")
                        or item.get("display")
                        or ""
                    )
                )
    return [n for n in names if n]


def _set_password(user_id: str, password: str) -> None:
    code, payload, _ = _admin(
        "PUT",
        f"/users/{urllib.parse.quote(user_id)}/reset-password",
        {
            "type": "password",
            "value": password,
            "temporary": False,
        },
    )
    if code >= 400:
        raise RuntimeError(f"set password failed ({code}): {payload}")


def _set_groups(user_id: str, group_names: list[str]) -> None:
    idx = _group_index()
    # current
    code, current, _ = _admin("GET", f"/users/{urllib.parse.quote(user_id)}/groups")
    current_ids = set()
    if code < 400 and isinstance(current, list):
        current_ids = {str(g.get("id")) for g in current if g.get("id")}
    wanted_ids = {idx[n] for n in group_names if n in idx}
    for gid in wanted_ids - current_ids:
        c, p, _ = _admin("PUT", f"/users/{urllib.parse.quote(user_id)}/groups/{gid}", {})
        if c >= 400:
            raise RuntimeError(f"add group {gid} failed ({c}): {p}")
    for gid in current_ids - wanted_ids:
        # only remove groups we manage in birthright path if explicitly replaced;
        # for PATCH replace we sync to wanted set
        c, p, _ = _admin("DELETE", f"/users/{urllib.parse.quote(user_id)}/groups/{gid}")
        if c >= 400:
            raise RuntimeError(f"remove group {gid} failed ({c}): {p}")


def create_user_scim(body: dict) -> dict:
    username = body.get("userName") or body.get("username")
    if not username:
        raise RuntimeError("userName required")
    name = body.get("name") if isinstance(body.get("name"), dict) else {}
    email = body.get("emails")
    if isinstance(email, list) and email:
        first = email[0]
        email = first.get("value") if isinstance(first, dict) else first
    attrs: dict[str, list[str]] = {}
    ext = body.get("externalId")
    if ext:
        attrs["employeeId"] = [str(ext)]
    # also accept employeeId top-level
    if body.get("employeeId"):
        attrs["employeeId"] = [str(body["employeeId"])]

    kc_user = {
        "username": username,
        "enabled": bool(body.get("active", True)),
        "email": email,
        "firstName": name.get("givenName") or body.get("givenName") or body.get("firstName"),
        "lastName": name.get("familyName") or body.get("familyName") or body.get("lastName"),
        "emailVerified": True,
        "attributes": attrs,
    }
    code, payload, headers = _admin("POST", "/users", kc_user)
    if code not in (201, 204) and code != 409:
        raise RuntimeError(f"create user failed ({code}): {payload}")

    user_id = None
    loc = headers.get("location") or headers.get("Location")
    if loc and "/" in loc:
        user_id = loc.rstrip("/").rsplit("/", 1)[-1]
    if not user_id:
        found = get_user_scim(str(username))
        if found:
            user_id = found.get("id")
    if not user_id:
        raise RuntimeError("create user: could not resolve user id")

    password = body.get("password") or DEFAULT_PASSWORD
    _set_password(str(user_id), str(password))

    if attrs:
        code_g, full, _ = _admin("GET", f"/users/{urllib.parse.quote(str(user_id))}")
        if code_g < 400 and isinstance(full, dict):
            merged = dict(full.get("attributes") or {})
            merged.update(attrs)
            full["attributes"] = merged
            code_u, payload_u, _ = _admin("PUT", f"/users/{urllib.parse.quote(str(user_id))}", full)
            if code_u >= 400:
                raise RuntimeError(f"set attributes failed ({code_u}): {payload_u}")

    groups = _normalize_groups(body.get("groups"))
    if groups:
        _set_groups(str(user_id), groups)

    out = get_user_scim(str(user_id))
    if not out:
        raise RuntimeError("create user: fetch after create failed")
    return out


def patch_user_scim(rid: str, body: dict) -> dict:
    existing = get_user_scim(rid)
    if not existing:
        raise RuntimeError(f"user not found: {rid}")
    user_id = str(existing["id"])

    enabled = existing.get("active", True)
    groups = list(existing.get("groups") or [])
    for op in body.get("Operations") or []:
        path = (op.get("path") or "").lstrip("/")
        val = op.get("value")
        opname = (op.get("op") or "replace").lower()
        if path == "active" or (isinstance(val, dict) and "active" in val):
            if isinstance(val, dict) and "active" in val:
                enabled = bool(val["active"])
            elif isinstance(val, bool):
                enabled = val
        if path == "groups" or (isinstance(val, dict) and "groups" in val):
            raw = val.get("groups") if isinstance(val, dict) and "groups" in val else val
            if opname == "add":
                groups = list(dict.fromkeys(groups + _normalize_groups(raw)))
            else:
                groups = _normalize_groups(raw)
    if "active" in body:
        enabled = bool(body["active"])
    if "groups" in body:
        groups = _normalize_groups(body["groups"])

    code, payload, _ = _admin("PUT", f"/users/{urllib.parse.quote(user_id)}", {"enabled": enabled})
    # Keycloak PUT requires full representation — fetch + merge
    code_g, full, _ = _admin("GET", f"/users/{urllib.parse.quote(user_id)}")
    if code_g < 400 and isinstance(full, dict):
        full["enabled"] = enabled
        code, payload, _ = _admin("PUT", f"/users/{urllib.parse.quote(user_id)}", full)
        if code >= 400:
            raise RuntimeError(f"update user failed ({code}): {payload}")

    if groups is not None:
        _set_groups(user_id, groups)

    out = get_user_scim(user_id)
    if not out:
        raise RuntimeError("patch user: refetch failed")
    return out


def health() -> dict:
    try:
        get_token(force=True)
        idx = _group_index()
        return {
            "ok": True,
            "keycloak": KC_BASE,
            "realm": KC_REALM,
            "groups": sorted(idx.keys()),
        }
    except Exception as e:  # noqa: BLE001 — surface lab misconfig
        return {"ok": False, "keycloak": KC_BASE, "error": str(e)}
