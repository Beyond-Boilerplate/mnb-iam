# Lesson 110 — Ultimate Meridian Production Blueprint (Capstone)

**Level:** Advanced (Capstone)  
**Track:** Enterprise Hardening & Mastery  
**Time:** 120–150 min  
**Prereq:** Lessons 96–109 complete (Part I foundations strongly recommended)  

**Lab data:**
- All Meridian lab paths under `~/iiq-lab-data/` and `lab-data/`
- [docs/SSD.md](../SSD.md); [docs/HOMELAB-CD.md](../HOMELAB-CD.md)
- Plugins/rules READMEs; binder artifacts from Lessons 93–109

---

## Learning objectives

You will be able to:

- Produce a **Meridian National Bank IdentityIQ production blueprint** covering people, apps, controls, platforms, and operations
- Tie connectors, roles, SoD, JML, certifications, plugins, APIs, workflows/forms, and hardening into one architecture
- Define go-live gates, residual risks, and RACI for production
- Deliver an examiner-ready evidence index mapping controls to lessons/artifacts
- Demonstrate the curriculum end-state: closed-loop governance with enterprise customization discipline
- Honestly mark lab readiness vs production claim — convert weak passes to residual risk IDs

---

## Why this matters

**Business.** Meridian does not go live on fifty disconnected lab tips. Executives need one blueprint: what runs where, who owns it, how it changes, how it recovers, and how it proves control. When Commercial Lending asks whether Wire dual-control is “really live,” the answer is a dated blueprint with gates — not a slide that says “IIQ deployed.”

**Control / audit.** The blueprint is the control narrative. Gaps become numbered residual risks with owners and dates — not silent omissions. When the OCC asks for the IAM control story end-to-end, you hand them `MNB-IIQ-Production-Blueprint-YYYY-MM-DD` plus an evidence index you can retrieve in under five minutes.

---

## Concepts — blueprint spine

```
  People & org model          Applications & connectors
           \                       /
            \                     /
             v                   v
              Identity cubes + roles + policies
                        │
        JML / LCM  <----+---->  Certifications
                        │
              Provisioning + audit + SIEM
                        │
         SSB/CI promote + task topology + DR
                        │
              Least-privilege admin + plugins/APIs
```

### Curriculum map (what feeds each chapter)

| Blueprint chapter | Sourced from lessons (non-exhaustive) |
| --- | --- |
| Bank & org | 01–03, 21 |
| Authoritative HR & cubes | 04–07 |
| App inventory & connectors | 09–16, 51–88 track |
| Correlation & hygiene | 17–22 |
| Roles & privileged | 23–28 |
| JML | 29–34 |
| Requests & approvals | 35–38 |
| SoD & risk | 39–42 |
| Certifications | 43–46 |
| Ops & assurance | 47–50 |
| Rules / workflows / forms / UI authz | 89–96 |
| Plugins / APIs / SSD | 97–103 |
| Hardening & scale | 104–109 |

### Meridian non-negotiables (production)

1. HR is authoritative; directories are targets unless explicitly justified.
2. SoD for payment dual-control enforced and certified (`MNB-SOD-*`).
3. Leavers disabled to SLA with residual hunts (Rapid Offboarding).
4. Config in git via SSB; secrets in secret stores (Lessons 101, 108).
5. `spadmin` break-glass only (Lesson 109).
6. Env banners prevent wrong-system changes (Lesson 103).
7. Audit+SIEM on privileged IAM actions (Lesson 104).
8. Forms capture justification + `MNB-` tickets on privileged requests (Lesson 94).
9. LCM customized via `MNB-WF-*` clones — never hot-edit OOTB (Lesson 93).
10. Task vs UI topology and performance SLOs documented (Lessons 105–106).

### Closed-loop proof sketch

```
HR agg --> cube refresh --> birthright roles
    --> access request / JML --> approvals --> provisioning
    --> SoD evaluate --> cert campaigns --> revoke/remediate
    --> audit/SIEM --> assurance reports --> CAB/exams
```

