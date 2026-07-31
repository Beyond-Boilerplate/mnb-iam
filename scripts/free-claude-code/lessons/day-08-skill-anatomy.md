# Day 08 — Skill Anatomy

| Field | Value |
| --- | --- |
| **Week** | 2 — Skills |
| **Time** | 2–2.5 hours |
| **Prereq** | Week 1 ops pack |
| **Artifacts** | `artifacts/skills/_template/SKILL.md` |

## Learning objectives

You will be able to:

- Explain personal vs project skills and when Meridian knowledge belongs in-repo
- Author a valid `SKILL.md` with YAML frontmatter (`name`, `description`)
- Write descriptions that **trigger** correctly (and avoid false triggers)
- Use progressive disclosure (`reference.md`, `scripts/`) without stuffing the main skill

## IAM pain (today’s tax)

Engineers retype the same 40-line prompt for “tokenize this Application export.” Skills turn tribal paste into a callable procedure — the IAM SOPs your future self needed yesterday.

## Claude concept

A **skill** is a directory with `SKILL.md` that teaches the agent a workflow. Design rules:

1. **One job** per skill  
2. **Description** = when to load (keywords the model matches)  
3. **Body** = steps, invariants, output contract  
4. **Heavy detail** → linked files only when needed  

Claude Code paths typically: `~/.claude/skills/` (personal) or `.claude/skills/` (project). This curriculum stores drafts in `lessons/artifacts/skills/` then you install/copy into the live skills root.

| Scope | Path (Claude Code) | Put Meridian SSB truth? |
| --- | --- | --- |
| Personal | `~/.claude/skills/...` | Lab preferences, your evidence habits |
| Project | `.claude/skills/...` (repo) | Naming, tokens, verify commands |
| Draft | `scripts/free-claude-code/lessons/artifacts/skills/` | Iteration before promoting |

## Before you start

- [ ] Week 1 pack exists  
- [ ] Know whether you use Claude Code CLI skills path (confirm with `/skills` or docs for your version)

## Lab procedure

### Task 1 — Study a good skill shape

Read any installed skill on your machine (or use the template you create next). Note: frontmatter description quality.

### Task 2 — Create the Meridian skill template

Write `artifacts/skills/_template/SKILL.md`:

```markdown
---
name: meridian-skill-template
description: >-
  Template only. Replace name/description. Use when creating a new Meridian IAM
  Claude skill for IdentityIQ SSB workflows.
---

# <Skill title>

## When to use
## Invariants (never violate)
## Inputs you must gather
## Procedure
## Output contract
## Verification
```

### Task 3 — Description clinic

For three backlog skills from Day 07, draft **only** the `description:` fields. Peer-critique with Claude:

> Which descriptions are too broad? Which miss trigger phrases an IAM engineer would say?

### Task 4 — Anti-patterns list

Add to template README notes: skills that say “helps with everything”; skills duplicating entire CLAUDE.md; skills without verify step.

## Deliverable

`artifacts/skills/_template/SKILL.md` (+ description clinic notes in `artifacts/skills/DESCRIPTION-CLINIC.md`)

## Acceptance criteria

- [ ] Valid frontmatter template  
- [ ] Three real descriptions drafted for upcoming skills  
- [ ] You can explain personal vs project placement for tokenize vs “my screenshot path”

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Skill never triggers | Tighten description with verbs + IIQ nouns |
| Skill always triggers | Narrow scope; remove vague words like “general help” |

## Stretch

- Compare Cursor skill format vs Claude Code — note 5 deltas

## Knowledge check

1. What two YAML fields are mandatory on most skill designs?  
2. Why progressive disclosure?  
3. Where should `%%TOKEN%%` rules live — personal or project skill?

### Answers

1. `name`, `description` (plus body).  
2. Save context; load depth only when executing.  
3. Project — team-shared Meridian truth.

## Navigation

[← Day 07](day-07-evidence-and-verify.md) · [Day 09 →](day-09-skill-lab-bootstrap.md)
