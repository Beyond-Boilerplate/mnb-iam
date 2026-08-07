# Day 27 — On-Call Playbooks

| Field | Value |
| --- | --- |
| **Week** | 4 — MCPs + Capstone |
| **Time** | 2.5–3 hours |
| **Prereq** | Day 26 glue |
| **Artifacts** | `artifacts/playbooks/oncall/` |

## Learning objectives

You will be able to:

- Convert Meridian incident types into prompt packs with severity
- Drill orphan/dormant, failed aggregation, stuck provisioning, emergency leaver
- Timebox on-call responses with exit criteria
- Keep page-driven work from disabling hooks “for speed”

## IAM pain (today’s tax)

2am pages reward panic. Playbooks + agents reward procedure. Your binder becomes muscle memory.

## Claude concept

Each playbook file:

```markdown
# SEV / Title
Triggers:
Immediate human actions:
Agent/skill chain:
Do-not-do:
Exit criteria:
Evidence:
```

Severities: SEV1 emergency leaver / break-glass abuse suspicion; SEV2 agg down for HR; SEV3 cert stall.

## Before you start

- [ ] Skim Lessons 20, 34, 37, 47 themes  
- [ ] Glue doc available  

## Lab procedure

### Task 1 — Write four playbooks

1. HR aggregation down  
2. Emergency leaver  
3. Provisioning stuck on wire app  
4. Orphan/dormant hunt starter  

### Task 2 — Timed drill

Pick one SEV1/SEV2; execute with Claude under 30 minutes to “stable plan + evidence started.”

### Task 3 — Hook stress

Confirm you did **not** disable guardrails during drill.

### Task 4 — Index

`artifacts/playbooks/oncall/README.md` listing playbooks and owners.

## Deliverable

≥4 playbooks + drill notes.

## Acceptance criteria

- [ ] Four playbooks with exit criteria  
- [ ] One timed drill recorded  
- [ ] Hooks stayed on  
- [ ] Links to skills/agents/MCPs concrete  

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Playbook too long | One screen immediate actions; details linked |
| Claude improvises deletes | Bold do-not-do section |

## Stretch

- Tabletop with a peer  
- Add SEV for SoD spike after role change  

## Knowledge check

1. Why exit criteria?  
2. SEV1 first principle?  
3. Are playbooks skills?

### Answers

1. Know when to stop / escalate.  
2. Contain high-risk access with audit.  
3. Playbooks may invoke skills — they’re the ops UI.

## Navigation

[← Day 26](day-26-compose-skill-hook-mcp.md) · [Day 28 →](day-28-promotion-cab-automation.md)
