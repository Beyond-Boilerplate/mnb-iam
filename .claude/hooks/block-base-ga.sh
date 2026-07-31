#!/usr/bin/env bash
# PreToolUse (Edit|Write): block only when the *target path* is under base/ga/
set -euo pipefail
input="$(cat || true)"

path="$(printf '%s' "$input" | python3 -c '
import json,sys
raw=sys.stdin.read()
path=""
try:
    d=json.loads(raw)
except Exception:
    d={}
for key in ("file_path","path","filePath"):
    if isinstance(d.get(key), str):
        path=d[key]
        break
tool = d.get("tool_input") or d.get("toolInput") or d.get("input") or {}
if isinstance(tool, dict):
    for key in ("file_path","path","filePath"):
        if isinstance(tool.get(key), str):
            path=tool[key]
            break
print(path)
' 2>/dev/null || true)"

if [[ -z "$path" ]]; then
  exit 0
fi

norm="${path#./}"
case "$norm" in
  base/ga|base/ga/*|*/base/ga|*/base/ga/*)
    echo "Blocked: do not edit base/ga/ (GA binary tree). Use config/ or pluginsrc/." >&2
    exit 2
    ;;
esac
exit 0
