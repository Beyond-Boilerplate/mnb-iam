# Lesson 56 — Active Directory Connector

**Level:** Intermediate  
**Track:** Connectors — Directory  
**Time:** 75–90 min  
**Prereq:** Lessons 53–55 — IQService architecture, aggregation patterns, provisioning feature matrix  

**Lab data:**
- Home: `~/iiq-lab-data/connectors/ad/iqservice-checklist.md`
- Repo: `lab-data/connectors/ad/iqservice-checklist.md`

---

## Learning objectives

You will be able to:

- Explain what the **Active Directory - Direct** connector is, and why Meridian chose it over the generic LDAP connector
- Decode the three names of an AD account (`sAMAccountName`, `userPrincipalName`, `distinguishedName`) and the `userAccountControl` bitmask, and explain which one belongs in correlation
- Perform the real-world setup outside IIQ: a least-privilege delegated service account, LDAPS, IQService with TLS, and the firewall paths — step by step against a real domain
- Create and configure **MNB-ActiveDirectory** field by field, including forest/domain settings, search DNs, schema, and correlation
- Run the `Aggregate MNB-ActiveDirectory` Account Aggregation task and spot-check correlation for `helen.ross` and `priya.wire`
- Complete the lesson with or without a live domain controller (lab-without-live-target fallback provided)

---

## Why this matters

**Business.** Corporate AD is Meridian's primary workforce directory: every branch workstation login, every file share, every wire-room application checks an AD group. When `helen.ross` transferred from Retail Operations to Treasury, her HR record updated the same day — but her AD account had been created years earlier with a typo'd `employeeID`. IIQ could not correlate it, so her AD account sat as an **uncorrelated account** on no one's cube. Her old Retail groups were never certified, never removed, and never showed up in her leaver plan when she eventually resigned. One bad correlation key turned into a live account for a departed employee — the exact finding examiners hunt for.

**Control / audit.** When the OCC examiner asks *"is Active Directory authoritative for workforce identity at Meridian, and show me the setting,"* your answer is: no — `MNB-HR` is the only authoritative source, `MNB-ActiveDirectory` has create-identities disabled, and every AD account either correlates to an HR-fed cube or lands on the uncorrelated-accounts report that IAM works weekly. The Application configuration, the correlation map, and the aggregation Task Results are the evidence. This lesson builds all three.

---

## Concepts

### What "Active Directory - Direct" actually is

**Active Directory** (AD) is Microsoft's directory service: a replicated database of users, groups, computers, and organizational units, hosted on servers called **domain controllers**. IdentityIQ ships two very different ways to talk to it:

| Connector | How it works | What you give up |
| --- | --- | --- |
| Generic **LDAP** connector | Pure LDAP reads/writes from the IIQ JVM | No native password set, no enable/disable semantics, no Exchange — AD-specific behavior becomes your problem |
| **Active Directory - Direct** | LDAP reads for aggregation **plus** a Windows-side agent (**IQService**) for the operations only Windows can do properly | Requires a Windows member server to host IQService |

**IQService** is a small .NET Windows service, installed on a member server near the domain controllers, that executes the Windows-native operations on IIQ's behalf: password set/reset, account enable/disable, and (in Lesson 57) Exchange mailbox operations. Lesson 53 covered its placement, TLS, and service-account design in depth — this lesson consumes that design; it does not repeat it.

The real-life test: when `helen.ross` calls the help desk for a password reset routed through IIQ, the generic LDAP connector cannot honor it against AD (AD password writes require a secure Windows-aware channel); the Direct connector hands it to IQService, which performs it as a proper Windows password set. That single operation is why Meridian's checklist pins the type to **Active Directory - Direct**.

### The three names of an AD account

Every AD account carries at least three identifiers, and picking the wrong one for correlation is the most common AD onboarding mistake:

