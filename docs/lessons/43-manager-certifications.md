# Lesson 43 — Manager Access Certifications

**Level:** Intermediate  
**Track:** Certifications  
**Time:** 90–120  
**Prereq:** Lesson 42 — Risk Scores  

**Lab data:** `notifications/certification-sample.txt`, `apps/MNB-WirePortal.csv`, `apps/MNB-SAP-Finance.csv`, `apps/MNB-AWS-Cloud.csv`

---

## Learning objectives

You will be able to:

- Create a scoped **manager certification** campaign for Meridian (`MNB-Q-Lab-Manager-Cert`)
- Limit inclusion to high-risk entitlements on Wire Portal, SAP Finance, and AWS
- Generate the campaign and complete decisions as a manager (e.g., `rachel.evans`)
- Align notification tone with `certification-sample.txt`
- Explain why tight scopes beat “approve everything” thousand-line campaigns

---

## Why this matters

Quarterly access reviews are how managers attest that access still matches job reality. Oversized campaigns train managers to rubber-stamp. Examiners sample decisions for evidence of thought—not completion percentage alone.

Meridian’s Identity Governance Office sends clear, actionable mail (see sample). Your job is to make the work item match that promise: short scope, due date, high-risk focus.

---

## Concepts

A **manager certification** assigns each line item to the identity’s manager. Decisions typically include:

| Decision | Use when |
| --- | --- |
| **Approve** / Maintain | Access still required for role |
| **Revoke** | Access no longer needed or toxic |
| **Delegate** | Manager cannot decide; route to knowledgeable reviewer |
| **Allow exception** / account for | Temporary keep with comment (use sparingly; prefer revoke or policy mitigate) |

```
Population / entitlement filter
        │
        ▼
 Campaign generate ──► Work items per manager
        │
        ▼
 Decisions (approve / revoke / delegate)
        │
        ▼
 Remediation provisioning (Lesson 46)
```

**Scope for this lab:** High-risk entitlements only — Wire (`WIRE_INIT` / `WIRE_APPR`), SAP (`SAP_FI`), AWS (`AWS_ADMIN`). Population: Treasury / payments managers’ reports (e.g., reports of `rachel.evans`) or a small `MNB-Treasury` population if you built one in Lesson 07.

**Sample mail tone** (`lab-data/notifications/certification-sample.txt`): campaign name, scope, due date (10 business days), login path to Work Item Inbox.

**Campaign sizing rule of thumb:** If a manager needs more than ~30–45 minutes of focused review, you overscoped. Split by app, risk tier, or org slice rather than training Approve All.

