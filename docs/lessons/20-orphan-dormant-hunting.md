# Lesson 20 — Orphan & Dormant Access Hunting

**Level:** Intermediate  
**Track:** Correlation  
**Time:** 60–75 min  
**Prereq:** Lesson 19; HR contains terminated workers; platform apps aggregated  

**Lab data:**
- Primary persona: **`samir.hassan`** (`MNB00094`) — HR `status=0`, terminationDate populated
- Residual access in extracts: `MNB-SAP-Finance` (SAP_FI disabled), `MNB-ActiveDirectory` (ELDAP disabled), IT dump (`DWRP`, `ODS`, `SAP_FI`, …)
- Contrast: active toxic user `jordan.reed` (not a leaver yet)

---

## Learning objectives

You will be able to:

- Hunt **terminated identities that still show application accounts/entitlements**
- Build a case file for **`samir.hassan`** residual access
- Distinguish **orphan** (no identity / uncorrelated) vs **dormant/leaver residual** (identity inactive but access remains)
- Assign defect severity and propose leaver SLA / auto-remediation triggers
- Seed a future report/control name: `MNB-Terminated-With-Access`
- Practice the examiner answer that ties detection to evidence before full lifecycle automation exists

---

## Why this matters

**Business.** Terminated staff with live or even “disabled-but-present” privileged entitlements are tomorrow’s fraud or regulator headline. Meridian’s developer `samir.hassan` was terminated but still appears across finance and IT extracts — exactly the failure leaver processes must catch.

**Control / audit.** Examiners sample terminated employees and ask whether access was removed within policy (often 24 hours for privileged, same-day for wire/cloud). Hunting proves detection even when lifecycle automation is incomplete (automation deepens in Lessons 31–34). “We think IT disables accounts” is not evidence; a daily residual report is.

---

## Concepts

### Orphan vs leaver residual — different playbooks

An **orphan account** (Lesson 19) is access without a proper owning identity — uncorrelated. A **leaver residual / dormant access** is different: the identity exists and is inactive/terminated, but accounts or entitlements still appear on the cube or in target systems.

Mixing these causes wrong tickets. Raj’s vendor-email correlation gap is an orphan/correlation problem. Samir’s post-termination `SAP_FI` is a lifecycle defect. Same IAM tool, different owners and SLAs.

### Disabled vs removed

`accountStatus=disabled` in an extract is better than `active`, but residual entitlement membership can still fail certifications and prove incomplete offboarding. Treat critical residuals as defects until policy says “disabled is closed.” Banks often require remove-from-group / deprovision for finance and payment entitlements — not merely a disabled flag that still shows `SAP_FI` on the cube.

**Real-life Meridian example.** Samir’s SAP row shows disabled — good hygiene relative to an active login — but `SAP_FI` still present after `terminationDate=2026-05-30` is a Sev-1 control gap. Directory ELDAP disabled is Sev-2/3 hygiene. Dev residuals `DWRP` / `ODS` are Sev-2. Overall case severity = **max** of row severities → Samir is Sev-1.

### Detection before automation

Full joiner/mover/leaver workflows arrive later. Until then, Meridian still owes examiners a detection control: after HR aggregation marks someone terminated, a hunt (report/population) finds residual target access and opens tickets. Automation reduces mean time to remediate; hunting proves you notice failures when automation stalls.

### Wrong taxonomy — Jordan is not a leaver

| Persona | Pattern | Playbook |
| --- | --- | --- |
| `samir.hassan` | HR terminated; residual ents | Leaver residual hunt (this lesson) |
| `raj.external` | Contractor; correlation edge | Correlation / orphan (17–19) |
| `jordan.reed` | Active; toxic combination | SoD / policy (later) — **not** termination |

---

## How it works

Authoritative HR status drives the hunt. Target aggregations supply residual evidence. Correlation must largely work so residuals appear on the cube; otherwise hunt on application account lists by `employeeId` / userName.

```
HR status=0 (samir.hassan) + terminationDate
        │
        ▼
Identity cube (inactive) ──► Accounts / Entitlements tabs
        │
        ├── still linked to MNB-SAP-Finance (SAP_FI, disabled) ──► Sev-1
        ├── still linked to MNB-ActiveDirectory (ELDAP, disabled)
        └── IT inventory residuals (DWRP, ODS, SAP_FI, …)
                │
                ▼
Case file → ticket MNB-LAB-LEAVER-001 → owners
Daily control: MNB-Terminated-With-Access after pipeline
```

| Signal | Meaning |
| --- | --- |
| HR `status=0` + `terminationDate` | Authoritative leaver |
| Target `accountStatus=active` on leaver | **Urgent** live residual |
| Target `accountStatus=disabled` on leaver | Residual membership / incomplete cleanup |
| Uncorrelated privileged | Orphan path (Lesson 19); may also be ex-worker |

