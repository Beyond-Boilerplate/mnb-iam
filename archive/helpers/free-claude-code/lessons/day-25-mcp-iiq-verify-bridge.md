# Day 25 — IIQ Verify MCP (Custom Bridge)

| Field | Value |
| --- | --- |
| **Week** | 4 — MCPs + Capstone |
| **Time** | 3–4 hours |
| **Prereq** | Day 07 verify experience; some Python comfort |
| **Artifacts** | `artifacts/mcp/iiq-verify/` |

## Learning objectives

You will be able to:

- Wrap `tools/iiq-verify/verify_lesson.py` / shell scripts as an MCP **or** a disciplined Claude skill+script facade
- Expose tools: `health`, `assert_smoke`, `verify_lesson(n)`
- Return structured JSON Claude can feed into orchestrator playbooks
- Keep credentials in env, not in server source

## IAM pain (today’s tax)

Verify exists but humans forget flags and URLs. Making verify a first-class tool ends “paste me the error” ping-pong.

## Claude concept

You may not need a full MCP on day one — a **thin wrapper** counts if Claude can call it reliably:

```text
Option A: MCP server exposing verify tools
Option B: skill that always runs ./tools/iiq-verify/... with fixed output schema
```

Prefer A if you want true MCP mastery; B acceptable if time-boxed — but design as if MCP.

Tool sketch:

| Tool | Args | Result |
| --- | --- | --- |
| `iiq_health` | base_url? | pass/fail + notes |
| `iiq_assert_smoke` | mode | assert script output |
| `iiq_verify_lesson` | lesson_no | report path + summary |

## Before you start

- [ ] Lab up  
- [ ] Read `docs/LESSON_VERIFY.md`  
- [ ] Decide A vs B and write it atop README  

## Lab procedure

### Task 1 — Spec the tool contract

JSON schemas for inputs/outputs in `artifacts/mcp/iiq-verify/SPEC.md`.

### Task 2 — Implement wrapper

Minimal Python or node MCP **or** shell wrappers + skill. Store under `artifacts/mcp/iiq-verify/`.

### Task 3 — Call from Claude

> Run iiq_verify_lesson for lesson 03 (or smoke). Summarize for auditor.

### Task 4 — Orchestrator integration

Update Day 21 playbook to call verify tools by name.

## Deliverable

Working verify bridge (MCP or skill+script) + SPEC + sample output.

## Acceptance criteria

- [ ] Spec written before code  
- [ ] At least `assert_smoke` or one lesson verify callable from Claude session  
- [ ] Credentials not hardcoded  
- [ ] Playbook updated  

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Auth fail | IIQ_USER/PASSWORD env  
| MCP SDK unknown | Use Option B; schedule full MCP later  
| Long timeouts | Increase timeout; check lab load |

## Stretch

- Add `list_lesson_specs` tool scanning `lesson-specs/`  
- Prometheus-style metric counter for verify runs (optional)

## Knowledge check

1. Why SPEC before code?  
2. Smoke vs lesson verify?  
3. Where do reports go?

### Answers

1. Contracts stabilize agents.  
2. Smoke = HelloWorld pack; lesson = curriculum acceptance.  
3. Evidence/verify paths per tool.

## Navigation

[← Day 24](day-24-mcp-github-pr-discipline.md) · [Day 26 →](day-26-compose-skill-hook-mcp.md)
