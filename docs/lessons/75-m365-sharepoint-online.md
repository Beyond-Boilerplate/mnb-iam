# Lesson 75 — M365 & SharePoint Online Connectors

**Level:** Intermediate  
**Track:** Connectors — Web APIs & SaaS  
**Time:** 90–120 min  
**Prereq:** Lesson 74 — Google Workspace; Lesson 59 — Entra ID strongly recommended  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (Office 365 / SharePoint Online rows)
- Repo: `lab-data/connectors/features-string-glossary.md`

---

## Learning objectives

You will be able to:

- Explain the Microsoft 365 layering (Entra ID → M365 services → SharePoint sites) and why it needs **two or three separate IIQ applications**
- Perform the real-world Entra app registration: Graph API permissions, admin consent, certificate vs client secret
- Create **MNB-M365** and **MNB-SharePoint-Online** with correct schema, entitlement, and correlation choices
- Distinguish M365 group membership, license assignment, and SharePoint site permissions as three different governance objects
- Design the dual-app leaver pattern (mailbox, groups, sites) and its evidence chain
- Complete the lesson with or without a live Microsoft tenant (mock fallback provided)

---

## Why this matters

**Business.** Meridian's board packets, credit files, and HR investigations all live in SharePoint Online sites; mail and Teams run on M365. Last quarter, an internal review found that `marcus.approve` — an approver who transferred out of the credit committee — still had access to the Board site because his access came from a *site-level* SharePoint group nobody governs. That is the M365 pattern in a nutshell: access accumulates in layers (directory group, M365 group, site permission) and each layer has a different owner and a different blind spot.

**Control / audit.** Examiners ask two questions here: *"Who can read the board materials?"* and *"Show me that leavers lose mailbox and site access."* If your governance stops at Entra ID groups, you cannot answer the first question, because SharePoint sites can grant access outside directory groups entirely. Separate, scoped IIQ applications — with distinct certification owners — are how you answer both.

---

## Concepts

### The Microsoft layering problem

Microsoft 365 is not one system; it is a stack, and access can be granted at every layer:

| Layer | Object | Who typically grants it | Example at Meridian |
| --- | --- | --- | --- |
| Directory | Entra ID security group | IT | `SG_ALL_EMPLOYEES` drives SSO app assignment |
| Collaboration | **M365 group** (Team/Outlook group) | Any team owner | `M365_CREDIT_COMMITTEE` = Teams team + shared mailbox + a SharePoint site |
| Application | **SharePoint site permission** (site group or direct grant) | Site owners | `Board Site Members` added directly, no directory group at all |
| Licensing | License SKU / service plan | IT | `SPE_E3` decides whether the mailbox even exists |

The trap: an M365 group *automatically* provisions a SharePoint site, but a SharePoint site does **not** require an M365 group. Site owners can share with anyone, at file level, silently. This is why "we certify Entra groups" is an incomplete control — and why this lesson creates SharePoint as its own application.

### Why two (or three) IIQ applications

| System of record | IIQ application | Connector (matrix) | Cert owner |
| --- | --- | --- | --- |
| Cloud directory (users, security groups) | `MNB-Entra` (Lesson 59) | Azure Active Directory / Entra | IT / IAM |
| Mailboxes, M365 groups, licenses | `MNB-M365` | Microsoft Office365 | Collaboration ops |
| SharePoint sites and site groups | `MNB-SharePoint-Online` | Microsoft SharePoint Online | Data stewards |

One application "for Microsoft" would force a single owner to certify everything from group membership to site sharing — nobody is competent to review all of it, so the certification becomes rubber-stamping. Splitting by system of record gives each certification a reviewer who actually understands the access. This is the same principle you applied to OUs vs groups in Google (Lesson 74), scaled up a layer.

### Licenses: entitlement or attribute?

A license SKU (`SPE_E3`) gates service access *and* costs real money, so treat license assignments as **entitlements** when you want them requestable/certifiable (contractor gets E1, employee gets E3), or as attributes if licensing is purely automated by group-based licensing in Entra. Decide once, document it; Meridian's lab stance is group-based licensing in Entra, so licenses appear as read-only attributes in `MNB-M365` and the *license-granting groups* are the certified objects.

### The leaver problem is a dual-app problem

Terminating `samir.hassan` requires action in both systems, in order: revoke SharePoint site entitlements (fast, targeted), remove M365 groups (kills Teams/shared mailboxes), disable sign-in at Entra (blocks everything new), then convert the mailbox to a **shared mailbox** or apply litigation hold per retention policy — mail data, like Google data, is never just deleted at a bank.

