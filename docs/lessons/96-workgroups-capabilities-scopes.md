# Lesson 96 — Workgroups, Capabilities & Scopes

**Level:** Intermediate  
**Track:** Rules, Workflows, Forms  
**Time:** 75–90 min  
**Prereq:** Lesson 95 — QuickLinks and Custom UI  

**Lab data:**
- Personas in `~/iiq-lab-data/`
- Rule stubs: `lab-data/connectors/rules/README.md`
- QuickLink patterns from Lesson 95
- Deepens into Lesson 109 break-glass hardening

---

## Learning objectives

You will be able to:

- Distinguish **Workgroup**, **Capability**, and **Scope** and map each to Meridian RACI
- Create workgroups `MNB-WG-IAM-Ops`, `MNB-WG-Cert-Approvers`, and `MNB-WG-Risk-Review`
- Assign stock and custom capabilities so `helen.ross` can operate without full `SystemAdministrator`
- Apply a population-based **Scope** so helpdesk sees only contractors or a branch segment
- Prove least privilege with a negative test (denied Debug) and explain menu rights vs data rights to an examiner

---

## Why this matters

**Business.** Banks fail IAM exams when everyone shares `spadmin`, or when helpdesk can open every executive cube. When `kai.nguyen` works helpdesk tickets for contractors, he must reset or view *contractor* identities — not browse `helen.ross`’s peers or wire-approver cubes without a business need.

**Control / audit.** Examiners ask: *Who can certify, who can mitigate SoD, and can helpdesk see executive cubes?* Your answer is capability matrices + scoped populations — not tribal knowledge. Lesson 109 seals `spadmin`; this lesson builds the day-2 replacement.

---

## Concepts

### Three objects, three jobs

| Object | Controls | Meridian example |
| --- | --- | --- |
| **Workgroup** | Membership list used as owner, approver, or assignment target | `MNB-WG-IAM-Ops` owns tasks and receives escalations |
| **Capability** | Rights (menu + object actions) granted to identities/workgroups | Certifier, Compliance Officer — not SystemAdministrator for day-2 |
| **Scope** | Filters which identities/objects an operator may access | Helpdesk scoped to `employeeType == contractor` |

```
  Identity / Workgroup
           │
           ├── Capabilities → menus, Debug, cert admin, policy mitigate
           │
           └── Scope ───────→ which cubes / apps / orgs are visible
```

**Rights vs data:** Capability without scope = powerful menus over *all* people. Scope without capability = you see a subset but cannot open admin tasks. Production needs both.

### Meridian RACI sketch

| Role | Workgroup | Typical capabilities | Scope |
| --- | --- | --- | --- |
| IAM lead | `MNB-WG-IAM-Ops` | Identity admin, task admin (not full SystemAdministrator) | Enterprise |
| Certifiers | `MNB-WG-Cert-Approvers` | Certification | Manager tree / assigned campaigns |
| Risk | `MNB-WG-Risk-Review` | Compliance / policy mitigate | Enterprise read + mitigate |
| Helpdesk | `MNB-WG-Helpdesk` | Limited identity view + password reset if used | Contractors or branch OU |

**Naming:** Prefix Meridian workgroups `MNB-WG-`. Never grant `SystemAdministrator` to day-to-day ops personas.

### Wrong way vs Meridian way

| Wrong way | Why it fails | Meridian way |
| --- | --- | --- |
| Shared `spadmin` for ops | No accountability; exam finding | Named users + workgroups |
| Capability-only hardening | Helpdesk still sees everyone | Add ControlledScope / populations |
| Twenty micro-capabilities day one | Unmaintainable | Bundle: Operator / Cert / Risk + break-glass |

---

## How it works

```
Login as helen.ross
        │
        ▼
 Capabilities on identity and/or MNB-WG-IAM-Ops
        │  → which menus appear (Identities, Tasks, …)
        ▼
 Scope / ControlledScope (if assigned)
        │  → which Identity cubes search returns
        ▼
 QuickLink DynamicScope (Lesson 95)
        │  → which entry points appear on home
        ▼
 Audit of capability grants + admin actions (Lesson 104)
```

| Question | Answered by |
| --- | --- |
| Can she open Tasks? | Capability / rights |
| Can she see contractor `nina.joiner` only? | Scope / population |
| Can she see Payments QuickLink? | QuickLink DynamicScope + capability |
| Can she open Debug? | Should be **no** for day-2 ops |

Workgroups stabilize ownership when people rotate: certifications and LCM escalate to `MNB-WG-*`, not to a single mailbox that goes stale when `sofia.torres` changes roles.

---

## Real-world setup (authorization design)

### Step 1 — Authorization matrix workshop

