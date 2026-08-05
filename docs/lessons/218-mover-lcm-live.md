# Lesson 218 — Mover LCM End-to-End

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~55 minutes  
**Prereq:** Lesson 217  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 30

> **Why (1–2 lines):** Movers change what birthright *should* look like — stale entitlements left behind after a transfer are exactly what a bank audit flags. Unlike joiner/leaver, this cleanup never fires on its own.

## What this is

There is no `MNB-IdentityTrigger-Mover` in `config/` — the pack only ships `create` (joiner) and `attributeChange` (leaver) triggers. That's a deliberate gap: department/title moves run through the same `PATCH /hcm/v1/workers/{id}` as Lesson 215's attribute sync, and the *role* consequences (losing an entitlement tied to the old department) only happen when you explicitly run Identity Refresh with role detection **after** the attribute lands — nothing watches for it automatically. This lesson makes you feel that gap: move someone out of Treasury & Payments and confirm wire access doesn't clean itself up until you refresh on purpose.

## Know these

```text
HCM PATCH department/title → Aggregate MNB-Workday → cube attribute updates
  (no mover trigger fires — role/entitlement state untouched)
  → Identity Refresh + role detection + provisioning
  → stale role un-detected → live entitlement removed
```

| Event | Trigger exists? | Cleanup happens when |
| --- | --- | --- |
| Joiner (create) | Yes | Trigger fires automatically |
| Leaver (attributeChange) | Yes | Trigger fires automatically |
| Mover (department/title change) | **No** | Only when someone runs role-detection refresh |

**Wrong way:** Assuming a department change alone revokes anything — without a second, role-aware refresh, the stale entitlement just sits there.

## Intent

- Move a real persona between departments through the live HCM API.
- Run role detection/provisioning refresh and confirm stale entitlements are removed, not just new ones added.
- Prove wire access is revoked specifically when someone transfers out of a wire-eligible department.
- State, in one sentence, the operational risk this refresh-driven (not trigger-driven) cleanup creates.

## Before you start

- [ ] Lesson 216 birthright/wire roles wired to a live target
- [ ] A wire-eligible persona identified: `noah.ibrahim` (`MNB00021`) or `rachel.thapa` (`MNB00035`), both Treasury & Payments
- [ ] HCM mock healthy: `curl -sf http://localhost:8091/health`
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/218`

## Do this

1. Pick a mover with a real access consequence — a wire-eligible persona leaving Treasury & Payments (`MNB00021` or `MNB00035`; or `priya.wire` if she holds `MNB-Bundle-Wire-Initiator` from Lesson 216).  
   **Expect:** Persona currently shows wire-tied entitlement on a live app.

2. Trigger the mover live: `./tools/lab/enterprise/hcm-scenario.sh mover MNB00021 'Retail Banking' 'Customer Service Rep'`.  
   **Expect:** Script exits 0 with updated worker JSON.

3. Confirm it landed at the source: `curl -s http://localhost:8091/hcm/v1/workers/MNB00021 | python3 -m json.tool | grep -E 'department|title'`.  
   **Expect:** New department/title values present.

4. Run **Account Aggregation** on `MNB-Workday`, then **Identity Refresh** with attribute promotion only — same two-step pattern as Lesson 215.  
   **Why:** Isolates that attribute promotion alone touches nothing role-related.  
   **Expect:** Cube's `department` updated; Roles tab still shows pre-move state.

5. Run Identity Refresh **again**, this time with role detection **and** provisioning enabled.  
   **Why:** This is the step that re-evaluates every role's selector against the new department and computes/executes a plan for anything no longer matching.  
   **Expect:** Task Result shows a detection/de-provision event for the wire role.

6. Confirm the live consequence: re-aggregate `MNB-WirePortal`/`MNB-CoreBanking` (whichever you provisioned in Lessons 208/209/216) and confirm the moved persona's wire entitlement link is actually gone, not pending.  
   **Expect:** Entitlement absent after re-aggregation, not just "flagged" in IIQ.

7. If you moved `priya.wire`, confirm her `MNB-Bundle-Wire-Initiator` assignment itself is un-detected/revoked, not just the raw entitlement.  
   **Expect:** Role no longer listed on her cube.

## If it fails

- **Department changes but no role change after two refreshes** — check the wire role's selector is actually keyed off department; a manually-assigned (not detected) role never auto-revokes regardless of refresh.
- **Wire entitlement shows removed in IIQ but still active on the live app** — refresh ran without provisioning enabled, or you didn't re-aggregate the target after the plan executed.
- **`hcm-scenario.sh mover` errors "usage"** — exact form is `mover <username|workerId> <newDepartment> [newTitle]`; quote departments with spaces.
- **Wrong persona moved** — the script accepts HCM `id` or `userName`; confirm you passed `MNB00021`, not a plain username.

## You are done when

The chosen persona's department/title reflects the mover on their cube, their wire-tied entitlement is gone from the live app after a role-detection-and-provision refresh, and you can state from memory why cleanup didn't happen automatically.

## Control note

- **Control:** Mover access re-certification (implicit, refresh-driven).  
- **Owner:** IAM Ops (must schedule/trigger refresh) + HR Ops (source event).  
- **SLA (lab):** Manual, same session; production risk is exactly the gap between move date and next refresh.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/218/` — HCM curl output, before/after Roles tab, live app re-aggregation proof.

## Quick check

1. Which IIQ trigger fires on a department change? → None — no `MNB-IdentityTrigger-Mover` exists.  
2. What refresh option actually revokes the stale role? → Role detection + provisioning enabled.  
3. What's the operational risk this lesson demonstrates? → A mover with no follow-up refresh leaves stale access live indefinitely.

## Navigate

- Previous: Lesson 217  
- Next: Lesson 219  
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
