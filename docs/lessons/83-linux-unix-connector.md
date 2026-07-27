# Lesson 83 — Linux / Unix Connector

**Level:** Intermediate  
**Track:** Connectors — Infra, Logical, PAM  
**Time:** 90–120 min  
**Prereq:** Lesson 82 — Mainframe RACF for Banking  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (Unix / Linux jump hosts)
- Repo: `lab-data/connectors/ad/iqservice-checklist.md` (contrast: Windows path)
- Repo: `lab-data/connectors/features-string-glossary.md`
- Runtime: `~/iiq-lab-data/connectors/`

---

## Learning objectives

You will be able to:

- Explain Linux local accounts, secondary groups, and sudo-related group membership as IIQ accounts and entitlements
- Select **Linux - Direct** vs Unix connector patterns for Meridian hosts and document SSH key vs password posture
- Describe connectivity patterns: direct SSH from IIQ vs IQService-assisted patterns where your deployment uses them
- Create and configure **MNB-Linux-Hosts** with schema, correlation, and privileged sudo governance
- Design joiner/leaver for privileged shell access using Meridian personas `jordan.reed` and `kai.nguyen`
- Complete the lesson with or without live hosts (mock fallback provided)

---

## Why this matters

**Business.** Meridian engineers reach payment gateways, core adapters, and cloud bastions through Linux hosts. Last year `jordan.reed` kept a personal SSH key and `mnb-sudo-ops` membership on `pay-jump-01` after an incident “just in case.” Six weeks later the incident was closed, the ticket was archived, and the key still worked. Local accounts and sudo groups are a frequent breach path when left to tribal knowledge.

**Control / audit.** Examiners ask how bastion and midrange shell access is joined, certified, and removed on leaver day. “SSH keys on a shared wiki” fails. IIQ must inventory local (or host-scoped) accounts and groups, drive lockout and group removal, and produce Task Results — even when the laptop lab cannot SSH to production. This lesson builds that story on **MNB-Linux-Hosts**.

---

## Concepts

### Local accounts and what “sudo” really means

On a typical Meridian RHEL bastion:

| Object | What it is | IIQ treatment |
| --- | --- | --- |
| **Local account** (`/etc/passwd`) | Host-scoped login identity | Account; native identity usually `username` |
| **Primary / secondary groups** | Membership in `/etc/group` | **Entitlements** when they grant access |
| **sudoers via group** | e.g. `%mnb-sudo-ops ALL=(ALL) …` | The **group** is the entitlement; sudoers file is platform-owned |
| **Shell / home** | Login attributes | Account attributes, not entitlements |
| **SSH authorized_keys** | Credential material | Credential hygiene — often PAM/vault, not a certifiable entitlement |

The naive mistake: treating “has sudo” as a boolean attribute. You cannot certify or revoke a boolean cleanly. Model **`mnb-sudo-ops`** (and peer groups) as entitlements so revoke removes the group and the next aggregation proves it.

### SSH keys vs passwords

| Auth method | Meridian posture | IIQ implication |
| --- | --- | --- |
| **SSH public key** | Preferred for humans and service logins | IIQ may create the account + groups; keys often injected by PAM/CyberArk/config management — document the split |
| **Password** | Discouraged on bastions; locked or never set | `PASSWORD` feature only if Platform explicitly approves; never email passwords from IIQ |

If login is key-based, “disable” means **lock the account** (`usermod -L` / expire / nologin shell per standard) **and** remove sudo groups — not “reset password.”

### Linux - Direct vs Unix vs directory-joined hosts

| Pattern | When to use |
| --- | --- |
| **Linux - Direct** | Meridian preferred for RHEL/Ubuntu bastions and midrange Linux with local (or connector-visible) accounts |
| **Unix connector** | Legacy midrange / AIX-style patterns per matrix alternate |
| **AD/LDAP via SSSD** | Host is directory-joined — prefer governing the **directory group** that lands on the host (Lesson 56 patterns) rather than duplicating every local shadow account |

This lesson’s primary path is **local inventory via Linux - Direct** on hosts Meridian still treats as local-account authoritative. Hybrid joined hosts need an explicit “authoritative source” sentence so you do not double-govern the same access.

### Privileged shell narrative — jordan.reed and kai.nguyen

- **`jordan.reed`** (ops / cloud-adjacent): often needs `mnb-ssh-users` + sometimes `mnb-sudo-ops` for incident work — **time-bound**, dual-approved, never silent standing sudo.
- **`kai.nguyen`** (engineer): typically `mnb-ssh-users` and maybe `mnb-payments-support` for read/support paths — **not** standing `mnb-sudo-ops` by birthright.

