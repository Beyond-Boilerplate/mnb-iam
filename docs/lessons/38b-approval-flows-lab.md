# Lesson 38b — Configure Approval Flows in IdentityIQ

**Level:** Intermediate  
**Track:** Requests  
**Time:** 75–90 minutes  
**Prereq:** Lessons 35–38 (you know *what* Meridian wants); LCM imported (`init-lcm.xml`); manager hierarchy (Lesson 21)  
**Lab data:**
- Owners / approvers: `emily.bennett`, `sanjay.kapoor`, `christopher.hayes`, `helen.ross`, `rachel.evans`
- Access: `CRM` / `DWRP` (manager); `AWS_ADMIN` / `MNB-Role-CloudAdmin` (dual); `PRIV_BREAK` / `MNB-Role-BreakGlass` (Security); optional `WIRE_INIT`
- Evidence: `~/iiq-lab-data/evidence/approvals-L38b/`
**Path:** Core (01–50) — **setup** the approval schemes Lessons 35–38 designed

---

> **Verify:** Lab lesson — configure LCM Business Process approval variables, object owners, escalation timers, and Security routing in IIQ. Soft-fails until LCM/HR personas exist.

## Learning objectives

You will be able to:

- Open the **LCM Provisioning** business process and set **Process Variables** that control who approves
- Configure **manager-only**, **two-step (manager + owner)**, and **Security Officer** approval schemes in SailPoint
- Choose **serial vs parallel** dual approval (`approvalMode`)
- Set **escalation / reminder** timers on approval work items
- Point privileged and break-glass items at **Security** (`helen.ross` or a workgroup) instead of manager-only
- Smoke-test each scheme with one request so you know the config stuck

---

## Why this matters

**Business.** Lessons 35–38 described Meridian’s tiers. Until someone sets them in IdentityIQ, every request still follows the default (often manager-only or none). `owen.morris` asking for AWS and an on-call engineer asking for `PRIV_BREAK` then get the same rubber-stamp path.

**Control / audit.** Examiners ask: *Where in IIQ is dual approval configured?* The answer is not a slide — it is **Setup → Business Processes → Process Variables**, plus **object owners** and (when needed) **QuickLink args**. Control owner: IAM Governance.

---

## Concepts

### Where SailPoint stores approval behavior

Access requests run a business process (usually **`LCM Provisioning`**). Approvers come from **workflow process variables**, not from a separate “approval matrix” screen.

| You configure… | In SailPoint… | Effect |
| --- | --- | --- |
| Who approves | Process variable **`approvalScheme`** | Builds approval work items |
| Order vs simultaneous | Process variable **`approvalMode`** | Serial or parallel dual |
| Security inbox | **`securityOfficerName`** | Used when scheme includes `securityOfficer` |
| If owner/manager missing | **`fallbackApprover`** | Safety net (often `spadmin` in lab — change for Meridian) |
| Overdue handling | **`workItemHoursTillEscalation`** (+ reminders) | Escalation / nudge timers |
| Who “owner” means | App / Role / Entitlement **Owner** field | Second vote for `owner` scheme |

### `approvalScheme` values (OOTB)

Comma-separated; **order = serial processing order** when `approvalMode` is serial:

| Value | Work item goes to |
| --- | --- |
| `none` | No approval (lab Rapid Setup trap — avoid for Meridian) |
| `manager` | Target identity’s manager |
| `owner` | Role owner (bundles) or entitlement/app owner (managed attributes) |
| `securityOfficer` | Identity or workgroup named in `securityOfficerName` |
| `identity` | Explicit list in `approvingIdentities` |

**Meridian mappings for this lesson:**

| Access | Set `approvalScheme` to | Also set |
| --- | --- | --- |
| `CRM` / `DWRP` | `manager` | Managers populated (Lesson 21) |
| `AWS_ADMIN` / CloudAdmin | `manager,owner` | Owner = `christopher.hayes` on role/app |
| `PRIV_BREAK` / BreakGlass | `securityOfficer` | `securityOfficerName` = `helen.ross` (or Security workgroup) |
| `WIRE_INIT` (optional) | `manager,owner` | Owner = `rachel.evans` on Wire role/entitlement |

