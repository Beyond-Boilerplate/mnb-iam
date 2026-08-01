# Lab tutorials — annotated screencasts

Record Meridian academy lab walkthroughs against a live Docker IIQ with Playwright,
TTS narration (`edge-tts`), on-screen callouts, and ffmpeg mux to MP4.

## Prerequisites

- Docker lab up: `./tools/lab/docker/up.sh` (IIQ at http://localhost:8080/identityiq)
- Python 3.11+
- `ffmpeg` on PATH (`brew install ffmpeg`)
- Chromium for Playwright

```bash
cd tools/lab-tutorials
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Record Lesson 04

```bash
# Clean slate (deletes non-spadmin identities + MNB-HR), then record + mux
./tools/lab-tutorials/record.sh 04 --wipe

# Re-record without wipe
./tools/lab-tutorials/record.sh 04
```

Output:

- Working files: `tools/lab-tutorials/out/04/`
- Final MP4: `learn/media/04-authoritative-hr-source.mp4` (gitignored)

Target runtime: about 8–12 minutes.

## Notes

- HR file path in Docker: `/opt/iiq-lab-data/HRApplications.txt`
- Credentials default to `spadmin` / `admin` (override with `IIQ_USER` / `IIQ_PASSWORD`)
- Large media files are gitignored; regenerate locally and optionally embed via Academy build
