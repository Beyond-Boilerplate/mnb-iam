"""Build structured triage cards from agent tool steps (SoD, identity, etc.)."""

from __future__ import annotations

from typing import Any


def _data(result: Any) -> Any:
    if isinstance(result, dict):
        if "data" in result and result.get("ok") is not False:
            return result.get("data")
        return result
    return result


def _failed(result: Any) -> bool:
    return isinstance(result, dict) and result.get("ok") is False


def _identity_card(tool: str, result: Any) -> dict[str, Any] | None:
    data = _data(result)
    if not isinstance(data, dict):
        return None
    # Prefer tellerCard enrichment when present
    card = data.get("tellerCard")
    if isinstance(card, dict) and (card.get("displayName") or card.get("userName")):
        return {
            "type": "identity",
            "title": str(card.get("displayName") or card.get("userName")),
            "fields": {
                k: card[k]
                for k in (
                    "displayName",
                    "userName",
                    "employeeId",
                    "title",
                    "department",
                    "manager",
                    "location",
                    "active",
                    "locked",
                )
                if card.get(k) is not None
            },
            "source": tool,
        }

    identity = data.get("identity") if isinstance(data.get("identity"), dict) else data
    if not isinstance(identity, dict):
        return None
    display = (
        identity.get("displayName")
        or identity.get("name")
        or identity.get("userName")
        or data.get("displayName")
    )
    user = identity.get("userName") or data.get("userName")
    if not display and not user:
        return None
    hints = data.get("profileHints") if isinstance(data.get("profileHints"), dict) else {}
    fields: dict[str, Any] = {}
    for key, val in (
        ("displayName", display),
        ("userName", user),
        ("employeeId", identity.get("userId") or hints.get("employeeId")),
        ("title", hints.get("resolvedTitle") or hints.get("title") or identity.get("title")),
        ("department", hints.get("departmentName") or identity.get("department")),
        ("manager", data.get("managerLabel") or hints.get("manager") or identity.get("manager")),
        ("location", hints.get("location") or identity.get("location")),
        ("active", identity.get("active")),
        ("locked", identity.get("locked")),
    ):
        if val is not None and val != "":
            fields[key] = val
    return {
        "type": "identity",
        "title": str(display or user),
        "fields": fields,
        "source": tool,
    }


def _sod_card(tool: str, result: Any) -> dict[str, Any] | None:
    data = _data(result)
    count: int | None = None
    items: list[Any] = []
    if isinstance(data, dict):
        if data.get("count") is not None and not isinstance(data.get("count"), bool):
            try:
                count = int(data["count"])
            except (TypeError, ValueError):
                count = None
        items = data.get("items") or data.get("violations") or data.get("conflicts") or []
        if count is None and isinstance(items, list):
            count = len(items)
        if count is None and data.get("totalResults") is not None:
            try:
                count = int(data["totalResults"])
            except (TypeError, ValueError):
                count = None
    elif isinstance(data, list):
        items = data
        count = len(data)
    elif isinstance(data, (int, float)):
        count = int(data)

    if count is None and not items:
        return None

    top: list[str] = []
    for row in (items or [])[:5]:
        if isinstance(row, dict):
            label = (
                row.get("label")
                or row.get("displayName")
                or row.get("identity")
                or row.get("policyName")
                or row.get("name")
            )
            detail = row.get("conflict") or row.get("entitlements") or row.get("description")
            if label and detail:
                top.append(f"{label}: {detail}")
            elif label:
                top.append(str(label))
        elif row is not None:
            top.append(str(row)[:120])

    return {
        "type": "sod",
        "title": "Open SoD violations",
        "fields": {"count": count if count is not None else len(top), "top": top},
        "source": tool,
    }


def _certs_card(tool: str, result: Any) -> dict[str, Any] | None:
    data = _data(result)
    if not isinstance(data, dict) and not isinstance(data, list):
        return None
    items = data.get("items") if isinstance(data, dict) else data
    if not isinstance(items, list):
        items = []
    total = None
    if isinstance(data, dict):
        total = data.get("totalResults") or data.get("count") or len(items)
    else:
        total = len(items)
    names = []
    for row in items[:6]:
        if isinstance(row, dict):
            names.append(str(row.get("name") or row.get("displayName") or row.get("id") or ""))
    names = [n for n in names if n]
    if total is None and not names:
        return None
    return {
        "type": "certs",
        "title": "Certifications",
        "fields": {"count": total, "items": names},
        "source": tool,
    }


def build_cards(steps: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Derive UI triage cards from successful tool steps (deduped by type)."""
    cards: list[dict[str, Any]] = []
    seen: set[str] = set()
    for step in steps or []:
        tool = str(step.get("tool") or "")
        result = step.get("result")
        if not tool or _failed(result):
            continue
        card: dict[str, Any] | None = None
        low = tool.lower()
        if "sod" in low or "policy_violation" in low:
            card = _sod_card(tool, result)
        elif any(x in low for x in ("get_identity", "search_identities", "search_profiles", "identity360")):
            card = _identity_card(tool, result)
        elif "certif" in low:
            card = _certs_card(tool, result)
        if not card:
            continue
        key = f"{card['type']}:{card.get('title')}"
        if key in seen:
            continue
        seen.add(key)
        cards.append(card)
    return cards[:6]


def citation_footer(steps: list[dict[str, Any]] | None) -> str:
    """Markdown footer listing tools that returned usable data."""
    sources: list[str] = []
    for step in steps or []:
        tool = str(step.get("tool") or "").strip()
        if not tool:
            continue
        result = step.get("result")
        if _failed(result):
            continue
        if tool not in sources:
            sources.append(tool)
    if not sources:
        return ""
    return "\n\n---\n**Sources:** " + ", ".join(f"`{s}`" for s in sources)
