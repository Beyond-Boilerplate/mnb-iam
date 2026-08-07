---
name: skill-template
description: >-
  Template only — replace name and description before use. Describe the exact
  situations and trigger phrases that should load this skill, not a vague summary.
---

# <Skill title — one job, stated plainly>

## When to use

- `<trigger situation 1 — what the user says or what state the repo is in>`
- `<trigger situation 2>`
- Not for: `<explicitly say what this skill is NOT for, to prevent false triggers>`

## Invariants (never violate)

- `<a rule that must always hold, regardless of input>`
- `<a rule that protects against a destructive or irreversible action>`

## Inputs you must gather

| Input | Required | Notes |
| --- | --- | --- |
| `<input>` | yes/no | `<how to get it if the user didn't provide it>` |

## Procedure

1. `<step — keep steps imperative and checkable>`
2. `<step>`
3. `<step>`

> **Token note:** if this skill's body grows past ~1 page, move detail into
> `reference.md` (see below) and load it only when the procedure actually needs it.
> Every line here loads on every trigger, whether the current task needs it or not.

## Progressive disclosure

For anything beyond the core procedure — edge cases, long examples, a schema, a full
API reference — put it in a sibling file and link it, instead of inlining it here:

```text
_template/
  SKILL.md         # short: when/invariants/procedure/output contract
  reference.md      # long: edge cases, schemas, worked examples
  scripts/          # optional: helper scripts the procedure shells out to
```

Reference [`reference.md`](reference.md) only when the current task needs the deep
detail — don't make Claude read it every time this skill loads.

## Output contract

```text
status: PASS|FAIL|NEED_HUMAN
summary: <one or two sentences>
evidence: [<what you checked/ran to support the summary>]
next_actions: [<if FAIL or NEED_HUMAN, what should happen next>]
```

## Verification

`<commands or checks that prove the procedure actually worked, not just that it ran>`
