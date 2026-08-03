"""Load show catalog and gather source lesson text for an episode."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CATALOG = HERE / "catalog" / "show.yaml"
LESSONS = ROOT / "docs" / "lessons"

# Keep source packs lean for LLM context.
KEEP_SECTIONS = {
    "learning objectives",
    "why this matters",
    "concepts",
    "how it works",
    "summary",
    "further reading",
}
DROP_SECTIONS = {
    "lab procedure",
    "before you start",
    "acceptance criteria",
    "troubleshooting",
    "training binder evidence",
    "knowledge check",
    "answers",
    "stretch lab",
    "real-world setup",
}


def load_show() -> dict[str, Any]:
    return yaml.safe_load(CATALOG.read_text(encoding="utf-8"))


def get_episode(episode_id: str) -> dict[str, Any]:
    show = load_show()
    eid = episode_id.strip().upper()
    if not eid.startswith("E"):
        eid = f"E{eid}" if eid.isdigit() else episode_id
    for ep in show["episodes"]:
        if ep["id"].upper() == eid.upper() or ep["slug"] == episode_id:
            return {"show": show["show"], "episode": ep, "hosts": show["show"]["hosts"]}
    raise SystemExit(f"Unknown episode {episode_id}. Known: {[e['id'] for e in show['episodes']]}")


def _extract_sections(md: str) -> str:
    """Keep conceptual sections; drop lab/procedure noise."""
    parts = re.split(r"^(## .+)$", md, flags=re.M)
    if len(parts) == 1:
        return md[:6000]
    out: list[str] = []
    # title / preamble
    head = parts[0].strip()
    if head:
        out.append(head[:800])
    for i in range(1, len(parts), 2):
        heading = parts[i].strip()
        body = parts[i + 1] if i + 1 < len(parts) else ""
        name = re.sub(r"^##\s+", "", heading).strip().lower()
        if name in DROP_SECTIONS:
            continue
        if name in KEEP_SECTIONS or name.startswith("concept"):
            # strip giant tables a bit
            body = re.sub(r"(?m)^\|.+\|$", "", body)
            body = re.sub(r"```.*?```", "[diagram omitted]", body, flags=re.S)
            out.append(f"{heading}\n{body.strip()[:3500]}")
    text = "\n\n".join(out).strip()
    return text[:12000]


def gather_sources(episode: dict[str, Any]) -> str:
    chunks: list[str] = []
    for stem in episode.get("source_lessons") or []:
        path = LESSONS / f"{stem}.md"
        if not path.is_file():
            # allow stems without extension already
            matches = list(LESSONS.glob(f"{stem}*"))
            path = matches[0] if matches else path
        if not path.is_file():
            chunks.append(f"### MISSING SOURCE: {stem}\n")
            continue
        md = path.read_text(encoding="utf-8")
        chunks.append(f"### SOURCE LESSON: {stem}\n\n{_extract_sections(md)}")
    return "\n\n---\n\n".join(chunks)
