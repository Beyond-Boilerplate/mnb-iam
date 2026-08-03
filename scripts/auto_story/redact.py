"""Secret redaction for ledger / evidence (mirrors iiq-delivery/redact_json)."""

from __future__ import annotations

from typing import Any

SECRET_KEYS = {
    "password",
    "passwd",
    "secret",
    "token",
    "authorization",
    "api_key",
    "apikey",
    "private_key",
    "client_secret",
    "refresh_token",
    "access_token",
}


def redact(obj: Any, *, depth: int = 0) -> Any:
    if depth > 40:
        return "***"
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            lk = str(k).lower().replace("-", "_")
            if any(s in lk for s in SECRET_KEYS):
                out[k] = "***"
            elif lk in {"emails", "phone_numbers", "telephone_number", "mobilephone"} and isinstance(
                v, list
            ):
                out[k] = ["***"] if v else []
            else:
                out[k] = redact(v, depth=depth + 1)
        return out
    if isinstance(obj, list):
        return [redact(x, depth=depth + 1) for x in obj[:50]]
    if isinstance(obj, str) and len(obj) > 8000:
        return obj[:8000] + "…[truncated]"
    return obj
