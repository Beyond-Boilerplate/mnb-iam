# Lesson 27 — Role Detection vs Assignment

**Level:** Intermediate  
**Track:** Roles  
**Time:** 45–60 minutes  
**Prereq:** Lesson 26; birthright and job roles assigned; some identities hold entitlements without matching assigned privileged roles  

**Lab data:**
- Developer / cloud personas (e.g. identities with AWS_ADMIN on account)
- `amelia.brooks` birthright assignee
- Dual-control reference: `priya.wire` / `marcus.approve` assigned job packs

---

## Learning objectives

You will be able to:

- Identify **detected** vs **assigned** roles on an identity cube
- Explain the difference in Meridian business language (analytical vs normative)
- Use detection to find outliers (entitlements present without approved assigned roles)
- Confirm which identity refresh options affect assignment vs detection
- Decide what managers should certify (roles, entitlements, or hybrid by risk)
- Write a manager-ready narrative that prevents wrong keep/revoke decisions

---

## Why this matters

**Business.** Detection explains what you **already have**; assignment decides what you **should have**. Confusing them breaks certifications: revoking a “detected only” signal is not the same as removing an assigned birthright. Managers who treat all role chips as identical will make wrong keep/revoke decisions—and tellers like `amelia.brooks` can lose baseline directory access because someone “cleaned up detected noise.”

**Control / audit.** Procedures must define whether campaigns certify assigned roles, detected roles, raw entitlements, or a mix. Meridian’s emerging standard: **assigned roles for baseline/job packs; entitlements (or privileged roles) for critical access.** Examiners ask: *“How do you distinguish approved access from merely observed access?”*

---

## Concepts

### Normative vs analytical

| Concept | Nature | Question it answers | Actionability |
| --- | --- | --- | --- |
| **Assignment** | Normative | What should this identity have per policy/rules/requests? | Provision / deprovision via role lifecycle |
| **Detection** | Analytical | What role profiles match entitlements already on accounts? | Insight / outlier hunting; not automatic approval |

```
Entitlements on accounts ──► Detection engine ──► “Detected: looks like Developer”
Assignment rules / requests ──► Assignment ──► “Assigned: MNB-Role-Developer”
```

### Outlier pattern — privilege without approved role

Identity has AWS_ADMIN entitlement on MNB-AWS-Cloud but **no** assigned `MNB-Role-CloudAdmin`. That is expected if CloudAdmin is request-only and not yet granted—or a standing privilege defect (e.g. `raj.external` residual, or a cloud engineer granted outside LCM). Detection may light up a cloud-admin-like profile; detection is **not** approval.

### Birthright pattern

`amelia.brooks` should show **assigned** `MNB-Birthright-Employee`; detection may also light up if ELDAP matches the birthright profile. Do not revoke birthright because it “also shows as detected.”

### Dual-control check

`priya.wire` should show **assigned** WireInitiator; `marcus.approve` should not. If detection claims both “look like” wire operators because of shared department groups, trust assignment for normative decisions—and hunt residuals as entitlements.

---

## How it works

Refresh can assign, detect, both, or neither—depending on task options. Certification policy must name which signal managers act on.

```
Identity Refresh
   ├── Assign roles ON  → evaluate rules/requests → Assigned roles on cube
   └── Detect roles ON  → match profiles to ents → Detected roles on cube

Certification campaign
   ├── Birthright / job packs     → certify Assigned roles
   ├── Critical ents (WIRE_*, AWS_ADMIN, SAP_FI) → certify ents / privileged assigned roles
   └── Unknown direct ents        → entitlement line items
```

| Refresh mistake | Symptom | Fix |
| --- | --- | --- |
| Assign OFF | Birthright/job packs never appear | Enable assign roles |
| Detect OFF | No analytical matches | Enable detect if you use outlier hunting |
| Certify “all role chips” | Managers revoke detection noise | Train with Task 4 sentences |

---

## Before you start

- [ ] Lessons 24–26 roles exist and refresh has been run
- [ ] At least one identity with AWS_ADMIN account entitlement (e.g. from MNB-AWS-Cloud extract)
- [ ] `amelia.brooks` available as birthright control sample
- [ ] Notebook headings: Normative vs Analytical

---

## Lab procedure

### Task 1 — Inspect a job-role identity

Learn the UI labels on a clean, expected assignee before hunting outliers.

1. Open a developer identity expected to hold DWRP (e.g. `diego.hayes`).
2. Go to the Roles area of the cube.
3. Note sections/labels for assigned vs detected (wording varies by IIQ version/UI).
4. Record: which MNB roles appear, and under which category.

**Expected result:** `MNB-Role-Developer` and/or birthright visible; you can say which are assigned.

**If it fails:** Run Refresh with detect/assign options; confirm entitlements correlated on accounts.

### Task 2 — Inspect birthright assignment

1. Open `amelia.brooks`.
2. Confirm `MNB-Birthright-Employee` is **assigned** (normative).
3. Note any detection flags for the same profile.

**Expected result:** Clear evidence birthright is assigned, not merely detected noise.

**If it fails:** Revisit Lesson 24 assignment rule and refresh flags.

### Task 3 — Privileged outlier hunt

This is the finding that feeds Lesson 28 and monthly privileged certs.

1. Find an identity with **AWS_ADMIN** on an account (search entitlement or open known cloud engineers / `jordan.reed` / `raj.external` lab pattern).
2. Check whether `MNB-Role-CloudAdmin` is assigned (likely **no** if not created/requested yet).
3. Classify:
   - **Expected gap:** request-only role not granted; entitlement may still be residual/standalone → remediation candidate
   - **Design OK interim:** detection may show a cloud-admin-like profile if you defined detection profiles

