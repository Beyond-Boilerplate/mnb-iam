# Lesson 84 — Windows Local Connector

**Level:** Intermediate  
**Track:** Connectors — Infra, Logical, PAM  
**Time:** 90–120 min  
**Prereq:** Lesson 83 — Linux / Unix Connector; Lesson 56 — Active Directory Connector (contrast)  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (Windows servers)
- Repo: `lab-data/connectors/ad/iqservice-checklist.md`
- Repo: `lab-data/connectors/features-string-glossary.md`
- Runtime: `~/iiq-lab-data/connectors/`

---

## Learning objectives

You will be able to:

- Differentiate **Windows Local - Direct** (SAM database on the member server) from **Active Directory - Direct** (Lesson 56)
- Explain why local Administrators on member servers are a classic audit finding even when AD is well governed
- Perform the real-world setup: IQService dependency, TLS, service account, and host scope
- Create and configure **MNB-Windows-Local** with local group entitlements and correlation rules for named vs shared accounts
- Design break-glass and leaver patterns for local SAM accounts
- Complete the lesson with or without a live Windows host (mock fallback provided)

---

## Why this matters

**Business.** Meridian’s AD forest (Lesson 56) covers most human access — but some Windows member servers still keep **local SAM accounts** for break-glass, appliance-like utilities, or isolated segments where domain auth is unavailable. Last quarter an examiner found `.\Administrator` and a stale `jordan.reed` local admin on a payment jump box that everyone assumed was “covered by AD groups.” Domain governance had never seen those SIDs.

**Control / audit.** Domain aggregation does **not** automatically inventory local SAM. Examiners ask for continuous inventory and disablement of local privileged groups on servers that still have them. Your answer must be an explicit Application boundary — **MNB-Windows-Local** — with IQService-backed aggregation Task Results and a leaver path that disables the local account, not only the domain user.

---

## Concepts

### SAM vs Active Directory — two directories

| Plane | Where accounts live | Meridian application | What it governs |
| --- | --- | --- | --- |
| **Active Directory** | Domain NC on DCs | `MNB-ActiveDirectory` (Lesson 56) | Domain users/groups, OU, disable UAC bit |
| **Windows Local (SAM)** | Local Security Accounts Manager on **that server** | `MNB-Windows-Local` (this lesson) | Local users + local groups (`Administrators`, `Remote Desktop Users`, …) |

A domain-joined server can have **both**. Disabling `jordan.reed` in AD does nothing to a **local** `jordan.reed` that was created on the box during an outage. That asymmetry is why local admins remain a finding after “we finished AD.”

### Why local Administrators are a finding

Local Administrators membership means full control of that host: install software, read any file, dump credentials, disable agents. Standing local admin for humans is almost always wrong when AD and LAPS/gMSA patterns exist. Meridian rules of thumb:

- Prefer **domain groups** nested into local Administrators via GPO/Restricted Groups (governed in AD) when the host is domain-joined.
- Keep **Windows Local** for: true non-domain hosts, documented break-glass local accounts, and residual discovery of unexpected local users.
- Every unexpected local admin in aggregation is a ticket, not a shrug.

### IQService dependency

Unlike many Linux direct-SSH patterns (Lesson 83), Windows Local remote operations in IdentityIQ commonly depend on **IQService** on a Windows host that can reach the targets (RPC / remote SAM APIs per your version). Lesson 56 already taught IQService for AD; the same service often brokers Windows Local — complete the checklist rows for TLS, service account, and connectivity even when Exchange/OU rows are N/A.

### Contrast with Lesson 56 AD Direct

```
Lesson 56 — MNB-ActiveDirectory
   └── Domain identities; disable = ACCOUNTDISABLE
   └── Groups are domain groups
   └── IQService + AD SIEM/UAC story

Lesson 84 — MNB-Windows-Local
   └── Per-server SAM identities
   └── Groups are *local* groups on that server
   └── Still typically IQService-dependent
   └── Does NOT replace AD; fills the SAM blind spot
```

Rule: **If the account is a domain account, do not duplicate it as a “local” row in this app without justification.** Govern domain privilege in AD; use this app for local SAM principals.

---

## How it works

The Windows Local connector enumerates local users and group memberships on target servers and provisions create/disable/group changes through IQService (typical enterprise pattern). Exact Application field labels vary — use “or equivalent menu path” and your version’s guide.