### `approvalMode` (dual chain behavior)

| Mode | Behavior | Meridian use |
| --- | --- | --- |
| `serial` | Approver 1 must finish before Approver 2 is created | **Preferred** for AWS (manager then tech owner) |
| `parallel` | Both work items open; **both** required | Faster dual when both votes are mandatory |
| `serialPoll` / `parallelPoll` | Poll variants (any/all semantics differ) | Advanced — stick to `serial` or `parallel` here |

Wrong way: parallel where *either* vote is enough — that is not dual control.

### One global scheme vs many

OOTB **one** `LCM Provisioning` process has **one** default `approvalScheme`. Meridian needs **different** schemes by risk. Practical options (pick one path in Task 3):

| Approach | How | When |
| --- | --- | --- |
| **A — Owners + dual default** | Global `manager,owner`; low-risk items share app owner with manager or use manager-only QuickLink | Simple labs |
| **B — Separate QuickLinks** | “Standard Access” QuickLink passes `approvalScheme=manager`; “Privileged Access” passes `manager,owner` or `securityOfficer` | **Recommended training path** |
| **C — Clone workflow** | `MNB-WF-AccessRequest-*` per tier (Lesson 93) | Production hardening |

This lesson does **A + B** without editing OOTB XML in place.

```
Gear → Lifecycle Manager (which process runs)
        │
        ▼
Setup → Business Processes → LCM Provisioning
        │
        ▼
Process Variables: approvalScheme, approvalMode,
  securityOfficerName, fallbackApprover,
  workItemHoursTillEscalation, reminders
        │
        ▼
Object Owners (App / Role / Entitlement)
        │
        ▼
Optional: QuickLink args override scheme per catalog
```

---

## How it works

| Step in IIQ | Object | What you set today |
| --- | --- | --- |
| 1 | Lifecycle Manager → Business Processes | Confirm Access Request → `LCM Provisioning` |
| 2 | Business Process → Process Variables | Schemes, mode, Security name, escalation hours |
| 3 | Application / Bundle / ManagedAttribute | Owners for `owner` scheme |
| 4 | Workgroup (optional) | `MNB-WG-Security` containing `helen.ross` |
| 5 | QuickLink (optional) | Privileged vs standard `approvalScheme` args |
| 6 | Smoke request | Prove inbox landed on the right person |

**IIQ terms:** *Business Process* = Workflow shown in Setup. *Process Variables* = inputs such as `approvalScheme`. *Owner* on a role/entitlement resolves the `owner` token. *Security Officer* is not a capability — it is whoever you name in `securityOfficerName`.

---

## Before you start

- [ ] IIQ at `http://localhost:8080/identityiq` as `spadmin`
- [ ] `import init-lcm.xml` done; **Manage Access** visible
- [ ] Identities exist: `christopher.hayes`, `helen.ross`, `rachel.evans`, plus a manager (`emily.bennett` / `sanjay.kapoor`)
- [ ] Create `~/iiq-lab-data/evidence/approvals-L38b/`
- [ ] Do **not** set production-like `approvalScheme=none`

---

## Lab procedure

### Task 1 — Confirm which process handles Access Requests

Wrong process = you edit variables that never run.

1. Click the **gear** → **Lifecycle Manager** (or **Global Settings → Lifecycle Manager**).
2. Open the **Business Processes** tab.
3. Find the row for **Access Request** / Request Access / Entitlements / Roles (labels vary by version).
4. Confirm the process name is **`LCM Provisioning`** (or note the exact name your lab uses — Rapid Setup may show a variant).
5. Screenshot that mapping into the evidence folder.

**Expected result:** Written note: “Access Request → \<process name\>.”

