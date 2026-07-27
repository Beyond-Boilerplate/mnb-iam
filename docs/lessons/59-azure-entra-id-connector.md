# Lesson 59 — Azure / Entra ID Connector

**Level:** Intermediate  
**Track:** Connectors — Directory  
**Time:** 90–120 min  
**Prereq:** Lesson 58 — LDAP / OpenLDAP Connector; matrix row Entra ID / Azure AD  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv`
- Lesson 55 feature matrix; worksheet output `~/iiq-lab-data/connectors/MNB-Entra-hybrid-59.md`

---

## Learning objectives

You will be able to:

- Explain how Entra ID differs from on-prem AD — flat directory, administrative units, group types, app registrations versus service principals — and why "AD in the cloud" is a dangerous mental model
- Describe the Microsoft Graph client-credentials flow the connector uses, including application permissions and admin consent
- Perform the real-world tenant setup: app registration, `User.Read.All` / `Group.Read.All` application permissions, admin consent, and the certificate-versus-secret decision
- Create and configure **MNB-EntraID** with the native Azure Active Directory connector as the primary path, non-authoritative, create-identities off
- Design correlation using UPN↔email with the `employeeId` extension attribute as the production answer, and defend it against email drift
- Write the aggregation, disable, and group test cases, and keep Entra guests out of workforce cube creation

---

## Why this matters

**Business.** Meridian is a hybrid-identity bank: Corporate AD still authenticates the teller platforms and legacy bank apps, while Entra ID brokers every SaaS login — Salesforce, ServiceNow, the M365 estate. When `kai.nguyen` joined the digital banking team, his AD account synced up to Entra within the hour, but the *governance* view lagged for weeks: nobody had aggregated Entra, so the security groups gating production Azure resources never appeared in his access review. Cloud access that IIQ cannot see is cloud access nobody certifies.

**Control / audit.** Two controls anchor this lesson. First, **identity truth stays with HR**: `MNB-HR` creates cubes; AD and Entra are both *targets* that correlate to them — the moment two directories can each create identities, you have split-brain, and Lesson 21's manager hierarchy quietly forks. Second, **cloud credentials are governed artifacts**: the examiner will ask for the tenant ID, the app registration, the exact Graph permissions consented, and where the client secret lives. "In the connector config, which is in git" is a reportable finding — secrets never live in git, and this lesson's worksheet is built around that rule.

---

## Concepts

### Entra ID is not AD in the cloud

Microsoft Entra ID (formerly Azure AD) shares a vendor and a sync pipeline with on-prem AD, and almost nothing else architecturally. Engineers who carry AD assumptions into Entra design the wrong schema and the wrong scoping.

| | On-prem Active Directory | Microsoft Entra ID |
| --- | --- | --- |
| Structure | Hierarchical: forests, domains, **OUs** | **Flat** — no OUs; scoping via **administrative units** |
| Protocols | LDAP, Kerberos, NTLM | HTTPS REST (Microsoft Graph), OAuth 2.0, OIDC, SAML |
| Account key | `sAMAccountName` / `objectSid` | `userPrincipalName` (UPN) / immutable `id` (objectId GUID) |
| Disable | `userAccountControl` bit flags | Boolean `accountEnabled` |
| Groups | Security / distribution groups in OUs | **Security groups** and **Microsoft 365 groups**; assigned or **dynamic** |
| Delegation | OU-based ACLs | Entra RBAC roles, scoped by administrative unit |

The flat structure is the one that bites first. At Meridian, AD engineers scope things by OU reflexively — *"just aggregate the `/Employees` OU"*. Entra has no OUs. An **administrative unit** is the nearest analog, but it scopes *admin role assignments* (who may reset whose password), not policy or aggregation. When `sofia.torres` asked why her "cloud OU filter" returned everything, this was why: there is nothing to filter on — you scope by attribute filters or group membership instead.

### Group types: security vs M365, assigned vs dynamic

Entra has two group *purposes* and two *membership mechanics*, and governance treats them differently:

- **Security groups** gate access — Azure resources, app role assignments, Conditional Access. These are your certifiable entitlements.
- **Microsoft 365 groups** bundle collaboration surfaces (a mailbox, a Team, a SharePoint site). They still grant access to content, so they are entitlements too — Lesson 75 goes deep on them.
- **Assigned** membership is explicit — someone granted it, someone can revoke it, a certification makes sense.
- **Dynamic** membership is computed from a rule like `user.department -eq "Wire Operations"`. You do not certify a dynamic member's *membership* — you certify the **rule** and the *attribute pipeline feeding it*. When `priya.wire` transferred out of wire operations, her dynamic group membership dropped only because HR fixed `department` — the entitlement review question becomes "who reviews that rule and that attribute?"

### App registrations vs enterprise applications (service principals)

The connector needs its own credential in the tenant, and Entra's terminology here confuses everyone once:

- An **app registration** is the *definition* of an application: its client ID, credentials, and requested permissions. Think of it as the blueprint.
- An **enterprise application** (technically a **service principal**) is the *instance* of that app in a tenant — the object that actually gets granted permissions and shows up in sign-in logs.

Register once, and a service principal is created alongside it. IIQ authenticates *as* that service principal. When Meridian's cloud team audits "what can log into our tenant non-interactively," they are enumerating service principals — and `MNB-EntraID`'s will be on the list, which is exactly why its permissions must be least-privilege and documented.

### Split-brain: why only HR creates identities

Meridian runs three identity-bearing systems: `MNB-HR` (authoritative), `MNB-ActiveDirectory` (on-prem target), and `MNB-EntraID` (cloud target). The failure mode to design against is **dual authoritative directories**: if both AD and Entra aggregations can create identity cubes, the same human arrives twice — once from an AD `sAMAccountName`, once from an Entra UPN — with duplicate cubes, forked manager chains, and certifications that each cover half the person. The fix is structural, not procedural: create-identities is **off** on both directory applications, correlation binds their accounts to HR-created cubes, and anything that fails correlation surfaces as an uncorrelated account for Lesson 19 remediation. When a `raj.external` contractor account appears in Entra with no HR record behind it, you *want* that to be a visible exception, not a silently minted cube.

---

## How it works

The native Azure Active Directory connector talks to **Microsoft Graph** — Microsoft's unified REST API — authenticating with the **OAuth 2.0 client credentials flow**: no user signs in; the app presents its own credential and receives a token scoped to its consented **application permissions**.

```
IdentityIQ (MNB-EntraID)
        │  tenant ID + client ID + client secret (or certificate)
        ▼
