# Lesson 55 — Provisioning Feature Matrix

| Field | Value |
| --- | --- |
| **Level** | Intermediate |
| **Track** | Connectors |
| **Time** | 60–75 minutes |
| **Prereq** | Lessons 51–54; glossary + selection matrix |
| **Lab data** | `~/iiq-lab-data/connectors/features-string-glossary.md`; selection matrix CSV |

## Learning objectives

You will be able to:

- Build a Meridian test matrix for ENABLE, PASSWORD, UNLOCK, SYNC_PROVISIONING, and basic CRUD
- Map each feature to Application types from the selection matrix
- Design lab-without-live-target test cases with Expected result / If it fails
- Align leaver/joiner controls to declared features only
- Hand Risk a signed capability matrix before connector build-out

## Why this matters

Joiner-mover-leaver (JML) SLAs fail when someone assumes every connector can disable and reset passwords. Meridian’s Wire Portal may support SCIM active flags but not UNLOCK; AD may support ENABLE via IQService; DelimitedFile may only “provision” by rewriting files.

**Control / audit:** The feature test matrix is the contract between IAM and application owners. Examiners compare promised leaver disable to this matrix.

## Concepts

| Feature | JML / ops use | Typical Meridian types |
| --- | --- | --- |
| `PROVISIONING` | Create/modify/delete | AD, JDBC, WS, SCIM, SAP… |
| `SYNC_PROVISIONING` | Synchronous plan execution | When type declares it |
| `ENABLE` | Disable on leaver | AD Direct, many directories/DBs |
| `PASSWORD` | Reset / set | AD (+ IQService), some SaaS |
| `UNLOCK` | Helpdesk unlock | AD / some directories |
| `CURRENT_PASSWORD` | Change requires old password | Policy-sensitive |

```text
  featuresString (registry)
        |
        v
  Meridian capability matrix (this lesson)
        |
        v
  Provisioning policies + test plan
        |
        v
  Production JML controls
```

## Before you start

- [ ] Glossary and Lesson 51 worksheet available
- [ ] Selection records for AD, Core banking, Wire Portal (Lesson 52)
- [ ] Personas remembered: `priya.wire`, `marcus.approve`, `samir.hassan` (leaver-style)

## Lab procedure

### Task 1 — Build the empty Meridian feature matrix

1. Create `~/iiq-lab-data/connectors/MNB-provisioning-feature-matrix-55.csv` with header:

```text
application,type,PROVISIONING,ENABLE,PASSWORD,UNLOCK,SYNC_PROVISIONING,notes
```

2. Add rows for: `MNB-HR`, `MNB-IT-Access`, `MNB-ActiveDirectory`, `MNB-OpenLDAP`, `MNB-CoreBanking-JDBC`, `MNB-WirePortal-WS`, `MNB-EntraID`, `MNB-MSSQL-Reporting`.

**Expected result:** CSV created with eight application rows (values TBD next tasks).

### Task 2 — Fill from registry knowledge (lab without live target)

1. For each row, mark `Y` / `N` / `Unknown` using glossary + Lesson 51 notes—not wishful thinking.
2. Guidance defaults for training:

| Application | PROVISIONING | ENABLE | PASSWORD | UNLOCK |
| --- | --- | --- | --- | --- |
| `MNB-HR` | N (authoritative inbound) | N | N | N |
| `MNB-IT-Access` | Limited/file | N | N | N |
| `MNB-ActiveDirectory` | Y | Y | Y (IQService) | Y typical |
| `MNB-CoreBanking-JDBC` | Y via SQL/procs | Y via status | Rare | Rare |
| `MNB-WirePortal-WS` | Y if API allows | If API has active | If API | If API |

3. Mark Unknown where API/OpenAPI not yet read—Lesson 68 will refine Wire Portal.

**Expected result:** Matrix filled; Unknown allowed with note “confirm in build.”

**If it fails:** Leave Unknown rather than inventing Y.

### Task 3 — Write test cases with Expected result / If it fails

1. For `MNB-ActiveDirectory` (design-only OK):