**Delegation policy (lab default):** Delegate only to a knowledgeable peer or app owner; never to a peer who will Approve All on your behalf. Document every delegation reason.

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq`
- [ ] Manager hierarchy intact (`priya.wire` → `rachel.evans` from Lesson 21)
- [ ] Wire / SAP / AWS apps correlated
- [ ] Copy of `~/iiq-lab-data/notifications/certification-sample.txt` open
- [ ] Risk weights from Lesson 42 optional but helpful for prioritization story

---

## Lab procedure

### Task 1 — Read the sample notification

1. Open `lab-data/notifications/certification-sample.txt` (or `~/iiq-lab-data/notifications/...`).
2. Note: From `identity-noreply@meridiannb.com`, To `rachel.evans@meridiannb.com`, campaign `MNB-Q3-Manager-Cert-Treasury`, due in 10 business days, high-risk Wire/SAP/AWS scope.
3. Write three attributes your IIQ cert email must include: campaign name, due date, how to open the work item.

**Expected result:** Checklist of actionable email elements ready for Lesson 49 alignment.

### Task 2 — Define scope

1. Create or reuse population: managers’ reports under Treasury / payments, **or** filter identities with Wire/SAP/AWS entitlements whose manager is `rachel.evans`.
2. Entitlement inclusion: only critical payment/finance/cloud ents—exclude birthright `ELDAP` / CRM noise if the cert type allows entitlement filters.
3. Name campaign: `MNB-Q-Lab-Manager-Cert` (lab). Production-style name in sample is `MNB-Q3-Manager-Cert-Treasury`.

**Expected result:** Written scope: who + which apps/ents + campaign name.

**If it fails:** If entitlement filter UI is limited, certify a tiny population (≤15 identities) instead of filtering ents—still document intent.

### Task 3 — Create manager certification

1. Navigate to **Certifications** → Create / New Certification (or equivalent Certification Schedule).
2. Type: **Manager** certification.
3. Set name `MNB-Q-Lab-Manager-Cert`, short description, due date ~10 business days out.
4. Attach population / inclusion rules from Task 2.
5. Enable notifications if lab SMTP exists; otherwise proceed and rely on work items.
6. Save / schedule / generate as required by your IIQ version.

**Expected result:** Campaign object exists in Staging or Active state.

**If it fails:** Confirm LCM / certification features initialized; check required fields (owner, period, certifier rules).

### Task 4 — Generate and open as manager

1. **Generate** the certification (if separate from create).
2. Open **Work Item Inbox** as `rachel.evans` (or proxy/login as manager).
3. Open `MNB-Q-Lab-Manager-Cert` work item.
4. Spot-check line items: Priya wire init, Marcus approve, any SAP/AWS on reports.

**Expected result:** Manager sees a manageable list focused on high-risk access—not hundreds of ELDAP rows.

### Task 5 — Complete decisions

1. **Approve** clearly job-appropriate access (e.g., Priya `WIRE_INIT` if still in Treasury wire role).
2. **Revoke** anything residual/wrong (e.g., AWS on a non-cloud report if present; leftover mover access).
3. Use **Delegate** once for practice if UI allows; note rule for when delegation is OK.
4. Sign off / complete the certification phase for this manager.
5. As admin, note campaign completion % and any open remediations.

**Expected result:** At least one approve and one revoke recorded; campaign progress advanced.

**If it fails:** If login-as is disabled, complete decisions from admin forward/certifier reassignment for lab only—and note that production forbids admin rubber-stamping.

### Task 6 — Compare notifications

1. Compare sample subject/body to IIQ’s default certification email template text (preview or Debug `EmailTemplate`).
2. List gaps: missing due date? missing scope? weak CTA?
3. Park improvements for Lesson 49.

**Expected result:** Gap list of 3+ items vs `certification-sample.txt`.

---

## Acceptance criteria

- [ ] Campaign `MNB-Q-Lab-Manager-Cert` created and generated
- [ ] Scope limited to high-risk Wire/SAP/AWS (or tiny population with documented intent)
- [ ] Manager work item opened and decisions completed (approve + revoke)
- [ ] Sample email compared; gaps noted
- [ ] Completion % recorded for binder

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Empty cert | Population empty / no ents match | Broaden slightly; verify manager links |
| Thousand-line cert | No entitlement filter | Restrict ents or population; regenerate |
| Manager inbox empty | Wrong certifier / not generated | Generate; check certifier = manager |
| Cannot decide | Phase locked / already signed | Use admin forward or new campaign |
| Email never sends | SMTP off in lab | Expected; use sample + work item proof |

---

## Training binder evidence

- Screenshot: campaign definition (name, due date, scope)
- Screenshot: manager work item with one approve + one revoke
- Completion % note
- Annotated copy of `certification-sample.txt` with gaps vs IIQ defaults

---

## Knowledge check

1. Why keep manager cert scopes tight?
2. Name four decision types commonly available.
3. Who receives the sample Treasury cert email?
4. What three apps/entitlement domains are in lab scope?
5. What happens after revoke? (preview Lesson 46)

### Answers

1. Prevents rubber-stamping; improves decision quality for examiners.  
2. Approve/maintain, revoke, delegate, exception/allow (wording varies).  
3. `rachel.evans@meridiannb.com` (Payments Operations Manager).  
4. Wire Portal, SAP Finance, AWS Admin (high-risk).  
5. Remediation / provisioning must complete—cert “done” is incomplete until revokes close.

---

## Stretch lab

Enable lab email if SMTP is available; capture one generated message and store beside `certification-sample.txt`. Or add a 48-hour reminder template note for overdue managers.

---

## Summary

- Manager certs attest people-context; scope them to high-risk access.
- Generate, decide, measure completion—then chase remediations.
- Notifications must be as clear as Meridian’s sample mail.

---

**Previous:** [Lesson 42 — Risk Scores](42-risk-scores.md)  
**Next:** [Lesson 44 — Application Owner Certifications](44-app-owner-certifications.md)
