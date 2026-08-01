# Lesson 29 — Joiner Lifecycle

**Level:** Intermediate  
**Track:** Lifecycle  
**Time:** 60–90 minutes  
**Prereq:** Lessons 24–28 (birthright + job/priv roles); MNB-HR aggregation path known  
**Lab data:** `~/iiq-lab-data/scenarios/joiner/hr-delta-new-hire.csv` → persona **`nina.joiner`** (`MNB00120`)

---

## Learning objectives

You will be able to:

- Apply the joiner HR delta for Nina Foster (`nina.joiner`) into the authoritative HR file safely
- Run Account Aggregation for MNB-HR and Refresh MNB Identities to materialize the cube
- Confirm birthright `MNB-Birthright-Employee` / ELDAP assignment intent for the new hire
- Distinguish automatic birthright from job-specific access still requiring requests
- Document Meridian joiner SLA and evidence for training/exam records
- Explain why HR file insert is the lab stand-in for a full LCM Joiner lifecycle event

---

## Why this matters

**Business.** Nina Foster starts Monday as a Retail teller. If IdentityIQ has no cube and no directory baseline by opening, she cannot log in — and her branch invents workarounds (shared passwords, borrowed CRM sessions). Automated birthright triggered from HR is Meridian’s first IAM promise: identity exists, directory baseline lands, tickets cover only non-birthright needs.

**Control / audit.** Joiner control = HR active row → Account Aggregation → Refresh → birthright within SLA. Evidence = HR delta file + Task Results + identity screenshots. Examiners ask how quickly a new teller gets baseline access and what is excluded from automation. Control owners: HR Operations (trigger) + IAM Operations (pipeline).

---

## Concepts

### The joiner business event

In full LCM, a **joiner lifecycle event** fires when IIQ detects a new authoritative account (or attribute pattern) and launches a workflow. In this file-based lab, **inserting an HR row** is the business event — same control story, without Rapid Setup ceremony.

A **birthright role** (`MNB-Birthright-Employee`) is the automatic package every active Employee should receive: typically ELDAP login baseline and nothing privileged. Job packs (Wire, RM, CloudAdmin) stay request-driven.

### Nina’s story — what “day one” must look like

| Field (Nina) | Value | Why it matters |
| --- | --- | --- |
| userId | `MNB00120` | Native key into HR (account id / cube associate key) |
| userName | `nina.joiner` | Cube name; email local-part |
| email | `nina.joiner@meridiannb.com` | Target correlation for SaaS later |
| managersAssociateID | `MNB00007` (`emily.bennett`) | Approvals and manager certs route here |
| inactive / status | `false` / `Active` | Joiner signal — terminated would skip birthright |
| departmentName / division | `RET` | Retail branch context |
| JobCode | `TEL01` | Teller — not wire, not cloud |
| employeeType | `Employee` | Birthright rule includes Employees; contractors differ (Lesson 32) |
| hireDate | `2026-07-26` | SLA clock starts when HR marks active |

**Automatic:** birthright ELDAP via `MNB-Birthright-Employee`. **Not automatic:** CRM, wire (`WIRE_INIT`/`WIRE_APPR`), cloud, privileged roles. Compare `amelia.brooks` (also TEL01) — same birthright composition is the convergence test.

### The wrong way

Hand-create a cube and manually assign ELDAP without an HR row. That works until the next HR aggregation “finds” Nina as uncorrelated or overwrites attributes. Banks fail exams when joiners exist only in AD, not in the authoritative HR feed.

---

## How it works

```
hr-delta-new-hire.csv
        │  append/merge (no duplicate header)
        ▼
HRApplications.txt  (authoritative MNB-HR feed)
        │
        ▼
Account Aggregation task (MNB-HR)
        │  creates/links HR account; create-identities ON for HR only
        ▼
Refresh MNB Identities
        │  attribute sync + role assignment
        ▼
Identity cube nina.joiner
        └── MNB-Birthright-Employee (ELDAP intent)
        └── NO WireInitiator / CloudAdmin / BreakGlass
```

| Stage | IIQ object / action | What you verify |
| --- | --- | --- |
| HR delta applied | File row `MNB00120` | One line; field counts match header |
| Aggregation | Account Aggregation task | Task Result success; no parse errors |
| Materialization | Refresh MNB Identities | Cube exists; manager resolves |
| Birthright | Role assignment | `MNB-Birthright-Employee` present |
| Gap check | Manual analysis | CRM/Wire/Cloud still request-only |

**Production reality:** Live Meridian HR would be Workday or similar (Part II connectors). The delimited HR file here teaches the governance mechanics — aggregate → refresh → birthright — without a live HCM tenant.

