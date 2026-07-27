# Lesson 87 — Duo MFA Integration Patterns

**Level:** Intermediate  
**Track:** Connectors — Infra, Logical, PAM  
**Time:** 90–120 min  
**Prereq:** Lesson 86 — PAM / CyberArk Module; Lesson 34 — Rapid Offboarding strongly recommended  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv`
- Repo: `lab-data/connectors/README.md`
- Runtime: `~/iiq-lab-data/connectors/duo-mfa/`

---

## Learning objectives

You will be able to:

- Separate **MFA as a control layer** from primary account connectors (AD, Entra, Google, Wire Portal) — IdentityIQ does not replace Duo
- Document Meridian Duo patterns: enrollment groups, protected applications, privileged/payments step-up, and emergency bypass
- Create governance artifacts (`MNB-Duo` notes / optional Application) without inventing unsupported connector claims
- Map MFA requirements onto privileged roles, Wire Portal dual control, and contractor access
- Produce examiner answers for MFA enforcement and prove that rapid offboarding **revokes MFA bypass tokens** (Lesson 34)

---

## Why this matters

**Business.** Phishing-resistant MFA reduces account-takeover risk on VPN, email, cloud consoles, and payment tools. Meridian requires stronger step-up for privileged users and for payment dual-control holders (`priya.wire`, `marcus.approve`). When `raj.external` (contractor) retained network access after a project ended, the AD disable happened — but a leftover **MFA bypass** token still let a stolen password through for hours. That gap is how “we disabled the account” fails a real incident.

**Control / audit.** Auditors ask for MFA coverage, who can bypass, and how authenticators and bypass exceptions die on termination — not a lone screenshot of the Duo admin console. IIQ’s job is **governance alignment**: populations, role annotations, certifications, leaver evidence, and exception expiry — even when Duo remains the system of record for factors. IdentityIQ does **not** replace Duo; it must not pretend to.

---

## Concepts

### MFA is a control layer, not an account source

Primary identity and access still live in HR → AD/Entra → applications. Duo sits beside that stack as the **second factor and policy engine** for protected apps. Confusing the layers produces bad designs: teams invent a “Duo connector” as the joiner source, or they assume granting `WIRE_APPR` in IIQ somehow enrolls MFA.

| Layer | System of record | What IIQ governs |
| --- | --- | --- |
| Workforce identity | HR / AD | Cubes, correlation, leavers |
| Application access | App connectors / groups | Entitlements, roles, SoD |
| MFA factors & policies | **Duo Admin** | Requirement flags, populations, exceptions, evidence links |
| Emergency bypass | Duo bypass codes / trusted endpoints (as configured) | Approval, expiry, **revoke on term** |

### Patterns Meridian uses

```
Authoritative HR / AD account
        │
        ▼
 Populations: MFA-required / privileged / payments
        │
        ├── Duo enrollment (groups / directories — Duo or IdP-driven)
        ├── Protect applications (VPN, O365, Wire Portal SSO, IIQ UI, cloud consoles)
        ├── Privileged step-up (CloudAdmin, BreakGlass, local/RACF privileged)
        └── Leaver: disable AD + remove Duo user + revoke bypass  ← Lesson 34
```

| Pattern | Use at Meridian | Example personas |
| --- | --- | --- |
| Workforce MFA | All employees + contractors with network access | `sofia.torres`, `raj.external` |
| Enrollment groups | Drive who must enroll / which policy applies | Group-driven Duo or IdP group sync |
| Protect applications | SSO/VPN/app integrations require Duo | Wire Portal SSO, VPN, M365 |
| Privileged step-up | Extra policy for admin and vault use | `kai.nguyen`, `jordan.reed` |
| Payments step-up | Dual-control holders | `priya.wire`, `marcus.approve` |
| Emergency bypass | Temporary, Security-approved, short TTL | Lost phone during wire window |

### Bypass is privilege — treat it like BreakGlass

An MFA bypass token or temporary bypass exception is **privileged access to skip a control**. It needs: Security approval, ≤ **24 hours** in this lab’s policy, ticket evidence, and **mandatory revoke in rapid offboarding**. Lesson 34’s drill is incomplete if it only disables AD and removes app entitlements while bypass remains valid.

### Honesty about connectors

IdentityIQ may integrate MFA via SSO/IdP, plugins, or adjacent connectors depending on version and packaging. **Do not claim a native Duo connector exists** unless your build’s ConnectorRegistry (or New Application type list) shows one. Meridian’s default teaching pattern is **governance-first**: populations + annotations + runbooks + optional `MNB-Duo` tracking application/worksheet.

---

## How it works

```
┌──────────────┐     SSO / RADIUS / Agent      ┌─────────────┐
│ User + AD    │──────────────────────────────►│ Duo         │
│ password     │                               │ (factors +  │
└──────────────┘                               │  policies)  │
                                               └──────┬──────┘
                                                      │
