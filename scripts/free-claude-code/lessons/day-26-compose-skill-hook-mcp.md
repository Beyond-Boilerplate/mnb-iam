# Day 26 — Compose Skill + Hook + MCP

| Field | Value |
| --- | --- |
| **Week** | 4 — MCPs + Capstone |
| **Time** | 3 hours |
| **Prereq** | Days 09–25 artifacts exist |
| **Artifacts** | `artifacts/playbooks/full-stack-glue.md` |

## Learning objectives

You will be able to:

- Wire one vertical slice using all four primitives together
- Choose the right primitive at each stage (no duplicates)
- Prove fail-closed behavior when hooks deny + MCP still works for reads
- Document the architecture for Day 30 demo

## IAM pain (today’s tax)

Owning skills, hooks, agents, and MCPs separately still leaves swivel-chair work. Glue is the product.

## Claude concept

**Reference vertical — “Ticketed aggregation failure”:**

```text
1. Jira MCP      → read issue
2. Skill         → meridian-agg-triage (plan)
3. Shell/IIQ     → apply fix (human approve)
4. MCP verify    → assert / lesson check
5. Hook Stop     → evidence checklist
6. Agent cab     → write summary comment draft
7. Jira MCP      → gated comment post
```

Draw this in your glue doc with actual file paths you built.

## Before you start

- [ ] Pick one vertical only — depth over breadth  
- [ ] Hooks on  

## Lab procedure

### Task 1 — Architecture diagram

ASCII or mermaid in `full-stack-glue.md`.

### Task 2 — Execute the slice

Run end-to-end once (fixture Jira OK). Save transcript highlights / evidence paths.

### Task 3 — Failure injection

Deny a dangerous command mid-slice; confirm recovery path.

### Task 4 — Responsibility matrix

Table: Primitive | Owns | Does not own.

## Deliverable

`full-stack-glue.md` + evidence from one successful slice.

## Acceptance criteria

- [ ] All four primitives appear in the slice  
- [ ] Human gates labeled  
- [ ] Failure injection handled cleanly  
- [ ] Ready to demo in ≤15 minutes  

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Overlapping skill+agent | Assign one owner per stage |
| MCP write too early | Keep comment until verify PASS |

## Stretch

- Second slice: export-tokenize → PR review MCP  
- Metrics: stage timings  

## Knowledge check

1. Who enforces policy — skill or hook?  
2. When is MCP preferred over shell curl?  
3. What makes a vertical slice “done”?

### Answers

1. Hook enforces; skill teaches.  
2. When auth/session/tooling is standardized and safer.  
3. Verify PASS + evidence + documented handoff.

## Navigation

[← Day 25](day-25-mcp-iiq-verify-bridge.md) · [Day 27 →](day-27-oncall-playbooks.md)
