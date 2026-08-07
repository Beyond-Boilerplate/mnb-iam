---
title: 02 — Memory
description: Staff Claude Code module 2
sidebar:
  order: 2
---

:::tip[Zero tokens]
This page is static. Read and do the labs in your editor/terminal — no Claude session required for learning.
:::

## At a glance

| | |
| --- | --- |
| **Level** | Beginner+ |
| **Time** | ~45 min |
| **Prereq** | [01 — Slash commands](../01-slash-commands/) |
| **Artifacts** | [`lessons/artifacts/playbooks/`](../artifacts/playbooks/) |

## Why this matters

New hire joins the team, opens Claude Code in the monorepo, and asks it to add an
endpoint. Claude doesn't know the repo uses hexagonal architecture, that migrations go
through Flyway, or that `legacy-billing/` is frozen. Without memory, you re-explain the
same 15 facts every session — or worse, Claude guesses wrong and someone reviews a PR
that imports directly from a forbidden internal package. `CLAUDE.md` is how a repo
teaches every session (yours and your teammates') the facts that would otherwise live
only in your head.

## Concept primer

`CLAUDE.md` is a plain markdown file Claude Code loads automatically into context at
session start. It is **memory**, not a prompt you type — you write it once, it applies
every time, until you edit it.

| Scope | Path | Applies to | Typical content |
| --- | --- | --- | --- |
| Personal | `~/.claude/CLAUDE.md` | Every repo you open | Your habits, environment, review style |
| Project | `<repo>/CLAUDE.md` | Everyone who opens this repo | Build/test commands, architecture, hard stops |
| Directory | `<repo>/<dir>/CLAUDE.md` | That directory and below | Local rules that don't apply repo-wide |

- **Hierarchy**: personal → project → directory, each loaded in addition to (not
  instead of) the ones above it. More specific files add to, not replace, broader ones.
- **Context budget**: every line in every loaded `CLAUDE.md` consumes tokens on *every*
  message, whether relevant to the current task or not. Bloated memory is a recurring
  tax, not a one-time cost.
- **Rules vs facts**: a good `CLAUDE.md` states hard stops ("never force-push") and
  pointers to deeper docs — it does not inline the entire architecture doc.

```text
~/.claude/CLAUDE.md          # you, everywhere
repo/
  CLAUDE.md                  # this repo, everyone
  services/payments/
    CLAUDE.md                # this directory only, adds to the two above
```

> **Tip:** If you're about to paste a paragraph you've typed in chat three times this
> week, that's a `CLAUDE.md` candidate, not a one-off prompt.

## Hands-on walkthrough

1. **Check what's already loaded.**
   - Action: from a repo root, start Claude Code and ask:

     ```text
     What CLAUDE.md files are currently loaded, and summarize each in one line.
     ```

   - Expect: it names personal (if you have one), project root, and any directory-level
     files it picked up for your current working directory.
   - Tip: if it says none exist, that confirms you're starting from zero — proceed.

2. **Read the three templates in this module.**
   - Open [`project-CLAUDE.md`](/templates/02-memory/project-CLAUDE.md), [`personal-CLAUDE.md`](/templates/02-memory/personal-CLAUDE.md),
     and [`directory-CLAUDE.md`](/templates/02-memory/directory-CLAUDE.md).
   - Expect: project = build/test/hard-stops/architecture; personal = your habits and
     environment; directory = narrow local rules.
   - Why: seeing the split makes it obvious what does *not* belong in each — e.g. your
     personal editor preferences don't belong in the project file your teammates load.

3. **Draft a project `CLAUDE.md` for a monorepo, in artifacts (not the repo root yet).**
   - Action:

     ```bash
     cd archive/helpers/free-claude-code/lessons
     mkdir -p artifacts/playbooks
     cp 02-memory/project-CLAUDE.md artifacts/playbooks/monorepo-CLAUDE.draft.md
     ```

   - Then open `artifacts/playbooks/monorepo-CLAUDE.draft.md` and fill in every
     `<placeholder>` for a real monorepo you work in (this repo works: build/test
     commands, hard stops, where not to edit, toolkit table).
   - Expect: no `<...>` placeholders remain; every command in it actually runs.
   - > **Watch out:** don't inline your entire architecture doc. Link to it instead —
     > memory is for facts Claude needs *every* session, not a full reference manual.

4. **Sanity-check length and specificity.**
   - Action: ask Claude to review your draft:

     ```text
     Review artifacts/playbooks/monorepo-CLAUDE.draft.md. Flag anything vague enough
     that two engineers could disagree on what it means, and anything that belongs in
     a linked doc instead of here.
     ```

   - Expect: concrete feedback — e.g. "‘use good commit messages’ is not enforceable;
     name the convention."
   - Tip: tighten hard stops into imperative sentences ("Never edit `X`"), not vibes.

5. **Promote it (only when it's true for the real repo).**
   - Action: once every command in the draft actually runs against the real repo:

     ```bash
     cp artifacts/playbooks/monorepo-CLAUDE.draft.md CLAUDE.md   # at that repo's root
     ```

   - Expect: next session in that repo, Claude cites facts from it unprompted.
   - > **Important:** never blind-overwrite an existing team `CLAUDE.md` — diff first,
     > merge the useful parts, and get a teammate to skim the change.

## Copy-paste templates

- [`project-CLAUDE.md`](/templates/02-memory/project-CLAUDE.md) — repo-root template.
- [`personal-CLAUDE.md`](/templates/02-memory/personal-CLAUDE.md) — your `~/.claude/CLAUDE.md`.
- [`directory-CLAUDE.md`](/templates/02-memory/directory-CLAUDE.md) — narrow, directory-scoped template.

## How it works

Claude Code walks from your current working directory up to the repo root (and reads
`~/.claude/CLAUDE.md` for personal memory), loading every `CLAUDE.md` it finds along the
way into the system context before your first message is even processed. That's why a
directory-level file only "activates" when you're actually working inside that
directory — it's proximity-based, not global. There's no merge conflict resolution
beyond "all loaded files are present" — if two files contradict each other, you get
inconsistent behavior, which is why hierarchy discipline (broad facts high, narrow
overrides low) matters.

## Pitfalls

- **One giant file with everything** → burns budget every message, most of it
  irrelevant to the current task. Fix: split by scope; link to docs instead of inlining.
- **Personal preferences leaking into project memory** → teammates inherit your habits
  as if they were team rules. Fix: keep "how I like to work" in `~/.claude/CLAUDE.md`.
- **Stale commands** → `CLAUDE.md` says `npm test`, the repo migrated to `pnpm test`
  last quarter. Fix: treat `CLAUDE.md` drift like code drift — review it in PRs that
  change build tooling.
- **Vague hard stops** ("be careful with prod") → unenforceable, ignored under pressure.
  Fix: name the exact action and exact condition ("never run migrations against `prod`
  without a reviewed rollback plan").
- **Directory file duplicating the root file** → wastes budget twice. Fix: directory
  files should only add deltas, not restate the root file.

## Knowledge check

1. What is the load order/hierarchy for `CLAUDE.md` files?
   <br>**A:** Personal (`~/.claude/CLAUDE.md`) → project root → directory-level, all
   loaded together (additive), not overriding each other automatically.
2. Why does file length matter for `CLAUDE.md` specifically, more than for a normal doc?
   <br>**A:** It's loaded into context on every message in every session — length is a
   recurring cost, not a one-time read.
3. Where should your personal review preferences (e.g. "always show a diff first") live?
   <br>**A:** `~/.claude/CLAUDE.md` — personal scope, not the project file.
4. Give one example of content that belongs in a *linked* doc, not inlined in `CLAUDE.md`.
   <br>**A:** A full architecture doc, ADRs, or a runbook — link to them instead.
5. What should you do before promoting a draft `CLAUDE.md` to a repo root that already
   has one?
   <br>**A:** Diff against the existing file and merge useful parts — never blind-
   overwrite a team file.
6. Why is a directory-scoped `CLAUDE.md` useful even when a project-level one exists?
   <br>**A:** It carries rules specific to one subtree (e.g. a frozen legacy module)
   that would waste budget if repeated for every other directory in the repo.

## Acceptance criteria

- [ ] `artifacts/playbooks/project-CLAUDE.draft.md` exists and is adapted (not empty template)
- [ ] Personal vs project split is clear in your notes or files
- [ ] No secrets in any memory draft

## Recap

- **Built:** a filled-in, placeholder-free project `CLAUDE.md` draft under
  `artifacts/playbooks/`, reviewed for vagueness and length.
- **Understand:** the personal/project/directory hierarchy, why context budget matters,
  and the difference between a hard stop and a vague preference.
- **Can do next:** promote the draft to a real repo root, or move on to skills (module
  03) to turn recurring *procedures* (not facts) into reusable workflows.

## Stretch

- Add a directory-scoped `CLAUDE.md` for one subtree of a real monorepo you work in,
  and verify Claude cites its local rule when you work there.
- Run a "budget audit": ask Claude to estimate how many tokens your current `CLAUDE.md`
  files cost per message, and cut anything that isn't pulling its weight.

## Feedback

Could you redo the "draft a project `CLAUDE.md`" task from memory, for a different
repo? If a section felt hard to write concretely (not vaguely), note which one — that's
usually a sign the underlying convention itself is fuzzy, not just the writing.

## Domain Stretch

> Optional, skippable. Meridian/IIQ mapping only.

For this SSD repo, a project `CLAUDE.md` hard stop worth keeping verbatim is "never edit
`base/ga/`" — it maps directly to the durable-XML-overlay pattern in `config/` +
`%%TOKENS%%` + `./build.sh` that this repo already uses.

