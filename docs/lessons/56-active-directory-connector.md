# Lesson 56 — Active Directory Connector

| Field | Value |
| --- | --- |
| **Level** | Intermediate |
| **Track** | Connectors — Directory |
| **Time** | 75–90 minutes |
| **Prereq** | Lessons 53–55; IQService design + feature matrix |
| **Lab data** | `~/iiq-lab-data/connectors/ad/iqservice-checklist.md` |

## Learning objectives

You will be able to:

- Create Application shell `MNB-ActiveDirectory` as **Active Directory - Direct**
- Complete forest/domain, OU, and correlation fields from the Meridian checklist
- Map `sAMAccountName` ↔ `userName` and `employeeID` ↔ `employeeId`
- Finish lab-without-live-AD tasks: schema maps, policy stubs, Test Connection deferred
- Define aggregate task name and test plan order

## Why this matters

Corporate AD is Meridian’s primary workforce directory target for access and many certifications. A half-configured AD Direct app that cannot correlate `helen.ross` produces orphans and failed leavers.

**Control / audit:** Checklist completion, correlation rules, and “create identities = no” are examiner evidence. Live DC is optional for training; the Application shell is not.

## Concepts

| Setting | Meridian intent |
| --- | --- |
| Type | Active Directory - Direct |
| Authoritative | **No** (HR remains truth) |
| Account id | `sAMAccountName` / distinguishedName per design |
| Correlation | `sAMAccountName`↔`userName`; `employeeID`↔`employeeId` |
| IQService | Required for password/enable paths |

```text
  MNB-HR (authoritative)
        |
        v
  Identity cubes (helen.ross, priya.wire, …)
        ^
        | correlate
  MNB-ActiveDirectory (target)
        |
        v
  IQService → DCs
```

## Before you start

- [ ] Lesson 53 network + checklist Y/N/TBD
- [ ] Feature matrix AD row reviewed
- [ ] IIQ up as `spadmin`
- [ ] Decide: live AD available? If no, complete shell only

## Lab procedure

### Task 1 — Reconfirm checklist gates

1. Open `ad/iqservice-checklist.md`.
2. Verify Application type line: **Active Directory - Direct**.
3. Confirm correlation lines match Meridian HR attributes.
4. Exchange required? Mark yes/no for Meridian lab (default **no** unless mailbox lessons demand).

**Expected result:** Checklist gates for app type, correlation, Exchange answered.

### Task 2 — Create Application shell MNB-ActiveDirectory

1. **Applications** → Add New → **Active Directory - Direct** (or equivalent menu path).
2. Name: `MNB-ActiveDirectory`. Owner: Technology (lab: `spadmin`).
3. Enter forest/domain placeholders: `meridiannb.com` (lab).
4. Enter IQService host from Lesson 53 worksheet (`mnb-iqsvc-lab` fictional OK).
5. Save even if Test Connection will fail without live target.

**Expected result:** Application `MNB-ActiveDirectory` listed.

**If it fails:** If type unavailable in lab image, create Application object notes + XML stub file `~/iiq-lab-data/connectors/ad/MNB-ActiveDirectory-shell-notes-56.md` documenting every field—counts as shell.

### Task 3 — Lab without live target — schema & correlation maps

1. Document account attributes to manage: `sAMAccountName`, `givenName`, `sn`, `mail`, `employeeID`, `userAccountControl` (or status equivalent), `memberOf`.
2. Correlation plan:

| AD attribute | Identity attribute |
| --- | --- |
| `sAMAccountName` | `userName` |
| `employeeID` | `employeeId` |
| `mail` | `email` (secondary) |

3. Explicitly set: **do not create identities** from AD.
4. Save maps in `~/iiq-lab-data/connectors/ad/MNB-AD-schema-correlation-56.md`.

**Expected result:** Correlation file complete; create-identities = no documented.

### Task 4 — Search DN / OU scope

