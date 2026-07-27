# Lesson 50 — Capstone: Exam Readiness & Go-Live Checklist

**Level:** Advanced  
**Track:** Capstone  
**Time:** 90–120  
**Prereq:** Lesson 49 — Email Templates & Notifications (full curriculum 01–49 recommended)

**Lab data:** Full Meridian pack under `~/iiq-lab-data/` — HR, `apps/MNB-*.csv`, `reference/*`, `scenarios/*`, `notifications/certification-sample.txt`

---

## Learning objectives

You will be able to:

- Execute a full **aggregation + refresh pipeline** and save task evidence
- Demonstrate one **clean SoD case** and one **violated / remediated** case
- Present **certification completion** evidence including a traced revoke
- Present **JML** evidence: joiner (`nina.joiner`), mover (`priya.wire`), leaver packet
- Publish a **printable go-live checklist**, residual risk register, and retro of top gaps before real bank production

---

## Why this matters

Go-live is a control statement, not a feeling. Meridian’s Identity Governance Office must prove—under exam pressure—that IdentityIQ closes the loop from HR truth to roles, requests, policies, certifications, provisioning, and reports.

This capstone is your dress rehearsal for internal audit week. Residual risk honesty beats greenwashed checklists; examiners punish “unknown unknowns” harder than documented accepted risks with owners and dates.

---

## Concepts

**Closed-loop governance** at Meridian:

```
HR authoritative ──► Correlate accounts ──► Roles / birthright
        │                                      │
        │                                      ▼
        │                              Requests + approvals
        │                                      │
        ▼                                      ▼
   Policies / SoD ◄──────────────────── Provisioning plans
        │                                      │
        ▼                                      ▼
   Certifications ──► Remediation ──► Reports / evidence pack
```

| Demo pillar | Minimum proof |
| --- | --- |
| Pipeline | HR + apps aggregated; Refresh MNB Identities succeeded |
| SoD | Priya/Marcus clean split; finance-cloud case documented |
| Certs | Manager or owner campaign with revoke traced |
| JML | Nina joiner + Priya mover + leaver/residual packet |
| Ops | Assurance reports dated; email templates reviewed |
| Governance | Checklist + residual risks + retro |

---

## How it works

The capstone is a **closed-loop demo**: prove the Meridian control chain end-to-end under timebox, then file a go-live checklist with residual risks. Examiners care about attributable evidence—not that every Stretch lab was finished.

```text
Pipeline (HR→apps→refresh)
        │
        ├── Correlation / roles / requests
        ├── SoD + violations + risk
        ├── Certs → remediation → reports
        └── Binder index + go-live checklist
```

| Demo pillar | Minimum proof |
| --- | --- |
| Pipeline | Named aggregates + refresh Success |
| SoD | Clean wire split + documented finance-cloud case |
| Certs | Campaign with revoke traced |
| JML | Joiner/mover/leaver evidence packet |
| Assurance | Dated reports + templates reviewed |

**Real-life Meridian example.** Walk `priya.wire` / `marcus.approve` dual control, then `jordan.reed` SoD case, then one cert revoke with TaskResult—three artifacts beat twenty unfinished half-demos.

## Before you start

- [ ] IIQ at `http://localhost:8080/identityiq` (or homelab URL) healthy: `/identityiq` login works
- [ ] Lab data copied to `~/iiq-lab-data/` per [README](README.md)
- [ ] Objects from prior lessons present (apps, roles, policies, populations, certs)—rebuild critical gaps before demos if missing
- [ ] Binder folders: pipeline, SoD, certs, JML, assurance, go-live
- [ ] Timebox: treat this as a mock exam—work from checklist, not memory alone
- [ ] Printer or PDF export ready for the go-live checklist section

---

## Lab procedure

### Task 1 — Full pipeline run

A closed-loop demo starts with a green pipeline—prove aggregates and refresh before SoD and cert showpieces.