| Test ID | Operation | Persona | Expected result | If it fails |
| --- | --- | --- | --- | --- |
| AD-EN-01 | Disable | `samir.hassan` | Account disabled in AD / plan success | Check IQService + ENABLE feature |
| AD-PW-01 | Password set | lab only | Password op succeeds | TLS/IQService/account rights |
| AD-UN-01 | Unlock | lab only | Unlock succeeds | Feature missing → remove from helpdesk catalog |

2. For `MNB-CoreBanking-JDBC`:

| Test ID | Operation | Expected result | If it fails |
| --- | --- | --- | --- | --- |
| JDBC-EN-01 | Set status DISABLED | Row status updated via policy SQL | Fix provisioning policy SQL/proc |
| JDBC-CR-01 | Create account | New `mnb_app_accounts` row | Check PROVISIONING + JDBC URL |

3. Store as `~/iiq-lab-data/connectors/MNB-feature-tests-55.md`.

**Expected result:** ≥5 test cases with Expected result and If it fails lines.

### Task 4 — Align leaver control to matrix

1. Draft leaver control statement:

> Meridian leaver disable is mandatory on applications where ENABLE=Y. File inventory apps are evidence sources, not disable targets.

2. List apps where disable is **in scope** vs **out of scope**.

**Expected result:** Two lists in binder.

### Task 5 — SYNC_PROVISIONING decision

1. For each Y on SYNC_PROVISIONING, note whether Meridian requires sync for that app (wire apps may want sync; huge AD may not).
2. Document “async + retry” as default unless Risk requires sync.

**Expected result:** One paragraph sync policy.

### Task 6 — Map features to IdentityRequest outcomes

1. For a failed disable IdentityRequest, first check: does the app’s matrix row show ENABLE=Y?
2. If N: close as configuration defect (wrong promise), not connector bug.
3. Expected result: triage rule written. If it fails (ops always retries): retrain using matrix.

**Expected result:** Triage rule in tests file.

### Task 7 — Risk review simulation

1. Present matrix to a peer (or self-review).
2. Challenge any Y without registry evidence—downgrade to Unknown.
3. CHANGELOG: “Lesson 55 feature matrix drafted.”

**Expected result:** Peer/self sign-off line + CHANGELOG.

## Acceptance criteria

- [ ] Feature matrix CSV created for ≥8 apps
- [ ] Values justified from glossary/registry (Unknown OK)
- [ ] ≥5 test cases with Expected result / If it fails
- [ ] Leaver in-scope list written
- [ ] IdentityRequest triage rule written
- [ ] Sync policy paragraph + CHANGELOG

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Everything marked Y | Optimism | Re-read glossary; downgrade |
| File app PASSWORD=Y | Misunderstanding | Set N |
| No IQService note on AD PASSWORD | Incomplete | Add dependency note |
| Tests require live AD | Scope | Design-only tests accepted this lesson |
| Matrix diverges from Lesson 52 | Drift | Align types to selection records |

## Training binder evidence

- `MNB-provisioning-feature-matrix-55.csv`
- `MNB-feature-tests-55.md`
- Leaver in-scope / out-of-scope lists

**Examiner question:** “Which applications are you obligated to disable on termination, and what feature proves IIQ can do it?”

## Knowledge check

1. Which feature supports account disable on leaver?
2. Why is `MNB-HR` typically not a PASSWORD target?
3. What must accompany every PASSWORD=Y for AD?
4. What does SYNC_PROVISIONING imply?
5. Is Unknown acceptable in the matrix?

### Answers

1. `ENABLE` (with provisioning path configured).
2. HR is authoritative inbound identity truth, not a password management target.
3. IQService (TLS, rights) architecture per Lesson 53.
4. Connector can execute provisioning synchronously when the plan runs.
5. Yes—prefer Unknown over false Y until registry/API confirms.

## Stretch lab

- Add AUTHENTICATE column and mark pass-through candidates.
- Cross-walk matrix to Lesson 47 provisioning troubleshooting playbook.
- Create a helpdesk catalog that only lists UNLOCK where UNLOCK=Y.

## Summary

- Feature matrices prevent impossible JML promises.
- Every Y needs registry/API evidence; Unknown is honest.
- Test cases with Expected result / If it fails become the build QA script.

---

**Previous:** [Lesson 54 — Aggregation Patterns Advanced](54-aggregation-patterns-advanced.md)  
**Next:** [Lesson 56 — Active Directory Connector](56-active-directory-connector.md)
