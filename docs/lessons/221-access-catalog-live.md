# Lesson 221 — Build a Live Request Catalog

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~70 minutes  
**Prereq:** Lessons 210, 216, 220  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 35 / 10

> **Why:** A request catalog is only honest if every item in it actually provisions on a live target when granted — not a pretty list of things that were never wired end to end. Contractors and elevated employee access both land here, not in birthright.

## What this is

So far, access arrived via **birthright** (automatic roles) or **ops assignment**. Banks also need **self-service requests**: “I need Wire Initiator for my Q3 rotation.”

Lesson 220 already showed contractors are **excluded** from employee birthright. Elevated Wire access for employees is also **not** day-one birthright — both populations use this catalog.

In IIQ that surface is usually:

| Piece | What it is | In this estate |
| --- | --- | --- |
| **QuickLink** | Home-page shortcut | `MNB-QuickLink-Request-Access` → `accessRequest.jsf` |
| **DynamicScope** | Who sees the QuickLink | `Self Service` (`allowSelf="true"`) |
| **Requestable flag** | What appears *inside* the catalog | Bundles / entitlements with `requestable=true` |
| **IdentityRequest** | The ticket IIQ creates on submit | Id you need for Lesson 222 |

Nothing magical fills the catalog. If Wire Initiator isn’t requestable, Priya can’t find it. If CRM was never aggregation-tested, making it requestable invents a hollow button.

Classic 35 taught catalog design on static data; here every item must already provision for real — Lesson 222 will approve the request you leave pending.

## Know these

```text
Self Service DynamicScope
  → Request Access QuickLink visible to workforce
  → catalog = requestable Bundles / entitlements
  → submit + justification
  → IdentityRequest (pending)
  → approval work item (Lesson 222 wires Manager→Owner)
```


| Catalog item    | Backing object                           | Live proof it’s real                          |
| --------------- | ---------------------------------------- | --------------------------------------------- |
| Wire Initiator  | `MNB-Bundle-Wire-Initiator`              | `WIRE_INIT` on Wire/Core Banking (Lesson 216) |
| CRM access      | `CRM-Users` on `MNB-Salesforce-CRM-Live` | Aggregated in Lesson 210                      |
| Optional: Gitea | Keycloak group Bundle                    | Only if Lesson 213 SSO is live                |



| Term                          | Plain English                                       |
| ----------------------------- | --------------------------------------------------- |
| **Requestable**               | Appears in the access request UI for eligible users |
| **Birthright vs requestable** | Auto day-one vs must ask + get approved             |
| **Justification**             | Why you need it — auditors read this later          |
| **Work item**                 | Approval queue entry someone must act on            |
| **ManagedAttribute**          | Entitlement Catalog object — raw code + governance metadata (classic 10) |

**Entitlement dictionary metadata** (what managers and requesters actually see):

| Metadata | Purpose | Meridian example |
| --- | --- | --- |
| **Display name** | Human review in catalog / certs | Wire Portal — Initiate (not bare `WIRE_INIT`) |
| **Description** | What the power does | Create wire instructions |
| **Risk** | Campaign / SoD priority | critical for Wire; medium for CRM |
| **Owner** | Accountable business/IT owner | Wire → treasury owner; CRM → CRM owner |
| **Requestable** | Self-service catalog flag | CRM yes; break-glass / AWS_ADMIN-style **no** |

- **Wrong way:** Flagging something requestable that was never provisioning-tested — the catalog looks complete and grants nothing.
- **Wrong way:** Approving the request in this lesson — leave it pending so Lesson 222 has a live approval to work.
- **Wrong way:** Building catalog-only Bundles with no required entitlements / IT roles underneath.
- **Wrong way:** Leaving display name as the opaque code — managers rubber-stamp what they can’t read (classic 10).
- **Wrong way:** Making privileged / dual-control entitlements requestable without owner + risk set.



## Intent

- Confirm **Request Access** is visible to a normal workforce persona (not only admins).
- Make at least two live-provisioning entitlements genuinely requestable, with ManagedAttribute display/risk/owner where thin (classic 10).
- Submit a real Access Request as `priya.wire` with a real justification; capture the `IdentityRequest` id.
- Leave it **unapproved** on purpose for Lesson 222.



## Before you start

