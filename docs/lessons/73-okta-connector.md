# Lesson 73 — Okta Workforce IdP Connector

**Level:** Intermediate  
**Track:** Connectors — Web APIs & SaaS  
**Time:** 75–90 min  
**Prereq:** Lesson 72 — ServiceNow Connector; Lesson 59 Entra patterns helpful  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (Okta row)
- Repo: `lab-data/connectors/features-string-glossary.md`
- Repo: `lab-data/connectors/scim/Users.json` (SCIM-shaped reference if Okta SCIM used)

---

## Learning objectives

You will be able to:

- Position Okta as Meridian workforce IdP target (and optionally source of authN truth—not HR truth)
- Create **MNB-Okta** application with API token/OAuth placeholders
- Map Okta users, groups, and app assignments to IIQ accounts/entitlements
- Complete lab-without-live-target mock group inventory for Wire and AWS app assignments
- Document authoritative boundary: HR remains `MNB-HR`; Okta is not the joiner source of record

---

## Why this matters

**Business.** Meridian may federate workforce SSO through Okta. Group sprawl in Okta often equals SaaS access. IAM must see those groups to certify and revoke.

**Control / audit.** Examiners ask whether the IdP is treated as HR. Your control narrative must keep Okta as directory/IdP target unless formally designated otherwise.

---

## Concepts

**Okta connector.** OOTB connector for Okta users/groups (and related assignments depending on configuration).

```
MNB-HR (authoritative identities)
        │
        ▼
 Identity cubes
        │
        ├── MNB-Okta (target) ← groups / app assignments
        ├── MNB-AD / Entra (directories)
        └── Business apps
```

| Concern | Source of truth |
| --- | --- |
| Who is an employee? | `MNB-HR` |
| SSO groups / app tiles | Okta (target) |
| Passwords | Per policy / interceptor lessons—not reinvented here |

**Matrix:** Okta → Okta; alternate SCIM 2.0.

**Lab-without-live-target.** Mock CSV of users/groups; app shell; boundary diagram above.

---

## Before you start

- [ ] IIQ up; HR authoritative concept from Lesson 04 understood
- [ ] Matrix Okta row visible
- [ ] Personas `sofia.torres`, `kai.nguyen` available for mock groups

---

## Lab procedure

### Task 1 — Authoritative boundary statement

1. Write: *Okta does not create Meridian identities in this design; `MNB-HR` does.*
2. Note exception process if a future project proposes Okta-authoritative contractors—requires ADR.

**Expected result:** Boundary statement in binder.

### Task 2 — Create MNB-Okta

1. Applications → Add New → **Okta**.
2. Name: `MNB-Okta`. Owner: `helen.ross`; IdP eng contact `kai.nguyen`.
3. Org URL + API token/OAuth placeholders from vault.
4. Save shell (skip live Test Connection if no tenant).

**Expected result:** `MNB-Okta` application object.

**If it fails:** Record required Okta scopes offline; continue mock.

### Task 3 — Group entitlement design

1. Define groups: `OKTA_AWS_POWER`, `OKTA_WIRE_USERS`, `OKTA_ALL_STAFF`, `OKTA_CONTRACTORS`.
2. Risk-rate AWS and Wire groups high/critical.
3. Correlation: login/email → cube.

**Expected result:** Group dictionary table.

### Task 4 — Mock inventory (lab-without-live-target)

1. Create `~/iiq-lab-data/connectors/okta/MNB-Okta-mock.csv` with `userName,email,employeeId,groups,status`.
2. Assign `priya.wire` → `OKTA_WIRE_USERS`; `jordan.reed` → `OKTA_AWS_POWER`; `nina.joiner` → `OKTA_ALL_STAFF`.
3. Shadow DelimitedFile + **Account Aggregation** if no Okta org.

**Expected result:** Task Result with three personas’ groups visible.

**If it fails:** Fix multi-value group delimiter; re-agg.

### Task 5 — Aggregation & leaver

1. Task name: `MNB-Okta-Account-Aggregation`.
2. Leaver storyboard: remove high-risk groups then deactivate Okta user per SLA.
3. Emphasize: deactivate IdP session path in addition to app-level disables.

**Expected result:** Leaver storyboard including IdP step.

### Task 6 — SCIM alternate note

1. Matrix alternate = SCIM 2.0.
2. When to use SCIM endpoint vs native Okta connector—document license/capability check.

**Expected result:** Alternate decision paragraph.

### Task 7 — Examiner drill

Answer: *Show how a terminated employee loses Okta AWS group.* Provide evidence list (plan, Task Result, post-agg).

**Expected result:** Evidence list written.

---


### Task 8 — Residual risk

Record `RR-OKTA-AUTHZ-01`: *Okta group names may not match app RBAC 1:1—certify groups with business owner glossary.*

**Expected result:** Residual risk row with owner `helen.ross`.


## Acceptance criteria

- [ ] Authoritative boundary statement signed in notes
- [ ] `MNB-Okta` shell + group dictionary
- [ ] Mock/Shadow aggregation for ≥3 users
- [ ] Leaver storyboard includes IdP deactivation
- [ ] SCIM alternate note + examiner evidence list

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Token 401 | Wrong token / IP | Rotate token; Shadow path for class |
| Groups missing | Group filter / type | Include Okta groups used for app assignment |
| Okta creating identities | Authoritative flag mis-set | Ensure non-authoritative application |
| Duplicate cubes | Correlation weak | Prefer employeeId/email match to HR |
| Contractor gap | HR feed incomplete | Handle via contractor lifecycle—not Okta as HR |
| SSO still works after disable | Cached session | Document session revoke / MFA policy with IdP team |

---

## Training binder evidence

- Boundary diagram/statement
- App config redacted
- Mock CSV + aggregation result
- Leaver storyboard
- Examiner evidence list

---

## Knowledge check

1. Is Okta Meridian’s HR source of truth in this design?
2. What application name did you create?
3. Name one high-risk Okta group from the lab.
4. What matrix alternate exists for Okta?
5. Why include IdP disable in leaver SLA?
6. Which persona was assigned `OKTA_WIRE_USERS` in the mock?

### Answers

1. No—`MNB-HR` remains authoritative for identities.
2. `MNB-Okta`.
3. `OKTA_AWS_POWER` or `OKTA_WIRE_USERS`.
4. SCIM 2.0.
5. Ends SSO sessions/app tiles even if some app accounts lag.
6. `priya.wire`.

---

## Stretch lab

Design birthright rule sketch: employees get `OKTA_ALL_STAFF` only; Wire groups requestable with approval. Do not deploy rules yet.

---

## Summary

- `MNB-Okta` governs IdP groups as entitlements while HR stays authoritative.
- Lab-without-live-target mock groups still support cert and leaver design.
- Leaver controls must include IdP deactivation evidence.

---

**Previous:** [Lesson 72 — ServiceNow Connector](72-servicenow-connector.md)  
**Next:** [Lesson 74 — Google Workspace Connector](74-google-workspace-connector.md)
