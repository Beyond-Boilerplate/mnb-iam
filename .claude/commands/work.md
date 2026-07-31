---
description: Deliver a Meridian IAM/IIQ Jira ticket end-to-end with judgment
argument-hint: KAN-6
---

# /work $ARGUMENTS

Own ticket **$ARGUMENTS** until it’s ready for human PM review — or until you hit a real blocker.

## Outcome

1. Understand the ticket (Atlassian MCP or user paste).
2. Decide the right change surface (live IIQ MCP, `config/` SSD, `web/` branding, plugin code, or mix).
3. Do the work (ask before risky writes).
4. Prove it (MCP reads, UI checks, build notes — whatever fits).
5. Offer a PM-ready Jira comment + move to **In Review** only after the user confirms.

## How to think

- Match the **intent**, not a keyword coincidence. “Application branding” ≠ `create_application`. Logo/theme/favicon → `web/` overlays (see `docs/lessons/103-ui-customization-branding.md`).
- Skim `.ai-delivery/_memory/` or run helpers under `scripts/iiq-delivery/` **if** they speed you up — ignore them when they’d mislead.
- Write useful notes under `.ai-delivery/$ARGUMENTS/` when evidence helps the next session; don’t fill templates as ritual.
- Subagents are optional — spawn only when parallelism or isolation helps.

## Hard stops

See root `CLAUDE.md`. Never auto-**Done**. Never touch `base/ga/`.

## Done looks like

Short wrap-up: what you did, how to test, residual risk, Jira status (pending confirm / In Review).
