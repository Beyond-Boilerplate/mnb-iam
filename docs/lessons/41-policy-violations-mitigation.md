# Lesson 41 — Policy Violations & Mitigation

**Level:** Intermediate  
**Track:** Policies  
**Time:** 60–75  
**Prereq:** Lesson 40 — Payment Dual-Control Policy  

**Lab data:** `reference/sod-matrix.csv`, `apps/MNB-SAP-Finance.csv`, `apps/MNB-AWS-Cloud.csv`

---

## Learning objectives

You will be able to:

- Open and filter Meridian SoD policy violations (`MNB-SOD-*`) in IdentityIQ
- Execute a **revoke** path that clears a finance-cloud violation for `jordan.reed`
- Execute a **mitigate** path with compensating control text and a hard expiry date
- Distinguish IAM tooling ownership from Risk acceptance of residual risk
- Produce open / mitigated / closed violation counts suitable for a Risk KPI pack
- Answer the examiner question on last finance-cloud hit, acceptor, and expiry

---

## Why this matters

**Business.** Open policy violations without owners rot into silent acceptance. When `jordan.reed` holds `SAP_FI` and `AWS_ADMIN`, every day without a revoke or time-boxed mitigation is an accepted fraud/evidence-destruction window — whether anyone said so out loud or not.

**Control / audit.** Examiners treat “we saw it and did nothing” as a control failure equal to never detecting the toxic pair. Mitigation is how Risk **consciously** accepts residual risk for a bounded period. Revoke is the default. Eternal mitigations without expiry are fake compliance and fail sampling. Control split: Risk owns acceptance; IAM owns tooling, SLA clocks, and evidence packs.

---

## Concepts

### What a policy violation is

A **policy violation** is an IdentityIQ work item (or violation record) raised when an identity holds a prohibited entitlement/role pair defined by a policy such as `MNB-SOD-Finance-Cloud` (`SAP_FI` + `AWS_ADMIN`).

Persona under test: `jordan.reed` (`MNB00092`) — the finance-cloud toxic pair from `sod-matrix.csv`. Wire dual-control (`WIRE_INIT`/`WIRE_APPR`) should remain clean on Priya/Marcus unless Lesson 40 induction was left unrestored.

### Meridian example — Jordan’s finance-cloud hit

Jordan is a Staff Accountant (`FIN` / `GL01`) under `deepa.nair`. He needs `SAP_FI` (and often `GL_POST`) to do the job. He does **not** need `AWS_ADMIN`. The toxic combination is not “finance access is bad” — it is finance *plus* infrastructure escape hatch. That is why Meridian’s revoke default for this persona is: remove cloud admin, keep SAP, re-check the policy.

Contrast: if a cloud platform engineer somehow held `SAP_FI`, Risk might prefer revoking the finance side instead. Always ask *which side is least disruptive to the legitimate job* — then document the choice.

Digital stretch: `kai.nguyen` with `IBSI`+`ECOM` (if you built `MNB-SOD-Digital-Channel` in Lesson 39 stretch) follows the same revoke/mitigate discipline — different pair, same ownership rules.

### Decision table

| Decision | Meaning | Who owns it | Evidence required |
| --- | --- | --- | --- |
| **Revoke** | Remove one side of the toxic pair | IAM executes; business confirms which side | Provisioning plan / account change |
| **Mitigate** | Keep access temporarily | **Risk** accepts residual risk | Compensating control + expiry + approver |
| **Ignore / dismiss** | Not used at Meridian for SoD | — | Forbidden for payment/finance SoD |

### Meridian SLA sketch

| Stage | SLA |
| --- | --- |
| Open critical SoD → IAM triage | ≤ 1 business day |
| Risk decision mitigate vs revoke | ≤ 3 business days |
| Expired mitigations | Re-open to IAM queue on next refresh after expiry |

**Examiner trap:** “Mitigated indefinitely pending project” with no end date. Treat blank expiry as a finding against IAM and Risk jointly.

### Compensating controls that Risk will accept

Vague comments fail sampling. Prefer concrete compensation:

- Daily manager review of GL posts vs cloud change tickets (Jordan finance-cloud mitigate)
- Dual manual wire review log with reduced limits (wire SoD mitigate — Lesson 40)
- Named secondary reviewer + ticket ID + calendar expiry reminder

“Monitoring” alone is not a compensating control unless you say *who monitors, what artifact, how often*.

The wrong way: IAM clicks Mitigate in the UI with a comment “ok for now” and no Risk name — that is IAM accepting residual risk alone.

---

## How it works

```
Detect (Refresh + policy check)
        │
        ▼
   Violation open ──► IAM triages
        │
        ├── Revoke preferred ──► provision remove ──► re-check clear
        │     (Jordan default: revoke AWS_ADMIN; keep SAP_FI)
        │
        └── Mitigate (Risk) ──► expiry + compensation ──► calendar reminder
                                      │
                                      └── on expiry: re-open or force revoke
```

