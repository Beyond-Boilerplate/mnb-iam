# Lesson 229 — Certification Remediation Proof

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~60 minutes  
**Prereq:** Lessons 226–227  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 46

> **Why (1–2 lines):** Revoke without target proof is theater — ops needs the target system row to prove revoke actually hit the target, not only IIQ's word that it happened.

## What this is

A "Revoke" decision in a certification is a promise, not an action — IIQ turns it into a `ProvisioningPlan`, then a `ProvisioningTransaction`, which either auto-provisions (`processRevokesImmediately=true`) or drops a manual **Remediation** work item when it can't. This lesson closes the loop from Lessons 226–227: pick one revoke, trace its full chain — cert decision → transaction → target system row → re-aggregation confirming IIQ agrees with the target — and file the evidence a real auditor asks for.

## Know these

```text
Cert Revoke decision → ProvisioningPlan → ProvisioningTransaction
  → Committed (auto) or Failed/Retry (manual Remediation work item)
  → re-aggregate target → cube's Entitlements tab confirms no drift
```

**Wrong way:** Trusting "Committed" status on the transaction alone — always verify against the actual target query, since cache/aggregation lag can make IIQ believe something the target hasn't caught up to yet.

## Intent

- Pick one revoke from Lesson 226 or 227 and pull its Provisioning Transaction record.
- Verify the underlying account on OpenLDAP, JDBC, or CRM actually lost the entitlement.
- If auto-provisioning failed, work the manual Remediation work item to completion.
- Re-aggregate the target and confirm IIQ's cube matches reality — no drift.

## Before you start

- [ ] At least one Revoke decision completed in Lesson 226 or 227
- [ ] Target app credentials/access for direct query (`ldapsearch`, `psql`, or `curl`)
- [ ] Mailpit UI: `http://localhost:8025`
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/229`

## Do this

1. Open **Setup → Provisioning Transactions**, filter by the identity revoked in Lesson 226 or 227. Copy the transaction id, target application, and status (Committed/Failed/Retry).  
   **Expect:** One clearly identifiable transaction row.

2. Verify on the actual target:
   - OpenLDAP: `ldapsearch -x -H ldap://localhost:389 -b ou=people,dc=meridiannb,dc=com -D 'cn=admin,dc=meridiannb,dc=com' -w admin '(uid=<user>)' memberOf`
   - JDBC Core Banking: `psql -h localhost -p 5435 -U mnb -d mnb_apps -c "select username, status, entitlement from mnb_app_accounts where username='<user>';"`
   - CRM SCIM mock: `curl -s http://localhost:8091/crm/scim/v2/Users | python3 -m json.tool`  
   **Expect:** Revoked group/entitlement absent or account disabled.

3. If the transaction is **Failed** or **Retry**, this is the manual-remediation path: open **Work Items → My Work Items** as the app owner (`spadmin` or `marcus.approve`), find the Certification Remediation item, complete the manual step yourself (run the LDIF/SQL), then mark it **Complete**.  
   **Why:** The lesson isn't done until target agrees with IIQ — automated or manual.  
   **Expect:** Work item closed, target actually changed.

4. Run **Applications → Aggregate** for the affected app, then open the identity cube's **Entitlements** tab.  
   **Why:** This catches "IIQ thinks it revoked it but the target still has it" drift.  
   **Expect:** Entitlement gone from the cube after re-aggregation.

5. Open **Monitor → Tasks → Task Results**, locate the aggregation task result; note finish time and row/change counts.  
   **Expect:** Task result confirms the aggregation actually ran and changed something.

6. Return to Mailpit and find the full thread for this identity — launch, decision, remediation (if any), completion.  
   **Expect:** Subjects/timestamps tell a consistent story.

7. Save the transaction id, target query output, Task Result, and Mailpit thread together under `~/iiq-lab-evidence/sandbox/229/`.  
   **Expect:** One matched evidence set.

## If it fails

- **Transaction shows Committed but target unchanged** — connector cache or aggregation lag; force a fresh aggregate before concluding drift.
- **Remediation work item never appeared** — check the certification definition has a remediation flow configured (remediator = app owner) and the app's `featuresString` includes `PROVISIONING`.
- **Re-aggregation still shows the old entitlement** — connector may read from a cache/replica; for the JDBC mock confirm you're querying the same `mnb_apps` DB the connector uses, not a stale local copy.

## You are done when

One revoke is verified end-to-end on a live target, with Task Result and Mailpit thread saved as matched evidence.

## Control note

- **Control:** Certification remediation closure and drift detection.  
- **Owner:** App owner (manual remediation) + IAM Ops (drift monitoring).  
- **SLA (lab):** Same session; production remediation SLAs are often 5–10 business days.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/229/` — transaction id, target query output, Task Result, Mailpit thread.

## Quick check

1. What turns a cert Revoke into an actual action? → A `ProvisioningPlan` → `ProvisioningTransaction`.  
2. What catches "IIQ thinks it revoked it, target didn't" drift? → Re-aggregation plus a direct target query.  
3. What closes a Failed/Retry transaction? → A manual Remediation work item, completed and marked done.

## Navigate

- Previous: Lesson 228  
- Next: Lesson 230  
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
