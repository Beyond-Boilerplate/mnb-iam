# Lesson 109 — Hardening spadmin & Capabilities

**Level:** Advanced  
**Track:** Enterprise Hardening & Mastery  
**Time:** 75–90 min  
**Prereq:** Lesson 108 — Multi-Environment Promotion; Lesson 96 workgroups  

**Lab data:**
- Workgroups/capabilities from Lesson 96
- AuditConfig from Lesson 104
- API account from Lesson 100 (`mnb.api.lab`)

---

## Learning objectives

You will be able to:

- Position `spadmin` as **break-glass only** with sealed credentials and dual control
- Complete a Meridian admin RACI replacing daily `spadmin` use
- Remove SystemAdministrator from standing human operators (`helen.ross` pattern)
- Define monitoring for `spadmin` authentications in SIEM
- Run a break-glass drill with ticket, time box, and post-use review
- Publish a hardening standard that feeds Lesson 110’s production blueprint

---

## Why this matters

**Business.** Shared `spadmin` / `admin` is the fastest way to fail an IAM exam and the easiest insider path to silent capability grants. When every engineer knows the default `admin` password from a training wiki, Meridian’s control plane has no accountability — anyone can grant Wire entitlements or import SoD exceptions at 2 a.m. without a name on the audit trail that means anything.

**Control / audit.** Every `spadmin` login should be exceptional, ticketed, and reviewed. Standing admins use named accounts with least privilege (`MNB-WG-IAM-Ops`). When the OCC asks *"show the last spadmin use and prove day-2 does not require it,"* you produce `LAB-BG-109` packets + Lesson 96 matrix — not “we trust our people.”

---

## Concepts

### Account types

| Account type | Purpose | Standing use? |
| --- | --- | --- |
| `spadmin` | Break-glass SystemAdministrator | **No** |
| Named IAM engineer | Day-2 with scoped capabilities | Yes |
| `mnb.api.*` | Non-human integrations | Yes (non-interactive) |
| Workgroups `MNB-WG-*` | Team rights | Yes |

```
  Normal day: helen.ross + MNB-WG-IAM-Ops capabilities
        │
  Emergency: open ticket --> retrieve spadmin from vault (dual control)
        │
        ▼
  Time-boxed work --> logout --> rotate if policy --> post-incident review
        │
        ▼
  SIEM alert on spadmin success/fail --> SOC acknowledges
```

**Password lab default `admin` must never ship to shared/prod.** Homelab docs already say change immediately.

### Privileged access lifecycle

1. Joiners to IAM team receive named accounts — never shared `spadmin`.
2. Movers between IAM and helpdesk lose Debug/SystemAdministrator immediately.
3. Leavers: disable named admin same day; rotate break-glass if that person knew the vault procedure.
4. Quarterly: certify who holds admin-class capabilities (stretch campaign).

### Real-life Meridian example

An engineer used `spadmin` daily “because helen.ross menus were missing one right.” Instead of adding the specific right, the team normalized break-glass. A capability grant to a contractor went unnoticed for a week because every login looked like routine ops. Hardening flipped the culture: day-2 without SystemAdministrator; SIEM high-severity on every `spadmin` success.

### Wrong way vs Meridian way

| Wrong way | Why it fails | Meridian way |
| --- | --- | --- |
| Shared daily `spadmin` | No accountability | Named least privilege |
| API account with SystemAdministrator | Integration blast radius | Strip to API rights only |
| Password in chat / wiki | Credential sprawl | Vault + dual control + rotate |
| No audit on login | Silent break-glass | AuditConfig + SIEM (Lesson 104) |
| Skip post-use review | Habit forms | “Could least privilege have worked?” |

---

## How it works

| Control | Mechanism | Evidence |
| --- | --- | --- |
| Day-2 ops | Capabilities on `helen.ross` / `MNB-WG-IAM-Ops` | Matrix + login screenshots |
| Break-glass | Vault dual control + ticket | `LAB-BG-109` packet |
| Detect | SIEM / audit on `spadmin` auth | Sample event + rule def |
| Review | Post-use least-privilege question | Packet sign-off |
| Continuous | Weekly audit of SystemAdministrator grants | Assurance extract |

Emergency contact card:

