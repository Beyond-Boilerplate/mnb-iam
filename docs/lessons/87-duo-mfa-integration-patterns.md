# Lesson 87 — Duo MFA Integration Patterns

**Level:** Intermediate  
**Track:** Connectors — Infra, Logical, PAM  
**Time:** 60–75 min  
**Prereq:** Lesson 86 — PAM / CyberArk Module  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv`
- Repo: `lab-data/connectors/README.md`
- Runtime notes: `~/iiq-lab-data/connectors/`

---

## Learning objectives

You will be able to:

- Separate **MFA enrollment governance** from primary account connectors (AD/Entra)
- Document Meridian Duo patterns: who must enroll, privileged step-up, and leaver offboarding
- Create design objects `MNB-MFA-Duo-Notes` (Application or custom config worksheet) without inventing unsupported connector claims
- Map MFA requirements onto privileged roles and Wire Portal access
- Produce examiner answers for “how is MFA enforced for payments and admins?”

---

## Why this matters

**Business.** Phishing-resistant MFA reduces account-takeover risk on VPN, email, and payment tools. Meridian requires stronger step-up for privileged and payment dual-control users.

**Control / audit.** Auditors ask for MFA coverage reports and offboarding of authenticators—not a screenshot of a Duo admin console alone. IIQ’s job is governance alignment: populations, roles, certifications, and evidence—even when Duo is administered outside IIQ.

---

## Concepts

IdentityIQ may integrate MFA via SSO/IdP, plugins, or adjacent connectors depending on version/packaging. **Do not claim a native Duo connector exists** unless your build’s ConnectorRegistry shows one.

Meridian pattern (governance-first):

```
Authoritative HR / AD account
        │
        ▼
 Population: MFA-required (employees, privileged, payments)
        │
        ├── Duo enrollment (IdP / Duo Admin — system of record for factors)
        ├── IIQ: track requirement flags / entitlements / exceptions
        └── Leaver: disable AD + remove Duo user (PAM/IdP runbook)
```

| Pattern | Use at Meridian |
| --- | --- |
| Workforce MFA | All employees + contractors with network access |
| Privileged step-up | CloudAdmin, BreakGlass, RACF SPECIAL, local Administrators |
| Payments step-up | `WIRE_INIT` / `WIRE_APPR` holders |
| Exception | Temporary break-glass with Security approval + expiry |

**Lab-without-live-target:** Design worksheet, populations, role annotations, and optional placeholder Application for tracking—no live Duo Admin API required.

---

## Before you start

- [ ] IIQ up
- [ ] Know personas: `priya.wire`, `marcus.approve`, `kai.nguyen`, `raj.external`
- [ ] Privileged and Wire Portal lessons available for reference
- [ ] Binder: `connectors/duo-mfa/`

---

## Lab procedure

### Task 1 — ConnectorRegistry honesty check

1. Debug → ConnectorRegistry (or Applications → New → browse types).
2. Search for Duo / MFA / similar.
3. Record finding: **Present** or **Not present**.
4. Write Meridian decision: If absent, govern via populations + IdP/Duo runbooks; if present, note connector name for future build.

**Expected result:** Written Registry finding—no invented UI labels.

**If it fails:** Assume Not present; continue governance design.

---

### Task 2 — Create governance worksheet `MNB-MFA-Duo-Notes`

1. Create markdown/PDF in binder (and optional empty Application Description dump) titled `MNB-MFA-Duo-Notes`.
2. Include sections: In-scope systems (VPN, O365, Wire Portal SSO, IIQ UI), Factor policy, Privileged step-up, Exceptions, Leaver.
3. Corporate emails: `@meridiannb.com`.
4. Control owners: Security (A), IAM (R for IIQ populations), Helpdesk (C for enrollment).

**Expected result:** Completed notes document in `~/iiq-lab-data/connectors/` or binder folder.

**If it fails:** Minimum one-pager with owners and in-scope systems.

---

### Task 3 — Populations for MFA coverage

1. Design population **MNB-Pop-MFA-Required**: active employees + contractors (`raj.external` if active).
2. Design population **MNB-Pop-MFA-Privileged**: union of privileged role holders + local/RACF privileged entitlements (conceptual).
3. Design population **MNB-Pop-MFA-Payments**: identities with `WIRE_INIT` or `WIRE_APPR`.
4. In IIQ, create at least one population if UI available; otherwise keep selector XML/notes.

**Expected result:** Three population definitions; at least one created in IIQ or fully specified in binder.

**If it fails:** Binder selectors with filter logic in plain English.

---

### Task 4 — Role and entitlement annotations

1. Annotate privileged roles: “MFA step-up required before checkout / use.”
2. Annotate Wire Portal entitlements: “SSO + Duo required; IIQ grant is necessary but not sufficient.”
3. For `raj.external`: contractor MFA mandatory; sponsor `helen.ross` accountable for exceptions.
4. Capture screenshots of role/entitlement descriptions updated (or binder redlines).

**Expected result:** Updated descriptions or redline table.

---

### Task 5 — Leaver / exception runbook

1. Write steps: HR terminate → AD disable → Duo account disable/delete → confirm no active factors.
2. Exception path: Security approves MFA bypass ≤ 24h; log ticket; auto-expire.
3. Evidence: ticket IDs + Duo admin export + IIQ IdentityRequest.

**Expected result:** One-page runbook.

---

### Task 6 — Examiner Q&A

Answer:

1. How do you prove payment approvers use MFA?
2. Where is the system of record for authenticators?
3. What does IIQ store vs Duo?

**Expected result:** Written answers referencing populations and runbook.

---

## Acceptance criteria

- [ ] ConnectorRegistry finding recorded honestly
- [ ] `MNB-MFA-Duo-Notes` worksheet complete
- [ ] Three MFA populations defined
- [ ] Privileged + payments annotations done
- [ ] Leaver/exception runbook written
- [ ] Examiner Q&A complete

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Team expects Duo connector | Assumption | Use Registry finding; governance pattern |
| Contractors missing MFA | Population gap | Include contractor employeeType |
| Privileged without step-up | Role doc gap | Annotate + PAM integration |
| Orphan Duo users | Leaver gap | Add Duo step to leaver runbook |
| Exception forever | No expiry | 24h max + Security ownership |

---

## Training binder evidence

- Registry finding screenshot/notes
- `MNB-MFA-Duo-Notes` document
- Population definitions
- Role/entitlement annotation evidence
- Leaver/exception runbook
- Examiner answers

---

## Knowledge check

1. Should you invent a Duo connector if Registry lacks one?
2. Name the Meridian MFA notes artifact.
3. Which personas illustrate payments MFA scope?
4. Who is Accountable for MFA policy in the notes?
5. What is the maximum MFA bypass exception in this lab?

### Answers

1. No—record absence and use governance/IdP patterns.  
2. `MNB-MFA-Duo-Notes`.  
3. `priya.wire` and `marcus.approve`.  
4. Security.  
5. ≤ 24 hours with Security approval.

---

## Stretch lab

Draft a weekly MFA coverage report definition: identities in `MNB-Pop-MFA-Required` lacking a “MFA enrolled” identity attribute (attribute may be future IdentityAttribute rule).

---

## Summary

- Duo is adjacent MFA governance: populations, annotations, and runbooks first.
- Meridian does not invent connectors; Registry findings drive integration claims.
- Payments and privileged access carry explicit MFA requirements.

---

**Previous:** [Lesson 86 — PAM / CyberArk Module](86-pam-cyberark-module.md)  
**Next:** [Lesson 88 — Connector Gateway / Cloud Patterns](88-connector-gateway-cloud-patterns.md)
