# Handoff stage

Produce a **brief** PM-ready handoff for Jira **In Review**. Do not call write tools unless needed to re-check status.

## Jira comment rules (strict)

- **Short:** ~8–15 lines max. No emoji walls, no restating the whole implement chat.
- **Concrete only:** name the real IIQ objects (policy, roles, apps, identities) from this run.
- **How to test must be clickable/checkable steps** a PM can follow in lab IIQ (or name exact MCP checks as backup) — not “validate acceptance criteria.”
- Prefer Meridian personas when relevant (`priya.wire`, `marcus.approve`, `nina.joiner`, …).
- **One line residual risk** max (or omit if none). Skip process lectures (“PM owns Done”, “until automated reconciliation”).
- Do **not** paste tool dumps, JSON, or long MCP transcripts into the comment.

## Output format

1. Markdown comment body only (what goes on the Jira ticket).
2. Then a fenced JSON block (machine fields — **not** posted as the comment):

```json
{
  "ready_for_review": true,
  "comment": "same brief Markdown as above (optional duplicate)",
  "summary": "one sentence",
  "how_to_test": [
    "UI or MCP step with object names",
    "expected result"
  ],
  "residual_risk": ["optional one-liner"],
  "mcp_tools_used": ["…"]
}
```

If not ready: `ready_for_review: false`, short comment listing blockers, empty or honest `how_to_test`.
