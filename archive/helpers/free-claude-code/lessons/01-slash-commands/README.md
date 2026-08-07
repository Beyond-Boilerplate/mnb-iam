# 01 — Slash commands & skills-as-commands

## At a glance

| | |
| --- | --- |
| **Level** | Beginner |
| **Time** | ~30–45 min |
| **Prereq** | Claude Code installed (`claude` / `cc`); any git repo to run it in |
| **Artifacts** | [`lessons/artifacts/skills/`](../artifacts/skills/) |

## Why this matters

You are mid-review on a PR that touches a hot loop in a request handler. You want the
same disciplined optimization pass every time: read first, find the real bottleneck,
keep behavior identical, measure the delta. Retyping that checklist in every chat
wastes time and drifts — one review says "check tests," another forgets. A **reusable
command** turns that checklist into `/optimize handler.go` and gets you the same rigor
every time, from you or any teammate who copies the file.

## Concept primer

Claude Code gives you two overlapping ways to make a reusable, typed-in shortcut:

| Mechanism | File | Invoked as | Argument passing | Best for |
| --- | --- | --- | --- | --- |
| **Slash command** | `.claude/commands/<name>.md` | `/name args` | Literal `$ARGUMENTS` placeholder substituted into the prompt text | One-shot prompt templates |
| **Skill (as a command)** | `.claude/skills/<name>/SKILL.md` | `/name args` or auto-triggered | Model reads your typed text as context — no literal substitution, but the effect is the same | Multi-step procedures with invariants, output contracts, progressive disclosure |

- **Slash command**: the simplest reusable prompt. Claude Code substitutes anything you
  type after the command name into `$ARGUMENTS` inside the markdown file, then runs the
  resulting prompt.
- **Skill**: a directory with `SKILL.md` (YAML frontmatter `name` + `description`, then
  a body). Skills can be invoked the same way (`/name args`) *or* auto-loaded when your
  request matches the `description`. Skills scale better because they carry procedure,
  invariants, and an output contract — not just a templated sentence.
- **Personal vs project**: `~/.claude/skills/` (or `~/.claude/commands/`) applies to
  every repo you open; `.claude/skills/` (or `.claude/commands/`) is committed with the
  repo and shared with your team.

```text
.claude/
  commands/
    quick-note.md        # $ARGUMENTS substitution, one prompt, no logic
  skills/
    optimize/
      SKILL.md            # procedure + invariants + output contract
    pr/
      SKILL.md
```

> **Tip:** Reach for a slash command when the "shortcut" is really one paragraph of
> boilerplate prompt. Reach for a skill the moment you find yourself writing "step 1,
> step 2, never do X" — that structure deserves a real procedure.

## Hands-on walkthrough

1. **See what already exists.**
   - Run:

     ```bash
     claude
     /help
     ```

   - Expect: a list including built-in commands like `/compact`, `/model`, `/rewind`.
   - Why: confirms your install works and shows the baseline before you add anything.

2. **Read the two prebuilt skill templates in this module.**
   - Open [`optimize/SKILL.md`](optimize/SKILL.md) and [`pr/SKILL.md`](pr/SKILL.md).
   - Expect: each has YAML frontmatter (`name`, `description`), a "When to use", a
     numbered "Procedure", "Invariants", and an "Output contract".
   - Tip: the `description` field is what makes auto-trigger work — it is the only
     thing Claude sees before deciding whether to load the rest of the file.

3. **Stage them into your artifacts folder.**
   - Action:

     ```bash
     cd archive/helpers/free-claude-code/lessons
     mkdir -p artifacts/skills
     cp -R 01-slash-commands/optimize artifacts/skills/
     cp -R 01-slash-commands/pr artifacts/skills/
     ```

   - Expect: `artifacts/skills/optimize/SKILL.md` and `artifacts/skills/pr/SKILL.md`
     exist.
   - Why: artifacts is your durable "I built this" record, separate from the lesson copy.

4. **Install into a real project's skills directory.**
   - Action (run from any project root you are allowed to write to — this monorepo
     works):

     ```bash
     mkdir -p .claude/skills
     cp -R archive/helpers/free-claude-code/lessons/artifacts/skills/optimize .claude/skills/
     cp -R archive/helpers/free-claude-code/lessons/artifacts/skills/pr .claude/skills/
     ```

   - Expect: `.claude/skills/optimize/` and `.claude/skills/pr/` exist in the project
     you are working in.
   - > **Watch out:** copying into `.claude/skills/` commits the skill to the repo if
     > you `git add` it. Confirm that is what you want before committing.

5. **Run `/optimize` against a real file.**
   - Action: pick any file with a loop, a query, or a serialization step, then:

     ```text
     /optimize path/to/file.ext
     ```

   - Expect: Claude states the bottleneck in one sentence *before* changing code, then
     makes a minimal change, then reports the output contract (`bottleneck`, `change`,
     `verification`, `risk`).
   - Tip: if Claude jumps straight to editing without naming the bottleneck first, stop
     it and ask it to restate the procedure — that is the invariant being skipped.

