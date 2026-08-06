# Lesson 231 — Audit-Ready Reports Live

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~50 minutes  
**Prereq:** Lesson 226  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 48 / 104

> **Why (1–2 lines):** Ops needs exports, not stories — a report row that ties to a specific decision, identity, and timestamp when someone asks why access changed.

## What this is

IIQ's report definitions (**Intelligence → Reports**) generate exactly that: Access Review Reports, Provisioning Activity, and Audit reports all export to CSV/PDF with row-level detail. This lesson runs three report types against the live activity from Lessons 226–230 and proves a single row in each export maps back to a real Mailpit message or `IdentityRequest` id — the actual audit trail, not a description of one.

## Know these

```text
Report export row → IdentityRequest / work item id column
  → search that id in Access Request Status → same cert/request opens
  → search identity in Mailpit → message timestamp falls in report's date range
```

**Wrong way:** Treating "we ran a report" as the proof — the proof is one specific row traced to a live message and request id.

## Intent

- Run an Access Review Report against the manager cert from Lesson 226.
- Run a Provisioning Activity / Transaction report covering the revokes from Lessons 226–229.
- Run an Audit report filtered to certification and provisioning events for one identity.
- Export each as CSV or PDF and match one exported row to its Mailpit message or IdentityRequest id.

## Before you start

- [ ] Lessons 226–229 activity exists in the last 7 days
- [ ] Access to **Intelligence → Reports**
- [ ] Mailpit UI: `http://localhost:8025`
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/231`

## Do this

1. **Intelligence → Reports → Access Review Report** (or **Certification Report**). Filter to the `MNB-Mgr-<date>` certification from Lesson 226, run, **Export** to CSV.  
   **Expect:** Export contains the row for the identity you revoked.

2. **Intelligence → Reports → Provisioning Activity Report** (or **Identity Requests Report**). Filter by date range covering Lessons 226–229, run, export.  
   **Expect:** Row whose target application and identity match Lesson 229's transaction id.

3. **Intelligence → Reports → Audit Report**. Filter **Action** to `Certified`/`Revoke`/`Complete Certification`, **Identity** to the one you've tracked across this arc. Run, export.  
   **Expect:** Row-level events for that identity across the arc.

4. Open the exported CSV from step 1; find the row's `IdentityRequest` id or work item id column.  
   **Expect:** Id present and legible.

5. Go to `http://localhost:8080/identityiq/manage/access/identityRequest.jsf` (or **Manage Access → Access Request Status**) and search that id.  
   **Expect:** Opens the exact request/cert you exported.

6. Open Mailpit, search the identity's name, confirm at least one message's timestamp falls inside the report's date range and references the same certification/request name.  
   **Expect:** Match found.

7. Save all three exports plus a short note ("row N in report X = IdentityRequest Y = Mailpit message Z") under `~/iiq-lab-evidence/sandbox/231/`.  
   **Expect:** Matched evidence set complete.

## If it fails

- **Report returns zero rows** — date filter is likely narrower than when Lessons 226–229 activity actually ran; widen to "last 7 days".
- **Export button greyed out** — some report types only export after the task result finishes; wait for status **Complete** in **Monitor → Tasks**.
- **Row has no request id column** — switch report template/detail level to "detailed" or add the `Identity Request Id` field if your definition supports custom columns.
- **PDF export times out on large date range** — CSV is fine for this proof; PDF rendering is heavier and not required here.

## You are done when

Three exports exist and one row in each is traced to a real Mailpit message and IdentityRequest id — not just a description of what should have happened.

## Control note

- **Control:** Audit reporting and evidence traceability.  
- **Owner:** Compliance/Audit + IAM Ops (report definitions).  
- **SLA (lab):** Same session; production audit report packages are typically generated on-demand when ops or incident response needs a decision trail.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/231/` — three exports, matched-row note.

## Quick check

1. What proves a report row is real, not decorative? → Tracing it to a live Mailpit message and `IdentityRequest` id.  
2. What's the most common cause of a zero-row report? → Date filter narrower than when the activity actually ran.  
3. Which export format is sufficient for this proof? → CSV — PDF isn't required.

## Navigate

- Previous: Lesson 230  
- Next: Lesson 232  
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