**If it fails:** Gear → IdentityIQ Configuration / System Settings sometimes lists `workflowLCMAccessRequest`; Debug → Configuration `SystemConfiguration` entries `workflowLCM*` also show the name. Use that name in Task 2.

---

### Task 2 — Open Process Variables on `LCM Provisioning`

This is the primary SailPoint approval control panel.

1. Go to **Setup → Business Processes** (some builds: Setup → Workflows).
2. In **Edit an Existing Process**, select **`LCM Provisioning`** (or the name from Task 1).
3. Open the **Process Variables** tab.
4. Prefer the **form / simplified** view first; use **Advanced View** if a variable is missing.
5. Locate at least these fields (names may appear as friendly labels):

| Variable | Friendly label (approx.) | Meridian lab value |
| --- | --- | --- |
| `approvalScheme` | Approvers / Approval scheme | Start with `manager` (Task 4 changes per tier) |
| `approvalMode` | Approval mode | `serial` |
| `securityOfficerName` | Security officer | `helen.ross` (or workgroup from Task 5) |
| `fallbackApprover` | Fallback approver | `helen.ross` (avoid silent `spadmin` in Meridian story) |
| `workItemHoursTillEscalation` | Hours/days until escalation | See Task 6 |
| `workItemHoursBetweenReminders` | Reminder interval | e.g. 24 hours |
| `workItemMaxReminders` | Max reminders | e.g. 2 |

6. **Save** after each intentional change (do not leave the page with unsaved edits).

**Expected result:** You can point to the Process Variables screen and name the six variables above.

**If it fails:** Debug → Workflow `LCM Provisioning` → edit Variable initializers for the same keys; still screenshot. Prefer UI Process Variables when available.

---

### Task 3 — Decide how Meridian gets *multiple* schemes

Document the approach before clicking further.

1. Write in the binder:

```text
L38b routing approach: B — Separate QuickLinks
- Standard Access QuickLink: approvalScheme=manager
- Privileged Access QuickLink: approvalScheme=manager,owner  (AWS)
- Break-Glass QuickLink (or admin-on-behalf): approvalScheme=securityOfficer
Global LCM Provisioning fallback: approvalScheme=manager, approvalMode=serial
securityOfficerName=helen.ross
fallbackApprover=helen.ross
```

2. If your lab cannot edit QuickLink args, use approach **A**: set global `approvalScheme` to `manager,owner`, set owners correctly, and route break-glass by temporarily setting scheme to `securityOfficer` for that smoke test (or reassign — document honestly).

**Expected result:** One chosen approach recorded before Task 4.

---

### Task 4 — Set manager-only (CRM / DWRP)

Low-risk path: one vote from the target’s manager.

1. On `LCM Provisioning` Process Variables (or Standard Access QuickLink args):

   - **`approvalScheme`** = `manager`
   - **`approvalMode`** = `serial` (irrelevant for single approver; keep consistent)

2. Save.
3. Prerequisites that make `manager` resolve:

   - Target has a **Manager** on the identity cube (Lesson 21).
   - Manager identity is active.

4. Smoke test (short):

   - Request `CRM` for `amelia.brooks` (manager should be `emily.bennett`).
   - Confirm the approval work item owner is the manager — not `spadmin`, not Security.

**Expected result:** Work item description/owner shows manager approval for CRM.

**If it fails:** Fix manager attribute + Refresh; check `fallbackApprover` did not catch a blank manager; ensure scheme is not `none`.

---

### Task 5 — Set the two-approver chain (AWS)

Dual control = scheme **`manager,owner`** + a real **Owner** on the privileged object + **`approvalMode=serial`** (or parallel both-required).

#### 5a — Assign the Technology owner in IIQ

1. Open **`MNB-Role-CloudAdmin`** (Setup → Roles) **or** the `AWS_ADMIN` managed attribute / **`MNB-AWS-Cloud`** application — whichever you request in the catalog.
2. Set **Owner** = `christopher.hayes`.
3. Save. (For entitlements: Applications → entitlements / Managed Attribute editor → Owner.)

