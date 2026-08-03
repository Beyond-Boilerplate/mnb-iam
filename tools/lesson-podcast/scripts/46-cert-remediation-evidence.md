---
title: "Lesson 46 — Certification Remediation & Evidence"
stem: 46-cert-remediation-evidence
voice: en-US-BrianNeural
rate: "-12%"
pitch: "+0Hz"
source: auto-draft
---

## cold-open

Hey — welcome back to Meridian National Bank’s Identity and Access Academy.

This is the listen-along for Lesson 46: Certification Remediation & Evidence.

This is a theory companion. Listen for the ideas and the control story, then use the written lesson for any binder sketches or design tasks.

Grab a notebook.

By the end of this lesson, you will be able to: Trace a certification revoke from decision → remediation work item / provisioning plan → account outcome; Measure campaign completion % and list late certifiers; Assemble an examiner-ready evidence binder checklist for Meridian certs; Sample five approve decisions for rubber-stamp signals; Propose a short manager coaching note based on QA findings.

## why-this-matters

Business. A certification marked “complete” with open revokes is incomplete. When Rachel revokes leftover AWS_ADMIN on a report, the control is not the click — it is the removal (or documented exception) that follows. Without that chain, Meridian’s quarterly review is theater.

Control / audit. Internal audit and banking examiners sample both decision quality and remediation closure. Rubber-stamping (approve-all, sub-minute completes) destroys the control’s credibility even when completion % looks green. Control owner: IAM Ops chasing remediations; Risk tracking overdue KPI; managers owning decision quality.

---

## concepts-remediation-vs-certification-co

Remediation vs certification complete.

Remediation is the downstream work created when a certifier revokes access: provisioning plan, access request, or manual ticket depending on connector and IIQ configuration.

Certification phase complete means managers finished deciding. Control complete means remediations closed (or exceptions documented). Examiners care about the second definition.

## concepts-evidence-binder-exam-pack

Evidence binder (exam pack).

Artifact: Campaign definition; Proves: Scope, period, cert type, owner. Artifact: Population / inclusion logic; Proves: Who was in scope and why. Artifact: Completion % + aging; Proves: Timeliness / late managers. Artifact: Sample decisions; Proves: Thoughtful review vs rubber-stamp. Artifact: Revoke → provisioning proof; Proves: Access actually removed. Artifact: Notification sample; Proves: Users were informed (SLA start).

## concepts-rubber-stamp-signals

Rubber-stamp signals.

Entire campaign approved in minutes
Zero revokes on high-risk apps (Wire/SAP/AWS in scope)
Identical comments on every line
Certifier never opened line-item detail
Approve rate ~100% with known toxic pairs in scope (e.g. both WIRE_INIT and WIRE_APPR on one person)

## concepts-meridian-example-a-revoke-that-

Meridian example — a revoke that “completed” but did nothing.

Rachel revokes residual AWS_ADMIN on a report. Campaign shows 100% complete. Three weeks later aggregation still shows the entitlement — the remediation IdentityRequest failed on a bad file path (Lesson 47). Completion % was green; the control was red. Your binder must include the revoke trace, not only the decision screenshot.

The wrong way: hand Audit a green completion dashboard and no revoke traces. That fails sampling.

---

## how-it-works

KPI: Completion %; Good signal: High by due date; Bad signal: High with zero comments. KPI: Remediations open; Good signal: Trend to zero by day +10; Bad signal: Still open after “complete”. KPI: Revoke rate on critical ents; Good signal: Non-zero when residuals exist; Bad signal: Always 0%. KPI: QA sample grade; Good signal: Pass / Coach; Bad signal: Fail (rubber-stamp).

Binder folder: MNB-Exam-Binder-Certs/ — this lesson’s cover sheet feeds Capstone evidence packs.

Include artifacts from Lessons 43–45: manager campaign seed, owner cert decisions, micro-cert Risk one-pager with FIND-IAM-45-001. The cover checklist (Task 3) is how those pieces become one examiner pack.

---

## close

Certifications end when remediations close, not when managers click Done.
Binders combine definition, sampling, and revoke proof.
Rubber-stamp detection protects the control’s credibility.
The two-minute stranger test is the pack quality gate before Capstone.

---

Previous: Lesson 45 — Targeted Campaigns 
Next: Lesson 47 — Provisioning Troubleshooting

When you’re ready, open the written lesson for binder work, then move on in the Academy. That’s your briefing for Lesson 46.
