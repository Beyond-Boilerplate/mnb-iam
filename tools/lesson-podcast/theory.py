"""Theory-lesson catalog for Meridian podcast companions.

Theory = Academy paperwork / design lessons (no live Verify), plus any lesson
that already has a handcrafted spoken script under scripts/.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPECS = ROOT / "tools" / "iiq-verify" / "lesson-specs"
LESSONS = ROOT / "docs" / "lessons"
SCRIPTS = Path(__file__).resolve().parent / "scripts"


def _paperwork_stems() -> list[str]:
    stems: list[str] = []
    for spec in sorted(SPECS.glob("*.json")):
        try:
            data = json.loads(spec.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        mode = (data.get("verifyMode") or "lab").strip().lower()
        if data.get("disabled") is True:
            mode = "paperwork"
        if mode != "paperwork":
            continue
        stem = spec.stem
        if (LESSONS / f"{stem}.md").is_file():
            stems.append(stem)
    return stems


def theory_stems() -> list[str]:
    """Sorted unique theory stems (paperwork + handcrafted script owners)."""
    stems = set(_paperwork_stems())
    for script in SCRIPTS.glob("*.md"):
        stems.add(script.stem)
    # Stable curriculum order
    def key(stem: str) -> tuple:
        if stem.startswith("mid-"):
            m = re.match(r"mid-(\d+)-", stem)
            return (int(m.group(1)) if m else 9999, 50, stem)
        m = re.match(r"^(\d{2,3})([a-z])?-", stem)
        if not m:
            return (9999, 0, stem)
        sub = 0 if not m.group(2) else ord(m.group(2)) - ord("a") + 1
        return (int(m.group(1)), sub, stem)

    return sorted(stems, key=key)


def is_theory(stem: str) -> bool:
    return stem in set(theory_stems())
