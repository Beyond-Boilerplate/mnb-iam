---
title: "Lesson 38 — IdentityRequest Tracking & Auditing"
stem: 38-identity-request-tracking
voice: en-US-BrianNeural
rate: "-12%"
pitch: "+0Hz"
source: auto-draft
---

## cold-open

Hey — welcome back to Meridian National Bank’s Identity and Access Academy.

This is the listen-along for Lesson 38: IdentityRequest Tracking & Auditing.

This is a theory companion. Listen for the ideas and the control story, then use the written lesson for any binder sketches or design tasks.

Grab a notebook.

By the end of this lesson, you will be able to: Locate a completed or in-flight IdentityRequest by id, requester, or target identity; Trace approval decisions (who, when, approve/reject) from work item / request history; Determine provisioning status (executed, pending, failed, not applicable in file lab); Search audit events related to access requests when audit actions are enabled; Assemble an evidence pack suitable for Internal Audit / examiners.

## why-this-matters

Business. Disputes and fraud investigations need a single narrative: request → approval → provision → revoke. When someone asks whether CRM for a returning RM was approved—or whether PRIV_BREAK for MNB-INC-1042 was Security-approved and removed—you need artifacts, not memory.

Control / audit. “We think the manager approved” fails exams. IdentityRequest + work items + provisioning transactions + audit logs are the answer. Control owner: IAM Ops; Audit may sample monthly. Examiner question: Produce the evidence pack for request X end-to-end.

---

## concepts-evidence-spine

Evidence spine.

## concepts-pack-contents-meridian-minimum

Pack contents (Meridian minimum).

Artifact: IdentityRequest summary; Proves: What was asked for whom. Artifact: Approval history; Proves: Who decided, timestamps. Artifact: Reject/approve comments; Proves: Intent / ticket linkage. Artifact: Provisioning status; Proves: Whether access changed. Artifact: Identity entitlements before/after; Proves: Outcome on cube. Artifact: Audit search export (optional); Proves: Independent log trail.

## concepts-three-stories-this-pack-should-

Three stories this pack should cover.

Story: Low-risk CRM approve; Source lesson: 35–36; What must appear: Manager approve + advanced state. Story: Reject path; Source lesson: 36; What must appear: Reject comment; no provision. Story: Break-glass; Source lesson: 37; What must appear: MNB-INC-####, Security approve, revoke evidence.

## concepts-the-wrong-way

The wrong way.

Screenshots of the catalog alone, or “approver said OK in Slack.” Examiners want the IdentityRequest object lineage. Slack is not a control.

---

## how-it-works

Every LCM ask creates (or updates) an IdentityRequest. Approvals attach as work-item history; provisioning attaches as plans/transactions; AuditConfig may emit parallel events.

Status class: Finished / committed; Meaning: Change applied; Lab honesty: Ideal. Status class: Pending; Meaning: Waiting connector / manual; Lab honesty: Common in file lab. Status class: Failed; Meaning: Error—needs Lesson 47; Lab honesty: Track owner. Status class: None / N/A; Meaning: Rejected or stub lab; Lab honesty: Still valid evidence.

IIQ terms: IdentityRequest is the LCM request object. Provisioning plan is the technical change set. AuditConfig controls which actions are logged—if off, turn on relevant actions in lab thoughtfully.

---

## close

You traced IdentityRequests from submission through approvals and provisioning status.
You attempted audit-log corroboration and documented gaps honestly.
You assembled a reusable examiner-ready evidence pack.

---

Previous: Lesson 37 — Emergency / Break-Glass Access 
Next: Lesson 39 — SoD Fundamentals for Banking

When you’re ready, open the written lesson for binder work, then move on in the Academy. That’s your briefing for Lesson 38.
