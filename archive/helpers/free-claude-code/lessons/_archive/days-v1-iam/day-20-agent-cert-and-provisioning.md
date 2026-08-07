# Day 20 — Cert + Provisioning Agents

| Field | Value |
| --- | --- |
| **Week** | 3 — Hooks + Agents |
| **Time** | 3–3.5 hours |
| **Prereq** | Skim Lessons 43–47 |
| **Artifacts** | `artifacts/agents/cert-campaign-assistant.md`, `prov-troubleshooter.md` |

## Learning objectives

You will be able to:

- Build a certification campaign assistant that prepares checklists (manager vs app-owner)
- Build a provisioning troubleshooter that walks Identity Request → Prov Plan → connector
- Keep both agents evidence-first and non-destructive by default
- Tie outputs to audit-ready reporting patterns (Lesson 48)

## IAM pain (today’s tax)

Cert kicks and provisioning tickets are interrupt-driven. Context switching loses the thread (which AccessRequest? which AccountRequest error?). Agents hold the breadcrumb trail.

## Claude concept

State the **investigation spine** in the agent prompt:

```text
Cert assistant:
  campaign type → population → certifiers → item samples → remediation path → evidence

Prov troubleshooter:
  IdentityRequest id → Approval → Provisioning plan → Integration/connector logs → retry posture
```

Never approve access or close cert items without human.

## Before you start

- [ ] Lab may have partial cert objects — agent must handle “not built yet”  
- [ ] Aggregation triage skill available for connector-layer handoff  

## Lab procedure

### Task 1 — Author cert-campaign-assistant

Include Meridian campaign types (manager, app owner, targeted). Checklist for kickoff and mid-campaign stall.

### Task 2 — Author prov-troubleshooter

Ordered probes; when to bounce to agg-triage skill; when to suspect policy/SoD blocking.

### Task 3 — Tabletop exercises

Without live fail: feed agents fictional but realistic failure narratives (timeout, missing entitlement, IQService down). Score their plans.

### Task 4 — Live probe (optional)

If you have requests in lab, run read-only investigation.

## Deliverable

Two agent defs + `artifacts/agents/reports/tabletop-cert-prov.md`.

## Acceptance criteria

- [ ] Both agents have explicit human gates  
- [ ] Tabletop produces actionable ordered steps  
- [ ] Handoffs to existing skills named  
- [ ] Audit evidence section present  

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Agent invents UI clicks wrongly | Prefer “or equivalent path” + docs/lessons links |
| Jumps to rebuild connector | Force spine order in prompt |

## Stretch

- Break-glass scenario (Lesson 37) as cert exception path  
- Email template reminders (Lesson 49) as appendix  

## Knowledge check

1. Why human gate on cert remediation?  
2. Prov vs aggregation failure — first fork question?  
3. What evidence satisfies an examiner mid-campaign?

### Answers

1. Access decisions are control ownership.  
2. Did account aggregation succeed / entitlement exist?  
3. Campaign config, population, sample decisions, remediation tickets.

## Navigation

[← Day 19](day-19-agent-xml-beanshell-review.md) · [Day 21 →](day-21-agent-teams-orchestration.md)