IdentityIQ                                          Protect
  ├── Populations / roles annotate "MFA required"   applications
  ├── Exceptions tracked with expiry                  (VPN, Wire,
  ├── Leaver workflow includes Duo + bypass revoke     O365, IIQ…)
  └── Evidence: IdentityRequest, tickets, Duo export
```

| Concern | Duo Admin | IdentityIQ |
| --- | --- | --- |
| Enrolled devices / factors | Yes (SoR) | Optional attribute/flag if integrated |
| Policy: who needs MFA | Groups / directories / apps | Populations + role text |
| Protect application config | Duo integrations | Notes which apps are in scope |
| Bypass issue / revoke | Duo | Approval + leaver step + ticket |
| Coverage report for examiners | User export | Population membership + exceptions list |

---

## Real-world setup (outside IIQ)

Even when the lab stays offline, production engineers must know this sequence:

### Step 1 — Duo tenant and integrations

1. Security owns the Duo tenant for `meridiannb.com`.
2. Protect applications: VPN, Microsoft 365 / Okta SSO apps, Wire Portal SSO, IdentityIQ UI (if exposed), cloud consoles as applicable.
3. Prefer phishing-resistant factors where policy requires (align NIST 800-63B authenticator guidance for high-risk apps).

### Step 2 — Enrollment groups

1. Define groups (AD or IdP) that drive Duo enrollment / policy — e.g. all workforce, privileged, payments.
2. Map those groups to Duo groups or IdP→Duo sync — exact admin UI paths vary; document the *decision*, not invented clicks.
3. Contractors (`raj.external`) included whenever they have network or payments-adjacent access.

### Step 3 — Emergency bypass procedure

1. Only Security (`amelia.brooks` or on-call delegate) may approve bypass.
2. Max duration **24 hours**; ticket required; list of active bypasses reviewable weekly.
3. Leaver and emergency revoke procedures must clear bypass codes — same urgency as privileged vault remove.

### Step 4 — IIQ alignment

1. Populations for coverage (Task 3).
2. Role/entitlement annotations (Task 4).
3. Lesson 34 runbook updated with Duo user disable/delete **and** bypass revoke (Task 5).

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq`
- [ ] Personas known: `priya.wire`, `marcus.approve`, `kai.nguyen`, `raj.external`, `amelia.brooks`
- [ ] Privileged (28/37), Wire Portal, and Lesson 34 concepts available for reference
- [ ] Binder: `~/iiq-lab-data/connectors/duo-mfa/`
- [ ] No Duo Admin API secrets in the lab repo

---

## Lab procedure

### Task 1 — ConnectorRegistry honesty check

Before designing fantasy integrations, record what your build actually has.

1. Debug → ConnectorRegistry (or Applications → New → browse types) — or equivalent menu path.
2. Search for Duo / MFA / similar.
3. Record finding: **Present** (note exact type name) or **Not present**.
4. Write Meridian decision: If absent, govern via populations + IdP/Duo runbooks and `MNB-Duo` notes; if present, note the connector for a future build — still complete governance tasks below.

**Expected result:** Written Registry finding — no invented UI labels or connector claims.

**If it fails:** Assume **Not present**; continue with governance design.

### Task 2 — Create `MNB-Duo` governance notes (and optional app)

1. Create `~/iiq-lab-data/connectors/duo-mfa/MNB-Duo-Notes.md` (filename may also appear as `MNB-MFA-Duo-Notes` in older binders — use **`MNB-Duo-Notes.md`** going forward; optional Application Description can say `MNB-Duo`).
2. Required sections:
   - In-scope protected applications (VPN, O365, Wire Portal SSO, IIQ UI, cloud consoles)
   - Enrollment group strategy (workforce / privileged / payments)
   - Factor policy summary (phishing-resistant where required for payments/privileged)
   - Privileged step-up
   - Emergency bypass (≤24h, Security accountable)
   - Leaver + bypass revoke (Lesson 34 link)
