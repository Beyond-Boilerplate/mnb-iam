# CLAUDE.md (project — template)

> Copy this to your repo root as `CLAUDE.md`. Delete sections that don't apply. Keep it
> short — this file is loaded into every session's context, and every line costs budget.

## What this repo is

One or two sentences: what the service/app does, who owns it, where it runs.

## Hard stops (always)

- Never commit secrets, `.env` files, or credentials.
- Never force-push to `main`/`master`.
- Confirm before destructive git operations (`reset --hard`, `clean -fd`, history rewrite).
- Confirm before any prod deploy or migration.

## Build / test / run

```bash
# build
<command>

# run tests (fast subset)
<command>

# run the full suite (slow — use before opening a PR, not every edit)
<command>

# run locally
<command>
```

## Conventions

- Language/framework version: `<e.g. Java 21, Node 20>`
- Formatter/linter: `<command>` — run before committing.
- Commit style: `<e.g. Conventional Commits>`
- Branch naming: `<e.g. feature/, fix/, chore/>`

## Architecture notes Claude needs every session

- `<layer/module>` → `<what lives there, what must not leak into it>`
- `<layer/module>` → `<what lives there, what must not leak into it>`

## Where NOT to look / edit without asking

- `<generated dir, vendor dir, legacy module>` — reason.

## Toolkits / integrations in this repo

| Need | Where |
| --- | --- |
| CI config | `<path>` |
| Feature flags | `<path or system>` |
| Secrets | `<external secret manager — never inline>` |

## Pointers, not paragraphs

Link to deeper docs instead of inlining them:

- Architecture: `docs/architecture.md`
- Runbook: `docs/runbook.md`
- ADRs: `docs/adr/`
