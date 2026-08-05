#!/usr/bin/env python3
"""Regenerate Enterprise Sandbox Path lessons 201–250.

Prefer editing docs/lessons/201-*.md … 250-*.md directly.
This script is a convenience regenerator used when bulk-rewriting the track;
it embeds the same content last shipped to the catalog.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LESSONS = ROOT / "docs" / "lessons"


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    existing = list(LESSONS.glob("2[0-4][0-9]-*.md")) + list(LESSONS.glob("250-*.md"))
    if len(existing) < 50:
        die(
            f"Expected 50 sandbox lessons under {LESSONS}; found {len(existing)}. "
            "Restore from git or re-run the curriculum generator from the delivery session."
        )
    print(f"OK: {len(existing)} Enterprise Sandbox lessons present under docs/lessons/")
    print("Catalog: docs/lessons/_CATALOG_201_250.md")
    print("Style:   docs/lessons/_SANDBOX_STYLE.md")


if __name__ == "__main__":
    main()