```
IdentityIQ
        │
        ▼
   IQService (Windows)
        │  remote SAM / local account APIs
        ▼
Target member server(s)
        ├── Local users (SAM)           → accounts
        ├── Local groups + members      → entitlements
        ├── Disable local user          → leaver control
        └── Add/remove local group      → entitlement grant/revoke
```

| Operation | Target behavior | IIQ behavior |
| --- | --- | --- |
| Account aggregation | Enumerate local users | Account per local username (scoped per host/app design) |
| Entitlement aggregation | Local group memberships | `Administrators`, `Remote Desktop Users`, … as ManagedAttributes |
| Disable | Disable local account | ENABLE / disable feature |
| Group revoke | Remove from local Administrators / RDP | Entitlement remove |
| Password set | Local password | Only if approved; vault-backed — never lesson markdown |

**Multi-host design:** Production often uses one Application per host class or a connector feature for multiple hosts — document Meridian’s choice. Lab default: single logical app `MNB-Windows-Local` representing the jump/utility class.

---

## Real-world setup (outside IIQ)

### Step 1 — Decide what stays local

1. List host classes: break-glass jump boxes, non-domain utilities, appliances.
2. For domain-joined app servers: prefer Restricted Groups / AD-driven local admin; use Windows Local aggregation as **discovery** to find violations.
3. Write the SoT rule: domain account privilege → AD app; local SAM principal → this app.

### Step 2 — IQService

1. Reuse or place IQService near targets (same checklist mindset as Lesson 56 / `iqservice-checklist.md`).
2. TLS for IQService client connection; service account with rights to manage local accounts on targets (least privilege — not Domain Admin).
3. Firewall: IIQ → IQService; IQService → targets (RPC/dynamic ports per Platform standard — capture in worksheet, don’t guess production ports in git).

### Step 3 — Service account and LAPS

1. Connector / IQService account vaulted; rotation owned by Platform.
2. Break-glass local Administrator passwords: **LAPS** or vault checkout — IIQ must not store them in cleartext config exports.
3. Guardrail: connector cannot disable the last break-glass without a documented exception process.

### Step 4 — Governance records

Document: host list, IQService endpoint, TLS yes, phase 1 (aggregate) vs phase 2 (provision), owner Platform Ops, contrast note to `MNB-ActiveDirectory`.

---

## Before you start

- [ ] IIQ up; `spadmin` access
- [ ] Copy/read `~/iiq-lab-data/connectors/ad/iqservice-checklist.md`
- [ ] Lesson 56 AD notes available (or checklist alone)
- [ ] Decide path: live lab Windows host **or** mock fallback in Task 4
- [ ] Binder: `connectors/windows-local/`

---

## Lab procedure

### Task 1 — Local vs AD decision memo

Ground the boundary before creating objects.

1. Open the matrix; record **Windows Local - Direct** for local SAM.
2. Write Meridian rule: *If the principal is a domain account, govern it in `MNB-ActiveDirectory` (Lesson 56). Use `MNB-Windows-Local` for local SAM accounts and for discovery of unexpected local users/groups.*
3. List two host classes that stay in scope: (a) break-glass local admin on jump hosts, (b) non-domain utility host.
4. Note the examiner finding pattern: “AD looks clean; local Administrators still populated.”

**Expected result:** Decision memo clarifying no unjustified double-governance of the same access in AD + Local.

### Task 2 — IQService checklist pass

1. Open `iqservice-checklist.md`.
2. Mark required for Windows Local: IQService host placement, TLS, service account, aggregate→create→disable test plan.
3. Mark Exchange / OU provisioning rows **N/A** with rationale (those are AD/Exchange, Lesson 56/57).
4. Save annotated copy in binder as `MNB-Windows-Local-IQService.md`.

**Expected result:** Annotated checklist with required vs N/A rows clear.

**If it fails:** Complete network/TLS rows at minimum; leave install steps TBD with owner.

### Task 3 — Create MNB-Windows-Local (native primary)

