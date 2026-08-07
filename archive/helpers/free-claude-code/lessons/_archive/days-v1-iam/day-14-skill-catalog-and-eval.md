# Day 14 — Skill Catalog & Eval (Week 2 Cap)

| Field | Value |
| --- | --- |
| **Week** | 2 — Skills |
| **Time** | 2–3 hours |
| **Prereq** | Days 08–13 skills drafted |
| **Artifacts** | `artifacts/skills/INDEX.md` |

## Learning objectives

You will be able to:

- Catalog all Meridian skills with trigger phrases and owners
- A/B test prompts with vs without skills
- Retire or merge overlapping skills
- Define quality bar for Week 3–4 consumers (hooks/agents/MCPs)

## IAM pain (today’s tax)

Skill sprawl mirrors IIQ object sprawl: nobody knows what exists, duplicates conflict, trust collapses. Catalog + eval is IAM CMDB thinking applied to agents.

## Claude concept

**Eval harness (lightweight):**

| Scenario | Prompt | Expect skill | Pass criteria |
| --- | --- | --- | --- |
| Morning | “is meridian lab up?” | lab-bootstrap | PASS table |
| Export | “tokenize this Application XML” | export-tokenize | tokens+properties plan |
| Agg | “Aggregate MNB-HR failed” | agg-triage | ordered tree |
| SoD | “CAB review this policy” | sod-review | matrix grounded |
| JML | “leaver pack for helen.ross” | jml-pack | mode checklist |

Run each twice: skill available vs forced general chat. Note quality delta.

## Before you start

- [ ] Skills from Days 09–13 present under artifacts (and installed if possible)  

## Lab procedure

### Task 1 — Build INDEX.md

Table: name | path | triggers | inputs | verify | status (draft/prod)

### Task 2 — Run eval harness

Document results in `artifacts/skills/EVAL.md`.

### Task 3 — Consolidation pass

Merge near-duplicates; fix noisy descriptions; mark one skill deferred if low value.

### Task 4 — Week 3 briefing

Write 10 lines: which skills hooks should invoke reminders for; which agents will wrap skills.

## Deliverable

`INDEX.md` + `EVAL.md`

## Acceptance criteria

- [ ] All Week 2 skills listed  
- [ ] ≥3 eval scenarios recorded with pass/fail  
- [ ] At least one description improved from eval learnings  
- [ ] Clear backlog for unused ideas (don’t build yet)

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Skill never triggers in eval | Description clinic from Day 08  
| Skills conflict | Narrow descriptions; rename  

## Stretch

- Add CI idea: lint SKILL.md frontmatter with a tiny script  
- Port one skill to Cursor `.cursor/skills` as comparison  

## Knowledge check

1. Why eval with and without skills?  
2. What belongs in INDEX vs SKILL body?  
3. When is “draft” better than “prod”?

### Answers

1. Prove skills add value, not just folklore.  
2. INDEX = discovery metadata; body = procedure.  
3. Until eval passes and blast radius understood.

## Navigation

[← Day 13](day-13-skill-joiner-mover-leaver.md) · [Day 15 →](day-15-hooks-fundamentals.md)
