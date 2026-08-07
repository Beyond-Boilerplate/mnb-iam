# Plugins

| Field | Value |
| --- | --- |
| **Level** | Advanced |
| **Time** | ~45 min |
| **Prereq** | Skills + hooks basics ([03](../03-skills/), [06](../06-hooks/)) |
| **Artifacts** | `artifacts/playbooks/pr-review-plugin-sketch.md` |

## Why this matters

Five engineers each copy half a skill set. Six months later nothing matches. A **plugin** packages co-required skills, agents, hooks, and MCP bits so the team installs one unit. Staff judgment: **bundle what must ship together; keep optional skills separate**.

## Concept primer

| Approach | Use when |
| --- | --- |
| Single skill | One job, reusable alone |
| Plugin | A workflow needs several primitives as a unit |
| Repo `.claude/` | Source of truth for *this* codebase |
| Distributed plugin | Same pack across many repos |

```text
pr-review plugin
  ├─ skills: /pr, review-checklist
  ├─ agents: code-reviewer
  └─ hooks: block-secrets
```

## Hands-on walkthrough

### Task 1 — Decide boundaries

Pick a workflow (recommended: PR review). List must-have vs nice-to-have pieces.

### Task 2 — Sketch the pack

Write `lessons/artifacts/playbooks/pr-review-plugin-sketch.md` with:

- Purpose (one paragraph)  
- Included skills / agents / hooks / MCP  
- Install steps  
- Explicit non-goals  
- Secret/env requirements (names only)

### Task 3 — Review against sprawl

Cut anything that is useful alone and unrelated to PR review. Keep the sketch honest.

- **Expect:** A teammate could implement from the sketch without Slack.

## Copy-paste templates

- [`plugin-manifest.template.json`](plugin-manifest.template.json) — starter manifest fields for a bounded PR-review pack (adapt; do not ship secrets)

## How it works

Plugins reduce install drift. They do not replace thinking about least privilege — a plugin that ships write-everything MCP is still a bad plugin.

## Pitfalls

| Symptom | Fix |
| --- | --- |
| Kitchen-sink plugin | Split by workflow |
| Secrets in the bundle | Env vars + docs only |
| Undocumented commands | Catalog every `/name` |
| Diverging forks | Version and changelog the pack |

## Knowledge check

1. What is a plugin?  
2. When keep a skill separate?  
3. What must a sketch document?  
4. Plugins vs manual copy for teams?  
5. May plugins ship live credentials?

<details>
<summary>Answers</summary>

1. Distributable bundle of related Claude Code pieces.  
2. When useful alone and not co-required.  
3. Contents, install, non-goals, env names.  
4. Plugins standardize installs.  
5. No.

</details>

## Acceptance criteria

- [ ] `artifacts/playbooks/pr-review-plugin-sketch.md` exists
- [ ] Sketch lists non-goals and env var names (no secrets)
- [ ] Bundle is intentionally bounded

## Recap

- You sketched a bounded PR-review plugin.  
- Next: [Checkpoints](../08-checkpoints/) or [Advanced](../09-advanced/).

## Stretch

Turn the sketch into a real folder layout under `artifacts/playbooks/pr-review-plugin/` (even if not published).

## Feedback

What did you cut from the first draft of the bundle?

## Domain Stretch (optional)

Sketch a domain “ops desk” plugin — only if your team shares that pain.
