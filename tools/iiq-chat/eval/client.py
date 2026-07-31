"""HTTP client for Teller blackbox eval."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


class TellerClient:
    def __init__(self, base_url: str | None = None, timeout: float = 180.0) -> None:
        self.base_url = (base_url or os.environ.get("TELLER_URL") or "http://127.0.0.1:4180").rstrip(
            "/"
        )
        self.timeout = timeout

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:800]
            try:
                parsed = json.loads(detail)
                if isinstance(parsed, dict):
                    parsed.setdefault("ok", False)
                    parsed.setdefault("http_status", exc.code)
                    return parsed
            except json.JSONDecodeError:
                pass
            return {"ok": False, "error": f"HTTP {exc.code}: {detail}", "http_status": exc.code}
        except urllib.error.URLError as exc:
            return {"ok": False, "error": f"Teller unreachable at {self.base_url}: {exc}"}

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/api/health")

    def config(self) -> dict[str, Any]:
        return self._request("GET", "/api/config")

    def chat(self, message: str, history: list[dict[str, str]] | None = None) -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/chat",
            {"message": message, "history": history or []},
        )

    def refresh_tools(self) -> dict[str, Any]:
        return self._request("POST", "/api/tools/refresh", {})
