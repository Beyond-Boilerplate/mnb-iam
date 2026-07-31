"""Normalize LLM-produced MCP arguments before tools/call."""

from __future__ import annotations

from typing import Any, Callable

# Tools whose primary identity key is ``id`` (SCIM id or userName).
IDENTITY_ID_TOOLS = {
    "get_identity",
    "get_identity_access",
    "get_identity_accounts",
    "get_identity_history",
    "get_identity_risk_score",
    "get_identity_risk_breakdown",
    "get_manager_hierarchy",
    "disable_identity",
    "enable_identity",
}

IDENTITY_ID_OR_IDENTITY_ID_TOOLS = {
    "get_identity_capabilities",
}

IDENTITY_NAME_TOOLS = {
    "unlock_iiq_identity",
}

_ID_ALIASES = ("name", "userName", "username", "identity", "displayName", "user", "identity_name")


def _pick_identity_hint(args: dict[str, Any]) -> str | None:
    for key in ("id", "identity_id", "identity_name", *_ID_ALIASES):
        val = args.get(key)
        if val:
            return str(val).strip()
    return None


def _looks_like_display_name(value: str) -> bool:
    return " " in value.strip()


def resolve_identity_username(
    search_fn: Callable[[str], Any],
    hint: str,
) -> str:
    """Resolve a display name / partial query to a userName via search_identities."""
    hint_l = hint.lower().strip()
    dotted = hint_l.replace(" ", ".")

    def _items(result: Any) -> list[dict[str, Any]]:
        found: list[dict[str, Any]] = []
        if not isinstance(result, dict):
            return found
        data = result.get("data")
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            found = [i for i in data["items"] if isinstance(i, dict)]
        elif isinstance(data, list):
            found = [i for i in data if isinstance(i, dict)]
        elif isinstance(result.get("items"), list):
            found = [i for i in result["items"] if isinstance(i, dict)]
        return found

    def _prefer(items: list[dict[str, Any]]) -> str | None:
        if not items:
            return None
        # Exact userName / displayName
        for item in items:
            un = str(item.get("userName") or "").strip()
            dn = str(item.get("displayName") or "").strip().lower()
            if un.lower() == dotted or un.lower() == hint_l or dn == hint_l:
                # Prefer dotted lab ids over space-containing userNames
                if un.lower() == dotted:
                    return un
        for item in items:
            un = str(item.get("userName") or "").strip()
            if un.lower() == dotted:
                return un
        # Display-name query: prefer first.last style userNames
        if " " in hint:
            for item in items:
                un = str(item.get("userName") or "").strip()
                if "." in un and " " not in un:
                    return un
        first = items[0]
        return str(first.get("userName") or first.get("id") or hint)

    items = _items(search_fn(hint))
    chosen = _prefer(items)
    if chosen and (chosen.lower() == dotted or (" " not in chosen and "." in chosen)):
        return chosen

    # Secondary search: lab convention first.last
    if " " in hint and dotted != hint_l:
        items2 = _items(search_fn(dotted))
        chosen2 = _prefer(items2)
        if chosen2:
            return chosen2

    if chosen:
        return chosen
    return dotted if " " in hint else hint


def normalize_tool_args(
    tool: str,
    args: dict[str, Any] | None,
    *,
    search_fn: Callable[[str], Any] | None = None,
) -> dict[str, Any]:
    """Fix common free-model arg mistakes before MCP tools/call."""
    out = dict(args or {})
    hint = _pick_identity_hint(out)

    if tool in IDENTITY_ID_TOOLS or tool in IDENTITY_ID_OR_IDENTITY_ID_TOOLS:
        for key in list(out.keys()):
            if key in _ID_ALIASES or key in ("identity_id", "identity_name"):
                out.pop(key, None)
        if hint:
            if search_fn and _looks_like_display_name(hint):
                hint = resolve_identity_username(search_fn, hint)
            out["id"] = hint

    if tool in IDENTITY_NAME_TOOLS:
        for key in list(out.keys()):
            if key in _ID_ALIASES or key in ("id", "identity_id"):
                out.pop(key, None)
        if hint:
            if search_fn and _looks_like_display_name(hint):
                hint = resolve_identity_username(search_fn, hint)
            out["identity_name"] = hint

    if tool == "get_requestable_items":
        ident = out.get("identity") or hint
        for key in ("id", "name", "userName", "username", "displayName", "identity_id"):
            out.pop(key, None)
        if ident:
            if search_fn and _looks_like_display_name(str(ident)):
                ident = resolve_identity_username(search_fn, str(ident))
            out["identity"] = ident

    if tool == "search_identities":
        q = out.get("query")
        if isinstance(q, str) and " " in q.strip():
            # Keep original query (MCP now expands it); also stash dotted form if model used name=
            out["query"] = q.strip()
        # Models sometimes put the person in "name" instead of query
        if not out.get("query"):
            alt = out.get("name") or out.get("displayName") or out.get("userName")
            if alt:
                out["query"] = str(alt).strip()
        for key in ("name", "displayName", "userName", "id"):
            if key != "query":
                out.pop(key, None)

    return out