3. Control owners: Security **(A)**, IAM **(R)** for IIQ populations, Helpdesk **(C)** for enrollment support.
4. Optional: empty Application named `MNB-Duo` used only as a documentation anchor — **not** authoritative, **not** a fake connector claim.

**Expected result:** Completed notes document in the runtime folder; owners recorded.

**If it fails:** Minimum one-pager with owners, in-scope systems, and bypass TTL.

### Task 3 — Populations for MFA coverage

Populations turn “everyone should have MFA” into something you can certify and report.

1. Design **`MNB-Pop-MFA-Required`**: active employees + contractors with network access (`raj.external` if active).
2. Design **`MNB-Pop-MFA-Privileged`**: union of privileged role holders + local/RACF/PAM privileged entitlements (conceptual — CloudAdmin, BreakGlass, etc.).
3. Design **`MNB-Pop-MFA-Payments`**: identities with `WIRE_INIT` or `WIRE_APPR` (Priya / Marcus story).
4. In IIQ, create at least one population if the UI allows; otherwise write selector logic in plain English in the binder.

**Expected result:** Three population definitions; at least one created in IIQ or fully specified offline.

**If it fails:** Binder selectors with filter logic in plain English still pass the task.

### Task 4 — Role and entitlement annotations

IIQ grants are necessary but not sufficient when MFA protects the app.

1. Annotate privileged roles: “MFA step-up required before interactive admin use / vault checkout.”
2. Annotate Wire Portal entitlements: “SSO + Duo required; IIQ grant is necessary but not sufficient.”
3. For `raj.external`: contractor MFA mandatory; sponsor (`helen.ross` if used) accountable for exceptions.
4. Capture screenshots of updated descriptions **or** a redline table in the binder.

**Expected result:** Updated descriptions or redline table linking MFA to privileged and payments access.

### Task 5 — Rapid offboarding runbook (Duo + bypass)

This task explicitly extends Lesson 34.

1. Write the ordered steps for a termination:
   1. HR terminate event received.
   2. Disable AD / primary directory account.
   3. Revoke sensitive app entitlements (wires, cloud, etc.).
   4. **Disable/delete Duo user** (factors cannot authenticate).
   5. **Revoke any active MFA bypass tokens / exceptions** — do not skip.
   6. Confirm: no active factors; no active bypass; next-day coverage export shows absence.
2. Exception path (separate from leaver): Security approves MFA bypass ≤ **24h**; ticket; auto-expire; weekly open-bypass review.
3. Evidence list: ticket IDs, Duo admin export (user + bypass), IIQ IdentityRequest / workflow log, Lesson 34 drill checklist initialed.

**Expected result:** One-page runbook with bypass revoke called out in bold in your binder notes (or highlighted).

**If it fails:** At minimum, a checkbox line “Duo user + bypass cleared” added to the existing Lesson 34 card.

### Task 6 — Group-driven enrollment worksheet

1. Draft a table mapping AD/IdP groups → Duo policy purpose:

| Group (illustrative) | Purpose | Population tie-in |
| --- | --- | --- |
| `MNB-Duo-Workforce` | Baseline enrollment | `MNB-Pop-MFA-Required` |
| `MNB-Duo-Privileged` | Stricter policy / step-up | `MNB-Pop-MFA-Privileged` |
| `MNB-Duo-Payments` | Payments step-up | `MNB-Pop-MFA-Payments` |

2. Note: exact Duo Admin labels vary — document intent; do not invent product UI clicks you have not verified.
3. Record residual risk if group sync lags AD: user has IIQ entitlement before Duo policy applies — mitigate with IdP enforcement order notes.

**Expected result:** Enrollment group worksheet filed.

### Task 7 — Examiner Q&A

Answer in writing:

1. How do you prove payment approvers use MFA?
2. Where is the system of record for authenticators (factors)?
3. What does IIQ store vs Duo?
4. How do you prove a terminated user’s MFA bypass cannot still work?

**Expected result:** Written answers referencing populations, Duo SoR, and the Lesson 34 revoke step.

### Task 8 — Residual risk

