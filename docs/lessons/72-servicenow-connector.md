# Lesson 72 — ServiceNow Connector

**Level:** Intermediate  
**Track:** Connectors — Web APIs & SaaS  
**Time:** 90–120 min  
**Prereq:** Lesson 71 — Salesforce Native Connector; Lesson 38 (IdentityRequest tracking) for the ticket pattern  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (ServiceNow ITSM row)
- Repo: `lab-data/connectors/features-string-glossary.md`

---

## Learning objectives

You will be able to:

- Explain the ServiceNow access model — `sys_user`, `sys_user_group`, `sys_user_role` — and how group-inherited vs directly-assigned roles differ for governance
- Explain why `itil` and `admin` are high-risk roles and what an over-granted ITSM platform can do to a bank
- Distinguish ServiceNow's two hats — a **governed target** and a **fulfillment channel** — and keep them separate in design and evidence
- Perform the real-world setup: least-privilege integration user, `snc_read_only` plus scoped ACLs, OAuth application registry entry
- Create **MNB-ServiceNow** with a two-family entitlement taxonomy (groups + roles) and run Account Aggregation
- Design the ticket-integration pattern: when IIQ opens a ServiceNow ticket for manual fulfillment, and why a closed ticket is not revoke evidence

---

## Why this matters

**Business.** ServiceNow is Meridian's ITSM spine: incidents, changes, the service catalog, and the CMDB all live there. That makes it two things at once. It is a **target** — `jordan.reed` holds the `admin` role, and a ServiceNow admin can read every ticket (including ones containing credentials pasted by careless users), modify ACLs, and approve their own changes. And it is a **channel** — when IIQ cannot provision a system directly (the mainframe, a vendor portal), it opens a ServiceNow ticket for a human to do it. Confusing those two roles is the most common design mistake teams make with this connector.

**Control / audit.** The examiner will probe both hats separately: *"who holds admin on your ITSM platform and when was that certified?"* (target) and *"when access is fulfilled by ticket, how do you know the work was actually done?"* (channel). Your binder must answer each with its own evidence — an aggregation-backed certification for the first, a verify-after-close discipline for the second. This lesson builds both and keeps them apart.

---

## Concepts

### The ServiceNow access model — three tables that matter

ServiceNow is a database with a workflow engine on top; access control lives in a handful of system tables. Learn these names — the connector literally reads them:

| Table | What it holds | Real-life example at Meridian | Governance treatment |
| --- | --- | --- | --- |
| `sys_user` | People and service accounts | `jordan.reed`'s ServiceNow account, `active=true/false` | The account IIQ aggregates |
| `sys_user_group` | Assignment groups — who works which queues, who sits on CAB | `SN_CAB` (change advisory board), `SN_HR_FULFILLER` | Entitlement family 1 |
| `sys_user_role` | Named capabilities: `itil`, `admin`, `approver_user`… | `SN_ADMIN` (the `admin` role), `SN_ITIL` (the `itil` role) | Entitlement family 2 |
| `sys_user_grmember` | Group membership rows (user ↔ group) | Jordan in `SN_CAB` | How family 1 is read |
| `sys_user_has_role` | Role assignment rows — **each row records whether the role came via a group or was granted directly** | Jordan's `admin` row with no inheriting group | How family 2 is read |

The key mechanic: **groups carry roles.** Put a user in a group and they inherit every role attached to it. That is the governed norm — access flows through group membership, and reviewing groups reviews most access.

### Direct role assignment is the finding, not the norm

A role can also be granted **directly** to a user, bypassing every group. This is the exact ServiceNow parallel of a managed policy attached directly to an AWS user (Lesson 76): it escapes group-based review, it's usually a leftover from an incident or a go-live, and each one is a candidate finding. When aggregation shows `jordan.reed` holding `admin` *directly* — not inherited through any group — that single row justifies the connector. Your taxonomy therefore keeps **inherited** and **direct** roles distinguishable wherever the schema allows, and treats direct grants as high-visibility review items.

The naive approach — flatten everything into one "roles" list — hides precisely this signal. A reviewer sees `itil` on forty people and approves; they never learn that thirty-nine inherited it from `SN_ITSM_OPS` group membership and one was hand-granted at 2 a.m. during an outage and never removed.

### Why `itil` and `admin` are high risk

- **`itil`** is the working license of ITSM: create/update incidents, problems, and changes. In a bank, change records drive production deployments — someone with `itil` and bad intent can raise, self-shepherd, and document a malicious change to look routine. Risk tier: high.
- **`admin`** is platform god mode: modify ACLs, run background scripts, impersonate users, edit workflow. An `admin` can grant themselves anything and erase the evidence trail between your aggregation cycles. Risk tier: critical, non-requestable, certified every cycle.

