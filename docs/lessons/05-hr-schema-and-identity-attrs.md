# Lesson 05 — HR Schema & Identity Attribute Design

| Field | Value |
| --- | --- |
| **Level** | Beginner |
| **Track** | Foundations |
| **Time** | 60–75 minutes |
| **Prereq** | Lesson 04 (`MNB-HR` aggregated; cubes exist) |
| **Lab data** | `~/iiq-lab-data/HRApplications.txt`; reference `departments.csv`, `job-codes.csv` |

## Learning objectives

You will be able to:

- Decide which HR fields belong on the Identity vs only on the Link (account)
- Map HR schema attributes so identity attributes populate after refresh
- Validate manager linkage for a wire specialist toward Payments leadership
- Distinguish `status=0` termination from `onLeave=true` temporary freeze
- Publish a short Meridian identity attribute dictionary for roles/SoD/JML

## Why this matters

Attribute design decides what roles, lifecycle events, and certifications can see. If `departmentCode` lives only on the account link, population rules and birthright roles silently miss people—control gaps with no red error banner.

**Control / audit:** Examiners ask how manager certifications know who reports to whom, and how leavers are distinguished from leave-of-absence. Your attribute dictionary is the design record; the cube is the runtime proof.

## Concepts

| Layer | Holds | Example |
| --- | --- | --- |
| **Account (Link)** | Raw connector attributes | HR row as aggregated |
| **Identity** | Promoted person attributes | Used by roles, policies, certs, selectors |

Promote fields that drive governance:

| Identity attribute | Source column | Used by |
| --- | --- | --- |
| email | email | Notifications, correlation |
| manager | managerId → identity | Certs, approvals |
| departmentCode | departmentCode | Roles, populations |
| jobCode | jobCode | Roles |
| status / inactive | status | Leaver controls |
| workerType | workerType | Contractor SLAs |
| onLeave | onLeave | Temporary freeze |
| locationCode | locationCode | Locational scopes |

```text
  HR account attributes
        |  schema mapping / identity attribute assignment
        v
  Identity attributes  -->  roles / populations / JML / cert display
```

**Codes beat display strings:** Rule on `TRS`, not `"Treasury & Payments"`. Display titles change; codes stay stable.

**Termination vs leave:**

| Signal | Meaning | Control intent |
| --- | --- | --- |
| `status=0` | Employment ended | Disable / remove access (leaver) |
| `onLeave=true` | Still employed, temporarily away | Freeze / reduce access; retain identity |

## Before you start

- [ ] `MNB-HR` exists and `Aggregate MNB-HR` has succeeded
- [ ] You can open cubes for `priya.wire`, `samir.hassan`, `sofia.torres`
- [ ] Lesson 03 attribute/path notes handy

## Lab procedure

### Task 1 — Attribute inventory

1. List every HR header column in your notebook.
2. Mark each **Identity** (promote) or **Link-only** (keep on account).
3. Minimum identity set: `email`, `manager`, `departmentCode`, `jobCode`, `status`, `workerType`, `onLeave`, `locationCode`.
4. Optional promote: `costCenter`, `hireDate`, `jobTitle` (title is display-friendly but prefer codes for rules).

**Expected result:** Two-column inventory table completed before changing IIQ.

### Task 2 — Refine MNB-HR schema maps

1. Open application `MNB-HR` → Schema / Attribute mapping (or Identity attribute mappings—path varies).
2. Map account attributes onto identity attributes used by IIQ (normalize names if UI expects `firstname` vs `firstName`—match what your install shows for existing identities).
3. Confirm manager mapping uses `managerId` toward identity correlation (manager name/id as your version requires).
4. Save. Re-run `Aggregate MNB-HR` if the UI warns that schema changes need aggregation.

**Expected result:** Mapping saved without errors. Notebook lists each identity attribute → HR column.

**If it fails:** Prefer IIQ’s documented identity attribute names from Debug → Identity example; do not invent conflicting attribute names.

### Task 3 — Manager hierarchy check

1. Open identity `priya.wire` (MNB00090).
2. Confirm HR shows `managerId=MNB00005` in the source file.
3. After mappings (and refresh in Lesson 06 if manager not yet resolved), expect manager toward `rachel.evans`.
4. Open `rachel.evans` and note her department `TRS` / job `WIR02`.
5. Sketch two levels: `rachel.evans` → `priya.wire` / `marcus.approve`.

**Expected result:** Written hierarchy snippet for Payments. If manager display is empty, note “pending Identity Refresh” and continue—Lesson 06 completes calculation.

### Task 4 — Inactive and leave flags

