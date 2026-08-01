# Lesson 30 — Mover / Transfer Events

**Level:** Intermediate  
**Track:** Lifecycle  
**Time:** 60–90 minutes  
**Prereq:** Lesson 29; job roles from Lesson 25 (`WireInitiator`, `RelationshipManager`); baseline understanding of `priya.wire`  
**Lab data:** `~/iiq-lab-data/scenarios/mover/hr-delta-priya-to-commercial.csv`

---

## Learning objectives

You will be able to:

- Apply Priya Mehta’s commercial transfer delta (TRS/WIR01 → CML/RM01) in authoritative HR
- Re-aggregate and refresh so role assignment tracks the new jobCode
- Confirm WireInitiator assignment stops and RelationshipManager path starts
- Identify **residual WIRE_INIT** entitlement risk on an RM and open remediation
- Document Meridian mover control SLA (residual high-risk review within 5 business days)
- Explain why role de-assignment alone is not proof that payment entitlements are gone

---

## Why this matters

**Business.** Movers who keep old access accumulate privilege. When `priya.wire` transfers from Wire Specialist to Relationship Manager, she must drop wire initiate capability and pick up CRM-style RM access. A Relationship Manager who still holds **WIRE_INIT** can initiate wires outside the dual-control staffing model — exactly the residual risk this lab highlights.

**Control / audit.** Mover control = HR attribute change → refresh → role re-evaluation → residual entitlement remediation. Evidence = before/after cubes, role diffs, and a remediation work item/note for leftover critical ents. Examiners ask how quickly old payment access is removed after transfer. Control owners: IAM Ops + receiving manager (Commercial).

---

## Concepts

### What a mover is (and is not)

A **mover** is an identity whose job context changes while employment continues: department, jobCode, manager, cost center. It is not a leaver (`inactive=true` / `status=Terminated`) and not a joiner (new `userId`). Meridian’s trigger is HR attribute change on an existing row — here `MNB00090`.

**Role assignment** re-evaluates which business roles match the new attributes. **Residual entitlements** are account-level rights (e.g. `WIRE_INIT` on Wire Portal) that may survive after the role is gone if provisioning did not revoke them.

### Priya’s transfer — before and after

| Attribute | Before (baseline) | After (delta) |
| --- | --- | --- |
| managersAssociateID | `MNB00005` (`rachel.evans`) | `MNB00006` (`sanjay.kapoor`) |
| departmentName | `TRS` | `CML` |
| jobCode | `WIR01` | `RM01` |
| jobTitle | Wire Specialist | Relationship Manager |
| costCenter | `CC-TRS-210` | `CC-CML-220` |
| locationCode | `US-NY` | `US-NY` |
| Expected roles | Birthright + WireInitiator | Birthright + RelationshipManager |
| Entitlement risk | `WIRE_INIT` (expected) | Residual `WIRE_INIT` = Sev-1 until cleared |

```
Before: priya.wire
  dept TRS, job WIR01, manager rachel.evans
  roles: Birthright + WireInitiator
  entitlement: WIRE_INIT (expected)

After mover delta:
  dept CML, job RM01, manager sanjay.kapoor
  roles: Birthright + RelationshipManager (WireInitiator assignment should end)
  residual risk: WIRE_INIT may still exist on Wire Portal until removed
```

### Why residuals happen — and why banks care

Role assignment removal ≠ immediate account entitlement deletion in all labs/connectors. Detection may still show wire-like access. Treat residual `WIRE_INIT` on an RM as **Sev-1** until cleared — it bypasses the Priya/Marcus dual-control split that Lesson 40 will certify.

The naive approach: “Refresh cleared the role, we’re done.” Under exam that fails when Wire Portal still lists her as an initiator.

---

## How it works

```
HR row update (MNB00090 attributes)
        │
        ▼
Account Aggregation task (MNB-HR)
        │
        ▼
Refresh MNB Identities (assign + de-assign roles)
        │
        ├── Lose: MNB-Role-WireInitiator
        └── Gain: MNB-Role-RelationshipManager
        │
        ▼
Residual entitlement hunt (WIRE_INIT on Wire Portal)
        │
        ├── Clean → evidence “no residual”
        └── Present → Sev-1 remediation (remove + re-aggregate)
        │
        ▼
Manager hierarchy now Sanjay → future certs/approvals route to CML
```

| Control step | System action | Human action |
| --- | --- | --- |
| Trigger | HR dept/job change | HR enters transfer |
| Same-day | Aggregate + refresh | IAM verifies role gain/loss |
| ≤5 business days | Residual critical ent review | Business + IAM clear `WIRE_*` on non-WIR jobs |
| Continuous | Manager field update | Certifiers follow new manager |

