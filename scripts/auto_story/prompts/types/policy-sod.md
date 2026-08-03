# policy-sod

DoR: policy name and/or violation id + mitigate/exception intent; or left/right **Bundle (role) names** for constraint edit.

Typical tools: `list_sod_policies`, `create_sod_policy`, `list_agent_roles`, `update_sod_constraints`, `simulate_sod_policy`, `create_policy_violation_exception`.

## Critical wiring rules

- `update_sod_constraints` left_roles / right_roles must be **IIQ Bundle names** (e.g. `MNB-Role-WireInitiator`, `MNB-IT-WireInit`), **not** entitlement values like `WIRE_INIT`.
- Resolve roles first with `list_agent_roles` (query `Wire`). Prefer business roles for exclusive-role policies; include matching IT packs when present.
- `create_sod_policy` alone is a shell — always follow with successful `update_sod_constraints`. If constraints return `Bundle not found`, stop and escalate (`blocked-needs-human`); do **not** claim success.
- Template: always pass **`SOD Template`** (Role SOD). Never invent template names — an unknown template used to create a bare `Policy` without `type=SOD` / `configPage=sodpolicy.xhtml`, and the UI shows a blank generic form with no rules table.
- After create, confirm response includes `type=SOD` (or re-export). If constraints exist in XML but UI has no rules table, the policy type metadata is wrong.
- Violation formatting rule / Violation business process UI fields are optional workflow metadata — not the SoD left/right sets. Confirm constraints via export or constraint API response `leftRoles`/`rightRoles`.

Verify: `update_sod_constraints` result ok with non-empty leftRoles and rightRoles; policy listed; do not mark ready if constraints failed.

## Handoff (policy-sod)

Keep the Jira comment tight. Example shape:

```text
KAN-7: MNB-SOD-Wire-DualControl is Active.

Constraint: MNB-Role-WireInitiator ✕ MNB-Role-WireApprover

How to test:
1. IIQ → Intelligence → Policies → open MNB-SOD-Wire-DualControl → confirm one SOD rule with those left/right roles.
2. simulate_sod_policy policy=MNB-SOD-Wire-DualControl with both roles → wouldViolate=true.
3. Optional live: grant both roles to a lab identity that has neither (not priya.wire alone / marcus.approve alone), run policy scan / list_open_sod_violations → open violation; remove one role → clears.

Note: empty open violations right after create is OK until someone holds both sides.
```

Do not use `search_roles` with `displayName` filters (SCIM rejects). Use `list_agent_roles`. Prefer `list_sod_policies` over `get_policy_detail` for SOD.
