#!/usr/bin/env python3
"""Meridian IAM Audio — multi-agent podcast studio.

Pipeline per episode:
  1) Planner   — conversational lesson plan (no lab detail)
  2) Blender   — continuity / de-dupe across the show
  3) Showrunner — two-host dialogue script (Alex + Jordan)
  4) TTS       — dual-voice MP3 into learn/media/audio/

Usage:
  export OPENROUTER_API_KEY=sk-or-…
  cd tools/podcast-studio && python3 -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  ./run.py E01
  ./run.py --all --skip-existing
  ./run.py E01 --from showrunner   # resume from a stage
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
MEDIA = ROOT / "learn" / "media" / "audio"
CONTINUITY = HERE / "catalog" / "continuity.md"

STAGES = ("planner", "blender", "showrunner", "tts")

# Make local imports work when run as ./run.py
sys.path.insert(0, str(HERE))

from agents.blender import run_blender  # noqa: E402
from agents.planner import run_planner  # noqa: E402
from agents.showrunner import run_showrunner  # noqa: E402
from catalog import gather_sources, get_episode, load_show  # noqa: E402
from dialogue_tts import synthesize_dialogue  # noqa: E402
from llm import StudioLLM  # noqa: E402

try:
    sys.stdout.reconfigure(line_buffering=True)  # type: ignore[attr-defined]
except Exception:
    pass


def _ep_dir(episode_id: str) -> Path:
    d = OUT / episode_id.upper()
    d.mkdir(parents=True, exist_ok=True)
    return d


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def _extract_continuity_seeds(plan: str, episode: dict[str, Any]) -> str:
    """Pull must-cover + do-not-repeat for the show continuity file."""
    must = ""
    m = re.search(r"## Must-cover checklist\n(.+?)(?:\n## |\Z)", plan, re.S | re.I)
    if m:
        must = m.group(1).strip()
    dnr = ""
    m2 = re.search(r"## Do-not-repeat seeds\n(.+?)(?:\n## |\Z)", plan, re.S | re.I)
    if m2:
        dnr = m2.group(1).strip()
    return (
        f"### {episode['id']} — {episode['title']}\n"
        f"**Must-cover:**\n{must or '- (none extracted)'}\n\n"
        f"**Do-not-repeat seeds:**\n{dnr or '- (none)'}\n"
    )


def _update_continuity(episode: dict[str, Any], blended_plan: str) -> None:
    block = _extract_continuity_seeds(blended_plan, episode)
    existing = _read(CONTINUITY)
    header = "# Meridian IAM Audio — show continuity\n\n"
    if not existing.startswith("#"):
        existing = header + existing
    # Replace or append this episode's block
    pat = re.compile(
        rf"### {re.escape(episode['id'])} — .+?(?=### |\Z)",
        re.S,
    )
    if pat.search(existing):
        existing = pat.sub(block + "\n", existing)
    else:
        existing = existing.rstrip() + "\n\n" + block + "\n"
    _write(CONTINUITY, existing)


def run_episode(episode_id: str, *, start_from: str = "planner", skip_tts: bool = False) -> Path | None:
    bundle = get_episode(episode_id)
    show = bundle["show"]
    episode = bundle["episode"]
    hosts = bundle["hosts"]
    eid = episode["id"].upper()
    work = _ep_dir(eid)
    llm = StudioLLM()

    plan_path = work / "01-plan.md"
    blend_path = work / "02-blended-plan.md"
    script_path = work / "03-dialogue.md"
    manifest_path = work / "manifest.json"

    MEDIA.mkdir(parents=True, exist_ok=True)
    mp3_path = MEDIA / f"{episode['slug']}.mp3"

    stage_i = STAGES.index(start_from)

    if stage_i <= STAGES.index("planner"):
        print(f"[{eid}] Agent 1 — Planner…")
        sources = gather_sources(episode)
        _write(work / "00-sources.md", sources)
        plan = run_planner(llm, show=show, episode=episode, sources=sources)
        _write(plan_path, plan)
    else:
        plan = _read(plan_path)
        if not plan:
            raise SystemExit(f"Missing {plan_path}; run from planner")

    if stage_i <= STAGES.index("blender"):
        print(f"[{eid}] Agent 2 — Blender / continuity…")
        prior = _read(CONTINUITY)
        # Exclude this episode's own prior block to avoid self-compression loops
        prior = re.sub(
            rf"### {re.escape(eid)} — .+?(?=### |\Z)",
            "",
            prior,
            flags=re.S,
        )
        blended = run_blender(llm, episode=episode, plan=plan, prior_continuity=prior)
        _write(blend_path, blended)
        _update_continuity(episode, blended)
    else:
        blended = _read(blend_path) or plan

    if stage_i <= STAGES.index("showrunner"):
        print(f"[{eid}] Agent 3 — Showrunner (two-host)…")
        script = run_showrunner(llm, show=show, episode=episode, hosts=hosts, blended_plan=blended)
        _write(script_path, script)
    else:
        script = _read(script_path)
        if not script:
            raise SystemExit(f"Missing {script_path}")

    if skip_tts or stage_i > STAGES.index("tts"):
        print(f"[{eid}] Skipping TTS")
        return None

    print(f"[{eid}] Dual-voice TTS → {mp3_path.relative_to(ROOT)}")
    voices = {
        "ALEX": hosts["interviewer"]["voice"],
        "JORDAN": hosts["expert"]["voice"],
    }
    tts_meta = synthesize_dialogue(script, mp3_path, voices=voices, work_dir=work / "tts")
    manifest: dict[str, Any] = {
        "id": eid,
        "slug": episode["slug"],
        "title": episode["title"],
        "season": episode.get("season"),
        "themes": episode.get("themes"),
        "source_lessons": episode.get("source_lessons"),
        "audio": str(mp3_path.relative_to(ROOT)),
        "script": str(script_path.relative_to(ROOT)),
        "hosts": {
            "interviewer": hosts["interviewer"]["name"],
            "expert": hosts["expert"]["name"],
            "voices": voices,
        },
        **tts_meta,
    }
    _write(manifest_path, json.dumps(manifest, indent=2))
    # Hub-facing manifest next to mp3
    _write(MEDIA / f"{episode['slug']}.json", json.dumps(manifest, indent=2))
    print(f"[{eid}] Done · ~{manifest.get('durationMin')} min · {tts_meta.get('turns')} turns")
    return mp3_path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("episode", nargs="?", help="Episode id (E01) or slug")
    ap.add_argument("--all", action="store_true", help="Produce every episode in the catalog")
    ap.add_argument("--skip-existing", action="store_true", help="Skip episodes that already have MP3")
    ap.add_argument("--skip-tts", action="store_true", help="Stop after dialogue script")
    ap.add_argument(
        "--from",
        dest="start_from",
        default="planner",
        choices=STAGES,
        help="Resume pipeline from this stage",
    )
    ap.add_argument("--list", action="store_true", help="List catalog episodes")
    args = ap.parse_args()

    if args.list:
        show = load_show()
        for ep in show["episodes"]:
            print(f"{ep['id']:4}  S{ep.get('season','?')}  {ep['slug']:28}  {ep['title']}")
        return

    if args.all:
        show = load_show()
        for ep in show["episodes"]:
            mp3 = MEDIA / f"{ep['slug']}.mp3"
            if args.skip_existing and mp3.is_file() and mp3.stat().st_size > 1000:
                print(f"[{ep['id']}] Skip existing {mp3.name}")
                continue
            run_episode(ep["id"], start_from=args.start_from, skip_tts=args.skip_tts)
        return

    if not args.episode:
        ap.error("episode required (or --all / --list)")
    run_episode(args.episode, start_from=args.start_from, skip_tts=args.skip_tts)


if __name__ == "__main__":
    main()
