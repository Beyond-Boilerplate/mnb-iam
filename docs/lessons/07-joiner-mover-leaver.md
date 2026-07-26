# Lesson 07 — Joiner / Mover / Leaver

**Level:** Intermediate  
**Prereq:** Lessons 02–06; `init-lcm.xml` imported recommended  
**Meridian story:** Banks live and die by joiner/mover/leaver. A leaver who keeps `SAP` + `AWS` is an incident waiting to happen.

---

## Story

You will simulate:

1. **Joiner** — add a new employee to the HR file  
2. **Mover** — change department/job for an existing employee  
3. **Leaver** — set `status=0` (or inactive) for someone

Then watch IdentityIQ pick up changes via aggregation + refresh + lifecycle events.

---

## How it works

Lifecycle Manager watches identity changes (often after aggregation/refresh) and triggers **business processes / workflows**:

| Event | Typical trigger | Typical outcome |
| --- | --- | --- |
| Joiner | New identity / active hire | Birthright roles, tickets, AD account create |
| Mover | Dept/title/manager change | Remove old birthright, add new |
| Leaver | Terminated / inactive | Disable accounts, revoke access, approvals |

In a file-based lab, **you** change the CSV; IIQ reacts when tasks run.

---

## Lesson goals

- [ ] Simulate joiner/mover/leaver in `HRApplications.txt`
- [ ] Re-aggregate + refresh and observe cube changes
- [ ] Locate Lifecycle event configuration / event triggers
- [ ] Define Meridian’s expected leaver control in writing

---

## Tasks

### Task 1 — Joiner

1. Append a new row to `~/iiq-lab-data/HRApplications.txt` with a unique `employeeId` / `userName` / email.  
2. Set `status=1`, pick a real `managerId` that exists (e.g. `a1`).  
3. Save file.  
4. Run `Aggregate MNB-HR` then `Refresh MNB Identities`.  
5. Find the new identity. Confirm manager + birthright role behavior from Lesson 06.

### Task 2 — Mover

1. Pick `sarah.smith` (or another active user).  
2. Change `departmentCode` and/or `positionCode` in the HR file.  
3. Re-aggregate + refresh.  
4. Observe attribute changes on the cube.  
5. If you have department-based roles, confirm role movement (may require role rule updates).

### Task 3 — Leaver

1. Choose a user with IT entitlements correlated.  
2. Set `status=0` in HR file (and optionally `onLeave=false`).  
3. Re-aggregate + refresh.  
4. Note how IIQ represents inactivity (identity inactive flag, lifecycle event, work items—depends on config).

### Task 4 — Explore Lifecycle config

1. Find **Lifecycle Events** / Business Processes related to joiner mover leaver.  
2. Open one workflow in Debug and skim steps (don’t rewrite yet).  
3. Identify where you would add “disable all accounts” for leavers in a real build.

### Task 5 — Meridian leaver standard (write it)

Create a short control statement:

1. HR status inactive within X hours propagates to IIQ  
2. All high-risk entitlements revoked / accounts disabled  
3. Manager notified  
4. Evidence retained for audit  

---

## Tips & tricks

- File editors sometimes break CSV commas—validate the header column count after edits.  
- Lifecycle events won’t fire if LCM isn’t activated or triggers aren’t mapped to your attributes.  
- Process one scenario at a time so task results stay interpretable.  
- `onLeave=true` is a great stretch trigger for “temporary access freeze” policies.

---

## Checkpoint

1. What data change typically starts a leaver?  
2. Why is mover harder than joiner in role design?  
3. Which two tasks do you almost always run after editing the HR file?

---

## Stretch

Configure a lifecycle event that fires when `onLeave` flips to true. Outcome can be a work item to the manager (“Review access for employee on leave”) without full termination.

**Next:** [Lesson 08 — Access requests & approvals](08-access-requests-approvals.md)
