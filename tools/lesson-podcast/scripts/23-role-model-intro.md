---
title: "Lesson 23 — Role Model Introduction"
stem: 23-role-model-intro
voice: en-US-BrianNeural
rate: "-12%"
pitch: "+0Hz"
source: auto-draft
---

## cold-open

Hey — welcome back to Meridian National Bank’s Identity and Access Academy.

This is the listen-along for Lesson 23: Role Model Introduction.

This is a theory companion. Listen for the ideas and the control story, then use the written lesson for any binder sketches or design tasks.

Grab a notebook.

By the end of this lesson, you will be able to: Distinguish IT roles vs business roles in IdentityIQ terms Meridian can defend to audit; Sketch a starter role catalog using MNB-Birthright- and MNB-Role- naming; Map department/job codes to candidate roles without exploding the catalog; Mark which roles are birthright, assignment-rule driven, or request-only; List stakeholders who must approve the catalog before go-live.

## why-this-matters

Business. Without roles, every access request is a snowflake entitlement pick—slow for joiners, opaque for certifiers. When amelia.brooks joined as a teller, her manager should have seen “baseline employee pack,” not fifteen raw group codes. Roles translate bank jobs into governed bundles managers understand: “Relationship Manager pack,” not CRM|ODS|ELDAP soup.

Control / audit. Role composition is a change-controlled artifact. When the OCC examiner asks "how is birthright bounded, and how is privileged access excluded?" your answer is the catalog sketch plus the anti-goals (no birthright CloudAdmin, no initiate+approve wire pack). Later lessons implement the bundles in IIQ; this lesson freezes the design control.

---

## concepts-bundles-speak-two-languages

Bundles speak two languages.

In IdentityIQ, roles are often Bundles. Two common modeling styles:

Style: IT role; Speaks to: Technical packaging; Contains: Entitlements / accounts; Meridian use: Building blocks (e.g. directory + ODS). Style: Business role; Speaks to: Job / function; Contains: IT roles and/or entitlements; Meridian use: What HR and managers recognize.

The naive alternative is to skip roles and certify every entitlement forever. That fails at a bank under exam: managers cannot attest technical codes they do not understand, and joiner SLAs collapse under ticket volume.

## concepts-starter-catalog-sketch-implemen

Starter catalog (sketch — implement in Lessons 24–28).

Role name: MNB-Birthright-Employee; Type: Birthright; Entitlements (intent): ELDAP; Assignment posture: Auto: active Employee. Role name: MNB-Role-Developer; Type: Job; Entitlements (intent): DWRP, ODS; Assignment posture: Auto: DEV01 / SRE01. Role name: MNB-Role-RelationshipManager; Type: Job; Entitlements (intent): CRM (+ optional ODS); Assignment posture: Auto: RM01 / LO01. Role name: MNB-Role-WireInitiator; Type: Job; Entitlements (intent): WIRE_INIT; Assignment posture: Auto: WIR01 only. Role name: MNB-Role-WireApprover; Type: Job; Entitlements (intent): WIRE_APPR; Assignment posture: Auto: WIR02 (separate forever). Role name: MNB-Role-CloudAdmin; Type: Privileged; Entitlements (intent): AWS_ADMIN; Assignment posture: Request-only. Role name: MNB-Role-BreakGlass; Type: Privileged; Entitlements (intent): PRIV_BREAK; Assignment posture: Request-only.

Anti-goals: Never birthright CloudAdmin, WireApprover, BreakGlass, or SAP_FI. Never merge WIRE_INIT and WIRE_APPR into one role—that destroys payment dual control.

## concepts-why-dual-control-shows-up-in-th

Why dual control shows up in the catalog, not later.

priya.wire (WIR01) initiates; marcus.approve (WIR02) approves. If the catalog treats “Treasury wire access” as one pack, SoD policy later is theater—the conflict is already baked into the role. Catalog design is the first SoD control.

---

## how-it-works

Roles sit between HR attributes and entitlements. Refresh evaluates assignment rules; LCM later lets humans request privileged packs. Detection (Lesson 27) is analytical—do not confuse it with assignment.

Layer: HR; Object: jobCode, employeeType, status; What it answers: Who is this person at Meridian?. Layer: Role (Bundle); Object: MNB-Birthright- / MNB-Role-; What it answers: What pack should they have?. Layer: Entitlement; Object: ELDAP, WIRE_INIT, AWS_ADMIN…; What it answers: What access does the pack grant?. Layer: Request path; Object: LCM catalog; What it answers: What can they ask for that rules do not auto-grant?.

One consequence: catalog size is a control. Fifteen thoughtful job packs beat two hundred entitlement-named “roles.” Rare access stays requestable, not auto-assigned.

---

## close

Roles convert entitlement soup into auditable business language.
Meridian v0 catalog centers birthright ELDAP, job packs for Dev/RM/Wire, and request-only privilege.
Naming, dual-control splits, and stakeholder approval are design controls—not paperwork afterthoughts.

---

Previous: Lesson 22 — Identity Attribute Sync Hygiene 
Next: Lesson 24 — Birthright Employee Role

When you’re ready, open the written lesson for binder work, then move on in the Academy. That’s your briefing for Lesson 23.
