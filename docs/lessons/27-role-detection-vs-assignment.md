# Lesson 27 — Role Detection vs Assignment

**Level:** Intermediate  
**Track:** Roles  
**Time:** 45–60 minutes  
**Prereq:** Lesson 26; birthright and job roles assigned (two-tier IT + business); some identities hold entitlements without matching assigned privileged roles  

**Lab data:**
- Developer / cloud personas (e.g. identities with AWS_ADMIN on account)
- `amelia.brooks` birthright assignee
- Dual-control reference: `priya.wire` / `marcus.approve` assigned job packs

---

> **Verify:** Analysis / paperwork — inspect cubes and write certifier policy. No new roles to create. Academy **Verify now** is disabled; mark the binder complete when acceptance criteria are done.

## Learning objectives

You will be able to:

- Identify **detected** vs **assigned** roles on an identity cube
- Map those signals to Meridian’s two-tier model (**business** = assigned / normative; **IT** = often detected / analytical)
- Use detection to find outliers (entitlements present without approved assigned business roles)
- Confirm which identity refresh options affect assignment vs detection
- Decide what managers should certify (roles, entitlements, or hybrid by risk)
- Write a manager-ready narrative that prevents wrong keep/revoke decisions

---

## Why this matters

**Business.** Detection explains what you **already have**; assignment decides what you **should have**. Confusing them breaks certifications: revoking a “detected only” signal is not the same as removing an assigned birthright. Managers who treat all role chips as identical will make wrong keep/revoke decisions—and tellers like `amelia.brooks` can lose baseline directory access because someone “cleaned up detected noise.”

**Control / audit.** Procedures must define whether campaigns certify assigned roles, detected roles, raw entitlements, or a mix. Meridian’s emerging standard: **assigned business roles for baseline/job packs; entitlements (or privileged assigned business roles) for critical access.** Examiners ask: *“How do you distinguish approved access from merely observed access?”*

---

## Concepts

### Normative vs analytical (and where two-tier fits)

| Concept | Nature | Typical Meridian object | Question it answers | Actionability |
| --- | --- | --- | --- | --- |
| **Assignment** | Normative | **Business** roles (`MNB-Birthright-*`, `MNB-Role-*`) via Match List / request | What should this identity have per policy? | Provision / deprovision via role lifecycle |
| **Detection** | Analytical | Often **IT** packs (`MNB-IT-*`) whose Entitlement profiles match accounts | What packs resemble entitlements already held? | Insight / outlier hunting; not automatic approval |

Stock IIQ puts entitlement **profiles** on type **it**. Refresh **detects** those IT roles when account entitlements match. Refresh **assigns** business roles when Match Lists / requests say so. That is why Amelia may show **Assigned** `MNB-Birthright-Employee` and also **Detected** `MNB-IT-ELDAP` if ELDAP is on her account—both can be healthy.

```
Entitlements on accounts ──► Detection ──► “Detected: MNB-IT-Developer” (analytical)
Assignment rules / requests ──► Assignment ──► “Assigned: MNB-Role-Developer” (normative)
                                                      └── Required ──► MNB-IT-Developer
```

### Outlier pattern — privilege without approved role

Identity has AWS_ADMIN entitlement on MNB-AWS-Cloud but **no** assigned `MNB-Role-CloudAdmin`. That is expected if CloudAdmin is request-only and not yet granted—or a standing privilege defect (e.g. `raj.external` residual, or a cloud engineer granted outside LCM). Detection may light up `MNB-IT-CloudAdmin` (or a cloud-admin-like profile) once Lesson 28 exists; detection is **not** approval.

### Birthright pattern

`amelia.brooks` should show **assigned** `MNB-Birthright-Employee`. Detection may also light up `MNB-IT-ELDAP` if ELDAP matches the IT profile. Do **not** revoke birthright because an IT pack “also shows as detected.”

### Dual-control check

`priya.wire` should show **assigned** `MNB-Role-WireInitiator`; `marcus.approve` should not. Detection may show `MNB-IT-WireInit` only when WIRE_INIT is on the account. Trust **assignment** for normative dual-control decisions—and hunt residual **entitlements** when accounts still hold WIRE_* after a mover.

---

## How it works

Refresh can assign, detect, both, or neither—depending on task options. Certification policy must name which signal managers act on.

```
Identity Refresh  (Setup → Tasks → Refresh MNB Roles / Identities)
   ├── Assign roles ON  → evaluate business Match Lists / requests → Assigned business roles
   └── Detect roles ON  → match IT profiles to ents → Detected IT roles

Certification campaign
   ├── Birthright / job packs     → certify Assigned business roles
   ├── Critical ents (WIRE_*, AWS_ADMIN, SAP_FI) → certify ents / privileged assigned business roles
   └── Unknown direct ents        → entitlement line items
```

