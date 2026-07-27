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
- Tie the campaign to a finding ID (`FIND-IAM-45-001`) for evidence packs

---

## Why this matters

**Business.** Quarterly manager reviews are necessary but slow. After a failed leaver (`jordan.reed` residuals), cloud incident, or audit finding on contractor AWS (`raj.external`), Meridian needs an agile cert that answers one question well: “Who still has this dangerous access *right now*?”

**Control / audit.** Targeted campaigns are examiner favorites when tied to a finding ID and closed with remediation evidence — not when used as theater without follow-through. Control owner: IAM lead (`helen.ross`) with Risk air cover; certifiers prioritize over routine quarterly noise.

---

## Concepts

### What a targeted / focused certification is

A **targeted / focused certification** is a narrowly scoped campaign (population + optional entitlement filter) with a short SLA, often triggered by risk events — not the quarterly calendar.

| Focus option | Population logic | Why Meridian cares |
| --- | --- | --- |
| **Terminated-with-access** | HR inactive / terminated **and** still holds app ents | Classic orphan / residual access (`jordan.reed`) |
| **Contractors-with-AWS** | `workerType=Contractor` (or equivalent) **and** `AWS_ADMIN` | Vendor cloud blast radius (`raj.external`) |
| On-leave-with-privileged | LOA flag + critical ents | Stretch; Lesson 33 adjacency |

### Air cover and success metrics

**Air cover email (template)** — send from IAM lead / Risk before launch:

> We are launching `{campaign}` under finding `{FIND-ID}`. Due in 5 business days. Scope is intentionally small. Please prioritize over routine quarterly noise. Escalations: `helen.ross@meridiannb.com`.

Without that message, micro-certs lose to inbox fatigue.

**Success metrics:** % complete by day 5; % of revokes closed by day 10; residual open items with named owners.

### How targeted certs relate to SoD and leavers

Micro-certs are not SoD policies. If Terminated-with-access finds Jordan still holding `SAP_FI`+`AWS_ADMIN`, you still open (or reopen) `MNB-SOD-Finance-Cloud` remediation — the cert removes access; the policy explains why the combo was forbidden. Likewise, Contractor AWS maintains must cite a ticket; standing contractor admin without expiry fails the same exam as eternal SoD mitigations (Lesson 41).

### Meridian example — when to pick which focus

After Lesson 31, if `jordan.reed` still shows `SAP_FI` / `AWS_ADMIN` on terminated status, **Terminated-with-access** is the honest micro-cert — it answers Internal Audit’s “did leavers clear?” finding. If Jordan was cleaned but `raj.external` still holds `AWS_ADMIN` after a cloud change window, **Contractors-with-AWS** is the right knife.

You can run both over a quarter; do not merge them into one vague “risky people” population. Precision is the control.

The wrong way: launch a “targeted” cert that is secretly the whole bank again. Examiners see calendar theater with a new name.

---

## How it works

```
Risk trigger / finding (FIND-IAM-45-001)
        │
        ▼
 Build population (precise)
        │  Terminated-with-access  OR  Contractors-with-AWS
        ▼
 Micro-cert (due ~5 days) + exec air cover
        │
        ▼
 Decisions → remediations → one-pager to Risk
```

| Focus | Campaign name | Default bias |
| --- | --- | --- |
| Contractors-with-AWS | `MNB-Micro-Cert-Contractors-AWS` | Maintain only with ticketed justification |
| Terminated-with-access | `MNB-Micro-Cert-Terminated-Access` | **Revoke** |

| Metric | Target | Owner |
| --- | --- | --- |
| Decisions complete | Day 5 | Certifiers + helen.ross escalation |
| Revokes closed | Day 10 | IAM Ops |
| Residual open items | Named owner + date | Risk tracks |

**Pick one focus for the lab.** Recommended: Contractors-with-AWS if `raj.external` is active; Terminated-with-access if you ran Jordan’s leaver delta and residuals remain.

---

## Before you start

- [ ] Populations skill from Lesson 07 available
- [ ] HR attributes distinguish Employee vs Contractor (or inactive status)
- [ ] AWS and/or residual leaver data aggregated
- [ ] Stakeholder note: micro-certs need manager priority (air cover) — document who asked for this campaign
- [ ] Binder folder `MNB-Exam-Binder-Certs/` exists (seeded in Lesson 43) or create it now
- [ ] Decide focus before opening the certification wizard — changing populations mid-campaign confuses evidence

---

## Lab procedure

### Task 1 — Choose the focus risk

Finding IDs turn a campaign into a control response. Write the trigger first. If you cannot name the finding, you are inventing theater.

1. Pick **Terminated-with-access** *or* **Contractors-with-AWS**.
2. Write the trigger in one sentence (e.g., “Post-leaver drill showed residual AWS on terminated finance user” or “Vendor AWS admin must be attested after cloud change window”).
3. Assign a fictional finding ID: `FIND-IAM-45-001`.
4. Note the executive sponsor (Risk or `helen.ross`) who will send air cover.

**Expected result:** Focus + trigger sentence + finding ID + sponsor in notebook.

### Task 2 — Build the population

Precision beats size. Empty populations teach nothing; 200-row “micro” certs are quarterly certs in disguise. Record the population rule text verbatim — examiners ask how you defined “terminated with access.”

**Option A — Contractors-with-AWS**

1. Advanced search / population: worker type Contractor (or identity `raj.external`) AND entitlement `AWS_ADMIN` on `MNB-AWS-Cloud`.
2. Name population `MNB-Pop-Contractors-AWS`.
3. Spot-check: `raj.external` should appear if still entitled; employees without AWS should not.

