# Lesson 24 — Birthright Employee Role

**Level:** Intermediate  
**Track:** Roles  
**Time:** 60–90 minutes  
**Prereq:** Lesson 23 catalog sketch; MNB-ActiveDirectory (or entitlement source containing **ELDAP**) aggregated  

**Lab data:**
- HR identities: `amelia.brooks` (active teller), `samir.hassan` (terminated)
- Entitlement: **ELDAP** (Enterprise Directory)
- Catalog intent: Lesson 23 `MNB-Birthright-Employee` = ELDAP only

---

## Learning objectives

You will be able to:

- Create bundle **`MNB-Birthright-Employee`** containing only **ELDAP**
- Write an assignment rule/selector for active employees (`employeeType=Employee`, `inactive=false`)
- Run identity refresh with role assignment enabled and verify birthright on `amelia.brooks`
- Prove terminated identities (e.g. `samir.hassan`) do not retain birthright assignment intent
- Document birthright composition, exclusions, and joiner SLA impact
- Explain why contractors (`raj.external`) must never inherit this employee pack

---

## Why this matters

**Business.** Joiners should be productive on day one without tickets for baseline directory access. When `amelia.brooks` starts as a teller, Meridian’s promise is: HR goes active → refresh assigns birthright → ELDAP lands. Birthright that includes wire or cloud privilege turns that promise into an automatic control failure—every joiner becomes a privileged account factory.

**Control / audit.** Birthright composition is dual-approved (IAM + Risk). Evidence = role definition + assignment criteria + sample identities (positive and negative). Examiners ask: *“What does every employee get automatically, and what is excluded?”* Your answer must name ELDAP and explicitly exclude `WIRE_*`, `AWS_ADMIN`, `SAP_FI`, and `PRIV_BREAK`.

---

## Concepts

### Birthright is normative automation

A **birthright role** is automatically assigned when an identity matches criteria and typically deprovisioned when criteria fail (via refresh / lifecycle). It is normative—“you should have this”—not a detection of what you already hold (Lesson 27).

```
IF identity has MNB-HR account
 AND status = active (1)
 AND employeeType = Employee
THEN assign MNB-Birthright-Employee
         └── entitlement ELDAP (Enterprise Directory)
```

| Include | Exclude |
| --- | --- |
| Active Employee | Contractor (`raj.external` and peers) |
| ELDAP only | WIRE_*, AWS_ADMIN, SAP_FI, PRIV_BREAK |
| Tellers, analysts, specialists | Terminated (`inactive=true` / `status=Terminated`, e.g. `samir.hassan`) |

### Why ELDAP alone

Directory login is the shared baseline for employees. Payment initiate, cloud admin, and break-glass are never “everyone needs it on day one.” Over-scoping birthright is how banks accidentally automate privilege. Under-scoping (no birthright at all) floods the service desk and creates shadow access.

### Contractors are a different promise

`raj.external` is a Cloud Platform Engineer contractor with vendor email and `AWS_ADMIN` risk. He must **not** receive `MNB-Birthright-Employee`. Lesson 32 defines a stricter contingent path. If your assignment rule forgets `employeeType=Employee`, every contractor inherits employee baseline—and examiners will find it in population reports.

---

## How it works

Identity refresh is the engine that turns the rule into cube state. Without assign-roles options enabled, the Bundle exists but nobody receives it.

```
MNB-HR aggregation ──► identity attributes (employeeType, status)
        │
        ▼
Refresh MNB Identities (assign roles ON)
        │
        ├── match rule? ──yes──► Assigned: MNB-Birthright-Employee
        │                              └── plan may grant ELDAP
        └── no match ──► remove / do not assign birthright
```

| Step | IIQ object | Meridian evidence |
| --- | --- | --- |
| Define | Bundle `MNB-Birthright-Employee` | Composition screenshot (ELDAP only) |
| Select | Assignment rule / Match Filter | Plain-English + pseudo-logic in binder |
| Enforce | Identity Refresh task | Task Result + Amelia Roles tab |
| Negative proof | Terminated / Contractor cubes | Samir without birthright; Raj excluded |

**IIQ terms:** Bundle (role), assignment rule / selector, role detection vs assignment (Lesson 27), provisioning policy (may be stubbed in file lab—still verify **assignment**).

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

Birthright can only grant what exists as a managed entitlement. Confirm the building block before the Bundle.

1. Navigate to Applications / Entitlements (or equivalent Managed Attribute view).
2. Find **ELDAP** — display name should resemble “Enterprise Directory”.
3. Confirm risk tier medium (from dictionary)—birthright-worthy, not critical payment privilege.

**Expected result:** ELDAP located; you know which application owns it (typically MNB-ActiveDirectory).