| Refresh mistake | Symptom | Fix |
| --- | --- | --- |
| Assign OFF | Birthright/job business packs never appear | Enable assign roles |
| Detect OFF | No analytical IT matches | Enable detect if you use outlier hunting |
| Certify “all role chips” | Managers revoke detection noise / IT packs | Train with Task 4 sentences |

---

## Before you start

- [ ] Lessons 24–26 roles exist (IT + business pairs) and refresh has been run
- [ ] At least one identity with AWS_ADMIN account entitlement (e.g. from MNB-AWS-Cloud extract)
- [ ] `amelia.brooks` available as birthright control sample
- [ ] Notebook headings: Normative vs Analytical; Assigned business vs Detected IT

---

## Lab procedure

### Task 1 — Inspect a job-role identity

Learn the UI labels on a clean, expected assignee before hunting outliers.

1. **Identities → Identity Warehouse** → open a developer expected to hold DWRP (e.g. `diego.hayes`).
2. Open the **Roles** tab (wording varies by IIQ version/UI).
3. Note sections/labels for **Assigned** vs **Detected**.
4. Record:
   - **Assigned:** expect `MNB-Role-Developer` and usually `MNB-Birthright-Employee`
   - **Detected (if present):** may show `MNB-IT-Developer` and/or `MNB-IT-ELDAP` when account ents match those IT profiles

**Expected result:** You can name which MNB **business** roles are assigned vs which **IT** packs (if any) are detected.

**If it fails:** **Setup → Tasks** → run Refresh with detect/assign options; confirm entitlements correlated on Accounts tab. If UI shows a single Roles list, use Debug Identity XML (`roleAssignments` vs detected) — see Troubleshooting.

### Task 2 — Inspect birthright assignment

1. Open `amelia.brooks` → **Roles**.
2. Confirm `MNB-Birthright-Employee` is **Assigned** (normative).
3. Note any **Detected** `MNB-IT-ELDAP` (analytical match on ELDAP)—healthy, not a reason to revoke.

**Expected result:** Clear evidence birthright is assigned, not merely detected noise.

**If it fails:** Revisit Lesson 24 Match List + Required → `MNB-IT-ELDAP`; re-run refresh with assign ON.

### Task 3 — Privileged outlier hunt

This is the finding that feeds Lesson 28 and monthly privileged certs.

1. Find an identity with **AWS_ADMIN** on an account (entitlement search or known cloud engineers / `jordan.reed` / `raj.external`).
2. Check whether `MNB-Role-CloudAdmin` is **Assigned** (likely **no** if not created/requested yet).
3. Classify:
   - **Expected gap:** request-only business role not granted; entitlement may still be residual/standalone → remediation candidate
   - **Design OK interim:** after Lesson 28, detection may show `MNB-IT-CloudAdmin` without an assigned business role—still not approval

**Expected result:** Written outlier case file: identity, entitlements, assigned **business** roles, detected IT (if any), risk note.

**If it fails:** Aggregate MNB-AWS-Cloud; correlate accounts; then re-check.

### Task 4 — Meridian narrative (manager-ready)

Certifier training fails without plain language.

1. Write exactly two sentences managers can read in training:
   - Sentence A: **Assigned** roles = access Meridian formally decided you should have (desk / birthright business packs).
   - Sentence B: **Detected** roles = IdentityIQ noticed your current entitlements resemble an IT pack—investigate, don’t assume approval.
2. Add a warning: Do not revoke birthright because `MNB-IT-ELDAP` also shows as detected.

**Expected result:** Two-sentence card stored in binder for certifier training.

### Task 5 — Refresh flags literacy

1. **Setup → Tasks** → open **`Refresh MNB Roles`** (or **`Refresh MNB Identities`**).
2. Identify options related to **assign** roles, **detect** roles, and provisioning.
3. Document which checkbox does what in your lab build.
4. Run a scoped refresh if needed to observe differences (assign on vs detect on).

**Expected result:** Mini runbook: “To enforce birthright/job **assignment**, enable _____; to refresh **detection** of IT packs, enable _____.”

**If it fails:** Use product docs/help for your IIQ 8.5 build—still capture lab-specific labels.

### Task 6 — Certification implication decision

1. Propose Meridian standard:

| Access class | Certify |
| --- | --- |
| Birthright / job packs | **Assigned business** roles |
| Critical ents (WIRE_*, AWS_ADMIN, SAP_FI) | Entitlements and/or privileged **assigned business** roles |
| Unknown direct ents | Entitlement line items |
| Detected IT packs alone | Do **not** treat as approval—use for hunting |

2. Note that Lessons 43–46 will implement campaigns—this lesson locks the policy intent.

**Expected result:** One policy paragraph approved in binder.

### Task 7 — Anti-pattern checklist

