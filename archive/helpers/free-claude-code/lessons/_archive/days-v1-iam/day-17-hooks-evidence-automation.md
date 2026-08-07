# Day 17 — Evidence Automation Hooks

| Field | Value |
| --- | --- |
| **Week** | 3 — Hooks + Agents |
| **Time** | 2–3 hours |
| **Prereq** | Day 07 evidence habits; Day 15 hooks |
| **Artifacts** | `artifacts/hooks/evidence/` |

## Learning objectives

You will be able to:

- Use SessionStart / Stop hooks to nudge evidence discipline
- Auto-create dated evidence directories
- Append session summaries to CHANGELOG stubs
- Keep hooks from becoming nagware (signal > noise)

## IAM pain (today’s tax)

The work happened; the binder is empty. Training and audit fail for lack of screenshots and verify JSON. Automation should make the happy path the easy path.

## Claude concept

**Lifecycle hooks**:

```text
SessionStart → mkdir evidence/$(date) → remind SPTARGET
    ... work ...
Stop → prompt: did you save verify output + CHANGELOG line?
```

Prefer injecting short context over blocking Stop (unless enterprise requires gate).

## Before you start

- [ ] Evidence root `~/iiq-lab-evidence` exists  

## Lab procedure

### Task 1 — SessionStart script

Creates `~/iiq-lab-evidence/YYYY-MM-DD/` if missing; prints path into agent context.

### Task 2 — Stop checklist hook

Asks agent to list: verifies run, screenshots needed, CHANGELOG entries for new `MNB-*` objects.

### Task 3 — Optional PostToolUse on verify scripts

When `verify-lesson.sh` or `assert-mnb-objects.sh` runs, copy/symlink report into today’s evidence folder.

### Task 4 — Noise control

Document max 1 SessionStart banner; no hooks on every Read.

## Deliverable

Evidence hook pack + sample CHANGELOG template `artifacts/playbooks/CHANGELOG.template.md`.

## Acceptance criteria

- [ ] New session creates/shows evidence path  
- [ ] Stop produces a checklist at least once in testing  
- [ ] Verify output landing documented  
- [ ] Hooks do not deny ordinary reads  

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Duplicate directories | Idempotent mkdir -p only  
| Agent ignores Stop text | Strengthen wording; add to CLAUDE.md  

## Stretch

- Auto-open evidence path in Finder note  
- Tie Stop hook to Jira comment stub (Day 23)  

## Knowledge check

1. Why SessionStart over manual mkdir?  
2. What belongs in CHANGELOG for Meridian academy?  
3. Observe vs deny for Stop?

### Answers

1. Removes forgotten ritual.  
2. Objects created/exported, tickets, verify results.  
3. Usually observe/remind — deny only if policy demands.

## Navigation

[← Day 16](day-16-hooks-iiq-guardrails.md) · [Day 18 →](day-18-agents-specialists.md)
