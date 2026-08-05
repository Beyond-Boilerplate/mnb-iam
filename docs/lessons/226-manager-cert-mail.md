# Lesson 226 — Manager Cert + Email

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~80 minutes  
**Prereq:** Lessons 203, 214  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 43

> **Why (1–2 lines):** Certs are real when certifiers get mail and decide in-product — rubber-stamp Approve-All is an examiner red flag. Revoke must reach a live target, not only the IIQ database.

## What this is

Manager Access Review is an `Identity`-type certification: one cert per manager, rows = direct reports’ entitlements/roles. Pack ships `MNB-Cert-Manager-Access-Review` (`config/CertificationDefinition/MNB-CertificationDefinition-Manager.xml`, `certifierName="manager"`, `processRevokesImmediately=true`). Classic 43 taught decision quality and scope discipline on static data; here every **Revoke** can fire a Provisioning Transaction against Samba/OpenLDAP/JDBC/CRM, and stage changes SMTP to Mailpit (`mailpit:1025`, UI `http://localhost:8025`).

## Know these

| Decision | When to use |
| --- | --- |
| Approve | Access still required and appropriate |
| Revoke | Access no longer needed — expect live provision |
| Delegate | Someone else must decide (use sparingly in lab) |
| Exception / forward | Edge cases — document why |

```text
Generate cert → launch mail (Mailpit)
  → certifier decides (Approve + Revoke)
  → sign-off → completion mail
  → revoke → Provisioning Transaction on live app
```

**Sizing:** Prefer a scoped org (Helen’s reports) you can finish in ~30–45 minutes. Birthright-only noise trains Approve-All pathology — include at least one high-risk Wire/CRM row to revoke.

**Wrong way:** Completing as `spadmin` instead of the manager — no certifier accountability trail.

## Intent

- Launch manager cert for Helen’s org; see launch mail in Mailpit.
- Decide as `helen.ross` (approve one, revoke one meaningful entitlement).
- Prove revoke on a live target via Provisioning Transaction.
- Sign off; confirm completion (and optional remediation) mail.
- Save ids for Lesson 229 remediation tracing.

## Before you start

- [ ] Mailpit works (Lesson 203): `http://localhost:8025`
- [ ] Manager correlation: Helen has reports (Lesson 214)
- [ ] Pass-through / lab password for Helen: `LabUser1!` (or your seed)
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/226`

## Do this

1. Confirm org: IIQ identity search `manager: helen.ross` — Christopher Hayes and others.  
   **Expect:** Non-empty report list; empty org = zero-row cert.

2. **Certifications → Schedule/Generate → Manager Access Review.** Definition `MNB-Cert-Manager-Access-Review`, scope Helen’s subordinates, name `MNB-Mgr-<today>`, **Generate Now**.  
   **Why:** `processRevokesImmediately=true` provisions on save so you verify targets same session.  
   **Expect:** Generation Task Result success.

3. Mailpit search `helen.ross` — launch/assignment message.  
   **Expect:** Certification generated / assignment mail visible.

4. Log out `spadmin`; log in `helen.ross` / `LabUser1!` → **My Certifications**. **Approve** one correct birthright-style entitlement; **Revoke** one Wire or CRM entitlement on a report (e.g. Christopher Hayes) you can re-check on a live app.  
   **Expect:** Two different decision types recorded — not Approve-All.

5. **Complete Certification** (sign-off).  
   **Why:** Sign-off is the audit-relevant event; undecided certs don’t complete the mail/provision story.  
   **Expect:** Cert status completed / signed off.

6. As `spadmin`, **Provisioning Transactions** filtered to the revoked identity.  
   **Expect:** Committed/Success against live app (e.g. `MNB-Salesforce-CRM-Live` or `MNB-WirePortal`).

7. Refresh Mailpit — completion/sign-off mail; optional Certification Remediation WI mail if revoke needs manual follow-up.  
   **Expect:** Completion mail present; note remediation if shown.

8. Save launch mail id, Provisioning Transaction id, completed-cert screenshot under `~/iiq-lab-evidence/sandbox/226/`.  
   **Expect:** Ids ready for Lesson 229.

## If it fails

- **No Mailpit mail** — Notification SMTP host `mailpit` port `1025`; re-launch; refresh Mailpit.
- **Zero identities** — manager attribute missing; Refresh Identity Cubes for Helen’s org; regenerate.
- **Revoke doesn’t provision** — `processRevokesImmediately` false in your copy, or connector down; check Failed PT rows.
- **Helen can’t see cert** — she must be certifier via `manager` chain (`certifierName="manager"`), not only a random capability.

## You are done when

Manager cert decided with mail trail: launch mail, one live revoke with Committed transaction, completion mail in Mailpit.

## Control note

- **Control:** Manager access certification + notification.  
- **Owner:** Manager (certifier) + IAM Ops (campaign).  
- **SLA (lab):** Same session decide; production campaigns often 14–30 day windows with reminders.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/226/` — mails, PT id, sign-off proof.

## Quick check

1. Why not certify as spadmin? → No manager accountability.  
2. What flag provisions revokes immediately? → `processRevokesImmediately=true`.  
3. Name one rubber-stamp signal. → Approve-All with no revokes on a mixed-risk population.

## Navigate

- Previous: Lesson 225  
- Next: Lesson 227  
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
