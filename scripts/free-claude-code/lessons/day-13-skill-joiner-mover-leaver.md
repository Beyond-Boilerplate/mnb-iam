# Day 13 — Skill: Joiner / Mover / Leaver Ticket Pack

| Field | Value |
| --- | --- |
| **Week** | 2 — Skills |
| **Time** | 3 hours |
| **Prereq** | Lessons 29–34 concepts skimmed |
| **Artifacts** | `artifacts/skills/meridian-jml-pack/SKILL.md` |

## Learning objectives

You will be able to:

- Build a multi-mode skill (joiner | mover | leaver | rapid offboarding)
- Generate identity-centric checklists tied to Meridian personas
- Attach verify steps (identity cube attrs, role assignment, disablement)
- Prepare inputs later wired to Jira MCP (Day 23)

## IAM pain (today’s tax)

JML tickets arrive incomplete: missing manager, wrong effective date, apps unknown. Engineers chase Slack. A ticket pack skill invents structure and evidence expectations up front.

## Claude concept

**Parameterized skills**:

```text
inputs: { mode, identity, effectiveDate, ticketId }
modes: joiner | mover | leaver | emergency-leaver
```

Use `scripts/` only if helpful (e.g., render markdown from JSON). Keep BeanShell out unless reviewing existing workflows.

## Before you start

- [ ] Pick personas: `nina.joiner`, transfer candidate, `sofia.torres` LOA/leave themes as needed  
- [ ] Know which LCM objects exist in your lab (may be partial — skill still outputs plan)  

## Lab procedure

### Task 1 — Author multi-mode skill

Each mode: required data, IIQ objects to inspect (triggers, workflows, roles), evidence screenshots, rollback notes.

Emergency leaver references Lesson 34 drill discipline.

### Task 2 — Simulate three tickets

Run joiner, mover, leaver prompts. Save packs under `artifacts/playbooks/jml-samples/`.

### Task 3 — Lab validation (as available)

For any identity that exists, execute non-destructive verify steps the skill lists; mark gaps honestly.

### Task 4 — Interface stub for Jira

Add section “MCP fields to pull” (summary, assignee, custom effective date) — implemented Week 4.

## Deliverable

Skill + three sample ticket packs.

## Acceptance criteria

- [ ] Four modes documented (including emergency)  
- [ ] Samples don’t assume CD pre-created all LCM objects  
- [ ] Output is actionable under partial lab state  
- [ ] Clear human gates before provisioning changes

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| No LCM built | Skill produces build-from-lessons backlog linking 29–34 |
| Over-automation urge | Keep approve gates in skill invariants |

## Stretch

- Rapid offboarding timed drill with evidence folder  
- Birthright role checklist cross-link Lesson 24  

## Knowledge check

1. Joiner vs birthright — how does the skill keep them distinct?  
2. What must emergency leaver prioritize first?  
3. Why stub Jira fields before MCP day?

### Answers

1. Birthright = automatic role packages; joiner = lifecycle process orchestrating many steps.  
2. Disable/revoke high-risk access with audit trail.  
3. So MCP mapping is designed, not improvised.

## Navigation

[← Day 12](day-12-skill-sod-and-policy-review.md) · [Day 14 →](day-14-skill-catalog-and-eval.md)
