# CLAUDE.md

SailPoint IdentityIQ **8.5** SSD repo. Be **agentic**: pursue the user’s goal with judgment; use tools when they help; don’t run ceremony for its own sake.

## Hard stops (always)

- Never edit `base/ga/`.
- Never auto-move Jira to **Done** (PM owns Done). Confirm before Jira transitions/comments and before destructive IIQ writes.
- Don’t call: `update_rule_source`, `update_scope`, legacy `grant_capability` (use `assign_identity_capability`).
- Empty MCP **resources** ≠ MCP down — call **tools**.
- Don’t treat `jira-stories/fixtures` `MNB-*` as the live board unless the user asks for fixtures.

## Toolkits (use what fits)

| Need | Where |
| --- | --- |
| Live IIQ | MCP `identityiq` — `docs/api/MCP-TOOLS.md`; start via `./tools/lab/docker/up.sh` or `tools/iiq-mcp/./run.sh` |
| IIQ chatbot | Teller at http://localhost:4180 — `tools/iiq-chat/` (35+ pre-baked MCP + OpenRouter) |
| Durable XML / branding overlays | `config/` + `%%TOKENS%%` + `./build.sh`; UI under `web/` |
| Plugins | `pluginsrc/mnb-iam-toolkit/` |
| Live Jira (KAN) | Atlassian MCP · https://mnbiam.atlassian.net · project `KAN` |
| Optional helpers | `scripts/iiq-delivery/`, `scripts/jira/` — call if useful, not mandatory |
| Past approaches | `.ai-delivery/_memory/` — skim when it saves time |
| Notes / evidence | `.ai-delivery/<KEY>/` when working a ticket |

## Commands

- `/intake` — what’s in **To Do** on KAN (keys + one-line summaries).
- `/work KEY` — take the ticket from understanding → change → prove → PM-ready handoff. You choose the path.

Lab only if IIQ isn’t already at `http://localhost:8080/identityiq`.

More: `docs/SSD.md` · `docs/REPO_LAYOUT.md` · `docs/api/MCP-TOOLS.md` · `tools/iiq-mcp/README.md` · `.ai-delivery/_memory/GOTCHAS.md`