**Expected result:** Owner field shows Christopher Hayes / `christopher.hayes`.

#### 5b — Configure the dual scheme

1. For the **Privileged** path (QuickLink args **or** temporary global Process Variables):

   - **`approvalScheme`** = `manager,owner`  
     (order matters for serial: manager first, then owner)
   - **`approvalMode`** = `serial`  
     (use `parallel` only if you intentionally want both inboxes at once; both must still approve)

2. Save.

#### 5c — Smoke test dual chain

1. Request `AWS_ADMIN` or `MNB-Role-CloudAdmin` for `owen.morris` (manager `sanjay.kapoor` ≠ owner `christopher.hayes`).
2. Confirm **first** work item → `sanjay.kapoor`.
3. Approve as manager (or proxy).
4. Confirm **second** work item → `christopher.hayes`.
5. Screenshot both history entries.

**Expected result:** Two distinct approver identities in series (or two open items if parallel).

**If it fails:**

- Only manager appears → Owner blank; set Task 5a.
- Only owner appears → scheme is `owner` only; set `manager,owner`.
- Same person twice (`raj.external`) → manager equals owner; add Security (Task 7 / conflict note).

---

### Task 6 — Configure complex escalation timers

Escalation is configured on the **same** business process (approval step / process variables), not on the catalog tile.

1. On `LCM Provisioning` Process Variables, set reminder/escalation fields (labels vary; Advanced View if needed):

| Meridian tier | Convert to hours (lab) | Variable |
| --- | --- | --- |
| CRM / DWRP — Day 3 | `72` | `workItemHoursTillEscalation` |
| AWS dual — Day 2 | `48` | same variable (global) **or** privileged QuickLink/process override |
| Break-glass — 1 hour | `1` | privileged / break-glass process |

2. Set **`workItemHoursBetweenReminders`** (e.g. `24`) and **`workItemMaxReminders`** (e.g. `2`).
3. If the form shows **Escalation rule** / **Escalation template**:

   - Pick an OOTB escalation rule if present (often escalates to manager’s manager), **or**
   - Document: “Rule = OOTB / none — Meridian Tier-2 target `helen.ross` via manual forward until custom rule (Lesson 93).”

4. **Honest lab limit:** One global process usually has **one** escalation clock. To get 72h vs 48h vs 1h truly separated you need **separate processes/QuickLink arg overrides** or a custom rule. For training:

```text
Global LCM Provisioning: workItemHoursTillEscalation=72 (CRM default)
Privileged QuickLink / break-glass process: override to 48 or 1
Binder SLA table still states Meridian policy even if only one timer is live.
```

5. Screenshot the escalation/reminder fields.

**Expected result:** At least one timer configured; Meridian SLA table written beside it (policy + what IIQ actually has).

**If it fails:** Policy table alone is not enough for *this* lesson — set any non-empty `workItemHoursTillEscalation` (e.g. `72`) so the variable is clearly in use; note multi-tier overrides as follow-up.

---

### Task 7 — Set break-glass / Security-only approval

Break-glass must **not** use manager-only.

#### 7a — Security Officer target

1. Option A (simplest): set Process Variable **`securityOfficerName`** = `helen.ross`.
2. Option B (better ops): **Setup → Groups** (Workgroups) → create **`MNB-WG-Security`**, add `helen.ross` (and SOC identities if present), set `securityOfficerName` = `MNB-WG-Security`.

#### 7b — Scheme for break-glass

1. On the **Break-Glass / Privileged** QuickLink args **or** dedicated process variables for that path:

   - **`approvalScheme`** = `securityOfficer`
   - Do **not** use `manager` alone.

2. Ensure `PRIV_BREAK` / `MNB-Role-BreakGlass` is **not** on the casual catalog (Lesson 35) — requestable only via privileged QuickLink or admin-on-behalf.

3. Optional TTL: on the role/request UI enable **sunrise/sunset**; train requesters to set end ≤ 8 hours (Lesson 37).

