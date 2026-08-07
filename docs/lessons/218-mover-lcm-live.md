# Lesson 218 — Mover LCM End-to-End

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~70 minutes  
**Prereq:** Lessons 216–217  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 30

> **Why:** When someone transfers departments, yesterday’s birthright can become today’s over-entitlement. Auditors flag stale wire access after a move — and unlike joiners/leavers, this cleanup never fires by itself.

## What this is

**LCM** (Lifecycle Management) is how IIQ reacts when someone’s employment *state* changes: hire, transfer, terminate.

| Event | Everyday meaning | Does this estate auto-fire a workflow? |
| --- | --- | --- |
| **Joiner** | New hire | Yes — Create IdentityTrigger (Lesson 217) |
| **Mover** | Department / title / manager change | **No** — you must refresh with role detection |
| **Leaver** | Termination | Yes — attributeChange IdentityTrigger (Lesson 219) |

A **mover** is an HR transfer: Noah leaves Treasury & Payments for Retail Banking. His cube attributes update after Workday aggregation — but any role that *matched* the old department stays until something re-evaluates the selectors.

That “something” is **Identity Refresh with role detection** (and usually **provisioning**). Detection asks: “Does this identity still match every assigned role’s selector?” If no, IIQ builds a plan to remove the stale role and its entitlements.

You will move a wire-eligible person out of Treasury, prove attributes update without touching roles, then run the cleanup refresh and confirm wire access is gone on the live app.

## Know these

```text
HCM PATCH department/title
  → Aggregate MNB-Workday
  → Identity Refresh (promote attributes only)
       cube.department updated — Roles UNCHANGED
  → Identity Refresh (role detection + provision)
       selector no longer matches → de-provision plan
  → re-aggregate Wire / Core Banking
       live entitlement actually gone
```

| Term | Plain English | Meridian example |
| --- | --- | --- |
| **Attribute promotion** | Copy HR attributes onto the cube | `department` becomes `Retail Banking` |
| **Role detection** | Re-match identity against role selectors | Wire role no longer matches → un-detect |
| **Detected role** | Assigned because a selector matched | Auto-revokes when selector fails |
| **Manually assigned role** | Someone clicked Assign | **Never** auto-revokes on mover |
| **Provisioning** | Execute the plan on target apps | Remove `WIRE_INIT` from Wire Portal |

| Event | Trigger exists? | Cleanup happens when |
| --- | --- | --- |
| Joiner (create) | Yes | Trigger fires with Process events |
| Leaver (attributeChange) | Yes | Trigger fires with Process events |
| Mover (department/title) | **No** | Ops runs role-detection refresh |

- **Wrong way:** Expecting a department PATCH alone to revoke anything — without a second, role-aware refresh, the stale entitlement sits forever.
- **Wrong way:** Using a persona with no wire-tied entitlement — a move with nothing to lose teaches nothing about stale access.
- **Wrong way:** Treating a *manually assigned* Wire role as “detected” — detection only cleans what detection put there.

## Intent

- Move a real persona between departments through the live HCM API (not Debug edits).
- Prove attribute promotion alone does **not** change roles.
- Run role detection + provisioning and confirm the stale entitlement leaves the live app.
- State the operational risk: movers without a scheduled refresh leave access live indefinitely.

## Before you start

- [ ] Lesson 216 birthright / Wire roles exist and can provision on a live target
- [ ] Wire-eligible persona identified (pick one):
  - `noah.ibrahim` (`MNB00021`) — Treasury & Payments
  - `rachel.thapa` (`MNB00035`) — Treasury & Payments
  - `priya.wire` — if she holds `MNB-Bundle-Wire-Initiator` from 216/222
- [ ] That persona currently shows a wire-tied entitlement (Roles or Application Accounts)
- [ ] HCM mock healthy:

```bash
curl -sf http://localhost:8091/health
```

- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/218
```

## Do this

### Task 1 — Pick a mover with a real access consequence

Open the candidate cube in IIQ. Confirm they hold something wire-related (role and/or entitlement on `MNB-WirePortal` / `MNB-CoreBanking`).

Screenshot the **before** Roles / Application Accounts tab under evidence.

- **Why:** a department change with no entitlement to lose is a no-op drill.
- **Expect:** clear “before” proof of wire-tied access.

> **Tip:** Prefer a **detected** Wire role (selector matched department). If the role was only manually assigned, Task 5 will not auto-revoke it — that’s a finding, not a bug.

### Task 2 — Trigger the mover in live HCM

```bash
./tools/lab/enterprise/hcm-scenario.sh mover MNB00021 \
  'Retail Banking' 'Customer Service Rep'
```

Substitute your chosen worker id (`MNB00021`, `MNB00035`, or the username if the script accepts it).

- **Why:** movers are HR events — same live `PATCH` path as attribute sync (Lesson 215), not Debug cube edits.
- **Expect:** script exits 0 and prints updated worker JSON.

### Task 3 — Confirm the source (ground truth)

```bash
curl -s http://localhost:8091/hcm/v1/workers/MNB00021 \
  | python3 -m json.tool | grep -E 'department|title|userName'
