# Day 15 — Hooks Fundamentals

| Field | Value |
| --- | --- |
| **Week** | 3 — Hooks + Agents |
| **Time** | 2.5–3 hours |
| **Prereq** | Day 03 allow/deny draft |
| **Artifacts** | `artifacts/hooks/README.md`, sample hook script |

## Learning objectives

You will be able to:

- Explain hook events (PreToolUse / PostToolUse / Stop / SessionStart — names vary by product)
- Write a minimal command hook that reads JSON stdin and returns allow/deny
- Distinguish observe vs block vs rewrite behaviors
- Place project hooks where the Meridian team can version them

## IAM pain (today’s tax)

Permissions prompts get click-fatigue; people Approve recklessly. Hooks encode policy once so the dangerous path fails closed even when humans are tired.

## Claude concept

**Hooks** are automated gates around agent tool use. For Meridian:

| Intent | Hook style |
| --- | --- |
| Block `base/ga` writes | PreToolUse / beforeShell — deny |
| Log every `build.sh` | PostToolUse — observe |
| Remind evidence folder | SessionStart / Stop — inject message |
| Format XML after edit | afterFileEdit — careful, optional |

Claude Code and Cursor have related but not identical schemas. Today: learn the **pattern**; store portable scripts under `artifacts/hooks/` and adapt to your runtime’s `settings` / `hooks.json`.

```text
Tool call requested
    → Pre hook (may deny)
    → Tool executes
    → Post hook (may log / follow up)
```

## Before you start

- [ ] Day 03 draft available  
- [ ] Decide Claude Code vs Cursor hooks for implementation (document choice in README)  

## Lab procedure

### Task 1 — Map event names for your runtime

Write a table in `artifacts/hooks/README.md`: Event | Runtime name | Meridian use.

### Task 2 — Hello-deny hook

Create a script that denies any command/path containing `base/ga` or `identityiq-8.5.zip` write attempts. Test with a dry-run prompt asking Claude to delete that zip — must fail.

### Task 3 — Hello-observe hook

Log `./build.sh` invocations with timestamp to `~/iiq-lab-evidence/hooks.log`.

### Task 4 — Failure policy

Document fail-open vs fail-closed choice for each hook (IAM default: **fail closed** on deny hooks).

## Deliverable

`artifacts/hooks/README.md` + `block-base-ga.sh` (or equivalent) + log observer.

## Acceptance criteria

- [ ] At least one deny hook proven in a live agent session  
- [ ] At least one observe hook writes a log line  
- [ ] Runtime event names documented  
- [ ] No hooks silently swallow errors without notes  

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Hook not firing | Path in settings wrong; matcher too narrow |
| Everything denied | Matcher too greedy — tighten patterns |
| JSON parse errors | Validate stdin schema for your runtime |

## Stretch

- Port the same policy to the other runtime (Cursor ↔ Claude Code)  
- Add unit-testable pure function for path deny logic  

## Knowledge check

1. Deny vs observe — which for secrets?  
2. Why version hooks in git for Meridian?  
3. What is fail-closed?

### Answers

1. Deny (and never log secret values).  
2. Shared bank controls — not laptop folklore.  
3. If hook errors, block the action rather than allow.

## Navigation

[← Day 14](day-14-skill-catalog-and-eval.md) · [Day 16 →](day-16-hooks-iiq-guardrails.md)
