# 03 — Skills

## At a glance

| | |
| --- | --- |
| **Level** | Intermediate |
| **Time** | ~1 h |
| **Prereq** | [01 — Slash commands](../01-slash-commands/) (skill anatomy basics) |
| **Artifacts** | [`lessons/artifacts/skills/`](../artifacts/skills/) |

## Why this matters

Every senior engineer on your team has an informal checklist for reviewing a PR: check
tests, check for N+1 queries, check error handling, check for secrets in diffs. It lives
in their head and comes out slightly differently each time, from each person. A **skill**
turns that tribal checklist into a file the whole team runs the same way — auto-loaded
the moment someone's request matches "review this PR," not retyped from memory.

## Concept primer

A skill is a directory containing `SKILL.md`: YAML frontmatter (`name`, `description`)
plus a body Claude reads only after deciding — from the `description` alone — that this
skill is relevant.

| Scope | Path | Shared with team? | Use for |
| --- | --- | --- | --- |
| Personal | `~/.claude/skills/<name>/SKILL.md` | No | Your habits, drafts, experiments |
| Project | `.claude/skills/<name>/SKILL.md` | Yes (via git) | Team-shared, repeatable procedures |

- **One job per skill.** A skill named `review` that also formats code, writes tests,
  and drafts PRs is really three skills wearing one badge — split it.
- **Trigger description, not summary.** The `description` field is the *only* thing
  read before the model decides to load the rest. Write it as "use when X, Y, Z" with
  concrete situations and phrases, not a one-line abstract.
- **Progressive disclosure.** Keep `SKILL.md` itself short (procedure, invariants,
  output contract). Move long reference material, schemas, and worked examples into a
  sibling `reference.md` (or `scripts/`) that gets linked, not inlined — so it only
  costs tokens when a step actually needs it.

```text
.claude/skills/
  code-review-checklist/
    SKILL.md        # short: when/invariants/procedure/output contract
    reference.md      # long: the actual checklist items, examples of each failure
```

> **Tip:** If you can't write the `description` in one sentence starting with "Use
> when...", the skill is probably still two skills.

## Hands-on walkthrough

1. **Read the template and its progressive-disclosure sibling.**
   - Open [`_template/SKILL.md`](_template/SKILL.md) and [`_template/reference.md`](_template/reference.md).
   - Expect: `SKILL.md` stays short and procedural; `reference.md` holds the long tail
     (edge cases, worked example, schema) and is only linked from a step, not preloaded.
   - Why: this is the pattern every skill in this repo should follow once it grows.

2. **Pick a real, recurring review habit you actually use.**
   - Action: name one checklist you run mentally on every PR (tests, N+1 queries, error
     handling, secrets in diff, breaking API changes — pick 4–6 concrete items).
   - Expect: a short list you could dictate to a new hire in under a minute.
   - Tip: if your list is longer than 6 items, it's two skills (e.g. "review" and
     "security review") — split now, not later.

3. **Author `code-review-checklist` into artifacts, using the template.**
   - Action:

     ```bash
     cd archive/helpers/free-claude-code/lessons
     mkdir -p artifacts/skills/code-review-checklist
     cp 03-skills/_template/SKILL.md artifacts/skills/code-review-checklist/
     cp 03-skills/_template/reference.md artifacts/skills/code-review-checklist/
     ```

   - Then edit `artifacts/skills/code-review-checklist/SKILL.md`:
     - `description`: "Use when reviewing a PR/diff before approving or requesting
       changes" (tighten to your real trigger phrases).
     - `Procedure`: your 4–6 real checklist items as numbered steps.
     - `Output contract`: `PASS`/`FAIL`/`NEED_HUMAN` + which checklist items failed.
   - Expect: no `<placeholder>` text remains; every checklist item is concrete and
     checkable (not "check code quality").