1. IAM + Risk + ITSM list day-2 actions: identity edit, task run, cert admin, SoD mitigate, plugin install, Debug.
2. Map each to workgroup + capability + scope.
3. Explicitly mark SystemAdministrator / Debug as break-glass only (Lesson 109).

### Step 2 — Populations from HR

1. Prefer HR attributes (`employeeType`, cost center, branch) for populations — not manually curated lists that drift.
2. Name `MNB-Pop-Contractors` from `employeeType=contractor`.

### Step 3 — Change control

1. Capability grants require peer review / ticket.
2. Weekly audit query for new SystemAdministrator assignments (Lesson 109 continuous monitoring).

### Step 4 — QuickLink gating

1. Attach Lesson 95 QuickLinks to required rights/scopes so visibility matches the matrix.

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq` as `spadmin`
- [ ] Identities exist: `helen.ross`, `marcus.approve`, `sofia.torres`, `kai.nguyen`
- [ ] Lesson 95 QuickLink intent table available
- [ ] Binder page: “Authorization matrix — Lesson 96”

---

## Lab procedure

### Task 1 — Inventory stock capabilities

Know what SailPoint ships before inventing Meridian bundles.

1. Open **Setup** → **Capabilities** (or Gear → Capabilities / equivalent).
2. Locate `SystemAdministrator`, `IdentityAdministrator`, `CertificationAdministrator` (or equivalent names in your build).
3. Open each and note **Included Rights** at a high level (do not edit yet).
4. Record which rights open Debug, Tasks, and Certifications.

**Expected result:** Notebook table: Capability → 2–3 key rights → Meridian owner candidate.

**If it fails:** Use Debug → Capabilities list; export one Capability XML for study.

### Task 2 — Create Meridian workgroups

Stable assignment targets beat chasing individuals.

1. Open **Setup** → **Workgroups** (or Identities → Workgroups).
2. Create `MNB-WG-IAM-Ops`. Description: “Meridian IAM operations — task owners and LCM escalations.”
3. Add members: `helen.ross`, `sofia.torres`.
4. Create `MNB-WG-Cert-Approvers` with `marcus.approve`, `amelia.brooks`.
5. Create `MNB-WG-Risk-Review` with `helen.ross` (Risk proxy in lab) and note real Risk mailbox for prod.

**Expected result:** Three `MNB-WG-*` workgroups with named Meridian members (not only `spadmin`).

**If it fails:** Create Identity objects of type workgroup via Debug import if UI path differs; keep the same names.

### Task 3 — Grant least-privilege capabilities to IAM Ops

1. Open identity `helen.ross`.
2. Assign capabilities appropriate for IAM ops (e.g., IdentityAdministrator + Task management rights) — **not** SystemAdministrator.
3. Optionally assign the same capabilities to workgroup `MNB-WG-IAM-Ops` if your UI supports workgroup capability grants.
4. Log out. Log in as `helen.ross` (reset password via `spadmin` if needed).
5. Confirm she can open Identities and Tasks; confirm Debug is **hidden** or denied.

**Expected result:** `helen.ross` operates day-to-day menus without SystemAdministrator.

**If it fails:** If menus empty, add one missing right; if Debug appears, remove SystemAdministrator / Debug rights immediately and retest.

### Task 4 — Scope helpdesk (or certifiers)

1. Create or reuse a **Population** (Advanced Analytics / Populations): e.g., `MNB-Pop-Contractors` filter `employeeType` equals contractor (or equivalent HR attribute).
2. Open **Setup** → **Scopes** (or equivalent).
3. Create scope `MNB-Scope-Helpdesk-Contractors` bound to that population.
4. Assign the scope to a helpdesk identity (use `kai.nguyen` as lab helpdesk) with limited capabilities.
5. Log in as `kai.nguyen`. Search for contractor `nina.joiner` (or a known contractor) vs an out-of-scope identity.

**Expected result:** Scoped user finds in-scope identities; out-of-scope cubes are hidden or not actionable.

**If it fails:** Document “scope UI unavailable in this lab build” and simulate with ControlledScope notes — still complete the matrix design.

### Task 5 — Authorization matrix evidence

1. Build a matrix: Workgroup | Members | Capabilities | Scope | Allowed actions | Forbidden actions.
2. Include a row proving `spadmin` is break-glass only (Lesson 109 deepens this).
3. Tie one QuickLink from Lesson 95 to a required capability/right if applicable.

**Expected result:** One-page matrix suitable for examiner walkthrough.

### Task 6 — Negative test (control proof)

Positive grants are not enough — show intentional denial.

1. As scoped/limited user, attempt to open **Debug** or edit a System Configuration object.
2. As `helen.ross`, attempt one admin action she should have and one she should not (e.g., Plugin install).
3. Screenshot denial or missing menu.

**Expected result:** Binder shows at least one intentional **denied** path.

### Task 7 — ControlledScope mechanism note

1. Document whether your IIQ build uses ControlledScope attributes on the identity, assigned Scope objects, or both.
2. For Meridian contractors, prefer population `MNB-Pop-Contractors` driven from HR `employeeType`.
3. Record cache/re-login requirement after scope assignment.

**Expected result:** Scope mechanism note specific to your build.

### Task 8 — Capability bundling guidance

Do not create twenty micro-capabilities on day one. Record Meridian starter bundles:

1. `MNB-Cap-IAM-Operator` — identities, tasks (non-debug), reports read  
2. `MNB-Cap-Cert-Operator` — certification admin without plugin install  
3. `MNB-Cap-Risk-Officer` — policy violations, mitigate  
4. Stock SystemAdministrator — break-glass only (Lesson 109)

**Expected result:** Bundle list in binder for future custom capabilities.

---

## Acceptance criteria

- [ ] Three `MNB-WG-*` workgroups exist with Meridian personas
- [ ] `helen.ross` has ops capabilities without SystemAdministrator
- [ ] Capability inventory notes completed for stock admin capabilities
- [ ] Scope design documented; lab scope applied or binder exception recorded
- [ ] Authorization matrix filed
- [ ] Negative test (denied Debug/admin) evidenced
- [ ] Bundle list + ControlledScope note written

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| helen.ross sees empty home | Missing capability / not in workgroup | Re-grant IdentityAdministrator-class rights |
| Scoped user still sees everyone | Scope not assigned / cache | Re-login; verify ControlledScope on identity |
| Workgroup cannot own task | Task expects Identity owner | Set owner to workgroup explicitly if supported |
| Capabilities duplicated | Direct + workgroup grants | Prefer workgroup grants for ops teams |
| QuickLink visible to all | No `rightRequired` / DynamicScope | Gate QuickLink (Lessons 95–97) |
| Debug still visible | SystemAdministrator lingering | Remove immediately; retest |

---

## Training binder evidence

- Screenshots: three workgroups with members
- Capability list notes for `helen.ross`
- Scope / population definition
- Authorization matrix
- Denied-action screenshot
- Bundle list + ControlledScope note

---

## Knowledge check

1. What does a Capability control vs what a Scope controls?
2. Why should `MNB-WG-IAM-Ops` not receive SystemAdministrator?
3. Name two Meridian workgroups from this lesson and one intended member each.
4. How do workgroups help certifications and escalations?
5. What examiner question does the negative test answer?
6. What HR attribute should drive `MNB-Pop-Contractors`?

### Answers

1. Capability = menus/actions (rights); Scope = which identities/objects those rights apply to.
2. Day-to-day ops must not hold break-glass rights; least privilege + auditability.
3. Examples: `MNB-WG-IAM-Ops` / `helen.ross`; `MNB-WG-Cert-Approvers` / `marcus.approve`; `MNB-WG-Risk-Review` / Risk proxy.
4. Workgroups are stable assignment targets when people rotate; certifications and LCM can route to the group.
5. “Prove helpdesk/IAM ops cannot perform unrestricted admin” — shows intentional denial.
6. `employeeType` (contractor) from the authoritative HR source.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “Capabilities”, “Workgroups”, and “Scopes” / “ControlledScope” for your version.
- [SailPoint Community / Compass](https://community.sailpoint.com/) — search “least privilege capabilities” and “identity scope helpdesk”.
- [NIST SP 800-53 AC-2 / AC-6](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — account management and least privilege for admin roles.
- [CIS Controls — Control 5 Account Management](https://www.cisecurity.org/controls/account-management) — inventory and control of admin accounts.
- [FFIEC IT Handbook — Information Security](https://ithandbook.ffiec.gov/it-booklets/information-security/) — access control expectations for banking exams.

---

## Stretch lab

Design `MNB-WG-Branch-Ops` scoped to one cost center; map which cert campaigns and access-request approvals they may touch. Do not implement in prod without CAB review. Optionally draft the Enterprise RACI deep dive table for SystemAdministrator grants (Responsible/Accountable/Consulted/Informed).

---

## Summary

- Workgroups hold people; capabilities hold rights; scopes hold data boundaries — Meridian needs all three.
- Day-2 ops run as `MNB-WG-*` with least privilege — not shared `spadmin`.
- Matrices plus denied-path screenshots are the audit artifacts examiners accept.

---

**Previous:** [Lesson 95 — QuickLinks & Custom UI](95-quicklinks-custom-ui.md)  
**Next:** [Lesson 97 — Plugin Framework Basics](97-plugin-framework-basics.md)