Each arrow must cite an evidence artifact in your index.

### Meridian production topology (target)

| Pool | Count (example) | Workload |
| --- | --- | --- |
| UI | 2+ HA | Browser, LCM |
| Task | 2+ | Aggregations, refresh, cert fan-out |
| DB | HA/PITR | Cubes, audit, requests |
| IQService | Per AD site | AD/Windows ops |
| SIEM | Enterprise | Detections |

### Sample residual risks (seed — replace with yours)

| ID | Risk | Owner |
| --- | --- | --- |
| RR-MNB-110-01 | File/JDBC connectors approximate prod systems | IAM |
| RR-MNB-110-02 | Single-node lab ≠ prod task/UI split | Platform |
| RR-MNB-110-03 | SMTP / notifications off in lab | IAM |
| RR-MNB-110-04 | SCIM module not enabled | IAM |
| RR-MNB-110-05 | Admin MFA not integrated (`RR-MNB-MFA-ADMIN`) | Security |

---

## How it works — assembling the living design record

| Block | Minutes | Tasks |
| --- | --- | --- |
| Framing | 15 | Task 1–2 |
| Controls & apps | 30 | Task 3–5 |
| Customization & platform | 30 | Task 6–8 |
| Risks & gates | 25 | Task 9–10 |
| Evidence & peer | 20–30 | Task 11–12 |
| Honesty & archive | 10–15 | Task 13–14 |

Protect the peer review slot — solo blueprints hide optimism.

**Go-live narrative (fill-in):**

> Meridian National Bank operates IdentityIQ as the governance control plane for workforce and contractor access. Configuration is promoted via SSB from git SHA ____. Day-2 administration is performed by named members of `MNB-WG-IAM-Ops` without standing `spadmin`. Break-glass use is ticketed and SIEM-alerted. Aggregation freshness meets SLO ____. SoD dual-control policies `MNB-SOD-*` are certified quarterly. Residual risks ____ are accepted by Risk as of ____.

Lesson 50 (Part I) proved closed-loop foundations; Lessons 51–110 deepen connectors, customization, and hardening into production-grade detail. This blueprint **supersedes slideware** as the living design record.

---

## Real-world setup (before you claim production)

### Step 1 — Gather binder crown jewels

1. Matrices from 96; drills from 107/109; AuditConfig from 104; promotion checklists from 101/108.
2. Lesson 50 signed checklist as Appendix A.

### Step 2 — Write for two audiences

1. Executives: one-pager outcomes.
2. Examiners: control matrix + evidence index.

### Step 3 — Honesty pass

1. Weak “pass” gates become RR-IDs.
2. No secrets in the blueprint document.

### Step 4 — Schedule maintenance

1. Quarterly blueprint review calendar invite.
2. Curriculum complete; operations begin.

---

## Before you start

- [ ] Binder from Lessons 96–109 available (matrices, checklists, drill logs)
- [ ] Capstone checklist from Lesson 50 (Part I) available to extend — not replace
- [ ] Blank blueprint template (this lesson’s tasks)
- [ ] Peer reviewer scheduled (`sofia.torres` / mentor)
- [ ] IIQ lab up for any final screenshot gaps
- [ ] Time box 2–2.5 hours focused writing + demos

---

## Lab procedure

### Task 1 — Executive one-pager

Leadership will not read your Task Result archive. Give them outcomes.

1. Write ≤ 1 page: problem (exam + ops risk), solution (IIQ at Meridian), outcomes (JML SLA, SoD, cert cadence, evidence).
2. Name control owner IAM (`helen.ross` proxy) and sponsors.
3. State go-live target environment (homelab vs true prod fiction).

**Expected result:** Executive one-pager PDF/markdown in binder.

**If it fails:** Use bullet form; keep under one page.

### Task 2 — Architecture diagram

