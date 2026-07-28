# Lesson 74 — Google Workspace Connector

**Level:** Intermediate  
**Track:** Connectors — Web APIs & SaaS  
**Time:** 90–120 min  
**Prereq:** Lesson 73 — Okta Connector  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv`
- Repo: `lab-data/connectors/features-string-glossary.md`

---

## Learning objectives

You will be able to:

- Explain the Google Workspace object model (users, groups, Org Units, licenses) and how each maps into IdentityIQ
- Perform the real-world Google Cloud setup: project, Admin SDK API, service account, domain-wide delegation, and least-privilege scopes
- Create and configure **MNB-Google-Workspace** field by field, including schema and correlation
- Run an Account Aggregation and interpret what the connector actually fetched
- Design and defend the suspend-first leaver pattern for Workspace to an examiner
- Complete the lesson with or without a live Google tenant (mock fallback provided)

---

## Why this matters

**Business.** Meridian runs collaboration on Google Workspace: Gmail, Calendar, Drive, and Google Groups. When `sofia.torres` moved from Commercial Lending to Marketing last year, nobody removed her from `GRP_FINANCE_DRIVES`. Six months later she could still open credit memos she had no business reading. That is not a hypothetical — group memberships in collaboration suites are the single most common form of access creep, because they are granted casually ("add her to the drive") and reviewed never.

**Control / audit.** When the OCC examiner asks *"show me how a terminated employee loses access to email and shared documents, and prove it,"* your answer cannot be "IT does it manually." It has to be: IdentityIQ aggregates Google accounts nightly, the leaver workflow removes sensitive groups and suspends the account, and the next aggregation shows `suspended=true` — with Task Results as evidence. This lesson builds exactly that story.

---

## Concepts

### The Google Workspace object model

Before touching IIQ, understand what Google actually stores. Google Workspace (formerly G Suite) is organized around a **domain** (`meridiannb.com`) containing four object types that matter for governance:

| Google object | What it is | Real-life example at Meridian |
| --- | --- | --- |
| **User** | An account keyed by `primaryEmail` | `sofia.torres@meridiannb.com` — mailbox, Drive, Calendar |
| **Group** | A mailing list that doubles as an access-control list | `GRP_FINANCE_DRIVES` grants access to the finance Shared Drives |
| **Org Unit (OU)** | A folder in a tree that controls *policy* (2FA, app availability, session length) | `/Contractors` forces shorter sessions and blocks Takeout |
| **License** | A SKU assignment (Business Plus, Enterprise) | Contractors get Frontline; employees get Business Plus |

The critical distinction: **groups grant access to things; OUs apply policy to people.** A user lives in exactly one OU but can be in many groups. Teams new to Google constantly confuse these — they try to control Drive access with OUs (impossible) or apply security policy with groups (only partially possible).

### Why groups must be entitlements

In IIQ terms, a Google group membership behaves exactly like an AD group: it is discrete, grantable, revocable, and access-bearing. So the connector should surface `groups` as a **multi-valued entitlement attribute**, which makes each group a `ManagedAttribute` you can risk-rate, certify, and revoke through a provisioning plan.

The naive alternative — treating groups as a plain string attribute — means no entitlement catalog entry, no certification line item, and no revoke button. When the examiner asks who reviewed `GRP_FINANCE_DRIVES` this year, you would have nothing.

### Why the OU is an attribute, not an entitlement

OU placement (`/Employees`, `/Contractors`, `/Suspended`) is a single-valued state, not a grant. Model it as an **account attribute** you can read for correlation context and *write* during lifecycle events (a leaver moves to `/Suspended`). You do not certify OU membership; you certify the groups.

### Suspended vs deleted — the banking answer

Google offers two ways to end access: **suspend** (account frozen, data retained, license still consumed) and **delete** (account and data destroyed after a grace window). Banks suspend first, always:

- Legal hold and e-discovery need the mailbox and Drive contents intact.
- A wrongful-termination reversal is a one-click unsuspend, not a data-recovery incident.
- Suspension is instantly effective for access removal — the user cannot log in.

Deletion happens later, on a documented retention schedule, usually 30–90 days after termination. Your leaver pattern is therefore: **remove sensitive groups → move to `/Suspended` OU → suspend → verify by aggregation.**

---

## How it works

The SailPoint Google Workspace connector talks to the **Admin SDK Directory API** using a Google Cloud **service account** with **domain-wide delegation (DWD)**. That phrase deserves unpacking because it is the part engineers get wrong:

- A **service account** is a non-human Google Cloud identity with a JSON key pair. By itself it can access nothing in your Workspace domain.
- **Domain-wide delegation** is a Workspace admin setting that says: "this service account may impersonate users in my domain, but only for these OAuth scopes."
- The connector impersonates a **super admin user** (e.g. `svc-iiq-admin@meridiannb.com`) and calls the Directory API as that admin, limited to the delegated scopes.

```
IdentityIQ (MNB-Google-Workspace)
        │  JSON key + admin email to impersonate
        ▼
