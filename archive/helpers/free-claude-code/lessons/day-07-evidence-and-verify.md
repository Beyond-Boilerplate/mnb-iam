# Day 07 — Evidence & Verify (Week 1 Cap)

| Field | Value |
| --- | --- |
| **Week** | 1 — Fluency |
| **Time** | 2–3 hours |
| **Prereq** | Days 01–06 |
| **Artifacts** | `artifacts/playbooks/week1-ops-pack.md` |

## Learning objectives

You will be able to:

- Run `./tools/iiq-verify/verify-lesson.sh` (or assert smoke) and interpret output
- Structure evidence folders the way Meridian lessons expect
- Combine health + SSB loop + hygiene into one “Week 1 Ops Pack”
- Define Week 2 skill candidates with measurable acceptance

## IAM pain (today’s tax)

Examiners and CAB chairs do not accept “trust me.” Screenshots without task result IDs, unverified lesson completion, and missing CHANGELOG entries create rework. Verification automation is the IAM engineer’s receipt printer.

## Claude concept

**Structured outputs as contracts.** Require Claude to produce:

1. Command run  
2. Exit code / key JSON fields  
3. Evidence path written  
4. Pass/fail vs acceptance  

This becomes the default for every later agent.

## Before you start

- [ ] Lab up  
- [ ] `docs/LESSON_VERIFY.md` skimmed  
- [ ] Pick a lesson number you have built (or `01`/`03` orientation + HelloWorld smoke)

## Lab procedure

### Task 1 — Evidence folder ritual

```bash
EVID=~/iiq-lab-evidence/$(date +%F)-week1
mkdir -p "$EVID"
```

Tell Claude this path is mandatory for today’s outputs.

### Task 2 — Verify CLI with co-pilot

```bash
./tools/iiq-verify/assert-mnb-objects.sh local
# and/or:
./tools/iiq-verify/verify-lesson.sh 03
```

Have Claude summarize the report for a fictional auditor in ≤12 lines.

### Task 3 — Assemble Week 1 Ops Pack

Merge into `artifacts/playbooks/week1-ops-pack.md`:

- Mental model (Day 01)
- CLAUDE.md IAM section pointer (Day 02)
- Allow/Ask/Deny (Day 03)
- Lab health checklist (Day 04)
- SSB loop (Day 05)
- XML hygiene (Day 06)
- Verify commands (Day 07)

### Task 4 — Skill backlog for Week 2

List 5 skills you will build Days 09–13 with trigger phrases and success metrics.

## Deliverable

`artifacts/playbooks/week1-ops-pack.md` + evidence dir with at least one verify output copied/saved.

## Acceptance criteria

- [ ] At least one verify/assert run captured in evidence
- [ ] Ops pack links or inlines prior day artifacts
- [ ] Skill backlog ≥5 with triggers
- [ ] You can demo Week 1 pack live in 10 minutes

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| verify needs credentials | Env `IIQ_USER` / `IIQ_PASSWORD` per tool docs |
| Spec missing for lesson | Use smoke assert; or generate specs if tooling provides |

## Stretch

- Add CHANGELOG template for MNB objects created this week
- Time an end-to-end “health → verify” run for baseline KPI

## Knowledge check

1. Where do verify JSON reports often land?  
2. Why is HelloWorld smoke not proof of Lesson 40 SoD?  
3. Name two Week 2 skills that remove the most daily friction for you.

### Answers

1. Under `~/iiq-lab-evidence/verify` (per `verify_lesson.py`) or your dated folder.  
2. CD smoke ≠ full academy object set.  
3. Personal — e.g. tokenize + aggregation triage.

## Navigation

[← Day 06](day-06-config-xml-hygiene.md) · [Day 08 →](day-08-skill-anatomy.md)
