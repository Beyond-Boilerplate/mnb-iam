"""Smart identity query / resolution helpers for SCIM Users.

Lab IdentityIQ cubes often store ``userName`` / ``displayName`` as ``first.last``
(e.g. ``anita.rao``) while operators and LLMs ask for ``Anita Rao``. These helpers
bridge that gap without intent hardcoding.

Workplace attributes (city, title, department, location codes, manager, …) live on
application account schemas (e.g. MNB-HR), not on SCIM User searchable fields.
Profile match helpers scan those account attributes client-side.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

# Tokens that appear in natural-language questions but are not profile values.
_PROFILE_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "of",
        "in",
        "at",
        "from",
        "to",
        "for",
        "with",
        "who",
        "what",
        "which",
        "where",
        "all",
        "any",
        "every",
        "list",
        "show",
        "find",
        "get",
        "give",
        "me",
        "please",
        "people",
        "person",
        "persons",
        "identities",
        "identity",
        "employees",
        "employee",
        "users",
        "user",
        "staff",
        "based",
        "located",
        "working",
        "works",
        "live",
        "lives",
        "are",
        "is",
        "by",
        "their",
        "those",
        "these",
        "that",
        "this",
    }
)


def scim_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').strip()


def to_dotted_username(value: str) -> str | None:
    """``Anita Rao`` → ``anita.rao``; already-dotted values returned lowercased."""
    text = value.strip()
    if not text:
        return None
    if " " in text:
        parts = [p for p in text.split() if p]
        if len(parts) >= 2:
            return ".".join(p.lower() for p in parts)
        return parts[0].lower() if parts else None
    return text.lower()


def build_identity_search_filter(query: str) -> str:
    """Build a SCIM filter that matches spaced names and first.last lab ids."""
    q = scim_escape(query)
    clauses = [
        f'userName co "{q}"',
        f'displayName co "{q}"',
        f'name.formatted co "{q}"',
        f'userName eq "{q}"',
        f'displayName eq "{q}"',
    ]
    parts = [p for p in q.split() if p]
    if len(parts) >= 2:
        dotted = ".".join(p.lower() for p in parts)
        first = parts[0]
        last = parts[-1]
        clauses.extend(
            [
                f'userName eq "{dotted}"',
                f'userName co "{dotted}"',
                f'displayName eq "{dotted}"',
                f'displayName co "{dotted}"',
                f'name.formatted co "{dotted}"',
                f'userName co "{first}"',
                f'userName co "{last}"',
                f'displayName co "{first}"',
                f'displayName co "{last}"',
            ]
        )
    elif "." in q:
        # also try spaced form from dotted
        spaced = " ".join(p.capitalize() for p in q.split("."))
        clauses.extend(
            [
                f'displayName co "{spaced}"',
                f'name.formatted co "{spaced}"',
            ]
        )
    return " or ".join(clauses)


def prefer_identity(
    candidates: Sequence[Mapping[str, Any]],
    hint: str,
) -> Mapping[str, Any] | None:
    """Pick the best SCIM User from a candidate list for a human/LLM hint."""
    if not candidates:
        return None
    hint_l = hint.strip().lower()
    dotted = to_dotted_username(hint) or hint_l

    def uname(item: Mapping[str, Any]) -> str:
        return str(item.get("userName") or "").strip()

    def dname(item: Mapping[str, Any]) -> str:
        return str(item.get("displayName") or "").strip()

    # Exact userName match on dotted lab id
    for item in candidates:
        if uname(item).lower() == dotted:
            return item
    # Exact userName / displayName on raw hint
    for item in candidates:
        if uname(item).lower() == hint_l or dname(item).lower() == hint_l:
            # Prefer dotted usernames when hint was a display name
            if " " in hint and " " in uname(item) and "." not in uname(item):
                continue
            return item
    # Prefer first.last style when hint looked like a display name
    if " " in hint:
        for item in candidates:
            u = uname(item)
            if "." in u and " " not in u:
                return item
    return candidates[0]


def extract_account_profile(acct: Mapping[str, Any]) -> dict[str, Any]:
    """Pull HR/IT profile fields out of SCIM account application schemas."""
    profile: dict[str, Any] = {
        "application": None,
        "title": None,
        "jobTitle": None,
        "corporateTitle": None,
        "department": None,
        "departmentName": None,
        "email": None,
        "fullName": None,
        "displayName": None,
        "location": None,
        "manager": None,
        "employeeId": None,
        "status": None,
    }
    app = acct.get("application")
    if isinstance(app, Mapping):
        profile["application"] = app.get("displayName") or app.get("name") or app.get("value")
    elif app:
        profile["application"] = str(app)

    for key, val in acct.items():
        if not isinstance(val, Mapping):
            continue
        if "Application:Schema:" not in str(key):
            continue
        mapping = {
            "title": ("title",),
            "jobTitle": ("jobTitle",),
            "corporateTitle": ("corporateTitle",),
            "department": ("department", "departmentName"),
            "departmentName": ("departmentName",),
            "email": ("email", "mail"),
            "fullName": ("fullName",),
            "displayName": ("displayName",),
            "location": ("city", "rfLocationName", "location"),
            "manager": ("manager",),
            "employeeId": ("employeeId", "userId", "employeeNumber"),
            "status": ("status", "accountStatus", "statusFlag"),
        }
        for out_key, src_keys in mapping.items():
            if profile.get(out_key):
                continue
            for sk in src_keys:
                if val.get(sk) not in (None, ""):
                    profile[out_key] = val.get(sk)
                    break

    # Drop empties
    return {k: v for k, v in profile.items() if v not in (None, "", [])}


def coalesce_profiles(accounts: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Merge profile hints across accounts (first non-empty wins per field)."""
    merged: dict[str, Any] = {}
    apps: list[dict[str, Any]] = []
    for acct in accounts:
        prof = extract_account_profile(acct)
        if not prof:
            continue
        apps.append(prof)
        for k, v in prof.items():
            if k == "application":
                continue
            if k not in merged and v not in (None, ""):
                merged[k] = v
    if apps:
        merged["accounts"] = apps
    # Convenience: best title
    for key in ("title", "jobTitle", "corporateTitle"):
        if merged.get(key):
            merged["resolvedTitle"] = merged[key]
            break
    return merged


