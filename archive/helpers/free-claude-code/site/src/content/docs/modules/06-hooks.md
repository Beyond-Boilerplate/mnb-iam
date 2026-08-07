---
title: 06 — Hooks
description: Staff Claude Code module 6
sidebar:
  order: 6
---

:::tip[Zero tokens]
This page is static. Read and do the labs in your editor/terminal — no Claude session required for learning.
:::

## At a glance

| | |
| --- | --- |
| **Level** | Intermediate |
| **Time** | ~1 h |
| **Prereq** | [02 — Memory](../02-memory/) (hard stops), any module using `Edit`/`Write` |
| **Artifacts** | [`lessons/artifacts/hooks/`](../artifacts/hooks/) |

## Why this matters

Your `CLAUDE.md` says "never commit secrets." Under deadline pressure, on a long
session, that sentence is one instruction among hundreds already in context — and
instructions can be missed, argued past, or simply forgotten mid-flow. A **hook** is not
a reminder; it is a mechanical, always-run check that fires on every matching tool call,
with no dependence on the model remembering or agreeing. When a hook denies, nothing
happens — full stop, before the write lands.

## Concept primer

A **hook** is a shell command Claude Code runs automatically around specific tool
calls, configured in `settings.json` (or `settings.local.json`), keyed by lifecycle
event and a tool-name matcher.

| Event | Fires | Typical use |
| --- | --- | --- |
| **PreToolUse** | Before the tool call executes | Deny/allow gate — can block the action entirely |
| **PostToolUse** | After the tool call executes | Logging, notifications, follow-up automation |

- **Deny > hope.** A `CLAUDE.md` rule is a strong hint the model usually follows. A
  `PreToolUse` hook that returns `deny` is a hard stop the tool call cannot bypass —
  reach for a hook, not just a memory rule, for anything genuinely non-negotiable.
- **Matcher**: hooks are scoped to specific tools (e.g. `Edit|Write`) via a regex-like
  matcher, not globally — you're not intercepting every single action, just the ones
  you name.
- **Contract**: a `PreToolUse` hook reads the proposed tool call as JSON on stdin and
  writes an allow/deny decision as JSON on stdout. Non-zero exit or malformed output is
  treated conservatively by most configurations — test yours explicitly, don't assume.

```text
tool call requested
      │
      ▼
 PreToolUse hook(s) ──deny──> stopped, nothing written
      │ allow
      ▼
 tool call executes
      │
      ▼
 PostToolUse hook(s) (logging, notifications)
```

> **Watch out:** a hook that crashes or times out is not the same as a hook that denies.
> Test failure modes explicitly — don't assume "no output" means "safe."

## Hands-on walkthrough

1. **Read both hook scripts and the settings snippet.**
   - Open [`block-secrets.sh`](/templates/06-hooks/block-secrets.sh), [`block-protected-path.sh`](/templates/06-hooks/block-protected-path.sh),
     and [`settings-hooks.snippet.json`](/templates/06-hooks/settings-hooks.snippet.json).
   - Expect: each script reads JSON from stdin, checks a pattern, and emits
     `{"permissionDecision":"allow"}` or a `deny` with a human-readable reason.
   - Why: the reason string matters — whoever (or whatever) reads the denial should
     understand *why* without digging into the script.

2. **Stage the hooks into your artifacts folder.**
   - Action:

     ```bash
     cd archive/helpers/free-claude-code/lessons
     mkdir -p artifacts/hooks
     cp 06-hooks/block-secrets.sh artifacts/hooks/
     cp 06-hooks/block-protected-path.sh artifacts/hooks/
     cp 06-hooks/settings-hooks.snippet.json artifacts/hooks/
     chmod +x artifacts/hooks/*.sh
     ```

   - Expect: both scripts are executable (`ls -la` shows `x` bits set).

3. **Install into a real project and wire the settings snippet.**
   - Action:

     ```bash
     mkdir -p .claude/hooks
     cp archive/helpers/free-claude-code/lessons/artifacts/hooks/block-secrets.sh .claude/hooks/
     cp archive/helpers/free-claude-code/lessons/artifacts/hooks/block-protected-path.sh .claude/hooks/
     chmod +x .claude/hooks/*.sh
     ```

   - Then open that project's `.claude/settings.json` and merge in the `hooks` key from
     [`settings-hooks.snippet.json`](/templates/06-hooks/settings-hooks.snippet.json) — **merge**, don't
     overwrite, so you keep your existing `permissions` block.
   - Expect: `.claude/settings.json` now has both a `permissions` key (unchanged) and a
     `hooks` key (new).
   - > **Important:** back up or diff the file before saving — a bad merge that drops
     > your permissions block is a real regression.

4. **Test the deny path directly (before trusting it inside a live session).**
   - Action: simulate what the hook receives, without going through Claude at all:

     ```bash
     echo '{"tool_input":{"file_path":"src/app.js","content":"const key = \"AKIAABCDEFGHIJKLMNOP\";"}}' \
       | bash .claude/hooks/block-secrets.sh
     ```

   - Expect output:

     ```json
     {"permissionDecision":"deny","permissionDecisionReason":"block-secrets: proposed content matches a known secret pattern (API key / private key / token). Remove it and use an env var or secret manager instead."}
     ```

   - Tip: also test a clean payload (no secret pattern) and confirm you get back
     `{"permissionDecision":"allow"}` — a hook that always denies is as broken as one
     that never denies.