Meridian's dictionary names: `SN_ADMIN` (the `admin` role, critical), `SN_ITIL` (the `itil` role, high), `SN_CAB` (change advisory board group, high), `SN_HR_FULFILLER` (HR fulfillment group, medium).

### Target vs fulfillment channel — two hats, two evidence chains

```
Hat 1: governed TARGET                    Hat 2: fulfillment CHANNEL
──────────────────────                    ──────────────────────────
MNB-ServiceNow application                Access request approved in IIQ
  aggregates sys_user, groups, roles        │ target has no connector
  certifies SN_ADMIN / SN_ITIL              ▼
  leaver: deactivate + strip              IIQ opens ServiceNow RITM
        │                                   │ human fulfills manually
        ▼                                   ▼
Evidence: Task Results,                   Evidence: ticket closed
certification decisions                   + POST-CLOSE VERIFICATION
                                          (re-agg or cube check — the
                                           ticket alone proves nothing)
```

A closed ticket says a human clicked "closed"; it does not prove the access changed. The channel pattern is a **compensating control**, always paired with verification. Keep the two hats in separate binder sections, separate design documents, and — critically — do not bolt ticket-integration configuration onto the account-governance application object.

---

## How it works

The connector talks to the ServiceNow **Table API** — a generic REST interface over any table — as a dedicated integration user, over TLS, using OAuth (preferred) or basic auth:

```
IdentityIQ (MNB-ServiceNow)
        │  OAuth client credentials (app registry) or basic over TLS
        ▼
https://meridiannb.service-now.com/api/now/table/...
        ├── GET sys_user            → account aggregation (paged)
        ├── GET sys_user_group      → group entitlements
        ├── GET sys_user_grmember   → memberships
        ├── GET sys_user_has_role   → role entitlements (inherited vs direct)
        └── PATCH sys_user (active=false), DELETE grmember rows → provisioning
```

| Operation | API behavior | IIQ behavior |
| --- | --- | --- |
| Account aggregation | Paged `GET /api/now/table/sys_user` with `sysparm_offset` / `sysparm_limit` | One account per `sys_user`; `user_name` as native identity |
| Entitlement aggregation | Group + role tables and their membership tables | Two entitlement families: groups and roles |
| Disable / enable | `PATCH` `active=false/true` | Disable/enable operations |
| Group revoke | Delete the `sys_user_grmember` row | Entitlement remove |
| Ticket creation (channel hat) | `POST` to incident/RITM tables | Workflow integration — a separate config, not this application |

Two behaviors to internalize. **Pagination:** the Table API returns results in pages; the connector walks `sysparm_offset` until exhaustion, so a "suspiciously round" account count (exactly 10,000) usually means pagination stopped early. **ACL filtering:** ServiceNow applies ACLs *per row and per field* and does so **silently** — an under-privileged integration user gets HTTP 200 with rows or fields quietly missing, not an error. Empty-but-successful aggregations are almost always an ACL problem, which is why the Real-world setup below is mostly about ACLs.

---

## Real-world setup (outside IIQ)

