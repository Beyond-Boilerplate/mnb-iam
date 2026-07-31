# Day 19 — XML + BeanShell Review Agents

| Field | Value |
| --- | --- |
| **Week** | 3 — Hooks + Agents |
| **Time** | 3–3.5 hours |
| **Prereq** | Day 18; skim Lessons 89–92 |
| **Artifacts** | `artifacts/agents/beanshell-auditor.md`, dual-run report |

## Learning objectives

You will be able to:

- Run **parallel** reviewers: XML hygiene + BeanShell safety
- Encode BeanShell anti-patterns (unbounded queries, swallowed exceptions, plaintext secrets)
- Merge findings into one severity-ordered report for CAB
- Keep reviewers from “fixing” production logic without tests

## IAM pain (today’s tax)

Rules ship with subtle bugs that surface only under mover volume or SoD storms. Manual review misses concurrency and logging sins. Dual agents approximate senior+peer review.

## Claude concept

**Fan-out / fan-in**:

```text
Main
  ├─ Task A: iiq-xml-reviewer → findings-A
  └─ Task B: beanshell-auditor → findings-B
Main merges → CAB pack
```

BeanShell auditor invariants:

- Prefer `context.search` with filters over loading all identities  
- No credentials in source  
- Log identity ids carefully (PII policy)  
- Call out deprecated APIs if docs known  

## Before you start

- [ ] At least one Rule XML or lesson sample  
- [ ] Hooks still protecting `base/`  

## Lab procedure

### Task 1 — Author beanshell-auditor agent

Include references to Lessons 90–92 themes; require citations to code lines.

### Task 2 — Parallel review drill

Launch both agents on the same change set (Rule + related Application if any).

### Task 3 — Merge report

Main agent produces `artifacts/agents/reports/YYYY-MM-DD-dual-review.md` with deduped findings.

### Task 4 — Human adjudication

Mark each finding: fix now / defer / false positive — train your taste.

## Deliverable

Two agent defs + one merged report.

## Acceptance criteria

- [ ] Parallel run completed  
- [ ] BeanShell agent flags at least one intentional issue you planted OR cleanly reports none with rationale  
- [ ] Merge doesn’t double-count  
- [ ] No auto-import after review  

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Agents rewrite code unasked | “Findings only” in prompts  
| No BeanShell in lab | Use docs lesson sample snippets in artifacts  

## Stretch

- Add third agent: workflow LCM skim (Lesson 93)  
- Mutation idea: introduce a secret string and confirm catch  

## Knowledge check

1. Why fan-out for reviews?  
2. Name two BeanShell anti-patterns.  
3. Who is accountable for accepting false positives?

### Answers

1. Parallelism + cleaner context.  
2. e.g., load-all identities; empty catch; secrets in code.  
3. You (the engineer) — agents advise.

## Navigation

[← Day 18](day-18-agents-specialists.md) · [Day 20 →](day-20-agent-cert-and-provisioning.md)
