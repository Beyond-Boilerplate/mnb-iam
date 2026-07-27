# Lesson 74 — Google Workspace Connector

**Level:** Intermediate  
**Track:** Connectors — Web APIs & SaaS  
**Time:** 75–90 min  
**Prereq:** Lesson 73 — Okta Connector  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv`
- Repo: `lab-data/connectors/features-string-glossary.md`

---

## Learning objectives

You will be able to:

- Create **MNB-Google-Workspace** for users and groups (OU-aware design notes)
- Map Google Org Units and groups to IIQ entitlement strategy
- Configure service account / OAuth placeholders without live Google admin
- Build lab-without-live-target mock users including `sofia.torres` and `amelia.brooks`
- Define aggregation + suspend-user leaver pattern for Workspace

---

## Why this matters

**Business.** Meridian teams collaborate in Google Workspace. Shared drives and groups often outlive job changes, leaking customer documents.

**Control / audit.** Examiners ask how email/drive access is removed on termination. Suspend/archive patterns plus aggregation evidence answer the control.

---

## Concepts

**Google Workspace / G Suite connector.** Manages Google users, groups, and often Org Unit placement depending on connector options.

| Google concept | IIQ approach |
| --- | --- |
| User | Account (`primaryEmail`) |
| Group | Entitlement |
| Org Unit | Attribute and/or move operation |
| Suspended | Disable / inactive |

```
MNB-Google-Workspace
        │
        ▼
 Admin SDK APIs (service account)
        │
        ├── Aggregate users/groups
        └── Provision create / update / suspend
```

**Lab-without-live-target.** Mock CSV + schema + suspend storyboard; no Google Cloud project required for training completion.

---

## Before you start

- [ ] IIQ up; Okta boundary concepts clear
- [ ] No production Google admin keys in lab machines
- [ ] Domain `@meridiannb.com` used in mocks

---

## Lab procedure

### Task 1 — Domain & naming

1. Confirm email domain `@meridiannb.com` for Workspace users.
2. Application name: `MNB-Google-Workspace`.
3. Owner: `helen.ross`; collab owner `sofia.torres`.

**Expected result:** Naming card written.

### Task 2 — Create application shell

1. Applications → Add New → **Google Apps / Google Workspace** (or equivalent menu path).
2. Enter service account / OAuth placeholders; domain-wide delegation notes for admin API.
3. Save without live Test Connection if needed.

**Expected result:** Application object saved.

**If it fails:** Capture required Admin SDK scopes in binder; continue.

### Task 3 — OU and group strategy

1. Propose OUs: `/Employees`, `/Contractors`, `/Suspended`.
2. Groups: `GRP_ALL_STAFF`, `GRP_WIRE`, `GRP_FINANCE_DRIVES`.
3. Decide: OU as identity attribute; groups as entitlements.

**Expected result:** Strategy table.

### Task 4 — Mock inventory (lab-without-live-target)

1. Create `~/iiq-lab-data/connectors/google/MNB-Google-Workspace-mock.csv` columns `primaryEmail,employeeId,ou,groups,suspended`.
2. Rows: `sofia.torres`, `amelia.brooks`, `raj.external` (contractor OU).
3. Shadow aggregate via DelimitedFile.

**Expected result:** Three accounts; contractor OU visible.

### Task 5 — Account Aggregation task

1. Create `MNB-Google-Workspace-Account-Aggregation`.
2. Run live or shadow; capture counts.
3. Spot-check cube email match.

**Expected result:** Task Result archived.

### Task 6 — Leaver suspend pattern

1. Storyboard: remove sensitive groups → move to `/Suspended` → suspend user → confirm aggregation.
2. Align SLA minutes with Meridian rapid offboarding (Lesson 34 concepts).

**Expected result:** Suspend runbook card.

### Task 7 — featuresString check

1. Confirm ENABLE/PROVISIONING expectations via glossary + registry.
2. Note PASSWORD may differ (Google password vs SSO).

**Expected result:** Feature notes for Risk.

### Task 8 — Examiner question

*How do you prove Drive group removal?* → entitlement remove plan + post-agg group absence.

**Expected result:** Written proof steps.

---


### Task 9 — Residual risk

Record `RR-GW-DRIVE-01`: *Shared Drive memberships outside groups need separate unstructured governance.*

**Expected result:** Residual risk accepted for lab with follow-up owner `sofia.torres`.


## Acceptance criteria

- [ ] `MNB-Google-Workspace` shell with owners
- [ ] OU/group strategy documented
- [ ] Mock/Shadow aggregation evidence
- [ ] Suspend leaver runbook card
- [ ] Feature notes + examiner proof steps

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Delegation denied | Service account not delegated | Fix Google admin delegation; or Shadow path |
| Groups empty | CustomerId / domain wrong | Verify domain settings |
| OU moves fail | Provision policy missing OU attr | Add OU to provisioning policy |
| SSO users password ops fail | Federated accounts | Disable password feature claims; use IdP |
| Contractor in Employees OU | Lifecycle gap | Mover/contractor playbooks update OU |

---

## Training binder evidence

- Naming/owner card
- OU/group strategy
- Mock CSV + Task Result
- Suspend runbook
- Examiner proof steps

---

## Knowledge check

1. What is the Meridian Google application name?
2. Which OU is proposed for leavers pending delete?
3. Who is the collaboration business owner in this lab?
4. What happens in the suspend pattern before suspend itself?
5. Why might PASSWORD features not apply?

### Answers

1. `MNB-Google-Workspace`.
2. `/Suspended`.
3. `sofia.torres`.
4. Remove sensitive groups (and often OU move).
5. Federated/SSO users—password owned by IdP.

---

## Stretch lab

Draft Shared Drive membership governance note: treat Drive groups as certifiable entitlements owned by data stewards.

---

## Summary

- Google Workspace governance centers on users, groups, OUs, and suspend.
- Lab-without-live-target mocks still prove aggregation and leaver design.
- Suspend + group removal evidence satisfies examiner Drive access questions.

---

**Previous:** [Lesson 73 — Okta Connector](73-okta-connector.md)  
**Next:** [Lesson 75 — M365 & SharePoint Online](75-m365-sharepoint-online.md)
