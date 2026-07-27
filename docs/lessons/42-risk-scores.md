# Lesson 42 — Risk Scores & Scoring Models

**Level:** Advanced  
**Track:** Policies  
**Time:** 45–60  
**Prereq:** Lesson 41 — Policy Violations & Mitigation  

**Lab data:** `reference/entitlement-dictionary.csv`, `apps/MNB-WirePortal.csv`, `apps/MNB-AWS-Cloud.csv`

---

## Learning objectives

You will be able to:

- Locate identity / entitlement risk configuration in IdentityIQ 8.5
- Raise relative weight for critical Meridian entitlements (wire, SAP_FI, AWS_ADMIN)
- Identify top-scoring identities after refresh and explain why they rose
- Document Meridian’s usage rule: scores **prioritize** certifications and monitoring; they do **not** auto-revoke
- List score limitations (lag, missing events, false confidence)

---

## Why this matters

Not every identity deserves equal scrutiny each quarter. Risk scores focus manager attention and campaign scoping where toxic access concentrates—wire initiators, cloud admins, dual-control edges.

Scores are a **prioritization signal**, not a control. Auto-revoking on score thresholds creates false positives, breaks business, and still fails SoD and leaver SLAs. Examiners ask what you *do* with high scores, not what the number is.

---

## Concepts

**Identity risk score** (composite) typically blends entitlement criticality, policy violations, unused access, and composite role risk—exact formula depends on IIQ risk configuration.

| Input | Meridian example | Effect on score |
| --- | --- | --- |
| Critical entitlement | `WIRE_INIT`, `WIRE_APPR`, `AWS_ADMIN`, `SAP_FI`, `PRIV_BREAK` | High weight |
| Medium entitlement | `CRM`, `ODS`, `ELDAP` | Moderate |
| Open SoD violation | `MNB-SOD-Finance-Cloud` | Spike |
| Dormant / orphan signals | Unused high-risk ents | Elevate for hunt |

```
Critical ents weighted
        │
        ▼
 Identity risk score
        │
        ├──► Cert campaign scoping / sort order
        ├──► Dashboard / weekly IAM huddle
        └──► NOT auto-revoke / NOT SoD replacement
```

**Personas who should rank high after weighting:** `jordan.reed` (SAP_FI + AWS_ADMIN), wire holders (`priya.wire`, `marcus.approve`), cloud contractors (`raj.external`).

**What scores must never do at Meridian**

- Auto-revoke or auto-disable on threshold cross
- Replace SoD policy evaluation
- Delay leaver / rapid offboard SLAs while “waiting for score refresh”
- Become a vanity metric (“average risk down 2%”) without linked actions

**What scores should do**

- Sort manager cert work items so high-risk lines appear first
- Feed the weekly IAM huddle top-10 list
- Trigger optional targeted campaigns when a population’s median score spikes

---

## Before you start

- [ ] IIQ up; login as `spadmin`
- [ ] Apps and entitlements from Lessons 11–14 aggregated
- [ ] Policy work from Lessons 39–41 optionally present (violations boost scores)
- [ ] `~/iiq-lab-data/reference/entitlement-dictionary.csv` available for risk labels
- [ ] Notebook ready for “usage decision” write-up

---

## Lab procedure

### Task 1 — Locate risk UI

1. Search admin menus for **Risk** / **Identity Risk** / **Scoring** (or equivalent under Compliance / System Setup).
2. Open identity risk configuration or scorecard settings.
3. Note whether scores are entitlement-driven, composite, or both.
4. Open an identity cube (e.g., `priya.wire`) and find the **Risk** tab or risk attributes.

**Expected result:** You can point to where scores are configured and where they appear on a cube.

**If it fails:** Use Debug → search Identity XML for risk-related attributes; still document the UI path you used.

### Task 2 — Weight critical entitlements

1. Open entitlement dictionary or application entitlement list for `MNB-WirePortal`, `MNB-SAP-Finance`, `MNB-AWS-Cloud`.
2. Set / confirm **critical** (or high risk level) for: `WIRE_INIT`, `WIRE_APPR`, `SAP_FI`, `AWS_ADMIN`, `PRIV_BREAK`.
3. Leave `CRM` / `ODS` at medium unless your lab already elevated them.
4. Save configuration.