Google OAuth token endpoint ──► short-lived access token
        │                        (scoped: directory.user, directory.group, ...)
        ▼
Admin SDK Directory API
        ├── GET /users        → account aggregation
        ├── GET /groups       → group (entitlement) aggregation
        ├── PUT /users/{key}  → suspend, OU move, attribute update
        └── members insert/delete → group grant / revoke
```

| Operation | API behavior | IIQ behavior |
| --- | --- | --- |
| Account aggregation | Paged `users.list` for the domain | One account per user, `primaryEmail` as native identity |
| Group aggregation | `groups.list` + `members.list` | Managed attributes + memberships on accounts |
| Provision create | `users.insert` | New hire account with OU placement |
| Suspend / restore | `users.update` `suspended=true/false` | Disable / enable operations |
| Group add / remove | `members.insert` / `members.delete` | Entitlement add / remove in provisioning plan |

One consequence worth remembering: because auth is delegation-based, **the connector is exactly as powerful as the scopes you delegate**. Delegate read-only scopes and provisioning fails with 403s; delegate everything and you have created a domain-takeover credential. Least privilege is decided in the Google admin console, not in IIQ.

---

## Real-world setup (outside IIQ)

This is what you would actually do against a live tenant. Read it even if you use the mock fallback — the knowledge check and the examiner both assume you know it.

### Step 1 — Google Cloud project and API

1. In [Google Cloud Console](https://console.cloud.google.com/), create a project, e.g. `mnb-iam-connector`.
2. Enable the **Admin SDK API** for the project (APIs & Services → Library → Admin SDK API → Enable).

### Step 2 — Service account and key

1. IAM & Admin → Service Accounts → Create: `sa-identityiq@mnb-iam-connector.iam.gserviceaccount.com`.
2. Create a **JSON key** and download it once. Treat it like a domain admin password: vault it (CyberArk / Secret Manager), never commit it, rotate it on your key-rotation schedule.
3. Note the service account's **Client ID** (a long number) — you need it for delegation.

### Step 3 — Domain-wide delegation (Workspace admin console)

1. In [admin.google.com](https://admin.google.com/) → Security → Access and data control → API controls → **Domain-wide delegation** → Add new.
2. Paste the service account Client ID and delegate only the scopes the connector needs:

```text
https://www.googleapis.com/auth/admin.directory.user
https://www.googleapis.com/auth/admin.directory.group
https://www.googleapis.com/auth/admin.directory.group.member
https://www.googleapis.com/auth/admin.directory.orgunit
```

Aggregation-only deployments can use the `.readonly` variants of each — start there and widen when you enable provisioning.

### Step 4 — Impersonation account

1. Create `svc-iiq-admin@meridiannb.com` as a dedicated admin user. Prefer a **custom admin role** limited to user/group management over the Super Admin role.
2. Exclude it from user-facing licenses and from certifications-of-humans (it belongs in your service-account inventory instead — Lesson 20 patterns).

### Step 5 — Record the design decisions

Before configuration, an enterprise team writes down: which OU subtree is in scope, whether contractors aggregate, which groups are sensitive, and who owns the app. You will do exactly this in Task 1.

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq` as `spadmin`; Okta boundary concepts from Lesson 73 clear
- [ ] Decide your path: live Google tenant (test domain) or the mock fallback in Task 4
- [ ] No production Google admin keys on lab machines — lab uses placeholders or a disposable test tenant
- [ ] Domain `@meridiannb.com` used in all mock data

