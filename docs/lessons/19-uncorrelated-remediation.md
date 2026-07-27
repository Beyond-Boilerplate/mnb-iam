# Lesson 19 — Uncorrelated Account Remediation

**Level:** Intermediate  
**Track:** Correlation  
**Time:** 60–75 min  
**Prereq:** Lessons 17–18  

**Lab data:**
- Uncorrelated / weakly linked accounts across `MNB-*` target apps
- Privileged watchlist: `AWS_ADMIN`, `WIRE_*`, `SAP_FI`, `CORE`
- Persona emphasis: vendor/contractor and data-quality orphans (e.g. residual uncorrelated after Lesson 18)

---

## Learning objectives

You will be able to:

- Build an **uncorrelated account inventory** across Meridian applications
- **Classify** each item: correlate, disable/remove, or accept-with-ticket
- Execute safe remediation: fix correlation keys, manual correlate when justified, or mark for disable
- Apply severity SLAs for privileged uncorrelated access
- Produce examiner-ready remediation evidence without creating rogue identities

---

## Why this matters

**Business.** Uncorrelated accounts are operational debt. Left alone, they become the pathway for ex-vendors and forgotten service IDs. Meridian’s cloud and wire platforms make that debt urgent.

**Control / audit.** Auditors sample uncorrelated privileged accounts and ask for age, severity, and disposition. “We’ll look someday” fails. A classify → act → evidence loop is the control.

---

## Concepts

**Remediation dispositions:**

| Disposition | When | Action |
| --- | --- | --- |
| **Correlate** | Valid person exists; key mismatch/typo or rule gap | Fix data or manual correlate to correct cube |
| **Disable** | No valid owner; terminated vendor; stale ID | Disable account in source / flag for app owner; track ticket |
| **Exception** | Break-glass or service account pending vaulting | Document owner, review date, compensating control |

```
Uncorrelated account discovered
        │
        ▼
Privileged? ──yes──► Sev-1 SLA (e.g. 24h triage)
        │
        ▼
HR person match via employeeId/email/manual proof?
   │ yes                         │ no
   ▼                             ▼
Correlate + evidence          Disable / exception ticket
```

**Never:** create a new identity from an uncorrelated privileged account “so certs look clean.”

**Manual correlation.** IIQ UIs often allow linking an account to an identity when attribute correlation cannot. Use only with dual control / peer review in prod; in lab, document why the link is correct (`employeeId` proof).

---

## Before you start

- [ ] Correlation configured on IT-Access and AWS (Lessons 17–18)
- [ ] Ability to list uncorrelated accounts per application
- [ ] Ticket template ready (`MNB-LAB-UNC-###`)
- [ ] Privileged entitlement list from dictionary handy
- [ ] `spadmin` session; binder “Uncorrelated remediation log”

---

## Lab procedure

### Task 1 — Build the uncorrelated inventory

1. For each major target app, open Accounts and filter/view **Uncorrelated** (or equivalent):
   - `MNB-IT-Access`
   - `MNB-AWS-Cloud`
   - `MNB-WirePortal`
   - `MNB-SAP-Finance`
   - `MNB-CoreBanking`
   - Digital / CRM / AD as time allows
2. Export or hand-copy into a table:

| App | Account | Entitlements | Email | employeeId | Age (lab: “seen on”) |
| --- | --- | --- | --- | --- | --- |

3. Highlight any row with `AWS_ADMIN`, `WIRE_INIT`, `WIRE_APPR`, `SAP_FI`, `CORE`.

**Expected result:** Single inventory sheet of residuals after correlation work.

**If it fails:** If everything is correlated, still pick 2–3 accounts and walk the classification exercise using hypothetical “typo employeeId” reasoning—or temporarily review AD disabled orphans.

---

### Task 2 — Classify each privileged row

1. For each highlighted row, assign disposition: Correlate / Disable / Exception.
2. Apply rules:
   - Has matching HR `employeeId` → **Correlate**
   - Vendor with no HR cube and privileged access → **Disable** (or Exception only with named sponsor)
   - Service-looking name without HR → **Exception** with owner or **Disable**
3. Assign severity: privileged uncorrelated = **Sev-1**; standard ELDAP/CRM = Sev-2/3.

**Expected result:** Every privileged uncorrelated account has a disposition—no blank “TBD” for Sev-1.

---

### Task 3 — Remediate by correlation (happy path)

1. Pick one uncorrelated account that clearly matches an HR identity (same employeeId).
2. Prefer fixing configuration/data and re-aggregating (Lessons 17–18).
3. If attributes already match but UI still shows uncorrelated, use **manual correlate** to the correct identity (or equivalent menu path).
4. Record ticket `MNB-LAB-UNC-001`: before screenshot, action, after screenshot.

