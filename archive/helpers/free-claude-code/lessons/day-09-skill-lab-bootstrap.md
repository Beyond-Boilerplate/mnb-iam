# Day 09 — Skill: Lab Bootstrap

| Field | Value |
| --- | --- |
| **Week** | 2 — Skills |
| **Time** | 2–3 hours |
| **Prereq** | Day 08; Day 04 checklist |
| **Artifacts** | `artifacts/skills/meridian-lab-bootstrap/SKILL.md` |

## Learning objectives

You will be able to:

- Turn `lab-health-checklist.md` into a production-quality skill
- Install it where Claude Code can load it
- Execute “morning stack check” via skill trigger phrases
- Record a baseline KPI (minutes to healthy)

## IAM pain (today’s tax)

Every morning: Is Tomcat up? Is DB up? Did someone leave SPTARGET wrong? Did lab-data get wiped? The bootstrap skill is your first **time-back** automation.

## Claude concept

Skills should embed an **output contract** so agents cannot shrug:

```text
Return:
  overall: PASS|FAIL
  checks: [{name, result, evidence}]
  next_actions: [...]
```

## Before you start

- [ ] Day 04 checklist ready to lift  
- [ ] Lab can be started  

## Lab procedure

### Task 1 — Author the skill

Create `artifacts/skills/meridian-lab-bootstrap/SKILL.md` with:

- Description triggers: “lab health”, “is IIQ up”, “morning stack”, “Meridian bootstrap”
- Procedure: ports/login, HelloWorld smoke, SPTARGET, lab-data paths, optional Academy `:4173`
- Invariants: no DB drop; no `base/` edits; ask before `lab` reset scripts

### Task 2 — Install / link

Copy or symlink into `~/.claude/skills/meridian-lab-bootstrap/` (or project `.claude/skills/`). Confirm Claude lists/uses it.

### Task 3 — Cold start test

New session:

> Meridian lab bootstrap — full health check.

Approve probes. Save report under evidence.

### Task 4 — KPI

Time wall clock. Target: ≤5 minutes to PASS table on a warm lab, ≤15 including start.

## Deliverable

Installed skill + evidence report from one cold-start run.

## Acceptance criteria

- [ ] Skill file complete with verify output contract  
- [ ] Trigger works without pasting the whole checklist  
- [ ] KPI recorded in skill’s `reference.md` or playbook note  
- [ ] Fault-remediation points at `tools/lab` docs, not folklore

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Skill not found | Check skills directory path for your Claude Code version |
| Claude skips verify | Strengthen output contract + CLAUDE.md pointer |

## Stretch

- Add optional connectors compose health
- Personal skill wrapper that sets your absolute paths

## Knowledge check

1. Why ask before lab reset?  
2. What makes a bootstrap skill fail-closed vs chatty?  
3. Should bootstrap mutate config XML?

### Answers

1. Destructive / time-expensive.  
2. Explicit PASS/FAIL contract.  
3. No — diagnose only.

## Navigation

[← Day 08](day-08-skill-anatomy.md) · [Day 10 →](day-10-skill-export-tokenize.md)
