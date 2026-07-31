"""Independent write-audit trail (JSONL outside IIQ)."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class WriteAuditLog:
    """Append-only JSONL audit of MCP write / high-risk tool attempts."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()

    def record(
        self,
        *,
        tool: str,
        parameters: dict[str, Any] | None = None,
        result: Any = None,
        error: Any = None,
        justification: str | None = None,
        caller: str | None = None,
        risk: str | None = None,
    ) -> None:
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "tool": tool,
            "risk": risk,
            "caller": caller,
            "justification": justification,
            "parameters": _redact(parameters or {}),
            "result": _truncate(result),
            "error": _truncate(error),
        }
        line = json.dumps(entry, default=str) + "\n"
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(line)


_SECRET_KEYS = {
    "password",
    "new_password",
    "newPassword",
    "secret",
    "token",
    "api_key",
    "apiKey",
}


def _redact(params: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in params.items():
        if k.lower() in {s.lower() for s in _SECRET_KEYS} or "password" in k.lower():
            out[k] = "***REDACTED***"
        else:
            out[k] = _truncate(v)
    return out


def _truncate(value: Any, limit: int = 2000) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        text = json.dumps(value, default=str)
        if len(text) > limit:
            return text[:limit] + "…"
        return value
    text = str(value)
    return text if len(text) <= limit else text[:limit] + "…"
