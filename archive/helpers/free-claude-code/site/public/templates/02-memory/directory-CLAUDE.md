# CLAUDE.md (directory-scoped — short template)

> Drop this inside a specific subdirectory (e.g. `services/payments/CLAUDE.md`) when
> that directory has rules the repo-root `CLAUDE.md` shouldn't have to carry for every
> other directory. Loaded in addition to the root file when you're working here.

## Scope

This file applies only to `<this directory and its children>`.

## Local rules

- `<e.g. all money amounts are integer cents, never float>`
- `<e.g. this package has no external network calls in unit tests>`

## Local build/test override (if different from root)

```bash
<command, only if it differs from the root CLAUDE.md>
```

## Do not

- `<e.g. import from ../internal/ across service boundaries>`