| Role | Persona / mailbox |
| --- | --- |
| IAM lead | helen.ross@meridiannb.com |
| Platform | sofia.torres (lab) |
| Risk | MNB-WG-Risk-Review |
| SOC | (site-specific) |

Break-glass packet template:

```
Ticket: LAB-BG-109 / INC-####
Reason:
Approver / witness:
Start (UTC):
End (UTC):
Actions performed:
Artifacts changed:
Least-privilege alternative considered? Y/N — notes:
Audit event IDs:
Password rotated after? Y/N
```

Retain completed packets per bank records schedule (often multi-year).

---

## Real-world setup (break-glass as a governed exception)

### Step 1 — Inventory privileged holders

1. Who has SystemAdministrator? Flag standing humans as findings.

### Step 2 — Prove day-2 without break-glass

1. `helen.ross` path from Lesson 96; fix missing rights surgically.

### Step 3 — Seal and monitor

1. Vault, dual control, rotation date; SIEM high on success/fail.

### Step 4 — Drill and standardize

1. `LAB-BG-109` end-to-end; publish hardening standard for Lesson 110.
2. MFA for admin when IdP exists; else residual `RR-MNB-MFA-ADMIN`.

---

## Before you start

- [ ] Lesson 96 matrix available
- [ ] Vault or sealed envelope process for lab (even a password manager note)
- [ ] Audit login events enabled (Lesson 104)
- [ ] Second person available for dual-control simulation (`sofia.torres` or peer)
- [ ] Binder: `hardening/spadmin/`

---

## Lab procedure

### Task 1 — Admin inventory

You cannot seal what you have not found.

1. Search who holds SystemAdministrator (or equivalent).
2. List: `spadmin`, any named humans, any service accounts (`mnb.api.lab`).
3. Flag every standing human besides break-glass as **finding**.

**Expected result:** Privileged inventory with findings highlighted.

**If it fails:** Debug Capability → members; export XML.

### Task 2 — Day-2 role confirmation

Break-glass culture dies when day-2 works.

1. Confirm `helen.ross` can perform IAM ops without SystemAdministrator (Lesson 96).
2. If not, grant missing least-privilege caps — still not SystemAdministrator.
3. Repeat spot-check for cert admin path with `marcus.approve` / `MNB-WG-Cert-Approvers`.

**Expected result:** Written proof day-2 works without `spadmin`.

### Task 3 — Seal spadmin

1. Change `spadmin` password from any default; store in vault only.
2. Document dual-control: one person retrieves, second witnesses (lab peer).
3. Remove `spadmin` from browser password save on shared jump hosts.
4. Record password-last-rotated date.

**Expected result:** Seal procedure page with rotation date.

**If it fails:** On immutable shared training pods, document “platform-managed secret” and still forbid daily use.

### Task 4 — SIEM / alert rule

1. Define detection: successful auth as `spadmin`; failed brute attempts.
2. Severity: high; notify SOC + `helen.ross`.
3. If no SIEM, configure IIQ email/report mock or daily audit extract filter.
4. Generate one lab login event; show it in audit search (Lesson 104).

**Expected result:** Detection definition + sample event evidence.

### Task 5 — Break-glass drill

1. Open ticket `LAB-BG-109` stating reason (e.g. “restore AuditConfig” or “Lesson 109 drill”).
2. Dual-control retrieve password.
3. Login `spadmin`; perform **one** approved admin action; logout.
4. Close ticket with start/end timestamps and screenshot of audit event.
5. Hold 10-minute review: was least privilege possible instead?

**Expected result:** Completed drill packet using the template above.

### Task 6 — Hardening standard

1. Publish Meridian standard bullets:
   - No shared daily admin
   - MFA for admin if available
   - Session timeout hardened
   - Capability changes require peer review
   - Quarterly privileged access cert on admin accounts
2. Map to Lesson 110 blueprint input.

**Expected result:** One-page hardening standard.

### Task 7 — Session & MFA controls

1. Document session timeout settings for admin vs normal users if configurable.
2. Require MFA for admin logins when IdP integration exists (Okta/Entra patterns from connector track).
3. Lab without MFA: residual risk `RR-MNB-MFA-ADMIN` for Lesson 110.

**Expected result:** Session/MFA control note + risk ID if gap.