Control name: `MNB-Ctrl-Mover-Residual-Review`. Payment ents on non-WIR jobs = immediate priority (do not wait five days).

---

## Before you start

- [ ] Backup `~/iiq-lab-data/HRApplications.txt`
- [ ] Scenario file: `~/iiq-lab-data/scenarios/mover/hr-delta-priya-to-commercial.csv`
- [ ] Capture **before** screenshots of `priya.wire` (attrs, roles, WIRE_INIT)
- [ ] `MNB-Role-WireInitiator` and `MNB-Role-RelationshipManager` exist
- [ ] Joiner lesson complete or Nina state noted (do not overwrite unrelated HR rows)

---

## Lab procedure

### Task 1 — Baseline capture (before)

Without a BEFORE pack, AFTER screenshots prove nothing. Examiners want the delta.

1. Open `priya.wire` in Identity Warehouse.
2. Record manager, dept, jobCode, assigned roles, and whether `WIRE_INIT` is present on accounts.
3. Screenshot Roles and Accounts/Entitlements tabs.
4. Confirm baseline expectation: WireInitiator assigned; RM role not assigned.

**Expected result:** Binder “BEFORE” section complete with WIRE_INIT noted.

**If it fails:** If Priya already shows RM01, restore HR from backup taken before any prior mover experiments.

### Task 2 — Read mover delta

Read the change ticket before editing authoritative HR — same discipline as joiner.

1. Open `~/iiq-lab-data/scenarios/mover/hr-delta-priya-to-commercial.csv`.
2. Diff mentally against current HR row for `MNB00090`.
3. Confirm manager becomes `MNB00006` (`sanjay.kapoor`), job `RM01`.

**Expected result:** Clear before→after attribute list matching the Concepts table.

### Task 3 — Apply HR change

Update in place — never insert a second `MNB00090` or you create a correlation nightmare. Prefer the scenario runner (upsert by `userId`, automatic `.bak-*`):

```bash
./tools/lab/scripts/scenarios/apply-mover.sh
```

1. Runner (or hand-edit) updates Priya’s existing row in `HRApplications.txt` to match the delta (do not add a duplicate `MNB00090`).
2. If editing by hand, prefer search-and-replace of the single line; validate field count.
3. Confirm exactly one `MNB00090` row.

**Expected result:** Exactly one `MNB00090` row with CML/RM01/MNB00006.

**If it fails:** Restore from the runner backup (`.bak-*`) or repo seed; re-apply; avoid duplicating `userId`.

### Task 4 — Pipeline: aggregate + refresh

Role re-evaluation only happens when refresh runs with assignment (and de-assignment) enabled.

1. Run **Account Aggregation** for **MNB-HR**.
2. Run **Refresh MNB Identities** with role assignment (and de-assignment) options enabled.
3. Confirm tasks succeed.

**Expected result:** Cube attributes match delta; manager resolves to Sanjay Kapoor.

**If it fails:** Verify file path; confirm Sanjay identity exists; re-refresh.

### Task 5 — Role gain/loss verification

Confirm the role story before hunting residuals — otherwise you confuse “rule broken” with “entitlement leftover.”

1. Re-open `priya.wire`.
2. Confirm **`MNB-Role-RelationshipManager`** assigned (or assignment pending per provisioning).
3. Confirm **`MNB-Role-WireInitiator`** no longer assigned.
4. Confirm birthright remains (still active Employee).
5. Confirm CloudAdmin/BreakGlass still absent.

**Expected result:** Role set matches RM desk; wire initiator assignment gone.

**If it fails:** Check jobCode on cube = RM01; fix assignment rules; refresh again.

### Task 6 — Residual WIRE_INIT hunt

This is the lesson’s Sev-1 punchline. Role gone ≠ entitlement gone.

1. Inspect Wire Portal / IT inventory accounts on Priya for **WIRE_INIT**.
2. If present, classify as **residual high-risk access post-mover**.
3. Create remediation action in binder (and IIQ work item if available): “Remove WIRE_INIT from priya.wire after transfer to RM01.”
4. Note SoD/ senseless privilege: RM with wire initiate capability.

**Expected result:** Either clean (no WIRE_INIT) or documented Sev-1 residual with remediation owner/date.

**If it fails:** Aggregate Wire Portal app again to refresh entitlement view; do not assume role removal deleted the ent.

### Task 7 — Manager / cert routing check

Hierarchy changes are governance changes: future manager certs and approvals must not still route to Rachel.