---

## Lab procedure

### Task 1 — Design decisions and naming

Every production connector starts with a design card, because renaming an application after certifications reference it is painful. Decide now, change never.

1. Application name: `MNB-Google-Workspace`. Owner: `helen.ross`; collaboration business owner: `sofia.torres`.
2. Scope decision: aggregate the whole domain; contractors included (they hold Drive access too — excluding them is the classic blind spot).
3. Write the OU strategy: `/Employees`, `/Contractors`, `/Suspended`. OU = account attribute; groups = entitlements.
4. Sensitive group list for risk-rating later: `GRP_WIRE`, `GRP_FINANCE_DRIVES`; broad group: `GRP_ALL_STAFF`.

**Expected result:** A design card in your binder covering name, owners, scope, OU strategy, and sensitive groups.

### Task 2 — Create the application

In production this is where the Step 1–4 outputs (JSON key, admin email) get consumed. The connector form asks for exactly those artifacts.

1. Applications → Add New → **Google Apps / Google Workspace** (or equivalent menu path).
2. Fill the connection section:
   - **Domain / customer**: `meridiannb.com`
   - **Admin email (impersonated user)**: `svc-iiq-admin@meridiannb.com`
   - **Service account key**: upload/paste the JSON key (lab: placeholder text noting "key in vault")
3. Owner `helen.ross`. Save.
4. If you have a live test tenant, click **Test Connection** — a success here proves the whole delegation chain (key → token → impersonation → API).

**Expected result:** Application object saved; live path shows Test Connection success.

**If it fails:** `unauthorized_client` means DWD is missing or the Client ID/scopes don't match — fix in admin.google.com, not IIQ. `403 Not Authorized` usually means the impersonated user lacks admin rights.

### Task 3 — Schema and correlation

The schema decides what governance can see. Missing `suspended` here means your leaver evidence never materializes.

1. Open the account schema. Confirm/set: `primaryEmail` (native identity), `givenName`, `familyName`, `orgUnitPath`, `suspended`, `lastLoginTime`, and multi-valued `groups` marked as the **entitlement attribute**.
2. Group schema: `email` (native identity), `name`, `description`.
3. Correlation: Google has no employeeId by default, so correlate `primaryEmail` ↔ identity `email`, with a documented fallback plan (Google custom schema field carrying `employeeId` is the robust production answer — note it as a follow-up).
4. **Create identities: OFF.** Google is a target; `MNB-HR` remains the only authoritative source.

**Expected result:** Schema shows `groups` as entitlement, `suspended` present, create-identities disabled.

### Task 4 — Mock inventory (fallback: no live tenant)

If you have no tenant, simulate what the aggregation *would* return so every downstream step still works. This is a fallback, not the lesson.

1. Create `~/iiq-lab-data/connectors/google/MNB-Google-Workspace-mock.csv`:

```csv
primaryEmail,employeeId,orgUnitPath,groups,suspended
sofia.torres@meridiannb.com,MNB00095,/Employees,GRP_ALL_STAFF|GRP_FINANCE_DRIVES,false
amelia.brooks@meridiannb.com,MNB00098,/Employees,GRP_ALL_STAFF,false
raj.external@meridiannb.com,MNB00093,/Contractors,GRP_ALL_STAFF|GRP_WIRE,false
samir.hassan@meridiannb.com,MNB00094,/Suspended,,true
```

