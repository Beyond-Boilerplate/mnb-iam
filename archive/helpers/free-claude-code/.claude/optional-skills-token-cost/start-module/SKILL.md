---
name: start-module
description: >-
  Open a Staff Claude Code curriculum module as a thin checklist: objectives,
  before-you-start, first task, done-looks-like. Use for /start-module 03 or
  "start the hooks lesson". Keep responses short to save tokens — do not paste
  the entire README.
---

# Start module

Thin launcher for `lessons/NN-*/README.md`.

> **Token note:** Summarize — do not dump the whole file. Learner should open the README in the editor.

## Steps

1. Resolve module number/name (same map as lesson-quiz: 01–11).
2. Read only the top of `lessons/NN-*/README.md` (at a glance, why, before-you-start / first tasks).
3. Reply with:
   - Module title + time estimate
   - 3–5 learning objectives (bullets)
   - Before-you-start checklist
   - **Task 1 only** (framing + exact action + expected)
   - Path to full README and templates
   - Reminder: do the lab yourself when possible; ask Claude for help only on stuck steps
4. Ask whether to proceed to Task 2 when they finish Task 1 (do not auto-run the whole lab).