1. Draft employee search DN: `OU=Employees,DC=meridiannb,DC=com` (lab placeholder).
2. Draft contractor DN separately.
3. Group aggregation scope: security groups only? Document yes/no.
4. Tie to Lesson 54 aggregation pattern file.

**Expected result:** OU scope bullets in schema file.

### Task 5 — Provisioning policy stubs (forms later)

1. List required create attributes: CN, sAMAccountName, password (initial), OU, mail.
2. Disable/leaver: ENABLE/disable operation; optional OU move (Lesson 57).
3. Do not execute live create without lab AD.

**Expected result:** Stub list in notes; policies refined in Lesson 57/61.

### Task 6 — Aggregation task definition

1. Create (or name for later) Account Aggregation task `Aggregate MNB-ActiveDirectory`.
2. If no live AD: do **not** require success—document “deferred Test Connection / aggregate.”
3. If live AD exists: Run Now; correlate spot-check `helen.ross`, `priya.wire`.

**Expected result:** Task object named; success **or** deferred note with reason “no live target.”

**If it fails:** Connection errors expected without DC—capture error text as training evidence, then stop.

### Task 7 — Control owner & SLA card

1. Fill:

| Field | Value |
| --- | --- |
| App | `MNB-ActiveDirectory` |
| Control owner | Technology |
| Operate | IAM |
| Disable SLA | 4 hours from HR leaver aggregate |
| Aggregate SLA | Nightly before Refresh |

2. Expected result: SLA card in correlation file. If it fails (no owner): assign before go-live—do not leave blank.

**Expected result:** Owner/SLA card complete.

### Task 8 — Test plan from checklist

1. Copy checklist test plan: aggregate → correlate → create → disable → delete (lab only).
2. Mark which steps are design-complete vs executed.

**Expected result:** Test plan with status column.

## Acceptance criteria

- [ ] `MNB-ActiveDirectory` shell created **or** equivalent notes file
- [ ] Checklist type/correlation/Exchange answered
- [ ] Lab-without-live-target schema/correlation file saved
- [ ] Create-identities disabled documented
- [ ] Aggregate task named; live run optional
- [ ] Owner/SLA card written
- [ ] Test plan statused

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Test Connection fails | No DC/IQService | Expected; complete shell docs |
| Orphan identities | Create-identities on | Disable immediately |
| No correlate | Attribute mismatch | Fix maps; use employeeId |
| Wrong connector type | LDAP selected | Recreate as AD Direct |
| Exchange fields confusing | Out of scope | Set Exchange=no for now |

## Training binder evidence

- Screenshot: `MNB-ActiveDirectory` definition (or notes file)
- `MNB-AD-schema-correlation-56.md`
- Checklist with Application type checked
- Aggregate task name + deferred/success note

**Examiner question:** “Is Active Directory authoritative for workforce identity at Meridian? Show the setting.”

## Knowledge check

1. What Application type does Meridian use for Corporate AD?
2. Name two correlation pairs.
3. Should AD create identities?
4. What Windows component supports password/enable?
5. Can you pass this lesson without a live domain?

### Answers

1. Active Directory - Direct.
2. `sAMAccountName`↔`userName`; `employeeID`↔`employeeId` (mail secondary).
3. No—`MNB-HR` remains authoritative.
4. IQService.
5. Yes—shell + lab-without-live-target maps satisfy acceptance.

## Stretch lab

- Export Application XML and redact secrets for binder.
- Premap `userAccountControl` disable bits for leaver demos.
- Align search DNs to real Meridian OU design if provided by Windows team.

## Summary

- `MNB-ActiveDirectory` is a non-authoritative AD Direct target.
- Correlation and IQService design matter more than a green Test Connection in training.
- Lab-without-live-AD completes schema, policies stubs, and test plan status.

---

**Previous:** [Lesson 55 — Provisioning Feature Matrix](55-provisioning-feature-matrix.md)  
**Next:** [Lesson 57 — AD Groups, OUs & Exchange](57-ad-groups-ous-exchange.md)