---

## Before you start

- [ ] IIQ at `http://localhost:8080/identityiq` as `spadmin`
- [ ] Backup `~/iiq-lab-data/HRApplications.txt`
- [ ] Scenario file present: `~/iiq-lab-data/scenarios/joiner/hr-delta-new-hire.csv`
- [ ] `MNB-Birthright-Employee` assignment rule includes active Employees
- [ ] Confirm `nina.joiner` does **not** already exist (or plan to re-run cleanly)

---

## Lab procedure

### Task 1 — Read the joiner delta

Before you merge anything into production HR (or the lab feed that stands in for it), read the delta like a change ticket. Column shifts corrupt `managersAssociateID` and `status` silently — examiners will not accept “we thought she was active.”

1. Open `~/iiq-lab-data/scenarios/joiner/hr-delta-new-hire.csv`.
2. Verify header columns match `HRApplications.txt`.
3. Record Nina’s manager, job, dept, and hire date in your binder.

**Expected result:** Column counts match; you understand Nina is an active Retail teller under `MNB00007`.

**If it fails:** Fix header mismatch before merging — shifted columns corrupt managersAssociateID/inactive.

### Task 2 — Apply delta to HR file

This is the lab equivalent of HR marking Nina “Active” in the HCM. Prefer the scenario runner (upsert by `userId`, automatic backup) over hand-editing:

```bash
./tools/lab/scripts/scenarios/apply-joiner.sh
# optional: HR_FILE=~/iiq-lab-data/HRApplications.txt ./tools/lab/scripts/scenarios/apply-joiner.sh
```

If you must edit by hand: treat the file as authoritative — one row per `userId`, never a second header mid-file.

1. Backup HR file (the runner does this automatically as `HRApplications.txt.bak-<timestamp>`).
2. Append or upsert Nina’s data row into `~/iiq-lab-data/HRApplications.txt` (data only — do not duplicate header).
3. Confirm one row for `MNB00120` / `nina.joiner`.
4. Confirm no accidental truncation of prior rows.

**Expected result:** HR file contains Nina exactly once with valid CSV/TXT field counts.

**If it fails:** Restore backup; re-append carefully; validate with `wc -l` / spreadsheet open.

### Task 3 — Aggregate MNB-HR

Aggregation is continuous inventory. The Task Result timestamp is your joiner control’s start evidence.

1. Tasks → run **Account Aggregation** for application **MNB-HR**.
2. Wait for success in Task Results.
3. Check for errors/warnings referencing `MNB00120`.

**Expected result:** Aggregation succeeds; new account link for Nina creatable on next identity view.

**If it fails:** Validate file path on the application; fix malformed row; re-run aggregation.

### Task 4 — Refresh identities (joiner materialization)

Refresh is where attributes and birthright roles land on the cube. Aggregation alone does not assign `MNB-Birthright-Employee`.

1. Run **Refresh MNB Identities** with identity attribute refresh + **role assignment** enabled.
2. Optionally filter to new identity / recent hires if supported.
3. Confirm task success.

**Expected result:** Identity cube `nina.joiner` exists with HR attributes and manager resolved toward Emily Bennett / `MNB00007`.

**If it fails:** Confirm manager `MNB00007` exists; fix manager correlation; re-refresh.

### Task 5 — Verify cube & birthright

Examiners sample whether birthright is *only* birthright. Privileged roles on day one are a finding.

1. Identity Warehouse → search `nina.joiner`.
2. Confirm attributes: email `@meridiannb.com`, TEL01, RET, Employee, active.
3. Confirm Manager resolves (Emily Bennett).
4. Roles: **`MNB-Birthright-Employee` assigned**.
5. Confirm **no** CloudAdmin, BreakGlass, WireInitiator, or RM roles.

**Expected result:** Birthright only among business packs; privileged roles absent.

**If it fails:** Re-check birthright rule; ensure refresh assigned roles; verify `employeeType=Employee` on cube.

### Task 6 — Gap analysis (non-birthright)

Honest programs do not oversell automation. Nina still needs branch apps that are not birthright — those become catalog requests (Lesson 35), not silent grants.

1. List access Nina might still need for teller operations beyond ELDAP (core banking frontline, branch apps) — mark as **request / separate birthright** decisions.
2. Explicitly note CRM/Wire/Cloud are out of scope for TEL01 automation.
3. Open a training “ticket” note: optional follow-up request catalog items (Lesson 35).

**Expected result:** Gap list with “auto vs request” column; birthright alone not oversold.