#### 7c — Smoke test

1. Request BreakGlass / `PRIV_BREAK` with comment `MNB-INC-2048 — L38b config test`.
2. Confirm work item owner is `helen.ross` (or the Security workgroup) — **not** the user’s manager alone.
3. Screenshot.

**Expected result:** Security Officer scheme proven on one IdentityRequest.

**If it fails:** Re-check `securityOfficerName` spelling (must match identity or workgroup **name** exactly); scheme must include `securityOfficer`; reassign once only as temporary proof, then fix variables.

---

### Task 8 — Wire dual-control owner (optional but recommended)

Same dual pattern as AWS; different owner.

1. Set Owner on `WIRE_INIT` role/entitlement (or Wire app) to **`rachel.evans`**.
2. Privileged/Treasury QuickLink: `approvalScheme=manager,owner`, `approvalMode=serial`.
3. Never create one catalog tile that grants both `WIRE_INIT` and `WIRE_APPR`.

**Expected result:** Owner field + scheme note for Wire in the binder.

---

### Task 9 — Self-approval / manager=owner conflict (config note + control)

SailPoint will happily send both `manager` and `owner` votes to the **same** person when they are the same identity (`raj.external` → `christopher.hayes`).

1. On the matrix, write the compensating control:

```text
When manager == owner for AWS/CloudAdmin:
approvalScheme must become manager,securityOfficer
(or owner,securityOfficer) so helen.ross is the second vote.
```

2. Practical setup options:

   - **QuickLink / process for contractors** with `approvalScheme=manager,securityOfficer`, **or**
   - Approval Assignment Rule / custom workflow (Lesson 93) that detects manager=owner and injects Security.

3. For this lesson: document the rule and, if you can, set a **contractor privileged** QuickLink arg to `manager,securityOfficer` with `securityOfficerName=helen.ross`.

**Expected result:** Conflict rule written; optional QuickLink configured.

---

### Task 10 — Configuration evidence pack

1. Create `~/iiq-lab-data/evidence/approvals-L38b/CONFIG-README.txt`:

```text
Meridian L38b — SailPoint approval configuration
Access Request process name:
Global approvalScheme / approvalMode:
securityOfficerName:
fallbackApprover:
workItemHoursTillEscalation (global):
QuickLinks / overrides:
  Standard:
  Privileged (AWS):
  Break-glass:
Object owners:
  CloudAdmin / AWS_ADMIN → christopher.hayes
  Wire (optional) → rachel.evans
  BreakGlass requestable? (must be controlled):
Smoke tests (request id → observed approver):
  CRM manager-only:
  AWS dual:
  Break-glass Security:
```

2. Attach screenshots: Lifecycle Manager Business Processes tab, Process Variables (approvers + escalation), Owner fields, QuickLink args if used, three smoke-test work items.

**Expected result:** Another engineer can recreate the config from the pack without re-reading Lessons 35–38.

---

## Acceptance criteria

- [ ] Access Request process name identified (`LCM Provisioning` or lab equivalent)
- [ ] Process Variables opened; `approvalScheme`, `approvalMode`, `securityOfficerName`, `fallbackApprover` set intentionally
- [ ] Manager-only path configured and smoke-tested (CRM/DWRP)
- [ ] Dual chain configured: `manager,owner` + Owner `christopher.hayes` + serial/parallel choice; smoke-tested
- [ ] Escalation/reminder hours set; Meridian multi-tier SLA table documented (including IIQ global vs override limit)
- [ ] Break-glass uses `securityOfficer` → `helen.ross` / Security workgroup; smoke-tested
- [ ] Manager=owner conflict compensating scheme documented (optional QuickLink)
- [ ] `CONFIG-README.txt` + screenshots filed

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No approval work item | `approvalScheme=none` | Set `manager` or `manager,owner` |
| Always `spadmin` | Blank manager/owner → fallback | Fix manager/owner; set `fallbackApprover` to `helen.ross` |
| Dual skipped second vote | Owner not set | Task 5a Owner on role/entitlement/app |
| Break-glass to manager | Scheme still `manager` | Privileged path `securityOfficer` + `securityOfficerName` |
| `securityOfficer` skipped | Name typo / wrong object type | Exact identity or workgroup **name** |
| Edits have no effect | Wrong business process | Task 1 mapping; clear browser session; retry request |
| One timer for all tiers | Single global process | QuickLink/process overrides or Lesson 93 clones |
| Parallel but only one approve needed | Wrong mode/poll semantics | Use `serial` or confirm both-required parallel |

