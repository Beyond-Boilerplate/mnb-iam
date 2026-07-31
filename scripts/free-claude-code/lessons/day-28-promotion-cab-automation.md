# Day 28 — Promotion / CAB Automation

| Field | Value |
| --- | --- |
| **Week** | 4 — MCPs + Capstone |
| **Time** | 3 hours |
| **Prereq** | Days 10, 12, 24; skim Lessons 101 & 108 |
| **Artifacts** | `artifacts/playbooks/cab-pack.md` |

## Learning objectives

You will be able to:

- Generate a CAB pack from config diffs: risk, rollback, verify plan, token impact
- Compare sandbox vs dev/prod property overlays with Claude
- Refuse “promote everything” — require scoped object lists
- Align with SSB promotion discipline (export → tokenize → importdynamic)

## IAM pain (today’s tax)

Promotion anxiety causes shadow-IT UI clicks in higher envs. Automated CAB packs make the git path the path of least resistance.

## Claude concept

CAB pack template sections:

1. Change summary (business)  
2. Objects touched (`MNB-*` list)  
3. Token/property deltas by env  
4. Risk & SoD impact  
5. Test evidence (verify outputs)  
6. Rollback (previous XML / ignore)  
7. Approvers  

Agent/skills: tokenize + sod-review + xml-reviewer + github PR template.

## Before you start

- [ ] A real or simulated change set under `config/`  
- [ ] Property files for ≥2 targets available to read  

## Lab procedure

### Task 1 — Author cab-pack.md template

### Task 2 — Generate a pack for a sample change

Use Claude + skills/agents; no silent prod deploy.

### Task 3 — Multi-env property review

Table of tokens differing across sandbox/dev/prod.

### Task 4 — Dry-run promo checklist

List commands per env with `SPTARGET` — execute only sandbox unless you truly have lower non-prod.

## Deliverable

Filled CAB pack example + template.

## Acceptance criteria

- [ ] Template reusable  
- [ ] One filled example with object list  
- [ ] Token delta table present  
- [ ] Explicit “no prod from this curriculum without change ticket”  

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Claude wants to deploy prod | Hooks + prompt invariant |
| Missing exports | Point to Lesson 101 workflow |

## Stretch

- Auto-attach verify JSON paths into CAB pack  
- Map to Jira approval custom fields  

## Knowledge check

1. Why object lists beat “misc fixes”?  
2. What does Lesson 108 add beyond 101?  
3. Rollback unit?

### Answers

1. Auditable, bisectable, approvable.  
2. Multi-env maturity / promotion at scale.  
3. Prior git versions of XML + re-import.

## Navigation

[← Day 27](day-27-oncall-playbooks.md) · [Day 29 →](day-29-ops-desk-integration.md)