1. Open `samir.hassan` (MNB00094): `status=0`, `terminationDate=2026-05-30`.
2. Open `sofia.torres` (MNB00095): `status=1`, `onLeave=true`.
3. Write how Meridian should treat each:

| Persona | Flag | Treatment |
| --- | --- | --- |
| samir.hassan | terminated | Leaver disablement; hunt residual IT access |
| sofia.torres | on leave | Temporary freeze; do not treat as final exit |

**Expected result:** Clear written distinction—feeds Lessons 31–33.

### Task 5 — Contractor and email quality check

1. Open `raj.external` (MNB00093): `workerType=Contractor`, email `raj.contractor@vendor-mail.invalid`.
2. Note: corporate identity attribute email may not be `@meridiannb.com`.
3. Document: “Do not overwrite authoritative email from non-HR apps; flag vendor domains for correlation review.”

**Expected result:** Data-quality note in attribute dictionary.

### Task 6 — Publish attribute dictionary

Create this table in `~/iiq-lab-notes/` (or binder):

| Attribute | Source app | Source field | Consumers |
| --- | --- | --- | --- |
| employeeId / name | MNB-HR | employeeId / userName | Correlation, display |
| email | MNB-HR | email | Notify, correlate |
| manager | MNB-HR | managerId | Certs, approvals |
| departmentCode | MNB-HR | departmentCode | Roles, populations |
| jobCode | MNB-HR | jobCode | Roles |
| status | MNB-HR | status | Leaver, populations |
| workerType | MNB-HR | workerType | Contractor scope |
| onLeave | MNB-HR | onLeave | LoA controls |

**Expected result:** Dictionary page exists; CHANGELOG notes “attribute dictionary v1”.

### Task 7 — Anti-patterns checklist

Add these “do not” rules to the dictionary footer:

1. Do not map IT `accountStatus` onto HR `status`.
2. Do not drive roles from free-text `jobTitle` when `jobCode` exists.
3. Do not let non-HR apps overwrite authoritative `email`.
4. Do not treat `onLeave=true` as `status=0`.

**Expected result:** Four anti-patterns listed; reusable in code reviews for later connectors.

## Acceptance criteria

- [ ] Identity vs Link inventory complete
- [ ] `MNB-HR` mappings updated and saved
- [ ] Manager chain sketched for priya.wire → rachel.evans
- [ ] Termination vs onLeave comparison written
- [ ] raj.external email anomaly noted
- [ ] Attribute dictionary published in notes/binder
- [ ] Anti-patterns checklist written

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Identity attrs blank | Not mapped / no refresh yet | Fix maps; run refresh (Lesson 06) |
| Manager shows raw id only | Manager correlation not run | Enable manager options on refresh |
| Wrong department on cube | Mapped display name instead of code | Map `departmentCode` |
| Duplicate custom attributes | Invented names | Align to standard identity attrs |
| Contractor looks like employee | `workerType` not promoted | Promote and re-aggregate/refresh |

## Training binder evidence

- Attribute inventory table
- Screenshot: `priya.wire` attributes showing department/job/manager (or id)
- Screenshot: `sofia.torres` onLeave vs `samir.hassan` inactive
- Attribute dictionary v1 document

**Examiner question:** “Which identity attributes drive your termination controls versus leave-of-absence controls?”

## Knowledge check

1. Which flag drives termination vs temporary freeze?
2. Why keep `departmentCode` on the identity?
3. Name one attribute certifications commonly display.
4. Why avoid overwriting email from IT apps?
5. Who should be manager of `marcus.approve` per HR?

### Answers

1. `status=0` (termination) vs `onLeave=true` (temporary freeze while still employed).
2. Roles and populations filter people by org code; link-only fields are invisible to many selectors.
3. Examples: display name, department, job title, manager, email.
4. HR is authoritative; IT dumps can be stale or wrong (vendor domains, typos).
5. `rachel.evans` / MNB00005 (Payments Operations Manager).

## Stretch lab

- Promote `costCenter` to the identity and show it on `helen.ross`.
- Build a one-page “forbidden mappings” list (e.g. never map IT `accountStatus` onto HR `status`).
- Using Debug, compare Identity XML before vs after mapping changes (post-refresh).

## Summary

- Governance needs HR fields on the identity, not buried only on the link.
- Codes (`departmentCode`, `jobCode`) power roles; status and onLeave power lifecycle.
- The attribute dictionary is Meridian’s design contract for later lessons.

---

**Previous:** [Lesson 04 — Authoritative HR Source](04-authoritative-hr-source.md)  
**Next:** [Lesson 06 — Identity Cubes & Refresh](06-identity-cubes-and-refresh.md)
