# Enterprise Sandbox Path — style (lessons 201–258)

Practical, live, iterative. Distinct from Core Path [`_STYLE.md`](_STYLE.md).
Author coverage map (classic → sandbox): [`_COVERAGE_01_110.md`](_COVERAGE_01_110.md).

**Exemplar:** [Lesson 223 — Break-Glass](223-break-glass-live.md) (assume-nothing, Task-level steps, nested Why/Expect, Feedback).

This path is **standalone**. Classic 01–110 is an optional archive once coverage is `strong` / `replaced-by-live` / theory.

Target length for **live** lessons: enough depth that a beginner can reproduce unaided (often ~180–350 lines). Prefer assumption-safety over arbitrary line counts. Dense bullets beat classic worksheet sprawl.

## Required sections (every **live** lesson)

1. **Header** — Track, Time, Prereq, Stack, **Maps to classic**
2. **Why** — bank/ops outcome **and** a control/examiner hook (never write “Why (1–2 lines)”)
3. **What this is** — name the tool/service/IIQ feature; what it does in *this* estate
4. **Know these** — terms table and/or ASCII flow; include **wrong-way** bullets; absorb classic concepts here when Enterprise skips Core
5. **Intent** — 3–6 bullets of what you will prove before leaving
6. **Before you start** — checkboxes (stack, verify-or-create objects, persona, evidence dir) — **assume nothing** is pre-built for *this* lesson’s objects
7. **Do this** — `### Task N` sections; each: framing → exact action → nested **- Why:** / **- Expect:** → tip/gotcha where confusion is likely
8. **If it fails** — symptom → fix table
9. **You are done when** — observable proof checkboxes
10. **Control note** — control name/owner, SLA, evidence under `~/iiq-lab-evidence/sandbox/`
11. **Quick check** — 3–6 Qs with one-line answers inline
12. **Feedback** — self-check + what to note if stuck (required)
13. **Navigate** — prev/next + catalog (markdown links)

## Theory lessons (256–258)

Marked **Theory** in the catalog. Same header / Why / Know these / Intent / Quick check / Feedback / Navigate.

- May replace live Tasks with **guided inspection** (Debug registry, diagrams, decision tables) when the estate cannot honestly host the tech (IQService, LDIF offline packs).
- Still require concrete Meridian examples and “what the live lab proves vs does not.”

## Rules

- No worksheets, no Capstone essays, no “Further reading” blocks, no paper/notebook assignments
- No fluff — every sentence earns its place
- Prefer bullets and nested Why/Expect over long paragraphs
- Do not expose internal lab design docs or feasibility asides to the reader
- Disposable personas (`lab.*`) for destructive drills — never Helen / Priya / Marcus
- Stack: `./tools/lab/docker/up.sh --enterprise` (add `--with=ad|sso|pam` per lesson)
- Evidence under `~/iiq-lab-evidence/sandbox/<lesson#>/` when asked

## Anti-patterns

- Bare 4–5 line checklists with no context
- “You already have X” without a verify-or-create Task
- Soft “discuss with your team” without a clickable next step
- Cloning classic Knowledge-check / Binder / Stretch wholesale
- Re-teaching all of 01–110 — map with **Maps to classic** + **Know these** and move on
