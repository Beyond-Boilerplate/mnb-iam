# Lesson 83 — Linux / Unix Connector

**Level:** Intermediate  
**Track:** Connectors — Infra, Logical, PAM  
**Time:** 60–90 min  
**Prereq:** Lesson 82 — Mainframe RACF for Banking  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (Unix jump hosts)
- Repo: `lab-data/connectors/ad/iqservice-checklist.md` (contrast: Windows path)
- Runtime: `~/iiq-lab-data/connectors/`

---

## Learning objectives

You will be able to:

- Select **Linux - Direct** vs Unix connector for Meridian bastion / midrange hosts
- Create Application shell `MNB-Linux-Bastion` with account and group entitlement maps
- Document SSH key vs password provisioning posture and sudo group governance
- Complete a lab-without-live-target connection and aggregation worksheet
- Align Linux local accounts with PAM expectations (preview Lesson 86)

---

## Why this matters

**Business.** Meridian engineers reach payment and core platforms through Linux jump hosts. Local accounts and `sudo` groups are a frequent breach path when left unmanaged.

**Control / audit.** Examiners ask how bastion access is joined, certified, and removed on leaver day. “SSH keys on a shared wiki” fails. IIQ must inventory accounts/groups and drive disablement even when hosts are not always reachable from the laptop lab.

---

## Concepts

Matrix row:

| system | preferredConnector | alternate | notes |
| --- | --- | --- | --- |
| Unix jump hosts | Linux - Direct | Unix | Bastion / midrange |

```
Identity cube
     │
     ▼
MNB-Linux-Bastion (uid)
     ├── primary group / secondary groups
     ├── sudoers-related groups (entitlements)
     └── login shell / home (attributes)
```

| Attribute / object | Lab treatment |
| --- | --- |
| `uid` / `username` | Native identity |
| `uidNumber` / `gidNumber` | Optional; document if managed |
| Groups | Entitlements (`mnb-ssh-users`, `mnb-sudo-ops`) |
| Password | Prefer key-based; PASSWORD feature only if approved |
| Disable | Lock account / expire / remove groups |

**Lab-without-live-target:** App shell, schema, provisioning forms, SSH network worksheet. Do not embed real host passwords in repo files.

---

## Before you start

- [ ] IIQ healthy at `http://localhost:8080/identityiq`
- [ ] Matrix CSV in `~/iiq-lab-data/connectors/`
- [ ] Know Meridian personas who might need bastion: `kai.nguyen`, `amelia.brooks`, `jordan.reed`
- [ ] Binder: `connectors/linux/`

---

## Lab procedure

### Task 1 — Connector selection note

1. Open matrix; record Linux - Direct as preferred for jump hosts.
2. Note when Unix connector appears (legacy midrange / AIX patterns)—document Meridian preference for Linux Direct on RHEL bastions.
3. Contrast with AD: domain users ≠ Linux local; bastion may use AD via SSSD **or** local—capture which Meridian intends.

**Expected result:** Decision note: Linux Direct for `MNB-Linux-Bastion`, AD integration posture stated.

**If it fails:** Default local Linux Direct inventory for this lesson; AD join is stretch.

---

### Task 2 — Create `MNB-Linux-Bastion`

1. Applications → Add New → **Linux - Direct** (or Unix if Linux missing—note substitution).
2. Name: `MNB-Linux-Bastion`.
3. Owner: Technology / Platform Ops; temporary `spadmin` OK with note.
4. Not authoritative.
5. In Description: “Lab shell — jump host governance.”
6. Save.

**Expected result:** Application listed with exact name.

**If it fails:** Create placeholder Application and set connector type text in Description.

---

### Task 3 — Schema and sudo group catalog

1. Document account schema: username, uidNumber, gidNumber, home, shell, status/lock.
2. Entitlements = groups. Seed:
   - `mnb-ssh-users`
   - `mnb-sudo-ops` (privileged)
   - `mnb-payments-support` (business-sensitive)
3. Correlation: username ↔ `userName`.
4. Flag `mnb-sudo-ops` as request-only / dual approval (Tech Director + Security).

**Expected result:** Schema worksheet + three groups with risk flags.

