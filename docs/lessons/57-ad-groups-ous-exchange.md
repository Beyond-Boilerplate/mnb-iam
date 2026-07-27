# Lesson 57 — AD Groups, OUs & Exchange

**Level:** Intermediate  
**Track:** Connectors — Directory  
**Time:** 60–90 min  
**Prereq:** Lesson 56 — `MNB-ActiveDirectory` exists (application or shell notes)  

**Lab data:**
- Home: `~/iiq-lab-data/connectors/ad/iqservice-checklist.md`
- Home: `~/iiq-lab-data/connectors/ad/MNB-AD-schema-correlation-56.md` (Lesson 56 output)

---

## Learning objectives

You will be able to:

- Define OU, security group, and distribution group precisely, and defend which of them belong in access certifications
- Explain group scopes (domain local, global, universal) and why nesting can hide wire-room access from a manager's certification
- Configure group aggregation and group scoping on `MNB-ActiveDirectory` — group schema, group search DNs, security-only filter — as the primary path
- Design OU search scopes for employees, contractors, and terminated users, and defend the Terminated-OU inclusion decision
- Sequence the Meridian leaver correctly (disable **before** OU move) and explain why the reverse order is a classic finding
- Name the Exchange mailbox types, explain how mailbox provisioning rides IQService, and record the in/out-of-scope decision like a control owner

---

## Why this matters

**Business.** Meridian's wire-transfer dual control is enforced by two AD security groups: `MNB-Wire-Initiators` (holding `priya.wire`) and `MNB-Wire-Approvers` (holding `marcus.approve`). If group aggregation misses either group — wrong search DN, wrong filter — the SoD policy from the governance track has nothing to evaluate, and a single person could initiate and approve a wire without IIQ noticing. Meanwhile `jordan.reed`, who sits on a dozen distribution lists, would flood his manager's certification with mail-routing noise if you aggregate groups indiscriminately. Scope decides everything.

**Control / audit.** Last year's mock exam produced the finding this lesson exists to prevent: `samir.hassan`'s account had been *moved* to `OU=Terminated,DC=meridiannb,DC=com` on his exit — and left **enabled**. The OU looked like offboarding; the `userAccountControl` value said otherwise. The examiner's question is always *"show me terminated users are disabled, not just relocated"* — and the answer must be a written leaver sequence, group-type scoping policy, and an explicit Exchange decision, each with an owner. That written record is this lesson's deliverable.

---

## Concepts

### OU vs security group vs distribution group — three objects, one common confusion

These three AD object types get conflated constantly, and each confusion produces a different failure:

