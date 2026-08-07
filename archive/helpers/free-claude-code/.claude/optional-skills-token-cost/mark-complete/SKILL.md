---
name: mark-complete
description: >-
  Verify a Staff Claude Code curriculum module's acceptance criteria and update
  lessons/progress.md. Use for /mark-complete 06 or "I finished hooks". Require
  artifacts evidence — do not check boxes on reading alone.
---

# Mark complete

## Steps

1. Resolve module `NN` (01–11).
2. Read acceptance / deliverable sections in `lessons/NN-*/README.md`.
3. Check `lessons/artifacts/` for expected outputs (skills, hooks, agents, mcp, playbooks, demos).
4. If evidence missing: list what is still required; do **not** edit progress.
5. If evidence present:
   - Summarize what you found
   - Update `lessons/progress.md` — check the matching box for that module
   - Remind user they can refresh mental model via `local-progress/index.html` (static; free)
6. Offer `/lesson-quiz NN` as optional verification (uses tokens).

## Guardrails

- Never mark complete for skim-only.
- Never invent artifact files.
- Keep the progress.md edit minimal (checkbox only).
