# Lesson 109 — Hardening spadmin & Capabilities

| Field | Value |
| --- | --- |
| **Level** | Advanced |
| **Track** | Enterprise Hardening & Mastery |
| **Time** | 75–90 minutes |
| **Prereq** | [Lesson 108 — Multi-Environment Promotion](108-multi-env-promotion.md); Lesson 96 workgroups |
| **Lab data** | Workgroups/capabilities from Lesson 96; AuditConfig from Lesson 104; API account Lesson 100 |

## Learning objectives

You will be able to:

- Position `spadmin` as **break-glass only** with sealed credentials and dual control
- Complete a Meridian admin RACI replacing daily `spadmin` use
- Remove SystemAdministrator from standing human operators (`helen.ross` pattern)
- Define monitoring for `spadmin` authentications in SIEM
- Run a break-glass drill with ticket, time box, and post-use review

## Why this matters

Shared `spadmin` / `admin` is the fastest way to fail an IAM exam and the easiest insider path to silent capability grants. Hardening admin identities is non-negotiable for Meridian production.

**Control / audit:** Every `spadmin` login should be exceptional, ticketed, and reviewed. Standing admins use named accounts with least privilege.

## Concepts

| Account type | Purpose | Standing use? |
| --- | --- | --- |
| `spadmin` | Break-glass SystemAdministrator | **No** |
| Named IAM engineer | Day-2 with scoped capabilities | Yes |
| `mnb.api.*` | Non-human integrations | Yes (non-interactive) |
| Workgroups `MNB-WG-*` | Team rights | Yes |

```text
  Normal day: helen.ross + MNB-WG-IAM-Ops capabilities
        |
  Emergency: open ticket --> retrieve spadmin from vault (dual control)
        |
        v
  Time-boxed work --> logout --> rotate if policy --> post-incident review
        |
        v
  SIEM alert on spadmin success/fail --> SOC acknowledges
```

**Password lab default `admin` must never ship to shared/prod.** Homelab docs already say change immediately.

## Before you start

- [ ] Lesson 96 matrix available
- [ ] Vault or sealed envelope process for lab (even a password manager note)
- [ ] Audit login events enabled (Lesson 104)
- [ ] Second person available for dual-control simulation (`sofia.torres` or peer)

## Lab procedure

### Task 1 — Admin inventory

1. Search who holds SystemAdministrator (or equivalent).
2. List: `spadmin`, any named humans, any service accounts.
3. Flag every standing human besides break-glass as **finding**.

**Expected result:** Privileged inventory with findings highlighted.

**If it fails:** Debug Capability → members; export XML.

### Task 2 — Day-2 role confirmation

1. Confirm `helen.ross` can perform IAM ops without SystemAdministrator (Lesson 96).
2. If not, grant missing least-privilege caps—still not SystemAdministrator.
3. Repeat spot-check for cert admin path with `marcus.approve` workgroup.

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
4. Generate one lab login event; show it in audit search.

**Expected result:** Detection definition + sample event evidence.

### Task 5 — Break-glass drill

1. Open ticket `LAB-BG-109` stating reason (e.g., “restore AuditConfig”).
2. Dual-control retrieve password.
3. Login `spadmin`; perform **one** approved admin action; logout.
4. Close ticket with start/end timestamps and screenshot of audit event.
5. Hold 10-minute review: was least privilege possible instead?

**Expected result:** Completed drill packet.

### Task 6 — Hardening standard

1. Publish Meridian standard bullets:
   - No shared daily admin
   - MFA for admin if available
   - Session timeout hardened
   - Capability changes require peer review
   - Quarterly privileged access cert on admin accounts
2. Map to Lesson 110 blueprint input.

**Expected result:** One-page hardening standard.

## Acceptance criteria

- [ ] Privileged inventory complete with findings
- [ ] Day-2 ops proven without SystemAdministrator
- [ ] spadmin sealed / rotation dated
- [ ] Detection rule defined + sample event
- [ ] Break-glass drill packet filed
- [ ] Hardening standard written

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| helen.ross blocked on needed task | Missing right | Add specific right—not full admin |
| Everyone still uses spadmin | Culture / convenience | Disable standing knowledge; enforce vault dual control |
| No audit for login | AuditConfig off | Lesson 104 enable |
| Password in chat | Bad habit | Rotate immediately; revoke chat logs if possible |
| API account has SystemAdministrator | Over-provision | Strip to API rights only |

## Training binder evidence

- Privileged inventory  
- Day-2 proof screenshots  
- Seal / rotation record  
- Break-glass ticket + audit event  
- Hardening standard  

## Knowledge check

1. When is `spadmin` allowed?
2. What replaces daily `spadmin` for Meridian IAM?
3. Why dual control on break-glass retrieval?
4. What SIEM event is mandatory around `spadmin`?
5. What question ends every break-glass drill?

### Answers

1. Time-boxed emergency with ticket—not routine ops.  
2. Named users + `MNB-WG-*` least-privilege capabilities.  
3. Prevents unilateral silent privilege; creates witness evidence.  
4. Successful (and failed) authentications as `spadmin`.  
5. “Could least privilege have completed this without break-glass?”

## Stretch lab

Design quarterly certification campaign targeting identities with SystemAdministrator or Debug rights.

## Summary

- `spadmin` is sealed break-glass; day-2 is named least privilege.
- Detect every break-glass auth; drill the process.
- Hardening standards feed the ultimate blueprint (Lesson 110).

## Privileged access lifecycle

1. Joiners to IAM team receive named accounts—never shared `spadmin`.
2. Movers between IAM and helpdesk lose Debug/SystemAdministrator immediately.
3. Leavers: disable named admin same day; rotate break-glass if that person knew the vault procedure.
4. Quarterly: certify who holds admin-class capabilities (stretch campaign).

### Task 7 — Session & MFA controls

1. Document session timeout settings for admin vs normal users if configurable.
2. Require MFA for admin logins when IdP integration exists (Okta/Entra patterns from connector track).
3. Lab without MFA: residual risk `RR-MNB-MFA-ADMIN` for Lesson 110.

**Expected result:** Session/MFA control note + risk ID if gap.

### Emergency contact card

| Role | Persona / mailbox |
| --- | --- |
| IAM lead | helen.ross@meridiannb.com |
| Platform | sofia.torres (lab) |
| Risk | MNB-WG-Risk-Review |
| SOC | (site-specific) |

## Break-glass packet template

```text
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

Print or store completed packets for two years per records schedule (follow bank policy).

### Continuous control monitoring

Weekly: query audit for SystemAdministrator capability assignments. Any new grant outside change tickets is an incident.

---

**Previous:** [Lesson 108 — Multi-Environment Promotion](108-multi-env-promotion.md)  
**Next:** [Lesson 110 — Ultimate Meridian Production Blueprint](110-ultimate-blueprint-capstone.md)
