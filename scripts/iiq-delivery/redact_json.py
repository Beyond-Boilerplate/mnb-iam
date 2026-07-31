#!/usr/bin/env python3
"""Redact secrets / heavy PII from JSON before writing evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
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
            elif lk in {"emails", "phone_numbers", "telephone_number", "mobilephone"} and isinstance(v, list):
                out[k] = ["***"] if v else []
            else:
                out[k] = redact(v, depth=depth + 1)
        return out
    if isinstance(obj, list):
        # Cap huge lists in evidence
        capped = obj[:50]
        return [redact(x, depth=depth + 1) for x in capped]
    if isinstance(obj, str) and len(obj) > 8000:
        return obj[:8000] + "…[truncated]"
    return obj


def main() -> int:
    p = argparse.ArgumentParser(description="Redact JSON for evidence files")
    p.add_argument("input", nargs="?", help="Input JSON file (default stdin)")
    p.add_argument("-o", "--output", help="Output path (default stdout)")
    args = p.parse_args()

    if args.input:
        raw = Path(args.input).read_text(encoding="utf-8")
    else:
        raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1

    cleaned = redact(data)
    text = json.dumps(cleaned, indent=2) + "\n"
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(text, encoding="utf-8")
        print(json.dumps({"ok": True, "output": args.output}))
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