1. Confirm HR application authoritative; run **Account Aggregation** (or HR aggregation task) for Meridian HR.
2. Run **Account Aggregation** for critical apps: at minimum `MNB-ActiveDirectory`, `MNB-WirePortal` (or initiator/approver extracts), `MNB-SAP-Finance`, `MNB-AWS-Cloud`, `MNB-CoreBanking`.
3. Run **Refresh MNB Identities** with correlation, manager, role, and policy-checking options appropriate to your build.
4. Save Task Result screenshots/exports named `MNB-Pipeline-HR-YYYY-MM-DD`, `MNB-Pipeline-Apps-YYYY-MM-DD`, `MNB-Pipeline-Refresh-YYYY-MM-DD`.
5. Spot-check cubes: `helen.ross`, `rachel.evans`, `priya.wire`, `marcus.approve`, `jordan.reed`, `raj.external`, `nina.joiner` (if joined).

**Expected result:** All pipeline tasks Success (or documented known warnings); spot-check table initialed.

**If it fails:** Stop demos; fix aggregation/refresh first—capstone evidence on a broken cube is worthless.

### Task 2 — SoD demonstration

1. **Clean case:** Open `priya.wire` and `marcus.approve`. Confirm wire dual-control split: initiator vs approver—not both on one cube. Screenshot.
2. **Violation / remediation case:** Show `MNB-SOD-Finance-Cloud` history for `jordan.reed` (or current holder): open → revoke AWS_ADMIN **or** mitigated with expiry + Risk owner. Use Lesson 41 evidence if still valid; re-run refresh if needed.
3. Optional: note digital dual (`IBSI`+`ECOM`) if present on a persona.
4. Export `MNB-SoD-Open-YYYY-MM-DD` (Lesson 48).

**Expected result:** Side-by-side clean vs handled-toxic story in binder (two screenshots + one paragraph narrative).

### Task 3 — Certification demonstration

1. Open latest `MNB-Q-Lab-Manager-Cert` or owner/micro-cert.
2. Show definition: name, scope, due date, completion %.
3. Show one **Approve** with business rationale and one **Revoke** traced to provisioning/cube (Lesson 46).
4. Attach QA note: no rubber-stamp signals on the sampled rows.
5. Attach notification alignment note vs `certification-sample.txt` (Lesson 49).

**Expected result:** Cert demo packet: definition + decisions + revoke trace + completion %.

**If it fails:** Launch a tiny emergency micro-cert (Lesson 45 pattern) and complete two decisions before continuing—do not skip this pillar.

### Task 4 — JML demonstration

1. **Joiner:** Evidence for `nina.joiner` (or latest joiner): HR row present, identity cube created, birthright/AD access as designed (Lesson 29).
2. **Mover:** Evidence for `priya.wire` transfer scenario (Lesson 30): department/manager change reflected; stale Treasury vs new access story documented.
3. **Leaver:** Packet for terminated/residual path (Lesson 31/34): HR inactive, accounts disabled or residual hunt result `MNB-Terminated-With-Access-YYYY-MM-DD`.
4. One paragraph: SLA targets Meridian uses for join / move / leave (from earlier lessons—state your lab’s targets).

**Expected result:** Three-tab JML evidence with dated filenames.

### Task 5 — Assurance pack refresh

1. Re-run or refresh the four reports: AWS holders, open SoD, cert status, terminated-with-access.
2. Confirm all filenames date-stamped for **today**.
3. Confirm weekly SoD schedule still points to a human owner.
4. Confirm EmailTemplate proposal or updated cert template exists.

**Expected result:** Assurance pack cover sheet with today’s date and four counts.

### Task 6 — Author the go-live checklist (printable)

Complete every line in **Go-live checklist (printable)** below. Mark Pass / Fail / Waived. Waivers require residual risk ID.

### Task 7 — Residual risk register

Create a table with at least five rows:

| ID | Risk | Likelihood | Impact | Owner | Accept until | Compensating control |
| --- | --- | --- | --- | --- | --- | --- |
| RR-01 | … | … | … | … | … | … |

Include honest items (examples): file-connector fidelity ≠ production AD/SAP; lab SMTP off; incomplete connector retry automation; contractor AWS standing access; manager rubber-stamp residual.

