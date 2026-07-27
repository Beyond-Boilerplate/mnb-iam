# Lesson 24 — Birthright Employee Role

**Level:** Intermediate  
**Track:** Roles  
**Time:** 60–90 minutes  
**Prereq:** Lesson 23 catalog sketch; MNB-ActiveDirectory (or entitlement source containing **ELDAP**) aggregated  
**Lab data:** HR identities `amelia.brooks` (active teller), `samir.hassan` (terminated); entitlement **ELDAP**

---

## Learning objectives

You will be able to:

- Create bundle **`MNB-Birthright-Employee`** containing only **ELDAP**
- Write an assignment rule/selector for active employees (`workerType=Employee`, active status)
- Run identity refresh with role assignment enabled and verify birthright on `amelia.brooks`
- Prove terminated identities (e.g. `samir.hassan`) do not retain birthright assignment intent
- Document birthright composition, exclusions, and joiner SLA impact

---

## Why this matters

Joiners should be productive on day one without tickets for baseline directory access. Birthright is Meridian’s promise—and a liability if over-scoped. A birthright that includes wire or cloud privilege is an automatic control failure.

**Control / audit:** Birthright composition is dual-approved (IAM + Risk). Evidence = role definition + assignment criteria + sample identities (positive and negative). Examiners ask: “What does every employee get automatically, and what is excluded?”

---

## Concepts

**Birthright role:** Automatically assigned when identity matches criteria; typically deprovisioned when criteria fail (via refresh / lifecycle).

```
IF identity has MNB-HR account
 AND status = active (1)
 AND workerType = Employee
THEN assign MNB-Birthright-Employee
         └── entitlement ELDAP (Enterprise Directory)
```

| Include | Exclude |
| --- | --- |
| Active Employee | Contractor (separate pack later) |
| ELDAP only | WIRE_*, AWS_ADMIN, SAP_FI, PRIV_BREAK |
| Tellers, analysts, specialists | Terminated / status=0 |

**IIQ terms:** Bundle (role), assignment rule / selector, role detection vs assignment (Lesson 27), provisioning policy (may be stubbed in file lab).

---

## Before you start

- [ ] IIQ at `http://localhost:8080/identityiq` as `spadmin`
- [ ] ELDAP exists as a managed entitlement (dictionary Lesson 10; AD or IT inventory)
- [ ] `amelia.brooks` cube exists from HR (`MNB00097`, TEL01, active)
- [ ] Catalog v0 lists birthright as ELDAP-only
- [ ] Backup note: role XML export path if your lab exports bundles

---

## Lab procedure

### Task 1 — Confirm ELDAP entitlement object

1. Navigate to Applications / Entitlements (or equivalent Managed Attribute view).
2. Find **ELDAP** — display name should resemble “Enterprise Directory”.
3. Confirm risk tier medium (from dictionary)—birthright-worthy, not critical payment privilege.

**Expected result:** ELDAP located; you know which application owns it (typically MNB-ActiveDirectory).

**If it fails:** Aggregate AD/IT inventory; promote group/entitlement; apply dictionary display name.

### Task 2 — Create `MNB-Birthright-Employee`

1. Open **Roles** / **Business Roles** / Bundle editor (or equivalent menu path).
2. Create new role named exactly `MNB-Birthright-Employee`.
3. Set description: “Baseline directory access for active Meridian employees. No payment or cloud privilege.”
4. Set owner conceptually to IAM Engineering.
5. Mark **not requestable** (birthright is automatic—users should not “request birthright”).

**Expected result:** Role object saved with MNB- prefix and clear business description.

**If it fails:** Check required fields (type/owner); use Debug to confirm Bundle created.

### Task 3 — Attach ELDAP only

1. Add required entitlement/profile: **ELDAP** only.
2. Save. Re-open and verify no WIRE_INIT, AWS_ADMIN, or CRM slipped in.

**Expected result:** Composition list length = 1 (ELDAP).

**If it fails:** Remove extras immediately; treat as Sev-1 design defect if critical ents were added.

### Task 4 — Assignment rule for active employees

1. Configure assignment rule / identity selector approximately:
   - Application account on MNB-HR present (optional but recommended)
   - `status` active / `1`
   - `workerType` equals `Employee`
2. Explicitly **exclude** `Contractor` (and terminated).
3. Document the rule in binder in plain English and as pseudo-logic.

**Expected result:** Rule text captured; matches Lesson 23 intent.

**If it fails:** If UI rule builder differs by IIQ version, implement closest Match Filter / BeanShell per your lab guide—keep logic identical.