---

## Before you start

- [ ] `Aggregate MNB-HR` current; `samir.hassan` searchable and inactive
- [ ] SAP, AD, IT-Access aggregated
- [ ] Correlation largely working so residuals show on the cube when linked
- [ ] Binder “Access hunting” section
- [ ] SoD/toxic users not confused with leavers (`jordan.reed` is active)
- [ ] IIQ at `http://localhost:8080/identityiq` as `spadmin`

---

## Lab procedure

### Task 1 — Confirm authoritative leaver truth

Every residual case starts from HR truth. If the cube looks active, you are hunting the wrong person or a stale aggregate.

1. Open identity `samir.hassan`.
2. Confirm HR attributes: inactive/status 0, termination date `2026-05-30` (per lab HR file), department ITP / developer job.
3. Screenshot identity header showing terminated/inactive state.
4. Notebook: “Authoritative source says gone; targets must not disagree silently.”

**Expected result:** HR cube clearly represents a terminated worker.

**If it fails:** Re-aggregate `MNB-HR`; confirm you did not open an active similarly named identity.

### Task 2 — Enumerate residual accounts and entitlements

Build the case file from the cube first, then cross-check apps if correlation hid something. Screenshots of empty tabs are not a clean bill of health until you hunted the app lists.

1. On `samir.hassan`, open Accounts and Entitlements tabs.
2. List every `MNB-*` account still present.
3. Cross-check application account lists if correlation gaps hide something:
   - `MNB-SAP-Finance` → `samir.hassan` / `SAP_FI` / disabled
   - `MNB-ActiveDirectory` → ELDAP / disabled
   - `MNB-IT-Access` / EmployeeData → DWRP, ODS, SAP_FI, ELDAP disabled rows
4. Build case-file table:

| App | Entitlement | Account status | Defect? |
| --- | --- | --- | --- |

**Expected result:** Documented residual set for Samir—finance + directory + inventory at minimum.

**If it fails:** If cube shows nothing, hunt on application account lists filtered by `samir.hassan` / MNB00094—correlation may need refresh.

### Task 3 — Severity classification

Severity drives paging and examiner sampling. Document rationale per entitlement, then take the maximum.

1. Classify each residual:

| Access | Severity | Rationale |
| --- | --- | --- |
| SAP_FI | Sev-1 | Finance SoR |
| AWS_ADMIN / WIRE_* / CORE if ever present | Sev-1 | Privileged / payment / core |
| DWRP / ODS | Sev-2 | Dev/data residual |
| ELDAP disabled | Sev-2/3 | Directory hygiene |

2. Overall case severity = **max** of row severities → Samir is **Sev-1** due to SAP_FI.
3. Write defect statement:

```text
Leaver defect: samir.hassan (MNB00094) terminated 2026-05-30 still
present on MNB-SAP-Finance with SAP_FI (disabled) and other residuals.
Control gap: leaver disablement incomplete vs policy.
```

**Expected result:** Sev-1 case file ready for IAM/IR handoff language.

### Task 4 — Population / search hunt (broader than one user)

Hero users prove the pattern; populations prove the control scales. Sample beyond Samir so the hunt method is transferable.

1. Search or filter identities where HR status is inactive/terminated.
2. Spot-check 2–3 terminated users for any remaining accounts.
3. Note `anita.ross`-style disabled finance/cloud patterns as additional hygiene findings if present.
4. Record count: *Terminated identities reviewed: N; with residual access: M*.

**Expected result:** Hunt method works beyond the seeded hero user.

**If it fails:** Use Advanced Search / populations from Lesson 07 selecting inactive status—create `MNB-Terminated` population if missing.

### Task 5 — Define leaver SLA and auto-remediation trigger

Detection without SLA is curiosity. Write the targets automation will later meet — and the ticket you would open today.

1. Propose Meridian target SLAs:

```text
Privileged + payment + finance + core: disable within 4 hours of HR termination
Standard apps: within 24 hours
Directory: within 4 hours (login path)
Detection hunt: daily report MNB-Terminated-With-Access
```

2. Propose trigger: *When HR aggregation sets status=0, lifecycle leaver event disables target accounts* (implemented in later lifecycle lessons)—for now, detection + ticket is mandatory.
3. Ticket draft `MNB-LAB-LEAVER-001` for Samir residuals assigned to app owners (Finance `deepa.nair`, Technology `christopher.hayes`, IAM `helen.ross` oversight).

**Expected result:** SLA + trigger + ticket language captured—not only a screenshot.

### Task 6 — Dormant vs active confusion check

Wrong playbook is itself a finding. Confirm Jordan is active toxic access, not a termination residual.

1. Open `jordan.reed` briefly—active staff with toxic access (SoD), **not** a termination residual.
2. Write one sentence differentiating:
   - Jordan = active toxic combination (policy)
   - Samir = terminated residual (lifecycle)