### Task 8 — Continuous control monitoring note

1. Weekly: query audit for SystemAdministrator capability assignments.
2. Any new grant outside change tickets is an incident.
3. Tie to Lesson 104 privileged extract naming (`MNB-Audit-Priv-YYYY-MM-DD`).

**Expected result:** CCM paragraph in binder.

### Task 9 — Examiner question drill

*"Show the last spadmin use and prove day-2 does not require it."*

Write the three-artifact answer: (1) `LAB-BG-109` packet with audit event ids, (2) `helen.ross` day-2 screenshots without SystemAdministrator, (3) SIEM/detection definition for `spadmin` auth + inventory showing no standing human SystemAdministrators (or findings listed).

**Expected result:** Written proof steps in the binder.

---

## Acceptance criteria

- [ ] Privileged inventory complete with findings
- [ ] Day-2 ops proven without SystemAdministrator
- [ ] spadmin sealed / rotation dated
- [ ] Detection rule defined + sample event
- [ ] Break-glass drill packet filed
- [ ] Hardening standard written
- [ ] Session/MFA note (+ `RR-MNB-MFA-ADMIN` if needed)
- [ ] CCM weekly query note
- [ ] Examiner proof steps drafted

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| helen.ross blocked on needed task | Missing right | Add specific right — not full admin |
| Everyone still uses spadmin | Culture / convenience | Disable standing knowledge; enforce vault dual control |
| No audit for login | AuditConfig off | Lesson 104 enable |
| Password in chat | Bad habit | Rotate immediately; revoke chat logs if possible |
| API account has SystemAdministrator | Over-provision | Strip to API rights only |
| SIEM silent | Rule not deployed | Mock extract until SOC onboards |

---

## Training binder evidence

- Privileged inventory
- Day-2 proof screenshots
- Seal / rotation record
- Break-glass ticket + audit event (`LAB-BG-109`)
- Hardening standard
- Session/MFA / CCM notes
- Examiner proof steps

---

## Knowledge check

1. When is `spadmin` allowed?
2. What replaces daily `spadmin` for Meridian IAM?
3. Why dual control on break-glass retrieval?
4. What SIEM event is mandatory around `spadmin`?
5. What question ends every break-glass drill?
6. What residual risk ID covers missing admin MFA in lab?

### Answers

1. Time-boxed emergency with ticket — not routine ops.
2. Named users + `MNB-WG-*` least-privilege capabilities.
3. Prevents unilateral silent privilege; creates witness evidence.
4. Successful (and failed) authentications as `spadmin`.
5. “Could least privilege have completed this without break-glass?”
6. `RR-MNB-MFA-ADMIN`.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “capabilities,” “SystemAdministrator,” and “authentication” for admin rights models.
- [NIST SP 800-53 Rev. 5 — AC-2 / AC-6 / AU-6](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — account management, least privilege, and audit review for privileged use.
- [NIST SP 800-63B — Digital Identity Guidelines](https://pages.nist.gov/800-63-3/sp800-63b.html) — MFA and session management for privileged authenticators.
- [CIS Controls (v8) — Control 5 / 6](https://www.cisecurity.org/controls) — account management and access control management practices (map to break-glass + named admins).
- [FFIEC IT Handbook — Information Security](https://ithandbook.ffiec.gov/) — privileged access and monitoring expectations for banks.
- [OWASP Application Security Verification Standard](https://owasp.org/www-project-application-security-verification-standard/) — authentication and session requirements relevant to admin portals.

---

## Stretch lab

Design a quarterly certification campaign targeting identities with SystemAdministrator or Debug rights. Include `mnb.api.*` service accounts in the population. Draft the campaign owner as `MNB-WG-Risk-Review` with IAM support.

---

## Summary

- `spadmin` is sealed break-glass; day-2 is named least privilege via `MNB-WG-*`.
- Detect every break-glass auth; drill the process; ask the least-privilege question every time.
- Hardening standards and residual MFA risks feed the ultimate blueprint (Lesson 110).

---

**Previous:** [Lesson 108 — Multi-Environment Promotion](108-multi-env-promotion.md)  
**Next:** [Lesson 110 — Ultimate Meridian Production Blueprint](110-ultimate-blueprint-capstone.md)
