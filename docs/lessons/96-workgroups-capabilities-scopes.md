# Lesson 96 — Workgroups, Capabilities & Scopes

| Field | Value |
| --- | --- |
| **Level** | Intermediate |
| **Track** | Rules, Workflows, Forms |
| **Time** | 60–75 minutes |
| **Prereq** | [Lesson 95 — QuickLinks & Custom UI](95-quicklinks-custom-ui.md) |
| **Lab data** | Personas in `~/iiq-lab-data/`; rule stubs in `lab-data/connectors/rules/README.md`; QuickLink patterns from Lesson 95 |

## Learning objectives

You will be able to:

- Distinguish **Workgroup**, **Capability**, and **Scope** and map each to Meridian RACI
- Create workgroups `MNB-WG-IAM-Ops`, `MNB-WG-Cert-Approvers`, and `MNB-WG-Risk-Review`
- Assign stock and custom capabilities so `helen.ross` can operate without full `spadmin`
- Apply a population-based **Scope** so helpdesk sees only contractors or a branch segment
- Explain to an examiner how menu rights and data rights differ

## Why this matters

Banks fail IAM exams when everyone shares `spadmin`, or when helpdesk can open every cube. Workgroups and capabilities turn “who can click what” into an auditable control. Scopes limit *which identities* an operator may see or act on.

**Control / audit:** Examiners ask: “Who can certify, who can mitigate SoD, and can helpdesk see executive cubes?” Your answer is capability matrices + scoped populations—not tribal knowledge.

## Concepts

| Object | Controls | Meridian example |
| --- | --- | --- |
| **Workgroup** | Membership list used as owner, approver, or assignment target | `MNB-WG-IAM-Ops` owns tasks and receives escalations |
| **Capability** | Rights (menu + object actions) granted to identities/workgroups | Certifier, Compliance Officer, System Administrator |
| **Scope** | Filters which identities/objects an operator may access | Helpdesk scoped to `workerType == contractor` |

```text
  Identity / Workgroup
           |
           +-- Capabilities --> menus, Debug, cert admin, policy mitigate
           |
           +-- Scope ---------> which cubes / apps / orgs are visible
```

**Rights vs data:** Capability without scope = powerful menus over *all* people. Scope without capability = you see a subset but cannot open admin tasks. Production needs both.

**Meridian RACI sketch**

| Role | Workgroup | Typical capabilities | Scope |
| --- | --- | --- | --- |
| IAM lead | `MNB-WG-IAM-Ops` | Identity admin, task admin (not full SystemAdministrator) | Enterprise |
| Certifiers | `MNB-WG-Cert-Approvers` | Certification | Manager tree / assigned campaigns |
| Risk | `MNB-WG-Risk-Review` | Compliance / policy | Enterprise read + mitigate |
| Helpdesk | `MNB-WG-Helpdesk` | Limited identity view + password reset if used | Contractors or branch OU |