**Expected result:** Residual risk register signed (your name + date).

### Task 8 — Retro (top 5 gaps)

List top five gaps before **real** bank production (not lab cosplay):

1. …  
2. …  
3. …  
4. …  
5. …  

For each: severity, owner, target month.

**Expected result:** Retro page attached behind checklist.

### Task 9 — Mock examiner drill (15 minutes)

Answer aloud with binder proofs:

1. Show authoritative HR and correlation key.  
2. Show payment dual control is enforced.  
3. Show last cert completion and a closed revoke.  
4. Show terminated-with-access is empty or ticketed.  
5. Show who accepts SoD residual risk and for how long.  

**Expected result:** Five answers deliverable in ≤15 minutes without hunting randomly through menus.

---

## Go-live checklist (printable)

Print this section or export to PDF. Check each box only with evidence on file.

### A. Platform & data

- [ ] IdentityIQ 8.5 lab/prod build identified; environment banner understood
- [ ] Authoritative HR application live; aggregation scheduled
- [ ] Correlation keys documented (employee id / email rules)
- [ ] Critical apps onboarded: AD, Wire, SAP, AWS, Core (as in curriculum)
- [ ] Naming standard `MNB-` enforced until cutover naming approved
- [ ] Lab vs prod secrets not mixed; no committed passwords

### B. Roles & lifecycle

- [ ] Birthright employee role minimal (least privilege)
- [ ] Department/job roles mapped for priority orgs
- [ ] Privileged access request-only (not birthright)
- [ ] Joiner path tested (`nina.joiner` or equivalent)
- [ ] Mover path tested (`priya.wire` or equivalent)
- [ ] Leaver disablement + rapid offboard drill dated
- [ ] Contractor lifecycle controls documented (`raj.external`)

### C. Requests, policies, risk

- [ ] Access request catalog covers critical ents
- [ ] Approval chains defined for privileged / wire / cloud
- [ ] Break-glass role time-bounded and audited
- [ ] SoD matrix (`sod-matrix.csv`) enforced as `MNB-SOD-*` policies
- [ ] Wire dual-control clean for Priya/Marcus
- [ ] Finance-cloud path: revoke preferred; mitigate with expiry only
- [ ] Risk owns SoD acceptance; IAM owns tooling (written)
- [ ] Risk scores weight critical ents; **no auto-revoke** policy written

### D. Certifications & remediation

- [ ] Manager cert cadence quarterly; scoped to high-risk ents
- [ ] App owner cert cadence semi-annual for Wire/AWS/SAP/Core
- [ ] Targeted micro-cert playbook exists (terminated-with-access / contractors-AWS)
- [ ] Latest campaign completion % recorded
- [ ] At least one revoke traced to cube/target confirmation
- [ ] Rubber-stamp QA sample performed
- [ ] Notifications aligned to `certification-sample.txt`

### E. Ops, reporting, communications

- [ ] Provisioning debug playbook published (5 steps)
- [ ] Assurance reports: AWS holders, open SoD, cert status, terminated-with-access
- [ ] All evidence files date-stamped `YYYY-MM-DD`
- [ ] Weekly SoD report scheduled to named human
- [ ] EmailTemplate review complete; noise rules documented
- [ ] Actuator/health or equivalent uptime check known for hosting stack

### F. Governance sign-off

- [ ] Go-live checklist completed with Pass/Fail/Waived
- [ ] Residual risk register (≥5) accepted by Risk proxy
- [ ] Retro top 5 gaps owned with dates
- [ ] Training binder archived (pipeline, SoD, cert, JML, assurance)
- [ ] Capstone mock examiner drill passed (Task 9)

**Sign-off**

| Role | Name | Date | Signature |
| --- | --- | --- | --- |
| IAM Engineer (you) | | | |
| IAM Lead (`helen.ross` proxy) | | | |
| Risk acceptance proxy | | | |

---

## Acceptance criteria

- [ ] **Capstone grades git + evidence:** core Meridian objects present in `config/` (or binder lists SHAs/paths); screenshots alone are insufficient
- [ ] `./tools/iiq-verify/assert-mnb-objects.sh` passes locally or on homelab (or failures explained with residual risk)