1. Draw: users → IIQ UI/task nodes → DB → IQService/connectors → target systems (AD, Core, Wire, AWS, HR file/Workday pattern, Google/M365 as onboarded).
2. Include SIEM arrow from AuditConfig events.
3. Include CI/CD arrow from git → WAR/image → envs.
4. Mark sandbox vs prod clearly (Lesson 103 banners).

**Expected result:** One architecture diagram (draw.io/ASCII/PNG).

### Task 3 — Application & connector register

1. Table every Meridian app you onboarded or planned: `MNB-HR`, `MNB-ActiveDirectory`, `MNB-CoreBanking`, `MNB-WirePortal`, `MNB-AWS-Cloud`, `MNB-SAP-Finance`, CRM, Google Workspace, M365, etc.
2. Columns: Authoritative?, Connector type, Owner, Agg cadence, Prov enabled?, Residual risk.
3. Star any “lab-without-live-target” connectors with checklist status.

**Expected result:** Complete app register (≥ 6 rows).

### Task 4 — Control matrix (CTL map)

1. Extend Lesson 48 control IDs into a matrix: Control | Description | IIQ feature | Evidence artifact | Lesson ref | Frequency.
2. Minimum rows: joiner, leaver, SoD, manager cert, privileged access, aggregation integrity, admin break-glass, promotion discipline, form ticket/justification, env banner.
3. Point evidence to dated filenames where possible.

**Expected result:** Control matrix ≥ 8 rows (prefer ≥ 10 with customization/hardening).

### Task 5 — Identity lifecycle playbooks index

1. Index playbooks: joiner (`nina.joiner`), mover (`priya.wire`), leaver (`jordan.reed`), contractor (`raj.external`), break-glass access, LOA (`sofia.torres` patterns).
2. For each: trigger, IIQ tasks/workflows (`MNB-WF-*` where used), SLA, evidence path.
3. Note Rapid Offboarding drill reference.

**Expected result:** Lifecycle index (one table).

### Task 6 — Authorization & customization blueprint

1. Paste/upgrade Lesson 96 workgroup matrix (`MNB-WG-IAM-Ops`, cert, risk, helpdesk).
2. Plugin inventory: `mnb-iam-toolkit` + study plugins; rights required.
3. API register: `mnb.api.lab` pattern for prod naming `mnb.api.*`.
4. UI banner standard across envs (Lesson 103).
5. QuickLinks: `MNB-QL-Request-Payments`, `MNB-QL-BreakGlass-Info` scoped (Lesson 95).
6. Forms: `MNB-Form-AccessRequest-Extras` with ticket regex (Lesson 94).
7. Workflows: `MNB-WF-*` clones only (Lesson 93).
8. Explicit: no BeanShell sprawl — Java/services per Lesson 102 thresholds; SoD watch read-only.

**Expected result:** Authz + customization chapter (2 pages).

### Task 7 — Platform, scale, DR

1. Task vs UI hosts; partitioning strategy for AD/core (Lesson 105).
2. Performance SLOs from Lesson 106.
3. Backup RPO/RTO + last drill date `LAB-DR-107` (Lesson 107).
4. Promotion path sandbox→dev→prod with CAB (Lesson 108); importdynamic vs WAR decision tree (Lesson 101).
5. Homelab CD mapping (what you automate today vs enterprise gates still missing).

**Expected result:** Platform chapter with measurable targets.

### Task 8 — Hardening & monitoring

1. `spadmin` seal + break-glass drill reference `LAB-BG-109`.
2. AuditConfig minimum set + SIEM contract (Lesson 104).
3. Detection list: spadmin auth, capability grants, failed API auth, aggregation failure storms, SoD watch WARN.
4. On-call / RACI for IAM incidents (`helen.ross`, `sofia.torres`, Risk, SOC).

**Expected result:** Hardening chapter complete.

### Task 9 — Residual risk register

1. Create risks `RR-MNB-110-##` for every honest gap (file connector fidelity, SMTP off, SCIM disabled, single-node lab, MFA admin, QuickLink scope deferrals, etc.).
2. Columns: ID | Risk | Likelihood | Impact | Owner | Mitigate / Accept | Review date.
3. Require Risk proxy acknowledgment line (name/date) — lab signature OK.
4. Include carried risks: `RR-MNB-MFA-ADMIN`, `RR-QL-SCOPE-01`, `RR-AUDIT-CERT-01` if still open.