When aggregation shows both with `mnb-sudo-ops`, that is a finding to investigate, not a success metric.

---

## How it works

SailPoint **Linux - Direct** (or Unix) connectors commonly use **SSH** (or an approved remote execution channel) as a service account to read `passwd`/`group` and to provision account and group changes. Some Meridian deployments route Windows-heavy IQService estates separately; Linux often talks **direct from the IIQ task server**. Confirm your version’s Application guide — never invent UI labels; use “or equivalent menu path.”

```
IdentityIQ (MNB-Linux-Hosts)
        │  SSH (key in vault) as svc account
        │  — or — approved jumphost / connector host pattern
        ▼
Linux host(s) in scope
        ├── getent passwd / account list     → accounts
        ├── getent group / memberships       → group entitlements
        ├── useradd / usermod / gpasswd      → create, lock, group grant/revoke
        └── sudoers (platform-owned)         → enforced by group membership
```

| Operation | Host behavior | IIQ behavior |
| --- | --- | --- |
| Account aggregation | Enumerate users in scope | Account per username |
| Entitlement aggregation | Group memberships | Managed attributes |
| Create | `useradd` (+ home/shell policy) | Create account plan |
| Disable / lock | Lock / expire / nologin per standard | Disable / ENABLE |
| Group add/remove | Modify secondary groups | Entitlement add/remove |

**IQService note:** IQService is central for many **Windows** connectors (Lesson 84 / 56). For Linux, document whether your install uses direct SSH from IIQ or an intermediate connector host. The governance model (accounts + groups) stays the same; only the wire changes.

One operational consequence: if IIQ task servers cannot reach bastions on port 22, enterprises often place a **connector jump host** inside the management VLAN with the vaulted key and tighter firewall rules — still “Linux - Direct” logically, but the network hop is explicit on the architecture worksheet.

---

## Real-world setup (outside IIQ)

### Step 1 — Host scope and naming

1. Inventory hosts in scope: bastions, payment jump boxes, midrange app servers — not every developer laptop.
2. Decide one Application per host class vs per host. Lab default: **one app `MNB-Linux-Hosts`** representing the bastion class; production may split `MNB-Linux-Bastion` / `MNB-Linux-Payments` later.

### Step 2 — Service account least privilege

1. Create `iiq-svc-linux` (name per standard) with SSH key auth only.
2. Phase 1: read rights sufficient to enumerate passwd/group (and sudo group membership).
3. Phase 2: least-privilege sudoers snippet allowing only the provisioning commands Platform approves (`useradd`, `usermod`, `gpasswd`, lock) — **not** unbounded root.
4. Vault the private key; never commit it; rotate on the key-rotation schedule.

### Step 3 — Network

1. IIQ task servers (or connector hosts) → TCP/22 on targets; firewall owner Platform Ops.
2. Host key / known_hosts management documented so aggregation does not break on rotate.
3. No production keys on personal laptops for the lab.

### Step 4 — sudoers and PAM alignment

1. Platform owns `/etc/sudoers.d/mnb-*` content; IAM owns group membership as entitlements.
2. Preview Lesson 86 PAM: privileged sessions may still need session recording / vault checkout — IIQ group revoke does not replace PAM.

---

## Before you start

- [ ] IIQ healthy at `http://localhost:8080/identityiq` as `spadmin`
- [ ] Matrix CSV in `~/iiq-lab-data/connectors/`; skim IQService checklist only for contrast
- [ ] Personas in mind: `jordan.reed`, `kai.nguyen`, `amelia.brooks`
- [ ] Decide path: live lab VM **or** mock fallback in Task 4
- [ ] Binder: `connectors/linux/`

---

## Lab procedure

### Task 1 — Design decisions and connector choice

1. Open the matrix; record **Linux - Direct** as preferred for Meridian Linux hosts; Unix as alternate for legacy midrange.
2. Write the AD/SSSD posture sentence: *If the host is directory-joined and sudo is granted by AD group, prefer AD entitlement governance; this app covers hosts where local accounts/groups remain authoritative.*
3. Application name: `MNB-Linux-Hosts`. Owner: Platform Ops; IAM governance owner `helen.ross`.
4. Sensitive groups: `mnb-sudo-ops` (critical), `mnb-payments-support` (high), `mnb-ssh-users` (medium).

**Expected result:** Design card with connector choice, AD-hybrid posture, owners, and sensitive groups.

### Task 2 — Create MNB-Linux-Hosts (native primary)

1. Applications → Add New → **Linux - Direct** (or Unix if Linux missing — note substitution in Description).
2. Connection fields (labels vary): host list or hostname, port 22, service account `iiq-svc-linux`, private key / credential reference from vault (lab: placeholder text).
3. Not authoritative. Save.
4. Live lab VM: Test Connection — success proves SSH + service account rights for a handshake.

