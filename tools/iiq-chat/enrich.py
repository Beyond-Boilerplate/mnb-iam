"""Post-process MCP tool results so the model can write human-readable answers."""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable

CallFn = Callable[[str, dict[str, Any]], Any]

_MAX_RESOLVE = 40
_KEY_RE = re.compile(r"^(MNB\d{5}|[a-z][a-z0-9._-]{1,64})$", re.I)
# String fields that often hold bare identity keys.
_ID_STRING_FIELDS = frozenset(
    {
        "manager",
        "identity",
        "identityName",
        "identity_name",
        "owner",
        "requester",
        "certifiedBy",
        "target",
        "assignee",
        "recipient",
    }
)

# Tools that return people lists keyed by MNB / login only.
_REPORT_LIST_TOOLS = frozenset({"list_transitive_reports"})
_HIERARCHY_TOOLS = frozenset({"get_manager_hierarchy"})
_IDENTITY_DETAIL_TOOLS = frozenset({"get_identity", "get_identity_accounts", "search_identities", "search_profiles"})


def _display_from_identity(payload: Any) -> str | None:
    if not isinstance(payload, dict) or payload.get("ok") is False:
        return None
    data = payload.get("data", payload)
    if not isinstance(data, dict):
        return None
    dn = str(data.get("displayName") or "").strip()
    if dn:
        return dn
    name = data.get("name")
    if isinstance(name, dict):
        formatted = str(name.get("formatted") or "").strip()
        if formatted:
            return formatted
        given = str(name.get("givenName") or "").strip()
        family = str(name.get("familyName") or "").strip()
        joined = f"{given} {family}".strip()
        if joined:
            return joined
    return None


def _looks_like_key(value: str) -> bool:
    v = (value or "").strip()
    if not v or " " in v or "(" in v:
        return False
    return bool(_KEY_RE.match(v))


def _person_label(display: str | None, key: str) -> tuple[str, str]:
    key = (key or "").strip()
    dn = (display or "").strip()
    if dn and key and dn != key:
        return dn, f"{dn} ({key})"
    if dn:
        return dn, dn
    return key, key


def _resolve_person(call_fn: CallFn, key: str) -> tuple[str, str]:
    """Return (displayName, label) for an identity key."""
    key = (key or "").strip()
    if not key:
        return "", ""
    try:
        dn = _display_from_identity(call_fn("get_identity", {"id": key}))
    except Exception:  # noqa: BLE001
        dn = None
    return _person_label(dn, key)


def _resolve_many(call_fn: CallFn, keys: list[str]) -> dict[str, tuple[str, str]]:
    uniq = list(dict.fromkeys(k for k in keys if k))[:_MAX_RESOLVE]
    people: dict[str, tuple[str, str]] = {}
    if not uniq:
        return people
    workers = min(8, len(uniq))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_resolve_person, call_fn, k): k for k in uniq}
        for fut in as_completed(futures):
            k = futures[fut]
            try:
                people[k] = fut.result()
            except Exception:  # noqa: BLE001
                people[k] = (k, k)
    return people


def _label_identity_dict(item: dict[str, Any]) -> dict[str, Any]:
    out = dict(item)
    key = str(out.get("userName") or out.get("name") or out.get("id") or "").strip()
    dn = str(out.get("displayName") or "").strip()
    if not dn and isinstance(out.get("name"), dict):
        dn = str(out["name"].get("formatted") or "").strip()
    display, label = _person_label(dn or None, key)
    if display:
        out["displayName"] = display
    if label:
        out["label"] = label
    mgr = out.get("manager")
    if isinstance(mgr, dict):
        mdn = str(mgr.get("displayName") or "").strip()
        mid = str(mgr.get("value") or mgr.get("userName") or mgr.get("id") or "").strip()
        if mdn:
            out["managerLabel"] = f"{mdn} ({mid})" if mid and mid != mdn else mdn
        elif mid and _looks_like_key(mid):
            out.setdefault("managerKey", mid)
    # Compact card for free models (avoid drowning in SCIM).
    if display or key:
        out["tellerCard"] = {
            "label": label or display or key,
            "displayName": display or key,
            "userName": key or None,
            "active": out.get("active"),
            "manager": out.get("managerLabel")
            or (
                mgr.get("displayName")
                if isinstance(mgr, dict)
                else (mgr if isinstance(mgr, str) else None)
            ),
        }
    return out


