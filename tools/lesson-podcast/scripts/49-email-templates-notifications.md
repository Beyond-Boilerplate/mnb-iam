---
title: "Lesson 49 — Email Templates & Notifications"
stem: 49-email-templates-notifications
voice: en-US-BrianNeural
rate: "-12%"
pitch: "+0Hz"
source: auto-draft
---

## cold-open

Hey — welcome back to Meridian National Bank’s Identity and Access Academy.

This is the listen-along for Lesson 49: Email Templates & Notifications.

This is a theory companion. Listen for the ideas and the control story, then use the written lesson for any binder sketches or design tasks.

Grab a notebook.

By the end of this lesson, you will be able to: Compare Meridian’s sample certification mail to IdentityIQ EmailTemplate objects; Identify the certification (and related) templates used for manager campaigns; Rewrite subject/body for actionable clarity: campaign, scope, due date, CTA; Document recipient logic (manager vs app owner vs requester); List noise-control rules so notifications drive SLAs instead of training users to ignore mail.

## why-this-matters

Notifications start the human SLA clock. Vague emails get ignored; clear ones get certifications done on time. Examiners may ask how reviewers were notified and whether reminders existed.

Trusted From-addresses on @meridiannb.com matter in production. Lab SMTP may be off—you still align templates so go-live copy is ready.

---

## concepts-concepts

IdentityIQ stores mail content as EmailTemplate objects (Debug / gear menu → Business Processes / Email Templates, or equivalent). Common families:

Template family: Certification open / reminder; Typical recipient: Manager or app owner; Meridian use: Quarterly & micro-certs. Template family: Work item / approval; Typical recipient: Approver chain; Meridian use: LCM requests (Lessons 35–36). Template family: Policy violation; Typical recipient: Compliance / Risk / manager; Meridian use: SoD hits (Lesson 41). Template family: Lifecycle; Typical recipient: Manager / employee; Meridian use: Joiner/leaver notices.

Actionable cert mail checklist (from certification-sample.txt):

 

Noise rules: Do not email on every trivial attribute update; batch reminders; escalate overdue only to managers + their manager; never BCC the entire bank.

Subject line patterns that work

Event: Cert open; Subject pattern: Action required — {Campaign} ({Org}). Event: Cert reminder; Subject pattern: Reminder — {Campaign} due {Date}. Event: Cert overdue; Subject pattern: Overdue — {Campaign} — escalate. Event: SoD open; Subject pattern: Policy violation — {Policy} — {Identity}. Event: Break-glass; Subject pattern: Alert — PRIV_BREAK granted — {Identity}.

Avoid subjects like “IdentityIQ notification” or “You have a work item” with no campaign or due date.

---

## how-it-works

IIQ EmailTemplate objects render notifications for certifications, work items, policy violations, and lifecycle events. Templates must be actionable (campaign, due date, CTA path)—generic “you have a work item” mail trains managers to ignore governance.

Template family: Cert open / reminder; Must include: Campaign, scope, due date, Inbox CTA. Template family: SoD / policy; Must include: Policy name, identity, next action. Template family: Break-glass; Must include: Identity, entitlement, ticket, TTL.

Real-life Meridian example. rachel.evans receives “Action required — MNB-Mgr-Cert-Treasury — due Friday” with Inbox path—she can act. Subject “IdentityIQ notification” gets filtered and becomes a completion-rate finding.

## close

Meridian’s sample mail is the gold standard for cert notifications.
EmailTemplate objects must carry campaign, due date, and CTA—not vague prose.
Recipient and noise discipline protect the SLA.

---

Previous: Lesson 48 — Audit-Ready Reporting 
Next: Lesson 50 — Capstone Exam Readiness

When you’re ready, open the written lesson for binder work, then move on in the Academy. That’s your briefing for Lesson 49.
