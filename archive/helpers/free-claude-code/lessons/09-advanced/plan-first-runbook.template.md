# Plan-first runbook — template

Fill this in for one real, recurring task at your job. Save your copy as `../artifacts/playbooks/plan-first-runbook.md`.

## Task name

<!-- e.g. "Bump a shared internal library across N services" -->

## Why this needs plan mode (not just Manual/Accept edits)

<!-- What makes the blast radius unclear up front? -->

## Step 1 — Enter plan mode, ask for the plan

Prompt to use:

```text
<fill in the exact prompt you'd give Claude to scope this task>
```

Expect the plan to name:

- [ ] Every file/service it intends to touch
- [ ] Any external side effects (deploys, notifications, API calls)
- [ ] Open questions it couldn't resolve by reading alone

## Step 2 — Review checklist before approving

- [ ] Does the file list match what I'd expect? Anything surprising?
- [ ] Are there irreversible steps in the plan (deploy, delete, force-push)? Flag them explicitly.
- [ ] Does anything need to run in the background (long build/test)?

## Step 3 — Approve and execute

<!-- Permission mode to switch to after approval, e.g. "Accept edits" -->

## Step 4 — Verify

<!-- Concrete command/check that proves the task succeeded -->

## Rollback if it goes wrong

<!-- Checkpoint/rewind plan, or git-level rollback if beyond session scope -->
