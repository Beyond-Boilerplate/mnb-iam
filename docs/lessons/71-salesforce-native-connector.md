# Lesson 71 — Salesforce Native Connector

**Level:** Intermediate  
**Track:** Connectors — Web APIs & SaaS  
**Time:** 90–120 min  
**Prereq:** Lesson 70 — SCIM Custom Schemas; Lesson 52 selection matrix; Lesson 15 (`MNB-Salesforce-CRM` CSV onboard) for contrast  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (Salesforce CRM row)
- Repo: `lab-data/connectors/features-string-glossary.md`
- Repo: `lab-data/apps/MNB-Salesforce-CRM.csv` (legacy file extract for contrast)

---

## Learning objectives

You will be able to:

- Explain the Salesforce access model — Profiles, Permission Sets, Roles, Public Groups — and say precisely which of them are governable entitlements
- Recognize the "everyone is System Administrator" anti-pattern and explain why it is the classic Salesforce audit finding
- Perform the real-world setup: Connected App, OAuth flow (JWT bearer or client credentials), least-privilege integration user, IP policy, sandbox-first rollout
- Create **MNB-Salesforce** field by field, with a profile/permission-set entitlement taxonomy and documented correlation
- Run an Account Aggregation and read the results like an analyst, including the license angle
- Design the Salesforce leaver pattern — deactivate plus strip permission sets — and explain why deletion is not an option
- Upgrade Meridian from the Lesson 15 CSV extract to native aggregation with a coexistence and retirement plan

---

## Why this matters

**Business.** Meridian's relationship managers live in Salesforce: the commercial pipeline, customer contact data, and credit memos attached to opportunities. In Lesson 15 you governed a single `CRM` entitlement from a quarterly CSV. Here is what that file could never show you: after the CRM implementation project wrapped, `jordan.reed` — who was only supposed to help with data migration — was left holding the **System Administrator profile**. A sysadmin in Salesforce can read and export every customer record in the org, modify sharing rules, and grant access to anyone. The CSV said Jordan had "CRM". Nobody knew he had the keys.

**Control / audit.** When the examiner asks *"who can export your commercial book of business, and when was that list last reviewed?"*, the answer must come from a continuous inventory of profiles and permission sets, not a stale extract of a single flag. Native aggregation gives you that inventory nightly, makes each grant a certifiable entitlement, and produces Task Results as evidence. This lesson builds exactly that, and writes the retirement plan for the CSV.

---

## Concepts

### The Salesforce access model — four things that look alike and aren't

Salesforce access is famously confusing because four different constructs all *feel* like "groups". They are not interchangeable, and modeling them wrong in IIQ produces certifications that review the wrong thing:

| Salesforce construct | What it actually controls | Cardinality | Governance treatment |
| --- | --- | --- | --- |
| **Profile** | Baseline permissions: object CRUD, field access, login policy, app visibility | **Exactly one per user** | Single-valued entitlement — the base grant |
| **Permission Set** | Additive permissions layered on top of the profile | Zero to many per user | Multi-valued entitlement — the modern, reviewable grant |
| **Role** | Position in the **data visibility hierarchy** (who sees whose records) | Zero or one per user | Account attribute for context — it is *not* a permission grant |
| **Public Group** | A sharing bucket used in sharing rules and folder access | Zero to many | Attribute or entitlement depending on what it shares — decide per group |

The modern Salesforce design principle, and the one Meridian adopts: **profiles should be minimal and boring; real access rides on permission sets.** `amelia.brooks` holds the plain `Standard User` profile; her ability to view credit data comes from a permission set. That is what makes her access grantable, certifiable, and revocable one grant at a time — you cannot partially revoke a profile.