**If it fails:** Store catalog as `~/iiq-lab-data/connectors/linux-groups-stub.csv`.

---

### Task 4 — Provisioning policies (offline)

1. Create policy stubs: Create account, Add/Remove group, Disable/lock.
2. Fields: username (from identity `userName`), groups, comments/ticket.
3. Document password posture: “Keys via PAM/CyberArk; IIQ does not email passwords.”
4. Leaver: lock account + remove `mnb-sudo-ops` same day.
5. Save; redact secrets from any exported XML.

**Expected result:** Three policy stubs + password posture sentence in binder.

**If it fails:** Debug → create empty policies named `MNB-Linux-Create`, `MNB-Linux-Modify`, `MNB-Linux-Disable`.

---

### Task 5 — Connection worksheet (lab-without-live-target)

Complete this table in binder (no live SSH required):

| Item | Value |
| --- | --- |
| Hostnames | `bastion-lab-01.meridiannb.local` (example) |
| Port | 22 |
| Service account | `iiq-svc-linux` (least privilege) |
| Auth | SSH key path in vault — not in git |
| sudo for connector | Required? yes/no |
| Firewall owner | Platform Ops |
| Aggregate schedule | Nightly Account Aggregation |

**Expected result:** Completed worksheet; no secrets committed.

**If it fails:** Mark unknowns as TBD with owner names—do not invent production IPs.

---

### Task 6 — Optional proxy aggregation

1. Create `~/iiq-lab-data/apps/MNB-Linux-Bastion-proxy.csv` with `username,uid,groups,status`.
2. Rows for `kai.nguyen`, `amelia.brooks`, `jordan.reed`.
3. Optional Delimited proxy app + **Account Aggregation** for correlation practice.
4. Refresh identities; confirm accounts on cubes.

**Expected result:** Proxy Task Result **or** explicit skip with worksheet-only completion.

---

## Acceptance criteria

- [ ] Linux - Direct selected and documented
- [ ] `MNB-Linux-Bastion` shell exists
- [ ] Group catalog includes privileged sudo group
- [ ] Provisioning stubs + leaver lock note complete
- [ ] Connection worksheet complete without secrets in git
- [ ] Lab-without-live-target satisfied

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Connector cannot sudo | Service account rights | Request least-privilege sudoers snippet from Platform |
| Duplicate accounts (AD + local) | Hybrid join | Document authoritative account source; correlate carefully |
| SSH key failures | Wrong key / host key | Fix vault entry; never paste keys into Application XML in cleartext |
| Aggregation empty | Host unreachable | Use worksheet + proxy path |
| Sudo in birthright | Role error | Remove; request-only path |

---

## Training binder evidence

- Matrix decision note
- Application screenshot
- Group catalog with privilege flags
- Provisioning policy screenshots (redacted)
- Connection worksheet
- Optional proxy aggregation Task Result

---

## Knowledge check

1. Preferred connector for Meridian Unix jump hosts?
2. Name the Meridian Linux application object.
3. Which group is privileged / request-only in this lab?
4. What is Meridian’s stated password posture for bastions?
5. What mandatory lab path applies when hosts are unreachable?

### Answers

1. Linux - Direct (Unix as alternate).  
2. `MNB-Linux-Bastion`.  
3. `mnb-sudo-ops`.  
4. Prefer keys via PAM/vault; IIQ does not email passwords.  
5. App shell + schema + policies + connection worksheet (optional CSV proxy).

---

## Stretch lab

Draft sudoers intent: `%mnb-sudo-ops ALL=(ALL) NOPASSWD: /usr/bin/systemctl` limited commands—attach as non-authoritative design note for Platform Ops.

---

## Summary

- Bastion Linux accounts and sudo groups are first-class IIQ targets.
- Use Linux - Direct, named `MNB-Linux-Bastion`, with request-only sudo.
- Complete the lesson without live SSH via worksheet and optional proxy extract.

---

**Previous:** [Lesson 82 — Mainframe RACF for Banking](82-mainframe-racf-banking.md)  
**Next:** [Lesson 84 — Windows Local Connector](84-windows-local-connector.md)
