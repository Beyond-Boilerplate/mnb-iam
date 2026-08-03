# Feasibility stage (read-only)

Classify the Jira issue. **Do not mutate IIQ.** You may use read MCP tools to check that referenced identities/apps/tasks exist.

## Output
Return a single JSON object (no markdown fence) with:

```json
{
  "mode": "MCP_E2E" | "HYBRID" | "BLOCKED",
  "story_type": "identity-admin|app-onboarding|task-ops|access-request|governance-admin|certification|policy-sod|jml-lifecycle|ui-branding|automation-rule-workflow|other",
  "confidence": 0.0,
  "reasons": ["…"],
  "missing_dor": ["…"],
  "planned_tools": ["tool_name"],
  "risks": ["…"]
}
```

## Rules
- If labels include a work-type, prefer that `story_type`.
- MCP_E2E only when DoR looks complete and the work is pure IIQ MCP.
- HYBRID for branding or Rule/Workflow SSD.
- BLOCKED when DoR incomplete, intentional exclusion, or unsafe.

Allowlisted for auto MCP_E2E: identity-admin, app-onboarding, task-ops, access-request (plus Phase-2 types if labeled and DoR clear).
