# Day 11 — Skill: Aggregation Triage

| Field | Value |
| --- | --- |
| **Week** | 2 — Skills |
| **Time** | 2.5–3.5 hours |
| **Prereq** | Lab with at least one Application (Lesson 04+ ideal) |
| **Artifacts** | `artifacts/skills/meridian-agg-triage/SKILL.md` |

## Learning objectives

You will be able to:

- Build a diagnostic skill for Account Aggregation failures
- Separate connector symptoms (file missing, schema mismatch) from IIQ task misconfig
- Produce an ordered runbook: task result → app debug → file/path → schema → correlation later
- Capture evidence automatically in the skill’s output contract

## IAM pain (today’s tax)

“Aggregation failed” Slack messages burn hours. Juniors randomly re-run tasks; seniors follow a tree. Encode the senior tree.

## Claude concept

**Decision trees in skills** beat free-form chat:

```text
Task result error?
  ├─ file/path → check %% tokens / ~/iiq-lab-data
  ├─ schema/parse → headers vs app schema
  ├─ auth/connect → connector secrets / IQService (later lessons)
  └─ success but 0 accounts → filter, empty file, wrong delimiter
```

Do not jump to correlation (Lessons 17+) until accounts exist.

## Before you start

- [ ] Prefer a Delimited File app you know (`MNB-HR` if built)  
- [ ] Intentionally break something safe (rename CSV path) for a drill  

## Lab procedure

### Task 1 — Author triage skill

Include Meridian-specific commands: where task results live in UI; how to open Application debug; remind absolute paths (Lesson 03).

### Task 2 — Controlled failure drill

Break file path → run Aggregate → invoke skill → confirm it finds path issue before inventing connector bugs.

### Task 3 — Restore and confirm PASS path

Fix, re-agg, skill should report healthy account counts / next checks.

### Task 4 — Add “what not to do”

Skill must forbid: deleting Application, disabling prod-like schedules, schema wipe without backup export.

## Deliverable

Skill + `artifacts/skills/meridian-agg-triage/DRILL-NOTES.md` with failure and recovery.

## Acceptance criteria

- [ ] Drill correctly diagnosed injected path fault  
- [ ] Decision tree documented in skill or reference  
- [ ] Output includes evidence paths / screenshots checklist  
- [ ] No unauthorized destructive fixes

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| No app built yet | Use docs/lessons/04 to create HR app first (stretch time OK) |
| Claude blames correlation early | Strengthen skill: accounts first |

## Stretch

- Extend tree for JDBC/LDAP later (link Lessons 56+)  
- Log KPI: median time-to-diagnosis over 3 drills

## Knowledge check

1. Why absolute paths matter for Delimited File?  
2. Empty success vs failed task — which check first?  
3. When does aggregation triage hand off to correlation skill?

### Answers

1. Tomcat cwd ≠ shell cwd.  
2. Open task result / account count before deeper theories.  
3. After accounts exist but identities don’t link.

## Navigation

[← Day 10](day-10-skill-export-tokenize.md) · [Day 12 →](day-12-skill-sod-and-policy-review.md)
