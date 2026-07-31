# Day 18 — Specialist Agents

| Field | Value |
| --- | --- |
| **Week** | 3 — Hooks + Agents |
| **Time** | 2.5–3 hours |
| **Prereq** | Week 2 skills catalog |
| **Artifacts** | `artifacts/agents/README.md` + first agent defs |

## Learning objectives

You will be able to:

- Explain when to use a **subagent** vs the main thread vs a skill
- Write a specialist agent prompt with mission, tools allowed, and output schema
- Keep agents narrow (XML reviewer ≠ onboard JDBC connector)
- Route IAM work: diagnose vs mutate vs document

## IAM pain (today’s tax)

One overloaded chat mixes CAB writing, BeanShell debugging, and shell builds — context thrashes and mistakes rise. Specialists mirror how IAM teams already split ops / governance / engineering.

## Claude concept

**Agents** = scoped workers with their own instructions (and often limited tools). Skills teach *how*; agents embed *role + constraints*.

```text
Main orchestrator
  ├─ agent: xml-reviewer (read-focused)
  ├─ agent: beanshell-auditor
  └─ agent: cert-campaign-assistant
```

| Use a skill | Use an agent |
| --- | --- |
| Repeatable procedure you invoke often | Parallel deep review / long research |
| Stateless checklist | Needs isolated context window |
| Single-thread co-pilot | Multiple workstreams at once |

## Before you start

- [ ] `artifacts/skills/INDEX.md` exists  
- [ ] Know how your runtime launches subagents (Claude Code Task/agents; Cursor Task tool)  

## Lab procedure

### Task 1 — Role map for Meridian Ops Desk

Define ≥4 agent roles in README with one-sentence missions.

Suggested: `iiq-xml-reviewer`, `beanshell-auditor`, `agg-diagnostician`, `cab-writer`.

### Task 2 — Author first agent def

`artifacts/agents/iiq-xml-reviewer.md`:

- Reads only `config/`, docs, properties  
- Must call hygiene checklist / export-tokenize skill concepts  
- Output: findings table; no importdynamic  

### Task 3 — Launch from main session

Give it a real XML. Compare quality vs main agent doing the same alone.

### Task 4 — Tool allowlisting notes

Document which agents may run shell vs read-only.

## Deliverable

Agents README + ≥2 agent definition files.

## Acceptance criteria

- [ ] Clear skill vs agent decision table  
- [ ] Two specialists written  
- [ ] One live subagent run with saved report  
- [ ] Mutating powers explicitly denied where appropriate  

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Agent duplicates skill text | Reference skill by name; don’t paste novel  
| Agent tries to deploy | Tighten tool permissions / prompt  

## Stretch

- Agent that only writes CAB markdown from findings  
- Resume agent ID pattern for long reviews  

## Knowledge check

1. Why isolate BeanShell audit?  
2. Can agents replace hooks?  
3. What is an output schema for?

### Answers

1. Dangerous language + different review criteria.  
2. No — hooks enforce; agents perform.  
3. Reliable handoff to humans/other agents.

## Navigation

[← Day 17](day-17-hooks-evidence-automation.md) · [Day 19 →](day-19-agent-xml-beanshell-review.md)