- [ ] Lesson 216: `MNB-Bundle-Wire-Initiator` exists and can provision `WIRE_INIT`
- [ ] Lesson 210: CRM `CRM-Users` group aggregated into Entitlement Catalog
- [ ] `priya.wire` can log in (pass-through `LabUser1!` or your seed password — Lesson 206 pattern)
- [ ] `helen.ross` available to confirm Self Service QuickLink visibility
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/221
```



## Do this



### Task 1 — Confirm Request Access for a normal persona

1. Log in as `helen.ross` / `LabUser1!` (or your seed password)
2. Find **Request Access** on the home page / menu (QuickLink)

- **Why:** proves `Self Service` scope includes workforce identities, not just `spadmin`.
- **Expect:** QuickLink visible.

If missing for Helen:

1. Confirm `MNB-QuickLink-Request-Access` exists (**Debug → QuickLink**, or import `config/QuickLink/MNB-QuickLink-Request-Access.xml`)
2. Fix **DynamicScope** / capabilities for `Self Service` before blaming Priya’s login

Screenshot under evidence.

### Task 2 — Confirm Wire Initiator is requestable (+ dictionary metadata)

1. Still as Helen (or as `spadmin`): open the role `MNB-Bundle-Wire-Initiator`
2. Confirm **requestable** = true (Attributes / options depending on UI)
3. Open **Applications → Entitlement Catalog** → find Wire’s `WIRE_INIT` (or the Bundle’s required entitlement)
4. Enrich / confirm ManagedAttribute metadata if thin:
   - Display name: e.g. `Wire Portal — Initiate`
   - Description: what initiate means
   - Risk: **critical** (or your build’s high tier)
   - Owner: a real identity (not blank / not only spadmin)
5. Open **Request Access**, search `wire`

- **Why:** role must be requestable *and* searchable; dictionary metadata is what managers/requesters read (classic 10).
- **Expect:** role listed with a human display name / description — not a bare code; not hidden / owner-only.

> **Tip:** If search finds nothing, check display name vs name, and whether the Bundle type is allowed in LCM request config.



### Task 3 — Make CRM access requestable

Pick one path:

**Path A — Entitlement Catalog**

1. **Applications → Entitlement Catalog** (or Manage → Entitlements)
2. Find `MNB-Salesforce-CRM-Live` / `CRM-Users`
3. Set display name / description if still opaque; risk (e.g. medium); owner if blank
4. Enable requestable / request options

**Path B — Small requestable Bundle** (if entitlement UI won’t flag it)

1. Create IT Bundle e.g. `MNB-Bundle-CRM-Users`
2. Add required entitlement `CRM-Users`
3. Set `requestable=true` + readable display name

- **Why:** Lesson 222’s catalog integrity rule — every item must provision on a live target; metadata makes the catalog examiner-ready.
- **Expect:** CRM item searchable in **Request Access** with a human-readable label.



### Task 4 — Optional third item (Gitea / IdP group)

If Lesson 213 Gitea SSO is live, create a lightweight requestable Bundle mapped to the relevant Keycloak group.

- **Why:** proves catalog design generalizes past the two pre-wired apps.
- **Expect:** third item searchable — or skip with a note if 213 isn’t done.



### Task 5 — Submit as Priya (the real requester)

1. Log out; log in as `priya.wire` / `LabUser1!`
2. Open **Request Access**
3. Search `wire` → select `MNB-Bundle-Wire-Initiator`
4. Justification (copy exactly or adapt):

```text
Onboarding to wire desk per manager Sanjay Kapoor — Q3 rotation
```

1. Submit

- **Why:** governance needs a named requester + business reason, not an admin click.
- **Expect:** request accepted; **no** auto-grant of the entitlement yet.



### Task 6 — Capture the IdentityRequest id

Note the `IdentityRequest` id from the UI (confirmation page, request history, or Manage Access Requests).

Write it under evidence:

```text
IdentityRequest id: _______________
Requester: priya.wire
Item: MNB-Bundle-Wire-Initiator
```

- **Why:** Lesson 222 opens *this* request — without the id you’ll hunt blindly.
- **Expect:** id written down.



### Task 7 — Do **not** approve yet

Even as `spadmin`, do **not** approve or force-provision this request.

- **Why:** Lesson 222 is built around fixing Manager→Owner routing and approving *this* pending item.
- **Expect:** request sits pending.



### Task 8 — Confirm a pending work item exists

As `spadmin`: **Manage Work Items** (or Home → Work Items).

Look for an approval item for Priya’s request. Optionally check Sanjay Kapoor (`MNB00006`) queue if manager routing is already partially wired.

- **Why:** proves the request is live in the work queue, not just a log line.
- **Expect:** an addressable work item — **or** note “auto-approved / no workflow” as a finding for Lesson 222 (you’ll attach `MNB-Workflow-Access-Approval` there).



## If it fails


| Symptom                            | Fix                                                                                                                              |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Request Access missing for Priya   | Compare Helen; fix `Self Service` DynamicScope population / capability                                                           |
| Wire role doesn’t appear in search | `requestable=true` alone may not be enough — check hidden/owner-only / LCM requestable types                                     |
| CRM entitlement can’t be flagged   | Wrap in a small IT Bundle (Path B)                                                                                               |
| Submission errors                  | Missing required provisioning-form field (e.g. OpenLDAP create fields) — complete form fields or fix Create scripts (Lesson 216) |
| No approval work item              | Request may have auto-approved with no workflow — Lesson 222 attaches `MNB-Workflow-Access-Approval`                             |
| Priya can’t log in                 | Fix pass-through / password from Lesson 206; don’t submit the request as spadmin “for her”                                       |




## You are done when

- [ ] At least two live-provisioning items are genuinely requestable
- [ ] Priya submitted Wire Initiator with justification
- [ ] You have the exact `IdentityRequest` id for Lesson 222
- [ ] Request left **unapproved**
- [ ] You can explain why Wire is requestable (not birthright) for employees *and* contractors



## Control note

- **Control:** Self-service access request catalog integrity
- **Owner:** IAM Ops (catalog curation) + app owners (entitlement scope)
- **SLA (lab):** Same session; production catalogs are reviewed on a recurring cadence to prune non-provisioning items
- **Evidence:** `~/iiq-lab-evidence/sandbox/221/` — catalog screenshots, IdentityRequest id, pending work item proof



## Quick check

1. Why must every catalog item already provision for real? → Lesson 222 depends on this request being fulfillable
2. What scope controls who sees Request Access? → The `Self Service` DynamicScope
3. Why leave the request unapproved here? → So Lesson 222 has a live approval to work
4. Birthright vs requestable — what’s the difference? → Auto day-one vs ask-and-approve
5. Name three ManagedAttribute fields beyond the raw code → Display name, risk, owner (also description / requestable)

## Feedback

Could you explain catalog integrity in one sentence (requestable ≠ wired)? If Wire didn’t appear in search, note whether `requestable` was true *and* whether the Bundle type is allowed in your LCM request config. If the catalog still showed bare `WIRE_INIT`, note whether you skipped display-name enrichment — classic 10 trap.

## Navigate

- Previous: [Lesson 220](220-contractor-loa-live.md)
- Next: [Lesson 222](222-approvals-and-mail.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)