2. Create a shadow DelimitedFile app pointing at it (pipe-split the `groups` column as multi-valued entitlement), or attach the file to `MNB-Google-Workspace` if your build allows a file-based test mode.
3. Note the two seeded stories: Raj the contractor holds `GRP_WIRE` (finding!), and Samir demonstrates a completed suspend pattern.

**Expected result:** Four mock accounts ready to aggregate; Raj and Samir stories understood.

### Task 5 — Account Aggregation

Aggregation is your continuous inventory — the Task Result *is* the audit evidence.

1. Tasks → New → Account Aggregation: `MNB-Google-Workspace-Account-Aggregation`.
2. Run (live or against the shadow app). Record accounts scanned/created and any errors.
3. Open `sofia.torres` — confirm her cube shows the Google account with both groups; open `samir.hassan` — confirm `suspended=true` is visible.
4. Propose a schedule: nightly, after the HR aggregation, so correlation targets exist first.

**Expected result:** Task Result success; Sofia's groups and Samir's suspension visible on cubes.

**If it fails:** Live 403 → check delegated scopes include `admin.directory.group.member`. Shadow zero rows → path/delimiter/multi-valued split config.

### Task 6 — The leaver suspend pattern

Now build the story you'll tell the examiner. Walk it end-to-end, don't just name it.

1. Storyboard the sequence for a terminated employee, in order and with reasons:
   1. **Remove sensitive groups** (`GRP_WIRE`, `GRP_FINANCE_DRIVES`) — kills document/system access even if later steps stall.
   2. **Move to `/Suspended` OU** — applies lockdown policy and makes state visible in Google admin views.
   3. **Suspend the user** — blocks all login; mail flow stops.
   4. **Re-aggregate** — IIQ now shows `suspended=true` and empty sensitive groups: the evidence.
2. Attach the SLA from Lesson 34's rapid-offboarding drill (sensitive groups within 15 minutes of HR term event; suspend within 1 hour).
3. Deletion note: account deleted at day 60 per retention policy, after legal-hold check — outside IIQ's SLA but inside the runbook.

**Expected result:** A four-step suspend runbook card with SLAs and the deletion footnote.

### Task 7 — featuresString and provisioning readiness

1. Check the connector registry entry / `features-string-glossary.md`: expect `ENABLE` (suspend/restore) and `PROVISIONING`; note that `PASSWORD` is often irrelevant because Meridian federates Google login through Okta (Lesson 73) — passwords live at the IdP.
2. Record which operations you would enable in phase 1 (aggregation + suspend) vs phase 2 (full create/group provisioning) — enterprises stage this.

**Expected result:** Feature notes with a two-phase enablement plan.

### Task 8 — Examiner question drill

*"Prove that a terminated employee lost access to the finance Shared Drives."*

Write the three-artifact answer: (1) provisioning plan / workflow log showing `GRP_FINANCE_DRIVES` removal, (2) post-termination Task Result, (3) the account detail showing `suspended=true` and the group absent.

**Expected result:** Written proof steps in the binder.

### Task 9 — Residual risk

Honest programs write down what the connector does *not* cover.

Record `RR-GW-DRIVE-01`: *Shared Drive memberships granted directly to users (outside groups) are invisible to this connector and need separate unstructured-data governance.* Follow-up owner: `sofia.torres`.

**Expected result:** Residual risk logged with owner.

---

## Acceptance criteria