Entra token endpoint
  https://login.microsoftonline.com/{tenantId}/oauth2/v2.0/token
        │  client_credentials grant
        ▼
Access token (app-only; carries consented application permissions)
        │
        ▼
Microsoft Graph  https://graph.microsoft.com/v1.0
        ├── GET /users                 → account aggregation (paged)
        ├── GET /groups                → group (entitlement) aggregation
        ├── GET /groups/{id}/members   → membership resolution
        └── PATCH /users/{id}          → accountEnabled=false (leaver disable)
```

Two properties of this flow matter for governance. **Admin consent is the control point:** application permissions do nothing until a tenant admin consents, so the consent record *is* the authorization evidence — the cloud equivalent of Lesson 58's bind-account ACLs. **The token is app-only:** the connector acts as itself, not on behalf of any user, so its power is exactly the union of consented permissions — no more, no less.

| Operation | Graph behavior | IIQ behavior |
| --- | --- | --- |
| Account aggregation | Paged `GET /users` with `$select` for chosen attributes | One Link per user; UPN or objectId as native identity |
| Group aggregation | `GET /groups` (filterable to security groups) | ManagedAttribute per group |
| Membership resolution | `GET /groups/{id}/members` | Multi-valued entitlement on accounts |
| Disable / enable | `PATCH /users/{id}` with `accountEnabled: false/true` | Leaver disable; evidence on next aggregation |
| Attribute updates | `PATCH /users/{id}` | Attribute sync (needs `User.ReadWrite.All`) |

---

## Real-world setup (outside IIQ)

This is what a Meridian cloud engineer does in the tenant before the connector can bind. The lab uses fictional values, but the knowledge check assumes you can execute these steps for real.

### Step 1 — Register the application

1. In the [Entra admin center](https://entra.microsoft.com/) (or equivalent portal path): Identity → Applications → App registrations → New registration.
2. Name it `mnb-identityiq-connector`; single tenant; no redirect URI (client-credentials apps never do interactive sign-in).
3. Record the **Application (client) ID** and **Directory (tenant) ID** from the overview page — these are identifiers, not secrets, and belong on the worksheet.

### Step 2 — Grant application permissions and consent

1. API permissions → Add a permission → Microsoft Graph → **Application permissions** (not Delegated — there is no signed-in user).
2. Add `User.Read.All` and `Group.Read.All` — sufficient for aggregation. Provisioning comes later and wider (`User.ReadWrite.All`, `Group.ReadWrite.All`); enterprises stage this widening deliberately, read-first.
3. A Global Administrator (or Privileged Role Administrator) clicks **Grant admin consent**. Capture who consented and when — that record is binder evidence.

### Step 3 — Credential: certificate vs secret

- A **client secret** is a password string with an expiry. Fine for labs and short-lived pilots; in production it expires (silent connector outage) and it is one copy-paste away from a git commit.
- A **certificate** is the production answer: the private key never leaves the vault/HSM, Entra holds only the public half, and rotation is a scheduled ceremony, not an incident. Meridian's standard: *certificate auth for production; secrets only in non-prod, vaulted, 90-day expiry.*

Either way the credential value goes into the secret vault, and the connector reads it from secure configuration — **never git, never the lesson worksheet.**

### Step 4 — Cross-reference forward

Lesson 75 (M365 & SharePoint Online) builds on this *exact* app-registration pattern — same tenant, same consent model, wider Graph permissions for Exchange/SharePoint/Teams objects. Design the registration naming and ownership now so Lesson 75 extends it rather than duplicating it.

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq` as `spadmin`; `MNB-HR` cubes exist for correlation
- [ ] Lesson 52 selection record: preferred connector **Azure Active Directory**, alternate **SCIM 2.0**
- [ ] Lesson 55 feature matrix row for `MNB-EntraID` at hand
- [ ] No live Azure tenant is required — placeholders are used where tenant values would go; if you have a disposable dev tenant, the live steps are called out inline
- [ ] No real secrets anywhere in lab files or git