- [ ] Pipeline tasks run and evidence saved
- [ ] Clean + handled SoD stories documented
- [ ] Cert demo with traced revoke
- [ ] JML trio evidenced
- [ ] Assurance pack refreshed with today’s stamps
- [ ] Printable checklist completed (all rows Pass/Fail/Waived)
- [ ] Residual risks (≥5) and retro (top 5) written
- [ ] Mock examiner drill completed

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Missing personas | Data not loaded / wrong HR file | Re-copy lab-data; aggregate HR |
| SoD clean+toxic both missing | Policies inactive | Reactivate `MNB-SOD-*`; refresh |
| Cert evidence gone | Campaign purged | Re-run micro-cert; keep exports next time |
| Leaver still has AWS | Remediation never closed | Provisioning playbook; force remove; re-aggregate |
| Checklist all green, gut says no | Greenwash | Force residual risk rows; re-QA cert sample |
| Time overrun | Chasing perfection | Timebox demos; waive with RR IDs |

---

## Training binder evidence (capstone index)

1. Pipeline task results (HR, apps, refresh)  
2. SoD clean + toxic/remediated narratives  
3. Cert definition, completion %, revoke trace, QA sample  
4. JML joiner / mover / leaver packets  
5. Four dated assurance reports + control map  
6. Email template alignment + noise rules  
7. **This go-live checklist** (signed)  
8. Residual risk register  
9. Retro top 5  
10. Mock examiner Q&A notes  

Store as `MNB-Capstone-Exam-Binder-YYYY-MM-DD`.

---

## Knowledge check

1. What artifacts prove exam readiness at Meridian?
2. Name two residual risks you still accept (from your register).
3. What is closed-loop governance in one sentence?
4. Why can a 100% cert completion still fail an exam?
5. Who must sign Risk acceptance on the checklist?
6. What three JML proofs does the capstone require?

### Answers

1. Pipeline proof, SoD clean+handled cases, cert+revoke trace, JML evidence, dated assurance reports, signed checklist + residual risks.  
2. *(Your RR-IDs—e.g., file-connector fidelity; lab SMTP off.)* Any honest register entries count.  
3. Data → roles/requests → policies → certs → provisioning → reports, continuously evidenced.  
4. Open remediations or rubber-stamped decisions mean access/control quality is unproven.  
5. Risk acceptance proxy (not IAM alone).  
6. Joiner (`nina.joiner`), mover (`priya.wire`), leaver/residual packet.

---

## Further reading

- Curriculum index: [docs/lessons/README.md](README.md) and Part II catalog [_CATALOG_51_110.md](_CATALOG_51_110.md).
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — version-specific release notes and go-live checklists; search “certification” / “policy” as needed for demo gaps.
- [SailPoint Community](https://community.sailpoint.com/) — search “IdentityIQ go live checklist” for practitioner cutover lists.
- [FFIEC IT Examination Handbook — Information Security](https://ithandbook.ffiec.gov/it-booklets/information-security.aspx) — exam readiness framing for access governance evidence.
- [NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) — control families mapped throughout this academy (AC, AU, CA, IA).


## Stretch lab

Onboard a new application `MNB-MobileDeposit` with two entitlements; aggregate; correlate; add one SoD pair; run a 5-identity owner micro-cert. Treat it as a timeboxed simulation of production app onboarding using Lessons 09–14 patterns.

---

## Summary

- Capstone proves closed-loop Meridian IAM with demos, not slides.
- The printable checklist + residual risks are the go-live control statement.
- Honest gaps and owners beat perfect theater.

---

**Previous:** [Lesson 49 — Email Templates & Notifications](49-email-templates-notifications.md)

**Next:** [Lesson 51 — Connector Landscape & Registry](51-connector-landscape-and-registry.md) — Part II (connectors & customization) continues. Archive your Part I capstone binder, keep residual risks under review, and use the go-live checklist as the gate for any environment promotion beyond lab; then proceed into the connector and enterprise customization track through Lesson 110.
