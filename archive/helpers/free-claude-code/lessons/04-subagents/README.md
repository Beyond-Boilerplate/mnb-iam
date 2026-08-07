# 04 — Subagents

## At a glance

| | |
| --- | --- |
| **Level** | Intermediate+ |
| **Time** | ~1–1.5 h |
| **Prereq** | [03 — Skills](../03-skills/) |
| **Artifacts** | [`lessons/artifacts/agents/`](../artifacts/agents/) |

## Why this matters

You just spent 40 minutes pairing with Claude to implement a feature — the context
window is full of your back-and-forth, dead ends, and half-explained requirements. Now
you ask the same session "review this for me." It's biased: it wrote the code, it wants
to defend it, and its context is cluttered with everything except a clean read of the
diff. A **subagent** runs the review in a fresh, isolated context — it sees the diff and
nothing else, the way a real second reviewer would.

## Concept primer

A subagent is a named, reusable persona (`.claude/agents/<name>.md`) with its own system
prompt, optional restricted tool list, and its own context window — separate from your
main conversation.

| Property | Main conversation | Subagent |
| --- | --- | --- |
| Context | Everything said so far | Only what you hand it (task + relevant files) |
| Bias | Remembers writing the code | Sees the artifact fresh |
| Tools | Whatever you've allowed | Can be scoped narrower per agent |
| Parallelism | One thread | Multiple subagents can run concurrently |

- **Isolation is the point**, not a side effect. A code reviewer that shares context
  with the implementer inherits its blind spots.
- **When to delegate**: the task benefits from a fresh, unbiased look (review), from
  running in parallel with other work (multiple independent checks), or from a narrower
  tool set (a reviewer that can `Read`/`Grep` but not `Edit`, so it literally cannot
  "fix" what it should only flag).
- **When NOT to delegate**: quick, low-stakes edits where spinning up isolation costs
  more than it saves — just do it inline.

```text
.claude/agents/
  code-reviewer.md    # tools: Read, Grep, Glob, Bash — no Edit
  test-engineer.md    # tools: Read, Grep, Glob, Bash, Edit, Write
```

> **Tip:** If an agent's tool list lets it "fix" the very thing it's supposed to only
> flag, you've built a reviewer that can grade its own homework. Scope tools narrowly.

## Hands-on walkthrough

1. **Read both agent definitions in this module.**
   - Open [`code-reviewer.md`](code-reviewer.md) and [`test-engineer.md`](test-engineer.md).
   - Expect: each has frontmatter (`name`, `description`, `tools`), an explicit "one
     job," a numbered procedure, invariants, and an output contract — the same shape as
     a skill, but scoped to a persona plus a restricted tool list.
   - Why: notice `code-reviewer` has no `Edit`/`Write` in its tool list — that's the
     isolation-of-power invariant enforced structurally, not just by instruction.

2. **Install both agents into a real project.**
   - Action:

     ```bash
     mkdir -p .claude/agents
     cp archive/helpers/free-claude-code/lessons/04-subagents/code-reviewer.md .claude/agents/
     cp archive/helpers/free-claude-code/lessons/04-subagents/test-engineer.md .claude/agents/
     ```

   - Expect: `.claude/agents/code-reviewer.md` and `.claude/agents/test-engineer.md`
     exist in the project.

3. **Stage a real (or realistic) change with a gap.**
   - Action: make a small, real code change in a scratch branch — on purpose, leave out
     a test for one edge case (e.g. empty input) so you have something genuine to catch.
   - Expect: `git diff` shows a real, reviewable change.

4. **Run the parallel review scenario.**
   - Action: ask Claude Code to delegate both agents at once:

     ```text
     Delegate to the code-reviewer agent to review my current diff, and to the
     test-engineer agent to check test coverage for the same diff — run them in
     parallel and report both results.
     ```

   - Expect: two independent reports — a review verdict (`APPROVE`/`REQUEST_CHANGES`/
     `NEED_HUMAN`) with file:line findings, and a test-coverage report naming the gap
     you left on purpose.
   - Tip: if `test-engineer` doesn't catch your deliberate gap, your diff wasn't
     realistic enough — make the missing case less obvious and retry, or treat it as a
     genuine finding about the agent's thoroughness.