---

## How it works

Both connectors authenticate to **Microsoft Graph** (SharePoint connector may also use SharePoint REST/CSOM depending on version) as an **Entra app registration** using client credentials:

```
IdentityIQ
   ├── MNB-M365 ───────────────┐
   └── MNB-SharePoint-Online ──┤  tenant ID + client ID + cert/secret
                               ▼
                Entra ID token endpoint ──► app-only access token
                               │
                               ▼
                     Microsoft Graph API
                       ├── /users, /users/{id}/licenseDetails
                       ├── /groups, /groups/{id}/members
                       └── /sites, site permissions (SPO scope)
```

| Operation | Graph behavior | IIQ behavior |
| --- | --- | --- |
| Account aggregation | Paged `/users` with `$select` | Account per user, UPN as native identity |
| Group aggregation | `/groups` filtered to M365 groups + members | Entitlements + memberships |
| Site aggregation (SPO app) | Sites + site groups + members | Site permissions as entitlements |
| Disable | `accountEnabled=false` (note: this is directory state — coordinate with `MNB-Entra` ownership) | Disable operation |
| Group add/remove | `/groups/{id}/members/$ref` | Entitlement add/remove |

Unlike Google's domain-wide delegation (impersonating an admin), Microsoft uses **application permissions** — the app registration itself holds directory-wide rights, approved once by a Global Admin through **admin consent**. Same lesson as Google though: the connector is exactly as dangerous as the permissions consented to it.

---

## Real-world setup (outside IIQ)

### Step 1 — App registration

