# Lesson 218 — Mover LCM End-to-End

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~55 minutes  
**Prereq:** Lesson 217  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 30

> **Why:** Movers change what birthright *should* look like — stale entitlements left after a transfer are exactly what audits flag. Unlike joiner/leaver, this cleanup never fires on its own.

## What this is

There is no mover IdentityTrigger in this pack — only `create` (joiner) and `attributeChange` (leaver). Department/title moves use the same `PATCH /hcm/v1/workers/{id}` as Lesson 215’s attribute sync.

Role consequences (losing an entitlement tied to the old department) only happen when you explicitly run Identity Refresh with role detection **after** the attribute lands. Nothing watches for it automatically.

This lesson makes you feel that gap: move someone out of Treasury & Payments and confirm wire access doesn’t clean itself up until you refresh on purpose.

## Know these

```text
HCM PATCH department/title
  → Aggregate MNB-Workday → cube attributes update
  (no mover trigger — roles untouched)
  → Identity Refresh + role detection + provisioning
  → stale role un-detected → live entitlement removed
```

| Event | Trigger exists? | Cleanup happens when |
| --- | --- | --- |
| Joiner (create) | Yes | Trigger fires automatically |
| Leaver (attributeChange) | Yes | Trigger fires automatically |
| Mover (department/title) | **No** | Only when someone runs role-detection refresh |

- **Wrong way:** Assuming a department change alone revokes anything — without a second, role-aware refresh, the stale entitlement just sits there.

## Intent

- Move a real persona between departments through the live HCM API.
- Run role detection/provisioning refresh and confirm stale entitlements are removed.
- Prove wire access is revoked when someone leaves a wire-eligible department.
- State the operational risk of refresh-driven (not trigger-driven) cleanup.

## Before you start

- [ ] Lesson 216 birthright/wire roles wired to a live target
- [ ] Wire-eligible persona identified: `noah.ibrahim` (`MNB00021`) or `rachel.thapa` (`MNB00035`), both Treasury & Payments — or `priya.wire` if she holds Wire Initiator from 216
- [ ] HCM mock healthy: `curl -sf http://localhost:8091/health`
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/218
```

## Do this

### Task 1 — Pick a mover with a real access consequence

Choose a wire-eligible persona who currently shows a wire-tied entitlement on a live app (`MNB00021`, `MNB00035`, or `priya.wire` with `MNB-Bundle-Wire-Initiator`).

- **Why:** a department change with no entitlement to lose teaches nothing about stale access.
- **Expect:** persona currently shows wire-tied entitlement before the move.

Screenshot the “before” Roles / Application Accounts state under evidence.

### Task 2 — Trigger the mover in live HCM

```bash
./tools/lab/enterprise/hcm-scenario.sh mover MNB00021 \
  'Retail Banking' 'Customer Service Rep'
```

(Substitute your chosen worker id.)

- **Why:** same live PATCH path as attribute sync — movers are HR events, not Debug edits.
- **Expect:** script exits 0 with updated worker JSON.

### Task 3 — Confirm the source

```bash
curl -s http://localhost:8091/hcm/v1/workers/MNB00021 \
  | python3 -m json.tool | grep -E 'department|title'
```

- **Why:** ground truth before IIQ — wrong id here wastes the rest of the lab.
- **Expect:** new department/title values present.

### Task 4 — Aggregate and promote attributes only

1. Run **Account Aggregation** on `MNB-Workday`
2. Run **Identity Refresh** with attribute promotion **only** (no role detection yet)

- **Why:** isolates that attribute promotion alone touches nothing role-related.
- **Expect:** cube `department` updated; Roles tab still shows pre-move state.

### Task 5 — Role-detection refresh (the cleanup step)

Run Identity Refresh **again**, this time with role detection **and** provisioning enabled.

- **Why:** this re-evaluates every role’s selector against the new department and executes a plan for anything no longer matching.
- **Expect:** Task Result shows a detection/de-provision event for the wire role.

### Task 6 — Prove the live entitlement is gone

Re-aggregate `MNB-WirePortal` / `MNB-CoreBanking` (whichever you provisioned in 208/209/216) and confirm the moved persona’s wire entitlement link is actually gone.

- **Why:** IIQ “flagged” is not the same as the target account changed.
- **Expect:** entitlement absent after re-aggregation.

### Task 7 — If you moved Priya, confirm role revocation

If you moved `priya.wire`, confirm `MNB-Bundle-Wire-Initiator` itself is un-detected/revoked — not just the raw entitlement.

- **Why:** role assignment and entitlement link can diverge if detection didn’t run.
- **Expect:** role no longer listed on her cube.

## If it fails

| Symptom | Fix |
| --- | --- |
| Department changes, no role change after two refreshes | Wire role selector may not key off department; a *manually assigned* (not detected) role never auto-revokes |
| IIQ shows removed, live app still has it | Refresh without provisioning, or you didn’t re-aggregate the target after the plan |
| `hcm-scenario.sh mover` usage error | Form is `mover <username\|workerId> <newDepartment> [newTitle]`; quote departments with spaces |
| Wrong persona moved | Script accepts HCM `id` or `userName` — confirm you passed `MNB00021`, not a colliding name |

## You are done when

- [ ] Chosen persona’s department/title reflects the mover on their cube
- [ ] Wire-tied entitlement gone from the live app after role-detection + provision refresh
- [ ] You can state why cleanup didn’t happen automatically

## Control note

- **Control:** Mover access re-evaluation (refresh-driven, not trigger-driven)
- **Owner:** IAM Ops (must schedule/trigger refresh) + HR Ops (source event)
- **SLA (lab):** manual, same session; production risk is the gap between move date and next refresh
- **Evidence:** `~/iiq-lab-evidence/sandbox/218/` — HCM curl, before/after Roles tab, live app re-agg proof

## Quick check

1. Which IIQ trigger fires on a department change? → none — no mover trigger in this pack
2. What refresh options revoke the stale role? → role detection + provisioning
3. What’s the operational risk? → a mover with no follow-up refresh leaves stale access live indefinitely

## Feedback

Could you explain why joiner/leaver have triggers but mover doesn’t — and what ops must schedule instead? If roles didn’t change after Task 5, note whether the Wire role was *detected* or *manually assigned* — only detection auto-revokes.

## Navigate

- Previous: [Lesson 217](217-joiner-lcm-live.md)
- Next: [Lesson 219](219-leaver-lcm-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
