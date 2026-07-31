#!/usr/bin/env python3
"""Look up prior delivery solutions from .ai-delivery/_memory/ (deterministic).

Scores entries by work_type exact match + keyword overlap. Prints ranked hits
as JSON so skills can reuse approaches without re-deriving them.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import MEMORY_ROOT, memory_dir  # noqa: E402

MEMORY_SKILLS = ("classify", "implement", "verify")

TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9\-_/]+", re.I)


def tokenize(text: str) -> set[str]:
    return {t.lower() for t in TOKEN_RE.findall(text or "") if len(t) > 2}


def load_entries(skill: str) -> list[dict[str, Any]]:
    root = memory_dir(skill)
    if not root.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.json")):
        if path.name.startswith("_"):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        try:
            data["_path"] = str(path.relative_to(MEMORY_ROOT.parents[1]))
        except ValueError:
            data["_path"] = str(path)
        data["_file"] = path.name
        data["_skill"] = skill
        out.append(data)
    return out


def score_entry(
    entry: dict[str, Any],
    *,
    work_type: str | None,
    keywords: set[str],
    query_tokens: set[str],
) -> float:
    score = 0.0
    ewt = (entry.get("work_type") or "").lower()
    if work_type and ewt == work_type.lower():
        score += 5.0
    ekeys = {k.lower() for k in (entry.get("keywords") or [])}
    if keywords:
        score += 2.0 * len(keywords & ekeys)
    blob = " ".join(
        [
            entry.get("summary") or "",
            entry.get("approach") or "",
            " ".join(entry.get("keywords") or []),
            entry.get("source_issue") or "",
        ]
    )
    score += 1.0 * len(query_tokens & tokenize(blob))
    # prefer higher recorded confidence lightly
    try:
        score += 0.5 * float(entry.get("confidence") or 0)
    except (TypeError, ValueError):
        pass
    return score


def main() -> int:
    p = argparse.ArgumentParser(description="Lookup delivery memory entries")
    p.add_argument(
        "--skill",
        required=True,
        choices=("classify", "implement", "verify", "all"),
    )
    p.add_argument("--work-type", default=None)
    p.add_argument("--keywords", default="", help="Comma-separated keywords")
    p.add_argument("--query", default="", help="Free-text query (summary/desc)")
    p.add_argument("--limit", type=int, default=5)
    p.add_argument("--min-score", type=float, default=1.0)
    args = p.parse_args()

    skills = list(MEMORY_SKILLS) if args.skill == "all" else [args.skill]
    skills = [s for s in skills if s in MEMORY_SKILLS]
    keywords = {k.strip().lower() for k in args.keywords.split(",") if k.strip()}
    qtokens = tokenize(args.query) | keywords

    ranked: list[dict[str, Any]] = []
    for skill in skills:
        for entry in load_entries(skill):
            s = score_entry(
                entry,
                work_type=args.work_type,
                keywords=keywords,
                query_tokens=qtokens,
            )
            if s >= args.min_score or (args.work_type and (entry.get("work_type") or "").lower() == args.work_type.lower()):
                ranked.append({"score": round(s, 2), "skill": skill, "entry": entry})

    ranked.sort(key=lambda x: (-x["score"], x["entry"].get("_file", "")))
    hits = ranked[: args.limit]

    # Compact form for skill context (saves tokens)
    compact = []
    for h in hits:
        e = h["entry"]
        compact.append(
            {
                "score": h["score"],
                "skill": h["skill"],
                "id": e.get("id") or e.get("_file"),
                "work_type": e.get("work_type"),
                "summary": e.get("summary"),
                "approach": e.get("approach"),
                "solution": e.get("solution"),
                "gotchas": e.get("gotchas") or [],
                "source_issue": e.get("source_issue"),
                "file": e.get("_file"),
            }
        )

    print(json.dumps({"ok": True, "count": len(compact), "hits": compact}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
