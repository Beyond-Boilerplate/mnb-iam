"""Generate per-step narration audio with edge-tts."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import edge_tts

DEFAULT_VOICE = "en-US-GuyNeural"


async def _save(text: str, path: Path, voice: str) -> None:
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(path))


def synthesize_segments(
    segments: list[dict[str, Any]],
    audio_dir: Path,
    voice: str = DEFAULT_VOICE,
) -> list[dict[str, Any]]:
    """
    segments: [{id, text, ...}]
    Writes audio_dir/{id}.mp3 and returns segments with audioPath + durationMs approx.
    """
    audio_dir.mkdir(parents=True, exist_ok=True)

    async def run_all() -> None:
        for seg in segments:
            sid = seg["id"]
            text = (seg.get("narration") or seg.get("text") or "").strip()
            if not text:
                continue
            path = audio_dir / f"{sid}.mp3"
            await _save(text, path, voice)
            seg["audioPath"] = str(path)

    asyncio.run(run_all())

    # Rough duration from file size is poor; use ffprobe when available.
    from .mux import probe_duration_ms

    for seg in segments:
        ap = seg.get("audioPath")
        if ap:
            seg["audioDurationMs"] = probe_duration_ms(Path(ap))
    return segments


def write_timeline(path: Path, timeline: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(timeline, indent=2), encoding="utf-8")