1. In [entra.microsoft.com](https://entra.microsoft.com/) → App registrations → New: `app-identityiq-m365`.
2. Record **Tenant ID** and **Application (client) ID**.

### Step 2 — API permissions (application, not delegated)

Add Microsoft Graph **application permissions** and grant **admin consent**:

```text
User.Read.All            (aggregation)
Group.Read.All           (group aggregation)
GroupMember.ReadWrite.All (group provisioning — phase 2)
User.ReadWrite.All       (disable/update — phase 2)
Sites.FullControl.All    (SharePoint connector; consider Sites.Selected for least privilege)
```

Start read-only for phase 1 aggregation; widen for provisioning in phase 2. For SharePoint, prefer **`Sites.Selected`** with explicit per-site grants over `Sites.FullControl.All` when your connector version supports it — this is the single biggest least-privilege win available in this stack.

### Step 3 — Credential

Prefer a **certificate** over a client secret: secrets expire quietly (default 6–24 months) and leak in config exports. Upload the public cert to the app registration; keep the private key in the vault. If you must use a secret, calendar its expiry — "connector died because the secret expired" is the most common M365 connector incident.

### Step 4 — Governance records

Document: tenant ID, client ID, consented permissions with justification, credential expiry/rotation date, and the two business owners (collab ops for M365, data steward for SPO). Security review signs this before consent is granted.

---

## Before you start

- [ ] IIQ up as `spadmin`; matrix rows for Office 365 and SharePoint Online located
- [ ] Lesson 59 Entra concepts fresh (directory vs service layering)
- [ ] Decide your path: live Microsoft dev tenant (free via M365 developer program) or mock fallback
- [ ] Never use personal Microsoft credentials; personas `helen.ross`, `marcus.approve`, `amelia.brooks` for mocks

---

## Lab procedure

### Task 1 — Scope and ownership decision table

The most consequential decision in this lesson happens before any configuration: who owns what.

1. Reproduce the "Why two (or three) IIQ applications" table in your binder and add a **Cert owner** name per row: `helen.ross` (Entra/IAM), collab ops proxy (M365), `amelia.brooks` (SPO data steward).
2. Write the anti-pattern explicitly: *Certifying SharePoint access only via Entra group names misses site-level and direct grants. If forced into it, record a residual risk.*

**Expected result:** Scope table with named owners and the anti-pattern noted.

### Task 2 — Create MNB-M365

1. Applications → Add New → **Microsoft Office365** (or equivalent menu path).
2. Connection: Tenant ID, Client ID, certificate/secret reference (lab: placeholders noting "cert in vault").
3. Name `MNB-M365`; owner `helen.ross`, business owner collab ops.
4. Schema: `userPrincipalName` (native identity), `displayName`, `accountEnabled`, `assignedLicenses` (read-only attribute per the licensing decision), multi-valued `m365Groups` as the **entitlement attribute**.
5. Correlation: UPN ↔ identity email; note the production upgrade (employeeId in an Entra extension attribute). **Create identities: OFF.**
6. Live tenant: run Test Connection.

**Expected result:** Application saved; schema shows groups as entitlement, licenses as attribute.

**If it fails:** `AADSTS700016` = wrong tenant/client ID; `Authorization_RequestDenied` = permission added but admin consent never granted.

### Task 3 — Create MNB-SharePoint-Online

Site access deserves its own application because its grants and its reviewers are different.

1. Add **Microsoft SharePoint Online** connector app `MNB-SharePoint-Online`; business owner `amelia.brooks`.
2. Plan the entitlement model: site membership entitlements `SPO_CREDIT_SITE`, `SPO_BOARD_SITE`, `SPO_HR_SITE` (site + role, e.g. Members vs Owners, if your connector version splits them).
3. Scope: aggregate the three sensitive site collections first, not the whole tenant — a scoped rollout is how real programs start.
4. Record the `Sites.Selected` least-privilege intent from Step 2.

**Expected result:** Second application shell with three site entitlements and a scoped-rollout note.

### Task 4 — Mock inventories (fallback: no live tenant)

1. `~/iiq-lab-data/connectors/m365/MNB-M365-mock.csv`:

```csv
upn,employeeId,m365Groups,accountEnabled,license
marcus.approve@meridiannb.com,MNB00047,M365_CREDIT_COMMITTEE|M365_ALL_STAFF,true,SPE_E3
amelia.brooks@meridiannb.com,MNB00098,M365_ALL_STAFF,true,SPE_E3
samir.hassan@meridiannb.com,MNB00094,,false,
```

2. `~/iiq-lab-data/connectors/m365/MNB-SharePoint-Online-mock.csv`:

```csv
upn,employeeId,sites,active
marcus.approve@meridiannb.com,MNB00047,SPO_BOARD_SITE,true
amelia.brooks@meridiannb.com,MNB00098,SPO_CREDIT_SITE,true
```

3. Shadow-aggregate via DelimitedFile apps. Note the seeded story: Marcus holds `SPO_BOARD_SITE` *directly* — the site-level grant your Entra-only governance would never see.

**Expected result:** Two mock inventories aggregated; Marcus's board-site story understood.

### Task 5 — Aggregation tasks and scheduling

1. Create `MNB-M365-Account-Aggregation` and `MNB-SharePoint-Online-Account-Aggregation`; run both (live or shadow).
2. Order matters: schedule Entra agg → M365 agg → SPO agg nightly, so directory correlation lands before service-layer accounts arrive.
3. Spot-check: `marcus.approve` cube shows both the M365 group and the SPO site entitlement.

**Expected result:** Two Task Results; Marcus visible in both layers on one cube.

### Task 6 — Dual-app leaver pattern

1. Storyboard termination of `samir.hassan`, in order, with reasons:
   1. **Revoke SPO site entitlements** — targeted, fast, evidenced per-site.
   2. **Remove M365 groups** — exits Teams, shared mailboxes, group-provisioned sites.
   3. **Disable sign-in** (Entra layer — coordinate with `MNB-Entra` ownership) — blocks all fresh tokens.
   4. **Mailbox disposition** — convert to shared mailbox or litigation hold per retention; never silent deletion.
   5. **Re-aggregate both apps** — evidence: `accountEnabled=false`, groups empty, sites empty.
2. Token caveat for the binder: disabling the account does not instantly kill *existing* sessions — note "revoke sessions" as part of the rapid-offboarding drill (Lesson 34) for high-risk leavers.

**Expected result:** Five-step dual-app leaver card including the session-revocation caveat.

### Task 7 — featuresString and licensing note

1. Check registry/glossary: expect ENABLE + PROVISIONING on Office365; SPO features vary by version — mark CONFIRM against your ConnectorRegistry, do not invent.
2. Write the licensing paragraph: group-based licensing in Entra; license-granting groups are the certified objects; `assignedLicenses` read-only in `MNB-M365`.

**Expected result:** Feature notes + licensing approach paragraph.

### Task 8 — Residual risk

Record `RR-SPO-UNIQUE-01`: *File- and folder-level unique permissions, and anonymous/company-wide sharing links, are below this connector's visibility. Compensating control: site-owner attestation + SharePoint sharing reports.* Owner: `amelia.brooks`.

**Expected result:** RR logged with compensating control.

### Task 9 — Examiner question drill

*"Who can read board materials, and how do you know?"* Write the answer: `MNB-SharePoint-Online` aggregates `SPO_BOARD_SITE` holders nightly; the entitlement is certified quarterly by the data steward; direct sub-site sharing is covered by `RR-SPO-UNIQUE-01` attestation.

**Expected result:** Written examiner answer in the binder.

---

## Acceptance criteria

- [ ] Scope/ownership table separates Entra / M365 / SharePoint with named cert owners
- [ ] Real-world setup understood: app registration, application permissions, admin consent, cert-over-secret
- [ ] `MNB-M365` and `MNB-SharePoint-Online` created with correct entitlement/attribute choices
- [ ] Aggregation evidence for both apps (live or mock); Marcus visible in both layers
- [ ] Five-step dual-app leaver card with session-revocation caveat
- [ ] Licensing paragraph, `RR-SPO-UNIQUE-01`, and examiner answer recorded

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Authorization_RequestDenied` (403) | Permission added without admin consent | Grant admin consent in the app registration |
| Connector dies after months of working | Client secret expired | Rotate; migrate to certificate auth |
| Sites missing from aggregation | Site scope filter / `Sites.Selected` grant missing for that site | Add the site to scope and to the Selected grant |
| Same group appears in Entra and M365 apps | It's one directory object surfaced twice | Pick one system of record per control; document it |
| Leaver's mailbox still receiving mail | Only groups removed, sign-in never disabled | Follow the full five-step card |
| Teams access vs SPO access confusion | M365 group provisions both | Document: group membership governed in `MNB-M365`; site-unique grants in `MNB-SharePoint-Online` |

---

## Training binder evidence

- Scope/ownership table + anti-pattern note
- App registration worksheet (tenant/client IDs, consented permissions, credential expiry — no secrets)
- Both aggregation Task Results + Marcus dual-layer screenshot
- Five-step leaver card
- Licensing paragraph, `RR-SPO-UNIQUE-01`, examiner answer

---

## Knowledge check

1. Why does Meridian run separate IIQ applications for M365 and SharePoint Online?
2. What is admin consent, and how does it differ from Google's domain-wide delegation?
3. Why prefer certificate authentication over a client secret?
4. Why is `Sites.Selected` preferable to `Sites.FullControl.All`?
5. In the leaver card, why is disabling sign-in insufficient on its own for a high-risk leaver?
6. What access does `RR-SPO-UNIQUE-01` admit the connector cannot see?

### Answers

1. Different systems of record with different grant types and different competent reviewers — one merged app would produce rubber-stamp certifications.
2. A Global Admin's one-time approval of application permissions held by the app itself; Google instead delegates scopes for the service account to impersonate an admin user.
3. Secrets expire silently and leak in exports; certificates have manageable lifecycles and the private key never leaves the vault.
4. It grants access only to explicitly listed sites instead of every site in the tenant — least privilege at the API layer.
5. Existing tokens/sessions can survive the disable; rapid offboarding adds explicit session revocation.
6. File/folder-level unique permissions and sharing links below site scope.

---

## Further reading

- [Microsoft Graph permissions reference](https://learn.microsoft.com/en-us/graph/permissions-reference) — what each permission actually allows; the source for your least-privilege review.
- [Microsoft: grant admin consent to an application](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/grant-admin-consent) — the exact consent flow from Step 2.
- [Microsoft: Sites.Selected permission for SharePoint](https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins-modernize/from-acs-to-aad-apps) — background on scoped SharePoint app access.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search "Office 365 connector" and "SharePoint Online connector" for version-specific guides.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — field troubleshooting for Graph permission and consent issues.
- [FFIEC IT Handbook — Information Security](https://ithandbook.ffiec.gov/it-booklets/information-security/) — the examiner's own reference on access control expectations at banks.

---

## Stretch lab

Draft a targeted certification (Lesson 45 pattern) selecting only `SPO_BOARD_SITE` holders, owned by `amelia.brooks`, quarterly. Then investigate group-based licensing: design the Entra group structure (`LIC_E3_EMPLOYEES`, `LIC_E1_CONTRACTORS`) that would let you govern license spend through group certifications instead of per-user license reviews.

---

## Summary

- M365 access accumulates in layers — directory groups, M365 groups, site permissions — and each layer needs its own application, owner, and certification.
- The connectors authenticate as an Entra app registration with application permissions; admin consent and `Sites.Selected` are where least privilege is won or lost.
- The dual-app leaver card (sites → groups → sign-in → mailbox disposition → re-aggregate) plus residual-risk attestation is the complete examiner story.

---

**Previous:** [Lesson 74 — Google Workspace Connector](74-google-workspace-connector.md)  
**Next:** [Lesson 76 — AWS IAM Connector](76-aws-iam-connector.md)
