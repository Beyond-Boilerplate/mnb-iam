# Hook stub — block writes under base/ga

Adapt stdin/stdout JSON to your runtime (Claude Code hooks vs Cursor `hooks.json`).
The **policy** is portable; the wrapper is not.

## Policy

Deny any edit/write/delete whose path contains:

- `base/ga/`
- `identityiq-8.5.zip` (write/delete)

## Bash sketch (matcher logic)

```bash
#!/usr/bin/env bash
set -euo pipefail
# Read tool payload from stdin (schema depends on runtime)
payload="$(cat)"
if printf '%s' "$payload" | grep -Eiq 'base/ga|identityiq-8\.5\.zip'; then
  # Emit deny response in your runtime's format
  echo '{"permissionDecision":"deny","permissionDecisionReason":"Meridian: never mutate base/ga GA artifacts"}'
  exit 0
fi
echo '{"permissionDecision":"allow"}'
```

Wire this via Day 15–16 lesson instructions after confirming your runtime schema.
