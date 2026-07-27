# Lesson 57 — AD Groups, OUs & Exchange

| Field | Value |
| --- | --- |
| **Level** | Intermediate |
| **Track** | Connectors — Directory |
| **Time** | 60–90 minutes |
| **Prereq** | Lesson 56; `MNB-ActiveDirectory` shell exists |
| **Lab data** | `~/iiq-lab-data/connectors/ad/iqservice-checklist.md`; Lesson 56 correlation file |

## Learning objectives

You will be able to:

- Design OU search scopes for employees vs contractors and leaver OU moves
- Distinguish security vs distribution groups for Meridian governance
- Document group aggregation and entitlement promotion strategy
- Record Exchange/mailbox provisioning as in or out of scope
- Complete lab-without-live-AD group/OU worksheets with Expected result / If it fails

## Why this matters

Wire dual-control depends on the right AD security groups. Certifying distribution lists wastes manager time; missing security groups fails SoD. Leaver OU moves without disable leave active accounts in “Terminated” OU—classic finding.

**Control / audit:** Group type scope and OU move procedures must be written. Exchange mailbox creation is a separate control owner decision.

## Concepts

| Object | Governance note |
| --- | --- |
| Security group | Prefer for access certifications / SoD |
| Distribution group | Mail routing—often exclude from access certs |
| OU | Structural container; moves ≠ disable |
| Mailbox / Exchange | Optional AD Direct feature path via IQService |

```text
  Joiner → create in OU=Employees
  Mover  → change groups ± OU
  Leaver → DISABLE account
         → optional move OU=Terminated
         → remove high-risk groups
```

**Meridian personas:** `priya.wire` / `marcus.approve` model wire initiator/approver group membership; `jordan.reed` high-risk groups.

## Before you start

- [ ] `MNB-ActiveDirectory` shell or notes from Lesson 56
- [ ] Checklist Exchange yes/no answered
- [ ] Lesson 54 AD aggregation pattern file available

## Lab procedure

### Task 1 — OU design worksheet

1. Create `~/iiq-lab-data/connectors/ad/MNB-AD-OU-design-57.md` with:

| Population | Search/create OU (lab DN) |
| --- | --- |
| Employees | `OU=Employees,DC=meridiannb,DC=com` |
| Contractors | `OU=Contractors,DC=meridiannb,DC=com` |
| Terminated | `OU=Terminated,DC=meridiannb,DC=com` |
| Service accounts | Separate OU—**out of human JML** |

2. Rule: aggregation includes Employees + Contractors; Terminated included for evidence or excluded—**document choice**.

**Expected result:** OU file with explicit terminated inclusion decision.

### Task 2 — Group type policy

1. Write policy: “Certify security groups; exclude distribution lists unless Risk requires.”
2. Map example Meridian groups (design names):

| Group CN | Type | Members (lab) |
| --- | --- | --- |
| `MNB-Wire-Initiators` | Security | `priya.wire` |
| `MNB-Wire-Approvers` | Security | `marcus.approve` |
| `MNB-AllStaff-DL` | Distribution | exclude from access cert |

3. Save in same OU design file.

**Expected result:** Group policy + three example rows.

### Task 3 — Lab without live target — entitlement aggregation plan

1. Decide: groups as account attribute `memberOf` vs separate group aggregation application settings (per your IIQ version UI).
2. Draft Account Aggregation task notes: `Aggregate MNB-ActiveDirectory` includes groups Y/N.
3. Managed attribute promotion: promote security groups used in SoD policies.
4. Expected result when live: `priya.wire` shows wire initiator group; If it fails: check filter excluding that OU/group.

**Expected result:** Entitlement plan section with Expected result / If it fails for `priya.wire`.

### Task 4 — Leaver OU move vs disable

1. Sequence Meridian leaver:

| Step | Action | Feature |
| --- | --- | --- |
| 1 | Disable account | ENABLE |
| 2 | Remove wire/admin groups | PROVISIONING |
| 3 | Optional OU move | modify/move support |

2. Write anti-pattern: “OU move alone is not disable.”

**Expected result:** Ordered leaver steps in binder.

### Task 5 — Exchange / mailbox scope

1. From checklist: Exchange required? Default Meridian lab **No**.
2. If Yes later: document mailbox create attributes and IQService dependency; owner = Messaging.
3. If No: explicitly “mailbox provisioning out of IIQ scope for `MNB-ActiveDirectory` v1.”

**Expected result:** One-line Exchange scope decision signed in notes.

### Task 6 — Nested groups & certification noise

1. Decide Meridian stance: certify direct membership only vs expanded nested membership.
2. Write risk: nested expansion can flood managers; no expansion can hide inherited wire access.
3. Expected result: chosen stance documented. If it fails (cert too large): switch to direct-only + privileged nested review separately.

**Expected result:** Nested-group stance paragraph in OU design file.

### Task 7 — Update Application design notes

1. Attach OU DNs and group filters to `MNB-ActiveDirectory` configuration (UI or notes file).
2. Update CHANGELOG: “Lesson 57 OU/group/Exchange scope for MNB-ActiveDirectory.”

**Expected result:** App notes + CHANGELOG updated; live provision optional.

**If it fails:** UI field names differ—capture equivalent settings; do not invent labels.

## Acceptance criteria

- [ ] OU design file with Employees/Contractors/Terminated
- [ ] Security vs distribution policy written
- [ ] Lab-without-live-target entitlement plan with Expected result / If it fails
- [ ] Leaver disable-before-move sequence documented
- [ ] Exchange in/out of scope explicit
- [ ] Nested-group certification stance documented
- [ ] CHANGELOG updated

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Cert noise from DLs | Wrong group filter | Exclude distribution |
| Missing wire groups | OU/group filter | Widen security group scope |
| Account in Terminated still live | Disable skipped | Enforce ENABLE first |
| Mailbox errors | Exchange in scope without Messaging | Set Exchange=no for v1 |
| Nested group confusion | Deep nesting | Document expansion limits |

## Training binder evidence

- `MNB-AD-OU-design-57.md`
- Leaver sequence table
- Exchange scope one-liner
- Group examples for wire personas

**Examiner question:** “Show that terminated users are disabled—not only moved to a Terminated OU.”

## Knowledge check

1. Why prefer security groups for certifications?
2. Is OU move equivalent to disable?
3. Name Meridian lab OUs for employees and terminated.
4. Default Exchange scope for this lab track?
5. Which personas illustrate wire group separation?
6. Why document nested-group expansion stance before first certification?

### Answers

1. They typically gate access; distribution lists are mail routing.
2. No—disable is ENABLE; OU move is optional hygiene.
3. `OU=Employees,...` and `OU=Terminated,...` (lab DNs).
4. Out of scope (No) unless Messaging explicitly opts in.
5. `priya.wire` (initiators) and `marcus.approve` (approvers).
6. Expansion choice changes cert size and whether inherited access is visible to managers.

## Stretch lab

- Design nested group strategy for `MNB-Wire-*` and impact on aggregation.
- Draft Exchange=yes attribute list for a future Messaging sprint.
- Align group CNs to entitlement dictionary codes where possible.

## Summary

- OU design and group-type filters shape certifications and SoD.
- Disable before OU move; Exchange is an explicit scope decision.
- Lab-without-live-AD worksheets keep Meridian training unblocked.
- Nested-group expansion stance must be decided before the first AD access campaign.

---

**Previous:** [Lesson 56 — Active Directory Connector](56-active-directory-connector.md)  
**Next:** [Lesson 58 — LDAP / OpenLDAP Connector](58-ldap-openldap-connector.md)
