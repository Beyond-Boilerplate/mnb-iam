# Lesson 72 — ServiceNow Connector

**Level:** Intermediate  
**Track:** Connectors — Web APIs & SaaS  
**Time:** 75–90 min  
**Prereq:** Lesson 71 — Salesforce Native Connector  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (ServiceNow ITSM row)
- Repo: `lab-data/connectors/features-string-glossary.md`

---

## Learning objectives

You will be able to:

- Configure **MNB-ServiceNow** for account aggregation (and optional ticket hooks design)
- Distinguish account governance vs ITSM ticket integration patterns
- Map ServiceNow groups/roles to IIQ entitlements with Meridian naming
- Complete lab-without-live-target mock users including `jordan.reed` (IT)
- Document examiner evidence for joiner catalog fulfillment via ServiceNow

---

## Why this matters

**Business.** ServiceNow is Meridian’s ITSM spine. IAM must govern who holds admin roles in ServiceNow and may open fulfillment tickets when connectors cannot provision a target directly.

**Control / audit.** Examiners separate *account control on ServiceNow* from *ticketing as compensating control*. Your binder must not conflate the two.

---

## Concepts

**Two patterns:**

| Pattern | Purpose | IIQ object |
| --- | --- | --- |
| ServiceNow connector (accounts) | Govern SN users/groups | Application `MNB-ServiceNow` |
| Ticket hooks / integration | Create INC/RITM for manual fulfill | Workflow / integration config |

```
Access request approved
        │
        ├── Direct provision to target app (preferred)
        └── OR open ServiceNow RITM (compensating) + track IdentityRequest
```

**Matrix:** ServiceNow ITSM → ServiceNow; alternate Web Services.

**Lab-without-live-target.** App shell + mock CSV of SN users/groups + ticket-hook design note (no live instance).

---

## Before you start

- [ ] IIQ up; understand IdentityRequest tracking (Lesson 38)
- [ ] Matrix row for ServiceNow available
- [ ] Persona `jordan.reed` known as IT actor

---

## Lab procedure

### Task 1 — Split the patterns

1. Write two binder headings: Account governance vs Ticket fulfillment.
2. Under each, list Meridian examples (SN admin role vs “fulfill Linux access” RITM).

**Expected result:** Clear split—no mixed sentences.

### Task 2 — Create MNB-ServiceNow

1. Applications → Add New → **ServiceNow** connector.
2. Name: `MNB-ServiceNow`. Owner: `helen.ross`; tech contact `jordan.reed`.
3. Instance URL + auth placeholders only.
4. Save shell.

**Expected result:** Application exists.

**If it fails:** Document required mid-server/OAuth settings offline; continue mock path.

### Task 3 — Entitlement plan

1. Define groups/roles: `SN_ITIL`, `SN_ADMIN`, `SN_CAB`, `SN_HR_FULFILLER`.
2. Risk: `SN_ADMIN` = critical.
3. Add dictionary notes.

**Expected result:** Four entitlements with risk tiers.

### Task 4 — Mock inventory (lab-without-live-target)

1. Create `~/iiq-lab-data/connectors/servicenow/MNB-ServiceNow-mock.csv` with `userName,email,employeeId,groups,active`.
2. Include `jordan.reed`, `helen.ross`, `samir.hassan` with distinct groups.
3. Optional Shadow app + **Account Aggregation**.

**Expected result:** ≥3 accounts aggregated via shadow or live.

### Task 5 — Ticket hook design (no live required)

1. Draft when Meridian opens a RITM: target has no connector; break-glass; manual mainframe.
2. Required fields: IdentityRequest id, identity, app, entitlement, due date SLA.
3. State: ticket is **not** proof of revoke until closed + re-agg/verify.

**Expected result:** Ticket-hook design one-pager.

### Task 6 — Examiner Q&A

Answer: *How do you know ServiceNow admins are certified?* → app-owner cert on `MNB-ServiceNow` + aggregation evidence.

**Expected result:** Written answer in binder.

---


### Task 7 — Dual-control & SoD touchpoint

1. Note if `SN_ADMIN` plus cloud admin roles should be SoD-reviewed later.
2. Assign policy owner proxy: `helen.ross`.
3. Do not activate SoD in this lesson—design only.

**Expected result:** SoD touchpoint paragraph.

### Task 8 — Aggregation schedule

1. Propose daily **Account Aggregation** for `MNB-ServiceNow` at 05:30.
2. Define failure page: IAM on-call + `jordan.reed`.
3. Write count-floor: alert if accounts drop >10% WoW.

**Expected result:** Schedule/SLA card.



### Task 9 — Training binder label

Create binder label `MNB-ServiceNow-Connector-Lab` listing account governance artifacts separately from ticket-hook artifacts.

**Expected result:** Two labeled sections in the binder index.


## Acceptance criteria

- [ ] Account vs ticket patterns separated in writing
- [ ] `MNB-ServiceNow` shell + entitlement dictionary rows
- [ ] Mock/Shadow aggregation evidence
- [ ] Ticket-hook design one-pager
- [ ] Examiner Q&A answered

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Auth to instance fails | Wrong OAuth/basic user | Use dedicated integration user; Shadow path for class |
| Groups not entitlements | Schema not marked managed | Mark groups entitlement; re-agg |
| Ticket closed but access remains | No verify step | Require aggregation/cube check in runbook |
| Confused apps | One app doing both poorly | Keep account app; isolate integration config |
| Admin missed in cert | Population filter wrong | Cert on entitlement SN_ADMIN explicitly |

---

## Training binder evidence

- Pattern split page
- App + entitlement list
- Mock CSV / Task Result
- Ticket-hook one-pager
- Examiner answer

---

## Knowledge check

1. What is the Meridian ServiceNow application name?
2. Why is a closed RITM alone insufficient revoke evidence?
3. Which matrix connector is preferred for ServiceNow?
4. Name a critical ServiceNow entitlement from this lab.
5. Who is a sensible tech contact for MNB-ServiceNow?

### Answers

1. `MNB-ServiceNow`.
2. Fulfillment must be verified on the target/cube after closure.
3. ServiceNow (alternate Web Services).
4. `SN_ADMIN` (critical).
5. `jordan.reed`.

---

## Stretch lab

Sketch LCM workflow branch: if application `featuresString` lacks PROVISIONING, create ServiceNow RITM and park IdentityRequest awaiting ticket close signal.

---

## Summary

- `MNB-ServiceNow` governs SN accounts/groups separately from ticket integrations.
- Lab-without-live-target mock inventories still support cert design.
- Tickets are compensating controls—always verify access outcomes.

---

**Previous:** [Lesson 71 — Salesforce Native Connector](71-salesforce-native-connector.md)  
**Next:** [Lesson 73 — Okta Connector](73-okta-connector.md)
