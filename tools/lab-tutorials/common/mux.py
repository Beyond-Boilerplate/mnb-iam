"""ffmpeg helpers: probe duration and mux video + narration."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


def require_ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        raise SystemExit("ffmpeg not found on PATH (brew install ffmpeg)")
    return exe


def probe_duration_ms(path: Path) -> int:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        # Fallback estimate ~14 chars/sec
        return max(2000, len(path.read_bytes()) // 12)
    proc = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        data = json.loads(proc.stdout or "{}")
        sec = float(data.get("format", {}).get("duration") or 0)
        return int(sec * 1000)
    except (json.JSONDecodeError, TypeError, ValueError):
        return 3000


def find_playwright_webm(video_dir: Path) -> Path:
    vids = sorted(video_dir.glob("**/*.webm")) + sorted(video_dir.glob("**/*.mp4"))
    if not vids:
        raise SystemExit(f"No Playwright video under {video_dir}")
    return max(vids, key=lambda p: p.stat().st_mtime)


def build_narration_track(
    segments: list[dict[str, Any]],
    out_wav: Path,
    total_video_ms: int | None = None,
) -> Path:
    """
    Concatenate segment MP3s with silence pads so each starts near videoStartMs
    when provided; otherwise sequential with 400ms gaps.
    """
    require_ffmpeg()
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    parts_dir = out_wav.parent / "_parts"
    parts_dir.mkdir(exist_ok=True)

    # Sequential mix: pad between clips
    list_file = parts_dir / "concat.txt"
    lines: list[str] = []
    silence = parts_dir / "silence400.mp3"
    if not silence.exists():
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "anullsrc=r=24000:cl=mono",
                "-t",
                "0.4",
                "-q:a",
                "9",
                str(silence),
            ],
            check=True,
            capture_output=True,
        )

    first = True
    for seg in segments:
        ap = seg.get("audioPath")
        if not ap or not Path(ap).exists():
            continue
        if not first:
            lines.append(f"file '{silence}'")
        lines.append(f"file '{Path(ap).resolve()}'")
        first = False

    if not lines:
        raise SystemExit("No narration audio segments to mux")

    list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    concat_mp3 = parts_dir / "narration_concat.mp3"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-c",
            "copy",
            str(concat_mp3),
        ],
        check=True,
        capture_output=True,
    )
    # Normalize to AAC-friendly wav/m4a path — keep mp3 for mux
    shutil.copy(concat_mp3, out_wav.with_suffix(".mp3"))
    return out_wav.with_suffix(".mp3")


def mux_mp4(video: Path, audio: Path, dest: Path, width: int = 1280, height: int = 720) -> Path:
    require_ffmpeg()
    dest.parent.mkdir(parents=True, exist_ok=True)
    # shortest: if narration longer, trim; if video longer, pad audio with apad
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video),
        "-i",
        str(audio),
        "-filter_complex",
        f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p[v];"
        f"[1:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,"
        f"apad[a]",
        "-map",
        "[v]",
        "-map",
        "[a]",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-b:a",
        "160k",
        "-shortest",
        "-movflags",
        "+faststart",
        str(dest),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"ffmpeg mux failed:\n{proc.stderr[-2000:]}")
    return dest
