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
- Record completion % as the start of the certification evidence pack (Lesson 46)

---

## Why this matters

**Business.** Quarterly access reviews are how managers attest that access still matches job reality. When `rachel.evans` reviews Priya’s `WIRE_INIT` and Marcus’s `WIRE_APPR`, she is affirming the payment dual-control staffing model — not rubber-stamping ELDAP noise. Oversized campaigns train managers to Approve All.

**Control / audit.** Examiners sample decisions for evidence of thought — not completion percentage alone. Meridian’s Identity Governance Office sends clear, actionable mail (see sample). Your job is to make the work item match that promise: short scope, due date, high-risk focus. Control owner: Identity Governance with managers as certifiers.

---

## Concepts

### What a manager certification is

A **manager certification** assigns each line item to the identity’s manager (from the cube hierarchy — Lesson 21). Decisions typically include:

| Decision | Use when |
| --- | --- |
| **Approve** / Maintain | Access still required for role |
| **Revoke** | Access no longer needed or toxic |
| **Delegate** | Manager cannot decide; route to knowledgeable reviewer |
| **Allow exception** / account for | Temporary keep with comment (use sparingly; prefer revoke or policy mitigate) |

### Scope discipline

**Scope for this lab:** High-risk entitlements only — Wire (`WIRE_INIT` / `WIRE_APPR`), SAP (`SAP_FI`), AWS (`AWS_ADMIN`). Population: Treasury / payments managers’ reports (e.g., reports of `rachel.evans`) or a small `MNB-Treasury` population if you built one in Lesson 07.

**Campaign sizing rule of thumb:** If a manager needs more than ~30–45 minutes of focused review, you overscoped. Split by app, risk tier, or org slice rather than training Approve All.

**Delegation policy (lab default):** Delegate only to a knowledgeable peer or app owner; never to a peer who will Approve All on your behalf. Document every delegation reason.

**Sample mail tone** (`lab-data/notifications/certification-sample.txt`): campaign name, scope, due date (10 business days), login path to Work Item Inbox. Production-style name in sample: `MNB-Q3-Manager-Cert-Treasury`.

### What “high-risk only” means in practice

Include: `WIRE_INIT`, `WIRE_APPR`, `SAP_FI`, `AWS_ADMIN` (and peers like `GL_POST` if your filter allows). Exclude: birthright `ELDAP`, broad CRM read, `GRP_ALL_STAFF`-style noise. If the UI cannot filter entitlements, shrink the *population* instead — never ship a thousand-line birthright campaign and call it Treasury high-risk.

### Meridian example — Rachel’s Treasury review

`rachel.evans` should see payment-relevant reports: Marcus with `WIRE_APPR`, and (if still under her after Lesson 30) Priya with `WIRE_INIT`. Approving both sides of dual control on *different* people is correct. Approving both on the *same* person is a finding — escalate to SoD (Lesson 39–41), do not “maintain with comment.”

If Priya already moved to Sanjay (Lesson 30), Rachel’s cert may shrink — that is correct hierarchy behavior, not a broken campaign. Document which reports you used.

The wrong way: certify every entitlement on every employee every quarter. Completion looks green; decision quality fails sampling.

---

## How it works

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
        │
        ▼
 Evidence pack: definition + completion % + sample decisions
```

| Campaign element | Meridian lab value |
| --- | --- |
| Name | `MNB-Q-Lab-Manager-Cert` |
| Type | Manager |
| Due date | ~10 business days |
| Scope | High-risk Wire / SAP / AWS |
| Example certifier | `rachel.evans` |
| Notification from | `identity-noreply@meridiannb.com` (sample) |

| Decision quality signal | Examiner interpretation |
| --- | --- |
| Approve + revoke mixed on high-risk scope | Thoughtful review |
| 100% approve, zero comments | Rubber-stamp risk (Lesson 46) |
| Delegate with reason to app owner | Acceptable when manager lacks system knowledge |
| Admin completes as manager | Lab-only; invalid in production |

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq`
- [ ] Manager hierarchy intact (`priya.wire` → `rachel.evans` from Lesson 21 — note Priya may now report to Sanjay after Lesson 30; use remaining Treasury reports or restore hierarchy for this lab)
- [ ] Wire / SAP / AWS apps correlated
- [ ] Copy of `~/iiq-lab-data/notifications/certification-sample.txt` open
- [ ] Risk weights from Lesson 42 optional but helpful for prioritization story

---

## Lab procedure

### Task 1 — Read the sample notification

Notifications start the SLA clock. If the email is vague, managers treat the cert as spam.

1. Open `lab-data/notifications/certification-sample.txt` (or `~/iiq-lab-data/notifications/...`).
2. Note: From `identity-noreply@meridiannb.com`, To `rachel.evans@meridiannb.com`, campaign `MNB-Q3-Manager-Cert-Treasury`, due in 10 business days, high-risk Wire/SAP/AWS scope.
3. Write three attributes your IIQ cert email must include: campaign name, due date, how to open the work item.

**Expected result:** Checklist of actionable email elements ready for Lesson 49 alignment.

### Task 4 — Define scope

Write the scope card before clicking Create — renaming after generation is painful.

1. Create or reuse population: managers’ reports under Treasury / payments, **or** filter identities with Wire/SAP/AWS entitlements whose manager is `rachel.evans`.
2. Entitlement inclusion: only critical payment/finance/cloud ents — exclude birthright `ELDAP` / CRM noise if the cert type allows entitlement filters.
3. Name campaign: `MNB-Q-Lab-Manager-Cert` (lab). Production-style name in sample is `MNB-Q3-Manager-Cert-Treasury`.
4. Write the exclusion list explicitly (what you will *not* certify) so Audit sees intentional scoping.