**Expected result:** Application `MNB-Linux-Hosts` saved; live path Test Connection success.

**If it fails:** Firewall/key/host key first; then sudo rights for the svc account. Do not paste private keys into Application XML in git.

### Task 3 — Schema and sudo group catalog

1. Account schema: `username` (native identity), `uidNumber`, `gidNumber`, `home`, `shell`, lock/status.
2. Entitlements = groups. Seed:
   - `mnb-ssh-users`
   - `mnb-sudo-ops` (privileged / request-only / dual approval: Tech Director + Security)
   - `mnb-payments-support` (business-sensitive)
3. Correlation: `username` ↔ identity `userName`.
4. **Create identities: OFF.**
5. featuresString expectations from glossary: `PROVISIONING`, `ENABLE`; `PASSWORD` only if approved — Meridian bastion posture prefers keys.

**Expected result:** Schema worksheet + three groups with risk flags; password posture sentence.

### Task 4 — Mock inventory (fallback: no live host)

1. Create `~/iiq-lab-data/connectors/linux/MNB-Linux-Hosts-mock.csv`:

```csv
username,uidNumber,groups,status,authMethod
jordan.reed,1492,mnb-ssh-users|mnb-sudo-ops,active,ssh-key
kai.nguyen,1496,mnb-ssh-users|mnb-payments-support,active,ssh-key
amelia.brooks,1498,mnb-ssh-users,active,ssh-key
samir.hassan,1494,,locked,ssh-key
```

2. Shadow-aggregate via DelimitedFile (pipe-split groups). Description: proxy/mock for Linux training.
3. Read the stories: Jordan has standing sudo (finding unless break-glass ticket exists); Kai has payments support without sudo (good default); Samir locked (leaver pattern); Amelia SSH-only.

**Expected result:** Four mock accounts; Jordan sudo finding called out explicitly.

### Task 5 — Account Aggregation

1. Create `MNB-Linux-Hosts-Account-Aggregation`; run live or shadow.
2. Open `jordan.reed` and `kai.nguyen` cubes — confirm group entitlements match the narrative.
3. Schedule proposal: nightly; after HR aggregation.

**Expected result:** Task Result success; Jordan/Kai spot-checks documented.

**If it fails:** Live empty → svc cannot enumerate groups (rights) or wrong host. Shadow zero rows → delimiter / multi-valued config.

### Task 6 — Provisioning policies and password/key posture

1. Policy stubs: Create account, Add/Remove group, Disable/lock.
2. Create fields: username from identity `userName`, default groups (`mnb-ssh-users` only as birthright candidate), ticket/comment.
3. Document: *Keys via PAM/CyberArk/config management; IIQ does not email passwords; PASSWORD feature off unless Platform signs exception.*
4. Save; redact secrets from exports.

**Expected result:** Three policy stubs + key/password posture in binder.

### Task 7 — Privileged shell joiner / leaver

1. **Joiner (Kai-style):** create local account → add `mnb-ssh-users` → optional `mnb-payments-support` via request → aggregate verify. No sudo.
2. **Joiner (Jordan incident sudo):** request `mnb-sudo-ops` with dual approval + **8–24 hour sunset** (Lesson 37 intent) → aggregate shows membership → auto-remove or ticketed remove after sunset.
3. **Leaver (same-day):**
   1. Remove `mnb-sudo-ops` and sensitive groups first.
   2. Lock/expire account (and ensure keys invalidated per PAM/vault runbook).
   3. Re-aggregate — locked + empty privileged groups.
4. Explicitly write why removing groups before lock matters (defense in depth if lock stalls).

**Expected result:** Joiner variants + three-step leaver card with sudo sunset note.

### Task 8 — Examiner drill and residual risk

1. Answer: *"Prove a terminated engineer lost bastion sudo."* Artifacts: entitlement revoke log, post-term Task Result, account detail without `mnb-sudo-ops` and status locked.
2. Record `RR-LINUX-KEY-01`: *authorized_keys / vault checkouts not fully visible to this connector need PAM inventory compensating control.* Owner: Platform Ops / PAM team.
3. Record `RR-LINUX-SSSD-01` if hybrid: *Directory-joined sudo via AD groups governed in AD app — do not double-count without a source-of-truth rule.*

**Expected result:** Proof steps + residual risks with owners.

---

## Acceptance criteria

