---
name: optimize
description: >-
  Analyze code for performance and simplicity wins. Use when the user says
  /optimize, asks to speed something up, reduce allocations, or simplify a hot path.
---

# Optimize

You are reviewing code for **clarity and performance**, not rewriting for sport.

## Inputs

- Prefer the current selection, open files, or `$ARGUMENTS` as the focus.
- If scope is unclear, ask which file/function before large edits.

## Steps

1. State the suspected bottleneck in one sentence.
2. List 3–5 concrete findings (severity: high/med/low).
3. Propose the smallest change that helps; avoid speculative rewrites.
4. Call out measurement: how to verify (benchmark, log timing, test).

## Output contract

```markdown
## Focus
## Findings
- [severity] …
## Proposed change
## Verify
```

Do not invent metrics you did not observe.