- [ ] Design card: name, owners, scope, OU strategy, sensitive groups
- [ ] Real-world setup steps (project → SA → DWD → impersonation) understood and documented
- [ ] `MNB-Google-Workspace` created; schema has `groups` entitlement + `suspended`; create-identities off
- [ ] Aggregation evidence (live or mock) with Sofia/Samir spot-checks
- [ ] Four-step suspend runbook with SLAs
- [ ] Feature notes, examiner proof steps, and `RR-GW-DRIVE-01` recorded

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `unauthorized_client` on Test Connection | DWD missing, or Client ID / scopes mismatch | Re-add delegation in admin.google.com with exact scopes |
| `403 Not Authorized` on API calls | Impersonated user lacks admin role | Grant custom admin role to `svc-iiq-admin` |
| Groups aggregate empty | `group.member` scope not delegated, or domain/customer field wrong | Add member scope; verify domain value |
| OU move fails during provisioning | `orgunit` scope missing or OU path typo | Delegate orgunit scope; paths are case-sensitive and start with `/` |
| Password operations fail | Users federated via Okta SSO | Expected — manage passwords at the IdP, disable password feature |
| Contractor appears in `/Employees` | Joiner playbook never set OU | Fix create-provisioning policy to set `orgUnitPath` by `employeeType` |

---

## Training binder evidence

- Design card (naming, owners, scope, OU/group strategy)
- Real-world setup worksheet (project, SA client ID, delegated scopes — no keys!)
- Aggregation Task Result + Sofia/Samir cube screenshots
- Suspend runbook card with SLAs
- Examiner proof steps + `RR-GW-DRIVE-01`

---

## Knowledge check

1. Why must Google groups be modeled as entitlements rather than a plain account attribute?
2. What two things does domain-wide delegation bind together, and where is it configured?
3. Why does Meridian suspend rather than delete on termination?
4. In the leaver sequence, why remove sensitive groups *before* suspending?
5. Why might PASSWORD features be irrelevant for this connector at Meridian?
6. What access does `RR-GW-DRIVE-01` say this connector cannot see?

### Answers

1. Entitlements become ManagedAttributes — certifiable, risk-rated, revocable via provisioning plans; plain attributes get none of that.
2. A service account's Client ID and a set of OAuth scopes; configured in the Google Workspace admin console under API controls.
3. Legal hold / e-discovery needs data retained; suspension removes access instantly and is reversible; deletion follows the retention schedule later.
4. Defense in depth — group removal kills document access even if the suspend step fails or stalls, and it produces its own revoke evidence.
5. Meridian federates Google login through Okta, so passwords are owned by the IdP, not Google.
6. Shared Drive memberships granted directly to individual users, outside of groups.

---

## Further reading

- [Google Admin SDK Directory API overview](https://developers.google.com/admin-sdk/directory/v1/guides) — the API surface the connector actually calls; skim users, groups, and orgunits sections.
- [Google: Control API access with domain-wide delegation](https://support.google.com/a/answer/162106) — the authoritative DWD setup steps from Step 3 above.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search "Google Workspace connector" for the version-specific application guide and featuresString reference.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — real-world DWD and scope troubleshooting threads for this connector.
- [NIST SP 800-63B — Digital Identity Guidelines](https://pages.nist.gov/800-63-3/sp800-63b.html) — background on federated authentication, relevant to the "password lives at the IdP" decision.

---

## Stretch lab

Google supports **custom user schemas** — define one carrying `employeeId`, and redesign correlation to use it instead of email (survives name-change email rewrites). Then draft a Shared Drive governance note: treat Drive-access groups as certifiable entitlements owned by data stewards, and propose a targeted certification (Lesson 45 pattern) for `GRP_FINANCE_DRIVES` holders.

---

## Summary

- Google governance hinges on the object model: groups are entitlements, OUs are policy attributes, suspension is the leaver primitive.
- The connector's power equals its delegated scopes — least privilege is decided in the Google admin console via domain-wide delegation.
- The four-step suspend runbook (groups → OU → suspend → re-aggregate) plus Task Results is the examiner-ready evidence chain.

---

**Previous:** [Lesson 73 — Okta Connector](73-okta-connector.md)  
**Next:** [Lesson 75 — M365 & SharePoint Online](75-m365-sharepoint-online.md)