A role is the trap for newcomers. "Commercial Lending Manager" sounds like a permission, but the Role hierarchy only widens *record visibility* (managers see subordinates' records). Someone with a lofty role and a minimal profile still can't delete anything. Certifying roles as if they were permissions wastes reviewer attention on the wrong object; ignoring roles entirely misses a data-exposure dimension. Meridian's answer: aggregate the role as a context attribute, certify profiles and permission sets as entitlements.

### "Everyone is System Administrator" — the classic finding

Implementation partners and rushed admins grant the **System Administrator profile** because it makes every error message go away. Then the project ends and nobody walks it back. It is the single most common Salesforce audit finding, and it is structural: because a profile is a single opaque bundle, reviewers see one line — "System Administrator" — instead of the hundreds of permissions inside it, and they rubber-stamp it.

The naive governance approach — treat "has CRM access yes/no" as the entitlement, as the Lesson 15 CSV did — cannot even see this. The native connector surfaces the profile as its own entitlement, so `SFDC_SYSADMIN` becomes a **critical, non-requestable** dictionary entry, and Jordan's leftover grant becomes a visible finding in your first aggregation.

### Licenses — why governance saves real money here

Every **active** Salesforce user consumes a license, and Salesforce licenses are priced per seat per month. A deactivated user frees the seat. This gives your leaver process an unusual ally: finance. When `samir.hassan` left and his Salesforce user stayed active for four months, Meridian paid for four months of a seat that was also an audit finding. Track `IsActive` in your schema and your aggregation becomes a license-reclamation report as well as a control.

### Deactivate, never delete — the lifecycle Salesforce forces on you

Salesforce **cannot delete users**. Ever. Every record in the org carries `CreatedById` / `LastModifiedById` audit fields pointing at users; deleting a user would orphan that history, so the platform simply doesn't allow it. The governance consequences:

- Your leaver primitive is **deactivate** (`IsActive = false`), optionally preceded by **freeze** (an instant login block you can apply while the full deactivation checklist runs).
- Deactivated users linger in the org forever, so your aggregation filter and certification scoping must handle them deliberately — aggregate them (they are evidence) but exclude them from active-access reviews.
- Record ownership: a deactivated user can still *own* accounts and opportunities. Ownership transfer is a business step in the leaver runbook, not an IIQ provisioning step — write it down or the CRM team gets surprised.

---

## How it works

The SailPoint Salesforce connector calls the Salesforce **REST and SOAP APIs** as a dedicated **integration user**, authenticating via OAuth through a **Connected App** — Salesforce's registration object for external clients. No password sits in IIQ config in a modern setup; the connector holds a certificate (JWT bearer flow) or a client secret (client credentials flow) and exchanges it for short-lived access tokens.

```
IdentityIQ (MNB-Salesforce)
        │  Connected App consumer key + JWT (cert) or client secret
        ▼
Salesforce OAuth token endpoint ──► short-lived access token
        │                            (acting as svc-iiq@meridiannb.com)
        ▼
Salesforce REST / SOAP APIs
        ├── query User, Profile                    → account aggregation
        ├── query PermissionSet, PermissionSetAssignment → entitlement aggregation
        ├── update User (IsActive=false)           → deactivate (leaver)
        └── create/delete PermissionSetAssignment  → entitlement grant / revoke
```

| Operation | API behavior | IIQ behavior |
| --- | --- | --- |
| Account aggregation | SOQL query over `User` (paged) | One account per user; `Username` as native identity |
| Entitlement aggregation | `Profile`, `PermissionSet` + assignments | `profile` single-valued + `permissionSets` multi-valued entitlements |
| Create | `User` insert — **consumes a license immediately** | New-hire provisioning (phase 2) |
| Disable / enable | `User` update `IsActive` | Disable/enable operations — there is **no delete** |
| Permission set add/remove | `PermissionSetAssignment` create/delete | Entitlement add/remove in a provisioning plan |

Two behaviors worth internalizing: every API call spends against the org's **24-hour API request quota** (shared across all integrations — a runaway aggregation can starve other systems), and OAuth tokens expire, so a long aggregation must re-authenticate mid-run; the connector handles this, but `INVALID_SESSION_ID` errors in logs usually mean the token or session policy is fighting it.

---

## Real-world setup (outside IIQ)

This is what you would do against a live org. Read it even on the mock path — the knowledge check and the examiner assume you know it. A free [Salesforce Developer Edition](https://developer.salesforce.com/) org lets you do all of it for real.

### Step 1 — Integration user, minimum profile

1. Create `svc-iiq@meridiannb.com` as a dedicated user. Do **not** give it System Administrator — the connector that hunts over-privilege must not be over-privileged itself.
2. Assign a minimal profile plus a purpose-built permission set containing only: **API Enabled**, **View All Users**, and (phase 2 only) **Manage Users** and **Assign Permission Sets**.
3. Exclude it from SSO enforcement if your org forces SSO for humans — the integration user authenticates via the Connected App, not the IdP.

### Step 2 — Connected App

1. Setup → App Manager → New Connected App (or equivalent menu path). Name it `MNB-IdentityIQ`.
2. Enable OAuth. Choose the flow:
   - **JWT bearer** (recommended): upload a certificate; the connector signs a JWT with the private key. No shared secret ever leaves the vault.
   - **Client credentials** (simpler, newer): consumer key + secret, with a designated "run as" user.
3. Scopes: `api` (and `refresh_token` only if your flow needs it). Nothing broader.

### Step 3 — OAuth policy: pre-authorize, don't prompt

Set the Connected App's permitted-users policy to **admin-approved users are pre-authorized**, then assign the integration user's profile or permission set to the app. This is the step everyone forgets — without it, JWT bearer fails with `invalid_grant` because the user never "approved" the app.

### Step 4 — IP policy

Salesforce enforces login IP ranges per profile. Either add the IIQ server's egress IPs to the integration profile's trusted ranges (preferred — tight and auditable) or set the Connected App's IP relaxation to "Relax IP restrictions" (weaker; document the risk acceptance if you choose it).

### Step 5 — Sandbox-first rollout

Enterprises never point a new connector at production first. Clone the config against a **sandbox** (a copy of the org), run aggregation there, validate counts and the entitlement catalog, then repoint to production with change approval. Sandboxes refresh from production, so your test data is realistic.

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq` as `spadmin`
- [ ] Legacy `~/iiq-lab-data/apps/MNB-Salesforce-CRM.csv` readable for contrast (Lesson 15)
- [ ] Decide your path: live org (free Developer Edition) or the mock fallback in Task 5
- [ ] No production Salesforce credentials on lab machines — placeholders or a throwaway dev org only
- [ ] Personas: `amelia.brooks` (RM / business owner), `kai.nguyen`, `jordan.reed`, `sofia.torres`, `samir.hassan`

---

## Lab procedure

### Task 1 — Contrast: what the Lesson 15 CSV can never tell you

Ground the upgrade in specifics before building anything — the same discipline Lesson 76 applies to the AWS CSV.

1. Open `~/iiq-lab-data/apps/MNB-Salesforce-CRM.csv`. It carries `userName, email, employeeId, entitlement, accountStatus` with a single `CRM` value — a yes/no flag.
2. List what it structurally cannot contain: which **profile** each user holds (Jordan's sysadmin is invisible), permission set assignments, `IsActive` drift between exports, license consumption, anything newer than the last export.
3. Write the upgrade rationale: native aggregation makes profiles and permission sets first-class entitlements and closes the Jordan gap.
4. Coexistence plan: `MNB-Salesforce-CRM` (the CSV app) stays until two clean native aggregation cycles, then is retired (Task 8). Certifications referencing the `CRM` entitlement migrate to the new taxonomy.

**Expected result:** Upgrade rationale paragraph + coexistence plan in the binder.

### Task 2 — Design decisions and naming

Renaming an application after certifications reference it is painful, so a production team decides everything on a design card first.

1. Application name: `MNB-Salesforce` (the native app; the legacy CSV app keeps its `MNB-Salesforce-CRM` name until retirement). Owner: `helen.ross`; business owner: `amelia.brooks`.
2. Entitlement taxonomy, `SFDC_` prefix: `SFDC_SYSADMIN` (System Administrator profile — critical, non-requestable), `SFDC_RM_STANDARD` (relationship-manager permission set — medium, requestable with approval), `SFDC_CREDIT_VIEW` (credit-data permission set — high, approval by credit risk).
3. Scope: all users including deactivated ones (they are leaver evidence); role hierarchy aggregated as a context attribute only.
4. Record the auth design decision: JWT bearer flow, cert in the vault, sandbox-first.

**Expected result:** Design card covering name, owners, taxonomy with risk tiers, scope, and auth flow.

### Task 3 — Create the application

This is where the Real-world setup outputs (consumer key, cert or secret, integration username) get consumed. The connector form asks for exactly those artifacts.

1. Applications → Add New → **Salesforce** (or equivalent menu path).
2. Fill the connection section:
   - **Login/instance URL**: `https://login.salesforce.com` (sandbox: `https://test.salesforce.com`)
   - **Integration user**: `svc-iiq@meridiannb.com`
   - **Consumer key / credential**: from the Connected App (lab: placeholder noting "cert in vault")
3. Name `MNB-Salesforce`; owner `helen.ross`. Save.
4. Live org: click **Test Connection** — success proves the whole chain: Connected App → OAuth token → API access as the integration user.

**Expected result:** Application saved; live path shows Test Connection success.

**If it fails:** `invalid_grant` means the integration user isn't pre-authorized on the Connected App or the server clock is skewed (JWT timestamps) — fix in Salesforce Setup, not IIQ. `INVALID_LOGIN` with client credentials means key/secret or the "run as" user is wrong.

### Task 4 — Schema and correlation

The schema decides what governance can see. If `profile` isn't an entitlement here, Jordan's sysadmin never becomes a certifiable line item.

1. Account schema: `Username` (native identity), `Email`, `FederationIdentifier`, `IsActive`, `Profile` as a **single-valued entitlement attribute**, `permissionSets` as a **multi-valued entitlement attribute**, `UserRole` as a plain attribute, `LastLoginDate` for dormancy hunting.
2. Correlation, in documented order: `FederationIdentifier` ↔ identity `employeeId` (Meridian stamps the HR id into FederationIdentifier for SSO — the robust key), falling back to `Username`/`Email` ↔ identity `email`. Note the fallback risk: usernames must be unique across *all* Salesforce orgs globally, so some orgs suffix them (`amelia.brooks@meridiannb.com.prod`) — email correlation breaks there; FederationIdentifier doesn't.
3. **Create identities: OFF.** Salesforce is a target; `MNB-HR` remains the only authoritative source. An unknown Salesforce user must surface as an uncorrelated account (Lesson 19), not become a person.

**Expected result:** Schema shows two entitlement attributes (one single-, one multi-valued), correlation order written down, create-identities disabled.

### Task 5 — Mock inventory (fallback: no live org)

If you have no org, simulate what aggregation would return so every downstream step still works. This is a fallback, not the lesson.

1. Create `~/iiq-lab-data/connectors/salesforce/MNB-Salesforce-mock.csv`:

```csv
userName,email,employeeId,profile,permissionSets,active
amelia.brooks@meridiannb.com,amelia.brooks@meridiannb.com,MNB00098,Standard User,SFDC_RM_STANDARD|SFDC_CREDIT_VIEW,true
kai.nguyen@meridiannb.com,kai.nguyen@meridiannb.com,MNB00096,Standard User,SFDC_RM_STANDARD,true
sofia.torres@meridiannb.com,sofia.torres@meridiannb.com,MNB00095,Standard User,SFDC_RM_STANDARD,true
jordan.reed@meridiannb.com,jordan.reed@meridiannb.com,MNB00092,System Administrator,,true
samir.hassan@meridiannb.com,samir.hassan@meridiannb.com,MNB00094,Standard User,SFDC_CREDIT_VIEW,false
```

2. Shadow-aggregate via a DelimitedFile app (pipe-split `permissionSets` as the multi-valued entitlement; `profile` as single-valued entitlement).
3. Read the seeded stories like an analyst: **Jordan** still holds System Administrator from the migration project (the finding); **Samir** is deactivated but `SFDC_CREDIT_VIEW` was never removed — a half-finished leaver that also documents why deactivation alone isn't the full pattern.

**Expected result:** Five mock accounts ready to aggregate; the Jordan and Samir findings written down.

### Task 6 — Account Aggregation

Aggregation is your continuous inventory — the Task Result *is* the audit evidence, and here it doubles as a license report.

1. Tasks → New → Account Aggregation: `MNB-Salesforce-Account-Aggregation`. Run (live or shadow).
2. Spot-check cubes: `amelia.brooks` shows both permission sets; `jordan.reed` shows the sysadmin profile; `samir.hassan` shows `active=false` with a lingering permission set.
3. Compare against the legacy CSV app: the delta (Jordan's privilege, Samir's residue) is the retirement argument written in data.
4. Count active users vs licensed seats — note the reclamation opportunity. Schedule: nightly, after HR aggregation so correlation targets exist first.

**Expected result:** Task Result success; three spot-checks pass; delta note vs the CSV app in the binder.

**If it fails:** Live `REQUEST_LIMIT_EXCEEDED` → the org's daily API quota is spent; reschedule off-peak and check what else is consuming it. Shadow zero rows → path/delimiter/multi-valued split config.

### Task 7 — The leaver pattern: deactivate + strip

Salesforce cannot delete users, so your leaver story has to be airtight about what deactivation does and does not accomplish. Walk it end-to-end.

1. Storyboard termination of an RM, in order, with reasons:
   1. **Freeze** the user (instant login block) if the termination is hostile — buys time while the rest runs.
   2. **Remove permission sets** (`SFDC_CREDIT_VIEW` first) — produces per-grant revoke evidence and guarantees no access if the account is ever reactivated.
   3. **Deactivate** (`IsActive=false`) — ends login and mail-merge visibility, frees the license.
   4. **Re-aggregate** — IIQ shows `active=false` and empty permission sets: the evidence.
2. Business step outside IIQ: transfer record ownership (accounts, opportunities) to the manager — note it in the runbook with the CRM team as owner.
3. Attach the SLA from Lesson 34's rapid-offboarding drill: permission sets within 15 minutes of the HR term event; deactivation within 1 hour.
4. Anti-pattern note: teams that only deactivate (skipping step 2) recreate the Samir situation — reactivation for any reason silently restores full access.

**Expected result:** Four-step leaver card with SLAs, the ownership-transfer footnote, and the reactivation anti-pattern noted.

### Task 8 — Features, phases, and CSV retirement

1. Check `features-string-glossary.md` / the ConnectorRegistry entry: expect `PROVISIONING` and `ENABLE`; `PASSWORD` is largely irrelevant at Meridian because Salesforce login federates through Okta (Lesson 73) — passwords live at the IdP.
2. Phase plan: phase 1 = aggregation + deactivate; phase 2 = permission set provisioning and user creation (each addition security-reviewed — a writable CRM connector can grant credit-data access).
3. Retirement plan for the `MNB-Salesforce-CRM` CSV app: after two clean native cycles, mark it inactive, migrate certifications from the `CRM` entitlement to the `SFDC_*` taxonomy, archive the final Task Result, delete the export job.

**Expected result:** Feature notes with a two-phase plan and a dated CSV retirement plan.

### Task 9 — Examiner drill and residual risk

*"Who can export your commercial customer data, and prove a terminated RM lost access."*

1. Write the three-artifact answer: (1) entitlement catalog showing `SFDC_SYSADMIN` and `SFDC_CREDIT_VIEW` holders from the latest aggregation, (2) the leaver's provisioning plan / workflow log showing permission set removal and deactivation, (3) the post-termination account detail: `active=false`, permission sets empty.
2. Record `RR-SFDC-SHARE-01`: *Record-level access granted through sharing rules, public groups, and report/dashboard folder permissions is not fully visible to this connector; profile and permission set governance does not cover ad-hoc record sharing.* Compensating control: periodic org-health review with the Salesforce admin team. Owner: `amelia.brooks`.

**Expected result:** Written proof steps + residual risk logged with owner.

---

## Acceptance criteria

- [ ] Upgrade rationale and CSV coexistence/retirement plan written
- [ ] Real-world setup understood: Connected App, OAuth flow choice, integration user permissions, IP policy, sandbox-first
- [ ] `MNB-Salesforce` created; schema has profile (single-valued) + permissionSets (multi-valued) entitlements; create-identities off
- [ ] Aggregation evidence (live or mock) with the Jordan and Samir findings identified
- [ ] Four-step leaver card (freeze → strip → deactivate → re-aggregate) with SLAs and ownership-transfer note
- [ ] Feature/phase notes, examiner proof steps, and `RR-SFDC-SHARE-01` recorded

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `invalid_grant` on Test Connection | Integration user not pre-authorized on the Connected App, or JWT clock skew | Set admin-approved pre-authorization and assign the user's profile/permission set to the app; sync server time |
| `INVALID_SESSION_ID` mid-aggregation | Token expired or session settings revoke it | Let the connector re-authenticate; review the org's session timeout for the integration profile |
| `REQUEST_LIMIT_EXCEEDED` (HTTP 403/429-style) | Org's 24-hour API quota exhausted — shared across all integrations | Reschedule off-peak; find the other consumer; never fix by widening quota blindly |
| Login works in browser, API fails from IIQ | Login IP ranges on the integration profile exclude the IIQ server | Add IIQ egress IPs to the profile's trusted ranges (preferred over blanket IP relaxation) |
| Permission sets aggregate empty | Integration user lacks View All Users / query rights, or the schema attribute isn't marked entitlement | Fix the integration permission set; mark `permissionSets` as the multi-valued entitlement and re-aggregate |
| `LICENSE_LIMIT_EXCEEDED` on user create | No free seats — deactivated leavers were never processed | Run the leaver backlog; deactivation frees licenses (Task 7) |

---

## Training binder evidence

- Upgrade rationale + delta note vs the Lesson 15 CSV app
- Design card (naming, owners, taxonomy with risk tiers, auth flow)
- Real-world setup worksheet (Connected App name, flow, scopes, IP decision — no secrets!)
- Aggregation Task Result + Jordan/Samir cube screenshots
- Leaver card with SLAs and ownership-transfer footnote
- Examiner proof steps + `RR-SFDC-SHARE-01`

---

## Knowledge check

1. A user can hold how many profiles, and how many permission sets? Why does that shape the IIQ schema?
2. Why is a Salesforce Role *not* an entitlement in Meridian's design?
3. Why can't your leaver runbook delete a Salesforce user, and what is the primitive instead?
4. In the leaver sequence, why remove permission sets even though deactivation already blocks login?
5. What does the Connected App + JWT bearer design keep out of IIQ configuration entirely?
6. What access does `RR-SFDC-SHARE-01` admit this connector cannot fully see?

### Answers

1. Exactly one profile (single-valued entitlement) and zero-to-many permission sets (multi-valued entitlement) — the schema mirrors that cardinality so each is certifiable correctly.
2. Roles control record *visibility* via the hierarchy, not permissions; Meridian aggregates the role as a context attribute and certifies profiles/permission sets instead.
3. Salesforce cannot delete users because audit fields on every record reference them; the leaver primitive is deactivate (`IsActive=false`), optionally preceded by freeze.
4. Reactivation for any reason would silently restore all access; stripping grants first produces per-entitlement revoke evidence and defends in depth.
5. A long-lived shared password/secret — the connector signs a JWT with a vaulted certificate and exchanges it for short-lived tokens.
6. Record-level access via sharing rules, public groups, and report/dashboard folder permissions.

---

## Further reading

- [Salesforce Developer documentation](https://developer.salesforce.com/docs) — search "OAuth 2.0 JWT Bearer Flow" and "REST API Developer Guide" for the exact auth flow and API surface behind this connector.
- [Salesforce Help](https://help.salesforce.com/) — search "permission sets" and "deactivate users" for the vendor's own guidance that profiles should be minimal and access should ride on permission sets.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search "Salesforce connector" for the version-specific application guide, supported operations, and featuresString reference.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — real-world Connected App, `invalid_grant`, and API-quota troubleshooting threads for this connector.
- [Salesforce Trailhead](https://trailhead.salesforce.com/) — search "Data Security" module for the profile/permission-set/role/sharing model taught interactively; useful to send to app owners who must certify this access.

---

## Stretch lab

Draft (do not activate) an SoD candidate pairing `SFDC_SYSADMIN` with `WIRE_INIT` — a CRM sysadmin who can also initiate wires can manufacture and monetize customer data in one seat; route the draft to Risk via `marcus.approve`. Then explore **permission set groups** (bundles of permission sets): design how Meridian would model a group as a single requestable item while still aggregating the underlying sets for certification granularity.

---

## Summary

- Salesforce governance hinges on the access model: one profile as the base entitlement, permission sets as the additive grants, roles as visibility context — and "everyone is System Administrator" as the finding the taxonomy exists to catch.
- The connector authenticates as a least-privilege integration user through a Connected App (JWT bearer preferred), and every design choice — scopes, IP ranges, sandbox-first — happens in Salesforce Setup before IIQ ever connects.
- The leaver primitive is freeze → strip permission sets → deactivate → re-aggregate, because Salesforce never deletes users; the CSV app from Lesson 15 retires after two clean native cycles.

---

**Previous:** [Lesson 70 — SCIM Custom Schemas](70-scim-custom-schemas.md)  
**Next:** [Lesson 72 — ServiceNow Connector](72-servicenow-connector.md)