---

## Lab procedure

### Task 1 — Hybrid identity decision note

Before any configuration, write down who creates identities — the single sentence that prevents split-brain. In production this is an ADR the architecture board signs; here it is the header of your lesson file.

1. Create `~/iiq-lab-data/connectors/MNB-Entra-hybrid-59.md` and write the stance:

> Corporate AD is the on-prem account target. Entra ID is the cloud directory target. Neither creates workforce identities; `MNB-HR` does. Joiner provisioning may create AD then rely on sync/cloud create per Architecture — document the actual pattern when confirmed.

2. List the split-brain risks of dual authoritative directories: duplicate cubes for the same human, forked manager chains, certifications covering half a person each, joiner/leaver events firing twice.

**Expected result:** Hybrid note saved, opening with "HR only creates identities" and at least three named risks.

### Task 2 — App registration worksheet (fictional values)

Production engineers keep a registration worksheet precisely so identifiers are documented and secrets are conspicuously *not*. Fill it with the lab's fictional values — the discipline is the deliverable.

1. Add the worksheet to the hybrid note:

| Item | Lab value |
| --- | --- |
| Tenant ID | `00000000-lab-tenant` |
| Application (client) ID | `11111111-lab-app` |
| Client secret | Stored in vault — **not** in this file, not in git |
| Graph permissions (consented) | `User.Read.All`, `Group.Read.All` — application permissions, admin consent granted |
| Consent granted by | Cloud IAM admin (record name/date in production) |
| Certificate auth for prod? | Yes — secret allowed non-prod only, vaulted, 90-day expiry |

