# Meridian gotchas (light)

Principles, not a pipeline checklist.

1. MCP **tools** matter; empty resources are normal.
2. KAN To Do: prefer `status = "To Do"` (this board’s statusCategory can be wrong).
3. Branding/logo/theme → `web/` overlays — not `create_application`.
4. Confirm before IIQ writes and Jira moves; never auto-**Done**.
5. Never edit `base/ga/`. No excluded tools (`update_rule_source`, `update_scope`, `grant_capability`).
6. Persona missing in SCIM → don’t unlock a lookalike.
7. Fixtures ≠ live KAN.
8. Helpers under `scripts/iiq-delivery/` exist if you want them — skip when they don’t help.
9. Memory under `_memory/` is optional context, not a mandate to reuse a bad match.
10. Lab cubes often use ``first.last`` userNames; MCP identity tools accept ``id`` or ``name`` and resolve display names. Job title → ``get_identity_accounts`` ``profileHints.resolvedTitle`` (not the identity cube).
