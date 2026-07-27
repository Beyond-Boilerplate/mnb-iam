# Lesson 48 — Audit-Ready Reporting & Dashboards

**Level:** Intermediate  
**Track:** Ops  
**Time:** 60–90  
**Prereq:** Lesson 47 — Provisioning Troubleshooting  

**Lab data:** `apps/MNB-AWS-Cloud.csv`, `reference/sod-matrix.csv`, certification campaigns from Lessons 43–45, leaver scenarios

---

## Learning objectives

You will be able to:

- Run four Meridian assurance searches/reports: AWS holders, open SoD, cert status, terminated-with-access
- Name evidence artifacts with **date stamps** (`MNB-*-YYYY-MM-DD`)
- Schedule at least one report to a human who acts (Risk / helen.ross)
- Map each report to a control statement ID (lab fiction `CTL-IAM-*`)
- Explain why undated exports fail evidence hygiene

---

## Why this matters

If you cannot show it, examiners assume it does not exist. Reports turn live controls into durable evidence for SOX, banking exams, and internal audit.

Date-stamped names prevent “which version did we send?” chaos. Scheduled delivery to humans who act beats dumping CSV into a shared mailbox nobody reads.

---

## Concepts

Meridian’s **assurance pack** (minimum):

| Report | Question answered | Control ID (lab) |
| --- | --- | --- |
| AWS holders | Who has cloud admin? | `CTL-IAM-12` |
| Open SoD violations | Which toxic pairs remain? | `CTL-IAM-21` |
| Cert completion / status | Are reviews on time? | `CTL-IAM-30` |
| Terminated-with-access | Did leavers retain ents? | `CTL-IAM-08` |

```
Advanced Analytics / Reports / Populations
        │
        ▼
 Export / save as MNB-<topic>-YYYY-MM-DD
        │
        ├── Ad-hoc exam request
        └── Scheduled mail → Risk owner
```

**Naming rule:** Always include ISO date. Example: `MNB-AWS-Holders-2026-07-26`.

**Delivery hygiene**

| Do | Don’t |
| --- | --- |
| Store exports under access-controlled assurance folders | Leave PII CSVs on shared desktops |
| Send to named Risk + IAM owners | Only “iam-reports@” with no human RACI |
| Keep prior month’s packs for trend | Overwrite last export in place |
| Note row counts on a cover sheet | Assume “attached” without totals |

**Exam question to rehearse:** “Show me who had AWS admin last Friday and whether any terminated identity still holds it.” Your dated packs should answer in under five minutes.

---

## Before you start

- [ ] IIQ reporting / Advanced Analytics available
- [ ] SoD policies and cert campaigns from prior lessons present
- [ ] Know Risk distribution: e.g., Risk team + `helen.ross@meridiannb.com`
- [ ] Folder for exports: `MNB-Assurance-Pack/`

---

## Lab procedure

### Task 1 — AWS holders report

1. Advanced search / Entitlement search / Report: identities with `AWS_ADMIN` on `MNB-AWS-Cloud`.
2. Include: identity name, email, manager, worker type, account status.
3. Export or save result.
4. Name: `MNB-AWS-Holders-YYYY-MM-DD`.
5. Spot-check: `raj.external`, any residual `jordan.reed`.

**Expected result:** Dated AWS holders extract in assurance folder.

**If it fails:** Use Application account list export annotated manually; still date-stamp the filename.

### Task 2 — Open SoD violations

1. Policy Violations view or Compliance report filtered to `MNB-SOD-*` and status Open (include Mitigated as a second tab if useful).
2. Export.
3. Name: `MNB-SoD-Open-YYYY-MM-DD`.
4. Record count on KPI cover sheet.

**Expected result:** Dated open SoD extract; count matches Lesson 41 KPI within reason.

### Task 3 — Certification status