2. Add the footer: *"Production values come from the cloud team; rotate on schedule; widening to ReadWrite permissions requires a new consent record."*

**Expected result:** Worksheet complete with fictional identifiers and zero secret values anywhere.

### Task 3 — Create the MNB-EntraID application (native connector, primary path)

The native connector is the primary path because it understands Entra semantics — groups, `accountEnabled`, objectIds — that a generic Web Services wrapper would flatten into strings. This form consumes exactly the Step 1–3 artifacts.

1. Applications → Add New → **Azure Active Directory** (or equivalent menu path in your build).
2. Name: `MNB-EntraID`. Owner: Cloud IAM / Technology (lab session as `spadmin`; business owner `sofia.torres`).
3. Connection section, from the worksheet:
   - **Tenant / Directory ID:** `00000000-lab-tenant`
   - **Client ID:** `11111111-lab-app`
   - **Client secret:** placeholder text noting "value in vault" (live tenant: paste the real secret into the credential field only — it is stored encrypted, never exported to git)
4. Mark the application **non-authoritative**; confirm **create identities is OFF**.
5. Skip **Test Connection** with placeholders; if you have a dev tenant, run it — success proves tenant ID, client ID, secret, and consent in one click.

**Expected result:** `MNB-EntraID` saved as a fully-formed native application with placeholder credentials; non-authoritative, create-identities off.

**If it fails:** If the Azure AD type is absent from your IIQ build, document the alternate from the matrix — a SCIM 2.0 application `MNB-EntraID-SCIM` — as a *temporary* stand-in, and record why native is still the target state.

### Task 4 — Schema and correlation: the employeeId answer

Correlation design is where Entra deployments quietly rot. UPN↔email works on day one and drifts over years — name changes rewrite emails, UPNs get re-suffixed during domain cleanups. Design the durable answer now.

1. Account schema: `userPrincipalName`, `displayName`, `mail`, `accountEnabled`, `id` (objectId), `department`, and `employeeId` (also readable via `onPremisesExtensionAttributes` for synced accounts). Native identity: document your choice — UPN is human-readable; objectId is immutable. Record which you chose and why.
2. Entitlements: Entra **security groups** as the entitlement attribute; note which groups Meridian certifies (resource-gating groups yes; dynamic groups → certify the rule instead, per Concepts).
3. Correlation, in order:
   - **Production answer:** `employeeId` (Graph `employeeId` / extension attribute) ↔ identity `employeeId` — survives renames because HR owns both ends.
   - **Bootstrap fallback:** UPN ↔ identity `email`, explicitly labeled temporary with a follow-up to populate `employeeId` tenant-wide.
4. Worked example in the note: `kai.nguyen@meridiannb.com` correlates by employeeId even after a hypothetical rename to `kai.win@meridiannb.com`; the UPN-only design would orphan the renamed account.

**Expected result:** Schema and two-tier correlation plan in the hybrid note, with the Kai rename example written out.

### Task 5 — Aggregation design and test cases

Test cases written before the first live run are what make a later tenant connection a checklist instead of an improvisation — and they double as binder evidence of intent.

1. Aggregation design: task `Aggregate MNB-EntraID`; nightly, **after** `MNB-HR` (targets first) and coordinated with the AD aggregation so both directory sources do not race on the same identity attributes; delta aggregation once supported/verified for the tenant size.
2. Write the test table:

| Test ID | Action | Expected result | If it fails |
| --- | --- | --- | --- |
| ENTRA-AGG-01 | Run Account Aggregation | Cloud accounts linked to existing HR cubes; zero identities created | Check Graph permissions/consent, then correlation attribute population |
| ENTRA-EN-01 | Leaver disable for a test user | `accountEnabled=false` visible on the Link after re-aggregation | Verify ENABLE in featuresString and write-level Graph permission |
| ENTRA-GRP-01 | Group aggregation + certification preview | Security groups appear as certifiable entitlements with members | Confirm `Group.Read.All` consented; check group-type filter |

