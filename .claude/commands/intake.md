---
description: List live KAN To Do issues (mnbiam Jira). Prefer Atlassian MCP.
---

# /intake

Find what’s waiting on the **live** Meridian board and show it clearly.

**Board:** [KAN](https://mnbiam.atlassian.net/jira/software/projects/KAN/list)

## Goal

List To Do issue **keys** (and a short summary each). Do not implement.

## How (your choice)

Prefer Atlassian MCP. This board’s “To Do” status is often **not** in statusCategory “To Do” — try:

1. `project = KAN AND status = "To Do" ORDER BY created ASC`
2. If empty: `project = KAN AND statusCategory = "To Do" ORDER BY created ASC`

If MCP isn’t connected, say so and suggest `/mcp` auth — don’t invent fixture keys.

## Present

```text
Jira To Do ready for /work (KAN @ mnbiam.atlassian.net):
- KAN-6 — <summary>
```

Suggest `/work <KEY>` when useful.

**Note:** Atlassian HTTP+SSE MCP (`/v1/sse`) is deprecated after 2026-06-30 — prefer Streamable HTTP `https://mcp.atlassian.com/v1/mcp` ([notice](https://community.atlassian.com/forums/Atlassian-Remote-MCP-Server/HTTP-SSE-Deprecation-Notice/ba-p/3205484)).
