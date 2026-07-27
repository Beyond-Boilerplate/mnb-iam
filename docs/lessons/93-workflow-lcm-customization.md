# Lesson 93 — LCM Workflow Customization

**Level:** Advanced  
**Track:** Rules, Workflows, Forms  
**Time:** 75–90 min  
**Prereq:** Lesson 92 — Identity Attribute Rules  

**Lab data:**
- Repo: `lab-data/connectors/rules/README.md` (Workflow rule type)
- Runtime: `~/iiq-lab-data/connectors/rules/`
- Prior LCM lessons: joiner / mover / leaver / access request

---

## Learning objectives

You will be able to:

- Locate Meridian-relevant **LCM workflows** (Joiner, Mover, Leaver, Access Request)
- Apply safe customization patterns: variables, approval steps, email args — not reckless step deletion
- Preserve the **OOTB upgrade path** by cloning to `MNB-WF-*` before editing
- Record versioning discipline (`changeId`, owner, date) analogous to Temporal/`Workflow.getVersion` thinking
- Wire a lab clone, test an IdentityRequest end-to-end, and document rollback
- Explain to an examiner why editing OOTB in place fails the next IIQ upgrade

---

## Why this matters

**Business.** LCM is how Meridian joins `nina.joiner`, moves `sofia.torres` between cost centers, and removes `samir.hassan`. A broken Access Request workflow stalls every Wire entitlement for `priya.wire`'s team — visible as "IAM is down" even when the engine is healthy.

**Control / audit.** Unversioned workflow edits cause the classic bank failure mode: *works in lab, fails after upgrade* because someone edited OOTB in place and the next patch overwrote it — or worse, left a frankenstein merge. Examiners and platform teams require change records, backups, named clones, and rollback copies. This lesson builds that discipline on joiner/mover/leaver and access-request approval paths.

---

## Concepts

### What LCM workflows are

**Lifecycle Manager (LCM) workflows** are IdentityIQ process definitions that orchestrate joiner, mover, leaver, and access-request journeys: approvals, provisioning subprocesses, notifications, and audit steps. They are not "just XML" — they are production control logic with human SLAs attached.

| Journey | Typical Meridian trigger | Approval flavor |
| --- | --- | --- |
| **Joiner** | HR new hire / `nina.joiner` | Manager + birthright roles; limited manual |
| **Mover** | Department / manager change (`sofia.torres`) | Losing + gaining manager; entitlement delta |
| **Leaver** | HR termination (`samir.hassan`) | Rapid disable; privileged dual-control |
| **Access Request** | Self/manager request (`kai.nguyen`, `amelia.brooks`) | Manager + owner; dual control for Wire/PAM |

### Don't break the OOTB upgrade path

SailPoint ships **out-of-the-box (OOTB)** workflows. Patches and version upgrades replace or merge those objects. If you edit OOTB in place:

1. Your custom approval step disappears on upgrade — or blocks the upgrade.
2. You cannot tell "SailPoint default" from "Meridian change" in an audit.
3. Rollback means restoring from backup under incident pressure.

Meridian rule: **never edit OOTB in place without a backup; always clone to `MNB-WF-*` first; point configuration at the clone.**

### Versioning discipline (even when the API differs)

Temporal developers know `Workflow.getVersion(changeId, …)` — the idea is the same here even if IIQ's mechanism is documentation + clone naming, not that API:

- Record `changeId` = `mnb-lcm-v1-<date>`
- One controlled change per lab (and per CAB ticket in prod)
- Prefer configuration (approval schemes, QuickLink args, email templates) before custom steps
- Heavy logic → Workflow rules or Java services — not 500-line BeanShell inside a step

```
Trigger (HR change / Access Request)
        │
        ▼
 LCM Workflow (MNB-WF-* clone, not raw OOTB)
        │
        ├── Approval schemes (manager, dual control)
        ├── Provisioning subprocess
        ├── Email / audit steps
        └── Workflow rules (light, logged, no PII)
```

### Wrong way vs Meridian way

| Wrong way | Why it fails | Meridian way |
| --- | --- | --- |
| Edit OOTB Access Request in place | Upgrade wipe / unauditables | Clone `MNB-WF-AccessRequest-Lab` |
| Delete "unused" steps to "simplify" | Null errors; missing audit | Add/adjust; never delete required audit/provision hooks |
| Five customizations in one CAB | Untestable blast radius | One changeId per change |
| Dual control only in opaque BeanShell | No scheme visibility | Approval scheme reference + workgroups (Lesson 96) |

---

## How it works

```
Requester / HR event
        │
        ▼
 Lifecycle Manager config selects workflow name
        │
        ├── OOTB (untouched backup)
        └── MNB-WF-AccessRequest-Lab (active in lab)
                │
                ▼
         Approvals → Provisioning plan → Before/After Prov (91)
                │
                ▼
         IdentityRequest + WorkflowCase evidence
```