1. Confirm Manager field is Sanjay (`MNB00006`), not Rachel.
2. Write implication: future manager certs and approvals route to Commercial, not Payments Ops.
3. Note Rachel should not remain default certifier for Priya.

**Expected result:** Hierarchy note linking Lesson 21 to mover outcome.

### Task 8 — Mover control statement

1. Publish `MNB-Ctrl-Mover-Residual-Review`:
   - Trigger: HR dept/job change
   - System: refresh role re-eval within same day
   - Human: residual critical entitlements reviewed within **5 business days**
   - Payment ents (`WIRE_*`) on non-WIR jobs = immediate priority
2. Record control owner: IAM Ops + business manager of new dept.

**Expected result:** Control paragraph with SLA and residual WIRE_INIT example.

### Task 9 — After evidence pack

1. Screenshot AFTER attrs, roles, entitlements.
2. Store side-by-side BEFORE/AFTER in binder.
3. Attach remediation ticket/work item id if created.

**Expected result:** Examiner-ready mover evidence set.

---

## Acceptance criteria

- [ ] Priya HR row updated to CML / RM01 / manager MNB00006
- [ ] Aggregate + refresh completed successfully
- [ ] WireInitiator assignment removed; RelationshipManager assigned
- [ ] Residual WIRE_INIT checked and remediated or ticketed
- [ ] Mover control SLA documented (5 business days for residual high-risk)

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Attributes unchanged | Edited wrong file copy | Point app at `~/iiq-lab-data`; re-agg |
| Still WireInitiator | Refresh without deassign / rule uses dept only | Ensure jobCode rule; enable role updates on refresh |
| No RM role | RelationshipManager rule/job mismatch | Confirm RM01 in rule; active flag |
| Duplicate Priya identities | Bad correlation after edits | Fix employeeId/email; correlate manually if needed |
| WIRE_INIT remains after role loss | Expected without provisioning removal | Open remediation; remove ent via app process |

---

## Training binder evidence

- BEFORE/AFTER screenshots for `priya.wire`
- HR delta CSV reference + updated HR line note
- Task results (aggregate/refresh)
- Residual WIRE_INIT remediation note or clean bill
- `MNB-Ctrl-Mover-Residual-Review`

**Control owner:** IAM Operations + receiving manager (Commercial)  
**Examiner question:** “Show a transfer where payment initiate access was detected and removed after job change.”

---

## Knowledge check

1. What changed for Priya (dept, job, manager)?
2. Why is residual WIRE_INIT dangerous on an RM?
3. What is the mover residual review SLA?
4. Which role should she gain after refresh?
5. Does birthright get removed on this mover?
6. Why can WireInitiator role loss still leave WIRE_INIT on the account?

### Answers

1. Department TRS→CML, job WIR01→RM01, manager MNB00005→MNB00006 (Sanjay Kapoor).
2. She can initiate wires without belonging to the wire specialist control model — privilege accumulation and dual-control bypass risk.
3. Residual high-risk access reviewed within 5 business days (payment ents prioritized immediately).
4. `MNB-Role-RelationshipManager`.
5. No — she remains an active Employee; birthright stays.
6. Role de-assignment does not always provision entitlement removal; residuals need explicit revoke + re-aggregate.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “lifecycle event mover” and “role assignment refresh.”
- [SailPoint Community](https://community.sailpoint.com/) — search “mover residual access” for common post-transfer entitlement findings.
- [NIST SP 800-53 AC-2 / AC-6](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) — account management and least privilege after role change.
- [FFIEC Information Technology Examination Handbook](https://ithandbook.ffiec.gov/) — search access administration / change management expectations for transfers.
- [ISACA — Segregation of Duties](https://www.isaca.org/) — search “segregation of duties” for why leftover payment initiate on an RM is an ITGC finding.

---

## Stretch lab

- Configure a Lifecycle Event on `departmentName` or `jobCode` change to open a “mover residual access” work item automatically.
- Extend remediation to `ACH_OPS` if Priya still carries it from baseline IT inventory.
- Draft manager email template notifying Sanjay of transfer certification responsibility.

---

## Summary

- Movers succeed when HR codes change, refresh re-assigns roles, and residuals are hunted.
- Priya’s commercial transfer is the flagship case: RM role on, WireInitiator off, WIRE_INIT residual treated as Sev-1 until gone.
- Five-business-day residual review (faster for payment ents) is the control you will defend in exams.

---

**Previous:** [Lesson 29 — Joiner Lifecycle](29-joiner-lifecycle.md)  
**Next:** [Lesson 31 — Leaver & Access Disablement](31-leaver-disablement.md)
