# Lesson 231 — Audit-Ready Reports Live

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~55 minutes  
**Prereq:** Lessons 222, 226–229  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 48 / 104

> **Why:** Ops needs exports, not stories — a report row that ties to a specific decision, identity, and timestamp when someone asks why access changed.

## What this is

IIQ **report definitions** (**Intelligence → Reports**) turn live activity into auditor-ready artifacts: Access Review / Certification reports, Provisioning Activity, and Audit event reports. Each export is only useful if **one row** maps back to a real `IdentityRequest`, Provisioning Transaction, or Mailpit message.

You already have that trail from:

| Lesson | What you created |
| --- | --- |
| 222 | Access request + dual approval + `WIRE_INIT` |
| 226–227 | Manager / app-owner cert decisions + revokes |
| 229 | Matched PT id + target proof |

This lesson packages that trail. Classic 48/104 taught report mechanics; here the proof is **traceability**, not “we clicked Run.”

## Know these

```text
Report export row
  → IdentityRequest / work item / cert id column
  → open that object in IIQ (same id)
  → Mailpit message for same identity + overlapping timestamp
  → (optional) Provisioning Transaction id from Lesson 229
```

| Report type | Answers | Typical filter |
| --- | --- | --- |
| **Access Review / Certification** | Who decided what on which campaign | `MNB-Mgr-<date>` from 226 |
| **Provisioning Activity** | What changed on targets | Date range covering 226–229 |
| **Audit** | System events (Certified / Revoke / Complete) | One tracked identity |

| Term | Plain English |
| --- | --- |
| **Export** | CSV/PDF the auditor keeps |
| **Traceability** | Row → live object → mail / PT |
| **Date filter** | Most common zero-row cause |
| **Audit event** | IIQ’s recorded action for forensics / SIEM handoff |

- **Wrong way:** Treating “we ran a report” as proof — proof is one specific row traced to a live message and request id.
- **Wrong way:** Exporting a huge unfiltered dump — auditors want the *matched* row, not noise.
- **Wrong way:** Trusting PDF-only when CSV already has the id columns you need.

## Intent

- Run an Access Review / Certification report against Lesson 226’s manager cert.
- Run a Provisioning Activity report covering revokes from 226–229.
- Run an Audit report for one tracked identity’s cert/provision events.
- Export each; match **one row per export** to IdentityRequest / PT / Mailpit.

## Before you start

- [ ] Lessons 222 and 226–229 activity exists (last ~7 days)
- [ ] IdentityRequest id from 222 and/or PT id from 226/229 under evidence
- [ ] Access to **Intelligence → Reports**
- [ ] Mailpit: [http://localhost:8025](http://localhost:8025)
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/231
```

## Do this

### Task 1 — Access Review / Certification report

1. **Intelligence → Reports → Access Review Report** (or **Certification Report**)
2. Filter to the `MNB-Mgr-<date>` certification from Lesson 226
3. **Run** → wait for **Complete**
4. **Export** CSV

- **Why:** certification decisions must leave an exportable row, not only a UI screen.
- **Expect:** export contains the identity you revoked in 226.

Save as `~/iiq-lab-evidence/sandbox/231/access-review.csv`.

### Task 2 — Provisioning Activity report

1. Open **Provisioning Activity Report** (or **Identity Requests Report** if your build names it that way)
2. Date range covering Lessons 226–229
3. Run → Export CSV

- **Why:** revoke/provision proof for auditors often starts here, then drills to the PT.
- **Expect:** a row whose identity + application match Lesson 229’s transaction.

Save as `provisioning-activity.csv`.

### Task 3 — Audit report for one identity

1. Open **Audit Report**
2. Filter **Identity** to the person you tracked (e.g. the revoke target, or `priya.wire`)
3. Filter **Action** toward certification / revoke / complete / access-request events your build lists
4. Run → Export CSV

- **Why:** Audit events are the handoff surface when security asks “what did IIQ record?” (SIEM/log pipelines start from the same idea).
- **Expect:** row-level events for that identity across the arc.

Save as `audit.csv`.

### Task 4 — Trace one report row to a live object

1. Open `access-review.csv` (or the richest of your three)
2. Find a column with `IdentityRequest` id, work item id, or certification id
3. In IIQ: **Manage Access → Access Request Status** (or open the cert by name) and search that id

- **Why:** export without a live object is just a spreadsheet.
- **Expect:** the exact request/cert opens.

> **Watch out:** If the CSV has no id column, switch the report to a **detailed** template or add the Identity Request Id field — summary-only exports fail this lesson.

### Task 5 — Match Mailpit to the same story

1. Open [http://localhost:8025](http://localhost:8025)
2. Search the identity’s name
3. Confirm at least one message timestamp falls inside the report date range and references the same cert/request name

- **Expect:** Mailpit message Z ↔ report row N.

### Task 6 — Write the matched-row note

Under evidence:

```text
Report: access-review.csv row ____
  → IdentityRequest / cert id: ____
  → Mailpit message: ____ (timestamp ____)
  → PT id (if revoke): ____
```

Repeat one line each for provisioning + audit exports if ids differ.

- **Expect:** one matched set an auditor can follow without asking you questions.

## If it fails

| Symptom | Fix |
| --- | --- |
| Report returns zero rows | Widen date filter to last 7 days; confirm 226–229 actually ran |
| Export greyed out | Wait for Task Result **Complete** under Monitor → Tasks |
| No request id column | Use detailed template / add Identity Request Id field |
| PDF times out | CSV is enough for this proof |
| Mailpit has no matching message | Confirm Lesson 203 SMTP; search by identity name, not only subject |

## You are done when

- [ ] Three exports saved  
- [ ] One row in each traced to a live IIQ object and/or Mailpit message  
- [ ] Matched-row note written  

## Control note

- **Control:** Audit reporting and evidence traceability  
- **Owner:** Compliance/Audit + IAM Ops (report definitions)  
- **SLA (lab):** Same session; production packages are usually on-demand for IR / exam  
- **Evidence:** `~/iiq-lab-evidence/sandbox/231/` — three exports + matched-row note  

## Quick check

1. What proves a report row is real? → Tracing it to a live IdentityRequest / cert / Mailpit message  
2. Most common zero-row cause? → Date filter narrower than when the activity ran  
3. Which export format is enough here? → CSV  
4. How does this connect to Lesson 222? → Same IdentityRequest trail, now exportable  

## Feedback

Could you pick one CSV row and narrate its story (who, what decision, which mail) without opening IIQ? If a report was empty, write the date range you used vs when 226–229 actually ran.

## Navigate

- Previous: [Lesson 230](230-provisioning-troubleshoot-live.md)
- Next: [Lesson 232](232-email-templates-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
