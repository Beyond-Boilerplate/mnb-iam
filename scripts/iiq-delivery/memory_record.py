#!/usr/bin/env python3
"""Record a reusable delivery memory entry after classify/implement/verify PASS.

Dedupes by id; refreshes updated_at. Keeps solutions short for low token reuse.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import VALID_WORK_TYPES, memory_dir  # noqa: E402

SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    s = SLUG_RE.sub("-", text.lower()).strip("-")
    return s[:60] or "entry"


def main() -> int:
    p = argparse.ArgumentParser(description="Record delivery memory entry")
    p.add_argument("--skill", required=True, choices=("classify", "implement", "verify"))
    p.add_argument("--work-type", required=True)
    p.add_argument("--summary", required=True)
    p.add_argument("--approach", required=True)
    p.add_argument("--solution-json", default="{}", help="JSON object with reusable payload")
    p.add_argument("--keywords", default="", help="Comma-separated")
    p.add_argument("--gotchas", default="", help="Comma-separated gotcha strings")
    p.add_argument("--source-issue", default=None)
    p.add_argument("--confidence", type=float, default=0.85)
    p.add_argument("--id", default=None, help="Stable id (default derived)")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if args.work_type not in VALID_WORK_TYPES:
        print(json.dumps({"ok": False, "error": f"invalid work_type: {args.work_type}"}))
        return 1
    try:
        solution = json.loads(args.solution_json)
    except json.JSONDecodeError as exc:
        print(json.dumps({"ok": False, "error": f"solution-json: {exc}"}))
        return 1

    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    gotchas = [g.strip() for g in args.gotchas.split(",") if g.strip()]
    entry_id = args.id or f"{args.skill}-{slugify(args.work_type)}-{slugify(args.summary)[:40]}"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    dest_dir = memory_dir(args.skill)
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / f"{entry_id}.json"

    entry: dict[str, Any] = {
        "id": entry_id,
        "skill": args.skill,
        "work_type": args.work_type,
        "keywords": keywords,
        "summary": args.summary,
        "approach": args.approach,
        "solution": solution,
        "gotchas": gotchas,
        "source_issue": args.source_issue,
        "confidence": args.confidence,
        "created_at": now,
        "updated_at": now,
    }
    if path.exists():
        prev = json.loads(path.read_text(encoding="utf-8"))
        entry["created_at"] = prev.get("created_at", now)
        entry["updated_at"] = now

    if args.dry_run:
        print(json.dumps({"ok": True, "dry_run": True, "path": str(path), "entry": entry}, indent=2))
        return 0

    path.write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "path": str(path), "id": entry_id}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
