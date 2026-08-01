#!/usr/bin/env bash
# Record a Meridian lab tutorial (Lesson 04 MVP).
# Usage:
#   ./tools/lab-tutorials/record.sh 04 [--wipe] [--headed]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TUT="$ROOT/tools/lab-tutorials"
VENV="${TUT}/.venv"
LESSON="${1:?lesson number required (e.g. 04)}"
shift || true

WIPE=0
HEADED=0
for arg in "$@"; do
  case "$arg" in
    --wipe) WIPE=1 ;;
    --headed) HEADED=1 ;;
    *) echo "Unknown arg: $arg" >&2; exit 2 ;;
  esac
done

IIQ_BASE="${IIQ_BASE_URL:-http://localhost:8080/identityiq}"
MEDIA="$ROOT/learn/media"
OUT="$TUT/out/${LESSON}"

if [[ ! -x "$VENV/bin/python" ]]; then
  echo "Create venv first:" >&2
  echo "  cd tools/lab-tutorials && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/playwright install chromium" >&2
  exit 1
fi

command -v ffmpeg >/dev/null || { echo "ffmpeg required (brew install ffmpeg)" >&2; exit 1; }

echo "==> Health check ${IIQ_BASE}/login.jsf"
code="$(curl -s -o /dev/null -w '%{http_code}' "${IIQ_BASE}/login.jsf" || true)"
if [[ "$code" != "200" ]]; then
  echo "IIQ not reachable (HTTP $code). Start with ./tools/lab/docker/up.sh" >&2
  exit 1
fi

cd "$TUT"
export IIQ_BASE_URL="$IIQ_BASE"
export PYTHONPATH="$TUT${PYTHONPATH:+:$PYTHONPATH}"

if [[ "$WIPE" -eq 1 ]]; then
  echo "==> Wipe clean slate (MNB-HR + non-spadmin identities)"
  "$VENV/bin/python" -c "from common.wipe import wipe_lesson04; print(wipe_lesson04())"
fi

mkdir -p "$OUT" "$MEDIA"

echo "==> Record lesson ${LESSON}"
REC_ARGS=(--out "$OUT")
if [[ "$HEADED" -eq 1 ]]; then
  REC_ARGS+=(--headed)
fi

case "$LESSON" in
  04|4)
    "$VENV/bin/python" "$TUT/lessons/04_authoritative_hr.py" "${REC_ARGS[@]}"
    STEM="04-authoritative-hr-source"
    ;;
  *)
    echo "Only lesson 04 is implemented in MVP" >&2
    exit 1
    ;;
esac

echo "==> Mux MP4"
"$VENV/bin/python" "$TUT/common/mux_cli.py" --lesson "$LESSON" --stem "$STEM"

echo "==> Done. Play: ${MEDIA}/${STEM}.mp4"
