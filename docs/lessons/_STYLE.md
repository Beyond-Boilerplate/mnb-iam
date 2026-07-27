# Meridian IAM Academy — Enterprise lesson style guide

Use this for every lesson rewrite. Pure technical tutorial voice. No fluff marketing.

## Required sections (in order)

1. **Title block** — Lesson number, title, level, track, time, prereq, lab data paths
2. **Learning objectives** — 4–7 measurable bullets (“You will be able to…”)
3. **Why this matters** — 1 short business paragraph + 1 control/audit paragraph
4. **Concepts** — Technical explanation with at least one table or ASCII flow; define IIQ terms before using them
5. **Before you start** — Checklist (IIQ up, lab files copied, prior objects exist)
6. **Lab procedure** — Numbered tasks (Task 1, Task 2…). Each task must include:
   - Exact navigation / commands
   - **Expected result** callout (what the screen/file should show)
   - Optional **If it fails** one-liner
7. **Acceptance criteria** — Checkbox list for “done”
8. **Troubleshooting** — 3–6 common failures with fixes
9. **Training binder evidence** — What to screenshot / note for enterprise training records
10. **Knowledge check** — 4–6 questions (answers in a collapsed-style **Answers** subsection at bottom of that section)
11. **Stretch lab** — Optional harder practice
12. **Summary** — 3 bullets of what you built/learned
13. **Navigation** — Previous / Next links

## Voice rules

- Imperative steps: “Open…”, “Click…”, “Run…”, “Confirm…”
- Name Meridian objects with `MNB-` prefix
- Use real lab personas: `helen.ross`, `priya.wire`, `marcus.approve`, `jordan.reed`, `raj.external`, `samir.hassan`, `sofia.torres`, `kai.nguyen`, `amelia.brooks`, `nina.joiner`
- Corporate email domain: `@meridiannb.com`
- Paths: `~/iiq-lab-data/...` and repo `lab-data/...`
- IIQ URL: `http://localhost:8080/identityiq` (mention homelab URL only as alternate)
- Prefer “Account Aggregation task” over vague “run aggregation”
- Never invent UI labels you are unsure of—say “or equivalent menu path”
- Include enterprise framing: control owner, SLA, evidence, examiner question

## Length target

- Foundations / early: ~180–280 lines
- Intermediate / advanced: ~200–320 lines
- Capstone: ~280–350 lines

## Filename

`docs/lessons/NN-slug.md` — keep existing slug; only deepen content.