5. **Compare against a same-session review (no subagent).**
   - Action: in your original implementation session (not a fresh one), ask "review the
     change you just made" directly, no delegation.
   - Expect: a noticeably softer or less specific review than the isolated subagent's —
     this is the bias isolation was meant to remove.
   - > **Watch out:** this comparison is the actual lesson here — if you skip it, you'll
     > have to take isolation's value on faith instead of seeing it.

## Copy-paste templates

- [`code-reviewer.md`](code-reviewer.md) — isolated review, no edit/write tools.
- [`test-engineer.md`](test-engineer.md) — isolated test-writing, full edit tools.

## How it works

When you delegate to a named subagent, Claude Code starts a new context populated only
with that agent's system prompt (its `.md` file body) plus whatever task description
and files you hand it — none of your main conversation's history carries over unless you
explicitly pass it along. Multiple subagents can run concurrently because they don't
share or block on each other's context; each returns a single final report to the main
conversation when done. That report — not the subagent's internal reasoning — is what
lands back in your context, keeping your main thread's budget from ballooning.

## Pitfalls

- **Mega-agent doing review + fix + test + deploy** → defeats isolation; it's now
  reviewing its own fixes again. Fix: one job per agent, chain agents instead of
  merging them.
- **Reviewer agent with `Edit` in its tool list** → it "fixes" instead of flagging,
  and you lose the independent check. Fix: scope tools to match the job.
- **Delegating trivial one-line changes** → isolation overhead isn't worth it. Fix:
  reserve subagents for tasks that actually benefit from a fresh, unbiased context.
- **Passing the entire main conversation into the subagent's task** → reintroduces the
  same bias isolation was meant to remove. Fix: hand it the artifact (diff, file), not
  the backstory.
- **No output contract** → reports come back in different shapes each run, hard to act
  on programmatically or compare across agents. Fix: fix the contract, always.

## Knowledge check

1. What is the core benefit of a subagent's isolated context, concretely?
   <br>**A:** It reviews/tests the artifact without inheriting the bias or clutter of
   the conversation that produced it.
2. Why does `code-reviewer.md` deliberately exclude `Edit`/`Write` from its tools?
   <br>**A:** So it structurally cannot "fix" what it's supposed to only flag —
   isolation of power, not just isolation of context.
3. What is the "mega-agent" anti-pattern?
   <br>**A:** One agent doing multiple unrelated jobs (review + fix + test + deploy),
   which reintroduces bias and makes failures hard to isolate.
4. When should you *not* bother delegating to a subagent?
   <br>**A:** For trivial, low-stakes edits where isolation overhead costs more than
   it saves — just do it inline.
5. What comes back to your main conversation when a subagent finishes?
   <br>**A:** Its final report/output contract — not its full internal reasoning or
   intermediate steps.
6. Why is running `code-reviewer` and `test-engineer` in parallel useful here, rather
   than sequentially?
   <br>**A:** They're independent checks on the same artifact — parallel execution gets
   both results without one blocking the other, and neither biases the other's read.

## Acceptance criteria

- [ ] Both agent files under `artifacts/agents/`
- [ ] Installed to a project `.claude/agents/` (or documented install path)
- [ ] One parallel review scenario completed (live or tabletop merge of both agent contracts)

## Recap

- **Built:** two installed subagents (`code-reviewer`, `test-engineer`) run in parallel
  against a real diff, plus a same-session comparison showing the bias isolation removes.
- **Understand:** context isolation, tool scoping as a safety mechanism, when
  delegation earns its overhead, and the mega-agent anti-pattern.
- **Can do next:** wire an MCP server (module 05) so a subagent can pull live data
  (a real PR, a real ticket) instead of only local files.

## Stretch

- Add a third agent, `security-reviewer.md`, scoped even narrower (`Read`, `Grep` only)
  and run all three in parallel against the same diff.
- Chain agents deliberately: have `test-engineer` run only after `code-reviewer`
  returns `REQUEST_CHANGES` citing missing coverage.

## Feedback

Could you explain, from memory, why `code-reviewer` has no write access? If the
parallel review didn't catch your deliberately-planted gap, note exactly what you
expected it to flag versus what it actually reported.

## Domain Stretch

> Optional, skippable. Meridian/IIQ mapping only.

This repo's `.claude/CLAUDE.md` hard stops (never call `update_rule_source`, confirm
before Jira transitions) are exactly the kind of invariant an IIQ-specific subagent
(e.g. an "XML/BeanShell reviewer") would encode in its own tool-scoped definition,
mirroring `code-reviewer.md` above.