1. Applications → Add New → **Windows Local - Direct** (or equivalent menu path).
2. Name: `MNB-Windows-Local`. Description: “local SAM / break-glass / discovery — not a substitute for AD.”
3. Connection: target host(s), IQService host reference, credentials from vault (lab: placeholders).
4. Owner: Platform Ops; governance contact `helen.ross`. **Not authoritative.**
5. Live host: Test Connection via IQService path.

**Expected result:** Application `MNB-Windows-Local` saved; live path Test Connection success.

**If it fails:** IQService down / TLS / firewall first; then local rights for the service account. Template missing → shell Application with connector type in Description; escalate license/pack.

### Task 4 — Schema and local group entitlements

1. Account attributes: Username (native identity), Full Name, Disabled, password-expired flags (document as available in your version).
2. Entitlements = local groups:
   - `Administrators` — critical / dual approve / monthly privileged cert
   - `Remote Desktop Users` — medium / manager approve
   - `Users` — usually omit from requestable catalog
3. Correlation: named break-glass IDs `username` ↔ identity `userName`; **shared** accounts (`Administrator`, `svc-*`) marked non-human — exclude from normal people correlation / manager certs.
4. featuresString from glossary: expect `PROVISIONING`, `ENABLE`, possibly `PASSWORD` — confirm before enabling password ops.
5. **Create identities: OFF.**

**Expected result:** Schema + entitlement risk table; shared-account policy sentence.

### Task 5 — Mock inventory (fallback: no live host)

1. Create `~/iiq-lab-data/connectors/windows-local/MNB-Windows-Local-mock.csv`:

```csv
username,groups,disabled,accountType
jordan.reed,Administrators|Remote Desktop Users,false,human-local
kai.nguyen,Remote Desktop Users,false,human-local
Administrator,Administrators,false,shared-breakglass
samir.hassan,Remote Desktop Users,true,human-local
```

2. Shadow-aggregate via DelimitedFile (pipe-split groups). Description must say proxy/mock.
3. Analyst read: Jordan is local **Administrators** (finding unless break-glass ticket); Kai is RDP-only (acceptable for support jump); built-in Administrator present (must be vault/LAPS governed, not certified as a person); Samir disabled (leaver evidence).

**Expected result:** Four mock accounts; Jordan local-admin finding and shared Administrator handling documented.

### Task 6 — Account Aggregation

1. Create `MNB-Windows-Local-Account-Aggregation`; run live or shadow.
2. Spot-check Jordan/Kai/Samir; confirm shared Administrator did **not** create a new identity cube.
3. Optionally compare: does AD show Jordan as disabled while local still enabled? That delta is the whole point of this connector.

**Expected result:** Task Result + written note if AD vs local state can diverge.

**If it fails:** Live RPC errors → IQService checklist. Shadow zero rows → path/delimiter.

### Task 7 — Provisioning, break-glass, and leaver

1. Policy stubs: Create local user, Add/Remove `Administrators` / `Remote Desktop Users`, Disable.
2. Break-glass rule: local Administrators membership requires Security + Tech Director; **≤8-hour sunset** (Lessons 28/37 intent); ticket required.
3. Leaver (same day):
   1. Remove from `Administrators` and sensitive local groups.
   2. **Disable** the local account (the control — parallel to Lesson 56’s AD disable, but on SAM).
   3. Re-aggregate — disabled=true, privileged groups empty.
4. Never store local admin passwords in markdown or git — vault / LAPS only.
5. Phase plan: phase 1 aggregation + discovery tickets; phase 2 provisioning after IQService hardening sign-off.

**Expected result:** Policies saved + break-glass SLA + three-step leaver card.

### Task 8 — Examiner drill and residual risk

1. Answer: *"Show that local admin on the payment jump box is inventoried and that leavers lose it."* Artifacts: aggregation showing Administrators membership, revoke/disable provisioning evidence, post-leaver Task Result.
2. Record `RR-WINLOCAL-01`: *Domain users nested into local Administrators via GPO may appear differently than SAM-only users — Restricted Groups design must be documented so certs target the right plane (AD vs local).* Owner: Platform Ops.
3. Explicit contrast sentence for the binder: *Lesson 56 proves domain disable; this lesson proves local SAM disable — both may be required for one human.*

**Expected result:** Proof steps + residual risk + Lesson 56 contrast sentence.

---

## Acceptance criteria