1. Open certifications list / certification report for `MNB-Q-Lab-Manager-Cert` (and micro-cert if run).
2. Capture completion %, due date, open remediations.
3. Name: `MNB-Cert-Status-YYYY-MM-DD`.

**Expected result:** One status sheet covering latest manager (and optional owner/micro) campaigns.

### Task 4 — Terminated-with-access

1. Search inactive/terminated identities that still have entitlements or accounts.
2. Include Jordan leaver residuals if present.
3. Name: `MNB-Terminated-With-Access-YYYY-MM-DD`.
4. If zero rows: document “clean as of DATE” as positive evidence—still save the empty-result proof.

**Expected result:** Dated hunt result (rows or clean attestation).

### Task 5 — Control map + schedule

1. Map the four reports to `CTL-IAM-12`, `CTL-IAM-21`, `CTL-IAM-30`, `CTL-IAM-08` in a table.
2. Schedule **one** report (weekly SoD open recommended) to a named human inbox.
3. Note: schedules to shared mailboxes require a named secondary owner.

**Expected result:** Control map table + schedule definition screenshot/name.

### Task 6 — Cover sheet

1. Create `MNB-Assurance-Cover-YYYY-MM-DD` with: report names, row counts, generator (your name), IIQ environment, anomalies (e.g., unexpected AWS holders).
2. Flag any row that requires immediate revoke (terminated + AWS, dual wire, etc.).
3. File the cover sheet as page 1 of the assurance pack PDF/folder.

**Expected result:** One-page cover sheet sitting on top of the four extracts.

---

## Acceptance criteria

- [ ] Four assurance artifacts produced with date-stamped names
- [ ] Control ID map completed
- [ ] One report scheduled to an acting human
- [ ] Cover sheet lists counts for AWS holders and open SoD
- [ ] Empty terminated-with-access still archived as clean proof if applicable
- [ ] Anomalies requiring immediate revoke flagged on the cover sheet

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Report empty incorrectly | Wrong filter / inactive policy | Validate with known persona (raj/jordan) |
| Undated filenames | Habit | Rename before binder insert |
| Schedule never fires | Task not enabled | Check Task schedule / quartz |
| PII sprawl in exports | Over-broad columns | Minimize attributes; protect folder ACLs |
| Cert % disagrees with UI | Different campaign selected | Match exact campaign name |

---

## Training binder evidence

- Four dated report files (or screenshots)  
- Control map table  
- Schedule definition  
- Assurance pack cover sheet with counts  

---

## Knowledge check

1. Name three assurance reports Meridian expects weekly/quarterly.
2. Why date-stamp report names?
3. Who should receive weekly SoD mail?
4. What control does terminated-with-access support?
5. Is an empty terminated-with-access result useless?

### Answers

1. Any three of: AWS holders, open SoD, cert status, terminated-with-access.  
2. Evidence hygiene—know which extract was provided when.  
3. A named Risk owner (and IAM lead such as helen.ross)—not only a silent DL.  
4. Leaver / orphan access control (`CTL-IAM-08` in lab map).  
5. No—dated clean results are positive evidence.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “advanced analytics” / “report” / “certification campaign reports.”
- [NIST SP 800-53 AU-6 / AU-7](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) — audit review and report generation.
- [FFIEC IT Handbook — Information Security](https://ithandbook.ffiec.gov/it-booklets/information-security/) — evidence packs examiners expect.

## Stretch lab

Draft a monthly IAM metrics email outline: SoD open trend, cert on-time %, AWS holder count, terminated-with-access count, top risk identities (Lesson 42).

---

## Summary

- Four core reports form Meridian’s assurance pack.
- Date-stamp everything; schedule to humans who act.
- Map reports to control IDs before exam week.

---

**Previous:** [Lesson 47 — Provisioning Troubleshooting](47-provisioning-troubleshooting.md)  
**Next:** [Lesson 49 — Email Templates & Notifications](49-email-templates-notifications.md)

