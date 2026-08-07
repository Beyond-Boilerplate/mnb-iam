# Day 16 — IIQ Guardrail Hooks

| Field | Value |
| --- | --- |
| **Week** | 3 — Hooks + Agents |
| **Time** | 2.5–3.5 hours |
| **Prereq** | Day 15 |
| **Artifacts** | `artifacts/hooks/iiq-guardrails/` |

## Learning objectives

You will be able to:

- Implement a Meridian guardrail pack: `base/`, secrets patterns, reckless git, prod SPTARGET
- Use matchers so hooks don’t slow every `ls`
- Emit human-readable deny reasons agents (and you) can learn from
- Align hooks with Day 03 policy document

## IAM pain (today’s tax)

The landmines are known — people still hit them. Guardrails are how mature IAM platforms survive staff rotation.

## Claude concept

**Matcher-scoped hooks** only run when tool input matches (e.g., Bash command contains `git`, or Write path under `base/`).

Minimum Meridian pack:

1. **block-base-ga** — writes under `base/`  
2. **block-secret-files** — `*.iiq.properties` password lines, `.env`, key files  
3. **warn-prod-target** — `SPTARGET=prod` or `prod.target.properties` edits from laptop sessions  
4. **ask-force-git** — `push --force`, `reset --hard`  

## Before you start

- [ ] Deny hook from Day 15 working  
- [ ] Copy Day 03 draft into this folder as `POLICY.md`  

## Lab procedure

### Task 1 — Implement pack

Scripts + config snippet checked into `artifacts/hooks/iiq-guardrails/`.

### Task 2 — Red team

Ask Claude (separate prompts) to violate each rule. All must block or escalate.

### Task 3 — False positive hunt

Run normal `./build.sh clean war` — must still work (Ask is OK; Deny is not).

### Task 4 — Team README

How to install on a new laptop in <10 minutes.

## Deliverable

Installable guardrail pack with POLICY.md and test notes `REDTEAM.md`.

## Acceptance criteria

- [ ] ≥4 rules implemented  
- [ ] Red team shows block/ask for each  
- [ ] Normal SSB loop still completable  
- [ ] Deny messages mention Meridian rationale  

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Build blocked | Exclude read-only or allowlist `./build.sh` with Ask  
| Properties blocked on read | Match Write/Edit only, not Read  

## Stretch

- Hook that blocks commits of `build/` artifacts  
- Prompt injection sticky notes in CLAUDE.md referencing hooks  

## Knowledge check

1. Why warn on prod SPTARGET in a learning laptop?  
2. Should hooks modify secrets to redact in logs?  
3. Name one false-positive risk.

### Answers

1. Habit + property misuse → accidental prod-shaped actions.  
2. Prefer never logging secrets; redact if you must.  
3. Over-broad `prod` string matching in docs paths.

## Navigation

[← Day 15](day-15-hooks-fundamentals.md) · [Day 17 →](day-17-hooks-evidence-automation.md)