5. **Test it live, inside a real session.**
   - Action: ask Claude to write a file containing something that matches your pattern
     (e.g. a fake AWS-shaped key like `AKIAABCDEFGHIJKLMNOP` — not a real credential):

     ```text
     Create scratch.txt with the line: const key = "AKIAABCDEFGHIJKLMNOP";
     ```

   - Expect: the write is blocked, and Claude reports the denial reason back to you —
     the file is never created.
   - Then try the protected-path hook: ask it to edit a file under a path you listed in
     `PROTECTED` (e.g. `base/ga/anything.txt` if that pattern is in your repo).
   - Expect: same deny behavior, different reason string.

## Copy-paste templates

- [`block-secrets.sh`](/templates/06-hooks/block-secrets.sh) — deny on likely secret patterns.
- [`block-protected-path.sh`](/templates/06-hooks/block-protected-path.sh) — deny on protected path writes.
- [`settings-hooks.snippet.json`](/templates/06-hooks/settings-hooks.snippet.json) — wiring for both, plus a
  `PostToolUse` logging example.

## How it works

`PreToolUse` hooks run synchronously, in order, before the tool call executes — if
*any* hook returns `deny`, the whole call is blocked and neither later hooks nor the
tool itself run. Each hook is a separate process: Claude Code serializes the proposed
tool call to JSON, pipes it to your command's stdin, and parses stdout as the decision.
That is why hooks outrank a `CLAUDE.md` instruction — the model isn't "deciding" to
respect the hook; the exit path is enforced by the harness regardless of intent.

## Pitfalls

- **Pattern too narrow** (only matches AWS keys) → other secret shapes (GitHub tokens,
  private keys, Slack tokens) sail through. Fix: keep patterns broad and update them as
  you learn your stack's actual secret shapes.
- **Silent failure on hook crash** → a hook that throws an unhandled error might not
  behave like a `deny`. Fix: `set -euo pipefail` plus explicit testing of malformed input.
- **Hardcoded absolute paths** (`/Users/you/project/...`) → breaks for every other
  teammate. Fix: use `$CLAUDE_PROJECT_DIR` (repo-relative), never a personal path.
- **Overwriting `settings.json` instead of merging** → silently drops your existing
  `permissions` block. Fix: diff before saving; merge keys, never replace the file.
- **Treating a hook as "set and forget"** → secret shapes and protected paths change as
  the repo evolves. Fix: review hook patterns in the same PRs that add new secret types
  or new generated/vendor directories.

## Knowledge check

1. What is the practical difference between a `PreToolUse` and a `PostToolUse` hook?
   <br>**A:** `PreToolUse` runs before the tool call and can deny/block it entirely;
   `PostToolUse` runs after and can only react (log, notify), not prevent.
2. Why is "deny > hope" more than a slogan — what does a hook enforce that a `CLAUDE.md`
   rule doesn't?
   <br>**A:** A hook is enforced by the harness mechanically on every matching call; a
   `CLAUDE.md` rule is a strong instruction the model could still miss or be argued past.
3. What format does a `PreToolUse` hook read on stdin, and what must it write to stdout?
   <br>**A:** JSON describing the proposed tool call in; JSON with a
   `permissionDecision` (`allow`/`deny`) and, for deny, a `permissionDecisionReason` out.
4. Why should a hook script never hardcode a path like `/Users/you/project/...`?
   <br>**A:** It breaks for every other teammate/machine; use the project-relative
   environment variable your runtime provides instead.
5. What is the risk of merging a `hooks` snippet by overwriting the whole
   `settings.json` file instead of merging keys?
   <br>**A:** You can silently drop the existing `permissions` block, weakening
   security instead of strengthening it.
6. Why test a hook script directly with a piped JSON payload *before* testing it live
   inside a session?
   <br>**A:** It isolates the hook's own logic from the session/tool-call plumbing —
   faster to debug, and confirms both the deny and allow paths independently.

## Acceptance criteria

- [ ] Hook scripts + snippet under `artifacts/hooks/`
- [ ] Deny + allow proven with JSON payloads (see Task 4) — record in `PROOF.md`
- [ ] You can explain deny > hope

## Recap

- **Built:** two working `PreToolUse` deny hooks (secrets, protected paths) installed
  and wired via a merged settings snippet, tested both directly and inside a live
  session.
- **Understand:** `PreToolUse` vs `PostToolUse`, why hooks are a stronger guarantee than
  a memory rule, and the "deny > hope" principle in practice.
- **Can do next:** revisit module 04's subagents and scope their allowed tools even
  tighter now that you can also enforce hard denies at the hook layer underneath them.

## Stretch

- Add a `PostToolUse` hook that pings a webhook (or just appends to a log file) whenever
  a `Bash` tool call matches `git push`, so you have an audit trail independent of chat
  history.
- Extend `block-secrets.sh`'s pattern list with one secret shape specific to a real
  service you use, and add a test payload for it.

## Feedback

Could you explain, from memory, why a hook is a stronger guarantee than a `CLAUDE.md`
instruction? If a test payload didn't produce the deny you expected, note the exact
payload you sent and the exact output you got — that's the fastest way to find a pattern
bug.

## Domain Stretch

> Optional, skippable. Meridian/IIQ mapping only.

The protected-path pattern in `block-protected-path.sh` mirrors this repo's real hard
stop — never edit `base/ga/` — and the stub at
[`../templates/hook-block-base-ga.stub.md`](../templates/hook-block-base-ga.stub.md)
sketches the same policy in Meridian's own runtime terms.

