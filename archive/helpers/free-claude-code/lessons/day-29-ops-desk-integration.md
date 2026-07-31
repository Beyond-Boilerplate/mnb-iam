# Day 29 — Ops Desk Integration

| Field | Value |
| --- | --- |
| **Week** | 4 — MCPs + Capstone |
| **Time** | 3–4 hours |
| **Prereq** | Days 01–28 artifacts |
| **Artifacts** | `artifacts/OPS-DESK.md` |

## Learning objectives

You will be able to:

- Assemble the Meridian **IAM Ops Desk** one-pager: how to run everything
- Resolve path inconsistencies (draft artifacts vs installed skills/hooks)
- Smoke-test the desk: health → triage → verify → CAB stub
- File a gap backlog for post–Day 30 (without expanding scope)

## IAM pain (today’s tax)

Tools that only exist in chat history don’t reduce friction tomorrow. Integration day is packaging.

## Claude concept

Ops Desk is a **control surface**:

```text
OPS-DESK.md
  ├─ Start here (cc + SPTARGET + lab up)
  ├─ Skills index
  ├─ Agents index
  ├─ Hooks install
  ├─ MCP status
  ├─ On-call playbooks
  └─ CAB / verify
```

If it’s not linked from OPS-DESK.md, it doesn’t exist for on-call.

## Before you start

- [ ] All weekly caps exist (Week1 pack, skills INDEX, hooks pack, orchestrator, glue)  

## Lab procedure

### Task 1 — Write OPS-DESK.md

### Task 2 — Install consistency pass

Copy/symlink drafts into live Claude skill/hook locations; document versions.

### Task 3 — Integration smoke (60–90 min)

Run: lab bootstrap → inject mild fault → triage skill → verify bridge → CAB stub.

### Task 4 — Backlog

`artifacts/BACKLOG.md` with frozen non-goals (avoid infinite build).

## Deliverable

`OPS-DESK.md` + smoke evidence + backlog.

## Acceptance criteria

- [ ] Desk is the only entry doc you need  
- [ ] Smoke path completes or fails with known backlog only  
- [ ] Install paths documented for a fresh laptop  
- [ ] progress.md Days 01–28 checked as honestly done  

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Too many drafts | Promote only eval-passed skills |
| Conflicting instructions | CLAUDE.md wins for repo; skills for procedures |

## Stretch

- Screen recording outline for Day 30  
- Cursor port checklist  

## Knowledge check

1. What’s the entry doc?  
2. Why backlog freezes scope?  
3. Name the smoke path stages.

### Answers

1. `OPS-DESK.md`.  
2. Mastery requires stopping to demo.  
3. Health → triage → verify → CAB stub.

## Navigation

[← Day 28](day-28-promotion-cab-automation.md) · [Day 30 →](day-30-capstone-demo-and-retro.md)
