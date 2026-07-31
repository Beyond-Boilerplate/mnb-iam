# Day 21 — Agent Teams Orchestration (Week 3 Cap)

| Field | Value |
| --- | --- |
| **Week** | 3 — Hooks + Agents |
| **Time** | 3 hours |
| **Prereq** | Days 15–20 |
| **Artifacts** | `artifacts/agents/orchestrator-playbook.md` |

## Learning objectives

You will be able to:

- Orchestrate a multi-agent flow: investigate → review → verify → document
- Use resumable agents / handoff notes
- Combine hooks + agents so mutants stay guarded
- Dry-run a full “incident” on a Meridian scenario end-to-end

## IAM pain (today’s tax)

Real incidents need multiple specialists without dropping context. Your orchestrator playbook becomes the Ops Desk brain.

## Claude concept

```text
Trigger (user or Jira later)
  → bootstrap skill (health)
  → diagnostic agent (agg/prov/cert)
  → parallel reviewers if code/XML change
  → verify scripts
  → cab-writer agent
  → Stop hook evidence checklist
```

Write this as a playbook with **inputs/outputs per stage**.

## Before you start

- [ ] Guardrails hooks on  
- [ ] Skills INDEX current  
- [ ] Pick incident scenario: e.g. “Aggregate MNB-HR failed after path change” or “leaver incomplete”  

## Lab procedure

### Task 1 — Draft orchestrator playbook

Stages, owners (which agent/skill), exit criteria, rollback.

### Task 2 — Execute tabletop or live

Run the chain once. Record where humans intervened.

### Task 3 — Retro

What stage was slow? What hallucination occurred? Update agent prompts.

### Task 4 — Week 4 preview

Mark which stages need MCP data (ticket fields, PR diffs, verify API).

## Deliverable

`orchestrator-playbook.md` + one run log under `artifacts/agents/reports/`.

## Acceptance criteria

- [ ] Playbook covers investigate→verify→document  
- [ ] Hooks remained active during run  
- [ ] Retro has ≥3 concrete prompt/skill edits  
- [ ] Clear MCP wishlist for Days 22–25  

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Context loss between agents | Mandatory handoff JSON schema |
| Endless loops | Max stage retries = 1 without new evidence |

## Stretch

- Time the full chain; set SLO (e.g. triage pack in 20 minutes)  
- Add subagentStop hook to chain next stage (advanced)  

## Knowledge check

1. Orchestrator vs specialist — who mutates IIQ?  
2. Why exit criteria per stage?  
3. Name one Week 4 MCP that removes a handoff pain.

### Answers

1. Orchestrator decides; specialists recommend; human/gated tools mutate.  
2. Prevent silent half-done work.  
3. Jira or iiq-verify MCP.

## Navigation

[← Day 20](day-20-agent-cert-and-provisioning.md) · [Day 22 →](day-22-mcp-fundamentals.md)
