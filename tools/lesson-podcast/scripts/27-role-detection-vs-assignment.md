---
title: "Lesson 27 — Role Detection vs Assignment"
stem: 27-role-detection-vs-assignment
voice: en-US-BrianNeural
rate: "-12%"
pitch: "+0Hz"
source: auto-draft
---

## cold-open

Hey — welcome back to Meridian National Bank’s Identity and Access Academy.

This is the listen-along for Lesson 27: Role Detection vs Assignment.

This is a theory companion. Listen for the ideas and the control story, then use the written lesson for any binder sketches or design tasks.

Grab a notebook.

By the end of this lesson, you will be able to: Identify detected vs assigned roles on an identity cube; Map those signals to Meridian’s two-tier model (business = assigned / normative; IT = often detected / analytical); Use detection to find outliers (entitlements present without approved assigned business roles); Confirm which identity refresh options affect assignment vs detection; Decide what managers should certify (roles, entitlements, or hybrid by risk).

## why-this-matters

Business. Detection explains what you already have; assignment decides what you should have. Confusing them breaks certifications: revoking a “detected only” signal is not the same as removing an assigned birthright. Managers who treat all role chips as identical will make wrong keep/revoke decisions—and tellers like amelia.brooks can lose baseline directory access because someone “cleaned up detected noise.”

Control / audit. Procedures must define whether campaigns certify assigned roles, detected roles, raw entitlements, or a mix. Meridian’s emerging standard: assigned business roles for baseline/job packs; entitlements (or privileged assigned business roles) for critical access. Examiners ask: “How do you distinguish approved access from merely observed access?”

---

## concepts-normative-vs-analytical-and-whe

Normative vs analytical (and where two-tier fits).

Concept: Assignment; Nature: Normative; Typical Meridian object: Business roles (MNB-Birthright-, MNB-Role-) via Match List / request; Question it answers: What should this identity have per policy?; Actionability: Provision / deprovision via role lifecycle. Concept: Detection; Nature: Analytical; Typical Meridian object: Often IT packs (MNB-IT-*) whose Entitlement profiles match accounts; Question it answers: What packs resemble entitlements already held?; Actionability: Insight / outlier hunting; not automatic approval.

Stock IIQ puts entitlement profiles on type it. Refresh detects those IT roles when account entitlements match. Refresh assigns business roles when Match Lists / requests say so. That is why Amelia may show Assigned MNB-Birthright-Employee and also Detected MNB-IT-ELDAP if ELDAP is on her account—both can be healthy.

## concepts-outlier-pattern-privilege-witho

Outlier pattern — privilege without approved role.

Identity has AWS_ADMIN entitlement on MNB-AWS-Cloud but no assigned MNB-Role-CloudAdmin. That is expected if CloudAdmin is request-only and not yet granted—or a standing privilege defect (e.g. raj.external residual, or a cloud engineer granted outside LCM). Detection may light up MNB-IT-CloudAdmin (or a cloud-admin-like profile) once Lesson 28 exists; detection is not approval.

## concepts-birthright-pattern

Birthright pattern.

amelia.brooks should show assigned MNB-Birthright-Employee. Detection may also light up MNB-IT-ELDAP if ELDAP matches the IT profile. Do not revoke birthright because an IT pack “also shows as detected.”

## concepts-dual-control-check

Dual-control check.

priya.wire should show assigned MNB-Role-WireInitiator; marcus.approve should not. Detection may show MNB-IT-WireInit only when WIRE_INIT is on the account. Trust assignment for normative dual-control decisions—and hunt residual entitlements when accounts still hold WIRE_* after a mover.

---

## how-it-works

Refresh can assign, detect, both, or neither—depending on task options. Certification policy must name which signal managers act on.

Refresh mistake: Assign OFF; Symptom: Birthright/job business packs never appear; Fix: Enable assign roles. Refresh mistake: Detect OFF; Symptom: No analytical IT matches; Fix: Enable detect if you use outlier hunting. Refresh mistake: Certify “all role chips”; Symptom: Managers revoke detection noise / IT packs; Fix: Train with Task 4 sentences.

---

## close

Assignment = policy decision on business roles; detection = analytical match—often on IT packs—never conflate them.
Outliers with critical entitlements but no privileged assigned business role are remediation fuel.
Certify standards must be explicit before campaign design.

---

Previous: Lesson 26 — IT Role Packaging & Least Privilege 
Next: Lesson 28 — Privileged Access Role Design

When you’re ready, open the written lesson for binder work, then move on in the Academy. That’s your briefing for Lesson 27.
