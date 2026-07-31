"""Response shaping, field trimming, and pagination helpers."""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from iiq_mcp.config import Settings, get_settings


def clamp_page(
    start: int | None = None,
    count: int | None = None,
    *,
    settings: Settings | None = None,
) -> tuple[int, int]:
    """Normalize list pagination to ``(start, count)`` with server-side caps."""
    cfg = settings or get_settings()
    s = 0 if start is None else max(0, int(start))
    default = cfg.iiq_mcp_default_page_size
    maximum = cfg.iiq_mcp_max_page_size
    c = default if count is None else int(count)
    c = max(1, min(c, maximum))
    return s, c


def scim_page_params(
    start: int | None = None,
    count: int | None = None,
    *,
    settings: Settings | None = None,
) -> dict[str, int]:
    """SCIM uses 1-based ``startIndex``."""
    s, c = clamp_page(start, count, settings=settings)
    return {"startIndex": s + 1, "count": c}


def pick(obj: Mapping[str, Any] | None, keys: Sequence[str]) -> dict[str, Any]:
    """Shallow-pick keys from a mapping (missing keys omitted)."""
    if not obj:
        return {}
    return {k: obj[k] for k in keys if k in obj}


def trim_identity(user: Mapping[str, Any], *, raw: bool = False) -> dict[str, Any]:
    if raw:
        return dict(user)
    keys = (
        "id",
        "userName",
        "displayName",
        "active",
        "emails",
        "name",
        "title",
        "userType",
        "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
        "urn:ietf:params:scim:schemas:sailpoint:1.0:User",
    )
    out = pick(user, keys)
    # Flatten common SailPoint-ish attrs when present
    sail = user.get("urn:ietf:params:scim:schemas:sailpoint:1.0:User")
    if isinstance(sail, Mapping):
        for k in ("department", "location", "manager", "riskScore", "isManager"):
            if k in sail and k not in out:
                out[k] = sail[k]
    ent = user.get("urn:ietf:params:scim:schemas:extension:enterprise:2.0:User")
    if isinstance(ent, Mapping) and "manager" in ent and "manager" not in out:
        out["manager"] = ent["manager"]
    return out


def trim_account(acct: Mapping[str, Any], *, raw: bool = False) -> dict[str, Any]:
    if raw:
        return dict(acct)
    return pick(
        acct,
        (
            "id",
            "displayName",
            "active",
            "userName",
            "application",
            "nativeIdentity",
            "urn:ietf:params:scim:schemas:sailpoint:1.0:Application:Account",
        ),
    )


def _sanitize_features(features: Any) -> list[str] | None:
    """Normalize SCIM Application.features; drop Java ``[Ljava.lang.String;@…`` junk."""
    if features is None:
        return None
    if isinstance(features, str):
        features = [features]
    if not isinstance(features, (list, tuple)):
        return None
    cleaned: list[str] = []
    for item in features:
        if item is None:
            continue
        s = str(item).strip()
        if not s:
            continue
        # IIQ SCIM sometimes emits String[].toString() instead of feature tokens
        if s.startswith("[L") and "@" in s:
            continue
        cleaned.append(s)
    return cleaned


def trim_application(app: Mapping[str, Any], *, raw: bool = False) -> dict[str, Any]:
    if raw:
        return dict(app)
    out = pick(app, ("id", "name", "displayName", "description", "type", "features", "active"))
    if "features" in out:
        sanitized = _sanitize_features(out.get("features"))
        if sanitized is None:
            out.pop("features", None)
        else:
            out["features"] = sanitized
    # Prefer explicit featuresString when SCIM features are empty/broken
    fs = app.get("featuresString")
    if isinstance(fs, str) and fs.strip() and not out.get("features"):
        out["features"] = [p.strip() for p in fs.split(",") if p.strip()]
        out["featuresString"] = fs
    return out


def trim_task_result(tr: Mapping[str, Any], *, raw: bool = False) -> dict[str, Any]:
    if raw:
        return dict(tr)
    return pick(
        tr,
        (
            "id",
            "name",
            "type",
            "completionStatus",
            "launcher",
            "created",
            "modified",
            "completed",
            "messages",
            "attributes",
            "progress",
            "percentComplete",
        ),
    )


def trim_policy_violation(v: Mapping[str, Any], *, raw: bool = False) -> dict[str, Any]:
    if raw:
        return dict(v)
    return pick(
        v,
        (
            "id",
            "name",
            "displayName",
            "description",
            "policyName",
            "status",
            "identity",
            "constraintName",
            "leftBundles",
            "rightBundles",
            "mitigator",
            "meta",
        ),
    )


def trim_generic(obj: Any, *, keys: Sequence[str] | None = None, raw: bool = False) -> Any:
    if raw or not isinstance(obj, Mapping):
        return obj if not isinstance(obj, Mapping) else dict(obj)
    if keys:
        return pick(obj, keys)
    # Conservative default: drop huge nested blobs often seen in IIQ REST
    drop = {"plan", "provisioningPlan", "xml", "source", "serializedForm", "completer"}
    return {k: v for k, v in obj.items() if k not in drop}


def list_envelope(
    items: Iterable[Any],
    *,
    start: int,
    count: int,
    total: int | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    materialised = list(items)
    return {
        "start": start,
        "count": count,
        "returned": len(materialised),
        "totalResults": total,
        "raw": raw,
        "items": materialised,
    }


def scim_resources(payload: Mapping[str, Any] | None) -> list[Any]:
    if not payload:
        return []
    return list(payload.get("Resources") or payload.get("resources") or [])


def scim_total(payload: Mapping[str, Any] | None) -> int | None:
    if not payload:
        return None
    for key in ("totalResults", "total"):
        if key in payload:
            try:
                return int(payload[key])
            except (TypeError, ValueError):
                return None
    return None