3. Personas for the walkthrough: `sofia.torres` and `kai.nguyen` as cloud-heavy users (lab assumption) — Sofia's disable is the ENTRA-EN-01 subject; the evidence chain is the pre-disable aggregation, the provisioning/PATCH record, and the post-disable aggregation showing `accountEnabled=false`.

**Expected result:** Three test cases with Expected result / If it fails, plus the Sofia disable evidence chain.

### Task 6 — Guest / B2B boundary

Entra tenants accumulate guests — B2B collaboration accounts with UPNs like `raj.external_partnerco.com#EXT#@meridiannb.onmicrosoft.com`. Left unhandled, they pollute workforce governance.

1. Write the boundary rule in the hybrid note: *Entra guest users (`userType=Guest`, `#EXT#` UPN pattern) must never create or correlate to Meridian workforce cubes.*
2. Strategy: filter guests out of the workforce aggregation (or land them in a separate population certified by their sponsors) — guests get governed, just not as employees.
3. Verification: create-identities off already prevents cube creation; tighten correlation so a guest UPN cannot accidentally match a workforce email.

**Expected result:** Guest/B2B paragraph with the filter-or-separate-population decision recorded.

### Task 7 — SCIM 2.0 alternate and the no-tenant fallback

Honest connector records name the alternate and the fallback explicitly, so nobody later mistakes a stopgap for the design.

1. Alternate note: **SCIM 2.0** remains the matrix alternate — standards-based users/groups CRUD, useful when the native type is unavailable or for SCIM-first targets (Lessons 69–70) — at the cost of Entra-specific semantics (dynamic group awareness, extension attributes).
2. Fallback (no tenant — clearly secondary): everything above except a live Test Connection and live aggregation is already complete with placeholders. Add a dated note: *"Live run deferred — no tenant; test cases ENTRA-AGG-01/EN-01/GRP-01 are the executable checklist for connection day."*
3. CHANGELOG entry: "Lesson 59 — MNB-EntraID native application, correlation plan, test cases, guest boundary."

**Expected result:** Alternate and fallback documented as secondary paths; CHANGELOG updated.

---

## Acceptance criteria

- [ ] Hybrid note opens with "HR only creates identities" and names ≥3 split-brain risks
- [ ] Registration worksheet complete — fictional tenant/client IDs, permissions, consent line, **no secrets**
- [ ] `MNB-EntraID` created on the native Azure Active Directory type (or documented SCIM stand-in), non-authoritative, create-identities off
- [ ] Two-tier correlation plan: employeeId production answer, UPN↔email labeled temporary, Kai rename example written
- [ ] ENTRA-AGG-01 / ENTRA-EN-01 / ENTRA-GRP-01 recorded with Expected result / If it fails
- [ ] Guest/B2B boundary rule written
- [ ] `Aggregate MNB-EntraID` named and sequenced after HR; CHANGELOG updated

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `401 Unauthorized` on Test Connection | Wrong tenant/client ID, or secret expired | Verify worksheet IDs; check secret expiry — expired secrets are the #1 silent Entra outage |
| `403 Insufficient privileges` on `/users` | Permissions added but **admin consent never granted**, or Delegated chosen instead of Application | Grant admin consent on Application permissions in the portal |
| Aggregation creates duplicate cubes | Create-identities left on | Disable it; remediate duplicates carefully (merge/delete per Lesson 19 discipline) |
| Accounts land uncorrelated | UPN↔email drift, or `employeeId` unpopulated in the tenant | Move to the employeeId correlation; drive the population task with the cloud team |
| Guests appear in workforce views | No guest filter; correlation matched an external UPN | Apply the Task 6 boundary: filter `userType=Guest` / `#EXT#` patterns |
| Disable test fails, aggregation fine | Read-only permissions consented; ENABLE needs write | Consent `User.ReadWrite.All` (new consent record) and re-check featuresString |

---

## Training binder evidence

- `MNB-Entra-hybrid-59.md`: hybrid stance, worksheet (no secrets), correlation plan, guest boundary
- `MNB-EntraID` application screenshot (placeholder credentials visible as placeholders)
- Test-case table ENTRA-AGG-01 / ENTRA-EN-01 / ENTRA-GRP-01
- Consent evidence line (who/when — real values in production)
- Feature matrix row updated if any Unknown resolved to Y/N

