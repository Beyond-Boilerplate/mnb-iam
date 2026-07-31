# Day 12 — Skill: SoD & Policy Review

| Field | Value |
| --- | --- |
| **Week** | 2 — Skills |
| **Time** | 2.5–3 hours |
| **Prereq** | Familiarity with Lessons 39–41 concepts (or read them) |
| **Artifacts** | `artifacts/skills/meridian-sod-review/SKILL.md` |

## Learning objectives

You will be able to:

- Encode a policy/SoD XML review skill tuned for Meridian dual-control examples
- Check compensating controls language, ownership, and violation workflows
- Produce CAB-ready findings (Severity | Control gap | Fix)
- Avoid “LLM invents bank policy” — require sources (`lab-data/reference/sod-matrix.csv`, lesson text)

## IAM pain (today’s tax)

SoD mistakes are exam findings. Engineers eyeball Policy XML and miss inverted entitlements or missing mitigation. A review skill that cites Meridian matrix rows beats vibes.

## Claude concept

**Grounded review skills** must list allowed sources:

1. Policy XML under review  
2. `lab-data/reference/sod-matrix.csv`  
3. Related Bundle names  
4. Explicit “unknown — ask human” when matrix silent  

## Before you start

- [ ] Open `lab-data/reference/sod-matrix.csv`  
- [ ] Skim `docs/lessons/39-sod-fundamentals.md` and `40-payment-dual-control-policy.md`  
- [ ] Policy XML if you built one; else use lesson examples as markdown inputs  

## Lab procedure

### Task 1 — Author skill

Triggers: “SoD review”, “policy XML CAB”, “dual control wire”, `MNB-SOD`.

Checklist sections: conflicting entitlements correct?; policy type; orphan entitlements; workgroup owners; notification templates referenced.

### Task 2 — Grounding drill

Feed skill a mistaken policy description (swap entitlements). Confirm it flags against sod-matrix.

### Task 3 — CAB blurb generator

Output contract includes a 5-line CAB summary a non-IIQ approver can read.

### Task 4 — Ethics note

Skill forbids weakening SoD “to make demo green” without explicit human override logged in evidence.

## Deliverable

Skill + one sample review report in `artifacts/skills/meridian-sod-review/examples/`.

## Acceptance criteria

- [ ] Matrix cited in procedure  
- [ ] Invented policy rules rejected by skill instructions  
- [ ] Sample report has severity + CAB blurb  
- [ ] Works on XML or structured pasted definitions

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| No Policy in lab yet | Use lesson sample text; still build skill |
| Claude hallucinates FFIEC cites | Require link or “unverified” label |

## Stretch

- Cross-link risk scores lesson (42) as optional second pass  
- Add mitigation workflow questions from Lesson 41

## Knowledge check

1. Why ground in sod-matrix.csv?  
2. What’s a compensating control in one sentence?  
3. Should the skill auto-import Policy XML?

### Answers

1. Bank-specific truth > model memory.  
2. Alternate control reducing residual risk when SoD conflict must exist temporarily.  
3. No — review & propose only until human approves.

## Navigation

[← Day 11](day-11-skill-aggregation-triage.md) · [Day 13 →](day-13-skill-joiner-mover-leaver.md)