**Naming:** Prefix Meridian workgroups `MNB-WG-`. Never grant `SystemAdministrator` to day-to-day ops personas.

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq` (or homelab alternate)
- [ ] Login as `spadmin`; Debug available
- [ ] Identities exist: `helen.ross`, `marcus.approve`, `sofia.torres`, `kai.nguyen`
- [ ] Lesson 95 QuickLink (if present) noted for capability gating later
- [ ] Binder page ready: “Authorization matrix — Lesson 96”

## Lab procedure

### Task 1 — Inventory stock capabilities

1. Open **Setup** → **Capabilities** (or **Gear** → Capabilities / equivalent).
2. Locate `SystemAdministrator`, `IdentityAdministrator`, `CertificationAdministrator` (or equivalent names in your build).
3. Open each and note **Included Rights** at a high level (do not edit yet).
4. Record which rights open Debug, Tasks, and Certifications.

**Expected result:** Notebook table: Capability → 2–3 key rights → Meridian owner candidate.

**If it fails:** Use Debug → Capabilities list; export one Capability XML for study.

### Task 2 — Create Meridian workgroups

1. Open **Setup** → **Workgroups** (or Identities → Workgroups).
2. Create `MNB-WG-IAM-Ops`. Description: “Meridian IAM operations — task owners and LCM escalations.”
3. Add members: `helen.ross`, `sofia.torres`.
4. Create `MNB-WG-Cert-Approvers` with `marcus.approve`, `amelia.brooks`.
5. Create `MNB-WG-Risk-Review` with `helen.ross` (Risk proxy in lab) and note real Risk mailbox for prod.

**Expected result:** Three `MNB-WG-*` workgroups with named Meridian members (not only `spadmin`).

**If it fails:** Create Identity objects of type workgroup via Debug import if UI path differs; keep the same names.

### Task 3 — Grant least-privilege capabilities to IAM Ops

1. Open identity `helen.ross`.
2. Assign capabilities appropriate for IAM ops (e.g., IdentityAdministrator + Task management rights)—**not** SystemAdministrator.
3. Optionally assign the same capabilities to workgroup `MNB-WG-IAM-Ops` if your UI supports workgroup capability grants.
4. Log out. Log in as `helen.ross` (reset password via `spadmin` if needed).
5. Confirm she can open Identities and Tasks; confirm Debug is **hidden** or denied.

**Expected result:** `helen.ross` operates day-to-day menus without SystemAdministrator.

**If it fails:** If menus empty, add one missing right; if Debug appears, remove SystemAdministrator / Debug rights immediately and retest.

### Task 4 — Scope helpdesk (or certifiers)

1. Create or reuse a **Population** (Advanced Analytics / Populations): e.g., `MNB-Pop-Contractors` filter `workerType` equals contractor (or equivalent attribute from HR).
2. Open **Setup** → **Scopes** (or equivalent).
3. Create scope `MNB-Scope-Helpdesk-Contractors` bound to that population.
4. Assign the scope to a helpdesk identity (use `kai.nguyen` as lab helpdesk) with limited capabilities.
5. Log in as `kai.nguyen`. Search for contractor `nina.joiner` (or a known contractor) vs executive-style identity if present.

**Expected result:** Scoped user finds in-scope identities; out-of-scope cubes are hidden or not actionable.

**If it fails:** Document “scope UI unavailable in this lab build” and simulate with ControlledScope notes in binder—still complete the matrix design.

### Task 5 — Authorization matrix evidence

1. Build a matrix: Workgroup | Members | Capabilities | Scope | Allowed actions | Forbidden actions.
2. Include a row proving `spadmin` is break-glass only (Lesson 109 deepens this).
3. Tie one QuickLink from Lesson 95 to a required capability/right if applicable.

**Expected result:** One-page matrix suitable for examiner walkthrough.

**If it fails:** Spreadsheet is fine; keep Meridian object names exact.

### Task 6 — Negative test (control proof)

1. As scoped/limited user, attempt to open **Debug** or edit a System Configuration object.
2. As `helen.ross`, attempt one admin action she should have and one she should not (e.g., Plugin install).
3. Screenshot denial or missing menu.

**Expected result:** Binder shows at least one intentional **denied** path—positive evidence of least privilege.

## Acceptance criteria

- [ ] Three `MNB-WG-*` workgroups exist with Meridian personas
- [ ] `helen.ross` has ops capabilities without SystemAdministrator
- [ ] Capability inventory notes completed for stock admin capabilities
- [ ] Scope design documented; lab scope applied or binder exception recorded
- [ ] Authorization matrix filed
- [ ] Negative test (denied Debug/admin) evidenced

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| helen.ross sees empty home | Missing capability / not in workgroup | Re-grant IdentityAdministrator-class rights |
| Scoped user still sees everyone | Scope not assigned / cache | Re-login; verify ControlledScope on identity |
| Workgroup cannot own task | Task expects Identity owner | Set owner to workgroup explicitly if supported |
| Capabilities duplicated | Direct + workgroup grants | Prefer workgroup grants for ops teams |
| QuickLink visible to all | No `rightRequired` | Gate QuickLink/plugin snippet (Lessons 95–97) |

## Training binder evidence

- Screenshots: three workgroups with members  
- Capability list notes for `helen.ross`  
- Scope / population definition  
- Authorization matrix  
- Denied-action screenshot  

## Knowledge check

1. What does a Capability control vs what a Scope controls?
2. Why should `MNB-WG-IAM-Ops` not receive SystemAdministrator?
3. Name two Meridian workgroups from this lesson and one intended member each.
4. How do workgroups help certifications and escalations?
5. What examiner question does the negative test answer?

### Answers

1. Capability = menus/actions (rights); Scope = which identities/objects those rights apply to.  
2. Day-to-day ops must not hold break-glass rights; least privilege + auditability.  
3. Examples: `MNB-WG-IAM-Ops` / `helen.ross`; `MNB-WG-Cert-Approvers` / `marcus.approve`; `MNB-WG-Risk-Review` / Risk proxy.  
4. Workgroups are stable assignment targets when people rotate; certifications and LCM can route to the group.  
5. “Prove helpdesk/IAM ops cannot perform unrestricted admin”—shows intentional denial.

## Stretch lab

Design `MNB-WG-Branch-Ops` scoped to one cost center; map which cert campaigns and access-request approvals they may touch. Do not implement in prod without Change Advisory Board (CAB) review.

## Summary

- Workgroups hold people; capabilities hold rights; scopes hold data boundaries.
- Meridian ops run as `MNB-WG-*` with least privilege—not shared `spadmin`.
- Matrices plus denied-path screenshots are the audit artifacts.

## Enterprise RACI deep dive

| Activity | Responsible | Accountable | Consulted | Informed |
| --- | --- | --- | --- | --- |
| Grant SystemAdministrator | Break-glass board | CISO / IAM head | Security architecture | SOC |
| Day-2 identity admin | `MNB-WG-IAM-Ops` | IAM lead (`helen.ross`) | App owners | Helpdesk |
| Certification campaign admin | `MNB-WG-Cert-Approvers` + IAM | IAM lead | Managers | Risk |
| SoD mitigate | `MNB-WG-Risk-Review` | Risk | IAM | Audit |
| Helpdesk password reset (if used) | `MNB-WG-Helpdesk` | ITSM owner | IAM | User |

**Examiner rehearsal:** “Show the person who can open every identity cube.” If the answer is an entire helpdesk team without scopes, remediate before prod.

### Task 7 — ControlledScope vs dynamic scope notes

1. Document whether your IIQ build uses ControlledScope attributes on the identity, assigned Scope objects, or both.
2. For Meridian contractors, prefer population `MNB-Pop-Contractors` driven from HR `workerType`.
3. For branch ops stretch, note cost-center attribute from HR cube (Lesson 05 schema).
4. Record cache/re-login requirement after scope assignment.

**Expected result:** Scope mechanism note specific to your build.

**If it fails:** Keep design-only ControlledScope paragraph—still required for blueprint Lesson 110.

### Capability bundling guidance

Do not create twenty micro-capabilities on day one. Start with:

1. `MNB-Cap-IAM-Operator` — identities, tasks (non-debug), reports read
2. `MNB-Cap-Cert-Operator` — certification admin without plugin install
3. `MNB-Cap-Risk-Officer` — policy violations, mitigate
4. Stock SystemAdministrator — break-glass only (Lesson 109)

Map stock rights into these bundles via included capabilities when the product allows nesting.

---

**Previous:** [Lesson 95 — QuickLinks & Custom UI](95-quicklinks-custom-ui.md)  
**Next:** [Lesson 97 — Plugin Framework Basics](97-plugin-framework-basics.md)
