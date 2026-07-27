# Lesson 49 — Email Templates & Notifications

**Level:** Intermediate  
**Track:** Ops  
**Time:** 45–60  
**Prereq:** Lesson 48 — Audit-Ready Reporting  

**Lab data:** `notifications/certification-sample.txt`, `lab-data/email.txt`

---

## Learning objectives

You will be able to:

- Compare Meridian’s sample certification mail to IdentityIQ **EmailTemplate** objects
- Identify the certification (and related) templates used for manager campaigns
- Rewrite subject/body for actionable clarity: campaign, scope, due date, CTA
- Document recipient logic (manager vs app owner vs requester)
- List noise-control rules so notifications drive SLAs instead of training users to ignore mail

---

## Why this matters

Notifications start the human SLA clock. Vague emails get ignored; clear ones get certifications done on time. Examiners may ask how reviewers were notified and whether reminders existed.

Trusted From-addresses on `@meridiannb.com` matter in production. Lab SMTP may be off—you still align templates so go-live copy is ready.

---

## Concepts

IdentityIQ stores mail content as **EmailTemplate** objects (Debug / gear menu → Business Processes / Email Templates, or equivalent). Common families:

| Template family | Typical recipient | Meridian use |
| --- | --- | --- |
| Certification open / reminder | Manager or app owner | Quarterly & micro-certs |
| Work item / approval | Approver chain | LCM requests (Lessons 35–36) |
| Policy violation | Compliance / Risk / manager | SoD hits (Lesson 41) |
| Lifecycle | Manager / employee | Joiner/leaver notices |

**Actionable cert mail checklist** (from `certification-sample.txt`):

```
From: identity-noreply@meridiannb.com
To: rachel.evans@meridiannb.com
Subject: Action required — <Campaign> (<Org slice>)

Body must include:
  - Campaign name
  - Scope (apps / risk focus)
  - Due date
  - Exact CTA: Login → Work Item Inbox → open certification
  - Sender office (Identity Governance Office)
```

**Noise rules:** Do not email on every trivial attribute update; batch reminders; escalate overdue only to managers + their manager; never BCC the entire bank.

**Subject line patterns that work**

| Event | Subject pattern |
| --- | --- |
| Cert open | `Action required — {Campaign} ({Org})` |
| Cert reminder | `Reminder — {Campaign} due {Date}` |
| Cert overdue | `Overdue — {Campaign} — escalate` |
| SoD open | `Policy violation — {Policy} — {Identity}` |
| Break-glass | `Alert — PRIV_BREAK granted — {Identity}` |

Avoid subjects like “IdentityIQ notification” or “You have a work item” with no campaign or due date.

---

## Before you start

- [ ] Read `~/iiq-lab-data/notifications/certification-sample.txt` end-to-end
- [ ] IIQ Debug access to browse `EmailTemplate` objects
- [ ] Lesson 43 gap list (if you created one) available
- [ ] Note whether lab SMTP is enabled (optional for send test)

---

## Lab procedure

### Task 1 — Study the Meridian sample

1. Open `lab-data/notifications/certification-sample.txt`.
2. Highlight: subject urgency (“Action required”), campaign name `MNB-Q3-Manager-Cert-Treasury`, scope line, 10-business-day due, CTA path.
3. Score the sample against the actionable checklist (all boxes should pass).

**Expected result:** Annotated sample with checklist ticks.

### Task 2 — Locate EmailTemplate objects

1. Open **Debug** → select object type **EmailTemplate** (or navigate UI Email Templates admin).
2. Search/filter for names containing `Cert` / `Certification` / `WorkItem`.
3. Open 1–2 templates; note subject and body variables (e.g., `$certification.name`, due date vars—exact tokens vary by version).
4. Record template names used for certification notifications in your lab.

**Expected result:** Table: Template name → purpose → recipient intent.

**If it fails:** Export list of EmailTemplate names from Debug search; still map which one Lesson 43 campaign referenced in its notification config.

### Task 3 — Align copy with the sample

1. Draft improved subject: `Action required — MNB-Q-Lab-Manager-Cert (Treasury high-risk)`  
2. Draft body paragraphs mirroring the sample (campaign, scope Wire/SAP/AWS, due date, CTA).
3. Either update the lab EmailTemplate (if permitted) **or** paste the proposed copy into binder as `MNB-EmailTemplate-Cert-Proposed.txt`.
4. Ensure From identity is a trusted noreply style address for production notes.

**Expected result:** Side-by-side: stock IIQ text vs Meridian-aligned proposed text.

### Task 4 — Recipient logic matrix

Fill:

| Event | Primary To | CC / escalate | Never |
| --- | --- | --- | --- |
| Manager cert open | Manager | — | Entire dept DL |
| App owner cert | App owner | Backup owner | spadmin only |
| Approval needed | Approver | Requester (optional status) | Unrelated executives |
| SoD violation | Risk + IAM queue | Manager | Public channels |
| Cert overdue reminder | Certifier | Certifier’s manager | All managers bank-wide |

**Expected result:** Recipient matrix in binder.

### Task 5 — Noise control review

1. List events that should **not** email (example: successful birthright ELDAP add).
2. List events that must email (cert open, cert overdue, policy violation open, break-glass grant).
3. Write one anti-pattern: “daily digest of every entitlement detect.”

**Expected result:** Noise do/don’t list signed for Capstone go-live.

---

## Acceptance criteria

- [ ] Sample mail checklist applied
- [ ] EmailTemplate objects located and named in notes
- [ ] Proposed Meridian-aligned cert subject/body produced
- [ ] Recipient matrix completed
- [ ] Noise-control do/don’t list written

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No mail in lab | SMTP disabled | Expected; use templates + sample as evidence |
| Variables render blank | Wrong token / null data | Test with known campaign; check null-safe text |
| Wrong recipient | Certifier rule mismatch | Fix campaign certifier config first |
| Users ignore mail | Weak subject / no due date | Adopt sample pattern |
| From spoof fears | Non-bank domain | Document production From on meridiannb.com |

---

## Training binder evidence

- Annotated `certification-sample.txt`  
- List of EmailTemplate names touched  
- Proposed cert email copy  
- Recipient matrix + noise rules  

---

## Knowledge check

1. What makes a cert email actionable?
2. Where are templates stored in IIQ?
3. What is the noise risk?
4. Who is the To: on Meridian’s Treasury sample?
5. Should every entitlement change send mail?

### Answers

1. Clear subject, campaign name, scope, due date, and explicit Work Item CTA.  
2. As `EmailTemplate` objects (Debug/UI admin).  
3. Over-mailing trains users to ignore governance messages—SLA collapse.  
4. `rachel.evans@meridiannb.com`.  
5. No—reserve mail for decisions, violations, and lifecycle events that need humans.

---

## Stretch lab

Draft a **leaver notification to manager** template: identity, termination date, residual high-risk ents count, link to rapid offboard runbook (Lesson 34). Save as `MNB-EmailTemplate-Leaver-Manager-Proposed.txt`.

---

## Summary

- Meridian’s sample mail is the gold standard for cert notifications.
- EmailTemplate objects must carry campaign, due date, and CTA—not vague prose.
- Recipient and noise discipline protect the SLA.

---

**Previous:** [Lesson 48 — Audit-Ready Reporting](48-audit-ready-reporting.md)  
**Next:** [Lesson 50 — Capstone Exam Readiness](50-capstone-exam-readiness.md)
