# Lesson 12 — Audit-Ready Reporting & Ops

**Level:** Intermediate  
**Prereq:** Lessons 01–11  
**Meridian story:** Exam week. Internal audit asks Meridian to prove joiners get birthright access, leavers lose privileged entitlements, SOD is monitored, and managers completed certifications.

---

## Story

You will assemble a mini **evidence pack** using IIQ reports/analytics and your notebook. Then define a lightweight weekly ops checklist so the lab (and someday production) does not rot.

---

## How it works

Auditors rarely accept screenshots alone. They want:

| Evidence | Example |
| --- | --- |
| Control description | How joiner works at Meridian |
| System report | Users with `AWS` |
| Campaign proof | Completed manager cert with revokes |
| Exception register | SOD mitigations with expiry |
| Change history | Who approved privileged access |

IdentityIQ Reports + Advanced Analytics + Certification archives cover much of this.

---

## Lesson goals

- [ ] Run at least three useful reports / searches for Meridian
- [ ] Build a one-page audit evidence index
- [ ] Define a weekly IAM ops checklist
- [ ] Identify your next learning targets beyond this curriculum

---

## Tasks

### Task 1 — Privileged access inventory

1. Search all identities/accounts with entitlement `AWS` or `SAP`.  
2. Export or screenshot with timestamp.  
3. Annotate: birthright (should be none), requested, or legacy.

### Task 2 — Orphan / uncorrelated review

1. Rerun uncorrelated account search from Lesson 05.  
2. Record count trend (hope it went down).  
3. File tickets in your notebook for remaining orphans.

### Task 3 — Certification evidence

1. Open completed `MNB Manager Access Review — Lab`.  
2. Capture: certifier, decisions, revokes processed.  
3. Compare conceptually to notifications in `email.txt`.

### Task 4 — Lifecycle proof

Demonstrate with identities from Lesson 07:

1. Joiner received baseline role  
2. Leaver is inactive / access removed or ticketed  
3. Mover attribute change visible on cube  

### Task 5 — Weekly ops checklist (create and follow once)

Copy this into your notebook and tick it:

- [ ] MySQL backup / dump for lab  
- [ ] Tomcat disk space / logs rotated  
- [ ] `Aggregate MNB-HR` ran  
- [ ] `Aggregate MNB-IT-Access` ran  
- [ ] `Refresh MNB Identities` ran  
- [ ] Open work items < threshold  
- [ ] New SOD violations reviewed  
- [ ] Failed tasks investigated  

### Task 6 — Personal graduation map

Pick two next topics from official docs:

- Password management  
- Rapid Setup  
- Plugins  
- Privileged Account Management integration  
- AI-driven identity security (8.5 doc present in `doc/`)  
- Real AD / SaaS connectors  

---

## Tips & tricks

- Name reports with dates: `MNB-AWS-Holders-2026-07-26`.  
- Evidence packs should map **control → test → result → exception**.  
- Ops checklists beat heroics. Schedule tasks; don’t rely on memory.  
- Export critical XML objects (apps, roles, policies, workflows) from your lab for portfolio / resume demos.

---

## Checkpoint — curriculum complete?

You should now be able to:

1. Stand up IIQ locally  
2. Connect HR + target data  
3. Correlate accounts  
4. Assign birthright roles  
5. Drive JML scenarios  
6. Run request/approve flows  
7. Encode SoD  
8. Run manager certifications  
9. Troubleshoot provisioning basics  
10. Speak like an IAM engineer in a bank audit meeting  

---

## Stretch — capstone project

**Meridian Capstone (fictitious go-live):**

1. Onboard a new delimited app `MNB-WirePortal` with entitlements `WIRE_INIT` and `WIRE_APPROVE`.  
2. SOD: nobody may hold both.  
3. Birthright: none for wire entitlements.  
4. Requestable with dual approval (manager + Wire Ops).  
5. Quarterly manager cert includes WirePortal.  
6. Produce a 2-page design doc + evidence screenshots.

When finished, you have a portfolio-ready IdentityIQ case study.

---

## After the lessons

- Re-read [INFRASTRUCTURE.md](../INFRASTRUCTURE.md) — it will make more sense now.  
- Keep [LOCAL_SETUP.md](../LOCAL_SETUP.md) as your rebuild runbook.  
- Explore PDFs in `identityiq-8.5/doc/` for depth on any weak area.
