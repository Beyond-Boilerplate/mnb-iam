# Lesson 44 — Application Owner Certifications

**Level:** Intermediate  
**Track:** Certifications  
**Time:** 60–90  
**Prereq:** Lesson 43 — Manager Certifications  

**Lab data:** `apps/MNB-WirePortal.csv`, `apps/MNB-AWS-Cloud.csv`

---

## Learning objectives

You will be able to:

- Create an **application owner certification** for `MNB-WirePortal` or `MNB-AWS-Cloud`
- Complete decisions as the application owner (accountable human, not a mailbox)
- Compare decision quality and blind spots vs the Lesson 43 manager certification
- Document Meridian cadence: manager quarterly; critical-app owner semi-annual
- Capture owner sign-off evidence for the training binder

---

## Why this matters

Managers know people and org charts. Application owners know which entitlements are toxic on *their* system—wire approve vs initiate, AWS admin blast radius, who should never hold both.

Owner certifications catch stale contractor cloud access and mis-assigned wire rights that a busy Treasury manager might rubber-stamp. Examiners expect both people-centric and system-centric reviews on critical banking apps.

---

## Concepts

An **application owner certification** reviews accounts/entitlements on one application, certified by the app’s owner (or designated certifiers), independent of HR manager quality.

| Dimension | Manager cert (L43) | App owner cert (L44) |
| --- | --- | --- |
| Lens | Person / job fit | System / entitlement toxicity |
| Blind spot | Weak managers; cross-app sprawl | People context (“why does Priya need this?”) |
| Best for | Quarterly high-risk people review | Semi-annual critical app deep dive |
| Cadence (Meridian) | Quarterly | Semi-annual for Wire / AWS / SAP / Core |
| Anti-pattern | Approve-all | Owner = shared DL nobody reads |

```
App owner assigned on Application object
        │
        ▼
 Owner certification generated
        │
        ▼
 Line items = accounts/ents on that app
        │
        ├── Maintain legitimate ops access
        └── Revoke contractors / residuals / toxic combos
```

**Lab choice:** Prefer `MNB-WirePortal` first (payment dual control). Stretch: `MNB-AWS-Cloud` (catch `raj.external` / residual `jordan.reed`).

**RACI (owner cert)**

| Activity | IAM | App owner | Risk | Manager |
| --- | --- | --- | --- | --- |
| Set Application.owner | R/A | C | I | I |
| Complete cert decisions | C | R/A | I | C (context) |
| Close remediations | R | C | I | I |
| Cadence exceptions | C | C | A | I |

Owners who “delegate everything back to IAM” recreate the manager rubber-stamp problem under a different name—call that out in QA.

---

## Before you start

- [ ] Lesson 43 manager cert exists (for comparison write-up)
- [ ] Application `MNB-WirePortal` (and/or `MNB-AWS-Cloud`) has a real **owner** identity set (e.g., `rachel.evans` for Wire; cloud platform lead for AWS—use a named Meridian identity, not `spadmin`)
- [ ] Account Aggregation completed for the target app
- [ ] IIQ login as `spadmin` plus ability to open owner work items

---

## Lab procedure

### Task 1 — Confirm application owner

1. Open **Applications** → `MNB-WirePortal` (or `MNB-AWS-Cloud`).
2. Verify **Owner** is a named accountable human (e.g., `rachel.evans@meridiannb.com` for Wire).
3. If owner is blank or `spadmin`, set a Meridian persona and save.
4. Note: production forbids DL-only ownership without a named secondary.

**Expected result:** Application shows a human owner you can log in as / forward to.

**If it fails:** Set owner via Debug Application XML only if UI blocked; document the change.

### Task 2 — Create application owner certification

1. Certifications → Create → type **Application Owner** (or equivalent Application certification).
2. Name: `MNB-Q-Lab-Owner-Cert-Wire` (or `...-AWS`).
3. Select application `MNB-WirePortal` (or AWS).
4. Due date: shorter than manager cert is OK for lab (5–10 business days).
5. Generate / activate.

**Expected result:** Owner campaign listed; work item destined to application owner.

### Task 3 — Complete as owner

1. Open Work Item Inbox as the app owner.
2. Review each account/entitlement:
   - Keep `priya.wire` / `WIRE_INIT` and `marcus.approve` / `WIRE_APPR` split clean.
   - Revoke any identity holding both initiate and approve if present.
   - On AWS campaign: scrutinize `raj.external` and any terminated residuals.
3. Add comments on revoke lines (examiner gold).
4. Sign off the owner certification.

**Expected result:** Completed owner cert with ≥1 thoughtful revoke or explicit maintain comments on privileged rows.

**If it fails:** Forward work item to owner; do not bulk-approve as spadmin for “lab convenience” without noting it as invalid production practice.

### Task 4 — Manager vs owner comparison (write 5 lines)

Write five lines covering:

1. What manager cert caught that owner might miss  
2. What owner cert caught that manager might miss  
3. When Meridian prefers owner cert (incident, toxic entitlement, contractor cloud)  
4. Cadence: manager quarterly; owner semi-annual for critical apps  
5. Shared anti-pattern: rubber-stamp / DL owner  

**Expected result:** Half-page comparison in binder titled `MNB-Cert-Type-Compare`.

### Task 5 — Evidence pack

1. Screenshot campaign definition + owner name.
2. Screenshot completed decisions (blur if needed in shared labs).
3. Record completion timestamp and any open remediations.

**Expected result:** Owner cert evidence ready for Lesson 46 / Capstone.

---

## Acceptance criteria

- [ ] Human owner set on Wire or AWS application
- [ ] Owner certification created, generated, and completed
- [ ] At least one risk-based revoke or documented maintain on privileged access
- [ ] Five-line manager vs owner comparison written
- [ ] Cadence rule documented (quarterly vs semi-annual)

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No certifier | Owner blank | Set Application owner |
| Empty line items | Aggregation stale | Run Account Aggregation; regenerate |
| Owner is spadmin | Lab shortcut | Reassign to Meridian persona |
| Same decisions as manager | Wrong lens | Focus on entitlement toxicity, not HR job title |
| Dual wire access missed | Split across apps | Include both initiator and approver extracts |

---

## Training binder evidence

- App owner field screenshot
- Campaign `MNB-Q-Lab-Owner-Cert-*` definition
- Completed decisions with comments
- `MNB-Cert-Type-Compare` five-line note

---

## Knowledge check

1. When prefer an owner cert over a manager cert?
2. What is Meridian’s cadence for critical-app owner reviews?
3. Name the owner anti-pattern.
4. Which lab apps are primary candidates?
5. Who should own `MNB-WirePortal` in spirit?

### Answers

1. When validating toxic entitlements, contractors on a system, or after an app-centric finding.  
2. Semi-annual for critical apps (Wire/AWS/SAP/Core); managers remain quarterly.  
3. Owner is a distribution list / nobody-accountable mailbox.  
4. `MNB-WirePortal` and `MNB-AWS-Cloud`.  
5. A named payments/Treasury accountable human (e.g., `rachel.evans`), not IAM admin.

---

## Stretch lab

Run the second app (AWS if you did Wire first). Explicitly decide on `raj.external` AWS_ADMIN and document contractor justification or revoke.

---

## Summary

- Owner certs add a system lens managers lack.
- Critical Meridian apps need named human owners and semi-annual reviews.
- Compare—don’t replace—manager certifications.

---

**Previous:** [Lesson 43 — Manager Certifications](43-manager-certifications.md)  
**Next:** [Lesson 45 — Targeted Campaigns](45-targeted-campaigns.md)