| KPI | Definition | Why Risk wants it |
| --- | --- | --- |
| Open | Unresolved violations | Active residual risk |
| Mitigated | Accepted with expiry | Conscious, time-boxed exceptions |
| Closed / remediated | Cleared after revoke | Control effectiveness |

| Actor | Owns | Does not own |
| --- | --- | --- |
| IAM Ops | Detection, routing, revoke execution, SLA clocks, evidence packs | Residual risk acceptance |
| Risk / CRO org | Accept mitigate, max exception life, sample mitigations | Day-to-day connector fixes |
| Business manager | Confirm which side to revoke; run compensating reviews | Policy object design |
| Payments (`rachel.evans`) | Wire SoD exception signoff (Lesson 40) | Finance-cloud acceptance alone |

Name the KPI file `MNB-SoD-KPI-YYYY-MM-DD` so weekly Risk packs sort cleanly in the binder.

---

## Before you start

- [ ] IIQ reachable at `http://localhost:8080/identityiq` (homelab URL alternate if used)
- [ ] Logged in as `spadmin` (and a Risk persona or proxy if your lab supports it)
- [ ] Policies `MNB-SOD-Wire-DualControl` and `MNB-SOD-Finance-Cloud` exist from Lessons 39–40
- [ ] Identity refresh with policy checking has been run recently
- [ ] Lab files under `~/iiq-lab-data/` include apps and `reference/sod-matrix.csv`
- [ ] Note: do not leave induced or open lab violations uncleared in shared environments

---

## Lab procedure

### Task 1 — Inventory open violations

KPI packs start with a dated count — not a feeling that “things look quiet.”

1. Open **Policy Violations** (or equivalent: Compliance / Policy → Violations).
2. Filter or search for policies named `MNB-SOD-*`.
3. Record counts: open, mitigated, closed (or remediated).
4. Confirm `jordan.reed` appears on `MNB-SOD-Finance-Cloud` (or recreate by restoring `SAP_FI` + `AWS_ADMIN` and running **Refresh MNB Identities** with policy checking).

**Expected result:** At least one open finance-cloud violation on `jordan.reed`. KPI sheet started with three numbers.

**If it fails:** Re-aggregate `MNB-SAP-Finance` and `MNB-AWS-Cloud`, then refresh with “check policies” (or equivalent) enabled.

### Task 2 — Revoke path (preferred)

Staff accountants need finance access; they do not need cloud admin. Meridian default: revoke the cloud side.

1. Decide which side to remove. Meridian default for staff accountants: **revoke AWS_ADMIN**; keep `SAP_FI` for GL work.
2. From the violation (or identity cube → accounts/entitlements), remove `AWS_ADMIN` from `jordan.reed` on `MNB-AWS-Cloud` via LCM request, certification remediation, or direct entitlement removal per your lab pattern.
3. Run **Account Aggregation** for `MNB-AWS-Cloud` if the connector is file-based and you edited the CSV, then **Refresh MNB Identities** with policy checking.
4. Re-open the violation list for `jordan.reed`.

**Expected result:** Finance-cloud violation clears (closed/remediated). Cube no longer shows `AWS_ADMIN`.

**If it fails:** Confirm the entitlement native identity still matches the CSV; check the provisioning plan completed (Lesson 47 deep-dive).

### Task 3 — Mitigate path with expiry (second violation or restore)

Practice mitigation on a throwaway identity when possible — do not re-break Jordan if Task 2 already produced clean revoke evidence.

1. Safely recreate a lab violation (e.g., temporary dual wire ents on a throwaway identity, or restore `AWS_ADMIN` on a non-production test cube). Prefer a **throwaway** identity over re-breaking jordan if you already closed Task 2 for evidence.
2. Open the violation → choose **Mitigate** (or equivalent allow/exception action).
3. Set expiry to **14 days** (lab max; Meridian production wire/finance exceptions typically ≤ 30 days with Rachel Evans / Risk sign-off).
4. Comment must include: compensating control (e.g., “daily GL vs cloud change review by manager”), Risk approver name, ticket ID.
5. Save. Confirm status shows mitigated with end date.

**Expected result:** Violation status = mitigated; expiry date visible; comment names Risk owner.

**If it fails:** Some IIQ versions require a mitigation workflow or work item — complete that work item as Risk proxy.

### Task 4 — Ownership & KPI pack

Write the ownership split in language you would say to Internal Audit.

1. Write in your notebook:
   - IAM: detects, routes, remediates tooling, tracks SLA
   - Risk: accepts residual risk, sets max exception life, samples mitigations
