---
title: "Lesson 29b — Lifecycle Events & Rapid Setup Joiner (Optional)"
stem: 29b-lifecycle-events-rapid-setup
voice: en-US-BrianNeural
rate: "-12%"
pitch: "+0Hz"
source: auto-draft
---

## cold-open

Hey — welcome back to Meridian National Bank’s Identity and Access Academy.

This is the listen-along for Lesson 29 B: Lifecycle Events & Rapid Setup Joiner (Optional).

This is a theory companion. Listen for the ideas and the control story, then use the written lesson for any binder sketches or design tasks.

Grab a notebook.

By the end of this lesson, you will be able to: Explain how a Lifecycle Event differs from a manual HR file insert; Keep Lesson 29’s file-delta path as the primary Core Path control story; Sketch (or configure, if available) a Joiner lifecycle event that creates a verification work item; Document license / import prerequisites honestly (init-lcm.xml, Rapid Setup); Decide when Meridian should automate joiner vs keep operator-driven refresh + birthright.

## why-this-matters

Business. Many banks eventually wire Joiner/Mover/Leaver events so HR account creation launches a workflow (welcome email, ticket, manager attestation). Juniors meet that vocabulary on day one even when the lab still teaches file inserts.

Control / audit. Examiners accept either model if the SLA and evidence are real: HR active → identity → birthright within policy time. Pretending Rapid Setup exists when it was never imported fails the interview. This lesson keeps file-insert primary and LCM as an optional accelerator.

---

## concepts-two-joiner-implementations-one-

Two joiner implementations, one control.

Approach: File delta + Aggregate + Refresh; Trigger: New HR row (apply-joiner.sh); What you prove: Cube + birthright; Core Path status: Primary (Lesson 29). Approach: Lifecycle Event / Rapid Setup; Trigger: Event rule on HR account create / attribute change; What you prove: Work item + workflow trail; Core Path status: Optional (this lesson).

## concepts-lifecycle-event-plain-english

Lifecycle Event (plain English).

A Lifecycle Event watches for a condition (new authoritative account, attribute change) and starts a workflow. Rapid Setup is SailPoint’s packaged UI for common JML events—useful when licensed and imported; not magic without init-lcm.xml / LCM artifacts.

## concepts-wrong-way

Wrong way.

Skip HR entirely and let a Joiner workflow create identities from AD. That inverts Meridian’s authoritative source rule (Lesson 04/62).

 

---

## how-it-works

Object: Application MNB-HR; Role: Authoritative; create-identities ON. Object: Lifecycle Event; Role: Optional trigger. Object: Workflow; Role: Optional orchestration. Object: Birthright Bundle; Role: Still the access package—event does not replace it.

---

## close

File-delta joiner stays the Core Path backbone. 
Lifecycle Events are optional orchestration, not a substitute for HR authority. 
Design LoA and Leaver as different events.

Previous: Lesson 29 — Joiner Lifecycle 
Next: Lesson 30 — Mover / Transfer Events

When you’re ready, open the written lesson for binder work, then move on in the Academy. That’s your briefing for Lesson 29 B.
