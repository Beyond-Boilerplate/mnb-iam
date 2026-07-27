# Lesson 84 — Windows Local Connector

**Level:** Intermediate  
**Track:** Connectors — Infra, Logical, PAM  
**Time:** 60–90 min  
**Prereq:** Lesson 83 — Linux / Unix Connector  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (Windows servers)
- Repo: `lab-data/connectors/ad/iqservice-checklist.md`
- Repo: `lab-data/connectors/features-string-glossary.md`
- Runtime: `~/iiq-lab-data/connectors/`

---

## Learning objectives

You will be able to:

- Differentiate **Windows Local - Direct** (SAM) from **Active Directory - Direct**
- Create Application shell `MNB-Windows-Local-Jump` for non-domain or break-glass local accounts
- Apply IQService checklist items that still apply to Windows Local provisioning
- Document Administrators / Remote Desktop Users as governed entitlements
- Complete lab-without-live-target aggregation and connection evidence

---

## Why this matters

**Business.** Some Meridian Windows servers keep local SAM accounts for break-glass, appliance-like hosts, or isolated segments. Untracked local Administrators are a classic audit finding.

**Control / audit.** Domain governance does not automatically cover local SAM. Examiners ask for inventory and disablement of local privileged groups on jump/RDP hosts. This lesson forces an explicit Application boundary.

---

## Concepts

Matrix:

| system | preferredConnector | alternate | notes |
| --- | --- | --- | --- |
| Windows servers | Windows Local - Direct | Active Directory - Direct | Local SAM when not domain |

```
Domain-joined server?
    │
    ├── Yes → prefer AD groups / gMSA (MNB-ActiveDirectory) when possible
    └── No / local break-glass → MNB-Windows-Local-Jump (Windows Local - Direct)
```

| Local group | Meridian treatment |
| --- | --- |
| Administrators | Privileged; request + dual approve; certify monthly |
| Remote Desktop Users | Medium; manager approve |
| Users | Birthright rare—usually omit |

IQService (from `ad/iqservice-checklist.md`) remains relevant when the Windows Local connector uses IQService for remote operations—complete TLS / service account rows even for local SAM targets.

**Lab-without-live-target:** Shell + schema + policies + IQService/network worksheet; optional CSV proxy.

---

## Before you start

- [ ] IIQ up; `spadmin` access
- [ ] Copy/read `~/iiq-lab-data/connectors/ad/iqservice-checklist.md`
- [ ] Lesson 56 AD notes available if present; otherwise use checklist alone
- [ ] Binder: `connectors/windows-local/`

---

## Lab procedure

### Task 1 — Decide Local vs AD

1. Open matrix; record Windows Local - Direct for local SAM.
2. Write Meridian rule: “If account is domain, do not duplicate in Windows Local app.”
3. List two host classes that stay Local: (a) break-glass local admin, (b) non-domain utility host.

**Expected result:** Decision memo clarifying no double-governance of the same account in AD + Local without justification.

**If it fails:** Default this lesson to break-glass local admin only.

---

### Task 2 — IQService checklist pass

1. Open `iqservice-checklist.md`.
2. Check items that apply to Windows Local remote management: IQService host near targets, TLS, service account, test plan aggregate→create→disable.
3. Mark Exchange / OU items N/A with rationale.
4. Save annotated checklist copy in binder as `MNB-Windows-Local-IQService.md`.

**Expected result:** Annotated checklist with N/A vs required rows clear.

**If it fails:** Complete network/TLS rows at minimum; leave install steps TBD.

---

### Task 3 — Create `MNB-Windows-Local-Jump`

1. Applications → Add New → **Windows Local - Direct** (or equivalent).
2. Name: `MNB-Windows-Local-Jump`.
3. Owner: Platform Ops; Description includes “local SAM / break-glass.”
4. Not authoritative.
5. Save.

**Expected result:** Application appears with exact name.

**If it fails:** Placeholder Application with connector type in Description.

---

### Task 4 — Schema and local groups

1. Account attributes: Username, Full Name, Disabled, Password expired flags (document).
2. Entitlements = local groups: `Administrators`, `Remote Desktop Users`.
3. Correlation: Username ↔ `userName` for named break-glass IDs; document shared accounts as **non-human** / exclude from normal identity correlation.
4. featuresString expectations: `PROVISIONING`, `ENABLE`, `PASSWORD` (confirm via glossary).

**Expected result:** Schema + entitlement table; shared account policy sentence.

**If it fails:** Use glossary to list features; schema in binder table only.

---

### Task 5 — Provisioning policies and break-glass

1. Policy stubs: Create local user, Add to Administrators / RDP, Disable.
2. Break-glass rule: local Administrator membership requires Security + Tech Director; 8-hour sunset note (align Lesson 28/37 intent).
3. Leaver: disable local account same day; remove Administrators.
4. Never store local admin passwords in lesson markdown or git—reference vault only.

**Expected result:** Policies saved + break-glass SLA note.

---

### Task 6 — Lab-without-live-target evidence

1. Connection worksheet: hostname, IQService endpoint, TLS yes/no, service account name (no password).
2. Optional proxy CSV `MNB-Windows-Local-proxy.csv` with `username,groups,disabled` for `kai.nguyen` RDP-only and one disabled row.
3. Run **Account Aggregation** on proxy if created; else attach worksheet only.

**Expected result:** Worksheet complete; optional aggregation Task Result.

---

## Acceptance criteria

- [ ] Local vs AD decision memo written
- [ ] IQService checklist annotated for Windows Local
- [ ] `MNB-Windows-Local-Jump` shell exists
- [ ] Administrators marked privileged with approval note
- [ ] Provisioning stubs + leaver disable documented
- [ ] Lab-without-live-target path complete

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Provision fails RPC | IQService / firewall | Fix checklist TLS and ports |
| Domain account duplicated | Wrong app boundary | Prefer AD app; remove local duplicate |
| Shared admin correlated to person | Bad correlation | Mark non-human; exclude |
| Password in XML export | Misconfig | Encrypt; scrub binder |
| Template missing | Version/license | Shell + Description; escalate |

---

## Training binder evidence

- Local vs AD memo
- Annotated IQService checklist
- Application screenshot
- Group entitlement risk table
- Break-glass SLA note
- Connection worksheet / proxy Task Result

---

## Knowledge check

1. When do you choose Windows Local - Direct over AD Direct?
2. Name the Meridian Windows Local application.
3. Which local group is privileged in this lab?
4. Why annotate the AD IQService checklist here?
5. What must never appear in git for this connector?

### Answers

1. When governing local SAM accounts (non-domain or explicit break-glass local), not domain identities.  
2. `MNB-Windows-Local-Jump`.  
3. Administrators.  
4. Windows Local remote operations often still depend on IQService TLS and service accounts.  
5. Cleartext local admin / service passwords.

---

## Stretch lab

Draft a population “Local Administrators on jump hosts” for a monthly privileged certification dry-run.

---

## Summary

- Windows Local is a deliberate SAM governance surface, not a substitute for AD.
- Meridian uses `MNB-Windows-Local-Jump` with privileged Administrators controls.
- IQService checklist + worksheet complete the lab without a live host.

---

**Previous:** [Lesson 83 — Linux / Unix Connector](83-linux-unix-connector.md)  
**Next:** [Lesson 85 — Logical Applications](85-logical-applications.md)