**Examiner question:** *"Which system creates the identity cube when a banker joins — Entra, AD, or HR? And show me exactly what your cloud connector's credential is permitted to do in the tenant."*

---

## Knowledge check

1. Entra ID has no OUs — what replaces them, and what does that object actually scope?
2. Why must the connector use **application** permissions with admin consent rather than delegated permissions?
3. What is the difference between an app registration and an enterprise application (service principal), and which one does IIQ authenticate as?
4. UPN↔email correlation works today — why is `employeeId` the production answer anyway?
5. Why is a certificate preferred over a client secret for the production connector credential?
6. Why must Entra guests (`#EXT#`) never become Meridian workforce cubes?

### Answers

1. Administrative units — but they scope *admin role assignments* (who may administer whom), not policy or aggregation; scoping data pulls uses attribute filters or group membership instead.
2. The connector runs headless with no signed-in user; delegated permissions require one. Application permissions grant app-only access, and admin consent is the tenant's explicit authorization record for that grant.
3. The registration is the app's definition (client ID, credentials, requested permissions); the service principal is its instance in the tenant that actually holds granted permissions. IIQ authenticates as the service principal.
4. Emails and UPNs drift — renames, domain cleanups — orphaning links. `employeeId` is HR-owned on both ends, so correlation survives every rename.
5. The private key never leaves the vault (a secret is a copyable string one paste from git), and certificate rotation is a planned ceremony rather than a surprise expiry that silently breaks aggregation.
6. Guests are B2B/external identities with no HR record; minting workforce cubes for them bypasses every HR joiner control and pollutes certifications — they are governed separately under sponsor ownership.

---

## Further reading

- [Microsoft Learn — Quickstart: Register an application](https://learn.microsoft.com/entra/identity-platform/quickstart-register-app) — the authoritative walkthrough of Real-world setup Step 1; ten minutes, screenshots included.
- [Microsoft Learn — OAuth 2.0 client credentials flow](https://learn.microsoft.com/entra/identity-platform/v2-oauth2-client-creds-grant-flow) — the exact token flow in the ASCII diagram, including why admin consent is mandatory for application permissions.
- [Microsoft Graph permissions reference](https://learn.microsoft.com/graph/permissions-reference) — look up `User.Read.All` and `Group.Read.All` to see precisely what the connector can read; the least-privilege source of truth.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search "Azure Active Directory connector" for the version-specific application guide, schema attributes, and featuresString.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — search "Azure AD connector correlation" for field reports on UPN drift and extension-attribute correlation.

---

## Stretch lab

Map the Azure AD connector's account attributes against the SCIM 2.0 Enterprise User schema (`urn:ietf:params:scim:schemas:extension:enterprise:2.0:User`) and note where the native connector is richer — preparation for Lessons 69–70. Then design a delta-aggregation watermark approach for a 100,000-user tenant and write the trade-offs (freshness vs Graph throttling). Finally, draft a Conditional Access governance note: CA policies gate *authentication*, IIQ governs *entitlement* — sketch where the two must reference each other, pointing at Lesson 87's MFA patterns.

---

## Summary

- Entra ID is not AD in the cloud: flat directory, administrative units instead of OUs, two group types with dynamic membership, and an app-registration/service-principal model where admin consent is the authorization control.
- `MNB-EntraID` is a non-authoritative cloud target on the native connector: Graph client-credentials auth, `User.Read.All`/`Group.Read.All` to start, employeeId correlation as the durable production answer, create-identities off, guests excluded.
- HR remains the only identity source — the hybrid note, the test cases, and the no-secrets worksheet are the artifacts that prove it to an examiner, tenant or no tenant.

---

**Previous:** [Lesson 58 — LDAP / OpenLDAP Connector](58-ldap-openldap-connector.md)  
**Next:** [Lesson 60 — LDIF Connector](60-ldif-connector.md)
