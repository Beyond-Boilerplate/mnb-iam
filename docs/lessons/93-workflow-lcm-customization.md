# Lesson 93 — LCM Workflow Customization

**Level:** Advanced  
**Track:** Rules, Workflows, Forms  
**Time:** 75–90 min  
**Prereq:** Lesson 92 — Identity Attribute Rules  

**Lab data:**
- Repo: `lab-data/connectors/rules/README.md` (Workflow rule type)
- Runtime: `~/iiq-lab-data/connectors/rules/`
- Prior LCM lessons: joiner/mover/leaver / access request

---

## Learning objectives

You will be able to:

- Locate Meridian-relevant **LCM workflows** (Joiner, Leaver, Access Request, etc.)
- Apply safe customization patterns: variables, approval steps, email args—not reckless step deletion
- Use `Workflow.getVersion`-style **versioning discipline** when editing (document even if API differs)
- Export/import workflow XML with naming `MNB-WF-*` copies before editing OOTB
- Test a lab IdentityRequest through the customized path and capture evidence

---

## Why this matters

**Business.** LCM is how Meridian joins, moves, and removes staff. Broken workflows stall every hire.

**Control / audit.** Unversioned workflow edits cause “works in lab, fails after upgrade.” Examiners and platform teams require change records, backups, and rollback copies.

---

## Concepts

```
Trigger (HR change / request)
        │
        ▼
 LCM Workflow (steps: provision, approve, notify, audit)
        │
        ├── Approval schemes
        ├── Provisioning subprocess
        └── Email / audit steps
```

| Practice | Meridian rule |
| --- | --- |
| Never edit OOTB in place without backup | Clone to `MNB-WF-...` first |
| Version changes | Document changeId + date + owner |
| Prefer config | Approval schemes / QuickLink args before custom steps |
| Heavy logic | Workflow rules or Java services—not 500-line BeanShell in step |

**Lab-without-live-target:** Clone + document + attach to a lab lifecycle event or Access Request; prove with Delimited provisioning apps.

---

## Before you start

- [ ] IIQ up; Debug → Workflows
- [ ] Ability to create IdentityRequest (Access Request or LCM event)
- [ ] Binder: `workflows/lcm/`
- [ ] Read Lesson 29/31/36 concepts if available

---

## Lab procedure

### Task 1 — Inventory LCM workflows

1. Debug → Workflows; filter LCM / Lifecycle / Access Request names present in your version.
2. List 5 workflow names into binder with one-line purpose each.
3. Identify which one handles **Access Request approvals** for your lab.

**Expected result:** Inventory table of ≥5 workflows.

**If it fails:** Use Monitor → Processes / Business Processes UI to list definitions.

---

### Task 2 — Clone before edit

1. Select the Access Request (or Leaver) workflow you will customize.
2. Export XML to binder `OOTB-<name>-backup.xml`.
3. Create copy named `MNB-WF-AccessRequest-Lab` (or `MNB-WF-Leaver-Lab`).
4. Save copy in IIQ.

**Expected result:** Backup file + Meridian-named clone exists.

**If it fails:** Duplicate via UI “Save As”; keep original untouched.

---

### Task 3 — Safe customization

On the **clone only**, pick **one** change:

**Option A:** Add/adjust a description variable or step description noting “Meridian lab dual control.”  
**Option B:** Ensure privileged entitlements route to dual approval (Tech Director + Security)—via approval scheme reference if possible.  
**Option C:** Add a Workflow rule step stub that logs request id (no PII).

1. Implement exactly one option.
2. Record changeId: `mnb-lcm-v1-<date>`.
3. Save workflow.

**Expected result:** Single documented customization on clone; changeId recorded.

**If it fails:** Description-only change still counts.

---

### Task 4 — Wire clone into lab path

1. Locate configuration that selects which workflow runs for Access Requests / LCM (Lifecycle Manager config, QuickLink, or System config—version-specific).
2. Point **lab** configuration to `MNB-WF-AccessRequest-Lab` **or** document manual test launch from Debug if global switch is locked.
3. Do not point production-like defaults without noting rollback.

**Expected result:** Written wiring notes + config screenshot if changed.

**If it fails:** Launch workflow from Debug with test identity for evidence.

---

### Task 5 — Test IdentityRequest

1. As a manager-capable user (or spadmin lab), request a **medium** entitlement for `kai.nguyen` or `amelia.brooks` (not break-glass).
2. Approve per scheme.
3. Confirm provisioning to file/lab app succeeds.
4. Capture IdentityRequest id, workflow case id, Task Results.

**Expected result:** End-to-end lab request evidence through customized workflow.

**If it fails:** Use simplest requestable entitlement on `MNB-IT-Access` or Wire Portal medium risk.

---

### Task 6 — Rollback plan

Write rollback:

1. Repoint config to OOTB workflow name.
2. Keep `MNB-WF-*` clone for forensics.
3. Re-import backup XML only if clone corrupted.

**Expected result:** Rollback card in binder.

---

## Acceptance criteria

- [ ] Workflow inventory complete
- [ ] OOTB backup exported
- [ ] `MNB-WF-*` clone created and customized once
- [ ] changeId documented
- [ ] Test IdentityRequest evidenced
- [ ] Rollback card written

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Request uses old WF | Config not pointed / cache | Re-check LCM config; retry |
| Step null error | Deleted required step | Restore from backup |
| Approval stuck | Scheme mis-set | Fix approver workgroup |
| Provision skip | No plan / app | Check requestable entitlement |
| Upgrade wipe fear | Edited OOTB | Always use MNB clone |

---

## Training binder evidence

- Inventory table
- OOTB backup XML (or hash/path note)
- Clone screenshot + changeId
- Wiring notes
- IdentityRequest + workflow case evidence
- Rollback card

---

## Knowledge check

1. What do you do before editing an OOTB LCM workflow?
2. Name a valid Meridian clone name pattern.
3. Why record a changeId?
4. How many customizations should you make in this lab?
5. What is the rollback first step?

### Answers

1. Export/backup and clone to `MNB-WF-*`.  
2. e.g., `MNB-WF-AccessRequest-Lab` or `MNB-WF-Leaver-Lab`.  
3. Versioning/audit trail for workflow evolution and upgrades.  
4. Exactly one safe change.  
5. Repoint configuration to the OOTB workflow.

---

## Stretch lab

Add a Meridian email template argument for leaver workflow notifying `amelia.brooks` on privileged account disable—document only if email lesson objects exist.

---

## Summary

- Customize LCM via named clones, one controlled change, and rollback plans.
- Version discipline beats clever BeanShell sprawl.
- Prove the path with a real lab IdentityRequest.

---

**Previous:** [Lesson 92 — Identity Attribute Rules](92-identity-attribute-rules.md)  
**Next:** [Lesson 94 — Forms and Field Validation](94-forms-and-field-validation.md)