**Option B — Terminated-with-access**

1. Population: inactive/terminated identities that still have accounts on Wire/SAP/AWS/AD.
2. Seed with Jordan leaver scenario residuals if present (`SAP_FI`, `AWS_ADMIN`, `GL_POST`).
3. Name population `MNB-Pop-Terminated-With-Access`.
4. Spot-check: active tellers like `nina.joiner` must not appear.

**Expected result:** Population returns a small, non-zero set (ideally ≤20); spot-checks recorded.

**If it fails:** Manually include known personas (`raj.external`, terminated jordan) in a static population for lab.

### Task 3 — Launch micro-cert

Short SLA is the point. Ten-business-day due dates belong to quarterly manager certs (Lesson 43).

1. Create certification (manager, app owner, or targeted/advanced type — whichever fits your population best).
2. Name: `MNB-Micro-Cert-Contractors-AWS` or `MNB-Micro-Cert-Terminated-Access`.
3. Due date: **5 business days**.
4. Description references `FIND-IAM-45-001`.
5. Generate and notify certifiers (or open work items directly). Draft the air cover note to `helen.ross@meridiannb.com` escalation path.

**Expected result:** Active short-SLA campaign with finding ID in description.

### Task 4 — Decide and remediate

Zero “I’ll get to it later” revokes without a ticket. Targeted certs exist to close risk, not open it.

1. Complete decisions quickly — default bias toward **revoke** for terminated; for contractors, maintain only with ticketed justification.
2. Open any remediation work items / provisioning from revokes.
3. Track to closed or document blocker (Lesson 46/47 if stuck).

**Expected result:** Zero “I’ll get to it later” revokes without a ticket.

### Task 5 — One-page Risk summary

Risk committees do not read campaign UIs. Close with a one-pager.

Draft a one-pager with:

- Finding ID and trigger  
- Population definition  
- Campaign name / due date / completion %  
- Revokes requested vs completed  
- Residual risk still open  
- Owner for follow-ups  

**Expected result:** `MNB-Micro-Cert-Summary-YYYY-MM-DD` suitable for Risk committee.

### Task 6 — File evidence into the cert binder

1. Add population rule, campaign definition (with `FIND-IAM-45-001`), completion %, and Risk one-pager into `MNB-Exam-Binder-Certs/`.
2. Cross-link to Lesson 43/44 artifacts so examiners see quarterly + event-driven coverage.
3. Note any remediations still open with Lesson 46/47 handoff.

**Expected result:** Micro-cert section present in the shared evidence binder.

---

## Acceptance criteria

- [ ] Focus risk chosen with finding ID
- [ ] Population built and non-empty
- [ ] Micro-cert launched with ~5-day due date
- [ ] Decisions completed; remediations tracked
- [ ] One-page summary written for Risk
- [ ] Evidence filed in `MNB-Exam-Binder-Certs/`

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Empty population | Attribute names differ | Inspect cube attrs; use static include |
| Managers ignore micro-cert | No air cover | Email from helen.ross / Risk; shorten list further |
| Overlaps quarterly cert | Expected | Document as finding-driven, not duplicate theater |
| Remediations stall | Connector/path issues | Jump to Lesson 47 playbook |
| Too large | Filters weak | Add entitlement AND status constraints |
| Finding ID missing from description | Rushed create | Edit campaign description; regenerate mail text if needed |

---

## Training binder evidence

- Population definition screenshot / rule text
- Campaign definition with finding ID
- Completion % and revoke tally
- One-page Risk summary dated
- Binder index entry linking `FIND-IAM-45-001` to L43/L44 artifacts

---

## Knowledge check

1. Give one incident that justifies a targeted cert.
2. What due-date strategy fits micro-certs?
3. What goes in the one-pager?
4. Why do examiners like targeted campaigns?
5. Default bias for terminated-with-access decisions?
6. What finding ID does this lab use?

### Answers

1. Failed leaver with residual access; cloud incident; audit finding on contractors.
2. Short SLA (about 5 business days) with executive priority.
3. Trigger, scope, completion, revoke closure, residual risk, owners.
4. They prove agile response tied to findings, not calendar-only compliance.
5. Revoke; maintain only with exceptional documented justification.
6. `FIND-IAM-45-001`.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “targeted certification” / “advanced certification.”
- [SailPoint Community](https://community.sailpoint.com/) — search “focused certification” for event-driven campaign patterns.
- [NIST SP 800-53 CA-7 — Continuous Monitoring](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) — risk-triggered reviews beyond periodic schedules.
- [FFIEC Information Technology Examination Handbook](https://ithandbook.ffiec.gov/) — search issue tracking / corrective action for finding-driven access reviews.
- [ISACA — Audit finding remediation primers](https://www.isaca.org/) — search “finding remediation” for one-pager evidence expectations.

---

## Stretch lab

Automate a quarterly schedule that launches `MNB-Pop-Contractors-AWS` micro-cert automatically. Document the Task schedule name and recipient list. Optional: after a rapid-offboarding drill (Lesson 34), launch a 48-hour Terminated-with-access micro-cert for the drill identity’s residual apps — proof that incident response and certification talk to each other.

---

## Summary

- Targeted certs answer one risk question fast.
- Short SLA + remediation closure beats vanity campaigns.
- Always close with a Risk one-pager and finding ID.
- File micro-cert evidence beside quarterly packs so examiners see both rhythms.

---

**Previous:** [Lesson 44 — Application Owner Certifications](44-app-owner-certifications.md)  
**Next:** [Lesson 46 — Certification Remediation & Evidence](46-cert-remediation-evidence.md)