---

## Training binder evidence

1. Lifecycle Manager → Business Processes screenshot (Access Request → process name)  
2. `LCM Provisioning` Process Variables (scheme, mode, Security, fallback, escalation)  
3. Owner screenshots (`christopher.hayes`, optional `rachel.evans`)  
4. QuickLink arg screenshots (if approach B)  
5. Three smoke-test work item / IdentityRequest screenshots  
6. `CONFIG-README.txt`

**Control owner:** IAM Governance  
**Examiner question:** “Show where in IdentityIQ manager-only, dual owner, Security Officer, and escalation hours are configured.”

---

## Knowledge check

1. Which IIQ screen sets `approvalScheme` for LCM access requests?  
2. What `approvalScheme` string creates a manager-then-owner dual chain?  
3. What else must be true for `owner` to resolve to `christopher.hayes`?  
4. Which variable names the Security approver for break-glass?  
5. What does `approvalMode=serial` guarantee?  
6. Why can’t one global `workItemHoursTillEscalation` alone express 3-day / 2-day / 1-hour SLAs?

### Answers

1. **Setup → Business Processes →** (Access Request process, usually `LCM Provisioning`) → **Process Variables** (or QuickLink args that override them).  
2. `manager,owner` (comma-separated, manager first for serial).  
3. The requested role/entitlement/application **Owner** field must be set to `christopher.hayes`.  
4. `securityOfficerName` (identity or workgroup), with scheme including `securityOfficer`.  
5. The second approver’s work item is created only after the first approves.  
6. One process variable is one clock — Meridian needs QuickLink/process overrides or separate workflows per tier.

---

## Further reading

- [Lifecycle Manager Configuration](https://documentation.sailpoint.com/identityiq/help/lifecycle_manager/lifecycle_manager_config.html) — gear → Lifecycle Manager; Business Processes tab.
- [SailPoint Community](https://community.sailpoint.com/) — search “approvalScheme manager owner securityOfficer” and “LCM Provisioning process variables.”
- Lesson [93](93-workflow-lcm-customization.md) — clone `MNB-WF-*` when QuickLink overrides are not enough.
- Lessons [35](35-access-request-catalog.md)–[38](38-identity-request-tracking.md) — *what* to configure; this lesson is *where* in SailPoint.

---

## Stretch lab

1. Create QuickLinks `MNB-QL-StandardAccess` and `MNB-QL-PrivilegedAccess` with different `approvalScheme` arguments and separate populations.  
2. Create workgroup `MNB-WG-Security`; point `securityOfficerName` at the workgroup; prove any member can approve.  
3. Clone `LCM Provisioning` to `MNB-WF-AccessRequest-Privileged` with `workItemHoursTillEscalation=48` (Lesson 93 discipline).  
4. Add an Approval Assignment Rule that forces `securityOfficer` when manager equals owner.

---

## Summary

- You configured SailPoint approvals in **Business Process Process Variables**: scheme, mode, Security officer, fallback, and escalation hours.  
- You wired **object owners** and optional **QuickLink overrides** so CRM, AWS dual, and break-glass no longer share one blind path.  
- You smoke-tested each scheme and filed a config pack an examiner can replay.

---

**Previous:** [Lesson 38 — IdentityRequest Tracking & Auditing](38-identity-request-tracking.md)  
**Next:** [Lesson 39 — SoD Fundamentals for Banking](39-sod-fundamentals.md)