**Expected result:** Written outlier case file: identity, entitlements, assigned roles, risk note.

**If it fails:** Aggregate MNB-AWS-Cloud; correlate accounts; then re-check.

### Task 4 — Meridian narrative (manager-ready)

Certifier training fails without plain language.

1. Write exactly two sentences managers can read in training:
   - Sentence A: Assigned roles = access Meridian formally decided you should have.
   - Sentence B: Detected roles = IdentityIQ noticed your current entitlements resemble a role—investigate, don’t assume approval.
2. Add a warning: Do not revoke birthright because you misunderstood detection.

**Expected result:** Two-sentence card stored in binder for certifier training.

### Task 5 — Refresh flags literacy

1. Open the Refresh MNB Identities task definition.
2. Identify options related to **assign** roles, **detect** roles, and provisioning.
3. Document which checkbox does what in your lab build.
4. Run a scoped refresh if needed to observe differences (assign on vs detect on).

**Expected result:** Mini runbook: “To enforce birthright assignment, enable _____; to refresh detection analysis, enable _____.”

**If it fails:** Use product docs/help for your IIQ 8.5 build—still capture lab-specific labels.

### Task 6 — Certification implication decision

1. Propose Meridian standard:

| Access class | Certify |
| --- | --- |
| Birthright / job packs | Assigned roles |
| Critical ents (WIRE_*, AWS_ADMIN, SAP_FI) | Entitlements and/or privileged assigned roles |
| Unknown direct ents | Entitlement line items |

2. Note that Lessons 43–46 will implement campaigns—this lesson locks the policy intent.

**Expected result:** One policy paragraph approved in binder.

### Task 7 — Anti-pattern checklist

1. Confirm you will never:
   - Delete birthright because it “also shows as detected”
   - Treat detection as proof of manager approval
   - Ignore AWS_ADMIN simply because no CloudAdmin role is assigned

**Expected result:** Checklist initialed.

### Task 8 — Dual-control spot-check

1. Open `priya.wire` and `marcus.approve`.
2. Confirm initiator assignment only on Priya (baseline).
3. Note any detection that might confuse a certifier who sees both as “Treasury.”

**Expected result:** Written note: assignment enforces dual control; detection alone does not.

---

## Acceptance criteria

- [ ] Assigned vs detected identified on at least two cubes
- [ ] Outlier case file for AWS_ADMIN without CloudAdmin assignment
- [ ] Manager-ready two-sentence narrative written
- [ ] Refresh assign/detect options documented
- [ ] Certification target policy drafted

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No detected roles ever | Detection profiles not defined / option off | Enable detect; ensure role profiles match ents |
| Assigned empty after refresh | Assignment option off / rule fail | Enable assign; fix rules |
| UI shows single Roles list | Version/UI simplification | Use Debug Identity XML to see roleAssignment vs detected |
| Manager confusion in UAT | Training gap | Use Task 4 sentences in cert kickoff deck |

---

## Training binder evidence

- Screenshots: Amelia assigned birthright; developer assigned job role
- Outlier case file (AWS_ADMIN without privileged role assignment)
- Two-sentence manager narrative card
- Refresh task option notes
- Certify-roles-vs-ents policy paragraph

**Control owner:** IAM Engineering (config) + Risk (certify standard)  
**Examiner question:** “How do you distinguish approved access from merely observed access?”

---

## Knowledge check

1. Detection vs assignment—which is normative?
2. Why can AWS_ADMIN appear without an assigned CloudAdmin role?
3. What should managers certify for birthright?
4. What refresh mistake blocks birthright enforcement?
5. Is detection alone proof of approval?
6. How should dual-control wire access be certified—by detection of “Treasury-like” access?

### Answers

1. Assignment is normative (should have); detection is analytical (resembles / already has).
2. Privileged role is request-only or not yet granted; entitlement may be standing residual or directly assigned—still a risk to review.
3. The assigned birthright role (and/or underlying ELDAP if certifying ents)—not “detected noise” as the sole signal.
4. Running refresh without role assignment options enabled.
5. No—detection is not approval.
6. No—certify assigned WireInitiator/WireApprover roles and/or WIRE_* entitlements; do not trust a vague detected “Treasury” profile.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “role detection” and “assigned roles” for refresh options and cube semantics.
- [SailPoint Community](https://community.sailpoint.com/) — search “detected vs assigned” for certifier confusion patterns and training tips.
- [NIST SP 800-53 AC-2](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — account management; assigned access as the authorized inventory.
- [NIST SP 800-53 AC-6](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — least privilege reviews should act on authorized grants, not mere observation.
- [FFIEC IT Handbook — Information Security](https://ithandbook.ffiec.gov/) — access review expectations that require clear “approved vs observed” language.

---

## Stretch lab

- Propose hybrid cert: role-level for retail birthright populations; entitlement-level for Treasury and Cloud.
- Build population `MNB-Pop-Priv-Ent-Without-Role` for AWS_ADMIN holders lacking CloudAdmin assignment.
- Export one Identity XML snippet (redact) showing role assignment structures for training.

---

## Summary

- Assignment = policy decision; detection = analytical match—never conflate them.
- Outliers with critical entitlements but no privileged assigned role are remediation fuel.
- Certify standards must be explicit before campaign design.

---

**Previous:** [Lesson 26 — IT Role Packaging & Least Privilege](26-it-role-packaging.md)  
**Next:** [Lesson 28 — Privileged Access Role Design](28-privileged-access-roles.md)