| Practice | Meridian rule |
| --- | --- |
| Backup before edit | Export `OOTB-<name>-backup.xml` |
| Clone naming | `MNB-WF-AccessRequest-Lab`, `MNB-WF-Leaver-Lab`, … |
| Version changes | Document `changeId` + date + owner (`helen.ross`) |
| Prefer config | Approval schemes / QuickLink args before custom steps |
| Heavy logic | Workflow rule or Java — not mega BeanShell in step |
| Rollback | Repoint config to OOTB; keep clone for forensics |

**Lab-without-live-target:** Clone + document + attach to a lab lifecycle event or Access Request; prove with Delimited provisioning apps (`MNB-IT-Access`, Wire Portal medium risk).

---

## Real-world setup (upgrade-safe customization)

### Step 1 — Inventory and owners

1. List LCM workflows in lower env; assign control owner (`helen.ross` / `MNB-WG-IAM-Ops`).
2. Map joiner/mover/leaver/access-request to workflow names for your IIQ version.

### Step 2 — Clone and CAB

1. Export OOTB XML to the SSD project as reference.
2. Create `MNB-WF-*` clone; CAB ticket describes the single behavioral change (e.g. dual approval for privileged Wire).
3. Record `changeId`.

### Step 3 — Wire configuration, not folklore

1. Point Lifecycle Manager / QuickLink / system config at the clone **in the target environment only**.
2. Document rollback: repoint to OOTB name within 15 minutes.

### Step 4 — Test personas before prod

1. Joiner smoke: `nina.joiner` birthright path.
2. Access request: `kai.nguyen` / `amelia.brooks` medium entitlement.
3. Privileged path: dual control involving `marcus.approve` / Security workgroup — without break-glass.

### Step 5 — Upgrade rehearsal

1. On each IIQ patch in lower env, diff OOTB backups; re-apply Meridian intent on clones if SailPoint changed defaults.
2. Never discover upgrade breaks on production Monday.

---

## Before you start

- [ ] IIQ up; Debug → Workflows
- [ ] Ability to create IdentityRequest (Access Request or LCM event)
- [ ] Binder: `workflows/lcm/`
- [ ] Prior joiner/mover/leaver / access-request concepts familiar (Lessons 29/31/36 if available)
- [ ] Lesson 91 rules may already be on `MNB-ActiveDirectory` — fine; do not break them

---

## Lab procedure

### Task 1 — Inventory LCM workflows

You cannot protect what you cannot name. Inventory first.

1. Debug → Workflows; filter LCM / Lifecycle / Access Request / Joiner / Leaver names present in your version.
2. List **at least five** workflow names into binder with one-line purpose each (include joiner, mover/leaver if present, access request, and two related helpers).
3. Identify which definition handles **Access Request approvals** for your lab.
4. Note the OOTB name you will back up in Task 2.

**Expected result:** Inventory table of ≥5 workflows with the Access Request target marked.

**If it fails:** Use Monitor → Processes / Business Processes UI to list definitions.

### Task 2 — Clone before edit

This is the upgrade-path insurance policy.

1. Select the Access Request (or Leaver) workflow you will customize.
2. Export XML to binder `OOTB-<name>-backup.xml`.
3. Create a copy named `MNB-WF-AccessRequest-Lab` (or `MNB-WF-Leaver-Lab` if you chose leaver).
4. Save the copy in IIQ. Leave the OOTB object untouched.

**Expected result:** Backup file + Meridian-named clone exists; OOTB unchanged.

**If it fails:** Duplicate via UI "Save As"; keep original untouched; still export what you can.

### Task 3 — Safe customization (exactly one)

On the **clone only**, implement **exactly one** change:

**Option A:** Add/adjust a description variable or step description noting "Meridian lab dual control."  
**Option B:** Ensure privileged entitlements route to dual approval (Tech Director + Security) — via approval scheme reference if possible (`marcus.approve` / Security workgroup conceptually).  
**Option C:** Add a Workflow rule step stub that logs request id only (no PII) — type Workflow from Lesson 89 catalog.

1. Implement exactly one option.
2. Record `changeId`: `mnb-lcm-v1-<date>` and owner `helen.ross`.
3. Save workflow.

**Expected result:** Single documented customization on clone; `changeId` recorded.

**If it fails:** Description-only change (Option A) still counts — upgrade discipline matters more than cleverness.

### Task 4 — Wire clone into lab path

1. Locate configuration that selects which workflow runs for Access Requests / LCM (Lifecycle Manager config, QuickLink, or System config — version-specific).
2. Point **lab** configuration to `MNB-WF-AccessRequest-Lab` **or** document manual test launch from Debug if the global switch is locked.
3. Do not point production-like defaults without noting rollback.
4. Screenshot wiring if changed.

**Expected result:** Written wiring notes + config screenshot if changed.

**If it fails:** Launch workflow from Debug with a test identity for evidence; still write how prod *would* wire it.

### Task 5 — Test IdentityRequest (joiner/mover/leaver awareness)

