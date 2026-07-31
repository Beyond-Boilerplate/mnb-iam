#!/usr/bin/env bash
# ~/.claude/statusline.sh — single-line left/right Claude Code statusline
# Requires: jq; optional: git, python3 (for accurate width)
set -euo pipefail

input=$(cat)

CYAN=$'\033[36m'
GREEN=$'\033[32m'
YELLOW=$'\033[33m'
RED=$'\033[31m'
MAGENTA=$'\033[35m'
DIM=$'\033[2m'
BOLD=$'\033[1m'
RESET=$'\033[0m'
SEP="${DIM}·${RESET}"

# Visible column width (ANSI/OSC-safe)
vlen() {
  python3 -c '
import re, sys
s = sys.argv[1]
s = re.sub(r"\x1b\]8;;.*?(?:\x07|\x1b\\)", "", s)
s = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", s)
s = re.sub(r"\x1b\][^\x07]*(?:\x07|\x1b\\)", "", s)
w = 0
for ch in s:
    o = ord(ch)
    if o < 0x7F:
        w += 1
    elif o in (0x2588, 0x2591, 0x2592, 0x2593, 0x00B7, 0x2022, 0x2502):  # █ ░ ▒ ▓ · │
        w += 1
    else:
        w += 2  # emoji / wide
print(w)
' "$1" 2>/dev/null || printf '%s' "$1" | sed -E $'s/\033\\]8;;[^\007]*\007//g; s/\033\\[[0-9;]*[A-Za-z]//g' | wc -m | tr -d ' '
}

# Robust field extract (empty/absent OK)
eval "$(printf '%s' "$input" | jq -r '
  def s: (. // "") | tostring | @sh;
  def n($d): ((. // $d) | tonumber? // $d) | tostring | @sh;
  def b: (if . == true then "1" else "0" end) | @sh;
  [
    "MODEL=\(.model.display_name | s)",
    "DIR=\(.workspace.current_dir // .cwd | s)",
    "SESSION_ID=\(.session_id // "nosession" | s)",
    "PCT=\(.context_window.used_percentage | n(0))",
    "COST=\(.cost.total_cost_usd | n(0))",
    "DURATION_MS=\(.cost.total_duration_ms | n(0))",
    "EFFORT=\(.effort.level | s)",
    "FAST=\(.fast_mode | b)",
    "THINKING=\(.thinking.enabled | b)",
    "FIVE_H=\(.rate_limits.five_hour.used_percentage | s)",
    "WEEK=\(.rate_limits.seven_day.used_percentage | s)",
    "SESSION_NAME=\(.session_name | s)",
    "PR_NUM=\(.pr.number | s)",
    "PR_URL=\(.pr.url | s)",
    "PR_STATE=\(.pr.review_state | s)",
    "VIM_MODE=\(.vim.mode | s)",
    "AGENT=\(.agent.name | s)",
    "WIDTH=\(.render_width_chars | n(0))"
  ] | join("\n")
')"

COLS="$WIDTH"
[[ "${COLS}" =~ ^[0-9]+$ ]] || COLS=0
[ "$COLS" -le 0 ] && COLS="${COLUMNS:-80}"
[[ "${COLS}" =~ ^[0-9]+$ ]] || COLS=80
COLS=$(( COLS > 4 ? COLS - 2 : COLS ))

PCT=${PCT%.*}; PCT=${PCT:-0}
DURATION_MS=${DURATION_MS%.*}; DURATION_MS=${DURATION_MS:-0}

DIR_BASE="${DIR##*/}"
[ -z "$DIR_BASE" ] && DIR_BASE="—"

MODEL_SHORT="$MODEL"
case "$MODEL_SHORT" in */*) MODEL_SHORT="${MODEL_SHORT##*/}" ;; esac
[ "${#MODEL_SHORT}" -gt 28 ] && MODEL_SHORT="${MODEL_SHORT:0:25}…"

# Cached git (5s)
CACHE_FILE="/tmp/cc-statusline-git-${SESSION_ID}"
CACHE_MAX_AGE=5
cache_is_stale() {
  [ ! -f "$CACHE_FILE" ] && return 0
  local mtime
  mtime=$(stat -c %Y "$CACHE_FILE" 2>/dev/null || stat -f %m "$CACHE_FILE" 2>/dev/null || echo 0)
  [ $(($(date +%s) - mtime)) -gt "$CACHE_MAX_AGE" ]
}

if cache_is_stale; then
  if [ -n "$DIR" ] && git -C "$DIR" rev-parse --git-dir >/dev/null 2>&1; then
    BRANCH=$(git -C "$DIR" branch --show-current 2>/dev/null || true)
    STAGED=$(git -C "$DIR" diff --cached --numstat 2>/dev/null | wc -l | tr -d ' ')
    MODIFIED=$(git -C "$DIR" diff --numstat 2>/dev/null | wc -l | tr -d ' ')
    printf '%s|%s|%s\n' "${BRANCH:-}" "${STAGED:-0}" "${MODIFIED:-0}" > "$CACHE_FILE"
  else
    printf '||\n' > "$CACHE_FILE"
  fi
fi
IFS='|' read -r BRANCH STAGED MODIFIED < "$CACHE_FILE" || true
STAGED=${STAGED:-0}; MODIFIED=${MODIFIED:-0}; BRANCH=${BRANCH:-}

# Context bar
if [ "$PCT" -ge 90 ]; then BAR_COLOR="$RED"
elif [ "$PCT" -ge 70 ]; then BAR_COLOR="$YELLOW"
else BAR_COLOR="$GREEN"; fi

FILLED=$((PCT / 10)); [ "$FILLED" -gt 10 ] && FILLED=10
EMPTY=$((10 - FILLED))
BAR=""
[ "$FILLED" -gt 0 ] && printf -v FILL "%${FILLED}s" && BAR="${FILL// /█}"
[ "$EMPTY" -gt 0 ] && printf -v PAD "%${EMPTY}s" && BAR="${BAR}${PAD// /░}"

COST_FMT=$(printf '$%.2f' "$COST")
MINS=$((DURATION_MS / 60000))
SECS=$(((DURATION_MS % 60000) / 1000))
if [ "$MINS" -ge 60 ]; then TIME_FMT="$((MINS / 60))h $((MINS % 60))m"
else TIME_FMT="${MINS}m ${SECS}s"; fi

# LEFT — identity
LEFT="${BOLD}${CYAN}${MODEL_SHORT}${RESET}"
[ -n "$SESSION_NAME" ] && LEFT="${LEFT} ${DIM}${SESSION_NAME}${RESET}"
LEFT="${LEFT} ${SEP} ${DIR_BASE}"
if [ -n "$BRANCH" ]; then
  LEFT="${LEFT} ${SEP} ${GREEN}${BRANCH}${RESET}"
  [ "$STAGED" -gt 0 ] && LEFT="${LEFT}${GREEN}+${STAGED}${RESET}"
  [ "$MODIFIED" -gt 0 ] && LEFT="${LEFT}${YELLOW}~${MODIFIED}${RESET}"
fi
if [ -n "$PR_NUM" ]; then
  case "$PR_STATE" in
    approved) PR_COLOR="$GREEN" ;;
    changes_requested) PR_COLOR="$RED" ;;
    draft) PR_COLOR="$DIM" ;;
    *) PR_COLOR="$YELLOW" ;;
  esac
  if [ -n "$PR_URL" ]; then
    LEFT="${LEFT} ${SEP} $(printf '%b' "${PR_COLOR}\033]8;;${PR_URL}\a#${PR_NUM}\033]8;;\a${RESET}")"
  else
    LEFT="${LEFT} ${SEP} ${PR_COLOR}#${PR_NUM}${RESET}"
  fi
