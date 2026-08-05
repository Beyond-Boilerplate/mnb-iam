# Lesson 214 — Nail Correlation Across Live Apps

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~55 minutes  
**Prereq:** Lessons 204–210  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 17–19

> **Why (1–2 lines):** Bad correlation quietly creates permanent orphans and duplicate cubes — the single most expensive mistake in any real IIQ deployment. Examiners ask how employee id stays stable when a username is reissued.

## What this is

By this point you've aggregated six live applications (`MNB-OpenLDAP`, `MNB-ActiveDirectory-Live`, `MNB-Workday`, `MNB-CoreBanking`, `MNB-WirePortal`, `MNB-Salesforce-CRM-Live`), each with its own native key. The Enterprise Lab correlation standard ([`ENTERPRISE-LAB-V2.md`](../ENTERPRISE-LAB-V2.md#identity-correlation-standard)): **every employee-id-shaped attribute correlates to identity `userId`; every username-shaped attribute is the login/display key.** HCM `userId` (`MNB00001`), OpenLDAP `employeeNumber`, Samba AD `employeeNumber`, Keycloak `employeeId`, JDBC `employee_id`, CRM `externalId` — six names, one rule. Classic Lessons 17–18 taught that on CSV; here you prove it holds across live connectors and practice the uncorrelated-account repair loop (classic 19).

## Know these

| App | Correlation key → IIQ | Login / display key |
| --- | --- | --- |
| MNB-Workday (auth) | `userId` | worker name / email |
| MNB-OpenLDAP | `employeeNumber` | `uid` |
| MNB-ActiveDirectory-Live | `employeeNumber` | `sAMAccountName` |
| MNB-CoreBanking | `employee_id` | `username` |
| MNB-WirePortal | app correlation attr | account id |
| MNB-Salesforce-CRM-Live | `externalId` | `userName` |

```text
HCM agg (authoritative) → cube exists
  → other apps agg → match employee-id → link on same cube
  → no match → Uncorrelated Accounts (fix key, don't create a second cube)
```

**Wrong way:** Correlating on `uid` / `sAMAccountName`. A login can change; the employment id must not — conflating them orphans the identity on rename.

## Intent

- State the correlation standard from memory for all six live apps.
- Re-aggregate in authoritative-first order; confirm named personas have no unexplained uncorrelated accounts.
- Deliberately break, diagnose, and heal one bad correlation.
- Confirm manager hierarchy for `priya.wire` after refresh.

## Before you start

- [ ] `./tools/lab/docker/up.sh --enterprise` is up; IIQ healthy on `:8080`
- [ ] Lessons 204–210 apps exist and have aggregated at least once
- [ ] JDBC container reachable: `mnb-jdbc-sample`
- [ ] Evidence dir: `mkdir -p ~/iiq-lab-evidence/sandbox/214`

## Do this

1. Write the correlation table from memory, then check [`ENTERPRISE-LAB-V2.md`](../ENTERPRISE-LAB-V2.md#identity-correlation-standard).  
   **Expect:** Your list matches HR/HCM, OpenLDAP, Samba, Keycloak, JDBC, CRM rows above. If one surprises you, revisit 204–210 before continuing.

2. Run **Account Aggregation** in this order: `MNB-Workday` → `MNB-OpenLDAP` → `MNB-ActiveDirectory-Live` → `MNB-CoreBanking` → `MNB-WirePortal` → `MNB-Salesforce-CRM-Live`.  
   **Why:** Authoritative source first creates cubes so later apps have something to attach to.  
   **Expect:** Task Results succeed; reverse order often creates transient uncorrelated noise.

3. Open **Identities → Identity Warehouse → helen.ross** and count Application Accounts links; repeat for `priya.wire` and `marcus.approve`.  
   **Expect:** Each named persona shows links for every live app they should have (HCM + directories + any entitled Wire/CRM/Core rows).

4. Open **Identities → Uncorrelated Accounts** (or each Application’s uncorrelated list).  
   **Expect:** Zero unexplained hits for the three personas. Any hit is a bug to fix now (classic 19), not later.

5. Break one correlation on purpose:  
   `docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps -c "update mnb_app_accounts set employee_id='BOGUS' where username='helen.ross';"`  
   Re-aggregate `MNB-CoreBanking`, confirm Helen’s Core Banking link goes uncorrelated, then restore `employee_id='MNB00001'` and re-aggregate.  
   **Expect:** Uncorrelated after break; self-heals after fix. Note the Task Result timestamps under evidence.

6. Run Identity Refresh with manager correlation (or your build’s manager task). Open `priya.wire`.  
   **Expect:** Manager resolves to `sanjay.kapoor` (`MNB00006` per identity master), not blank.

7. In one sentence (evidence note), explain why login key ≠ correlation key.  
   **Expect:** Username may reissue; `employeeNumber` / `userId` must not for the employment relationship.

## If it fails

- **Transient orphans after reverse-order agg** — re-run step 2 in documented order.
- **Duplicate cubes instead of one cube with many links** — classic correlation failure; fix the key and prefer clean re-agg over destructive merge early in this path.
- **Broken JDBC row not showing uncorrelated** — force a full Account Aggregation, not Test Connection.
- **Manager blank after refresh** — manager’s own HCM row may be missing; re-aggregate `MNB-Workday`.

## You are done when

All three personas show correlated links across every live app they should have; you’ve broken and repaired one correlation by hand; `priya.wire`’s manager resolves after refresh.

## Control note

- **Control:** Account correlation integrity (no unexplained orphans / duplicate cubes).  
- **Owner:** IAM Ops.  
- **SLA (lab):** Fix deliberate break same session; production target often ≤1 business day for orphan triage.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/214/` — Task Result ids, before/after uncorrelated screenshots.

## Quick check

1. Which attribute on Samba must match HCM `userId`? → `employeeNumber`.  
2. Why aggregate HCM first? → Cubes must exist before other apps can correlate.  
3. What’s the wrong correlation key on OpenLDAP? → `uid` (login), not `employeeNumber`.

## Navigate

- Previous: Lesson 213  
- Next: Lesson 215  
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