- **`sAMAccountName`** — the short legacy logon name (`hross`), unique per domain, maximum 20 characters. Stable across OU moves and renames unless an admin deliberately changes it.
- **`userPrincipalName`** (UPN) — the email-style logon name (`helen.ross@meridiannb.com`). Often matches email, but not guaranteed to.
- **`distinguishedName`** (DN) — the full LDAP path to the object: `CN=Helen Ross,OU=Employees,DC=meridiannb,DC=com`. This is the object's *address*, not its identity: move Helen to another OU and her DN changes while everything else stays put.

Meridian's design, seeded in the checklist and preserved throughout this track: the connector may use the DN internally as the account's native key (most builds default to it — record what yours does), but **correlation** uses stable business attributes: `sAMAccountName` ↔ identity `userName` as primary, `employeeID` ↔ `employeeId` as the authoritative tie-breaker, `mail` ↔ `email` as secondary only. The naive alternative — correlating on DN or display name — breaks the day `priya.wire` moves OUs or gets married and renamed, orphaning her account mid-certification.

### `userAccountControl` — the bitmask that decides enabled vs disabled

AD does not have a simple `enabled` column. It has **`userAccountControl`** (UAC), an integer whose individual bits are flags. The two values you will see constantly:

| Value | Bits set | Meaning |
| --- | --- | --- |
| `512` | NORMAL_ACCOUNT | Enabled, standard user |
| `514` | NORMAL_ACCOUNT + ACCOUNTDISABLE (0x2) | **Disabled** |
| `66048` | NORMAL_ACCOUNT + DONT_EXPIRE_PASSWORD | Enabled, non-expiring password (service-account smell) |
| `66050` | All of the above + ACCOUNTDISABLE | Disabled, non-expiring password |

When `samir.hassan` was terminated last quarter, the evidence that his leaver actually executed was the aggregation showing his UAC flip from `512` to `514`. An account sitting in a "Terminated" OU with UAC still `512` is a live account wearing a costume — Lesson 57 makes that anti-pattern explicit. The connector surfaces enable/disable as first-class operations (the `ENABLE` feature from Lesson 55), executed through IQService, but *you* must know how to read the raw number when the examiner points at an LDIF export.

### DC vs GC — where reads actually go

A **domain controller (DC)** holds a full, writable copy of one domain's directory. A **global catalog (GC)** is a DC that additionally holds a *partial, read-only* copy of every domain in the forest — a forest-wide phone book listening on its own ports (3268/3269 instead of 389/636).

Meridian's lab is a single domain (`meridiannb.com`), so DC reads suffice. But design for the real question: if Meridian acquires a bank with a child domain, do you aggregate against a GC (one connection, forest-wide, but only the partial attribute set) or per-domain DCs (full attributes, one application or connection per domain)? The trap: `employeeID` is **not** in the default GC partial attribute set — a GC-based aggregation can silently return blank `employeeID` for every account, and your primary tie-breaker correlation dies quietly. When `amelia.brooks` from the acquired subsidiary fails to correlate, this is the first thing to check. Document the forest/GC decision on the checklist line "Forest/domain configuration; GC usage decided."

---

## How it works

The Direct connector is really two channels wearing one Application. Reads (aggregation) are LDAP searches from the IIQ JVM straight to a DC or GC. Writes that Windows cares about (passwords, enable/disable, later Exchange) travel to IQService, which executes them Windows-natively and returns the result.

```
IdentityIQ (MNB-ActiveDirectory application)
        │
        ├── READ channel: LDAP(S) :389 signed / :636  (GC: :3268 / :3269)
        │        │
        │        ▼
        │   Domain Controller / Global Catalog ── users, groups, OUs
        │        (paged searches under the configured search DNs)
        │
        └── WRITE channel: TLS to IQService (commonly :5050 — confirm your build)
                 │
                 ▼
            IQService (.NET agent on Windows member server)
                 │  Windows-native APIs / secure channel
                 ▼
            Domain Controller ── password set, enable/disable,
                                 create/modify, (Lesson 57: Exchange)
```

