---
name: iiq-delivery
description: >-
  Deliver Meridian IdentityIQ / IAM work from a Jira ticket or free-form ask:
  branding, apps, identities, certs, SoD, JML, plugins, SSD config. Use when
  working KAN tickets, /work, or IIQ lab changes. Prefer judgment over fixed
  pipelines; MCP for live IIQ, web/ for branding, config/ for durable XML.
---

# IIQ delivery (agentic)

## Goal

Ship the user’s IAM/IIQ outcome safely in this Meridian lab/SSD repo.

## Decide the surface

| Signal | Likely path |
| --- | --- |
| logo, favicon, theme, branding, login look | `web/ui/images`, `web/ui/css/ui-custom.css` — not MCP app create |
| new connector / delimited feed / aggregation | MCP apps + optional `config/Application` |
| unlock, password, disable, capability | MCP identity tools |
| toolkit / Custom API / plugin zip | MCP plugins + `pluginsrc/` |
| Rule/Workflow as durable XML | `config/` + `importdynamic` (not `update_rule_source`) |

Read `docs/api/MCP-TOOLS.md` when touching live IIQ. Lesson branding: `docs/lessons/103-ui-customization-branding.md`.

## Operating style

1. Pull context (ticket, repo, MCP ping) as needed.
2. Form a short plan; say when you’re about to write.
3. Implement; keep evidence light but real.
4. Verify in a way that matches the change.
5. Offer Jira **In Review** + how-to-test comment — confirm first.

Optional helpers (never required): `scripts/iiq-delivery/*`, `.ai-delivery/_memory/`.

## Invariants

Root `CLAUDE.md` hard stops apply.