3. Optional: check `onLeave` users later (Lesson 33)—do not revoke the same way as terminations without policy.

**Expected result:** Clear taxonomy in binder; avoids wrong playbook.

### Task 7 — Report seed and recurring hunt

Name the control so ops can schedule it. Ad-hoc “I searched Samir” does not survive staff turnover.

1. Name the control report: **`MNB-Terminated-With-Access`**.
2. Define columns: employeeId, displayName, terminationDate, application, entitlement, accountStatus, severity, ticketId.
3. Schedule intent: daily after aggregation pipeline (Lesson 16).
4. Add to ops checklist: *If Sev-1 count > 0, page on-call.*

**Expected result:** Recurring hunt defined as a named control, not ad-hoc curiosity.

### Task 8 — Evidence pack closeout

Assemble the pack you would hand an examiner for the terminated-with-access sample.

1. Assemble:
   - HR inactive screenshot (Samir)
   - Residual entitlements/accounts screenshots
   - Severity table
   - Ticket draft
   - Report definition
2. Practice examiner answer: *“We detect leavers with residual access via daily MNB-Terminated-With-Access after HR aggregation; Samir is our lab proof.”*

**Expected result:** Complete hunting evidence pack for training records.

---

## Acceptance criteria

- [ ] `samir.hassan` confirmed terminated in HR
- [ ] Residual accounts/ents enumerated with statuses
- [ ] Case classified Sev-1 with defect statement
- [ ] Broader terminated hunt sampled (N/M counts)
- [ ] Leaver SLA + auto-remediation trigger proposed
- [ ] Jordan vs Samir taxonomy documented
- [ ] `MNB-Terminated-With-Access` report seeded
- [ ] Examiner answer practiced

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Samir looks active | Stale HR aggregate / wrong person | Re-aggregate HR; verify MNB00094 |
| No ents on cube | Uncorrelated residuals | Hunt on app account lists |
| Disabled treated as “fine” | Incomplete policy | Still log Sev-1 until cleanup standard met |
| Confused with Raj | Orphan vs leaver mix-up | Raj=contractor correlation; Samir=terminated residual |
| Hunt returns huge noise | Including disabled-only directory for all history | Prioritize active residuals + critical ents first |

---

## Training binder evidence

1. Samir HR termination evidence
2. Residual access table + screenshots
3. Sev-1 defect statement + ticket draft
4. Hunt counts (N terminated reviewed, M with residuals)
5. SLA + `MNB-Terminated-With-Access` report spec
6. Jordan vs Samir distinction note

Examiner question: *“Show a terminated user who still had finance access in your IAM tool.”* → `samir.hassan` / SAP_FI.

---

## Knowledge check

1. Who is the seeded terminated user with residual access?
2. What makes Samir’s case Sev-1?
3. How does a leaver residual differ from an uncorrelated orphan?
4. What report name should ops run daily after aggregation?
5. What SLA would you pitch for privileged leaver disablement?

### Answers

1. `samir.hassan` (MNB00094).
2. Residual finance access (`SAP_FI`) after termination (plus other residuals).
3. Leaver residual: inactive identity still showing access. Orphan: account lacks a proper identity link.
4. `MNB-Terminated-With-Access`.
5. Lab pitch example: disable within **4 hours** for privileged/finance/payment/core (document your org’s real policy when you have one).

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “advanced analytics,” “populations,” and “identity status” for building terminated-with-access hunts in your version.
- [SailPoint Community (Compass)](https://community.sailpoint.com/) — search “terminated with access” / “leaver residual” for report designs peers use in exams.
- [NIST SP 800-53 Rev. 5 — AC-2 / PS-4](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — account management and personnel termination controls that map to timely access removal.
- [FFIEC Information Security Booklet](https://ithandbook.ffiec.gov/it-booklets/information-security.aspx) — examiner focus on timely disablement after employment changes.
- [SANS / industry IAM primer: Joiner-Mover-Leaver](https://www.sans.org/white-papers/) — search “identity lifecycle” or “joiner mover leaver” for non-vendor framing of detection vs automation.

---

## Stretch lab

- Add a second hunt: **on-leave** users with privileged entitlements (preview Lesson 33).
- Compare Samir’s disabled flags across SAP vs any active flags in other systems—data quality finding.
- Draft the lifecycle requirement story that Lessons 31–34 will implement.

---

## Summary

- Terminated-with-access hunting turns leaver failures into detectable defects.
- **`samir.hassan`** is Meridian’s Sev-1 residual-access proof case.
- Named report + SLA connect detection to the lifecycle automation track next.

---

**Previous:** [Lesson 19 — Uncorrelated Account Remediation](19-uncorrelated-remediation.md)  
**Next:** [Lesson 21 — Manager Hierarchy & Reassignment](21-manager-hierarchy.md)