| Operation | Mechanism | Notes |
| --- | --- | --- |
| Account aggregation | LDAP(S) paged search from IIQ | Scoped by search DNs; filter like `(&(objectCategory=person)(objectClass=user))` |
| Group aggregation | LDAP(S) search (Lesson 57) | `memberOf` on accounts; group objects promoted to ManagedAttributes |
| Password set / reset | **IQService** | The operation the generic LDAP connector cannot do properly |
| Enable / disable | **IQService** writes `userAccountControl` | Surfaces as the `ENABLE` feature; evidence is UAC 512 ↔ 514 |
| Create / modify / OU move | **IQService** | Create needs a provisioning policy (stubs in Task 5, forms in Lessons 57/61) |
| Exchange mailbox ops | **IQService** → Exchange | Out of scope until Lesson 57's explicit decision |

Consequence worth memorizing: a green **Test Connection** proves *both* channels or neither, depending on your build's test behavior — LDAP bind success with IQService unreachable means aggregation will work while every password reset times out. Test the channels separately in production (aggregate once, then run one disable in a test OU).

---

## Real-world setup (outside IIQ)

This is what a production engineer does before the Application form is worth filling in. Read it even if you use the fallback path — the knowledge check and the examiner assume you know it. Lesson 53's worksheets are the design inputs here.

### Step 1 — Create the connector service account (not Domain Admin)

1. In Active Directory Users and Computers (or your provisioning tool of record), create `svc-iiq-ad` in the service-accounts OU — outside the human JML OUs so it never enters joiner/leaver flows.
2. Set a long random password sourced from the vault (CyberArk / Secrets Manager). Deny interactive logon via GPO. Document the rotation owner (Windows + IAM jointly, per the Lesson 53 worksheet).
3. **Do not add it to Domain Admins.** The whole point of the next step is that it never needs to be.

### Step 2 — Delegate least-privilege rights on the target OUs only

Use the **Delegation of Control** wizard (or explicit ACEs) on `OU=Employees` and `OU=Contractors` — not at the domain root:

1. Read all user information (aggregation needs read of user attributes including `employeeID`, `mail`, `memberOf`, `userAccountControl`).
2. **Reset password** and **Change password** on user objects (for the IQService password path).
3. Write `userAccountControl` (enable/disable) and, if creates are in scope later, Create/Delete user objects *in those OUs only*.
4. Record every delegated right in the binder. When the examiner asks "what can the IIQ service account actually do," the answer is this list — not "it's an admin."

The naive approach — dropping the account into Domain Admins "to make it work" — passes the demo and fails the audit: you have created a domain-takeover credential stored in an application server's configuration. Least privilege for this connector is decided in AD's ACLs, not in IIQ.

### Step 3 — Secure the LDAP read channel

1. Preferred: **LDAPS on port 636** — requires a server-authentication certificate on every DC the connector may hit (usually from the internal CA via auto-enrollment). Export the issuing CA chain; the IIQ JVM truststore must trust it.
2. Acceptable alternative: port 389 with **LDAP signing and channel binding enforced** (a DC-side policy). Cleartext simple bind on 389 is a finding — your service-account password would cross the network readable.
3. Verify before touching IIQ: from the IIQ host, `openssl s_client -connect dc1.meridiannb.com:636` (or `ldp.exe` from a Windows box) and confirm the certificate chain.

### Step 4 — Install IQService on a member server, with TLS