- [ ] Local vs AD decision memo written (SoT rule clear)
- [ ] IQService checklist annotated for Windows Local
- [ ] `MNB-Windows-Local` created; local groups as entitlements; create-identities off
- [ ] Aggregation evidence (live or mock) with Jordan admin finding + shared Administrator handling
- [ ] Break-glass SLA + leaver card (groups then disable then re-aggregate)
- [ ] Examiner proof steps + `RR-WINLOCAL-01` + Lesson 56 contrast recorded

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Provision fails / RPC errors | IQService down, TLS, or firewall | Fix checklist TLS/ports; verify IQService service account |
| Domain account “duplicated” as local | Wrong app boundary / local shadow account exists | Prefer AD for domain principals; ticket to remove unexpected local duplicates |
| Shared admin correlated to a person | Bad correlation | Mark non-human; exclude from manager certs |
| Password in XML export | Misconfig | Encrypt; scrub binder; rotate |
| AD disabled but local still works | Exactly the risk this lesson teaches | Disable local account; fix leaver to cover both planes |
| Template missing | Version/license | Shell + Description; escalate |

---

## Training binder evidence

- Local vs AD memo + Lesson 56 contrast sentence
- Annotated IQService checklist
- Application screenshot `MNB-Windows-Local`
- Group entitlement risk table + aggregation Task Result / findings
- Break-glass SLA + leaver card
- Examiner proof + `RR-WINLOCAL-01`

---

## Knowledge check

1. When do you choose Windows Local - Direct over AD Direct?
2. Why are local Administrators a finding even if AD certifications look clean?
3. Why annotate the AD IQService checklist for this connector?
4. How should shared `Administrator` accounts be treated in correlation and certifications?
5. What is the Meridian leaver order for a local privileged account?
6. What can be true for `jordan.reed` after Lesson 56 disable alone?

### Answers

1. When governing local SAM accounts (non-domain hosts or explicit local/break-glass accounts), not domain identities — AD Direct remains the plane for domain users/groups.
2. Local SAM membership is invisible to domain aggregation; standing local admin is full control of the host and a classic exam finding.
3. Windows Local remote operations typically still depend on IQService TLS, placement, and service accounts — Exchange/OU rows may be N/A, but IQService itself is not.
4. As non-human / shared break-glass: vault or LAPS, privileged inventory, not manager people-certification as if they were Helen or Jordan.
5. Remove privileged local groups, disable the local account, re-aggregate for evidence.
6. His domain account is disabled while a local SAM account on a jump box can still allow interactive/admin access — both planes must be covered.

---

## Further reading

- [Microsoft Learn: Local accounts](https://learn.microsoft.com/en-us/windows/security/identity-protection/access-control/local-accounts) — what SAM local users are and why built-in Administrator needs special handling.
- [Microsoft Learn: Active Directory vs local accounts (security guidance search)](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/plan/security-best-practices/best-practices-for-securing-active-directory) — AD securing practices; use alongside Restricted Groups designs that reduce local SAM sprawl.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “Windows Local connector” and “IQService” for version-specific installation and featuresString.
- [CIS Microsoft Windows Server Benchmarks](https://www.cisecurity.org/benchmark/microsoft_windows_server) — local account and admin group hardening items examiners recognize.
- [FFIEC Information Security](https://www.ffiec.gov/press/pr090906a.htm) (current FFIEC IT Examination Handbook — Information Security) — privileged access and inventory expectations for server administration.

---

## Stretch lab

Draft a population “Local Administrators on jump hosts” for a monthly privileged certification dry-run, and write the remediation play: revoke local Administrators → verify via aggregation → open Platform ticket if GPO Restricted Groups should have been the SoT instead. Optionally cross-check one persona in both `MNB-ActiveDirectory` and `MNB-Windows-Local` and document any divergence.

---

## Summary

- Windows Local is a deliberate SAM governance surface — it does not replace Lesson 56 AD Direct; it closes the local-admin blind spot on member servers.
- IQService, TLS, and least-privilege service accounts are part of the connector design, not optional plumbing.
- Examiner-ready evidence is aggregation of local Administrators, break-glass with sunset, and leaver disable on the **local** account with Task Results.

---

**Previous:** [Lesson 83 — Linux / Unix Connector](83-linux-unix-connector.md)  
**Next:** [Lesson 85 — Logical Applications](85-logical-applications.md)
