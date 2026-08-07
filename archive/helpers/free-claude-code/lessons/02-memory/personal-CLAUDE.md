# CLAUDE.md (personal — template)

> Copy to `~/.claude/CLAUDE.md`. Applies to **every** repo you open Claude Code in —
> keep it about *you*, not about any one project. Project facts belong in the
> project's own `CLAUDE.md`, not here.

## How I like to work

- Explain your plan in 2–4 bullets before editing more than one file.
- Prefer small, reviewable diffs over one large rewrite.
- Ask before installing new dependencies.

## My environment

- OS: `<macOS/Linux/WSL>`
- Shell: `<zsh/bash>`
- Package managers I use: `<npm/pnpm, pip/uv, ...>`

## My review preferences

- Always show a diff before applying multi-file changes.
- Flag anything that touches auth, payments, or migrations even if not asked.
- Prefer explicit error handling over silent fallbacks.

## Things I never want auto-run

- `git push --force*` in any form.
- Package publish commands (`npm publish`, `twine upload`, ...).
- Anything under `sudo`.

## Shortcuts I use often

- "ship it" → run tests, lint, then draft a PR description; do not push.
- "why is this slow" → treat as a request to profile/reason before editing.
