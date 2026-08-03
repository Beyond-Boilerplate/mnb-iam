# Implement stage (MCP_E2E)

Execute the story using IIQ MCP tools. Follow the visibility contract.

## Required behavior
1. Emit a short plan (numbered steps + intended tools) before mutating calls.
2. Use read tools to confirm targets exist.
3. Perform writes needed for acceptance.
4. Re-read to verify.
5. Summarize what changed, how to test, residual risk.

If dry_run is enabled, mutating tools return a dry_run skip — treat that as intended and continue verification with reads.

If you cannot finish: stop, explain the blocker, recommend `blocked-needs-human`.

Never attempt Jira Done. Never call denylisted tools.
