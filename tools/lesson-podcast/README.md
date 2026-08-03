# Lesson podcasts — listen-along companions

Turn Meridian Academy lessons into **podcast-style audio** students can digest
while commuting, walking, or reviewing before a lab session.

This is a **pilot** starting with Lesson 01. Audio is a companion, not a
replacement for the written lab procedure.

## Why a rewritten script (not raw markdown)

Reading lesson tables and click-paths aloud sounds robotic. Each episode uses a
**spoken companion script**: short sentences, contractions, intentional pauses,
and examiner framing — same teaching voice as `_STYLE.md`, tuned for ears.

## Voice quality

Default engine: **Microsoft Edge neural TTS** (`edge-tts`), Conversation voices.

| Voice | Character | Use |
| --- | --- | --- |
| `en-US-BrianNeural` (default) | Approachable, casual mentor | Pilot / day-one lessons |
| `en-US-AndrewNeural` | Warm, confident | Alternate A/B |
| `en-US-JennyNeural` | Friendly, clear | Alternate A/B |

Cadence: rate about **−12%** (digestible, not rushed). Segments are stitched
with short silence so section breaks breathe like a podcast.

**Pronunciation:** `pronounce.py` expands selective hard terms before TTS so
acronyms are letter-correct (e.g. `IAM` / `I.A.M.` → spoken **I A M**, never a
mushy “AAM”). Same for `IIQ`, `IGA`, `SoD`, `HR`, `UI`, and common connector
terms. Extend that lexicon when a new lesson introduces a mangled acronym.

**Upgrade path (more natural):** set `OPENAI_API_KEY` and
`LESSON_PODCAST_ENGINE=openai` to use OpenAI `tts-1-hd` / `nova` or `onyx`.
ElevenLabs can be added the same way when a key is available.

## Theory lesson set

Podcasts target **theory / paperwork** lessons (Academy `verifyMode: paperwork`)
plus any lesson with a handcrafted script (Lesson 01 today). Catalog:
`theory.py` → `theory_stems()`.

## Generate

```bash
cd tools/lesson-podcast
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# ffmpeg required for concat

# One lesson
./generate.py 01

# All theory lessons (auto-drafts missing scripts, then TTS)
./generate.py --theory --skip-existing
```

Outputs:

- Scripts: `scripts/<stem>.md` (committed; handcrafted or `source: auto-draft`)
- Working segments: `out/`
- Final MP3 + manifest: `learn/media/podcasts/` (gitignored binaries)

Voice bake-off (30s samples):

```bash
./generate.py 01 --bakeoff
```

## Academy Listen UI

`learn/build.py` when an MP3 exists:

- Injects a **Listen** player under the lesson title
- Marks TOC + curriculum cards with a Listen badge
- Rail filter **Listen** shows only podcast-ready lessons
- Index stats show companion count

```bash
python3 learn/build.py
# open learn/dist/01-bank-briefing-and-ui.html
# or Academy http://localhost:4173/ after lab up
```

## Authoring a new episode

1. Prefer handcrafted `scripts/<NN>-….md` with `## segment-id` sections, **or**
   let `./generate.py --theory` auto-draft from Why / Concepts / How / Summary.
2. Run `./generate.py <NN>` (or `--theory`).
3. Rebuild the learn site and spot-check cadence + acronym pronunciation.
