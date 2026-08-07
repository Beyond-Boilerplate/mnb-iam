---
name: pr
description: >-
  Draft or critique a pull request: summary, risk, test plan. Use when the user
  says /pr, asks for a PR description, or wants a pre-merge risk review. Args: $ARGUMENTS
---

# Pull request assistant

Focus: **merge readiness**, not feature brainstorming.

## Inputs

- `$ARGUMENTS` — extra focus (e.g. "auth tests", "migrations")
- Prefer `git status` / `git diff` (ask before destructive git commands)

## Steps

1. Summarize the change in 2–4 bullets (user-facing impact first).
2. Risk: what could break; blast radius; rollback note.
3. Test plan: commands or checks a reviewer can run.
4. Call out missing tests or docs explicitly.

## Output contract

```markdown
## Summary
## Risk
## Test plan
- [ ] …
## Reviewer notes
```

Never invent passing CI. If unknown, say what to run.