| Object | What it is | Grants access? | Governance treatment at Meridian |
| --- | --- | --- | --- |
| **Organizational Unit (OU)** | A *container* in the directory tree — a folder that holds users/groups/computers and is the attachment point for Group Policy and delegated admin rights | No (policy applies, access doesn't) | Account attribute / search scope; never certified as an entitlement |
| **Security group** | A group with a SID that can appear in ACLs — file shares, applications, wire systems check it | **Yes** | Entitlement → ManagedAttribute → certified, risk-rated, revocable |
| **Distribution group** | A mail-routing list with no SID — email delivery only | No | Exclude from access certifications unless Risk explicitly opts one in |

Concrete: `priya.wire` can initiate wires because the wire application checks membership in security group `MNB-Wire-Initiators`. She also appears on `MNB-AllStaff-DL` — a distribution group that routes the all-hands email and grants nothing. The naive approach — aggregate every group and certify all of it — puts `MNB-AllStaff-DL` on every manager's certification at Meridian. Managers bulk-approve to clear the noise, and the one line that mattered (`MNB-Wire-Initiators`) gets rubber-stamped along with it. Under exam, indiscriminate certification is *worse* than scoped certification: it proves reviews happen without attention.

One trap to know: a "distribution" group can be *converted* to a security group (or mail-enabled security groups exist that are both). Your scoping filter keys off the `groupType` attribute, not the name — Task 2 handles this.

### Group scope and nesting — why `jordan.reed`'s access can be invisible

Every AD group has a **scope**: **global** (members from its own domain, usable anywhere in the forest), **domain local** (members from anywhere, usable only in its own domain — the classic resource-ACL group), or **universal** (members and usage forest-wide, membership replicated to the Global Catalog). Single-domain Meridian mostly feels this as a design nicety — until nesting enters.

AD resolves group membership *transitively*: put global group `MNB-Ops-Admins` inside `MNB-Wire-Approvers`, and every Ops admin can approve wires. But the `memberOf` attribute IIQ aggregates on each account shows **direct membership only**. If `jordan.reed` is in `MNB-Ops-Admins`, his cube shows `MNB-Ops-Admins` — not the wire approval it transitively grants. His manager certifies what looks like a harmless ops group and never sees the wire access. (Related quirk: an account's *primary* group — usually Domain Users — is stored on a separate attribute and typically does not appear in `memberOf` at all.)

Meridian's stance, decided in Task 7: certify direct membership, prohibit nesting *into* high-risk groups by policy, and review the membership of high-risk groups (including any nested groups) in a separate targeted certification owned by Risk. Full nested expansion for everyone is the other extreme — it floods certifications and drowns managers.

### The leaver: disable is the control, OU move is hygiene

A leaver has three possible AD actions, and only one of them removes access:

1. **Disable** — sets the ACCOUNTDISABLE bit (`userAccountControl` 512 → 514, per Lesson 56). Login stops immediately. This is the control.
2. **Remove high-risk groups** — defense in depth; kills entitlement-gated access even if a system caches authentication.
3. **Move to `OU=Terminated`** — housekeeping and visibility. Applies lockdown GPOs, keeps the tree tidy. **It does not disable anything.**

Samir's finding happened because someone ran step 3 and skipped step 1: the account looked offboarded in every directory browser while remaining fully usable. The anti-pattern to write on the wall: **"OU move alone is not disable."** The correct Meridian order is disable first (fastest, highest-value control, 4-hour SLA from Lesson 56's card), groups second, OU move last and optional.

### Exchange mailbox types — what "provision a mailbox" actually means

**Exchange** is Microsoft's mail platform; on-premises Exchange stores mailbox configuration *in AD attributes* on the user object, which is why mailbox provisioning is an AD-connector concern at all. The recipient types you must be able to name:

| Mailbox type | What it is | Governance angle |
| --- | --- | --- |
| **User mailbox** | A person's mailbox tied to their AD account | Created at joiner time if in scope; disabled/retained at leaver per retention policy |
| **Shared mailbox** | A mailbox with no (enabled) login of its own — people get *delegated* access | The delegations are access! `amelia.brooks` covering `payments-desk@meridiannb.com` can read every payment instruction — that grant needs an owner and a review |
| **Room / equipment mailbox** | Calendaring resources | Low risk; usually out of governance scope |
| **Remote mailbox** | A stub on-prem object pointing at an Exchange Online mailbox (hybrid) | Provisioning writes different attributes; the M365 lessons pick this up |

When Exchange is in scope, the Direct connector performs mailbox operations **through IQService**, which invokes Exchange management (remote PowerShell) — another reason the Lesson 53 IQService design matters. Meridian's lab default is Exchange **No**: mailbox creation stays with the Messaging team, and Task 6 makes that a signed, dated decision rather than an accident.

---

## How it works

Lesson 56 established the two channels; this lesson widens what flows through them. Group aggregation adds a second read stream (group *objects*, not just the `memberOf` values on accounts), scoped by its own search DNs and filter. Provisioning gains three write operations: group membership changes, OU moves, and — only if in scope — mailbox operations.

```
IdentityIQ (MNB-ActiveDirectory)
        │
        ├── READ: LDAP(S) to DC/GC
        │     ├── Account aggregation: users under account search DNs
        │     │     └── memberOf (multi-valued)  → direct group memberships
        │     └── Group aggregation: group objects under GROUP search DNs
        │           filter: security groups only (groupType bit 0x80000000)
        │           └── promoted to ManagedAttributes (entitlement catalog)
        │
        └── WRITE: TLS to IQService ──► Windows-native ops
              ├── group member add / remove   (entitlement grant / revoke)
              ├── move object to new OU       (leaver hygiene step)
              ├── enable / disable            (the leaver CONTROL — Lesson 56)
              └── [if Exchange in scope] mailbox enable/disable
                    via Exchange management (remote PowerShell)
```

| Operation | Mechanism | Notes |
| --- | --- | --- |
| Group aggregation | LDAP(S) search under group search DN(s) | Filter security groups: `(&(objectCategory=group)(groupType:1.2.840.113556.1.4.803:=2147483648))` — the bitwise match on the security-enabled bit |
| Membership on accounts | `memberOf` from account aggregation | **Direct only** — nesting and primary group are invisible here |
| Entitlement add / remove | IQService writes the group's `member` attribute | Driven by provisioning plans (certification revokes, leaver plans) |
| OU move | IQService move/rename of the object | DN changes — one more reason DN is not a correlation key |
| Mailbox enable / disable | IQService → Exchange remote PowerShell | Requires Exchange RBAC rights and tools reachability (Real-world setup) |
| Mailbox attribute reads | LDAP — Exchange stamps AD attributes (e.g. recipient type details) | Visible in aggregation even when provisioning is out of scope |

Design consequence: account search DNs and **group** search DNs are independent knobs. A perfectly scoped account aggregation with a group search DN pointed at the wrong OU gives you accounts whose `memberOf` values reference groups the entitlement catalog has never heard of — certifiable strings with no owner, no description, no risk rating.

---

## Real-world setup (outside IIQ)

Lesson 56's setup got you reads and user-object writes. Groups, OU moves, and Exchange each add real prerequisites. Execute these against a live domain in this order.

### Step 1 — Extend the service-account delegation to groups and moves

1. On the OU(s) holding in-scope groups (e.g. `OU=Groups,DC=meridiannb,DC=com`), delegate to `svc-iiq-ad`: **read group properties** and **write the `member` attribute** — nothing more. This enables entitlement add/remove without letting the account create or delete groups.
2. For leaver OU moves, the account needs delete rights in the *source* OUs (`OU=Employees`, `OU=Contractors`) and create-user rights in `OU=Terminated` — a move is a delete-here/create-there pair in ACL terms.
3. Re-export the ACE list for the binder. The examiner's question is "exactly what can this account change" — keep the answer current.

### Step 2 — Decide and verify group read scope

1. Inventory where in-scope groups actually live. Wire groups in a locked-down admin OU won't be found by a group search DN pointed at the general `OU=Groups`.
2. If any in-scope group is **universal** and you read via a Global Catalog, confirm membership attributes replicate as expected; when in doubt, aggregate groups from a full DC of the owning domain.

### Step 3 — Exchange prerequisites (only if mailbox provisioning goes in scope)

1. Grant the connector's Exchange operations account the **least Exchange RBAC role that works** — typically the built-in *Mail Recipients* management role, never Organization Management.
2. Ensure the **IQService host** can reach Exchange management: remote PowerShell to an Exchange server (WinRM over 80/443 to the Exchange PowerShell virtual directory, per your Exchange version's guidance). This is IQService→Exchange traffic — a new firewall line beyond Lesson 56's table.
3. Agree ownership in writing: Messaging owns mailbox databases, retention, and litigation hold; IIQ owns *when* a mailbox is created or disabled. Without that split on paper, the first failed mailbox creation becomes a two-team blame loop.

### Step 4 — Credentials and evidence

Any Exchange operations credential joins the vault alongside the Lesson 56 accounts — same rotation owner, same "never in the repo" rule. Update the network diagram from Lesson 53 with the IQService→Exchange path before requesting firewall changes.

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq` as `spadmin`
- [ ] `MNB-ActiveDirectory` exists (application from Lesson 56, or its shell-notes fallback)
- [ ] `MNB-AD-schema-correlation-56.md` on hand — search DNs and correlation table feed this lesson
- [ ] Checklist Exchange line still open — you will close it in Task 6

---

## Lab procedure

### Task 1 — OU design: search scopes and the Terminated decision

Search DNs are the connector's field of vision. In production this worksheet is signed by the Windows team before anyone touches the app, because a missed OU means ungoverned accounts.

1. Create `~/iiq-lab-data/connectors/ad/MNB-AD-OU-design-57.md` and record the populations:

| Population | OU (lab DN) | In aggregation scope? |
| --- | --- | --- |
| Employees | `OU=Employees,DC=meridiannb,DC=com` | Yes |
| Contractors | `OU=Contractors,DC=meridiannb,DC=com` | Yes — `raj.external` holds real access |
| Terminated | `OU=Terminated,DC=meridiannb,DC=com` | **Decide and write it down** |
| Service accounts | Separate OU — out of human JML | Excluded from this app's human scope |

2. Make the Terminated call explicitly. Including it lets aggregation *prove* disabled state (Samir's 514) at the cost of dormant-account noise; excluding it keeps certifications clean but forfeits that evidence. Meridian lab default: **include, with disabled accounts filtered out of certifications** — but the deliverable is a written choice with a reason, either way.
3. Primary path: confirm the account search DNs on the `MNB-ActiveDirectory` application match this table (Lesson 56 Task 5 set Employees + Contractors; add Terminated if you chose inclusion).

**Expected result:** OU file with all four rows, an explicit Terminated decision with rationale, and the app's search DNs matching it.

**If it fails:** No app UI in your lab image → the file alone carries the design; flag the app update as deferred.

### Task 2 — Configure group aggregation on the application (primary path)

This is where the entitlement catalog gets its AD entries. Without it, `memberOf` values are naked strings — nothing to certify, nothing to revoke.

1. Open `MNB-ActiveDirectory` → group schema (or equivalent menu path). Confirm/set: group native identity (commonly the group DN), `sAMAccountName` or `cn` as display, `description`, `groupType`.
2. Set the **group search DN**: `OU=Groups,DC=meridiannb,DC=com` (lab placeholder — production uses the Step 2 inventory).
3. Apply the security-only filter if your build exposes a group filter field: `(&(objectCategory=group)(groupType:1.2.840.113556.1.4.803:=2147483648))` — the bitwise test for the security-enabled bit, immune to misleading group names.
4. Note in the OU design file which mechanism your build uses for group data: a group object type on this application, a separate group aggregation task, or both.

**Expected result:** Group schema and group search DN saved; security-only filter recorded (in the app or, failing that, in the file).

**If it fails:** Filter syntax rejected → some builds want the filter on the aggregation task rather than the app; capture where yours accepts it rather than forcing it.

### Task 3 — Group-type policy and the wire personas

Policy before mechanics: write the sentence the certification design will quote, then seed the examples every later lesson reuses.

1. Write into the OU design file: *"Meridian certifies security groups; distribution lists are excluded from access certifications unless Risk explicitly opts one in."*
2. Record the example groups:

| Group CN | Type | Members (lab) | Governance |
| --- | --- | --- | --- |
| `MNB-Wire-Initiators` | Security | `priya.wire` | Certify; SoD leg 1 |
| `MNB-Wire-Approvers` | Security | `marcus.approve` | Certify; SoD leg 2 |
| `MNB-AllStaff-DL` | Distribution | everyone incl. `jordan.reed` | Exclude from access certs |

**Expected result:** Policy sentence plus the three-row table in the OU design file.

### Task 4 — Aggregate and verify entitlement promotion

Run the pipeline end to end: group objects in, ManagedAttributes out, memberships visible on cubes. This is the moment the wire SoD policy becomes enforceable.

1. Run `Aggregate MNB-ActiveDirectory` (with group aggregation enabled per Task 2), or your build's separate group aggregation task.
2. Confirm in the Entitlement Catalog: `MNB-Wire-Initiators` and `MNB-Wire-Approvers` exist as ManagedAttributes; assign owner (Risk for wire groups) and a description — an entitlement without a description is un-certifiable in practice.
3. Spot-check `priya.wire`: her cube's AD link shows `MNB-Wire-Initiators`. Confirm `MNB-AllStaff-DL` is absent from the catalog (the filter worked).

**Expected result:** Two wire groups in the catalog with owners; Priya's membership on her cube; no DLs promoted.

**If it fails:** Wire groups missing → group search DN doesn't cover their OU (widen it) before suspecting the filter. DLs present → filter not applied where your build evaluates it; re-check Task 2 step 3.

### Task 5 — The leaver sequence: disable before move

Storyboard the sequence you would defend to the examiner, in the order that survives partial failure. Every step must leave evidence even if the next step stalls.

1. Write the ordered leaver into the binder:

| Step | Action | Feature / mechanism | Evidence |
| --- | --- | --- | --- |
| 1 | **Disable account** | ENABLE via IQService | UAC 512 → 514 in next aggregation |
| 2 | Remove high-risk groups (`MNB-Wire-*`, admin groups) | PROVISIONING — `member` writes | Provisioning plan + empty `memberOf` |
| 3 | Optional: move to `OU=Terminated` | IQService move | New DN in aggregation |

2. Attach the SLA from Lesson 56's card: disable within 4 hours of the HR leaver aggregate.
3. Write the anti-pattern verbatim: *"OU move alone is not disable"* — and cite Samir's mock-exam finding as the reason it is written down.

**Expected result:** Three-step ordered sequence with evidence column, SLA, and the anti-pattern sentence.

### Task 6 — Exchange scope: a signed decision, not a default

Unowned scope creep is how mailbox tickets end up bouncing between IAM and Messaging. Close the checklist's Exchange line the way a control owner would.

1. Meridian lab decision: **Exchange = No for `MNB-ActiveDirectory` v1.** Write it as one dated line in the OU design file: *"Mailbox provisioning out of IIQ scope for MNB-ActiveDirectory v1 — owner: Messaging; revisit trigger: Messaging opt-in."*
2. Record what "Yes later" requires, so the future sprint starts from facts: Exchange RBAC role for the ops account, IQService→Exchange remote PowerShell reachability, mailbox-create attributes, and shared-mailbox delegation governance (the `amelia.brooks` / `payments-desk@` exposure from Concepts).
3. Note that mailbox-related AD attributes still *aggregate* read-only regardless — visibility without provisioning.

**Expected result:** One dated, owned scope line plus the "if yes later" prerequisites list.

### Task 7 — Nested-group certification stance

Decide before the first campaign — changing expansion strategy mid-cycle invalidates comparisons between campaigns.

1. Write the two failure modes: full nested expansion floods managers into rubber-stamping; direct-only hides inherited access like Jordan's transitive wire approval.
2. Adopt and record the Meridian stance: **certify direct membership; prohibit nesting into high-risk groups by policy; run a separate Risk-owned targeted review of high-risk group membership including any nested groups.**

**Expected result:** Stance paragraph in the OU design file naming both rejected extremes and the chosen middle path.

**If it fails:** First certification still too large → tighten to direct-only plus the privileged review; document the change and the date.

### Task 8 — Lab-without-live-target fallback (secondary path)

**Use this only if you have no live domain or the group UI is unavailable.** Tasks 1–7's design is the lesson; this preserves it as executable-later artifacts.

1. Consolidate into `MNB-AD-OU-design-57.md`: the group schema fields, group search DN, and the exact security-only filter string from Task 2.
2. Write the deferred verification block: *"Expected when live: `priya.wire` shows `MNB-Wire-Initiators`; catalog contains both wire groups and zero DLs. If it fails: check group search DN coverage first, filter second."*
3. Mark Task 4 as `design-complete / execution deferred (no live target)` in the Lesson 56 test plan.

**Expected result:** Every configuration value and expected outcome captured; a future engineer could execute Task 4 from the file alone.

### Task 9 — Application notes and CHANGELOG

Traceability is cheap now and priceless during the exam prep scramble.

1. Attach (or reference in the app description) the OU design file path and the group filter to `MNB-ActiveDirectory`.
2. Update the CHANGELOG: *"Lesson 57: OU scopes, group aggregation + security-only filter, leaver sequence, Exchange=No (v1), nested-group stance for MNB-ActiveDirectory."*

**Expected result:** App notes and CHANGELOG updated.

**If it fails:** UI field names differ from these instructions → capture your build's equivalents in the notes; never invent labels.

---

## Acceptance criteria

- [ ] `MNB-AD-OU-design-57.md` with Employees/Contractors/Terminated/service-account rows and an explicit, reasoned Terminated decision
- [ ] Group schema + group search DN configured (or captured in the fallback file) with the security-only `groupType` filter
- [ ] Group-type policy sentence and the three example groups recorded
- [ ] Entitlement promotion verified for `MNB-Wire-Initiators` / `MNB-Wire-Approvers` — or the deferred verification block written
- [ ] Leaver sequence: disable → group removal → optional OU move, with SLA and the "OU move alone is not disable" anti-pattern
- [ ] Exchange scope decision dated and owned; mailbox types and "if yes later" prerequisites noted
- [ ] Nested-group certification stance documented
- [ ] CHANGELOG updated

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Certifications flooded with mail lists | Group aggregation unfiltered — DLs promoted | Apply the `groupType` bitwise security filter; re-aggregate; purge DL ManagedAttributes |
| Wire groups absent from entitlement catalog | Group search DN doesn't cover the OU where they live | Inventory actual group locations; widen/add group search DNs — check this *before* blaming the filter |
| Group aggregation returns zero groups | Filter syntax error or filter applied at the wrong layer for your build | Test the filter with an `ldapsearch`/`ldp.exe` query; try the task-level filter field |
| Account in `OU=Terminated` still enabled | Leaver ran OU move without disable | Enforce sequence step 1; sweep Terminated for `userAccountControl` ≠ 514 as a detective control |
| Mailbox operation fails from IQService | Exchange RBAC role missing, or WinRM/remote PowerShell path blocked | Grant Mail Recipients role; open IQService→Exchange management path; or confirm Exchange=No and disable the operation |
| Manager certifies a bland ops group; wire access rides inside it | Nested group hides transitive membership (`memberOf` is direct-only) | Enforce the no-nesting-into-high-risk policy; run the Risk-owned membership review of `MNB-Wire-*` |

---

## Training binder evidence

- `MNB-AD-OU-design-57.md` — OU table with Terminated decision, group policy + example groups, filter string, nested stance
- Entitlement catalog screenshot showing both wire groups with owners (or the deferred verification block)
- `priya.wire` cube screenshot with `MNB-Wire-Initiators` (live path)
- Leaver sequence table with SLA and the anti-pattern sentence
- Dated Exchange scope line with owner
- CHANGELOG entry

**Examiner question:** *"Show me that terminated users are disabled — not merely moved to a Terminated OU — and show me who reviewed the wire-approver group's membership this year."*

---

## Knowledge check

1. Why do security groups belong in access certifications while distribution groups usually do not?
2. Is moving an account to `OU=Terminated` equivalent to disabling it? What attribute proves the difference?
3. How can `jordan.reed` hold effective wire-approval access that never appears on his certification, and what is Meridian's mitigation?
4. What does the filter `(groupType:1.2.840.113556.1.4.803:=2147483648)` do, and why filter on `groupType` rather than group names?
5. Which mailbox type carries hidden access grants even though nobody logs into it directly?
6. What is Meridian's v1 Exchange decision for `MNB-ActiveDirectory`, and what three prerequisites would flipping it require?

### Answers

1. Security groups have SIDs and appear in ACLs — they gate access; distribution groups only route mail. Certifying DLs floods managers and trains them to rubber-stamp.
2. No. Disable sets the ACCOUNTDISABLE bit — `userAccountControl` goes 512 → 514. An enabled account in Terminated is Samir's finding: offboarded-looking, fully usable.
3. Via nesting — a group he's directly in sits inside `MNB-Wire-Approvers`, and `memberOf` shows direct membership only. Mitigation: no nesting into high-risk groups by policy, plus a Risk-owned targeted review of high-risk group membership.
4. It bitwise-tests the security-enabled bit of `groupType`, selecting security groups only — names lie (DLs get converted; naming conventions drift), the bit does not.
5. The shared mailbox — delegated access (like `amelia.brooks` on `payments-desk@meridiannb.com`) grants read of everything in it and needs an owner and a review.
6. Exchange = No, owned by Messaging. Flipping requires: an Exchange RBAC role (e.g. Mail Recipients) for the ops account, IQService→Exchange remote PowerShell reachability, and a documented mailbox-create attribute set plus shared-mailbox delegation governance.

---

## Further reading

- [Microsoft Learn — Active Directory security groups](https://learn.microsoft.com/windows-server/identity/ad-ds/manage/understand-security-groups) — the authoritative treatment of group types, scopes, and nesting; the source for Task 3's policy language.
- [Microsoft Learn — Exchange Server documentation](https://learn.microsoft.com/exchange/) — search "recipient types" and "manage shared mailboxes" for the mailbox-type taxonomy from Concepts and the delegation model behind the shared-mailbox risk.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search "Active Directory connector group aggregation" and "Exchange provisioning" for your version's exact group-schema fields and mailbox operation prerequisites.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — practitioner threads on `groupType` filters, group search DN scoping, and IQService Exchange setups that fail in exactly the ways Troubleshooting predicts.
- [NIST SP 800-53 — Security and Privacy Controls](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) — AC-2 (account management) and AC-6 (least privilege) are the control language behind the leaver sequence and the delegation model; useful for writing findings responses in the examiner's dialect.

---

## Stretch lab

Design the nesting strategy for the `MNB-Wire-*` groups end to end: propose an AD structure that keeps them nesting-free, draft the detective query (an LDAP filter or PowerShell one-liner) that alerts when a *group* appears in their `member` attribute, and estimate the aggregation impact. Then draft the Exchange=Yes attribute list for a future Messaging sprint — mailbox database selection, retention policy tag, and the shared-mailbox delegation review design — so the v2 decision starts from a page, not a blank. Finally, map the wire group CNs to entitlement-dictionary codes so certifications display business names instead of CNs.

---

## Summary

- Group aggregation scope is a control: security groups (filtered by the `groupType` bit, not by name) become owned, certifiable ManagedAttributes; distribution lists stay out; nested access into high-risk groups is prohibited and separately reviewed.
- The leaver order is disable → remove high-risk groups → optional OU move — because "OU move alone is not disable," and `userAccountControl` 514 is the proof examiners accept.
- Exchange mailbox provisioning is an explicit, owned scope decision (No for v1 at Meridian), with the IQService-to-Exchange prerequisites written down before anyone flips it to Yes.

---

**Previous:** [Lesson 56 — Active Directory Connector](56-active-directory-connector.md)  
**Next:** [Lesson 58 — LDAP / OpenLDAP Connector](58-ldap-openldap-connector.md)