**Expected result:** Written scope: who + which apps/ents + campaign name + exclusion list.

**If it fails:** If entitlement filter UI is limited, certify a tiny population (≤15 identities) instead of filtering ents — still document intent.

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

Generation creates the work items. Empty inbox usually means “not generated” or wrong certifier.

1. **Generate** the certification (if separate from create).
2. Open **Work Item Inbox** as `rachel.evans` (or proxy/login as manager).
3. Open `MNB-Q-Lab-Manager-Cert` work item.
4. Spot-check line items: Priya wire init (if still under Rachel), Marcus approve, any SAP/AWS on reports.

**Expected result:** Manager sees a manageable list focused on high-risk access — not hundreds of ELDAP rows.

### Task 5 — Complete decisions

Thoughtful review means at least one revoke when residuals exist — zero revokes on high-risk scope is a rubber-stamp signal (Lesson 46).

1. **Approve** clearly job-appropriate access (e.g., Priya `WIRE_INIT` if still in Treasury wire role).
2. **Revoke** anything residual/wrong (e.g., AWS on a non-cloud report if present; leftover mover access).
3. Use **Delegate** once for practice if UI allows; note rule for when delegation is OK.
4. Sign off / complete the certification phase for this manager.
5. As admin, note campaign completion % and any open remediations.

**Expected result:** At least one approve and one revoke recorded; campaign progress advanced.

**If it fails:** If login-as is disabled, complete decisions from admin forward/certifier reassignment for lab only — and note that production forbids admin rubber-stamping.

### Task 6 — Compare notifications

1. Compare sample subject/body to IIQ’s default certification email template text (preview or Debug `EmailTemplate`).
2. List gaps: missing due date? missing scope? weak CTA?
3. Park improvements for Lesson 49.

**Expected result:** Gap list of 3+ items vs `certification-sample.txt`.

### Task 7 — Seed the certification evidence pack

Lesson 46 builds the full binder. Start the cover sheet now so Capstone is not a scramble.

1. Create folder `MNB-Exam-Binder-Certs/` (or note path in binder index).
2. Drop in: campaign definition screenshot, completion % note, approve+revoke screenshot, notification gap list.
3. Label the pack `L43-manager-seed` so later owner/micro-cert artifacts can join it.

**Expected result:** Seed evidence pack with four artifacts indexed.

---

## Acceptance criteria

- [ ] Campaign `MNB-Q-Lab-Manager-Cert` created and generated
- [ ] Scope limited to high-risk Wire/SAP/AWS (or tiny population with documented intent)
- [ ] Manager work item opened and decisions completed (approve + revoke)
- [ ] Sample email compared; gaps noted
- [ ] Completion % recorded for binder
- [ ] Evidence pack seeded for Lesson 46

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Empty cert | Population empty / no ents match | Broaden slightly; verify manager links |
| Thousand-line cert | No entitlement filter | Restrict ents or population; regenerate |
| Manager inbox empty | Wrong certifier / not generated | Generate; check certifier = manager |
| Cannot decide | Phase locked / already signed | Use admin forward or new campaign |
| Email never sends | SMTP off in lab | Expected; use sample + work item proof |
| Priya missing after mover | Manager now Sanjay | Expected; certify remaining Treasury reports or restore hierarchy for lab |

---

## Training binder evidence

- Screenshot: campaign definition (name, due date, scope)
- Screenshot: manager work item with one approve + one revoke
- Completion % note
- Annotated copy of `certification-sample.txt` with gaps vs IIQ defaults
- Path note for `MNB-Exam-Binder-Certs/L43-manager-seed`

---

## Knowledge check

1. Why keep manager cert scopes tight?
2. Name four decision types commonly available.
3. Who receives the sample Treasury cert email?
4. What three apps/entitlement domains are in lab scope?
5. What happens after revoke? (preview Lesson 46)
6. What is the sizing rule of thumb for manager review time?

### Answers

1. Prevents rubber-stamping; improves decision quality for examiners.
2. Approve/maintain, revoke, delegate, exception/allow (wording varies).
3. `rachel.evans@meridiannb.com` (Payments Operations Manager).
4. Wire Portal, SAP Finance, AWS Admin (high-risk).
5. Remediation / provisioning must complete — cert “done” is incomplete until revokes close.
6. About 30–45 minutes of focused review; longer means overscoped.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “manager certification” and “certification campaign.”
- [SailPoint Community](https://community.sailpoint.com/) — search “certification best practices” for scoping and rubber-stamp prevention.
- [NIST SP 800-53 AC-2 / AC-6](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) — periodic review of accounts and privileges.
- [FFIEC Information Technology Examination Handbook](https://ithandbook.ffiec.gov/) — search access review / user access administration expectations.
- [ISACA — Access Certification / SOX ITGC primers](https://www.isaca.org/) — search “access certification” for evidence examiners sample.

---

## Stretch lab

Enable lab email if SMTP is available; capture one generated message and store beside `certification-sample.txt`. Or add a 48-hour reminder template note for overdue managers. Advanced: draft a population that excludes birthright `ELDAP` even when entitlement filters are weak — document the exclusion logic for Internal Audit.

---

## Summary

- Manager certs attest people-context; scope them to high-risk access.
- Generate, decide, measure completion — then chase remediations.
- Notifications must be as clear as Meridian’s sample mail.
- Seed the evidence pack early so Lesson 46 is assembly, not archaeology.

---

**Previous:** [Lesson 42 — Risk Scores](42-risk-scores.md)  
**Next:** [Lesson 44 — Application Owner Certifications](44-app-owner-certifications.md)