**If it fails:** Aggregate AD/IT inventory; promote group/entitlement; apply dictionary display name.

### Task 2 — Create `MNB-Birthright-Employee`

Production teams treat this name as permanent—certifications and reports will key off it.

1. Open **Roles** / **Business Roles** / Bundle editor (or equivalent menu path).
2. Create new role named exactly `MNB-Birthright-Employee`.
3. Set description: “Baseline directory access for active Meridian employees. No payment or cloud privilege.”
4. Set owner conceptually to IAM Engineering.
5. Mark **not requestable** (birthright is automatic—users should not “request birthright”).

**Expected result:** Role object saved with MNB- prefix and clear business description.

**If it fails:** Check required fields (type/owner); use Debug to confirm Bundle created.

### Task 3 — Attach ELDAP only

Composition is the control. One extra critical entitlement here is a Sev-1 design defect.

1. Add required entitlement/profile: **ELDAP** only.
2. Save. Re-open and verify no WIRE_INIT, AWS_ADMIN, or CRM slipped in.

**Expected result:** Composition list length = 1 (ELDAP).

**If it fails:** Remove extras immediately; treat critical ents as Sev-1 if added by mistake.

### Task 4 — Assignment rule for active employees

The rule is the difference between “every human” and “active employees only.”

1. Configure assignment rule / identity selector approximately:
   - Application account on MNB-HR present (optional but recommended)
   - `status` active / `1`
   - `employeeType` equals `Employee`
2. Explicitly **exclude** `Contractor` (and terminated).
3. Document the rule in binder in plain English and as pseudo-logic.

**Expected result:** Rule text captured; matches Lesson 23 intent; Raj’s employeeType would not match.

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

**If it fails:** Verify HR attributes on cube (`employeeType`, status); re-run refresh; check rule.

### Task 7 — Negative verify: terminated / non-employee

Positive proof without negative proof fails exams—examiners sample leavers and contractors.

1. Open `samir.hassan` (terminated developer pattern from earlier lessons).
2. Confirm birthright is **not** assigned (or is flagged for removal if previously assigned).
3. Optional: spot-check `raj.external`—Contractor must not receive Employee birthright.

**Expected result:** Terminated persona lacks active birthright assignment intent; contractor excluded if checked.

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

- [ ] **Bank craft exit:** Birthright role works in IIQ; optional export to `config/Bundle/MNB-Bundle-Birthright-Employee.xml`

- [ ] `MNB-Birthright-Employee` exists with ELDAP only
- [ ] Assignment rule limits to active Employees
- [ ] `amelia.brooks` shows assigned birthright after refresh
- [ ] Terminated example does not keep birthright intent
- [ ] Control document completed with exclusions (contractors named)

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Role created but never assigned | Refresh without assign option | Enable assign/provision roles on refresh |
| Everyone gets birthright including contractors | Rule too broad | Add employeeType=Employee |
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
6. Why check `raj.external` as a negative sample?

### Answers

1. ELDAP only.
2. No—Employee employeeType only; contractors need a tighter separate pack (Lesson 32).
3. When HR status becomes inactive/terminated, refresh/lifecycle removes assignment (and provisioning disables/removes access in full implementations).
4. No—automatic only; not requestable.
5. She is an active Employee teller with ELDAP-appropriate baseline and no treasury privilege expectation.
6. He is Contractor—if employee birthright assigns to him, the rule is broken and contingent controls fail.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “role assignment” and “birthright” for refresh options and Bundle profiles.
- [SailPoint Community](https://community.sailpoint.com/) — search “assignment rule Match Filter” for version-specific selector patterns.
- [NIST SP 800-53 AC-2](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — account management; birthright is automated account/entitlement assignment with defined population.
- [NIST SP 800-53 AC-6](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — least privilege; the reason birthright stays ELDAP-only.
- [CIS Controls v8 — Control 5 & 6](https://www.cisecurity.org/controls) — account and access control management baselines for joiner automation.

---

## Stretch lab

- Create `MNB-Birthright-Contractor` with ELDAP only **or** a time-boxed directory group; exclude all critical ents; assignment `employeeType=Contractor` AND active.
- Add audit note: any birthright composition change requires change ticket + Risk approval.
- Compare Amelia vs `nina.joiner` after Lesson 29—both tellers should converge on same birthright.

---

## Summary

- Birthright is minimal, automatic, and boring by design—ELDAP for active employees.
- `amelia.brooks` validates positive assignment; terminated and contractor identities validate exclusion.
- Over-scoping birthright is how banks accidentally automate privilege.

---

**Previous:** [Lesson 23 — Role Model Introduction](23-role-model-intro.md)  
**Next:** [Lesson 25 — Department & Job-Based Roles](25-dept-job-roles.md)
