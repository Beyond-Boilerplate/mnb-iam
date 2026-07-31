# Day 23 — Jira MCP Ticket Bridge

| Field | Value |
| --- | --- |
| **Week** | 4 — MCPs + Capstone |
| **Time** | 2.5–3.5 hours |
| **Prereq** | Day 22; Day 13 JML stub; optional Atlassian access |
| **Artifacts** | `artifacts/mcp/jira-bridge.md` |

## Learning objectives

You will be able to:

- Connect Jira MCP (see free-claude-code `.claude/TUTORIAL.md` pattern) or document a mock
- Pull a story/bug and transform it into a Meridian lab plan via JML or agg skills
- Write comments / transitions only with explicit approval
- Keep PII out of unnecessary logs

## IAM pain (today’s tax)

Tickets say “fix joiner for nina” with three missing fields. Bridging MCP → skill forces structured intake before touching IIQ.

## Claude concept

```text
Jira issue
  → MCP get issue
  → map fields → jml-pack skill inputs
  → human approve plan
  → (optional) MCP comment with plan link / evidence paths
```

Use the tutorial snippet if Atlassian MCP available:

```bash
claude mcp add --scope user --transport sse jira https://mcp.atlassian.com/v1/sse
```

Then authenticate via `/mcp`.

## Before you start

- [ ] Jira site access **or** prepare a JSON fixture mock issue in `artifacts/mcp/fixtures/issue.json`  
- [ ] JML skill installed  

## Lab procedure

### Task 1 — Connect or mock

If no Jira: write a fixture and a tiny “fake MCP” note describing how tools would look.

### Task 2 — End-to-end bridge (read)

> Fetch issue `<KEY>` (or fixture). Produce Meridian JML pack. Do not transition ticket.

### Task 3 — Field mapping table

Document: summary, description, custom effective date, identity, apps → skill inputs. Save in `jira-bridge.md`.

### Task 4 — Gated write

Only if real Jira: post a comment with plan summary after approval. No auto-close.

## Deliverable

`jira-bridge.md` + sample plan output from a real or fixture issue.

## Acceptance criteria

- [ ] Mapping table complete  
- [ ] One issue → plan demonstrated  
- [ ] Write actions gated  
- [ ] PII handling notes present  

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| SSE auth fails | Org policy; try alternate transport per Atlassian docs |
| Wrong project | Scope MCP / query filters |

## Stretch

- Auto-label tickets `iam-jml` when skill runs  
- Webhook idea (out of scope) noted for future  

## Knowledge check

1. Why fixture mode matters?  
2. What must never be auto-transitioned?  
3. How does Day 13 stub pay off?

### Answers

1. Learn without depending on SaaS.  
2. Prod access / approval tickets without human.  
3. Field names already designed.

## Navigation

[← Day 22](day-22-mcp-fundamentals.md) · [Day 24 →](day-24-mcp-github-pr-discipline.md)
