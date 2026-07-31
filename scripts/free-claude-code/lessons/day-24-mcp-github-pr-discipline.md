# Day 24 — GitHub MCP + PR Discipline

| Field | Value |
| --- | --- |
| **Week** | 4 — MCPs + Capstone |
| **Time** | 2.5–3 hours |
| **Prereq** | Day 22; familiarity with `.github/workflows/ssb-ci.yml` |
| **Artifacts** | `artifacts/mcp/github-pr-review.md` |

## Learning objectives

You will be able to:

- Use GitHub MCP (or `gh`) with Claude for PR review focused on `config/` XML
- Encode SSB CI expectations into review comments
- Block merge recommendations when hygiene/token issues remain
- Tie XML reviewer agent to PR diffs

## IAM pain (today’s tax)

PRs with “fix aggregation” and 800-line Debug dumps get rubber-stamped. Agentic review with Meridian checklists reduces silent production debt.

## Claude concept

PR review spine:

```text
changed files → only config/** + properties?
  → xml-reviewer agent on diff
  → check CI workflow implications
  → CAB comment template
```

Prefer **comment-only** bot behavior today; humans click merge.

## Before you start

- [ ] `gh auth` working **or** GitHub MCP connected  
- [ ] A branch/PR to review (create a harmless docs-only PR if needed)  

## Lab procedure

### Task 1 — Wire access

Document MCP vs `gh` approach in artifact file.

### Task 2 — Review checklist skill/agent glue

Prompt Claude to review a PR using meridian hygiene + tokenize rules.

### Task 3 — CI awareness

Ask: what does `ssb-ci.yml` run on this PR? Would XML-only changes still need WAR build?

### Task 4 — Sample review comment

Save a gold-standard review comment template for Meridian PRs.

## Deliverable

`github-pr-review.md` + template comment.

## Acceptance criteria

- [ ] One PR reviewed with checklist evidence  
- [ ] CI implications stated correctly at high level  
- [ ] No autonomous merge  
- [ ] Secrets scan mention included  

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| MCP lacks permission | Classic PAT scopes / GitHub app  
| Huge binary diffs | Ensure base/ga not in PR  

## Stretch

- Hook: deny `git push` if `base/` staged  
- Link verify evidence paths in PR body  

## Knowledge check

1. Why config XML PRs need token review?  
2. Who merges?  
3. Name one CI file to cite.

### Answers

1. Env leakage / broken higher envs.  
2. Human.  
3. `.github/workflows/ssb-ci.yml`.

## Navigation

[← Day 23](day-23-mcp-jira-ticket-bridge.md) · [Day 25 →](day-25-mcp-iiq-verify-bridge.md)