4. **Move the detail, not the decision, into `reference.md`.**
   - Action: for each checklist item, add one worked example of a violation in
     `reference.md` (e.g. "N+1: a loop calling `db.get()` per iteration instead of a
     batch query — here is what that looks like in a diff").
   - Expect: `SKILL.md` still reads in under a minute; `reference.md` carries the depth.
   - > **Watch out:** don't just copy the same content into both files — that doubles
     > your maintenance burden and defeats the point of disclosure.

5. **Install it and self-test with a real diff.**
   - Action:

     ```bash
     mkdir -p .claude/skills
     cp -R archive/helpers/free-claude-code/lessons/artifacts/skills/code-review-checklist .claude/skills/
     ```

     Then, with an actual uncommitted diff in the repo:

     ```text
     Review my current changes.
     ```

   - Expect: the skill auto-triggers (no `/name` typed) because "review my current
     changes" matches the description, and it walks your real checklist against the
     real diff.
   - Tip: if it doesn't trigger, the description is too narrow or uses words you didn't
     actually say — loosen it and retry.

## Copy-paste templates

- [`_template/SKILL.md`](_template/SKILL.md) — skill skeleton with all required sections.
- [`_template/reference.md`](_template/reference.md) — progressive-disclosure sibling.

## How it works

At session start (and periodically as you talk), Claude Code scans every skill's
`description` across personal and project scopes. When your message's intent matches a
description closely enough, it loads that skill's full `SKILL.md` body into context for
that turn — and only then, any linked `reference.md` if a procedure step tells it to.
This two-stage load (cheap description scan, then expensive body load, then optional
reference load) is exactly why progressive disclosure saves tokens: the expensive stuff
only loads when it's actually going to be used.

## Pitfalls

- **Mega-skill doing five jobs** → triggers unpredictably, hard to review, hard to fix
  without breaking something else. Fix: one job per skill; split aggressively.
- **Reference material inlined in `SKILL.md`** → every trigger pays the full token cost
  even for simple cases. Fix: move it to `reference.md`, link only where needed.
- **No invariants section** → the skill "helps" by doing something destructive (e.g.
  auto-fixing and force-pushing). Fix: always state what must never happen.
- **Copy-pasted description across two skills** → the model can't tell them apart and
  picks one arbitrarily. Fix: make descriptions mutually exclusive where possible.
- **Skill never updated after the team's process changes** → stale advice looks
  authoritative because it's "the skill." Fix: review skills in the same PRs that change
  the process they encode.

## Knowledge check

1. What's the difference in scope between `~/.claude/skills/` and `.claude/skills/`?
   <br>**A:** Personal (only you, every repo) vs project (in the repo, shared via git
   with your team).
2. What is the "one-job" rule for skills, and why does it matter?
   <br>**A:** Each skill should do exactly one job; multi-job skills trigger
   unpredictably and are harder to review/fix in isolation.
3. What goes in `SKILL.md` versus `reference.md`?
   <br>**A:** `SKILL.md` = short procedure, invariants, output contract; `reference.md`
   = long tail (edge cases, worked examples, schemas) linked only when needed.
4. Why does description quality matter more than body length for triggering correctly?
   <br>**A:** Only the description is scanned to decide whether to load the skill at
   all — a vague description means the skill loads too often or never.
5. What should an `Invariants` section protect against, concretely?
   <br>**A:** Destructive or irreversible actions the skill must never take on its own
   (e.g. force-push, deleting data, bypassing review).
6. How do you verify a skill actually works, beyond "it ran without erroring"?
   <br>**A:** Run it against a real artifact (a real diff, a real file) and check its
   output contract matches what actually happened — not just that it produced output.

## Acceptance criteria

- [ ] `artifacts/skills/code-review-checklist/SKILL.md` (+ reference) exists
- [ ] Skill evaluated once on a real diff (with Claude or by dry-reading the contract against a diff)
- [ ] Short `EVAL.md` notes trigger/output quality

## Recap

- **Built:** a `code-review-checklist` skill with progressive disclosure, installed and
  self-tested against a real diff.
- **Understand:** trigger descriptions, personal vs project scope, one-job design, and
  why progressive disclosure keeps token cost proportional to actual need.
- **Can do next:** delegate a skill's procedure to an isolated subagent (module 04) when
  the review needs its own context window instead of running inline.

## Stretch

- Split `code-review-checklist` into two narrower skills (e.g. `security-review-checklist`
  and `perf-review-checklist`) and compare trigger accuracy against the combined version.
- Add a `scripts/` helper (e.g. a grep for common secret patterns) that the procedure
  shells out to instead of describing in prose.

## Feedback

Could you write a new skill's `description` field from scratch, in one sentence, for a
different recurring task you do? If the skill triggered on something you didn't intend,
note the phrase that caused it — that's the exact fix the description needs.

## Domain Stretch

> Optional, skippable. Meridian/IIQ mapping only.

The Meridian skill template at [`../templates/SKILL.template.md`](../templates/SKILL.template.md)
follows the same shape with IIQ-specific invariants (never edit `base/ga/`, prefer
`./build.sh` with `SPTARGET` set) — a good side-by-side once you've built the generic
version above.
