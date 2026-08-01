# Lesson 29b — Lifecycle Events & Rapid Setup Joiner (Optional)

**Level:** Intermediate  
**Track:** Lifecycle  
**Time:** 45–60 minutes  
**Prereq:** Lesson 29 (file-delta joiner for `nina.joiner`); birthright roles (24)  
**Lab data:** Scenario runners; optional `init-lcm.xml` / Rapid Setup if licensed in your lab  
**Path:** Core (01–50) — optional depth

---

## Learning objectives

You will be able to:

- Explain how a **Lifecycle Event** differs from a manual HR file insert
- Keep Lesson 29’s file-delta path as the **primary Core Path control story**
- Sketch (or configure, if available) a Joiner lifecycle event that creates a verification work item
- Document license / import prerequisites honestly (`init-lcm.xml`, Rapid Setup)
- Decide when Meridian should automate joiner vs keep operator-driven refresh + birthright

---

## Why this matters

**Business.** Many banks eventually wire Joiner/Mover/Leaver events so HR account creation launches a workflow (welcome email, ticket, manager attestation). Juniors meet that vocabulary on day one even when the lab still teaches file inserts.

**Control / audit.** Examiners accept either model if the SLA and evidence are real: HR active → identity → birthright within policy time. Pretending Rapid Setup exists when it was never imported fails the interview. This lesson keeps file-insert primary and LCM as an optional accelerator.

---

## Concepts

### Two joiner implementations, one control

| Approach | Trigger | What you prove | Core Path status |
| --- | --- | --- | --- |
| File delta + Aggregate + Refresh | New HR row (`apply-joiner.sh`) | Cube + birthright | **Primary (Lesson 29)** |
| Lifecycle Event / Rapid Setup | Event rule on HR account create / attribute change | Work item + workflow trail | Optional (this lesson) |

### Lifecycle Event (plain English)

A **Lifecycle Event** watches for a condition (new authoritative account, attribute change) and starts a **workflow**. Rapid Setup is SailPoint’s packaged UI for common JML events—useful when licensed and imported; not magic without `init-lcm.xml` / LCM artifacts.

### Wrong way

Skip HR entirely and let a Joiner workflow create identities from AD. That inverts Meridian’s authoritative source rule (Lesson 04/62).

```
Primary (always):
  apply-joiner.sh → Aggregate MNB-HR → Refresh → birthright

Optional (if LCM present):
  HR account create event → Joiner workflow → work item “Verify birthright for nina.joiner”
```

---

## How it works

| Object | Role |
| --- | --- |
| Application `MNB-HR` | Authoritative; create-identities ON |
| Lifecycle Event | Optional trigger |
| Workflow | Optional orchestration |
| Birthright Bundle | Still the access package—event does not replace it |

---

## Before you start

- [ ] Lesson 29 complete (`nina.joiner` exists or you can re-apply joiner)
- [ ] Know whether your lab imported LCM / Rapid Setup (ask instructor or check for Lifecycle Event UI)
- [ ] If LCM is absent, you will complete **paper design** tasks only—still a full credit path

---

## Lab procedure

### Task 1 — Re-affirm the primary joiner control

```bash
./tools/lab/scripts/scenarios/apply-joiner.sh
```

1. Aggregate MNB-HR → Refresh MNB Attributes / Roles as needed.  
2. Confirm `nina.joiner` + birthright intent; no Wire/AWS packs.  
3. Binder: “Primary control = file delta + birthright (Lesson 29).”

**Expected result:** Primary path re-verified before optional LCM work.

### Task 2 — Inventory LCM capability

1. Search IIQ UI for **Lifecycle Events** / Rapid Setup / Lifecycle Manager menus (labels vary by version).  
2. Record one of:  
   - **Present** — list any existing Joiner-related events  
   - **Absent** — “not imported; paper design only”  
3. Do not import random XML in a shared lab without approval.

**Expected result:** Honest capability statement in binder.

### Task 3 — Design the Meridian Joiner event (paper or UI)

Write the event card:

```text
Name: MNB-LE-Joiner-HR
Trigger: new account on MNB-HR (or identity create from authoritative app)
Actions:
  1) Ensure Refresh / birthright evaluation
  2) Create work item → manager (emily.bennett for Nina) “Verify day-one access”
  3) Notify IAM Ops channel (email template later — Lesson 49)
Non-actions:
  - Do not grant Wire/AWS
  - Do not create identities from AD/IT apps
```

If UI is available, create a **disabled** draft event matching the card (do not enable in shared lab unless instructed).

**Expected result:** Event card (+ optional disabled draft).

### Task 4 — Contrast mover/leaver events (design only)

One paragraph each:

- Mover: attribute change on `JobCode` / `managersAssociateID` → residual access review work item (Priya pattern).  
- Leaver: `inactive=true` → disable plan (Jordan pattern).  
- LoA: `exceptions=LOA` → freeze (Sofia)—**not** leaver workflow.

**Expected result:** Four-event sketch (Joiner/Mover/Leaver/LoA) with Sofia ≠ Jordan called out.

### Task 5 — Stretch scenarios via runners (optional)

```bash
./tools/lab/scripts/scenarios/apply-batch-hire.sh   # leo.batch, isla.batch
./tools/lab/scripts/scenarios/apply-rehire.sh       # samir.hassan returns
```

Document how batch hire and rehire stress Joiner events (duplicates, same `userId` reactivation).

---

## Acceptance criteria

- [ ] Primary Lesson 29 path re-verified with runner  
- [ ] LCM present/absent stated honestly  
- [ ] Joiner event card written (UI draft optional)  
- [ ] LoA ≠ Leaver called out in design  

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No Lifecycle UI | LCM not imported | Paper path is valid |
| Event fires twice | Overlapping triggers | Disable draft; document |
| Birthright missing | Refresh roles not run | Refresh MNB Roles |

---

## Training binder evidence

1. Nina birthright screenshot  
2. LCM capability note  
3. Event card  
4. Optional batch/rehire notes  

**Control owner:** IAM Governance  
**Examiner question:** “Does joiner require Rapid Setup, or is HR+birthright enough?”

---

## Knowledge check

1. What remains Meridian’s authoritative joiner trigger in Core Path?  
2. Why can LCM be optional in the academy?  
3. Should a Joiner event grant `WIRE_INIT`?  
4. How does LoA differ from Leaver in event design?

### Answers

1. New/updated HR row via authoritative aggregate (`apply-joiner.sh`).  
2. Labs may lack LCM imports; control story must still be teachable.  
3. No—birthright only; privileged access is request-driven.  
4. LoA freezes while employed; Leaver terminates and deprovisions.

---

## Further reading

- [SailPoint IdentityIQ docs](https://documentation.sailpoint.com/) — search “Lifecycle Events” and “Rapid Setup.”  
- Lesson 29 primary joiner; Lesson 93 for deeper workflow customization  

---

## Stretch lab

If LCM is present and you have a personal lab, enable a Joiner event in a sandbox and capture the work item for Nina—then disable the event again.

---

## Summary

- File-delta joiner stays the Core Path backbone.  
- Lifecycle Events are optional orchestration, not a substitute for HR authority.  
- Design LoA and Leaver as different events.

**Previous:** [Lesson 29 — Joiner Lifecycle](29-joiner-lifecycle.md)  
**Next:** [Lesson 30 — Mover / Transfer Events](30-mover-transfers.md)