**Expected result:** Account moves onto the correct cube; uncorrelated list shrinks by one with evidence.

**If it fails:** Stop if you are unsure of the person—wrong manual correlate is a false merge.

---

### Task 4 — Remediate by disable / owner handoff (no owner path)

1. Select a scenario account that should not remain enabled unowned (lab may require role-play if all privileged accounts are linked).
2. Document the disable request to the application owner:

```text
To: AWS owner (christopher.hayes)
Account: <id> on MNB-AWS-Cloud
Issue: Uncorrelated AWS_ADMIN > SLA
Request: Disable in AWS and confirm next extract
Ticket: MNB-LAB-UNC-002
```

3. In IIQ, if account status attribute exists, note expected `disabled` on next aggregate; do not delete historical evidence casually.
4. Binder: keep the ticket even if you cannot change a real AWS account in this delimited lab—process evidence counts.

**Expected result:** Disable/handoff path practiced with written owner request.

---

### Task 5 — Exception path (controlled accept)

1. Draft one exception record:

```text
Account: svc-wire-batch (example)
App: MNB-WirePortal
Disposition: Exception
Sponsor: rachel.evans
Review-by: <date + 30 days>
Compensating: vault password, no interactive login, cert in app-owner campaign
```

2. State aloud: exceptions are temporary controls, not silent forever orphans.

**Expected result:** Exception template exists for non-human accounts.

---

### Task 6 — SLA dashboard (lightweight)

1. Define Meridian lab SLAs:

| Class | Triage | Close |
| --- | --- | --- |
| Uncorrelated AWS_ADMIN / WIRE_* / SAP_FI / CORE | 24 hours | 5 business days |
| Other uncorrelated | 5 business days | 30 days |

2. Count current Sev-1 items from Task 1. If zero, write “Sev-1 = 0 after Lesson 18—monitor after each pipeline run.”

**Expected result:** Measurable SLA commitments in binder.

---

### Task 7 — Re-run pipeline spot check

1. Run Aggregate for any app you changed + Refresh.
2. Re-open uncorrelated inventory; update counts.
3. Confirm no new identities were created during remediation.

**Expected result:** Post-remediation metrics updated; identity count stable.

---

## Acceptance criteria

- [ ] Cross-app uncorrelated inventory created
- [ ] Privileged rows classified with dispositions
- [ ] At least one correlate-path remediation evidenced
- [ ] Disable/owner handoff message drafted
- [ ] Exception template drafted
- [ ] SLAs written; post-counts recorded
- [ ] No create-identities used as a “fix”

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Manual correlate options missing | UI role / version path differs | Use attribute fix + re-aggregate; note path used |
| Account correlates to two people somehow | Data clone / bad prior merge | Stop; escalate; do not keep both |
| Disable “does nothing” | Delimited file still says active | Change source CSV status for lab re-aggregate |
| Inventory empty | Correlation succeeded fully | Still complete classification drill with exception template |
| Temptation to create identity | Cleanliness pressure | Reject; orphans are findings until dispositioned |

---

## Training binder evidence

1. Uncorrelated inventory table (with privileged highlighting)
2. Disposition decisions for Sev-1 rows
3. Before/after screenshots for correlate remediation
4. Owner disable request email/Slack draft
5. Exception record sample
6. SLA table

Examiner question: *“Show your oldest uncorrelated privileged account and its ticket.”*

---

## Knowledge check

1. Name the three remediation dispositions used in this lesson.
2. What must you never do to clear privileged uncorrelated accounts quickly?
3. What severity fits uncorrelated `AWS_ADMIN`?
4. Who should receive a disable request for AWS orphans?
5. Why keep exceptions time-bounded?

### Answers

1. Correlate, Disable, Exception.
2. Create a new identity from the privileged account.
3. Sev-1 (24h triage class).
4. Technology / AWS application owner (`christopher.hayes` intent).
5. Otherwise exceptions become permanent unowned access with paperwork theater.

---

## Stretch lab

- Build population or report name `MNB-Uncorrelated-Privileged` as a future object.
- After Lesson 16 pipeline runs, add “uncorrelated Sev-1 count” to the daily ops checklist.

---

## Summary

- Uncorrelated accounts are tracked, classified, and closed—not ignored.
- Correlate when proof exists; disable or exception when it does not.
- Privileged orphans carry explicit SLAs and owner handoffs.

---

**Previous:** [Lesson 18 — Correlation Rules & Edge Cases](18-correlation-rules-advanced.md)  
**Next:** [Lesson 20 — Orphan & Dormant Access Hunting](20-orphan-dormant-hunting.md)
