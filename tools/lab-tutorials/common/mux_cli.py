#!/usr/bin/env python3
"""Mux Lesson 04 recording artifacts to learn/media/*.mp4."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from common import MEDIA, OUT  # noqa: E402
from common.mux import build_narration_track, find_playwright_webm, mux_mp4  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lesson", default="04")
    ap.add_argument("--stem", default="04-authoritative-hr-source")
    args = ap.parse_args()
    out = OUT / args.lesson
    report = json.loads((out / "timeline.json").read_text(encoding="utf-8"))
    video = find_playwright_webm(out / "video")
    audio = build_narration_track(report["segments"], out / "narration.wav")
    dest = MEDIA / f"{args.stem}.mp4"
    mux_mp4(video, audio, dest)
    print(f"Wrote {dest} ({dest.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
