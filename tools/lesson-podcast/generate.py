#!/usr/bin/env python3
"""Generate podcast-style lesson audio from spoken companion scripts."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

# Progress lines show up immediately when piped/tee'd
try:
    sys.stdout.reconfigure(line_buffering=True)  # type: ignore[attr-defined]
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SCRIPTS = HERE / "scripts"
OUT_ROOT = HERE / "out"
MEDIA = ROOT / "learn" / "media" / "podcasts"

DEFAULT_VOICE = "en-US-BrianNeural"
DEFAULT_RATE = "-12%"
DEFAULT_PITCH = "+0Hz"
GAP_MS = 550
BAKEOFF_VOICES = (
    "en-US-BrianNeural",
    "en-US-AndrewNeural",
    "en-US-JennyNeural",
    "en-US-AriaNeural",
)


def parse_script(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    meta: dict[str, Any] = {
        "voice": DEFAULT_VOICE,
        "rate": DEFAULT_RATE,
        "pitch": DEFAULT_PITCH,
        "title": path.stem,
        "stem": path.stem,
    }
    body = raw
    if raw.startswith("---"):
        end = raw.find("\n---", 3)
        if end != -1:
            front = raw[3:end].strip()
            body = raw[end + 4 :].lstrip("\n")
            for line in front.splitlines():
                if ":" not in line:
                    continue
                key, val = line.split(":", 1)
                meta[key.strip()] = val.strip().strip('"').strip("'")

    segments: list[dict[str, str]] = []
    current_id: str | None = None
    buf: list[str] = []
    for line in body.splitlines():
        m = re.match(r"^##\s+([a-z0-9][a-z0-9-]*)\s*$", line.strip(), re.I)
        if m:
            if current_id is not None:
                text = "\n\n".join(p.strip() for p in "\n".join(buf).split("\n\n") if p.strip())
                if text:
                    segments.append({"id": current_id, "text": text})
            current_id = m.group(1).lower()
            buf = []
            continue
        if current_id is not None:
            buf.append(line)
    if current_id is not None:
        text = "\n\n".join(p.strip() for p in "\n".join(buf).split("\n\n") if p.strip())
        if text:
            segments.append({"id": current_id, "text": text})

    if not segments:
        raise SystemExit(f"No ## segments found in {path}")
    meta["segments"] = segments
    return meta


def _which(cmd: str) -> str | None:
    return shutil.which(cmd)


async def _edge_save(text: str, dest: Path, voice: str, rate: str, pitch: str) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(str(dest))


def _openai_save(text: str, dest: Path, voice: str) -> None:
    import urllib.request

    api_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is required for engine=openai")
    # Map edge voice names to OpenAI voices when authors leave defaults.
    oa_voice = {
        "en-US-BrianNeural": "onyx",
        "en-US-AndrewNeural": "onyx",
        "en-US-JennyNeural": "nova",
        "en-US-AriaNeural": "nova",
        "onyx": "onyx",
        "nova": "nova",
        "shimmer": "shimmer",
        "alloy": "alloy",
        "echo": "echo",
        "fable": "fable",
    }.get(voice, voice if voice in {"alloy", "echo", "fable", "onyx", "nova", "shimmer"} else "onyx")
    payload = json.dumps(
        {
            "model": os.environ.get("OPENAI_TTS_MODEL", "tts-1-hd"),
            "voice": oa_voice,
            "input": text,
            "format": "mp3",
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/audio/speech",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        dest.write_bytes(resp.read())


def synthesize_segment(
    text: str,
    dest: Path,
    *,
    engine: str,
    voice: str,
    rate: str,
    pitch: str,
) -> None:
    from pronounce import apply_pronunciation

    dest.parent.mkdir(parents=True, exist_ok=True)
    # Light spoken cleanup: collapse whitespace, keep paragraph breaths as periods/pauses.
    cleaned = re.sub(r"[ \t]+", " ", text).strip()
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = apply_pronunciation(cleaned)
    if engine == "openai":
        _openai_save(cleaned, dest, voice)
    else:
        asyncio.run(_edge_save(cleaned, dest, voice, rate, pitch))


def make_silence(path: Path, ms: int) -> None:
    ffmpeg = _which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg is required (brew install ffmpeg)")
    sec = max(ms, 50) / 1000.0
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"anullsrc=r=24000:cl=mono",
            "-t",
            f"{sec:.3f}",
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


def concat_mp3(parts: list[Path], dest: Path) -> None:
    ffmpeg = _which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg is required (brew install ffmpeg)")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fh:
        list_path = Path(fh.name)
        for p in parts:
            fh.write(f"file '{p.resolve()}'\n")
    try:
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_path),
                "-c",
                "copy",
                str(dest),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    finally:
        list_path.unlink(missing_ok=True)


def probe_duration_ms(path: Path) -> int:
    ffprobe = _which("ffprobe")
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


def find_script(lesson: str) -> Path:
    lesson = lesson.strip().lower().removesuffix(".md")
    exact = list(SCRIPTS.glob(f"{lesson}*.md"))
    if len(exact) == 1:
        return exact[0]
    if lesson.isdigit():
        padded = f"{int(lesson):02d}"
        matches = sorted(SCRIPTS.glob(f"{padded}-*.md"))
        if len(matches) == 1:
            return matches[0]
        if matches:
            raise SystemExit(f"Ambiguous lesson {lesson}: {[m.name for m in matches]}")
    raise SystemExit(f"No script for lesson {lesson} under {SCRIPTS}")


def generate_episode(script_path: Path, *, engine: str, voice_override: str | None) -> Path:
    meta = parse_script(script_path)
    voice = voice_override or meta.get("voice") or DEFAULT_VOICE
    rate = meta.get("rate") or DEFAULT_RATE
    pitch = meta.get("pitch") or DEFAULT_PITCH
    stem = meta.get("stem") or script_path.stem
    work = OUT_ROOT / stem.split("-")[0]
    audio_dir = work / "audio"
    if audio_dir.exists():
        shutil.rmtree(audio_dir)
    audio_dir.mkdir(parents=True)

    silence = audio_dir / "_gap.mp3"
    make_silence(silence, GAP_MS)

    parts: list[Path] = []
    seg_meta: list[dict[str, Any]] = []
    for i, seg in enumerate(meta["segments"]):
        dest = audio_dir / f"{i:02d}-{seg['id']}.mp3"
        print(f"  TTS [{engine}] {seg['id']} ({len(seg['text'].split())} words)…")
        synthesize_segment(
            seg["text"],
            dest,
            engine=engine,
            voice=voice,
            rate=rate,
            pitch=pitch,
        )
        parts.append(dest)
        seg_meta.append(
            {
                "id": seg["id"],
                "words": len(seg["text"].split()),
                "audio": dest.name,
                "durationMs": probe_duration_ms(dest),
            }
        )
        if i < len(meta["segments"]) - 1:
            parts.append(silence)

    MEDIA.mkdir(parents=True, exist_ok=True)
    final = MEDIA / f"{stem}.mp3"
    print(f"  Concat → {final.relative_to(ROOT)}")
    concat_mp3(parts, final)
    duration = probe_duration_ms(final)
    manifest = {
        "stem": stem,
        "title": meta.get("title"),
        "engine": engine,
        "voice": voice,
        "rate": rate,
        "pitch": pitch,
        "durationMs": duration,
        "durationMin": round(duration / 60000, 1) if duration else None,
        "segments": seg_meta,
        "script": str(script_path.relative_to(ROOT)),
        "audio": str(final.relative_to(ROOT)),
    }
    man_path = MEDIA / f"{stem}.json"
    man_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"  Duration ~{manifest['durationMin']} min · manifest {man_path.relative_to(ROOT)}")
    return final


def bakeoff(script_path: Path, *, engine: str) -> None:
    meta = parse_script(script_path)
    sample_text = meta["segments"][0]["text"]
    # Keep bake-off short (~25–35s spoken).
    words = sample_text.split()
    if len(words) > 90:
        sample_text = " ".join(words[:90]) + "."
    out = OUT_ROOT / "bakeoff"
    out.mkdir(parents=True, exist_ok=True)
    rate = meta.get("rate") or DEFAULT_RATE
    pitch = meta.get("pitch") or DEFAULT_PITCH
    print(f"Bake-off sample from segment '{meta['segments'][0]['id']}' ({len(sample_text.split())} words)")
    for voice in BAKEOFF_VOICES:
        dest = out / f"{voice}.mp3"
        print(f"  {voice}…")
        synthesize_segment(sample_text, dest, engine=engine, voice=voice, rate=rate, pitch=pitch)
        print(f"    → {dest} ({probe_duration_ms(dest) / 1000:.1f}s)")
    print(f"\nListen with: open {out}")


def ensure_script(stem: str, *, redraft: bool = False) -> Path:
    """Return script path, auto-drafting from lesson markdown when missing."""
    existing = SCRIPTS / f"{stem}.md"
    if existing.is_file() and not redraft:
        return existing
    if existing.is_file() and redraft:
        text = existing.read_text(encoding="utf-8")
        if "source: auto-draft" not in text:
            return existing  # never clobber handcrafted
    from draft_script import draft_from_lesson

    lesson_md = ROOT / "docs" / "lessons" / f"{stem}.md"
    if not lesson_md.is_file():
        raise SystemExit(f"No lesson markdown for {stem}")
    SCRIPTS.mkdir(parents=True, exist_ok=True)
    existing.write_text(draft_from_lesson(lesson_md), encoding="utf-8")
    print(f"  Drafted script → {existing.relative_to(ROOT)}")
    return existing


def generate_theory(*, engine: str, voice_override: str | None, redraft: bool, skip_existing_audio: bool) -> None:
    from theory import theory_stems

    stems = theory_stems()
    print(f"Theory podcasts: {len(stems)} lessons")
    for stem in stems:
        print(f"\n=== {stem} ===")
        script = ensure_script(stem, redraft=redraft)
        final = MEDIA / f"{stem}.mp3"
        if skip_existing_audio and final.is_file() and final.stat().st_size > 1000:
            print(f"  Skip (audio exists): {final.relative_to(ROOT)}")
            continue
        generate_episode(script, engine=engine, voice_override=voice_override)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "lesson",
        nargs="?",
        help="Lesson number or stem (e.g. 01 or 01-bank-briefing-and-ui)",
    )
    ap.add_argument("--bakeoff", action="store_true", help="Generate short voice A/B samples only")
    ap.add_argument("--theory", action="store_true", help="Draft + generate all theory / paperwork lessons")
    ap.add_argument("--redraft", action="store_true", help="Regenerate auto-draft scripts (never handcrafted)")
    ap.add_argument(
        "--skip-existing",
        action="store_true",
        help="With --theory, skip lessons that already have an MP3",
    )
    ap.add_argument("--voice", default=None, help="Override voice id")
    ap.add_argument(
        "--engine",
        default=os.environ.get("LESSON_PODCAST_ENGINE", "edge"),
        choices=("edge", "openai"),
        help="TTS engine (default edge; openai needs OPENAI_API_KEY)",
    )
    args = ap.parse_args()
    if args.theory:
        generate_theory(
            engine=args.engine,
            voice_override=args.voice,
            redraft=args.redraft,
            skip_existing_audio=args.skip_existing,
        )
        return
    if not args.lesson:
        ap.error("lesson is required unless --theory is set")
    script = find_script(args.lesson)
    print(f"Script: {script.relative_to(ROOT)}")
    if args.bakeoff:
        bakeoff(script, engine=args.engine)
        return
    generate_episode(script, engine=args.engine, voice_override=args.voice)


if __name__ == "__main__":
    main()