fi
[ -n "$EFFORT" ] && LEFT="${LEFT} ${DIM}⚡${EFFORT}${RESET}"
[ "$FAST" = "1" ] && LEFT="${LEFT} ${YELLOW}fast${RESET}"
[ "$THINKING" = "1" ] && LEFT="${LEFT} ${MAGENTA}think${RESET}"
[ -n "$VIM_MODE" ] && LEFT="${LEFT} ${DIM}${VIM_MODE}${RESET}"
[ -n "$AGENT" ] && LEFT="${LEFT} ${CYAN}@${AGENT}${RESET}"

# RIGHT — metrics
RIGHT="${BAR_COLOR}${BAR}${RESET} ${PCT}%"
RIGHT="${RIGHT} ${SEP} ${YELLOW}${COST_FMT}${RESET}"
RIGHT="${RIGHT} ${SEP} ${TIME_FMT}"

if [ -n "$FIVE_H" ] && [ "$FIVE_H" != "null" ]; then
  fh=$(printf '%.0f' "$FIVE_H")
  if [ "$fh" -ge 90 ]; then LC="$RED"
  elif [ "$fh" -ge 70 ]; then LC="$YELLOW"
  else LC="$GREEN"; fi
  RIGHT="${RIGHT} ${SEP} ${LC}5h ${fh}%${RESET}"
fi
if [ -n "$WEEK" ] && [ "$WEEK" != "null" ]; then
  wk=$(printf '%.0f' "$WEEK")
  if [ "$wk" -ge 90 ]; then LC="$RED"
  elif [ "$wk" -ge 70 ]; then LC="$YELLOW"
  else LC="$GREEN"; fi
  RIGHT="${RIGHT} ${SEP} ${LC}7d ${wk}%${RESET}"
fi

# Pad LEFT …… RIGHT
LW=$(vlen "$LEFT"); RW=$(vlen "$RIGHT")
[[ "$LW" =~ ^[0-9]+$ ]] || LW=40
[[ "$RW" =~ ^[0-9]+$ ]] || RW=30
GAP=$((COLS - LW - RW))
if [ "$GAP" -lt 2 ]; then
  LEFT="${BOLD}${CYAN}${MODEL_SHORT}${RESET}"
  [ -n "$EFFORT" ] && LEFT="${LEFT} ${DIM}⚡${EFFORT}${RESET}"
  [ "$THINKING" = "1" ] && LEFT="${LEFT} ${MAGENTA}think${RESET}"
  LW=$(vlen "$LEFT")
  GAP=$((COLS - LW - RW))
  [ "$GAP" -lt 1 ] && GAP=1
fi

printf -v SPACES "%*s" "$GAP" ""
printf '%b\n' "${LEFT}${SPACES}${RIGHT}"