def identity_key(*, id: str | None = None, name: str | None = None) -> str:
    """Accept either ``id`` or ``name`` (LLM alias) as the lookup key."""
    key = (id or name or "").strip()
    if not key:
        raise ValueError("id or name is required")
    return key


def _collect_strings(value: Any, out: list[str]) -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        out.append(str(value))
        return
    if isinstance(value, str):
        text = value.strip()
        if text:
            out.append(text)
        return
    if isinstance(value, Mapping):
        for v in value.values():
            _collect_strings(v, out)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for v in value:
            _collect_strings(v, out)


def flatten_account_text(acct: Mapping[str, Any]) -> str:
    """Concatenate searchable string fields from a SCIM Account resource."""
    parts: list[str] = []
    _collect_strings(acct, parts)
    return " ".join(parts)


def profile_query_tokens(query: str) -> list[str]:
    """Meaningful tokens from a free-text profile / location / title question."""
    raw = re.findall(r"[a-z0-9][a-z0-9._-]*", (query or "").lower())
    return [t for t in raw if t not in _PROFILE_STOPWORDS and len(t) >= 2]


def account_matches_profile_query(acct: Mapping[str, Any], query: str) -> bool:
    """True if the account's attribute blob matches the free-text query."""
    q = (query or "").strip()
    if not q:
        return False
    blob = flatten_account_text(acct).lower()
    if not blob:
        return False
    q_l = q.lower()
    if q_l in blob:
        return True
    tokens = profile_query_tokens(q)
    if not tokens:
        return False
    return all(tok in blob for tok in tokens)


def identity_from_account(acct: Mapping[str, Any]) -> dict[str, Any] | None:
    """Build a trimmed identity-like dict (with profileHints) from an Account."""
    ident = acct.get("identity")
    if not isinstance(ident, Mapping):
        return None
    iid = ident.get("value") or ident.get("id")
    uname = ident.get("userName") or ident.get("displayName")
    if not iid and not uname:
        return None
    profile = extract_account_profile(acct)
    # Prefer richer display from HR schema when cube displayName is first.last
    display = (
        profile.get("fullName")
        or profile.get("displayName")
        or ident.get("displayName")
        or uname
    )
    item: dict[str, Any] = {
        "id": iid,
        "userName": uname,
        "displayName": display,
    }
    if profile:
        # Attach resolvedTitle convenience like coalesce_profiles
        for key in ("title", "jobTitle", "corporateTitle"):
            if profile.get(key):
                profile = {**profile, "resolvedTitle": profile[key]}
                break
        item["profileHints"] = profile
    return item


def dedupe_identities(items: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Dedupe by id/userName keeping first occurrence."""
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for raw in items:
        item = dict(raw)
        key = str(item.get("id") or item.get("userName") or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out