```

- **Why:** if HCM still shows Treasury, IIQ cannot invent the move.
- **Expect:** `Retail Banking` (and new title if you set one).

Save the curl output under evidence.

### Task 4 — Aggregate, then promote attributes **only**

1. **Setup → Tasks** → run **Account Aggregation** on `MNB-Workday`
2. Run **Refresh Identity Cube** with:
   - Attribute promotion / refresh attributes **on**
   - Role detection **off**
   - Provisioning **off**
3. Optionally filter to your mover’s `userName`

Open the cube → confirm `department` / `title` updated. Open **Roles** — should still look like the “before” screenshot.

- **Why:** isolates the teaching point — attribute promotion alone never re-evaluates birthright.
- **Expect:** cube attributes new; Roles tab unchanged.

> **Watch out:** If you accidentally leave role detection on in this step, you skip the “gap” demonstration. Undo by noting it and still complete Tasks 5–6 for live proof.

### Task 5 — Role-detection refresh (the cleanup step)

Run **Refresh Identity Cube** again for the same identity, this time with:

| Option | Value |
| --- | --- |
| Role detection / refresh assigned / detected roles | **On** |
| Provisioning | **On** |
| Attribute promotion | optional (already done) |

- **Why:** this re-evaluates every detected role’s selector against the new department and executes a de-provision plan for anything that no longer matches.
- **Expect:** Task Result shows a detection / de-provision event for the wire role (or an explicit “no longer detected” message).

Screenshot the Task Result under evidence.

### Task 6 — Prove the live entitlement is gone

1. Re-aggregate the app that held the entitlement (`MNB-WirePortal` and/or `MNB-CoreBanking`)
2. Open the mover’s Application Accounts / Entitlements
3. Confirm the wire entitlement link is absent

Optional JDBC check if Core Banking was the target:

```bash
psql -h localhost -p 5435 -U mnb -d mnb_apps \
  -c "select username, entitlement, status from mnb_app_accounts where username='noah.ibrahim';"
```

(Adjust username to your persona; password is typically `mnb`.)

- **Why:** IIQ “role removed” is not the same as the target account changing.
- **Expect:** entitlement absent after re-aggregation (or SQL shows no `WIRE_INIT`).

### Task 7 — If you moved Priya, confirm the Bundle itself

If your mover was `priya.wire` with `MNB-Bundle-Wire-Initiator`:

- Roles tab: Bundle **gone** (or marked removed / no longer detected)
- Not just the raw entitlement missing while the role name still lists

- **Why:** role assignment and entitlement link can diverge if detection didn’t run or provisioning was off.
- **Expect:** both role and entitlement cleaned.

### Task 8 — Write the ops finding (one line)

Under evidence, save one sentence:

```text
Mover cleanup is refresh-driven (no IdentityTrigger). Gap risk = days of stale
wire access between HR move date and next role-detection refresh.
```

- **Why:** this is what you’d tell a control owner — not “IIQ broke.”
- **Expect:** written finding you can reuse in audits / Lesson 250.

## If it fails

| Symptom | Fix |
| --- | --- |
| Department changes, no role change after Task 5 | Wire role selector may not key off `department`; **or** the role was *manually assigned* (detection never owns it) |
| IIQ shows removed, live app still has it | Refresh ran without provisioning; or you didn’t re-aggregate the target after the plan |
| `hcm-scenario.sh mover` usage error | Form is `mover <username\|workerId> <newDepartment> [newTitle]`; quote departments with spaces |
| Wrong persona moved | Script accepts HCM `id` or `userName` — confirm `MNB00021`, not a colliding display name |
| No wire entitlement before the move | Finish Lesson 216 / 222 first, or pick another Treasury persona who already has wire access |

## You are done when

- [ ] Chosen persona’s department/title reflects the mover on their cube
- [ ] Task 4 proved attributes update without role cleanup
- [ ] Wire-tied entitlement gone from the live app after role-detection + provision refresh
- [ ] You can state why cleanup didn’t happen automatically

## Control note

- **Control:** Mover access re-evaluation (refresh-driven, not trigger-driven)
- **Owner:** IAM Ops (must schedule/trigger refresh) + HR Ops (source event)
- **SLA (lab):** manual, same session; production risk is the gap between move date and next refresh
- **Evidence:** `~/iiq-lab-evidence/sandbox/218/` — HCM curl, before/after Roles, Task Result, live re-agg proof

## Quick check

1. Which IIQ trigger fires on a department change? → **None** — no mover trigger in this pack  
2. What refresh options revoke the stale detected role? → **Role detection + provisioning**  
3. What’s the operational risk? → A mover with no follow-up refresh leaves stale access live indefinitely  
4. Does a manually assigned role auto-revoke on mover? → **No** — only detected roles do  

## Feedback

Could you explain why joiner/leaver have triggers but mover doesn’t — and what ops must schedule instead? If roles didn’t change after Task 5, note whether the Wire role was *detected* or *manually assigned* — only detection auto-revokes.

## Navigate

- Previous: [Lesson 217](217-joiner-lcm-live.md)
- Next: [Lesson 219](219-leaver-lcm-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