1. Confirm you will never:
   - Delete birthright because `MNB-IT-ELDAP` “also shows as detected”
   - Treat detection of an IT pack as proof of manager approval
   - Ignore AWS_ADMIN simply because no CloudAdmin **business** role is assigned

**Expected result:** Checklist initialed.

### Task 8 — Dual-control spot-check

1. Open `priya.wire` and `marcus.approve` → **Roles**.
2. Confirm **Assigned** `MNB-Role-WireInitiator` only on Priya (baseline).
3. Note any **Detected** `MNB-IT-WireInit` (or shared department noise) that might confuse a certifier who sees both as “Treasury.”

**Expected result:** Written note: assignment of the **business** role enforces dual control; detection alone does not.

---

## Acceptance criteria

- [ ] Assigned vs detected identified on at least two cubes (business vs IT called out where visible)
- [ ] Outlier case file for AWS_ADMIN without CloudAdmin **business** assignment
- [ ] Manager-ready two-sentence narrative written
- [ ] Refresh assign/detect options documented
- [ ] Certification target policy drafted

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No detected roles ever | Detect option off / IT profiles empty | Enable detect; confirm `MNB-IT-*` Entitlements profiles exist (Lessons 24–25) |
| Assigned empty after refresh | Assign option off / Match List fail | Enable assign; fix business role rules |
| Only IT names appear “assigned” | Misread UI / wrong expectation | Business roles are assigned; IT packs are usually detected when ents match |
| UI shows single Roles list | Version/UI simplification | Debug → Identity XML: assignment vs detected structures |
| Manager confusion in UAT | Training gap | Use Task 4 sentences in cert kickoff deck |

---

## Training binder evidence

- Screenshots: Amelia **Assigned** birthright; note Detected `MNB-IT-ELDAP` if present
- Screenshot: developer **Assigned** `MNB-Role-Developer` (+ Detected IT if shown)
- Outlier case file (AWS_ADMIN without privileged business assignment)
- Two-sentence manager narrative card
- Refresh task option notes
- Certify-roles-vs-ents policy paragraph

**Control owner:** IAM Engineering (config) + Risk (certify standard)  
**Examiner question:** “How do you distinguish approved access from merely observed access?”

---

## Knowledge check

1. Detection vs assignment—which is normative, and which Meridian role **type** usually carries it?
2. Why can AWS_ADMIN appear without an assigned CloudAdmin role?
3. What should managers certify for birthright?
4. What refresh mistake blocks birthright enforcement?
5. Is detection of `MNB-IT-ELDAP` alone proof Amelia should keep ELDAP?
6. How should dual-control wire access be certified—by detection of “Treasury-like” access?

### Answers

1. Assignment is normative—on **business** roles. Detection is analytical—often on **IT** packs with entitlement profiles.
2. Privileged business role is request-only or not yet granted; entitlement may be standing residual or directly assigned—still a risk to review.
3. The **assigned** birthright **business** role (and/or underlying ELDAP if certifying ents)—not “detected IT noise” as the sole signal.
4. Running refresh without role **assignment** options enabled.
5. No—detection is not approval; her **assigned** birthright is the normative grant.
6. No—certify assigned WireInitiator/WireApprover **business** roles and/or WIRE_* entitlements; do not trust a vague detected “Treasury” profile.

---

## Further reading

- [SailPoint IdentityIQ — Role Modeling](https://documentation.sailpoint.com/identityiq/help/roles_groups_and_populations/roles/role_modeling/index.html) — assigned vs detected semantics with business/IT types.
- [SailPoint Community](https://community.sailpoint.com/) — search “detected vs assigned” for certifier confusion patterns and training tips.
- [NIST SP 800-53 AC-2](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — account management; assigned access as the authorized inventory.
- [NIST SP 800-53 AC-6](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — least privilege reviews should act on authorized grants, not mere observation.
- [FFIEC IT Handbook — Information Security](https://ithandbook.ffiec.gov/) — access review expectations that require clear “approved vs observed” language.

---

## Stretch lab

- Propose hybrid cert: role-level for retail birthright populations; entitlement-level for Treasury and Cloud.
- Build population `MNB-Pop-Priv-Ent-Without-Role` for AWS_ADMIN holders lacking CloudAdmin **business** assignment.
- Export one Identity XML snippet (redact) showing assignment vs detected structures for training.

---

## Summary

- Assignment = policy decision on **business** roles; detection = analytical match—often on **IT** packs—never conflate them.
- Outliers with critical entitlements but no privileged **assigned** business role are remediation fuel.
- Certify standards must be explicit before campaign design.

---

**Previous:** [Lesson 26 — IT Role Packaging & Least Privilege](26-it-role-packaging.md)  
**Next:** [Lesson 28 — Privileged Access Role Design](28-privileged-access-roles.md)
