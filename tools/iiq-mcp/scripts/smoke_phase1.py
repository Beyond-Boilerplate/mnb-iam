"""Smoke Phase 1 reads against a live IIQ lab (skipped if unreachable)."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Allow running without install: python scripts/smoke_phase1.py
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import httpx

from iiq_mcp.client.http import IiqHttpClient
from iiq_mcp.config import Settings


async def _reachable(base: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.get(f"{base.rstrip('/')}/login.jsf")
            return r.status_code < 500
    except Exception:
        return False


async def main() -> int:
    cfg = Settings()
    if not await _reachable(cfg.iiq_base_url):
        print(f"SKIP: IIQ not reachable at {cfg.iiq_base_url}")
        return 0

    client = IiqHttpClient(cfg)
    try:
        checks = [
            ("SCIM Users", lambda: client.scim_get("/Users", params={"count": 1})),
            ("SCIM Accounts", lambda: client.scim_get("/Accounts", params={"count": 1})),
            ("SCIM TaskResults", lambda: client.scim_get("/TaskResults", params={"count": 1})),
            (
                "SCIM PolicyViolations",
                lambda: client.scim_get("/PolicyViolations", params={"count": 1}),
            ),
            ("SCIM Applications", lambda: client.scim_get("/Applications", params={"count": 1})),
            ("Plugin ping", lambda: client.plugin_get("/mnbToolkit/ping")),
        ]
        failures = 0
        for name, fn in checks:
            try:
                body = await fn()
                print(f"OK  {name}: {type(body).__name__}")
            except Exception as exc:  # noqa: BLE001
                msg = str(exc).lower()
                soft = (
                    "ping" in name.lower()
                    or "unauthorized" in msg
                    or "does not have access" in msg
                    or "401" in msg
                    or "403" in msg
                )
                level = "WARN" if soft else "FAIL"
                print(f"{level} {name}: {exc}")
                if level == "FAIL":
                    failures += 1
        if failures:
            print(
                "Hint: set IIQ_USER/IIQ_PASSWORD for an identity with SCIM rights "
                "(e.g. spadmin or mnb.api.lab)."
            )
        return 1 if failures else 0
    finally:
        await client.aclose()


if __name__ == "__main__":
    # Optional env: IIQ_PASSWORD (default empty)
    raise SystemExit(asyncio.run(main()))