Read this even on the mock path. Better: ServiceNow gives away full **Personal Developer Instances (PDI)** free at [developer.servicenow.com](https://developer.servicenow.com/) — you can execute every step here for real.

### Step 1 — Integration user

1. Create `svc-iiq` in `sys_user`. Set **Web service access only** (the account can call APIs but never log into the UI) and exclude it from SSO/MFA policy — it authenticates via OAuth, not the IdP.
2. Vault the credential; no interactive password use, ever.

### Step 2 — Least-privilege roles and ACLs (phase 1: read)

1. Grant `snc_read_only` — a platform role that blocks all writes regardless of what else the user holds. This is your seatbelt.
2. Grant read ACLs on exactly the tables the connector needs: `sys_user`, `sys_user_group`, `sys_user_grmember`, `sys_user_role`, `sys_user_has_role`. Field-level: ensure `user_name`, `email`, `employee_number`, `active` are readable — remember, ACL denials are silent.
3. Phase 2 (provisioning) removes `snc_read_only` and adds scoped write ACLs on `sys_user.active` and `sys_user_grmember` — each addition security-reviewed, because a writable ITSM connector can deactivate the help desk.

### Step 3 — OAuth application registry entry

1. System OAuth → Application Registry → create an **OAuth API endpoint for external clients** (or equivalent menu path). Record client ID; vault the secret.
2. Prefer OAuth over basic auth: tokens are short-lived, revocable without a password change, and show up distinctly in the audit log.

### Step 4 — Governance records

Document: instance URL, integration user sys_id, roles/ACLs granted, OAuth client ID, phase 1/2 status, and the security sign-off. Note the ACL list explicitly — six months from now, "why can't the connector see employee_number?" is answered by this document.

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq` as `spadmin`; IdentityRequest tracking from Lesson 38 understood
- [ ] Decide your path: live PDI (free) or the mock fallback in Task 4
- [ ] No production ServiceNow credentials on lab machines
- [ ] Personas: `jordan.reed` (IT / platform admin), `helen.ross` (IAM lead, CAB), `samir.hassan` (leaver), `raj.external` (contractor)

---

## Lab procedure

### Task 1 — Split the two hats in writing

Every design mistake with this connector traces back to conflating target and channel, so the first artifact forces the separation before any configuration exists.

1. Write two binder headings: **Account governance (target)** and **Ticket fulfillment (channel)**.
2. Under target, list: `SN_ADMIN` certification, leaver deactivation, direct-role findings. Under channel, list: "fulfill mainframe access" RITM, break-glass requests, manual vendor-portal provisioning.
3. Add the rule sentence: *a closed ticket is never revoke evidence; verification on the target is.*

**Expected result:** Two labeled sections with examples — no mixed sentences.

### Task 2 — Create MNB-ServiceNow

In production this consumes the Step 1–3 outputs: instance URL, integration user, OAuth client. The connector form asks for exactly those.

1. Applications → Add New → **ServiceNow** (or equivalent menu path).
2. Connection section: instance URL `https://meridiannb.service-now.com` (lab/PDI: your instance URL), auth = OAuth client ID + secret placeholders noting "secret in vault" (basic auth as documented fallback).
3. Name `MNB-ServiceNow`; owner `helen.ross`; technical contact `jordan.reed`. Save.
4. Live PDI: click **Test Connection** — success proves TLS, OAuth token issuance, and at least `sys_user` read access.

**Expected result:** Application saved; live path shows Test Connection success.

**If it fails:** `401` means client ID/secret or the integration user credential is wrong. A success with zero visible users later means ACLs — go back to Step 2, not the connection settings.

### Task 3 — Schema and the two entitlement families

The schema must keep groups and roles as *separate* entitlement attributes, and preserve the inherited-vs-direct distinction — otherwise the Jordan finding disappears into a flat list.

1. Account schema: `user_name` (native identity), `email`, `employee_number`, `active`, multi-valued `groups` (entitlement), multi-valued `roles` (entitlement). If your connector version exposes role inheritance, carry `rolesDirect` separately; if not, document that direct-vs-inherited analysis happens via the `sys_user_has_role` table's inheritance column and note it as a follow-up report.
2. Group schema: `name` (native identity), `description`, `manager`.
3. Dictionary risk tiers: `SN_ADMIN` critical / non-requestable; `SN_ITIL` high; `SN_CAB` high; `SN_HR_FULFILLER` medium.
4. Correlation: `employee_number` ↔ identity `employeeId` primary; `email` fallback. **Create identities: OFF** — ServiceNow is a target; `MNB-HR` stays the only authoritative source.

**Expected result:** Schema with two entitlement families; four dictionary rows with risk tiers; create-identities disabled.

### Task 4 — Mock inventory (fallback: no live instance)

If you have no PDI, simulate the aggregation result so the downstream tasks still work. This is a fallback, not the lesson.

1. Create `~/iiq-lab-data/connectors/servicenow/MNB-ServiceNow-mock.csv`:

```csv
userName,email,employeeId,groups,rolesInherited,rolesDirect,active
jordan.reed,jordan.reed@meridiannb.com,MNB00092,SN_CAB,SN_ITIL,SN_ADMIN,true
helen.ross,helen.ross@meridiannb.com,MNB00001,SN_CAB,SN_ITIL,,true
raj.external,raj.external@meridiannb.com,MNB00093,,,SN_ITIL,true
samir.hassan,samir.hassan@meridiannb.com,MNB00094,SN_HR_FULFILLER,,,false
```

2. Shadow-aggregate via a DelimitedFile app (pipe-split the multi-valued columns; mark groups and both role columns as entitlements).
3. Read the seeded findings like an analyst: **Jordan** holds `SN_ADMIN` *directly* — no group carries it, classic outage leftover; **Raj** the contractor holds `SN_ITIL` directly with no group membership at all (who granted it, and why not through a group?); **Samir** is deactivated but still sits in `SN_HR_FULFILLER` — a half-finished leaver.

**Expected result:** Four mock accounts ready to aggregate; three findings written down.

### Task 5 — Account Aggregation

The Task Result is your continuous inventory of ITSM power — and the evidence a certification will lean on.

1. Tasks → New → Account Aggregation: `MNB-ServiceNow-Account-Aggregation`. Run (live or shadow).
2. Spot-check cubes: `jordan.reed` shows both role families and the direct `SN_ADMIN`; `samir.hassan` shows `active=false` with the lingering group.
3. Live path: verify the account count is *not* suspiciously round — pagination truncation masquerades as success.

**Expected result:** Task Result success; Jordan and Samir spot-checks pass.

**If it fails:** Zero rows with HTTP 200 → ACLs on `sys_user` (silent filtering). Partial fields empty → field-level ACLs.

### Task 6 — The leaver pattern

ServiceNow leavers have the same shape as every SaaS leaver, plus one twist: fulfiller group residue quietly keeps tickets routing to a person who no longer exists.

1. Storyboard termination of an IT staffer, in order, with reasons:
   1. **Remove groups** (`SN_CAB`, fulfiller groups) — stops ticket routing and strips inherited roles in one move.
   2. **Remove direct roles** — the grants that groups never carried (`SN_ADMIN` in Jordan's case) need explicit revocation.
   3. **Deactivate** (`active=false`) — ends login.
   4. **Re-aggregate** — IIQ shows `active=false`, empty groups and roles: the evidence.
2. Attach the Lesson 34 SLA: critical roles (`SN_ADMIN`) within 15 minutes of the HR term event; deactivation within 1 hour.
3. Note the Samir anti-pattern: deactivation without group removal leaves assignment queues pointing at a ghost — an operational failure, not just an audit one.

**Expected result:** Four-step leaver card with SLAs and the ghost-queue footnote.

### Task 7 — Ticket-integration design note (the channel hat)

Now design the other hat — on paper only, and deliberately separate from the `MNB-ServiceNow` application.

1. Decision rule for when IIQ opens a ticket instead of provisioning directly: the target has no connector (mainframe RACF pre-Lesson 8x, vendor portals), the operation needs human judgment (break-glass), or the connector lacks `PROVISIONING` in its featuresString.
2. Required ticket fields: IdentityRequest ID, identity, application, entitlement, action (grant/revoke), due date per SLA.
3. The verification rule, verbatim in the binder: *the IdentityRequest stays open past ticket closure until re-aggregation (or a cube check) confirms the access actually changed.* Closed-but-unverified is the channel's signature failure mode.
4. Note the config boundary: ticket integration lives in workflow/integration configuration, never bolted onto the account-governance application.

**Expected result:** One-page ticket-integration design with decision rule, field list, and the verify-after-close rule.

### Task 8 — Aggregation schedule and operational guardrails

1. Propose daily Account Aggregation at 05:30, after the HR feed, so correlation targets exist first.
2. Failure paging: IAM on-call plus `jordan.reed` as platform contact.
3. Count floor: alert if accounts drop more than 10% week-over-week — the classic symptom of an ACL change silently filtering the integration user's view.

**Expected result:** Schedule/SLA card with the count-floor alert documented.

### Task 9 — Examiner drill and residual risk

*"Who administers your ITSM platform, and how do you know ticket-fulfilled access was actually granted or removed?"*

1. Target answer: entitlement catalog + latest aggregation for `SN_ADMIN` holders; certification decisions on that population; Jordan's direct-grant finding and its disposition.
2. Channel answer: the Task 7 design — ticket fields tie back to IdentityRequest, and closure is verified by re-aggregation before the request completes.
3. Record `RR-SN-ADMIN-01`: *Holders of the `admin` role can modify ACLs and grant access between aggregation cycles, invisible until the next run. Compensating controls: minimal admin population (target ≤3), critical-tier certification, and platform audit-log review by the ServiceNow team.* Owner: `jordan.reed`.

**Expected result:** Both answers written; residual risk logged with owner.

---

## Acceptance criteria

- [ ] Target vs channel split written, with the verify-after-close rule
- [ ] Real-world setup understood: integration user, `snc_read_only` + table ACLs, OAuth app registry
- [ ] `MNB-ServiceNow` created; schema carries groups and roles as separate entitlement families; create-identities off
- [ ] Aggregation evidence (live or mock) with the three seeded findings identified
- [ ] Four-step leaver card with SLAs; ticket-integration one-pager complete
- [ ] Schedule/count-floor card, examiner answers, and `RR-SN-ADMIN-01` recorded

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `401 Unauthorized` on Test Connection | Wrong OAuth client ID/secret, or integration user credential invalid | Re-check the application registry entry; rotate and re-vault the secret |
| Aggregation succeeds but returns zero rows | ACLs silently filtering `sys_user` for the integration user | Grant read ACLs per Step 2 — this is an ACL problem, not a connection problem |
| Some fields (e.g. `employee_number`) come back empty | Field-level ACLs deny read on specific columns | Add field-level read ACLs; remember denials return 200, not errors |
| `429 Too Many Requests` during large aggregations | Instance rate/transaction quotas throttling the integration user | Slow the connector's page rate; schedule off-peak; coordinate with the platform team |
| Account count suspiciously round, then stalls | Pagination stopped early (`sysparm_offset` handling or instance query limit) | Verify paging config; compare against a direct Table API count |
| Ticket closed but access unchanged on target | Fulfillment skipped or done wrong; no verification step | Enforce the Task 7 rule: IdentityRequest completes only after re-aggregation confirms the change |

---

## Training binder evidence

- Two-hat split page with the verify-after-close rule
- Real-world setup worksheet (integration user, roles/ACLs, OAuth client ID — no secrets!)
- Aggregation Task Result + Jordan/Samir cube screenshots and findings write-up
- Leaver card with SLAs
- Ticket-integration one-pager; schedule/count-floor card
- Examiner answers + `RR-SN-ADMIN-01`

---

## Knowledge check

1. What is the governance difference between a role inherited via a group and a role assigned directly, and which Lesson 76 concept does it parallel?
2. Why are `itil` and `admin` risk-tiered high and critical respectively?
3. Why does an under-privileged integration user produce empty results instead of errors?
4. In the leaver sequence, why is removing groups alone insufficient for Jordan?
5. Why is a closed RITM not revoke evidence, and what completes it?
6. What does `RR-SN-ADMIN-01` admit, and what compensates?

### Answers

1. Direct assignment bypasses group-based review — the exact parallel of a managed policy attached directly to an AWS IAM user; both are candidate findings, so the taxonomy must keep them distinguishable.
2. `itil` can create and shepherd change records that drive production deployments; `admin` is platform god mode — ACLs, scripts, impersonation — and can self-grant anything.
3. ServiceNow ACLs filter per row and per field silently, returning HTTP 200 with data quietly missing.
4. His `SN_ADMIN` is a direct grant no group carries; group removal strips only inherited roles, so direct roles need explicit revocation.
5. Ticket closure proves a human clicked a button; the IdentityRequest completes only after re-aggregation or a cube check confirms the access actually changed on the target.
6. Admins can grant access between aggregation cycles invisibly; compensated by a minimal admin population, critical-tier certification, and platform audit-log review.

---

## Further reading

- [ServiceNow product documentation](https://docs.servicenow.com/) — search "Table API" for the REST interface behind aggregation, and "Access control rules" for the silent ACL-filtering behavior in the troubleshooting table.
- [ServiceNow Developer site](https://developer.servicenow.com/) — request a free Personal Developer Instance and run this entire lesson live; also search "REST API Explorer" to watch the exact calls the connector makes.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search "ServiceNow connector" for the version-specific application guide, and "Service Desk integration" for the ticket-channel configuration kept separate from this application.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — field reports on ServiceNow ACL surprises, pagination limits, and ticket-integration patterns.
- [NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/final) — see the AC (Access Control) and CM (Configuration Management) families; change-management access like `itil` sits exactly at their intersection.

---

## Stretch lab

Sketch (do not build) the LCM workflow branch: if a target application's featuresString lacks `PROVISIONING`, create a ServiceNow RITM carrying the Task 7 field set and park the IdentityRequest awaiting a ticket-close signal plus verification. Then draft the SoD candidate: `SN_ADMIN` combined with `AWS_ADMIN` or `GRP_CLOUD_ADMINS` (Lesson 76) concentrates change control and cloud infrastructure in one person — route the draft to Risk via `marcus.approve` with `helen.ross` as policy owner proxy; design only, no activation.

---

## Summary

- ServiceNow access is three tables — users, groups, roles — with roles flowing through groups as the norm and direct role assignment as the finding, mirroring AWS direct policy attachment.
- The connector reads the Table API as a least-privilege integration user whose ACLs silently shape what IIQ can see — empty results are an ACL symptom, and the count-floor alert is your tripwire.
- ServiceNow wears two hats: a governed target (aggregate, certify, deactivate) and a fulfillment channel (ticket + verify-after-close) — separate designs, separate evidence, never conflated.

---

**Previous:** [Lesson 71 — Salesforce Native Connector](71-salesforce-native-connector.md)  
**Next:** [Lesson 73 — Okta Connector](73-okta-connector.md)
