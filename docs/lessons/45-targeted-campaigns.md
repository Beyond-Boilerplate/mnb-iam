# Lesson 45 — Targeted & Focused Campaigns

**Level:** Advanced  
**Track:** Certifications  
**Time:** 45–60  
**Prereq:** Lesson 44 — Application Owner Certifications  

**Lab data:** `scenarios/leaver/hr-delta-terminate-jordan.csv`, `apps/MNB-AWS-Cloud.csv`, `hr/MNB-HR-Employees.csv`

---

## Learning objectives

You will be able to:

- Design a **targeted micro-certification** driven by a concrete risk (not the quarter calendar)
- Build or reuse a population for **Terminated-with-access** or **Contractors-with-AWS**
- Launch a short-lived campaign (≈5 business day due date)
- Track revokes into remediation and close with a one-page Risk committee summary
- Explain when examiners favor targeted campaigns after incidents or failed controls

---

## Why this matters

Quarterly manager reviews are necessary but slow. After a failed leaver, cloud incident, or audit finding, Meridian needs an agile cert that answers one question well: “Who still has this dangerous access *right now*?”

Targeted campaigns are examiner favorites when tied to a finding ID and closed with remediation evidence—not when used as theater without follow-through.

---

## Concepts

A **targeted / focused certification** is a narrowly scoped campaign (population + optional entitlement filter) with a short SLA, often triggered by risk events.

| Focus option | Population logic | Why Meridian cares |
| --- | --- | --- |
| **Terminated-with-access** | HR inactive / terminated **and** still holds app ents | Classic orphan / residual access |
| **Contractors-with-AWS** | `workerType=Contractor` (or equivalent) **and** `AWS_ADMIN` | Vendor cloud blast radius (`raj.external`) |
| On-leave-with-privileged | LOA flag + critical ents | Stretch; Lesson 33 adjacency |

```
Risk trigger / finding
        │
        ▼
 Build population (precise)
        │
        ▼
 Micro-cert (due ~5 days) + exec air cover
        │
        ▼
 Decisions → remediations → one-pager to Risk
```

**Pick one focus for the lab.** Recommended: Contractors-with-AWS if `raj.external` is active; Terminated-with-access if you ran Jordan’s leaver delta and residuals remain.

**Air cover email (template)** — send from IAM lead / Risk before launch:

> We are launching `{campaign}` under finding `{FIND-ID}`. Due in 5 business days. Scope is intentionally small. Please prioritize over routine quarterly noise. Escalations: `helen.ross@meridiannb.com`.

Without that message, micro-certs lose to inbox fatigue.

**Success metrics:** % complete by day 5; % of revokes closed by day 10; residual open items with named owners.

---

## Before you start

- [ ] Populations skill from Lesson 07 available
- [ ] HR attributes distinguish Employee vs Contractor (or inactive status)
- [ ] AWS and/or residual leaver data aggregated
- [ ] Stakeholder note: micro-certs need manager priority (air cover)—document who asked for this campaign

---

## Lab procedure

### Task 1 — Choose the focus risk

1. Pick **Terminated-with-access** *or* **Contractors-with-AWS**.
2. Write the trigger in one sentence (e.g., “Post-leaver drill showed residual AWS on terminated finance user” or “Vendor AWS admin must be attested after cloud change window”).
3. Assign a fictional finding ID: `FIND-IAM-45-001`.

**Expected result:** Focus + trigger sentence + finding ID in notebook.

### Task 2 — Build the population

**Option A — Contractors-with-AWS**

1. Advanced search / population: worker type Contractor (or identity `raj.external`) AND entitlement `AWS_ADMIN` on `MNB-AWS-Cloud`.
2. Name population `MNB-Pop-Contractors-AWS`.

**Option B — Terminated-with-access**

1. Population: inactive/terminated identities that still have accounts on Wire/SAP/AWS/AD.
2. Seed with Jordan leaver scenario residuals if present.
3. Name population `MNB-Pop-Terminated-With-Access`.

**Expected result:** Population returns a small, non-zero set (ideally ≤20).

**If it fails:** Manually include known personas (`raj.external`, terminated jordan) in a static population for lab.

### Task 3 — Launch micro-cert

1. Create certification (manager, app owner, or targeted/advanced type—whichever fits your population best).
2. Name: `MNB-Micro-Cert-Contractors-AWS` or `MNB-Micro-Cert-Terminated-Access`.
3. Due date: **5 business days**.
4. Description references `FIND-IAM-45-001`.
5. Generate and notify certifiers (or open work items directly).

**Expected result:** Active short-SLA campaign with finding ID in description.

### Task 4 — Decide and remediate

1. Complete decisions quickly—default bias toward **revoke** for terminated; for contractors, maintain only with ticketed justification.
2. Open any remediation work items / provisioning from revokes.
3. Track to closed or document blocker (Lesson 46/47 if stuck).

**Expected result:** Zero “I’ll get to it later” revokes without a ticket.

### Task 5 — One-page Risk summary

Draft a one-pager with:

- Finding ID and trigger  
- Population definition  
- Campaign name / due date / completion %  
- Revokes requested vs completed  
- Residual risk still open  
- Owner for follow-ups  

**Expected result:** `MNB-Micro-Cert-Summary-YYYY-MM-DD` suitable for Risk committee.

---

## Acceptance criteria

- [ ] Focus risk chosen with finding ID
- [ ] Population built and non-empty
- [ ] Micro-cert launched with ~5-day due date
- [ ] Decisions completed; remediations tracked
- [ ] One-page summary written for Risk

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Empty population | Attribute names differ | Inspect cube attrs; use static include |
| Managers ignore micro-cert | No air cover | Email from helen.ross / Risk; shorten list further |
| Overlaps quarterly cert | Expected | Document as finding-driven, not duplicate theater |
| Remediations stall | Connector/path issues | Jump to Lesson 47 playbook |
| Too large | Filters weak | Add entitlement AND status constraints |

---

## Training binder evidence

- Population definition screenshot / rule text
- Campaign definition with finding ID
- Completion % and revoke tally
- One-page Risk summary dated

---

## Knowledge check

1. Give one incident that justifies a targeted cert.
2. What due-date strategy fits micro-certs?
3. What goes in the one-pager?
4. Why do examiners like targeted campaigns?
5. Default bias for terminated-with-access decisions?

### Answers

1. Failed leaver with residual access; cloud incident; audit finding on contractors.  
2. Short SLA (about 5 business days) with executive priority.  
3. Trigger, scope, completion, revoke closure, residual risk, owners.  
4. They prove agile response tied to findings, not calendar-only compliance.  
5. Revoke; maintain only with exceptional documented justification.

---

## Stretch lab

Automate a quarterly schedule that launches `MNB-Pop-Contractors-AWS` micro-cert automatically. Document the Task schedule name and recipient list.

---

## Summary

- Targeted certs answer one risk question fast.
- Short SLA + remediation closure beats vanity campaigns.
- Always close with a Risk one-pager and finding ID.

---

**Previous:** [Lesson 44 — Application Owner Certifications](44-app-owner-certifications.md)  
**Next:** [Lesson 46 — Certification Remediation & Evidence](46-cert-remediation-evidence.md)