Prove the path with a real request — and know which journey you did *not* break.

1. As a manager-capable user (or `spadmin` lab), request a **medium** entitlement for `kai.nguyen` or `amelia.brooks` (not break-glass, not Wire highest tier unless dual control is ready).
2. Approve per scheme.
3. Confirm provisioning to file/lab app succeeds.
4. Capture IdentityRequest id, workflow case id, Task Results.
5. Write one sentence: how joiner/mover/leaver would use the same clone-vs-OOTB discipline (even if you tested Access Request only).

**Expected result:** End-to-end lab request evidence through customized workflow + journey note.

**If it fails:** Use simplest requestable entitlement on `MNB-IT-Access` or Wire Portal medium risk.

### Task 6 — Rollback plan

Write rollback that a night-shift engineer can execute:

1. Repoint config to OOTB workflow name.
2. Keep `MNB-WF-*` clone for forensics — do not delete under panic.
3. Re-import backup XML only if the clone is corrupted.
4. Re-test one IdentityRequest after rollback.

**Expected result:** Rollback card in binder.

### Task 7 — Examiner / upgrade drill

*"Show that Meridian can upgrade IIQ without losing Access Request dual control."*

Write the answer: OOTB backup retained; active logic on `MNB-WF-*`; `changeId` history; post-upgrade checklist re-diff OOTB and re-validate clone.

**Expected result:** Written upgrade proof steps.

---

## Acceptance criteria

- [ ] Workflow inventory complete (≥5, Access Request marked)
- [ ] OOTB backup exported
- [ ] `MNB-WF-*` clone created and customized exactly once
- [ ] `changeId` documented with owner
- [ ] Test IdentityRequest evidenced
- [ ] Rollback card written
- [ ] Upgrade / examiner proof steps drafted

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Request uses old WF | Config not pointed / cache | Re-check LCM config; re-login; retry |
| Step null error | Deleted required step | Restore from backup; do not delete audit/provision hooks |
| Approval stuck | Scheme / workgroup mis-set | Fix approver workgroup (Lesson 96); check `marcus.approve` |
| Provision skip | No plan / app | Check requestable entitlement on lab app |
| Upgrade wipe fear | Edited OOTB in place | Always use `MNB-WF-*` clone; restore OOTB from backup if already damaged |
| BeanShell PII in logs | Workflow rule too chatty | Log request id only |

---

## Training binder evidence

- Inventory table (≥5 workflows)
- OOTB backup XML (or hash/path note)
- Clone screenshot + `changeId`
- Wiring notes
- IdentityRequest + workflow case evidence (`kai.nguyen` or `amelia.brooks`)
- Rollback card
- Upgrade / examiner proof steps

---

## Knowledge check

1. What do you do before editing an OOTB LCM workflow?
2. Name a valid Meridian clone name pattern.
3. Why record a `changeId`?
4. How many customizations should you make in this lab?
5. What is the rollback first step?
6. Why does editing OOTB in place fail the upgrade path?

### Answers

1. Export/backup and clone to `MNB-WF-*`.
2. e.g. `MNB-WF-AccessRequest-Lab` or `MNB-WF-Leaver-Lab`.
3. Versioning/audit trail for workflow evolution and upgrades — Meridian's analog to versioned workflow changes.
4. Exactly one safe change.
5. Repoint configuration to the OOTB workflow name.
6. Patches may overwrite OOTB or create unmergeable drift; clones keep Meridian logic separable and re-applicable.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search "Lifecycle Manager workflows" and "Access Request workflow" for version-specific step models.
- [SailPoint Community / Compass](https://community.sailpoint.com/) — search "customize LCM workflow" and "upgrade workflow best practices."
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — real upgrade war stories when OOTB was edited in place.
- [Temporal Workflow versioning (conceptual parallel)](https://docs.temporal.io/workflows#workflow-versioning) — optional read for `getVersion` mindset; IIQ uses clone+changeId discipline instead of that API.
- [NIST SP 800-53 CM-3 / CM-4](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — configuration change control and impact analysis for workflow edits.

---

## Stretch lab

Add a Meridian email template argument for leaver workflow notifying `amelia.brooks` (or HR ops) on privileged account disable — document only if email lesson objects exist. Separately, draft a mover approval sketch for `sofia.torres` (losing + gaining manager) as a future `MNB-WF-Mover-Lab` clone — design only.

---

## Summary

- Customize LCM via named `MNB-WF-*` clones, one controlled `changeId` change, and rollback plans — covering joiner/mover/leaver and access-request approvals.
- Protect the OOTB upgrade path: never edit SailPoint defaults in place as your live control logic.
- Prove the path with a real lab IdentityRequest and examiner-ready backup evidence.

---

**Previous:** [Lesson 92 — Identity Attribute Rules](92-identity-attribute-rules.md)  
**Next:** [Lesson 94 — Forms and Field Validation](94-forms-and-field-validation.md)