Record `RR-DUO-01`: *IIQ populations prove who **should** have MFA; they do not by themselves prove current factor enrollment unless an attribute/export feed exists.* Compensating control: weekly Duo enrollment export joined to `MNB-Pop-MFA-Required`. Owner: Security (`amelia.brooks`); IAM supports the join.

**Expected result:** Residual risk logged with compensating control.

---

## Acceptance criteria

- [ ] ConnectorRegistry finding recorded honestly
- [ ] `MNB-Duo-Notes.md` (optional `MNB-Duo` app anchor) complete with owners and bypass policy
- [ ] Three MFA populations defined
- [ ] Privileged + payments annotations done
- [ ] Leaver runbook includes Duo disable **and** bypass revoke (Lesson 34)
- [ ] Enrollment group worksheet, examiner Q&A, and `RR-DUO-01` complete

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Team expects a Duo connector | Assumption | Use Registry finding; stick to governance pattern |
| Contractors missing MFA | Population / group gap | Include contractor worker type in `MNB-Pop-MFA-Required` |
| Privileged without step-up | Role doc / Duo policy gap | Annotate roles; map `MNB-Duo-Privileged` |
| Orphan Duo users after term | Leaver gap | Add Duo delete/disable to Lesson 34 runbook |
| Bypass still valid after term | Bypass revoke skipped | Treat bypass as privileged; revoke in same SLA window |
| Exception forever | No expiry | 24h max + Security ownership + weekly review |

---

## Training binder evidence

- Registry finding notes/screenshot
- `MNB-Duo-Notes.md` (+ optional Application screenshot)
- Population definitions
- Role/entitlement annotation evidence
- Leaver/exception runbook with bypass revoke
- Enrollment group worksheet
- Examiner answers + `RR-DUO-01`

---

## Knowledge check

1. Does IdentityIQ replace Duo as the MFA control plane? What is IIQ’s role?
2. Should you invent a Duo connector if Registry lacks one?
3. Name the Meridian MFA notes artifact / optional app anchor.
4. Which personas illustrate payments MFA scope?
5. What is the maximum MFA bypass duration in this lab, and who is Accountable?
6. Which Lesson 34 step is most often forgotten for MFA, and why does it matter?

### Answers

1. No — Duo remains SoR for factors/policies; IIQ aligns populations, roles, exceptions, and leaver evidence.
2. No — record absence and use governance/IdP patterns.
3. `MNB-Duo-Notes.md` / optional Application `MNB-Duo`.
4. `priya.wire` and `marcus.approve`.
5. ≤ 24 hours; Security is Accountable.
6. Revoking MFA bypass tokens/exceptions — AD disable alone can leave a bypass path for account takeover.

---

## Further reading

- [Duo Admin documentation](https://duo.com/docs/adminapi) — start from Duo’s docs; also browse Admin documentation for users, groups, applications, and bypass procedures (use Duo’s doc search for “bypass” and “protect an application”).
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search MFA, SSO, and your IdP connector guides; do not assume a Duo-specific connector without Registry confirmation.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — real-world threads on MFA governance adjacent to IIQ.
- [NIST SP 800-63B — Digital Identity Guidelines](https://pages.nist.gov/800-63-3/sp800-63b.html) — authenticator types, AAL, and session considerations that justify phishing-resistant step-up for payments and privileged access.
- [FFIEC guidance](https://www.ffiec.gov/) — search IT Handbook / authentication topics for examiner language on multi-factor authentication at financial institutions.

---

## Stretch lab

Draft a weekly MFA coverage report definition: identities in `MNB-Pop-MFA-Required` lacking an “MFA enrolled” identity attribute (attribute may be a future IdentityAttribute rule or import from Duo export). Add a second column for open bypass exceptions older than 24 hours — those are Sev2 findings for Security.

---

## Summary

- Duo is Meridian’s MFA control layer; IIQ does not replace it — populations, annotations, and runbooks align governance to Duo.
- Enrollment groups, protected apps, privileged/payments step-up, and short-lived bypass form the pattern set.
- Rapid offboarding (Lesson 34) is incomplete until Duo users **and** bypass tokens are revoked.

---

**Previous:** [Lesson 86 — PAM / CyberArk Module](86-pam-cyberark-module.md)  
**Next:** [Lesson 88 — Connector Gateway / Cloud Patterns](88-connector-gateway-cloud-patterns.md)