2. Update KPI: open / mitigated / closed after Tasks 2–3.
3. Confirm no eternal mitigations (expiry blank or far-future) remain from this lab.

**Expected result:** One-page KPI note with ownership split and dated counts.

### Task 5 — Examiner question drill

Answer aloud (or in binder):

> “Show me your last finance-cloud SoD hit, who accepted residual risk, and when the exception expires.”

Point to jordan revoke evidence **or** the mitigated exception with Risk name + date.

**Expected result:** You can answer in under two minutes with UI proof.

### Task 6 — Expiry calendar hygiene

Expired mitigations that nobody watches become standing exceptions. Close the loop on paper even if your lab lacks automated re-open.

1. List every mitigated `MNB-SOD-*` item from this lab with expiry date and owner.
2. Add a calendar reminder (or binder “watch list”) for the day after expiry.
3. Write the reopen rule: next **Refresh MNB Identities** with policy checking should surface expired items to IAM; if your build does not auto-reopen, open a manual work item.

**Expected result:** Watch list with at least one dated expiry and a reopen action named.

---

## Acceptance criteria

- [ ] Open `MNB-SOD-*` violations inventoried with counts
- [ ] Revoke path demonstrated; finance-cloud clears for the revoke subject
- [ ] Mitigate path demonstrated with ≤14-day (lab) expiry and compensating control text
- [ ] Written statement: Risk owns acceptance; IAM owns tooling
- [ ] No blank-expiry mitigations left from this exercise
- [ ] KPI pack dated for training binder
- [ ] Expiry watch list / reopen rule documented

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No violations after refresh | Policy check not enabled / policy inactive | Enable policy on refresh task; activate policy |
| Violation survives revoke | Aggregation not run; wrong entitlement removed | Re-aggregate app; verify cube ents |
| Mitigate button missing | Rights / workflow not assigned | Use spadmin or assign Compliance officer capability |
| Mitigated but still “open” in report | Report filters exclude mitigated | Adjust report status filter; document both |
| Shared lab pollution | Prior student left toxic access | Clear jordan AWS_ADMIN; document wipe |
| Expired mitigate still “accepted” in KPI | Watch list missing | Re-open; force revoke or renew with Risk |

---

## Training binder evidence

- Screenshot: open violation on `jordan.reed` before action
- Screenshot: cleared violation after revoke **or** mitigated with expiry visible
- Note: compensating control text + Risk approver + ticket ID
- KPI table: open / mitigated / closed with date stamp `MNB-SoD-KPI-YYYY-MM-DD`
- Expiry watch list with reopen rule
- One sentence answering the examiner question above

---

## Knowledge check

1. Who accepts residual risk for an SoD mitigation at Meridian?
2. Why must mitigations have expirations?
3. Preferred first response to a finance-cloud hit on a staff accountant?
4. What does IAM own vs Risk?
5. What belongs in a mitigation comment?
6. What happens when a mitigation expires?

### Answers

1. **Risk** (not IAM alone).
2. Without expiry, exceptions become permanent shadow policy.
3. **Revoke** `AWS_ADMIN` (or the cloud side); keep required finance access.
4. IAM: tooling, detection, remediation execution, evidence; Risk: acceptance and exception policy.
5. Compensating control, approver, ticket ID, and expiry rationale.
6. Violation re-opens to the IAM queue (next refresh) for revoke or renewed Risk decision.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “policy violation” and “mitigation.”
- [SailPoint Community](https://community.sailpoint.com/) — search “SOD mitigation expiry” for operational patterns.
- [ISACA — SOX / ITGC and exception management primers](https://www.isaca.org/) — search “IT general controls” and “exception management” for Risk acceptance evidence.
- [NIST SP 800-53 AC-5 / CA-7](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) — separation of duties and continuous monitoring of control exceptions.
- [FFIEC Information Technology Examination Handbook](https://ithandbook.ffiec.gov/) — search audit and access-control exception handling expectations.

---

## Stretch lab

Schedule or draft a weekly report of open + mitigated `MNB-SOD-*` violations emailed to Risk. Include columns: identity, policy, status, expiry, owner. Name it `MNB-SoD-Open-Weekly-YYYY-MM-DD`. Optionally add a second sheet for `kai.nguyen` digital SoD if `MNB-SOD-Digital-Channel` exists, so Risk sees payment and digital channels in one pack.

---

## Summary

- Violations are actionable work, not wallpaper.
- Revoke is default; mitigate is time-boxed Risk acceptance with compensation.
- KPI hygiene (open / mitigated / closed) is examiner-grade evidence.
- Expiry watch lists prevent mitigations from becoming standing exceptions.

---

**Previous:** [Lesson 40 — Payment Dual-Control Policy](40-payment-dual-control-policy.md)  
**Next:** [Lesson 42 — Risk Scores](42-risk-scores.md)
