"""Two-host dialogue TTS (edge-tts) with pronunciation lexicon."""

from __future__ import annotations

import asyncio
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

# Reuse lesson-podcast pronunciation if available
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lesson-podcast"))
try:
    from pronounce import apply_pronunciation
except ImportError:  # pragma: no cover

    def apply_pronunciation(text: str) -> str:
        return text


DEFAULT_RATE = "-10%"
GAP_MS = 280
HOST_GAP_MS = 180


def parse_dialogue(script: str) -> list[dict[str, str]]:
    lines: list[dict[str, str]] = []
    # Accept ALEX: / **ALEX:** / Alex: (stage directions in parens stripped later)
    pat = re.compile(r"^\*{0,2}(ALEX|JORDAN)\*{0,2}\s*:\s*(.+)$", re.I)
    for raw in script.splitlines():
        m = pat.match(raw.strip())
        if not m:
            continue
        speaker = m.group(1).upper()
        text = m.group(2).strip()
        # Drop leading stage directions: (laughs) / (upbeat, …)
        text = re.sub(r"^\([^)]*\)\s*", "", text).strip()
        text = text.strip("*").strip()
        # Second pass if markdown left a leading paren block after trim
        text = re.sub(r"^\([^)]*\)\s*", "", text).strip()
        if text:
            lines.append({"speaker": speaker, "text": text})
    if len(lines) < 6:
        raise SystemExit(
            f"Dialogue parse found only {len(lines)} lines — showrunner script may be malformed."
        )
    return lines


def _spoken_cleanup(text: str) -> str:
    text = text.replace("`", "")
    text = text.replace("—", ", ")
    text = text.replace("–", ", ")
    text = re.sub(r"\s+", " ", text).strip()
    return apply_pronunciation(text)


async def _edge_save(text: str, dest: Path, voice: str, rate: str) -> None:
    import edge_tts

    await edge_tts.Communicate(_spoken_cleanup(text), voice, rate=rate).save(str(dest))


def _silence(path: Path, ms: int) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg required")
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=24000:cl=mono",
            "-t",
            f"{max(ms, 40) / 1000:.3f}",
            "-q:a",
            "9",
            "-acodec",
            "libmp3lame",
            str(path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _concat(parts: list[Path], dest: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg required")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fh:
        list_path = Path(fh.name)
        for p in parts:
            fh.write(f"file '{p.resolve()}'\n")
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_path), "-c", "copy", str(dest)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    finally:
        list_path.unlink(missing_ok=True)


def _duration_ms(path: Path) -> int:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return 0
    try:
        out = subprocess.check_output(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            text=True,
        ).strip()
        return int(float(out) * 1000)
    except (subprocess.CalledProcessError, ValueError):
        return 0


def synthesize_dialogue(
    script: str,
    dest_mp3: Path,
    *,
    voices: dict[str, str],
    work_dir: Path,
    rate: str = DEFAULT_RATE,
) -> dict[str, Any]:
    """voices: {'ALEX': voiceId, 'JORDAN': voiceId}"""
    turns = parse_dialogue(script)
    audio_dir = work_dir / "turns"
    if audio_dir.exists():
        shutil.rmtree(audio_dir)
    audio_dir.mkdir(parents=True)

    gap = audio_dir / "_gap.mp3"
    host_gap = audio_dir / "_hostgap.mp3"
    _silence(gap, GAP_MS)
    _silence(host_gap, HOST_GAP_MS)

    parts: list[Path] = []
    meta_turns: list[dict[str, Any]] = []
    prev_speaker: str | None = None
    for i, turn in enumerate(turns):
        speaker = turn["speaker"]
        voice = voices.get(speaker) or voices.get(speaker.title())
        if not voice:
            raise SystemExit(f"No voice mapped for {speaker}")
        dest = audio_dir / f"{i:03d}-{speaker.lower()}.mp3"
        print(f"  TTS {speaker}: {turn['text'][:72]}…")
        asyncio.run(_edge_save(turn["text"], dest, voice, rate))
        if prev_speaker is not None:
            parts.append(host_gap if prev_speaker != speaker else gap)
        parts.append(dest)
        meta_turns.append(
            {
                "i": i,
                "speaker": speaker,
                "chars": len(turn["text"]),
                "durationMs": _duration_ms(dest),
            }
        )
        prev_speaker = speaker

    _concat(parts, dest_mp3)
    duration = _duration_ms(dest_mp3)
    return {
        "turns": len(turns),
        "durationMs": duration,
        "durationMin": round(duration / 60000, 1) if duration else None,
        "turnMeta": meta_turns,
    }