6. **Run `/pr` against a branch with real commits.**
   - Action: on a feature branch with at least one commit ahead of `main`:

     ```text
     /pr
     ```

   - Expect: a title, a bulleted summary that maps to actual diff hunks, a test-plan
     checklist, and a risk-notes line (or "none").
   - Tip: if the summary mentions something not in the diff, the skill hallucinated —
     point it back at `git diff <base>...HEAD` and ask it to re-derive the summary.

## Copy-paste templates

- [`optimize/SKILL.md`](optimize/SKILL.md) — performance-pass skill, behavior-preserving.
- [`pr/SKILL.md`](pr/SKILL.md) — PR description drafted from a real diff.

## How it works

Claude Code resolves `/name` in this order: built-in commands first, then commands
under `.claude/commands/` and `~/.claude/commands/`, then skills registered under
`.claude/skills/` and `~/.claude/skills/`. For skills, the `description` field doubles
as a **router** — Claude also auto-loads a skill mid-conversation if your free-text
request matches it closely enough, with no `/name` typed at all. That is why description
quality matters more than body length: a vague description either never triggers or
triggers on everything.

## Pitfalls

- **Description too broad** ("helps with code") → triggers on unrelated requests, or
  the model can't tell which of several skills to use. Fix: name the exact trigger
  phrases and situations.
- **Description too narrow** ("optimize `handler.go` line 42") → never triggers again
  after that one use. Fix: describe the *class* of situation, not the instance.
- **No output contract** → every run reports results differently, making them hard to
  compare or paste into a PR. Fix: always end the procedure with a fixed-shape summary.
- **Skill silently skips its own invariants** → e.g. `/optimize` changes a public
  signature. Fix: call it out explicitly when reviewing the diff; invariants are not
  self-enforcing without you checking.
- **Committing a skill with hardcoded secrets or personal paths** → fix: keep skills
  environment-agnostic; parameters come from the conversation, not from baked-in paths.

## Knowledge check

1. What is the one required frontmatter field, besides `name`, on every `SKILL.md`?
   <br>**A:** `description` — it drives both explicit `/name` matching and auto-trigger.
2. What is the practical difference between a `.claude/commands/*.md` slash command and
   a skill, for argument handling?
   <br>**A:** Commands literally substitute `$ARGUMENTS` into the prompt text; skills
   have no literal substitution — the model reads whatever you typed as conversational
   context.
3. Where do you put a skill so it is shared with your whole team via git?
   <br>**A:** `.claude/skills/<name>/SKILL.md` inside the repo (not `~/.claude/skills/`).
4. Why does `optimize/SKILL.md` require reading the target file before editing?
   <br>**A:** To find the actual bottleneck instead of guessing — an invariant meant to
   stop premature or wrong optimizations.
5. What should you do if a skill's output doesn't match its own output contract?
   <br>**A:** Treat that as a bug in the run — ask Claude to re-derive the missing field
   rather than accepting a partial answer.
6. Name one reason to prefer a slash command over a skill for a given shortcut.
   <br>**A:** The shortcut is truly a single templated prompt with no procedure,
   invariants, or multi-step logic — a skill would be overkill.

## Acceptance criteria

- [ ] `artifacts/skills/optimize/` and `artifacts/skills/pr/` exist
- [ ] Skills installed under a project `.claude/skills/` and invoked once each (optional Claude — or verify files + skill shape by reading)
- [ ] You can explain `$ARGUMENTS` and why mega-commands are a bad default

## Recap

- **Built:** two working skills (`optimize`, `pr`) staged in `artifacts/skills/` and
  installed into a real project's `.claude/skills/`.
- **Understand:** slash commands vs skills, `$ARGUMENTS` vs conversational arguments,
  personal vs project scope, and why description quality drives trigger accuracy.
- **Can do next:** write a third skill from scratch for your own recurring shortcut, or
  move on to memory (`CLAUDE.md`) so Claude stops needing repo context re-explained.

## Stretch

- Write a `.claude/commands/quick-note.md` slash command using `$ARGUMENTS` and compare
  its behavior to a skill with the same intent — note where each falls short.
- Add a third invariant to `pr/SKILL.md` for your team's convention (e.g. Jira/Linear
  ticket ID in the title) and re-run it.

## Feedback

Could you explain, from memory, when you'd reach for a slash command versus a skill?
If a step tripped you up, note the step number and what you expected vs. what actually
happened — that is more useful signal than "it didn't work."

## Domain Stretch

> Optional, skippable. Meridian/IIQ mapping only.

If you work IdentityIQ SSB day to day, a natural third skill is a `tokenize` command
that walks an Application/Rule export and replaces environment-specific values with
`%%TOKENS%%` before it goes into `config/`. Same shape as `optimize`/`pr`: When to use,
Procedure, Invariants (never touch `base/ga/`), Output contract.
