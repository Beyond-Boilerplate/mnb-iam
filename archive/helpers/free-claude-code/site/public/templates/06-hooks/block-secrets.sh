#!/usr/bin/env bash
# PreToolUse hook — deny writes/edits that introduce likely secrets.
#
# Wire this to the Edit/Write matcher in your settings hooks config (see
# settings-hooks.snippet.json in this folder). Reads the tool call payload as JSON on
# stdin, inspects the proposed content, and emits an allow/deny decision as JSON on
# stdout. Deny-by-default on any match — never "hope it's a false positive."
set -euo pipefail

payload="$(cat)"

# Extract the proposed file content/diff from the payload. Field name depends on your
# Claude Code version's hook schema — adjust the jq path if yours differs.
content="$(printf '%s' "$payload" | jq -r '.tool_input.content // .tool_input.new_string // ""' 2>/dev/null || true)"

# Deliberately broad, deny-by-default patterns. Tune per repo, but err toward more
# false positives (ask/deny) over missed secrets.
PATTERNS='AKIA[0-9A-Z]{16}|-----BEGIN (RSA|EC|OPENSSH|DSA) PRIVATE KEY-----|ghp_[A-Za-z0-9]{36}|sk-[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|(api|secret|access)[_-]?key[[:space:]]*[:=][[:space:]]*[\"'"'"'][^\"'"'"']{12,}'

if printf '%s' "$content" | grep -Eiq "$PATTERNS"; then
  cat <<'JSON'
{"permissionDecision":"deny","permissionDecisionReason":"block-secrets: proposed content matches a known secret pattern (API key / private key / token). Remove it and use an env var or secret manager instead."}
JSON
  exit 0
fi

echo '{"permissionDecision":"allow"}'
