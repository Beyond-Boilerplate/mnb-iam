# Meridian IAM Audio — podcast studio

**Pivot:** not per-lesson TTS. One **central Audio hub** in the Academy, fed by a
three-agent pipeline that turns curriculum clusters into real conversational
podcast episodes.

## Agents

| Stage | Agent | Job |
| --- | --- | --- |
| 1 | **Planner** | Conversational lesson plan — concepts, examples, why. Strips lab/UI. |
| 2 | **Blender** | Continuity editor — kills cross-episode repetition, keeps callbacks. |
| 3 | **Showrunner** | Two-host dialogue (Alex interviewer + Jordan expert), tech-podcast energy. |

Then dual-voice `edge-tts` → `learn/media/audio/<slug>.mp3`.

Hosts are **inspired by** long-form interview energy — not a celebrity impersonation.

## Catalog

[`catalog/show.yaml`](catalog/show.yaml) — 14 thematic episodes covering:

- SailPoint / IIQ essentials  
- IAM constructs (identity, account, entitlement, role, policy)  
- Security posture (least privilege, break-glass, SoD)  
- Industry standards lens (FFIEC / NIST / exam fluency)  
- Tooling options (connectors, IdP, PAM, ITSM boundaries)

## Run

```bash
export OPENROUTER_API_KEY=sk-or-…
cd tools/podcast-studio
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # needs ffmpeg on PATH

./run.py --list
./run.py E01                      # full pipeline + TTS
./run.py E01 --skip-tts           # scripts only
./run.py E01 --from showrunner    # resume
./run.py --all --skip-existing

python3 ../../learn/build.py      # refresh Audio hub
```

Optional model override: `PODCAST_STUDIO_MODEL=…`

## Academy UI

`learn/build.py` publishes **`audio.html`** — the single Listen surface.
Per-lesson TTS players are retired in favor of this hub.
