# Lesson 75 — M365 & SharePoint Online Connectors

**Level:** Intermediate  
**Track:** Connectors — Web APIs & SaaS  
**Time:** 75–90 min  
**Prereq:** Lesson 74 — Google Workspace; Lesson 59 Entra ID helpful  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (Office 365 / SharePoint Online rows)
- Repo: `lab-data/connectors/features-string-glossary.md`

---

## Learning objectives

You will be able to:

- Differentiate **Microsoft Office365** vs **SharePoint Online** vs Entra ID connector scopes for Meridian
- Create **MNB-M365** and **MNB-SharePoint-Online** application shells with Graph/OAuth placeholders
- Map mailboxes, M365 groups, and SharePoint site permissions into entitlement strategy
- Complete lab-without-live-target mock inventories for both apps
- Document aggregation tasks and leaver mailbox/site access evidence

---

## Why this matters

**Business.** Meridian runs on Microsoft 365 for mail, Teams, and SharePoint sites holding credit files and board materials. Over-sharing on sites is a recurring exam finding.

**Control / audit.** Examiners ask who can access sensitive site collections and whether leavers lose mailbox and site entitlements. Separate apps clarify ownership and cert scope.

---

## Concepts

**Connector split (matrix):**

| System | Preferred connector | Meridian app name |
| --- | --- | --- |
| Office 365 / mailbox / M365 groups | Microsoft Office365 | `MNB-M365` |
| SharePoint Online sites/groups | Microsoft SharePoint Online | `MNB-SharePoint-Online` |
| Cloud directory | Azure Active Directory / Entra | (Lesson 59) `MNB-Entra` style |

```
Entra ID (directory)
        │
        ├── MNB-M365 (mailboxes / M365 groups)
        └── MNB-SharePoint-Online (sites / SP groups)
```

**Lab-without-live-target.** Two mock CSVs + shells + cert scope notes; no Microsoft tenant required.

---

## Before you start

- [ ] IIQ up; matrix rows for Office 365 and SharePoint Online located
- [ ] Do not use personal Microsoft credentials for lab connectors
- [ ] Personas `helen.ross`, `marcus.approve`, `amelia.brooks` for mocks

---

## Lab procedure

### Task 1 — Scope decision table

1. Copy the Concepts table into binder.
2. Add column “Cert owner”: M365 ops vs SharePoint data steward.
3. Write one anti-pattern: *Do not certify SharePoint site access only via Entra group names if site-unique permissions exist—and document residual risk if you must.*

**Expected result:** Scope table with owners.

### Task 2 — Create MNB-M365

1. Applications → Add New → **Microsoft Office365** (or equivalent).
2. Name: `MNB-M365`. Owner: `helen.ross`.
3. OAuth/Graph app registration placeholders only.
4. Schema plan: UPN native identity; entitlements for M365 groups / licenses as designed.

**Expected result:** Application shell saved.

**If it fails:** Document Graph permissions needed (`User.Read.All`, group reads, etc.) offline.

### Task 3 — Create MNB-SharePoint-Online

1. Add **SharePoint Online** connector app `MNB-SharePoint-Online`.
2. Business owner: `amelia.brooks` (credit/docs steward proxy).
3. Plan entitlements: `SPO_CREDIT_SITE`, `SPO_BOARD_SITE`, `SPO_HR_SITE`.

**Expected result:** Second application shell + three site ents.

### Task 4 — Mock inventories (lab-without-live-target)

1. `~/iiq-lab-data/connectors/m365/MNB-M365-mock.csv` — `upn,employeeId,m365Groups,mailboxEnabled`.
2. `~/iiq-lab-data/connectors/m365/MNB-SharePoint-Online-mock.csv` — `upn,employeeId,sites,active`.
3. Include `marcus.approve` on board site; `amelia.brooks` on credit site.
4. Shadow DelimitedFile apps optional; run **Account Aggregation** on shadows.

**Expected result:** Two Task Results or one combined evidence page with counts.

### Task 5 — Aggregation tasks

1. `MNB-M365-Account-Aggregation`
2. `MNB-SharePoint-Online-Account-Aggregation`
3. Schedule proposal: nightly after Entra agg if applicable.

**Expected result:** Task definitions documented.

### Task 6 — Leaver evidence path

1. Storyboard: remove SPO site ents → revoke M365 groups → disable/cloud mailbox per runbook → re-agg both apps.
2. List screenshots required for examiner.

**Expected result:** Dual-app leaver card.

### Task 7 — featuresString / licensing note

1. Confirm which license SKUs become entitlements vs attributes.
2. Mark CONFIRM with ConnectorRegistry—do not invent SKU lists.

**Expected result:** Licensing approach paragraph.

### Task 8 — Residual risk

`RR-SPO-UNIQUE-01`: unique SharePoint permissions outside groups may be invisible—track with site admin attestation.

**Expected result:** RR logged.

---


### Task 9 — Binder index

Create `MNB-M365-SPO-Binder` index listing: scope table, both apps, both mocks, both aggregation tasks, leaver card, RR-SPO-UNIQUE-01.

**Expected result:** Checklist index with all boxes to tick during demo.


## Acceptance criteria

- [ ] Scope table separates Entra / M365 / SharePoint
- [ ] `MNB-M365` and `MNB-SharePoint-Online` shells created
- [ ] Mock inventories + aggregation evidence (live or shadow)
- [ ] Dual-app leaver card written
- [ ] Residual risk for unique SPO permissions recorded

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Graph 403 | Missing app permission / admin consent | Consent in Entra; or Shadow path |
| Sites missing | Site filter / URL wrong | Widen site scope; verify tenant |
| Duplicate entitlements vs Entra | Same group twice | Cert strategy: pick system of record per control |
| Mailbox still active | Only group removed | Follow full leaver card including mailbox state |
| Board site overshared | Entitlement not certified | Include SPO_BOARD_SITE in owner cert |
| Teams vs SPO confusion | M365 groups vs sites | Document which connector owns which object |

---

## Training binder evidence

- Scope/owner table
- Both app configs redacted
- Mock CSVs + Task Results
- Dual-app leaver card
- RR-SPO-UNIQUE-01

---

## Knowledge check

1. Name both Meridian Microsoft collaboration apps from this lesson.
2. Which matrix connectors apply to Office 365 and SharePoint Online?
3. Who is the SharePoint business owner proxy?
4. Why keep SharePoint separate from Entra?
5. What residual risk covers unique site permissions?
6. Which persona was placed on the board site in the mock?

### Answers

1. `MNB-M365` and `MNB-SharePoint-Online`.
2. Microsoft Office365 and Microsoft SharePoint Online.
3. `amelia.brooks`.
4. Site collection permissions and cert ownership differ from directory groups.
5. `RR-SPO-UNIQUE-01` (unique permissions visibility gap).
6. `marcus.approve`.

---

## Stretch lab

Draft targeted cert definition selecting only `SPO_CREDIT_SITE` holders for a micro-campaign (Lesson 45 pattern).

---

## Summary

- M365 and SharePoint Online need distinct Meridian applications and cert scopes.
- Lab-without-live-target mocks still produce aggregation and leaver evidence design.
- Unique SharePoint permissions remain a documented residual risk.

---

**Previous:** [Lesson 74 — Google Workspace Connector](74-google-workspace-connector.md)  
**Next:** [Lesson 76 — AWS IAM Connector](76-aws-iam-connector.md)
