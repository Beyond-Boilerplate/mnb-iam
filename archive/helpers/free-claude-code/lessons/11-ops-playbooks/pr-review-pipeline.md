# Playbook: PR review pipeline

**Trigger:** a PR is opened or pushed to, and you want Claude to do the first pass before a human reviewer spends time on it.

**Composes:** skill (PR summary draft) + hook (block secrets/protected paths) + subagent (isolated diff reviewer) + optional MCP (post the comment live).

## Steps

1. **Hook — hard guardrail runs first, automatically.**
   - A `PreToolUse` hook on `Write`/`Edit` (or a pre-push hook, depending where you wire it) denies any change that matches your secrets pattern or a protected path (e.g. `base/ga/` in this repo — see [`../templates/hook-block-base-ga.stub.md`](../templates/hook-block-base-ga.stub.md) for the shape).
   - **Why here:** this must be non-negotiable and can't wait for a skill or subagent to "notice" — deny > hope.

2. **Skill — draft the PR summary.**
   - Invoke (or auto-trigger) a skill that reads the diff and drafts: what changed, why, risk level, test coverage delta.
   - **Why:** structures the reviewer's first read; a human still reads and edits this before it's the real PR description.

3. **Subagent — isolated diff review.**
   - Delegate the actual line-by-line review to a subagent with a narrow prompt ("review this diff for correctness and security issues, nothing else") and its own context — don't let it inherit the summary-drafting conversation.
   - **Why:** context isolation. A reviewer subagent that's seen the PR author's self-justification is a worse reviewer than one that hasn't.

4. **Human gate — approve or request changes.**
   - A person reads the drafted summary + subagent findings and decides: approve, request changes, or escalate.
   - **This step is never automated.** Composing the above three steps saves review *time*, not review *judgment*.

5. **(Optional) MCP — post the comment live.**
   - If a GitHub/GitLab MCP server is configured, post the subagent's findings as a PR comment instead of copy-pasting.
   - **Fallback if MCP is down:** the human reviewer copies the findings into the PR manually — the pipeline still works, just with one manual step.

## What "it worked" looks like

- The secrets/protected-path hook fired (or correctly stayed silent) on a real test diff.
- The drafted summary matches the actual diff's intent, not a generic restatement of the diff.
- The subagent's review findings are specific to lines in the diff, not generic advice.
- A human explicitly approved or requested changes — there's a record of that decision.

## Known gaps / open questions

<!-- Fill in after your dry run: what did this playbook get wrong about your real repo? -->