**Expected result:** Residual risk register with ≥ 5 items **or** explicit “none” with peer challenge.

### Task 10 — Go-live gate checklist

Binary gates (pass/fail). Any fail → no prod claim.

- [ ] SSB build reproducible from clean checkout
- [ ] Authz matrix enforced; spadmin sealed; day-2 without SystemAdministrator
- [ ] SoD policies active; open violations owned by Risk
- [ ] Cert campaigns scheduled; remediation SLA defined
- [ ] JML playbooks evidenced within last 90 days
- [ ] Audit→SIEM path proven (sample + contract)
- [ ] DR object drill + DB backup proof
- [ ] Env banners correct (word-labeled SANDBOX/PROD)
- [ ] API accounts least privilege
- [ ] Privileged request forms require ticket + justification
- [ ] LCM customizations on `MNB-WF-*` with rollback cards
- [ ] Residual risks accepted by Risk

**Expected result:** Gate checklist with pass/fail marks for **lab readiness** (honest).

### Task 11 — Examiner evidence index

1. Build index: Question → Artifact path → Owner → Lesson.
2. Include at least:
   - Who has wire initiate + approve?
   - Show last `spadmin` use
   - Prove leaver disable for named identity
   - Show aggregation success for AD
   - Show promotion SHA for last SoD change
   - Show Access Request ticket/justification fields
   - Show env banner screenshot
3. Time yourself finding one artifact (< 5 minutes).

**Expected result:** Evidence index + timed retrieval note.

### Task 12 — Peer review & demo script

1. 10-minute demo script: login banner → identity cube → SoD violation → cert item → Task Result → form/ticket fields → plugin/API ping → audit event → (optional) QuickLink visibility.
2. Peer scores: clarity, completeness, honesty of risks (1–5).
3. Revise blueprint once based on feedback.

**Expected result:** Demo script + peer score sheet + revision note.

### Task 13 — Bind Part I + Part II artifacts

1. Attach Lesson 50 signed checklist as Appendix A.
2. Attach Lessons 93–109 matrices/drills as Appendix B (workflows, forms, QuickLinks, workgroups, SSD, services, branding, audit, topology, perf, DR, promotion, hardening).
3. Declare blueprint supersedes slideware as the living design record.
4. Schedule quarterly blueprint review calendar invite.

**Expected result:** Appendices listed + review date set.

### Task 14 — Final honesty pass

1. Re-read every “pass” gate; convert weak passes to RR-IDs.
2. Ensure no secret values appear in the blueprint document.
3. Confirm curriculum-end mindset: maintenance begins; go-live gates are the only authority for claiming production readiness.
4. Archive as `MNB-IIQ-Production-Blueprint-YYYY-MM-DD`.

**Expected result:** Honesty pass checklist initialed; archive filename set.

---

## Acceptance criteria

- [ ] Blueprint evidence index maps controls to `config/MNB-*.xml` paths + lesson TaskResults (git + evidence)
- [ ] Assert script allowlist called out as wipe+redeploy acceptance for academy Meridian product layer

- [ ] Executive one-pager
- [ ] Architecture diagram (includes SIEM + CI/CD)
- [ ] App/connector register ≥ 6 apps
- [ ] Control matrix ≥ 8 controls
- [ ] Lifecycle playbook index
- [ ] Authz + plugin + API + forms/WF/QL chapter
- [ ] Platform/DR/promotion chapter with SLOs/RPO/RTO
- [ ] Hardening + detection list
- [ ] Residual risk register acknowledged
- [ ] Go-live gates marked honestly
- [ ] Examiner evidence index with one timed retrieval
- [ ] Peer-reviewed demo script
- [ ] Appendices + quarterly review date
- [ ] Honesty pass initialed; blueprint archived

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Blueprint becomes novel-length | No structure | Stick to task chapters; appendices for dumps |
| All gates “pass” on thin lab | Optimism bias | Peer challenge; convert weak passes to RR-IDs |
| Missing artifacts | Binder gaps | Re-run only the missing lesson task — not entire curriculum |
| Architecture omits SIEM/CI | Silo thinking | Add both arrows — they are mandatory spine |
| Demo fails live | Env drift | Use screenshots backup in binder |
| Customization chapter thin | Skipped 93–96 | Pull forms/WF/QL/WG artifacts before claiming complete |

