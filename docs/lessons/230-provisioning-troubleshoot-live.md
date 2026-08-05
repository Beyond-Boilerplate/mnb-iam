# Lesson 230 — Troubleshoot a Failed Provision

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~70 minutes  
**Prereq:** Lesson 222  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 47

> **Why (1–2 lines):** Most real IIQ incidents aren't "the product is broken" — they're a bad DN, an expired credential, or a plan referencing an attribute the target doesn't have.

## What this is

This lesson deliberately breaks three provisioning paths one at a time — LDAP bind, JDBC credentials, and a malformed plan — reads IIQ's actual error surfaces (`ProvisioningTransaction`, Task Result stack trace, connector Test Connection), fixes each, and re-runs to success. You leave with muscle memory for "where do I look first" instead of guessing.

## Know these

| Break | Error shape | Where it surfaces |
| --- | --- | --- |
| Bad LDAP bind | `INVALID_CREDENTIALS` / bind failure | Provisioning Transaction detail |
| Bad JDBC credential | `SQLException` / auth-denied | Task Result stack trace |
| Malformed plan (bad attribute) | Schema/attribute-not-found | Task Result stack trace, different text than auth failures |

**Wrong way:** Assuming Test Connection passing means provisioning will succeed — connection pooling/caching can mask a credential fix until the pool recycles.

## Intent

- Break OpenLDAP provisioning with a bad bind password; read the resulting error.
- Break JDBC Core Banking by rotating its credential without updating the target; read that error too.
- Fix both, retry the same transaction, get a clean Committed result.
- Break a plan with a bogus attribute name; confirm the error shape differs from a connection failure.

## Before you start

- [ ] `MNB-OpenLDAP` and `MNB-Application-CoreBanking` reachable and currently green
- [ ] `docs/lab-data/enterprise/PASS-THROUGH-AUTH.md` seed passwords on hand
- [ ] A pending or repeatable provisioning action available (e.g. Lesson 222's approval flow)
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/230`

## Do this

1. **Break #1 — bad LDAP bind.** **Applications → Application Definition → MNB-OpenLDAP**, change the bind password to a wrong value, Save. Trigger a provisioning action touching OpenLDAP (e.g. request an OpenLDAP-backed entitlement for `priya.wire` via Lesson 222's approval flow, or retry a pending transaction).  
   **Expect:** Action fails.

2. Open **Setup → Provisioning Transactions**, find the Failed row, read the error text.  
   **Expect:** LDAP `INVALID_CREDENTIALS`/bind failure message — note the exact text.

3. Fix: restore the correct bind password (`admin`), **Test Connection**, retry the failed transaction (or re-run the approval).  
   **Expect:** Transaction flips to Committed.

4. **Break #2 — bad JDBC credential.** Open `MNB-Application-CoreBanking`, change `password` from `mnb` to a wrong value, Save, **Test Connection**.  
   **Expect:** Immediate connection failure — a JDBC driver exception, a different shape than the LDAP bind error.

5. Attempt a JDBC provisioning action (e.g. disable a `MNB-CoreBanking` account from a leaver flow, Lesson 219). Check the Task Result for the aggregation/provisioning task.  
   **Expect:** `SQLException`/auth-denied message, distinct text from step 2's LDAP error.

6. Fix the password back to `mnb`, **Test Connection** green, retry.  
   **Expect:** Provisioning succeeds.

7. **Break #3 — malformed plan.** Edit a role or workflow so it generates a plan referencing an attribute that doesn't exist on the target schema (a bogus `AttributeRequest` name on `MNB-CoreBanking`, which only has `account_id, username, email, employee_id, status, entitlement`). Trigger it.  
   **Expect:** Schema/attribute-not-found error, a third distinct failure shape — not a connection error.

8. Revert the malformed change, re-run, confirm success.  
   **Expect:** Clean Committed result.

9. For each break, write one line: `<what you broke> → <error text location> → <fix> → <retry result>`.  
   **Expect:** Three lines saved with screenshots.

## If it fails

- **Test Connection passes but provisioning still fails** — connector caches connections; restart the failing task or bounce the app's connector cache via Debug Pages.
- **No error text on the transaction row** — click into the transaction detail, not just the list; full stack trace lives in the Task Result for the underlying task.
- **Fix doesn't take effect** — confirm you saved the `Application` object (not just closed the dialog) and are editing the app the failing plan actually targets, not a similarly-named Core CSV app.

## You are done when

All three induced failures are diagnosed from their real error surface, fixed, and confirmed Committed on retry, with three-line before/after notes saved.

## Control note

- **Control:** Provisioning failure triage and connector credential hygiene.  
- **Owner:** IAM Ops (connector config) + app owners (target credentials).  
- **SLA (lab):** Same session; production credential-related outages should be caught by connector health checks before they hit a provisioning queue.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/230/` — three break/fix/retry lines, error-text screenshots.

## Quick check

1. Where does a truncated transaction row's full error actually live? → The Task Result stack trace, not the transaction list.  
2. Why do LDAP and JDBC credential failures look different? → Different connector/driver error shapes for the same root cause.  
3. What's a third distinct failure class beyond bad credentials? → A malformed plan referencing a non-existent target attribute.

## Navigate

- Previous: Lesson 229  
- Next: Lesson 231  
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