def _enrich_reports_list(data: dict[str, Any], call_fn: CallFn) -> None:
    reports = data.get("reports")
    if not isinstance(reports, list) or not reports:
        return
    keys: list[str] = []
    for row in reports[:_MAX_RESOLVE]:
        if isinstance(row, dict):
            name = str(row.get("name") or row.get("id") or "").strip()
            if name:
                keys.append(name)
        elif isinstance(row, str) and row.strip():
            keys.append(row.strip())
    manager = str(data.get("manager") or "").strip()
    people = _resolve_many(call_fn, ([manager] if manager else []) + keys)
    if manager and manager in people:
        data["managerLabel"] = people[manager][1]
    enriched: list[dict[str, Any]] = []
    for row in reports:
        if isinstance(row, dict):
            item = dict(row)
            key = str(item.get("name") or item.get("id") or "").strip()
            dn, label = people.get(key, (key, key))
            item["displayName"] = dn
            item["label"] = label
            enriched.append(item)
        elif isinstance(row, str):
            key = row.strip()
            dn, label = people.get(key, (key, key))
            enriched.append({"name": key, "displayName": dn, "label": label})
    data["reports"] = enriched
    data["reportLabels"] = [r.get("label") or r.get("name") for r in enriched]
    data["peopleLabels"] = list(data["reportLabels"])


def _enrich_hierarchy(data: dict[str, Any]) -> None:
    for list_key, out_key in (
        ("directReports", "directReportLabels"),
        ("chain", "chainLabels"),
        ("reports", "reportLabels"),
    ):
        rows = data.get(list_key)
        if not isinstance(rows, list):
            continue
        labels: list[str] = []
        labeled_rows: list[Any] = []
        for row in rows:
            if isinstance(row, dict):
                item = _label_identity_dict(row)
                labeled_rows.append(item)
                if item.get("label"):
                    labels.append(str(item["label"]))
            else:
                labeled_rows.append(row)
        data[list_key] = labeled_rows
        if labels:
            data[out_key] = labels
    if data.get("directReportLabels"):
        data["peopleLabels"] = list(data["directReportLabels"])


def _enrich_identity_payload(tool: str, data: dict[str, Any]) -> None:
    if tool in ("search_identities", "search_profiles") and isinstance(data.get("items"), list):
        items = [_label_identity_dict(i) if isinstance(i, dict) else i for i in data["items"]]
        data["items"] = items
        data["peopleLabels"] = [
            str(i.get("label") or i.get("displayName") or i.get("userName"))
            for i in items
            if isinstance(i, dict)
        ]
        return
    # get_identity / get_identity_accounts
    if any(k in data for k in ("userName", "displayName", "id")):
        labeled = _label_identity_dict(data)
        data.clear()
        data.update(labeled)
    identity = data.get("identity")
    if isinstance(identity, dict):
        data["identity"] = _label_identity_dict(identity)
        if data["identity"].get("label"):
            data.setdefault("label", data["identity"]["label"])
            data.setdefault("peopleLabels", [data["identity"]["label"]])


def _collect_bare_keys(node: Any, found: list[str], depth: int = 0) -> None:
    if depth > 5:
        return
    if isinstance(node, dict):
        for k, v in node.items():
            if k in _ID_STRING_FIELDS and isinstance(v, str) and _looks_like_key(v):
                found.append(v.strip())
            elif k in _ID_STRING_FIELDS and isinstance(v, dict):
                # already named — skip
                pass
            else:
                _collect_bare_keys(v, found, depth + 1)
    elif isinstance(node, list):
        for item in node[:50]:
            _collect_bare_keys(item, found, depth + 1)


def _apply_labels(node: Any, people: dict[str, tuple[str, str]], depth: int = 0) -> Any:
    if depth > 5:
        return node
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            if k in _ID_STRING_FIELDS and isinstance(v, str) and v.strip() in people:
                dn, label = people[v.strip()]
                out[k] = v
                out[f"{k}Label"] = label
                out[f"{k}DisplayName"] = dn
            else:
                out[k] = _apply_labels(v, people, depth + 1)
        return out
    if isinstance(node, list):
        return [_apply_labels(i, people, depth + 1) for i in node[:80]]
    return node


def enrich_tool_result(tool: str, result: Any, call_fn: CallFn | None) -> Any:
    """Attach display names / labels onto identity-heavy tool results."""
    if not isinstance(result, dict) or result.get("ok") is False:
        return result
    data = result.get("data")
    if data is None:
        return result

    if tool in _REPORT_LIST_TOOLS and isinstance(data, dict) and call_fn:
        _enrich_reports_list(data, call_fn)
        return result

    if tool in _HIERARCHY_TOOLS and isinstance(data, dict):
        _enrich_hierarchy(data)
        return result

    if tool in _IDENTITY_DETAIL_TOOLS and isinstance(data, dict):
        _enrich_identity_payload(tool, data)
        # Still resolve bare manager keys if present as strings
        if call_fn:
            bare: list[str] = []
            _collect_bare_keys(data, bare)
            if bare:
                people = _resolve_many(call_fn, bare)
                result["data"] = _apply_labels(data, people)
        return result

    # Generic: label bare identity keys in common field names
    if call_fn and (isinstance(data, (dict, list))):
        bare: list[str] = []
        _collect_bare_keys(data, bare)
        if bare:
            people = _resolve_many(call_fn, bare)
            result["data"] = _apply_labels(data, people)
            labels = [people[k][1] for k in dict.fromkeys(bare) if k in people]
            if labels and isinstance(result["data"], dict):
                result["data"].setdefault("peopleLabels", labels[:20])
    return result
