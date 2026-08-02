"""Normalize LLM-produced MCP arguments before tools/call."""

from __future__ import annotations

import re
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

# Tools that take a manager= identity key (not "Display Name (key)" from @mentions).
MANAGER_KEY_TOOLS = {
    "list_transitive_reports",
}

_ID_ALIASES = ("name", "userName", "username", "identity", "displayName", "user", "identity_name")

# Teller @mention insert form: "Christopher Hayes (MNB00002)" or "Anita Rao (anita.rao)"
_MENTION_RE = re.compile(r"^(?P<label>.+?)\s*\((?P<key>[^)]+)\)\s*$")
_KEY_RE = re.compile(
    r"^(?:"
    r"MNB\d+"  # employee number
    r"|[a-z][a-z0-9._-]*\.[a-z0-9._-]+"  # dotted login
    r"|[a-f0-9]{16,}"  # IIQ/SCIM-ish hex id
    r")$",
    re.IGNORECASE,
)


def unwrap_identity_mention(value: str) -> str:
    """Extract bare identity key from Teller mention text.

    ``Christopher Hayes (MNB00002)`` → ``MNB00002``
    ``anita.rao`` → ``anita.rao`` (unchanged)
    """
    text = (value or "").strip()
    if not text:
        return text
    m = _MENTION_RE.match(text)
    if not m:
        return text
    key = m.group("key").strip()
    if _KEY_RE.match(key):
        return key
    return text


def _pick_identity_hint(args: dict[str, Any]) -> str | None:
    for key in ("id", "identity_id", "identity_name", "manager", *_ID_ALIASES):
        val = args.get(key)
        if val:
            return unwrap_identity_mention(str(val).strip())
    return None


def _looks_like_display_name(value: str) -> bool:
    text = unwrap_identity_mention(value.strip())
    # Bare keys are not display names even if original had spaces outside parens
    if _KEY_RE.match(text):
        return False
    return " " in text


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

    # Unwrap @mention forms on common identity-bearing fields first
    for key in ("id", "identity_id", "identity_name", "identity", "manager", *_ID_ALIASES):
        if key in out and isinstance(out[key], str):
            out[key] = unwrap_identity_mention(out[key])

    hint = _pick_identity_hint(out)

    if tool in IDENTITY_ID_TOOLS or tool in IDENTITY_ID_OR_IDENTITY_ID_TOOLS:
        for key in list(out.keys()):
            if key in _ID_ALIASES or key in ("identity_id", "identity_name", "manager"):
                out.pop(key, None)
        if hint:
            if search_fn and _looks_like_display_name(hint):
                hint = resolve_identity_username(search_fn, hint)
            out["id"] = hint

    if tool in IDENTITY_NAME_TOOLS:
        for key in list(out.keys()):
            if key in _ID_ALIASES or key in ("id", "identity_id", "manager"):
                out.pop(key, None)
        if hint:
            if search_fn and _looks_like_display_name(hint):
                hint = resolve_identity_username(search_fn, hint)
            out["identity_name"] = hint

    if tool in MANAGER_KEY_TOOLS:
        manager = out.get("manager") or hint
        # Drop alias clutter; keep manager (+ optional flags the tool accepts)
        for key in list(out.keys()):
            if key in _ID_ALIASES or key in ("id", "identity_id", "identity_name", "identity"):
                out.pop(key, None)
        if manager:
            manager = unwrap_identity_mention(str(manager))
            if search_fn and _looks_like_display_name(manager):
                manager = resolve_identity_username(search_fn, manager)
            out["manager"] = manager

    if tool == "get_requestable_items":
        ident = out.get("identity") or hint
        for key in ("id", "name", "userName", "username", "displayName", "identity_id"):
            out.pop(key, None)
        if ident:
            ident = unwrap_identity_mention(str(ident))
            if search_fn and _looks_like_display_name(str(ident)):
                ident = resolve_identity_username(search_fn, str(ident))
            out["identity"] = ident

    if tool == "search_identities":
        q = out.get("query")
        if isinstance(q, str):
            # If the model pasted a mention into query, search the key (more precise)
            unwrapped = unwrap_identity_mention(q.strip())
            out["query"] = unwrapped if unwrapped != q.strip() or _KEY_RE.match(unwrapped) else q.strip()
        # Models sometimes put the person in "name" instead of query
        if not out.get("query"):
            alt = out.get("name") or out.get("displayName") or out.get("userName")
            if alt:
                out["query"] = unwrap_identity_mention(str(alt).strip())
        for key in ("name", "displayName", "userName", "id"):
            if key != "query":
                out.pop(key, None)

    return out
