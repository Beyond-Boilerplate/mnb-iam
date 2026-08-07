# Lesson 229 — Certification Remediation Proof

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~70 minutes  
**Prereq:** Lessons 226–227  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 46

> **Why:** Revoke without target proof is theater — ops needs the target system row to prove revoke actually hit the target, not only IIQ’s word that it happened.

## What this is

In Lessons 226–227 you clicked **Revoke** and saw a **Provisioning Transaction**. That click is a **promise**. IIQ turns it into:

```text
Cert Revoke decision
  → ProvisioningPlan
  → ProvisioningTransaction
       → Committed (auto-provision succeeded)
       → Failed / Retry (needs manual Remediation work item)
  → re-aggregate target
  → cube Entitlements match reality (no drift)
```

**Remediation** here means closing that loop: either the connector already removed the access, or a human completes a **Certification Remediation** work item (run the LDIF/SQL/manual step) and marks it done.

You will pick **one** revoke from 226 or 227 and build an auditor-ready evidence pack: transaction id + direct target query + Task Result + Mailpit thread.

## Know these

| Status | Meaning | Your next move |
| --- | --- | --- |
| **Committed / Success** | Connector reported success | Still **verify on target** — don’t trust the label alone |
| **Failed / Retry** | Auto path didn’t finish | Open Remediation work item; fix target; Complete WI |
| **Drift** | IIQ cube ≠ target | Re-aggregate; if still wrong, connector/cache issue |

| Term | Plain English |
| --- | --- |
| **ProvisioningPlan** | What IIQ intends to change on apps |
| **ProvisioningTransaction** | Record of an attempt to execute a plan |
| **Remediation work item** | Manual task when auto-provision can’t finish |
| **Re-aggregation** | Re-read the target so the cube matches reality |
| **Drift** | IIQ believes X; target still has Y |

- **Wrong way:** Trusting “Committed” alone — always verify with a direct target query.
- **Wrong way:** Closing a Failed transaction without changing the target — paperwork without effect.
- **Wrong way:** Skipping re-aggregation — cube can lie until the next agg.

## Intent

- Pick one revoke from 226 or 227; pull its Provisioning Transaction.
- Verify the account on OpenLDAP, JDBC, or CRM actually lost the entitlement.
- If Failed/Retry, complete the manual Remediation work item.
- Re-aggregate; confirm cube matches target; bag matched evidence.

## Before you start

- [ ] At least one Revoke completed in Lesson 226 or 227 (with PT id if you saved it)
- [ ] Ability to query the target (`ldapsearch`, `psql`, or `curl`)
- [ ] Mailpit: [http://localhost:8025](http://localhost:8025)
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/229
```

## Do this

### Task 1 — Open the Provisioning Transaction

1. **Setup → Provisioning Transactions**  
2. Filter by the identity you revoked in 226 or 227  
3. Copy:

| Field | Value |
| --- | --- |
| Transaction id | |
| Target application | |
| Status (Committed / Failed / Retry) | |
| Identity | |
| Operation / entitlement | |

- **Expect:** one clearly identifiable transaction row.

Save under evidence.

### Task 2 — Verify on the actual target

Use the query that matches your revoked app:

**OpenLDAP:**

```bash
ldapsearch -x -H ldap://localhost:389 \
  -b ou=people,dc=meridiannb,dc=com \
  -D 'cn=admin,dc=meridiannb,dc=com' -w admin \
  '(uid=<user>)' memberOf
```

**JDBC Core Banking:**

```bash
psql -h localhost -p 5435 -U mnb -d mnb_apps \
  -c "select username, status, entitlement from mnb_app_accounts where username='<user>';"
```

**CRM SCIM mock:**

```bash
curl -s http://localhost:8091/crm/scim/v2/Users \
  | python3 -m json.tool
```

- **Expect:** revoked group/entitlement **absent**, or account disabled / inactive.

Save raw output under evidence (redact secrets if any).

> **Watch out:** Committed + target unchanged = lag, wrong DB, or connector lied — force fresh aggregate before concluding (Task 4).

### Task 3 — Manual remediation path (if Failed / Retry)

If status is **Failed** or **Retry**:

1. Open **Work Items** as the remediator (app owner — `marcus.approve` or `spadmin`)  
2. Find **Certification Remediation** item for this revoke  
3. Perform the manual change on the target yourself (LDIF / SQL / SCIM PATCH)  
4. Mark the work item **Complete**  

- **Why:** the lesson isn’t done until target agrees with IIQ — automated or manual.
- **Expect:** work item closed; target actually changed.

If you were already Committed and Task 2 proved the target, skip to Task 4.

### Task 4 — Re-aggregate and check the cube

1. **Applications → Aggregate** for the affected app  
2. Open the identity cube → **Entitlements** / Application Accounts  
3. Confirm the revoked item is gone from IIQ’s view too  

- **Why:** catches “IIQ thinks it revoked; target still has it” **and** the reverse after manual fix.
- **Expect:** entitlement gone from the cube after re-aggregation.

### Task 5 — Task Result proof aggregation ran

**Monitor → Tasks → Task Results** — locate the aggregation result.

Note:

- Finish time  
- Rows / change counts  

- **Expect:** Task Result confirms aggregation actually ran and (ideally) changed something.

### Task 6 — Mailpit thread for this identity

In Mailpit, find messages for this identity across the cert lifecycle:

- Launch  
- Decision / assignment  
- Remediation (if any)  
- Completion  

- **Expect:** subjects/timestamps tell a consistent story.

### Task 7 — Assemble the matched evidence pack

One folder / note under `~/iiq-lab-evidence/sandbox/229/`:

```text
PT id: ________
Target query file: ________
Agg Task Result: ________
Mailpit thread: ________
Outcome: Committed verified | Manual remediation completed
```

- **Expect:** one matched set an auditor can follow without asking you questions.

## If it fails

| Symptom | Fix |
| --- | --- |
| Committed but target unchanged | Force fresh aggregate; confirm you’re querying the same DB/host the connector uses |
| Remediation WI never appeared | Cert definition remediation flow / remediator; app `featuresString` includes provisioning |
| Re-agg still shows old entitlement | Wrong target query; cache/replica; confirm JDBC `mnb_apps` is the connector DB |
| No revoke to trace | Re-do a small revoke in 226/227 first — this lesson needs a real PT |

## You are done when

- [ ] One revoke verified end-to-end on a live target  
- [ ] Task Result + Mailpit thread saved  
- [ ] Cube matches target after re-aggregation  

## Control note

- **Control:** Certification remediation closure and drift detection  
- **Owner:** App owner (manual remediation) + IAM Ops (drift monitoring)  
- **SLA (lab):** Same session; production remediation SLAs are often 5–10 business days  
- **Evidence:** `~/iiq-lab-evidence/sandbox/229/` — transaction id, target query output, Task Result, Mailpit thread  

## Quick check

1. What turns a cert Revoke into an actual action? → ProvisioningPlan → ProvisioningTransaction  
2. What catches “IIQ revoked it, target didn’t” drift? → Re-aggregation + direct target query  
3. What closes a Failed/Retry transaction? → Manual Remediation work item, completed and marked done  
4. Why isn’t “Committed” enough alone? → Cache/lag/wrong target can disagree with the label  

## Feedback

Could you list the four evidence artifacts this lesson bags without scrolling up? If Committed disagreed with your target query, write which side you trusted first and why — that instinct is the skill.

## Navigate

- Previous: [Lesson 228](228-targeted-cert-live.md)
- Next: [Lesson 230](230-provisioning-troubleshoot-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
