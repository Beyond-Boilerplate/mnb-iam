---
title: "Lesson 22 — Identity Attribute Sync Hygiene"
stem: 22-attribute-sync-hygiene
voice: en-US-BrianNeural
rate: "-12%"
pitch: "+0Hz"
source: auto-draft
---

## cold-open

Hey — welcome back to Meridian National Bank’s Identity and Access Academy.

This is the listen-along for Lesson 22: Identity Attribute Sync Hygiene.

This is a theory companion. Listen for the ideas and the control story, then use the written lesson for any binder sketches or design tasks.

Grab a notebook.

By the end of this lesson, you will be able to: Build a Meridian source-of-truth table for email, status, department, job, and manager; Prove HR wins for identity attributes when an IT extract disagrees; Confirm MNB-IT-Access (and similar inventory apps) are not authoritative for identity lifecycle fields; Detect and document attribute flip-flop risk across aggregation order; Define exception attributes that may legitimately originate on a target system.

## why-this-matters

Business. Conflicting attribute sources create flip-flops: Monday HR says Teller for amelia.brooks; Tuesday an IT title overwrites the cube to “Interim CIO”; Wednesday roles misfire and managers lose trust. Unstable identity truth breaks every control that keys off department, job, status, or manager.

Control / audit. Authoritative source designation is a control. Meridian’s stance: HR owns identity truth for email, employment status, department, job, manager, and worker type. IT apps own account/entitlement facts only. Examiners ask which system is system-of-record — your source-of-truth table is the answer, not tribal knowledge.

---

## concepts-authoritative-promotion-vs-acco

Authoritative promotion vs account facts.

During aggregation and refresh, IdentityIQ can promote account attributes onto the identity. Authoritative applications and attribute promotion / identity mapping rules decide winners. MNB-HR is authoritative for the person. MNB-IT-Access and directory apps may carry copies of email or free-text titles — those belong on the Link (account), not as identity lifecycle winners.

## concepts-flip-flopping-defined

Flip-flopping defined.

Flip-flopping is two sources alternately overwriting the same identity attribute depending on which aggregation ran last. Classic lab failure: map IT jobTitle onto identity jobTitle, run IT aggregate after HR, and watch Amelia’s title oscillate. Roles and certifications then key off noise.

Real-life Meridian example. Amelia’s HR row is Teller / TEL01. An inflated IT inventory title must never become her cube jobTitle — birthright roles and mover logic read HR codes, not helpdesk free text. Samir’s identity status comes from HR termination; any remaining SAP accountStatus is per-application state (Lesson 20), not a second employment status.

## concepts-what-it-may-carry-without-ownin

What IT may carry without owning.

Attribute: email; Authoritative source: MNB-HR; IT apps may carry?: Yes (copy only); Identity owner: HR. Attribute: status (active/inactive); Authoritative source: MNB-HR; IT apps may carry?: Account status only; Identity owner: HR. Attribute: departmentName / jobCode; Authoritative source: MNB-HR; IT apps may carry?: Display title noise; Identity owner: HR. Attribute: managersAssociateID / manager; Authoritative source: MNB-HR; IT apps may carry?: No; Identity owner: HR. Attribute: employeeType / exceptions (LOA); Authoritative source: MNB-HR; IT apps may carry?: No; Identity owner: HR. Attribute: entitlements (WIRE_INIT, …); Authoritative source: Target apps; IT apps may carry?: Yes; Identity owner: App owner. Attribute: accountStatus on link; Authoritative source: Target app; IT apps may carry?: Yes; Identity owner: App. Attribute: lastLogin / tech aliases; Authoritative source: Target app; IT apps may carry?: Yes (account-level); Identity owner: App.

## concepts-aggregation-order-as-a-control

Aggregation order as a control.

Preferred Meridian nightly order: HR first, then target apps, then identity refresh (Lesson 16). HR-last aggregation of a mis-mapped IT source is especially dangerous — the last writer wins and the cube lies until someone notices role failures.

## concepts-wrong-way-vs-bank-ready-way

Wrong way vs bank-ready way.

Approach: “Directory is freshest — promote AD email/title to identity”; What examiners see: Flip-flops; contractor mail and free-text titles become governance truth. Approach: Dual authoritative apps for the same attributes; What examiners see: Unstable cubes; unexplained role churn. Approach: Fix cube fields by hand after each aggregate; What examiners see: Dual sources; next pipeline undoes the edit. Approach: HR authoritative; IT/AD non-authoritative; disagreement tests; What examiners see: Stable SoR table; defects logged when mappings fight.

Contractor note: raj.external’s vendor mailbox can be correct on HR. Hygiene is not “force everyone to @meridiannb.com on the cube” — it is “only HR may set identity email,” including known contractor exceptions.

---

## how-it-works

Stage: HR aggregation; Correct behavior: Updates identity lifecycle attrs; Defect signal: Missing/stale HR → wrong truth. Stage: IT/AD aggregation; Correct behavior: Updates Links / entitlements only; Defect signal: Identity title/dept/status changes from IT. Stage: Identity Refresh; Correct behavior: Recomputes derived cube state; Defect signal: Flip after refresh if mappings fight. Stage: Disagreement test; Correct behavior: HR title survives absurd IT title; Defect signal: Cube shows “Interim CIO” → Sev-2 mapping defect.

Mapping defects that can overwrite status or email are Sev-2 with a 2 business day fix SLA (binder control owner: IAM Engineering). Title-only noise is still a defect — it poisons role assignment — but status/email overwrites can revive terminated cubes or break correlation secondaries.

---

## close

HR owns email, status, dept, job, manager, worker type; IT apps must not clobber them.
Non-authoritative inventory apps are correlation aids, not identity systems of record.
Disagreement tests and aggregation order prevent silent flip-flops before roles and JML depend on clean attributes.

---

Previous: Lesson 21 — Manager Hierarchy & Reassignment 
Next: Lesson 23 — Role Model Introduction

When you’re ready, open the written lesson for binder work, then move on in the Academy. That’s your briefing for Lesson 22.
