# Lesson 218 — Mover LCM End-to-End

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~85 minutes  
**Prereq:** Lessons 216–217  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 30

> **Why:** When someone transfers departments, yesterday’s birthright can become today’s over-entitlement. Auditors flag stale wire access after a move — and unlike joiners/leavers, this cleanup never fires by itself. Manager changes on the same transfer also break approval routing if you never re-run manager correlation.

## What this is

**LCM** (Lifecycle Management) is how IIQ reacts when someone’s employment *state* changes: hire, transfer, terminate.

| Event | Everyday meaning | Does this estate auto-fire a workflow? |
| --- | --- | --- |
| **Joiner** | New hire | Yes — Create IdentityTrigger (Lesson 217) |
| **Mover** | Department / title / manager change | **No** — you must refresh with the right flags |
| **Leaver** | Termination | Yes — attributeChange IdentityTrigger (Lesson 219) |

A **mover** is an HR transfer: Noah leaves Treasury & Payments for Retail Banking. His cube attributes update after Workday aggregation — but any role that *matched* the old department stays until something re-evaluates the selectors.

That “something” is **Identity Refresh with role detection** (and usually **provisioning**). Detection asks: “Does this identity still match every assigned role’s selector?” If no, IIQ builds a plan to remove the stale role and its entitlements.

You will also **reassign the manager** in HCM and prove the cube’s manager pointer updates only when manager correlation runs — the same class of “refresh flags matter” lesson as role detection.

Nothing here assumes a prior refresh left the right checkboxes on. Every Refresh task spells the flags explicitly.

## Know these

```text
HCM PATCH department/title (+ optional managerId)
  → Aggregate MNB-Workday
  → Refresh A: promote attributes ONLY (role detect OFF, provision OFF, manager corr OFF)
       cube.department updated — Roles UNCHANGED — manager UNCHANGED
  → Refresh B: manager correlation ON (isolate manager pointer)
       cube.manager → new manager identity
  → Refresh C: role detection + provision ON
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
| **Manager correlation** | Resolve HCM `managerId` → Identity manager pointer | Noah’s manager → `michael.watson` after Retail move |
| **Provisioning** | Execute the plan on target apps | Remove `WIRE_INIT` from Wire Portal |

| Event | Trigger exists? | Cleanup happens when |
| --- | --- | --- |
| Joiner (create) | Yes | Trigger fires with Process events |
| Leaver (attributeChange) | Yes | Trigger fires with Process events |
| Mover (department/title/manager) | **No** | Ops runs the right refresh flags |

### Refresh flag cheat-sheet (assume nothing)

UI labels vary slightly by build. Treat these as the contracts:

| Refresh pass | Promote / refresh attributes | Role detection / refresh assigned & detected roles | Provisioning | Manager correlation / refresh managers | Process events |
| --- | --- | --- | --- | --- | --- |
| **A — attributes only** | **ON** | **OFF** | **OFF** | **OFF** | OFF |
| **B — manager only** | optional | **OFF** | **OFF** | **ON** | OFF |
| **C — role cleanup** | optional | **ON** | **ON** | optional | OFF |

- **Wrong way:** Expecting a department PATCH alone to revoke anything — without role-detection + provision, the stale entitlement sits forever.  
- **Wrong way:** Leaving role detection ON during Refresh A — you skip the “gap” demonstration.  
- **Wrong way:** Using a persona with no wire-tied **detected** entitlement — a move with nothing to lose teaches nothing.  
- **Wrong way:** Treating a *manually assigned* Wire role as “detected” — detection only cleans what detection put there.  
- **Wrong way:** Assuming manager updates when you only promoted attributes — manager correlation is a separate flag.

## Intent

- Verify (or repair) wire-tied detected access before the move.
- Move a real persona between departments through the live HCM API (not Debug edits).
- Reassign manager in HCM and prove manager correlation is a separate refresh concern.
- Prove attribute promotion alone does **not** change roles.
- Run role detection + provisioning and confirm the stale entitlement leaves the live app.
- State the operational risk: movers without a scheduled refresh leave access live indefinitely.

## Before you start

Complete every checkbox. Do not skip into Task 1 until these are true.

- [ ] IIQ up as `spadmin` / `admin`
- [ ] Lesson 216 birthright / Wire roles exist — you will **verify** the mover’s access in Task 1 (create/assign from 216 if missing)
- [ ] HCM mock healthy:

```bash
curl -sf http://localhost:8091/health
```

- [ ] Wire-eligible persona identified (pick one and stick with it):

| Persona | worker id | Starting dept (typical) | Starting managerUserId (typical) |
| --- | --- | --- | --- |
| `noah.ibrahim` | `MNB00021` | Treasury & Payments | `MNB00001` (Helen) |
| `rachel.thapa` | `MNB00035` | Treasury & Payments | `MNB00002` |
| `priya.wire` | `MNB00090` | if she holds detected Wire from 216/222 | `MNB00006` (Sanjay) |

- [ ] Target Retail manager exists as a cube (typical): `michael.watson` / `MNB00036`
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/218
```

## Do this