- [ ] Design card: Linux - Direct, hybrid AD posture, owners, sensitive groups
- [ ] Real-world setup understood: svc account, least-privilege sudoers, SSH network
- [ ] `MNB-Linux-Hosts` created; groups as entitlements; create-identities off; key posture documented
- [ ] Aggregation evidence (live or mock) with Jordan sudo vs Kai non-sudo narrative
- [ ] Provisioning stubs + joiner/leaver cards with sudo sunset
- [ ] Examiner proof steps + `RR-LINUX-KEY-01` recorded

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Connector cannot change groups | Service account sudoers too narrow/missing | Request least-privilege snippet from Platform — not NOPASSWD ALL |
| Duplicate accounts (AD + local) | Hybrid join without SoT rule | Document authoritative source; correlate carefully; avoid dual apps for same access |
| SSH auth failures | Wrong key, passphrase, or host key change | Fix vault entry / known_hosts; never paste keys into git |
| Aggregation empty | Host unreachable or filter excludes users | Use worksheet + mock; fix firewall |
| Sudo in birthright role | Role error | Remove; request-only + sunset |
| Password ops fail | Keys-only hosts | Expected — disable PASSWORD feature |
| Aggregation shows service accounts as people | `svc-*` / `iiq-svc-*` correlated | Exclude connector and system accounts from human populations; inventory separately |

---

## Training binder evidence

- Design card + matrix decision
- Connection worksheet (hosts, svc account name, key-in-vault — no private keys!)
- Aggregation Task Result + Jordan/Kai cube screenshots
- Provisioning stubs (redacted) + joiner/leaver cards
- Examiner proof + `RR-LINUX-KEY-01`

---

## Knowledge check

1. Why must sudo-related access be modeled as a group entitlement rather than a boolean attribute?
2. What is Meridian’s preferred connector for Linux bastion-class hosts?
3. How should `jordan.reed` vs `kai.nguyen` differ for `mnb-sudo-ops`?
4. Why might PASSWORD features be irrelevant on Meridian bastions?
5. What must a leaver runbook do besides locking the account?
6. What does `RR-LINUX-KEY-01` say this connector may not see?

### Answers

1. Entitlements are certifiable, risk-rated, and revocable via provisioning; booleans are not first-class ManagedAttributes.
2. Linux - Direct (Unix as alternate for legacy midrange).
3. Jordan may receive time-bound dual-approved sudo for incidents; Kai’s default is SSH (+ optional payments support) without standing sudo.
4. Login is SSH-key / PAM-vault based; passwords are discouraged and often unset.
5. Remove privileged groups (especially `mnb-sudo-ops`) and invalidate keys per PAM/vault; then re-aggregate for evidence.
6. authorized_keys material and vault checkouts outside group membership — needs PAM compensating inventory.

---

## Further reading

- [sudoers manual (sudo.ws)](https://www.sudo.ws/docs/man/sudoers.man/) — how group-based sudo actually evaluates; aligns entitlements with Platform’s sudoers.d files.
- [Linux-PAM documentation index](http://www.linux-pam.org/Linux-PAM-html/) — concepts behind auth stacks that sit beside account provisioning.
- [FreeIPA sudo rules documentation](https://www.freeipa.org/page/Documentation) — useful mental model when sudo is centralized in a directory (search “sudo” in FreeIPA docs); helps design the hybrid AD/SSSD posture sentence.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “Linux connector” / “Unix connector” for version-specific setup and featuresString.
- [CIS Distribution Independent Linux Benchmark](https://www.cisecurity.org/benchmark/distribution_independent_linux) — hardening checklist examiners and platform teams recognize; pair with IAM group governance, don’t substitute for it.
- [FFIEC Information Security](https://www.ffiec.gov/press/pr090906a.htm) (current FFIEC IT Examination Handbook — Information Security) — privileged access and remote administration expectations.

---

## Stretch lab

Draft a least-privilege sudoers intent for Platform Ops: `%mnb-sudo-ops ALL=(ALL) NOPASSWD: /usr/bin/systemctl, /usr/bin/journalctl` (example only — Platform owns the real file). Then propose a monthly privileged certification population for `mnb-sudo-ops` holders on `MNB-Linux-Hosts`.

---

## Summary

- Linux governance is local accounts plus **group entitlements** (SSH and sudo); keys and sudoers files need explicit ownership split with PAM/Platform.
- Prefer Linux - Direct for `MNB-Linux-Hosts`; document hybrid directory-joined hosts so you do not double-govern.
- Jordan’s standing sudo is the training finding; Kai’s SSH-without-sudo is the default engineer pattern; leaver = groups then lock then re-aggregate.

---

**Previous:** [Lesson 82 — Mainframe RACF for Banking](82-mainframe-racf-banking.md)  
**Next:** [Lesson 84 — Windows Local Connector](84-windows-local-connector.md)
