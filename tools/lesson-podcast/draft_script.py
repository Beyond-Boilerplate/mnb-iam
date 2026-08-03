#!/usr/bin/env python3
"""Draft a spoken podcast companion script from a lesson markdown file.

Extracts Why / Concepts / How it works / Summary — not click-by-click lab steps.
Handcrafted scripts in scripts/ are left alone unless --force is passed.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSONS = ROOT / "docs" / "lessons"
SCRIPTS = Path(__file__).resolve().parent / "scripts"

SKIP_SECTIONS = {
    "before you start",
    "lab procedure",
    "acceptance criteria",
    "troubleshooting",
    "training binder evidence",
    "knowledge check",
    "further reading",
    "stretch lab",
    "answers",
    "real-world setup",
}


def _strip_md(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", text)
    text = re.sub(r"^>\s?", "", text, flags=re.M)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.M)
    text = re.sub(r"^[-*]\s+", "", text, flags=re.M)
    text = re.sub(r"^\d+\.\s+", "", text, flags=re.M)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _table_to_speech(block: str) -> str:
    lines = [ln.strip() for ln in block.strip().splitlines() if ln.strip()]
    rows: list[list[str]] = []
    for ln in lines:
        if not ln.startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if cells and all(re.match(r"^:?-+:?$", c) for c in cells):
            continue
        rows.append([_strip_md(c) for c in cells])
    if len(rows) < 2:
        return ""
    header, *body = rows
    spoken: list[str] = []
    for row in body[:8]:  # keep podcasts digestible
        parts = []
        for h, v in zip(header, row):
            if not v or v == "-":
                continue
            parts.append(f"{h}: {v}")
        if parts:
            spoken.append("; ".join(parts) + ".")
    return " ".join(spoken)


def _section_body(md: str, heading: str) -> str:
    pat = re.compile(
        rf"^##\s+{re.escape(heading)}\s*\n(.+?)(?=^##\s+|\Z)",
        re.M | re.S | re.I,
    )
    m = pat.search(md)
    return m.group(1).strip() if m else ""


def _subsections(body: str) -> list[tuple[str, str]]:
    parts = re.split(r"^###\s+(.+)$", body, flags=re.M)
    if len(parts) == 1:
        return [("concepts", parts[0].strip())] if parts[0].strip() else []
    out: list[tuple[str, str]] = []
    # parts[0] is preface before first ###
    if parts[0].strip():
        out.append(("overview", parts[0].strip()))
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:48] or f"part-{i}"
        out.append((slug, f"{title}.\n\n{content}"))
    return out


def _blocks_to_speech(raw: str) -> str:
    """Convert a markdown section into spoken paragraphs (tables → sentences)."""
    if not raw.strip():
        return ""
    chunks: list[str] = []
    buf: list[str] = []
    lines = raw.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("|"):
            if buf:
                chunks.append(_strip_md("\n".join(buf)))
                buf = []
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            spoken = _table_to_speech("\n".join(table_lines))
            if spoken:
                chunks.append(spoken)
            continue
        buf.append(line)
        i += 1
    if buf:
        chunks.append(_strip_md("\n".join(buf)))
    text = "\n\n".join(c for c in chunks if c.strip())
    # Soft trim very long sections (~450 words)
    words = text.split()
    if len(words) > 450:
        text = " ".join(words[:450]).rstrip(",;:") + "."
    return text.strip()


def _lesson_num_words(stem: str) -> str:
    m = re.match(r"^(\d{2,3})([a-z])?-", stem)
    if not m:
        return stem
    n = int(m.group(1))
    letter = m.group(2)
    base = f"Lesson {n}"
    if letter:
        base += f" {letter.upper()}"
    return base


def draft_from_lesson(lesson_path: Path) -> str:
    md = lesson_path.read_text(encoding="utf-8")
    stem = lesson_path.stem
    title_m = re.search(r"^#\s+(.+)$", md, re.M)
    title = title_m.group(1).strip() if title_m else stem
    short = title.split("—", 1)[-1].strip() if "—" in title else title

    objectives = _section_body(md, "Learning objectives")
    obj_bits = []
    for ln in objectives.splitlines():
        ln = ln.strip()
        if ln.startswith("- "):
            obj_bits.append(_strip_md(ln[2:]))
    obj_speech = ""
    if obj_bits:
        top = obj_bits[:5]
        obj_speech = "By the end of this lesson, you will be able to: " + "; ".join(top) + "."

    why = _blocks_to_speech(_section_body(md, "Why this matters"))
    how = _blocks_to_speech(_section_body(md, "How it works"))
    summary = _blocks_to_speech(_section_body(md, "Summary"))
    concepts_raw = _section_body(md, "Concepts")
    concept_parts = _subsections(concepts_raw) if concepts_raw else []

    lesson_words = _lesson_num_words(stem)
    segments: list[tuple[str, str]] = []

    cold = (
        f"Hey — welcome back to Meridian National Bank’s Identity and Access Academy.\n\n"
        f"This is the listen-along for {lesson_words}: {short}.\n\n"
        f"This is a theory companion. Listen for the ideas and the control story, "
        f"then use the written lesson for any binder sketches or design tasks.\n\n"
        f"Grab a notebook."
    )
    if obj_speech:
        cold += f"\n\n{obj_speech}"
    segments.append(("cold-open", cold))

    if why:
        segments.append(("why-this-matters", why))

    for slug, body in concept_parts:
        spoken = _blocks_to_speech(body)
        if spoken:
            segments.append((f"concepts-{slug}"[:40], spoken))

    if how:
        segments.append(("how-it-works", how))

    close = summary or (
        f"That’s the theory for {lesson_words}. Open the written lesson to complete "
        f"any design binder work, then continue to the next module in the Academy."
    )
    if summary:
        close = (
            f"{summary}\n\n"
            f"When you’re ready, open the written lesson for binder work, then move on "
            f"in the Academy. That’s your briefing for {lesson_words}."
        )
    segments.append(("close", close))

    # YAML front matter + segments
    lines = [
        "---",
        f'title: "{title.replace(chr(34), "")}"',
        f"stem: {stem}",
        "voice: en-US-BrianNeural",
        'rate: "-12%"',
        'pitch: "+0Hz"',
        "source: auto-draft",
        "---",
        "",
    ]
    for sid, text in segments:
        lines.append(f"## {sid}")
        lines.append("")
        lines.append(text.strip())
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("lesson", help="Lesson stem or number (e.g. 23 or 23-role-model-intro)")
    ap.add_argument("--force", action="store_true", help="Overwrite existing script")
    ap.add_argument("--stdout", action="store_true", help="Print instead of writing")
    args = ap.parse_args()

    lesson = args.lesson.strip().removesuffix(".md")
    path = LESSONS / f"{lesson}.md"
    if not path.is_file():
        if lesson.isdigit():
            matches = sorted(LESSONS.glob(f"{int(lesson):02d}-*.md"))
            if len(matches) == 1:
                path = matches[0]
            elif matches:
                raise SystemExit(f"Ambiguous: {[p.name for p in matches]}")
        if not path.is_file():
            matches = sorted(LESSONS.glob(f"{lesson}*.md"))
            if len(matches) == 1:
                path = matches[0]
    if not path.is_file():
        raise SystemExit(f"Lesson markdown not found for {args.lesson}")

    dest = SCRIPTS / f"{path.stem}.md"
    if dest.exists() and not args.force and not args.stdout:
        # Protect handcrafted scripts
        existing = dest.read_text(encoding="utf-8")
        if "source: auto-draft" not in existing:
            raise SystemExit(f"Refusing to overwrite handcrafted script {dest} (use --force)")
        if "source: auto-draft" in existing and not args.force:
            raise SystemExit(f"Script exists {dest} (use --force to regenerate draft)")

    text = draft_from_lesson(path)
    if args.stdout:
        print(text)
        return
    SCRIPTS.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    print(f"Wrote {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