### Task 1 — Pick a mover with a real access consequence

Open the candidate cube in IIQ. Confirm they hold something wire-related:

- Role such as `MNB-Bundle-Wire-Initiator` (or birthright that includes wire IT packs), **and/or**
- Entitlement on `MNB-WirePortal` / `MNB-CoreBanking` (`WIRE_INIT`, etc.)

Screenshot the **before** Roles / Application Accounts tab under evidence.

Also note **Manager** on the cube (name + that you will change it).

If there is no wire access:

1. Finish / re-run Lesson 216 detection for a Treasury persona, **or**
2. Request/assign Wire through the Lesson 222 path, then prefer a **detected** assignment for this drill

- **Why:** a department change with no entitlement to lose is a no-op drill.
- **Expect:** clear “before” proof of wire-tied access + current manager.

> **Tip:** Prefer a **detected** Wire role (selector matched department). If the role was only manually assigned, Task 7 will not auto-revoke it — that’s a finding, not a bug. Record detected vs manual under evidence now.

### Task 2 — Trigger the mover in live HCM (department + title)

```bash
./tools/lab/enterprise/hcm-scenario.sh mover MNB00021 \
  'Retail Banking' 'Customer Service Rep'
```

Substitute your chosen worker id (`MNB00021`, `MNB00035`, or username if the script accepts it).

- **Why:** movers are HR events — same live `PATCH` path as attribute sync (Lesson 215), not Debug cube edits.
- **Expect:** script exits 0 and prints updated worker JSON with new department/title.

### Task 3 — Reassign manager in HCM (same transfer)

`hcm-scenario.sh mover` does **not** change `managerId`. Patch it explicitly so the transfer looks like a real bank move (new dept + new people manager).

Example: Noah (`MNB00021`) → Retail people manager Michael (`MNB00036`):

```bash
curl -sf -X PATCH "http://localhost:8091/hcm/v1/workers/MNB00021" \
  -H 'Content-Type: application/json' \
  -d '{"managerId":"MNB00036"}' | python3 -m json.tool \
  | grep -E 'userName|department|title|managerId'
```

Adjust ids for your persona / target manager.

- **Why:** department-only movers still leave approvals and certs routing to the old manager until correlation catches up.
- **Expect:** HCM JSON shows `managerId` = new manager’s associate id (`MNB00036` in the example).

> **Watch out:** Use the manager’s **HCM id** (`MNB#####`), not their username, in `managerId`.

### Task 4 — Confirm the source (ground truth)

```bash
curl -s http://localhost:8091/hcm/v1/workers/MNB00021 \
  | python3 -m json.tool | grep -E 'department|title|userName|managerId'
```

- **Why:** if HCM still shows Treasury / old manager, IIQ cannot invent the move.
- **Expect:** `Retail Banking`, new title if set, and new `managerId`.

Save the curl output under evidence.

### Task 5 — Aggregate Workday, then Refresh A (attributes **only**)

1. **Setup → Tasks** → run **Account Aggregation** on `MNB-Workday`
2. Open **Refresh Identity Cube** (create the task if missing)
3. Set flags **exactly** for Refresh A:

| Option | Value |
| --- | --- |
| Filter (optional) | your mover’s `userName` (e.g. `noah.ibrahim`) |
| Promote / refresh attributes | **ON** |
| Refresh assigned / detected roles (role detection) | **OFF** |
| Provisioning | **OFF** |
| Refresh managers / manager correlation | **OFF** |
| Process events | **OFF** |

4. **Save** → **Run Now**
5. Open the cube → confirm `department` / `title` updated
6. Open **Roles** — should still look like the “before” screenshot
7. Confirm **Manager** still shows the **old** manager

- **Why:** isolates the teaching point — attribute promotion alone never re-evaluates birthright or manager pointers.
- **Expect:** cube attributes new; Roles unchanged; Manager unchanged.

> **Watch out:** If you accidentally leave role detection or manager correlation on in this step, you skip the gap demonstration. Note it under evidence and still complete the later passes for live proof.

### Task 6 — Refresh B (manager correlation only)

Run **Refresh Identity Cube** again for the same identity:

| Option | Value |
| --- | --- |
| Filter | same mover |
| Role detection | **OFF** |
| Provisioning | **OFF** |
| Manager correlation / refresh managers | **ON** |
| Promote attributes | optional (already done) |
| Process events | **OFF** |

Open the cube → **Manager** should now resolve to the new manager identity (e.g. `michael.watson`).

- **Why:** manager correlation is not “free” with attribute promotion — ops must enable it (or schedule it) like role detection.
- **Expect:** Manager pointer matches HCM `managerId`; Roles still unchanged (detection still off).

Screenshot Manager before/after under evidence.

If Manager stays blank: confirm the new manager’s Workday row was aggregated, Searchable `userId` exists (Lesson 214), and the HCM attribute mapped for manager correlation on `MNB-Workday` points at `managerId`.

### Task 7 — Refresh C (role detection + provisioning)

Run **Refresh Identity Cube** again:

| Option | Value |
| --- | --- |
| Filter | same mover |
| Role detection / refresh assigned & detected roles | **ON** |
| Provisioning | **ON** |
| Attribute promotion | optional |
| Manager correlation | optional |
| Process events | **OFF** |

- **Why:** this re-evaluates every detected role’s selector against the new department and executes a de-provision plan for anything that no longer matches.
- **Expect:** Task Result shows a detection / de-provision event for the wire role (or an explicit “no longer detected” message).

Screenshot the Task Result under evidence.

> **Watch out:** Process events is for joiner/leaver triggers — leaving it on here is unnecessary noise for a mover drill. Role cleanup is detection + provision, not an IdentityTrigger.

### Task 8 — Prove the live entitlement is gone

1. Re-aggregate the app that held the entitlement (`MNB-WirePortal` and/or `MNB-CoreBanking`)
2. Open the mover’s Application Accounts / Entitlements
3. Confirm the wire entitlement link is absent

Optional JDBC check if Core Banking was the target:

```bash
docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps -c \
  "select username, entitlement, status from mnb_app_accounts where username='noah.ibrahim';"
```

(Adjust username; password inside the container path is the usual `mnb` DB user.)

- **Why:** IIQ “role removed” is not the same as the target account changing.
- **Expect:** entitlement absent after re-aggregation (or SQL shows no `WIRE_INIT`).

### Task 9 — If you moved Priya, confirm the Bundle itself

If your mover was `priya.wire` with `MNB-Bundle-Wire-Initiator`:

- Roles tab: Bundle **gone** (or marked removed / no longer detected)
- Not just the raw entitlement missing while the role name still lists

- **Why:** role assignment and entitlement link can diverge if detection didn’t run or provisioning was off.
- **Expect:** both role and entitlement cleaned.

### Task 10 — Write the ops finding (one line)

Under evidence, save:

```text
Mover cleanup is refresh-driven (no IdentityTrigger). Gap risk = days of stale
wire access between HR move date and next role-detection+provision refresh.
Manager pointer also requires an explicit manager-correlation refresh — attribute
promotion alone leaves approvals routing to the old manager.
```

- **Why:** this is what you’d tell a control owner — not “IIQ broke.”
- **Expect:** written finding you can reuse in audits / Lesson 250.

## If it fails

| Symptom | Fix |
| --- | --- |
| Department changes, no role change after Refresh C | Wire role selector may not key off `department`; **or** the role was *manually assigned* (detection never owns it) |
| IIQ shows removed, live app still has it | Refresh C ran without provisioning; or you didn’t re-aggregate the target after the plan |
| Manager still old after Refresh B | Manager correlation still off; new manager cube missing; `managerId` typo; Searchable `userId` / Workday manager map (Lesson 214) |
| Manager updated during Refresh A | You left manager correlation on — re-read the flag cheat-sheet |
| Roles cleaned during Refresh A | Role detection was on — re-seed a Treasury persona or document the skipped gap demo |
| `hcm-scenario.sh mover` usage error | Form is `mover <username\|workerId> <newDepartment> [newTitle]`; quote departments with spaces |
| Wrong persona moved | Script accepts HCM `id` or `userName` — confirm `MNB00021`, not a colliding display name |
| No wire entitlement before the move | Finish Lesson 216 / 222 first, or pick another Treasury persona who already has wire access |

## You are done when

- [ ] Chosen persona’s department/title reflects the mover on their cube
- [ ] HCM `managerId` changed; cube Manager updated only after Refresh B
- [ ] Refresh A proved attributes update without role cleanup (and without manager flip)
- [ ] Wire-tied entitlement gone from the live app after Refresh C (detection + provision)
- [ ] You can state why cleanup didn’t happen automatically — and which flags ops must schedule

## Control note

- **Control:** Mover access re-evaluation + manager reassignment (refresh-driven, not trigger-driven)
- **Owner:** IAM Ops (must schedule/trigger refresh) + HR Ops (source event)
- **SLA (lab):** manual, same session; production risk is the gap between move date and next role-detection / manager refresh
- **Evidence:** `~/iiq-lab-evidence/sandbox/218/` — HCM curls, before/after Roles + Manager, three Task Results, live re-agg / SQL proof

## Quick check

1. Which IIQ trigger fires on a department change? → **None** — no mover trigger in this pack  
2. What refresh options revoke the stale detected role? → **Role detection + provisioning**  
3. What’s the operational risk? → A mover with no follow-up refresh leaves stale access live indefinitely  
4. Does a manually assigned role auto-revoke on mover? → **No** — only detected roles do  
5. Does attribute promotion update the Manager pointer? → **No** — need manager correlation enabled  

## Feedback

Could you explain why joiner/leaver have triggers but mover doesn’t — and walk the three refresh passes (attributes → manager → role cleanup) from memory? If roles didn’t change after Refresh C, note whether the Wire role was *detected* or *manually assigned*. If Manager didn’t move, note whether Refresh B had manager correlation **ON** and the exact `managerId` you PATCHed.

## Navigate

- Previous: [Lesson 217](217-joiner-lcm-live.md)
- Next: [Lesson 219](219-leaver-lcm-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
