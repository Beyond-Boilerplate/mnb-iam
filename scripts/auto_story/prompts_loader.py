"""Load prompt markdown packs."""

from __future__ import annotations

from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def load_prompt(*parts: str) -> str:
    path = PROMPTS_DIR.joinpath(*parts)
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def compose_system(story_type: str | None = None, *extra_files: str) -> str:
    chunks = [load_prompt("system.md")]
    for rel in extra_files:
        text = load_prompt(rel) if "/" in rel or rel.endswith(".md") else load_prompt(f"{rel}.md")
        if text:
            chunks.append(text)
    if story_type:
        typed = load_prompt("types", f"{story_type}.md")
        if typed:
            chunks.append(typed)
    return "\n\n".join(c.strip() for c in chunks if c.strip())