---

## Training binder evidence

This lesson **is** the binder crown:

- Blueprint document (tasks 1–10 assembled)
- Evidence index
- Peer review sheet
- Demo script
- Residual risks signed
- Appendices A/B list
- Honesty pass initials

Store as `MNB-IIQ-Production-Blueprint-YYYY-MM-DD`.

---

## Knowledge check

1. Name four Meridian production non-negotiables.
2. What must never be promoted from sandbox to prod via DB clone?
3. Which two monitoring events prove admin hardening?
4. What closes a residual risk — deletion or acceptance with date?
5. What makes this curriculum “complete” operationally?
6. How does Part II (connectors & customization) relate to Part I capstone (Lesson 50)?
7. Why must LCM customizations use `MNB-WF-*` clones in the blueprint?

### Answers

1. Any four of: HR authoritative; SoD/payment dual-control; leaver SLA; git/SSB config; spadmin break-glass; env banners; audit+SIEM; form tickets; WF clones; topology/SLOs.
2. Runtime identity/certification databases and unmasked PII/test entitlements.
3. `spadmin` authentication events and capability/workgroup change audits (among others).
4. Formal accept/mitigate with owner and review date — not silent deletion.
5. A living blueprint with gates, evidence, and honest risks — not merely finished markdown lessons.
6. Lesson 50 proved closed-loop foundations; Lessons 51–110 deepen connectors/customization/hardening into production-grade blueprint detail.
7. OOTB edits do not survive upgrades and lack rollback/CAB artifacts — clones are the governed path (Lesson 93).

---

## Further reading

- [docs/SSD.md](../SSD.md) — Meridian SSD/SSB layout — the promotion spine of the blueprint.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — version-specific admin, LCM, connector, and audit references cited across the curriculum.
- [NIST SP 800-53 Rev. 5](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — control families (AC, AU, CM, CP, SI) that map to your CTL matrix.
- [NIST SP 800-34 Rev. 1 — Contingency Planning](https://csrc.nist.gov/publications/detail/sp/800-34/rev-1/final) — DR/RPO/RTO language for the platform chapter.
- [FFIEC IT Handbook](https://ithandbook.ffiec.gov/) — Information Security, Business Continuity, and Development & Acquisition booklets for banking exam narratives.
- [OWASP SAMM](https://owasp.org/www-project-samm/) — deployment and governance maturity for the customization/promotion chapters.

---

## Stretch lab

Convert the blueprint into a CAB presentation (8 slides max) and a one-hour tabletop incident: “Task server down during leaver storm.” Record decisions against gates and residual risks. Optionally draft year-1 roadmap: close top five RR-IDs.

---

## Summary

- You produced Meridian’s ultimate IIQ production blueprint: architecture, controls, authz/customization, platform, hardening, risks, and gates.
- Evidence index and peer-reviewed demo prove the academy path is operational — not theatrical.
- Curriculum complete: maintain the blueprint as the system of record for IAM platform decisions; go-live gates alone authorize a production claim.

---

**Previous:** [Lesson 109 — Hardening spadmin & Capabilities](109-hardening-spadmin-capabilities.md)

**Curriculum complete.** You finished the Meridian National Bank IdentityIQ enterprise training path through Lesson 110 (foundations through connectors, customization, and production hardening). Archive `MNB-IIQ-Production-Blueprint-YYYY-MM-DD`, keep residual risks under review, and use the go-live gates as the only authority for claiming production readiness.
