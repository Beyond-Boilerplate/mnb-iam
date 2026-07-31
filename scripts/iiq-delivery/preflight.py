#!/usr/bin/env python3
"""Preflight checks for Meridian lab (MCP / IIQ health)."""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import GOTCHAS, IIQ_BASE, MCP_URL, MEMORY_ROOT, REPO_ROOT  # noqa: E402


def _http_ok(url: str, timeout: float = 5.0) -> tuple[bool, str]:
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status < 500, f"HTTP {resp.status}"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def main() -> int:
    import argparse

    p = argparse.ArgumentParser(description="IIQ / MCP preflight")
    p.add_argument("--json", action="store_true")
    p.add_argument("--require-mcp", action="store_true")
    p.add_argument("--require-iiq", action="store_true")
    args = p.parse_args()

    mcp_url = os.environ.get("IIQ_MCP_URL", MCP_URL)
    health = mcp_url.replace("/mcp", "/healthz") if mcp_url.endswith("/mcp") else f"{mcp_url}/healthz"
    mcp_ok, mcp_detail = _http_ok(health)
    iiq_ok, iiq_detail = _http_ok(f"{os.environ.get('IIQ_BASE_URL', IIQ_BASE).rstrip('/')}/login.jsf")

    checks = {
        "repo_root": str(REPO_ROOT),
        "memory_root_exists": MEMORY_ROOT.is_dir(),
        "gotchas_exist": GOTCHAS.is_file(),
        "mcp": {"ok": mcp_ok, "url": health, "detail": mcp_detail},
        "iiq": {"ok": iiq_ok, "url": IIQ_BASE, "detail": iiq_detail},
    }

    ready = True
    if args.require_mcp:
        ready = ready and mcp_ok
    if args.require_iiq:
        ready = ready and iiq_ok
    if not args.require_mcp and not args.require_iiq:
        ready = mcp_ok or iiq_ok or MEMORY_ROOT.is_dir()

    out = {"ok": ready, "checks": checks}
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        print(f"PREFLIGHT: {'PASS' if ready else 'FAIL'}")
        print(f"  MCP healthz: {'OK' if mcp_ok else 'DOWN'} ({mcp_detail})")
        print(f"  IIQ login:   {'OK' if iiq_ok else 'DOWN'} ({iiq_detail})")
        print(f"  memory:      {'OK' if checks['memory_root_exists'] else 'MISSING'}")
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
