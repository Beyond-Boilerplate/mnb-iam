#!/usr/bin/env bash
# PreToolUse hook — deny edit/write/delete under protected paths.
#
# Wire this to the Edit/Write matcher in your settings hooks config (see
# settings-hooks.snippet.json in this folder). Deny > hope: this is a hard, mechanical
# stop, not a reminder in a CLAUDE.md that can be talked past under pressure.
set -euo pipefail

payload="$(cat)"

path="$(printf '%s' "$payload" | jq -r '.tool_input.file_path // .tool_input.path // ""' 2>/dev/null || true)"

# Add your repo's real protected paths here. Pipe-separated regex alternatives.
PROTECTED='(^|/)base/ga/|(^|/)\.env(\..*)?$|(^|/)vendor/|(^|/)node_modules/'

if printf '%s' "$path" | grep -Eiq "$PROTECTED"; then
  cat <<JSON
{"permissionDecision":"deny","permissionDecisionReason":"block-protected-path: '$path' is under a protected path. Confirm with a human before touching it, or route the change through the intended process."}
JSON
  exit 0
fi

echo '{"permissionDecision":"allow"}'