### Task 5 — Refresh with role assignment

1. Open Tasks → **Refresh MNB Identities** (or create/run identity refresh).
2. Enable options equivalent to: refresh assigned roles / provision assigned roles (as available in lab).
3. Scope to a population including `amelia.brooks` if full refresh is heavy.
4. Run task; wait for success.

**Expected result:** Task completes without error; check task result for role assignment activity if logged.

**If it fails:** Review task arguments; ensure role is enabled/active; check identity filter not excluding tellers.

### Task 6 — Positive verify: `amelia.brooks`

1. Open identity `amelia.brooks`.
2. Inspect Roles tab (Assigned / detected sections as shown).
3. Confirm `MNB-Birthright-Employee` appears as **assigned**.
4. Confirm she is active Employee teller (TEL01)—birthright expected.

**Expected result:** Assigned birthright role present on Amelia.

**If it fails:** Verify HR attributes on cube (`workerType`, status); re-run refresh; check rule.

### Task 7 — Negative verify: terminated / non-employee

1. Open `samir.hassan` (terminated developer pattern from earlier lessons).
2. Confirm birthright is **not** assigned (or is flagged for removal if previously assigned).
3. Optional: spot-check a Contractor identity—should not receive Employee birthright.

**Expected result:** Terminated persona lacks active birthright assignment intent.

**If it fails:** Tighten rule; ensure status mapping uses HR authoritative status (Lesson 22).

### Task 8 — Birthright control document

1. Write `MNB-Ctrl-Birthright-Employee` including:
   - Composition: ELDAP
   - Inclusion: active Employee
   - Exclusions: contractors, privileged ents, payment ents
   - Joiner SLA: identity + birthright within same refresh cycle after HR active (target ≤ 1 hour in production pattern)

**Expected result:** One-page control doc suitable for exam binder.

---

## Acceptance criteria

- [ ] `MNB-Birthright-Employee` exists with ELDAP only
- [ ] Assignment rule limits to active Employees
- [ ] `amelia.brooks` shows assigned birthright after refresh
- [ ] Terminated example does not keep birthright intent
- [ ] Control document completed with exclusions

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Role created but never assigned | Refresh without assign option | Enable assign/provision roles on refresh |
| Everyone gets birthright including contractors | Rule too broad | Add workerType=Employee |
| Amelia missing role | Inactive flag / wrong type | Fix HR attributes; re-aggregate HR; refresh |
| Provisioning errors for ELDAP | No connector provisioning in file lab | Document as detection/assignment-only lab; still verify assignment |
| Birthright contains extras | Editing mistake | Remove; re-approve composition |

---

## Training binder evidence

- Screenshot: role definition composition (ELDAP only)
- Screenshot: assignment rule / selector
- Screenshot: `amelia.brooks` Roles tab with birthright
- Screenshot: `samir.hassan` without birthright (annotated)
- Control doc `MNB-Ctrl-Birthright-Employee`

**Control owner:** IAM Engineering  
**Approver:** Risk (composition)  
**SLA:** Birthright assignment same cycle as HR active for joiners

---

## Knowledge check

1. What entitlement is in `MNB-Birthright-Employee`?
2. Are contractors included in this role?
3. How do leavers lose birthright in the intended design?
4. Should users request birthright from the catalog?
5. Why is `amelia.brooks` a good positive test?

### Answers

1. ELDAP only.
2. No—Employee workerType only; contractors need a tighter separate pack.
3. When HR status becomes inactive/terminated, refresh/lifecycle removes assignment (and provisioning disables/removes access in full implementations).
4. No—automatic only; not requestable.
5. She is an active Employee teller with ELDAP-appropriate baseline and no treasury privilege expectation.

---

## Stretch lab

- Create `MNB-Birthright-Contractor` with ELDAP only **or** a time-boxed directory group; exclude all critical ents; assignment `workerType=Contractor` AND active.
- Add audit note: any birthright composition change requires change ticket + Risk approval.
- Compare Amelia vs `nina.joiner` after Lesson 29—both tellers should converge on same birthright.

---

## Summary

- Birthright is minimal, automatic, and boring by design—ELDAP for active employees.
- `amelia.brooks` validates positive assignment; terminated identities validate exclusion.
- Over-scoping birthright is how banks accidentally automate privilege.

---

**Previous:** [Lesson 23 — Role Model Introduction](23-role-model-intro.md)  
**Next:** [Lesson 25 — Department & Job-Based Roles](25-dept-job-roles.md)