1. Provision a Windows member server near the DCs (site affinity — Lesson 53's placement rule), e.g. lab name `mnb-iqsvc-lab`.
2. Install IQService from your IIQ version's media, register it as a Windows service, and set its log-on account to the least-privilege `svc-iiq-iqservice` account from the Lesson 53 worksheet — never Local System with Domain Admin, never Domain Admin.
3. Enable **TLS between IIQ and IQService** (certificate on the IQService host, CN matching the hostname; follow your version's install guide for the exact registration commands — port is commonly 5050 for cleartext / a second port for TLS, so confirm and document).
4. Walk `~/iiq-lab-data/connectors/ad/iqservice-checklist.md` line by line and update your Y/N/TBD marks from Lesson 53.

### Step 5 — Firewall paths

| Source | Destination | Port(s) | Purpose |
| --- | --- | --- | --- |
| IIQ server | DCs / GC | 636 (or signed 389); 3269/3268 if GC | Aggregation reads |
| IIQ server | IQService host | IQService TLS port (build-specific, commonly 5050/5051) | Provisioning writes |
| IQService host | DCs | Standard AD member-server ports (Kerberos 88, LDAP 389/636, SMB 445, RPC) | Windows-native operations |

No path is needed from DCs back to IIQ. Get these opened *before* the change window — firewall tickets are the classic go-live delay.

### Step 6 — Where the credentials live

The `svc-iiq-ad` bind password is entered once into the Application (encrypted in the IIQ database) and mastered in the vault; the IQService log-on account password is mastered in the vault and set on the Windows service. Neither appears in the repo, the binder, or a lab notebook. Fictional lab values only.

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq` as `spadmin`
- [ ] Lesson 53 checklist marked Y/N/TBD; network sketch `MNB-iqservice-network-53.txt` exists
- [ ] Lesson 55 feature matrix AD row reviewed (`ENABLE`, `PROVISIONING`, `PASSWORD` expectations)
- [ ] Decide your path: live lab domain available? If not, Tasks 2–6 still run — you will save configuration and defer Test Connection, then complete the Task 7 fallback

---

## Lab procedure

### Task 1 — Reconfirm the checklist gates

Every production onboarding opens by re-reading the design gates, because configuration drifts from design silently. Two minutes here prevents rebuilding the app later.

1. Open `~/iiq-lab-data/connectors/ad/iqservice-checklist.md`.
2. Confirm the Application-type line reads **Active Directory - Direct**.
3. Confirm the correlation line: `sAMAccountName` ↔ `userName`, `employeeID` ↔ `employeeId`.
4. Answer the Exchange gate for this lab: **No** for now (Lesson 57 makes it an explicit signed decision).

**Expected result:** Type, correlation, and Exchange gates answered on the checklist.

### Task 2 — Create the application `MNB-ActiveDirectory`

This is the primary, native path: the real connector form, filled the way you would against a live forest. In production this form consumes the Step 1–5 outputs — service account, LDAPS, IQService host.

1. **Applications** → Add New → **Active Directory - Direct** (or equivalent menu path).
2. Name: `MNB-ActiveDirectory`. Owner: Technology (lab: `spadmin`).
3. Forest/domain section (labels vary by version — record equivalents, never invent):
   - Forest / domain name: `meridiannb.com`
   - Domain controller / server: `dc1.meridiannb.com` (lab placeholder)
   - Port: `636` with SSL/TLS checked (or signed 389 — document which)
   - Bind user: `svc-iiq-ad` (as DN or domain\user per your build); password: lab placeholder noting "real value in vault"
   - GC usage: off for the single-domain lab; note the forest decision from Concepts
4. IQService section: host `mnb-iqsvc-lab`, the TLS port from your install guide, TLS enabled.
5. Save. If you have a live target, click **Test Connection** now.

**Expected result:** `MNB-ActiveDirectory` listed under Applications. Live path: Test Connection succeeds. No live target: app saved with connection deferred — that is acceptable and expected.

**If it fails:** LDAP error 49 with data `52e` = the bind credentials are wrong — fix the user DN format or vault password, not the schema. Timeout = firewall (Step 5) before anything else.

### Task 3 — Account schema, field by field

The schema decides what governance can see. Miss `userAccountControl` here and your leaver evidence (512 → 514) never materializes; miss `employeeID` and correlation limps on one leg.

1. Open the account schema on `MNB-ActiveDirectory`. Confirm/add:
   - `sAMAccountName` — display attribute
   - Native/account identity: your build's default (commonly `distinguishedName`) — record which
   - `givenName`, `sn`, `mail`, `userPrincipalName`
   - `employeeID` — the correlation tie-breaker; verify exact case
   - `userAccountControl` — or your build's derived status field; note which
   - `memberOf` — multi-valued, marked as the **entitlement attribute** (groups deepen in Lesson 57)
2. Leave the group schema for Lesson 57.

**Expected result:** Account schema shows all seven attributes, `memberOf` flagged as entitlement.

**If it fails:** Attribute missing from the picker → add it manually with the exact LDAP name; AD attribute names are case-preserving and typos fail silently at aggregation time.

### Task 4 — Correlation and the authoritative-source decision

Correlation is where Helen's story from "Why this matters" is prevented. Configure the keys, then close the door that creates orphan identities.

1. On the correlation configuration (assignment rule or correlation wizard, per your build):
   - Primary: application `sAMAccountName` ↔ identity `userName`
   - Tie-breaker: `employeeID` ↔ `employeeId`
   - Secondary only: `mail` ↔ `email` — document that email is mutable (marriage renames) and must never be primary
2. **Create identities from this application: OFF.** `MNB-HR` remains the only authoritative source. An AD account with no HR match must surface as *uncorrelated*, not spawn a ghost identity.
3. Note the operational control: uncorrelated-accounts report reviewed weekly by IAM.

**Expected result:** Correlation keys configured in the app; create-identities disabled; the weekly-review control noted.

**If it fails:** If your lab build lacks the wizard, define the same pairs in the Task 7 correlation file — the design is the deliverable.

### Task 5 — Search DN scope and provisioning stubs

Scoping decides which accounts IIQ governs. Aggregating the whole domain pulls in service accounts, kiosks, and disabled relics — noise that swamps certifications.

1. Set the account search DN(s) on the application:
   - Employees: `OU=Employees,DC=meridiannb,DC=com`
   - Contractors: `OU=Contractors,DC=meridiannb,DC=com` (a second search DN — contractors like `raj.external` hold real access; excluding them is the classic blind spot)
2. Add the user filter if your build exposes one: `(&(objectCategory=person)(objectClass=user))`.
3. Stub the provisioning policy (forms are built properly in Lessons 57/61): create needs `CN`, `sAMAccountName`, initial password, target OU, `mail`; leaver needs disable (ENABLE feature) and optional OU move. Do **not** execute a live create in this lesson.

**Expected result:** Two search DNs saved on the app; provisioning stub list recorded.

### Task 6 — The `Aggregate MNB-ActiveDirectory` task

Aggregation is your continuous inventory, and its Task Result is the audit evidence. Even a deferred run is evidence — of a documented, deliberate state.

1. Tasks → New → Account Aggregation: name it exactly `Aggregate MNB-ActiveDirectory`.
2. Live target: Run Now. Record accounts scanned/created and errors. Spot-check `helen.ross` and `priya.wire` — each cube should show an AD account link, correlated (not created) via `sAMAccountName` or `employeeID`.
3. No live target: save the task definition and write a dated deferred note — "Test Connection / aggregation deferred: no live DC in lab."
4. Schedule design either way: nightly, **after** `MNB-HR` aggregation and before the Identity Refresh — correlation targets must exist before AD accounts arrive.

**Expected result:** Task exists; live run success with two correlated spot-checks, **or** a dated deferred note.

**If it fails:** Zero accounts on a live run → search DN typo (DN components are comma-separated, no spaces after commas by convention) or the filter excludes everyone. Connection errors without a DC are expected — capture the error text as training evidence and move on.

### Task 7 — Lab-without-live-target fallback (secondary path)

**Use this only if you have no live domain.** The native configuration in Tasks 2–6 is the lesson; this fallback preserves the design artifacts so Lesson 57 and the binder stay unblocked.

1. If the connector type itself was unavailable in your lab image, document every Task 2 field in `~/iiq-lab-data/connectors/ad/MNB-ActiveDirectory-shell-notes-56.md` — that file counts as the shell.
2. Write `~/iiq-lab-data/connectors/ad/MNB-AD-schema-correlation-56.md` containing: the seven schema attributes from Task 3, the correlation table below, the line "**create identities = NO — MNB-HR authoritative**", and the two search DNs from Task 5.

| AD attribute | Identity attribute | Role |
| --- | --- | --- |
| `sAMAccountName` | `userName` | Primary |
| `employeeID` | `employeeId` | Tie-breaker |
| `mail` | `email` | Secondary only |

**Expected result:** Both files exist with every design decision captured; nothing about the lesson depended on a green Test Connection.

### Task 8 — Control owner and SLA card

An application without a named control owner is an application nobody defends in an exam. Fill the card before go-live, not after the finding.

1. Record in the correlation file (or app description):

| Field | Value |
| --- | --- |
| App | `MNB-ActiveDirectory` |
| Control owner | Technology |
| Operate | IAM |
| Disable SLA | 4 hours from HR leaver aggregate |
| Aggregate SLA | Nightly, before Identity Refresh |

**Expected result:** Owner/SLA card complete — no blank cells.

**If it fails:** No owner identified → escalate and assign before go-live; a blank owner is itself a finding.

### Task 9 — Test plan from the checklist

Production cutovers run a written, ordered test plan so partial progress is visible and defensible.

1. Copy the checklist's test-plan line into your notes as a table: **aggregate → correlate → create → disable → delete (lab only)**.
2. Add a status column and mark each step: `design-complete`, `executed`, or `deferred (no live target)`.

**Expected result:** Five-row test plan with honest statuses.

---

## Acceptance criteria

- [ ] Checklist gates (type, correlation, Exchange) reconfirmed
- [ ] `MNB-ActiveDirectory` created as Active Directory - Direct with forest/domain + IQService fields — or shell-notes fallback file
- [ ] Account schema includes `employeeID`, `userAccountControl`, and `memberOf` as entitlement
- [ ] Correlation `sAMAccountName`↔`userName`, `employeeID`↔`employeeId`, `mail` secondary; **create identities = NO** documented
- [ ] Search DNs `OU=Employees,...` and `OU=Contractors,...` set
- [ ] `Aggregate MNB-ActiveDirectory` exists — live success with spot-checks, or dated deferred note
- [ ] Real-world setup steps (delegation, LDAPS, IQService TLS, firewall) understood and in the binder
- [ ] Owner/SLA card and statused test plan written

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Bind fails: LDAP error 49, data `52e` | Invalid credentials — wrong bind DN format or stale vault password | Verify DN vs `domain\user` format for your build; re-sync password from vault |
| Error 49, data `775` | Service account locked out (often a second system using an old password) | Unlock in AD; hunt the stale credential before it re-locks |
| Aggregation slow / partial results with referral errors | Referral chasing — search DN spans a partition the DC redirects elsewhere | Scope DNs inside one domain, or use a GC for forest reads (beware the partial attribute set) |
| Test Connection: connection refused to IQService | IQService not running, wrong port, or firewall | Check the Windows service, confirm the port from the install guide, verify the IIQ→IQService allow rule |
| Password reset works in test, fails in prod OU | Delegation granted on the test OU only | Extend Step 2 delegation to every in-scope OU; re-verify the ACE list |
| Account looks disabled in AD but active in IIQ | `userAccountControl` missing from schema, or aggregation stale | Add UAC to the schema; check value (514/66050 = disabled); re-run aggregation |

---

## Training binder evidence

- Screenshot: `MNB-ActiveDirectory` definition (connection + IQService sections, password field redacted) — or the shell-notes file
- `MNB-AD-schema-correlation-56.md` with the correlation table and "create identities = NO"
- Real-world setup worksheet: delegated rights list, LDAPS decision, firewall table (no secrets!)
- `Aggregate MNB-ActiveDirectory` Task Result or the dated deferred note
- Owner/SLA card and statused test plan

**Examiner question:** *"Is Active Directory authoritative for workforce identity at Meridian? Show me the setting, and show me what happens to an AD account that matches no HR record."*

---

## Knowledge check

1. Why does Meridian use Active Directory - Direct instead of the generic LDAP connector?
2. Name the two correlation pairs, the secondary pair, and why the DN would be a bad correlation key.
3. Should `MNB-ActiveDirectory` create identities? What happens to a non-matching AD account instead?
4. Which operations travel over the LDAP read channel, and which require IQService?
5. What do `userAccountControl` values 512 and 514 mean, and why does the difference matter for leaver evidence?
6. What silently breaks if you aggregate a forest through a Global Catalog without checking the partial attribute set?

### Answers

1. Direct adds Windows-native operations via IQService — password set/reset, enable/disable, Exchange — that pure LDAP cannot perform properly against AD.
2. `sAMAccountName`↔`userName` (primary), `employeeID`↔`employeeId` (tie-breaker), `mail`↔`email` secondary only. The DN is the object's *location*: it changes on every OU move, orphaning the account.
3. No — `MNB-HR` is the sole authoritative source. Non-matching accounts surface on the uncorrelated-accounts report, reviewed weekly by IAM.
4. Aggregation (account and group reads) is LDAP(S) from the IIQ JVM; password set, enable/disable, create/modify, and Exchange operations go through IQService.
5. 512 = enabled normal account; 514 = the same with the ACCOUNTDISABLE bit set. The 512→514 flip in a post-leaver aggregation is the proof the disable actually executed.
6. Attributes outside the GC's partial set — notably `employeeID` — come back blank, silently killing the tie-breaker correlation.

---

## Further reading

- [Microsoft Learn — Active Directory Domain Services overview](https://learn.microsoft.com/windows-server/identity/ad-ds/get-started/virtual-dc/active-directory-domain-services-overview) — the vendor's own grounding in DCs, partitions, and the object model; skim before any AD design conversation. Search the same site for "userAccountControl flags" for the full bitmask table.
- [Microsoft Learn — Active Directory security groups](https://learn.microsoft.com/windows-server/identity/ad-ds/manage/understand-security-groups) — read ahead of Lesson 57; explains group types and scopes with the authority you will quote in design reviews.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search "Active Directory connector" and "IQService installation" for the version-specific application guide, exact field names, and the current IQService port/TLS registration steps.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — real-world threads on 52e bind failures, IQService TLS setup, and GC-vs-DC aggregation trade-offs.
- [RFC 4511 — LDAP: The Protocol](https://www.rfc-editor.org/rfc/rfc4511) — the protocol underneath the read channel; the result-code section decodes errors like 49 at the source.
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks) — the Microsoft Windows Server benchmark covers LDAP signing/channel binding hardening, the control behind the "no cleartext 389" rule.

---

## Stretch lab

Export the `MNB-ActiveDirectory` Application XML (Debug pages or console), redact the encrypted password field, and file it in the binder — configuration-as-evidence. Then pre-map the `userAccountControl` values you expect to see across the leaver demo (512 → 514, and 66048 → 66050 for a non-expiring-password service account) so Lesson 57's disable sequence has predicted before/after values. Finally, if the Windows team publishes Meridian's real OU tree, align your search DNs to it and note every delta from the lab placeholders.

---

## Summary

- `MNB-ActiveDirectory` is a **non-authoritative** Active Directory - Direct target: LDAP(S) reads for aggregation, IQService for the Windows-native writes, and create-identities firmly off.
- Correlation rides stable keys — `sAMAccountName`↔`userName` with `employeeID`↔`employeeId` as tie-breaker — never the DN, never email as primary.
- The real engineering happens outside IIQ: delegated least-privilege rights on target OUs, LDAPS or signed 389, IQService with TLS, and firewall paths — all of it binder evidence whether or not a live DC exists.

---

**Previous:** [Lesson 55 — Provisioning Feature Matrix](55-provisioning-feature-matrix.md)  
**Next:** [Lesson 57 — AD Groups, OUs & Exchange](57-ad-groups-ous-exchange.md)
