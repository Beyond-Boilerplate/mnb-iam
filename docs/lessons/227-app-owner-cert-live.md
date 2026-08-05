# Lesson 227 — App-Owner Certification Live

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~65 minutes  
**Prereq:** Lesson 226  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 44

> **Why (1–2 lines):** App owners certify what managers cannot judge — whether an account still belongs on their system, not whether a person still needs it.

## What this is

Application-owner certification is the second governance lens IIQ ships: manager certs ask "does this person still need access"; owner certs ask "does this account still belong on my system." The pack has `MNB-Cert-App-Owner-Wire` (`certificationType="Application"`, `certifierName="applicationOwner"`) scoped to the Wire Portal app. Certifier resolution reads straight off the `Application` object's `Owner` field — currently `spadmin`. You'll reassign ownership to a real persona so the decision is made by someone who understands the app, then certify and revoke against the live connector.

## Know these

| Cert type | Certifier resolves from | Row = |
| --- | --- | --- |
| Manager (226) | `manager` chain | Identity's access |
| App Owner (227) | `Application.Owner` field | One account on the app |

```text
Application.Owner = spadmin (meaningless) → reassign to marcus.approve
  → generate MNB-Cert-App-Owner-Wire → Mailpit launch mail to owner
  → owner decides per-account → revoke → live target changes
```

**Wrong way:** Leaving `Owner` on `spadmin` and certifying anyway — an admin rubber-stamping their own admin account is not an owner decision.

## Intent

- Reassign an `Application`'s Owner to a real persona instead of `spadmin`.
- Launch an app-owner certification and decide as that owner.
- Revoke a stale entitlement and prove the account changed on the target.
- Compare this cert's row count/shape to Lesson 226's — application-scoped, not identity-scoped.

## Before you start

- [ ] Lesson 226 manager cert completed (comparison baseline)
- [ ] `marcus.approve` exists as an Identity cube
- [ ] Mailpit UI: `http://localhost:8025`
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/227`

## Do this

1. **Applications → Application Definition → MNB-WirePortal** (or `MNB-Salesforce-CRM-Live` if Wire isn't separately onboarded). Set **Owner** to `marcus.approve`. Save.  
   **Why:** `certifierName="applicationOwner"` resolves the certifier straight off this field.  
   **Expect:** Owner saved; not `spadmin`.

2. **Certifications → Schedule/Generate → Application Owner Certification**, definition `MNB-Cert-App-Owner-Wire`, target the re-owned app, **Generate Now**.  
   **Expect:** Generation Task Result success.

3. Mailpit should show a launch email addressed to `marcus.approve@meridiannb.com` — a different audience/template than Lesson 226's manager mail.  
   **Expect:** Launch mail present; note the subject for evidence.

4. Log in as `marcus.approve` / `LabUser1!`. Open **My Certifications**; rows are one per account on the app, not one per identity's whole access. Pick a stale one — e.g. `priya.wire`'s account if she no longer needs initiator rights — and **Revoke**.  
   **Expect:** Revoke recorded on an account-level row.

5. **Complete Certification** (sign-off).  
   **Why:** App-owner certs also honor `processRevokesImmediately`; sign-off is still the audit event.  
   **Expect:** Cert status completed.

6. Confirm the target changed: CRM `curl -s http://localhost:8091/crm/scim/v2/Users | python3 -m json.tool` (check `active:false` or entitlement removed), or JDBC `psql -h localhost -p 5435 -U mnb -d mnb_apps -c "select username, status from mnb_app_accounts;"`.  
   **Expect:** Live account reflects the revoke.

7. Refresh Mailpit for the owner's completion notice; check for a remediation work item if the revoke needed manual fulfillment.  
   **Expect:** Completion mail present; remediation noted if shown.

## If it fails

- **Owner field won't save / not in dropdown** — `marcus.approve` must exist as an Identity cube first; run **Refresh Identity Cubes** or re-check Lesson 202 seed.
- **Cert has zero accounts** — app hasn't been aggregated recently; run **Applications → Aggregate** for the target first.
- **Marcus can't see the cert in My Certifications** — certifier resolution needs the exact `Owner` reference to match his `Identity` name, not display name.
- **Revoke accepted but target unchanged** — check **Provisioning Transactions** for a Failed/Retry row, usually a stale connector credential; re-test connection then retry.

## You are done when

An app-owner cert with a live revoke: owner is a real persona, decision made as that persona, and the target system shows the account disabled or the entitlement removed.

## Control note

- **Control:** Application-owner (account-level) access certification.  
- **Owner:** App owner (`marcus.approve`) + IAM Ops (campaign).  
- **SLA (lab):** Same session decide; production account-level campaigns often quarterly per app.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/227/` — owner reassignment, launch mail, revoked account, target proof.

## Quick check

1. What field drives `certifierName="applicationOwner"` resolution? → The `Application.Owner` attribute.  
2. What's the row unit in an app-owner cert versus a manager cert? → Account-on-app, not identity's whole access.  
3. Why is `spadmin` as Owner meaningless? → No real accountability — an admin certifying their own admin-owned app.

## Navigate

- Previous: Lesson 226  
- Next: Lesson 228  
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
