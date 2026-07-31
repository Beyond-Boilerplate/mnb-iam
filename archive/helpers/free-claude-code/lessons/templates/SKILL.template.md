---
name: meridian-skill-template
description: >-
  Template only — replace name and description. Use when creating a new Meridian
  IAM Claude skill for IdentityIQ SSB / Ops Desk workflows.
---

# <Skill title>

## When to use

Trigger phrases and situations.

## Invariants (never violate)

- Do not edit `base/ga/`
- Do not commit secrets
- Prefer `./build.sh` with `SPTARGET` set explicitly
- Ask before mutating IIQ or posting to tickets/PRs

## Inputs you must gather

| Input | Required | Notes |
| --- | --- | --- |
| | yes/no | |

## Procedure

1. …
2. …

## Output contract

```text
status: PASS|FAIL|NEED_HUMAN
summary: …
evidence: […]
next_actions: […]
```

## Verification

Commands / UI checks that prove success.