**Expected result:** Critical Meridian ents show elevated risk level vs birthright directory access.

**If it fails:** If UI lacks editable risk levels, document intended weights in binder and apply via entitlement attributes in Debug only if comfortable.

### Task 3 — Refresh and rank top risk

1. Run **Refresh MNB Identities** (include risk recalculation if a separate option exists).
2. Use Advanced Analytics / Identity search sorted by risk score, or a risk report.
3. Record top 5 identities and one-line rationale each.
4. Confirm `jordan.reed`, wire personas, and/or `raj.external` appear near the top.

**Expected result:** Dated list `MNB-TopRisk-YYYY-MM-DD` with five names and rationales.

**If it fails:** Scores may need entitlement risk indexing—re-aggregate apps then refresh again.

### Task 4 — Meridian usage decision (write it)

Write exactly:

> Meridian uses risk scores to prioritize certification campaigns, monitoring queues, and manager coaching. Scores do not auto-revoke access. SoD policies, leavers, and certifications remain authoritative controls.

Add one limitation: scores lag HR events; rapid offboarding (Lesson 34) must not wait for score refresh.

**Expected result:** Signed usage paragraph in binder (your initials + date).

### Task 5 — Cert linkage sketch

1. Sketch how Lesson 43 manager cert will filter or sort by high-risk entitlements / high-score identities.
2. Note: targeted campaigns (Lesson 45) may use populations of high-score or high-risk holders instead of waiting for quarter-end.

**Expected result:** Two bullets linking scores → cert design.

### Task 6 — Anti-patterns walkthrough

1. Write one bad proposal you might hear (“auto-remove AWS if score > 800”) and the Meridian refusal reason.
2. Write one good proposal (“certify all identities in top risk decile within 10 days of quarter start”).
3. Confirm with a peer or self-check that Lesson 41 SoD still owns toxic-pair enforcement.

**Expected result:** Bad vs good proposal pair in binder.

---

## Acceptance criteria

- [ ] Risk configuration and cube risk view located
- [ ] Critical entitlements weighted (or documented if UI-limited)
- [ ] Top-5 risky identities captured with rationales
- [ ] Usage rule written: prioritize certs; no auto-revoke
- [ ] At least one score limitation documented (lag / events)

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| All scores zero | Risk engine not enabled / no refresh | Enable risk; re-run refresh |
| Birthright users score like wire | Weights not applied | Re-check entitlement risk levels |
| jordan not high | Missing AWS or SAP on cube | Aggregate apps; confirm correlation |
| Obsessing over score precision | Vanity tuning | Stop; tie scores to cert actions only |
| Score dropped after mitigate | Violation closed | Expected; still certify critical ents |

---

## Training binder evidence

- Screenshot: entitlement risk levels for wire/AWS/SAP
- Screenshot or export: top risk identities
- Usage decision paragraph (no auto-revoke)
- Limitation note for event-driven leavers

---

## Knowledge check

1. What do risk scores drive at Meridian?
2. Name three entitlements that should carry high weight.
3. Do scores replace SoD policies?
4. Who should rank high in this lab?
5. Name one limitation of score-based monitoring.

### Answers

1. Prioritization of certifications, queues, and attention—not auto-revoke.  
2. Any of: `WIRE_INIT`, `WIRE_APPR`, `AWS_ADMIN`, `SAP_FI`, `PRIV_BREAK`.  
3. No. SoD remains a separate preventive/detective control.  
4. `jordan.reed`, wire holders, cloud admins/contractors (e.g. `raj.external`).  
5. Scores lag; they miss real-time leaver/break-glass events without complementary controls.

---

## Stretch lab

Propose a weekly IAM huddle dashboard widget list: top 10 risk scores, open SoD count, cert completion %, terminated-with-access count. One sentence each on owner and SLA.

---

## Summary

- Weight critical banking entitlements so scores reflect real loss potential.
- Use scores to aim certifications and monitoring.
- Never treat a number as an automatic revoke engine.

---

**Previous:** [Lesson 41 — Policy Violations & Mitigation](41-policy-violations-mitigation.md)  
**Next:** [Lesson 43 — Manager Certifications](43-manager-certifications.md)