### Task 7 — Joiner SLA statement

Controls without SLAs are aspirations. Write the numbers you will defend.

1. Write Meridian lab/prod target:
   - Identity visible ≤ 1 hour after HR marks active
   - Birthright assigned same refresh cycle
   - Non-birthright fulfilled per catalog SLAs
2. Name control `MNB-Ctrl-Joiner-SLA`.

**Expected result:** SLA paragraph with metrics and owners (HR data + IAM ops).

### Task 8 — Evidence pack

1. Capture screenshots: HR row, aggregation result, Nina cube attrs, birthright role.
2. Store delta file path and bak file name in binder index.

**Expected result:** Complete joiner evidence folder entry.

---

## Acceptance criteria

- [ ] **Bank craft exit:** Joiner flow works in IIQ; optional export to `config/Workflow/MNB-Workflow-Joiner.xml`

- [ ] Nina’s HR row applied without corrupting HR file
- [ ] MNB-HR aggregation and identity refresh succeeded
- [ ] `nina.joiner` cube exists with correct manager/job
- [ ] `MNB-Birthright-Employee` assigned; privileged roles not assigned
- [ ] Joiner SLA and gap analysis documented

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Nina missing after agg | Row not in file path IIQ reads | Confirm `~/iiq-lab-data` path on app |
| Identity created, no birthright | Assign roles off / rule exclude | Enable assign; fix employeeType/inactive maps |
| Manager blank | MNB00007 missing or map fail | Ensure Emily exists; re-aggregate/refresh |
| Duplicate Nina | Delta applied twice | Dedupe HR file; re-aggregate |
| CSV column shift | Header appended or commas in fields | Restore bak; re-apply clean row |

---

## Training binder evidence

- Copy of joiner delta CSV + note of append time
- Task result screenshots (aggregate + refresh)
- `nina.joiner` attribute + roles screenshots
- Gap analysis table (auto vs request)
- `MNB-Ctrl-Joiner-SLA`

**Control owner:** HR Operations (trigger) + IAM Operations (pipeline)  
**Examiner question:** “Show a joiner from HR file to birthright assignment with timestamps.”

---

## Knowledge check

1. What triggers joiner in this lab?
2. What must Nina get automatically?
3. What is the joiner identity/birthright SLA target?
4. Who is Nina’s managersAssociateID?
5. Should Nina receive `MNB-Role-CloudAdmin` as a joiner?
6. Why is inserting an HR row preferred over hand-creating a cube?

### Answers

1. Inserting/merging the HR delta row for the new hire, then aggregating MNB-HR and refreshing identities.
2. Identity cube + `MNB-Birthright-Employee` (ELDAP baseline) — not privileged or wire packs.
3. Identity within ~1 hour of HR active; birthright same refresh cycle.
4. `MNB00007` (Emily Bennett).
5. No — privileged roles are request-only and never joiner birthright.
6. Hand-created cubes drift from authoritative HR and fail the aggregate/refresh control story examiners sample.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “Lifecycle Manager joiner” and “identity refresh role assignment” for your IIQ version.
- [SailPoint Community](https://community.sailpoint.com/) — search “joiner lifecycle event” for Rapid Setup and file-based HR patterns.
- [NIST SP 800-53 AC-2 — Account Management](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) — baseline expectation that accounts are authorized and provisioned from approved processes.
- [FFIEC Information Security booklet](https://www.ffiec.gov/press/pr060566.htm) — landing context for examiner expectations on access provisioning; search current FFIEC IT Handbook “Information Security.”
- [ISACA — Identity and Access Management guidance](https://www.isaca.org/) — search “identity and access management” for joiner control framing useful in SOX/ITGC discussions.

---

## Stretch lab

- If LCM Rapid Setup / Lifecycle Events are imported, configure a Joiner event on HR account create to create a work item “Verify birthright for nina.joiner.”
- Compare `amelia.brooks` and `nina.joiner` — both TEL01 tellers should converge on the same birthright composition.
- Measure wall-clock time from file save → birthright visible; record as lab KPI.

---

## Summary

- Joiner lab event = HR delta for `nina.joiner` → aggregate → refresh → birthright.
- Automatic access stays minimal; gaps become catalog requests.
- SLA and screenshots turn a demo into an auditable control.

---

**Previous:** [Lesson 28 — Privileged Access Role Design](28-privileged-access-roles.md)  
**Next:** [Lesson 29b — Lifecycle Events & Rapid Setup (optional)](29b-lifecycle-events-rapid-setup.md) · [Lesson 30 — Mover / Transfer Events](30-mover-transfers.md)
