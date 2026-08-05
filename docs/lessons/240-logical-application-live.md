# Lesson 240 — Logical Application Over Live Apps

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~50 minutes  
**Prereq:** Lessons 209–213  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 85

> **Why:** Logical apps give certifiers one surface for many connectors — but a decision made against the logical account still has to remediate against the real tier account, or the revoke is theater.

## What this is

A **Logical Application** is IIQ's composite-view connector: it doesn't talk to a target itself, it stitches together accounts already aggregated from Tier apps (`MNB-WirePortal`, `MNB-Salesforce-CRM-Live`) into one virtual account per identity, using a composite/correlation rule. A certifier reviewing "Meridian Banking Suite" access sees one row instead of two app rows to cross-reference by hand.

## Know these

| Concept | Detail |
| --- | --- |
| Tier application | Real connector already aggregated (Wire, CRM) |
| Composite/correlation key | Attribute shared across tiers (e.g. `username`) |
| Logical account | Virtual, read-only — cannot itself provision |

```text
Certifier decision on logical account → routed to real tier app's provisioning plan
```

**Wrong way:** Assuming a revoke against the logical app provisioned — logical apps are composite/read-only; the plan must route to the real tier.

## Intent

- Build a Logical Application composing Wire + CRM.
- Confirm one identity's logical account shows composite attributes/entitlements from both tiers.
- Certify against the logical app and decide a revoke.
- Confirm the revoke remediated on the correct underlying tier account, not the logical shell.

## Before you start

- [ ] `MNB-WirePortal` and `MNB-Salesforce-CRM-Live` aggregated recently
- [ ] Both apps resolve to the same login-name attribute for the same identity
- [ ] `priya.wire` has accounts on both tiers
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/240`

## Do this

1. **Applications → Application Definition → New → Logical Application**, name `MNB-Logical-Banking-Suite`. Add Tier applications `MNB-WirePortal` and `MNB-Salesforce-CRM-Live`. Set the composite/correlation key to `username` (confirm both schemas share it).  
   **Expect:** Logical app saves with two tiers configured.
2. Define the logical schema's attributes to surface fields from both tiers (e.g. `wireActive`, `crmGroups`).  
   **Expect:** Schema references real tier attributes.
3. **Aggregate** the logical app (re-run tier aggregation first if stale).  
   **Expect:** Composite accounts build from already-aggregated tier data.
4. Open `priya.wire`'s **Application Accounts** tab.  
   **Expect:** One `MNB-Logical-Banking-Suite` composite account with attributes from both underlying accounts.
5. Launch a Targeted Certification (228's pattern) scoped to `MNB-Logical-Banking-Suite`, certifier `helen.ross`. Generate now.  
   **Expect:** Cert generates with one combined row for Priya.
6. As Helen, review the row and **Revoke** the CRM-sourced entitlement (or the composite, if per-attribute decisions aren't available).  
   **Expect:** Decision recorded.
7. Complete the certification, check **Provisioning Transactions**.  
   **Expect:** Transaction targets the real tier app (`MNB-Salesforce-CRM-Live`), never `MNB-Logical-Banking-Suite` itself — logical apps can't provision.
8. Verify on the tier: `curl -s http://localhost:8091/crm/scim/v2/Users | python3 -m json.tool` shows the entitlement gone for Priya.  
   **Expect:** Real removal confirmed on the source of truth.
9. Write one sentence: the logical view let Helen certify Priya's Wire+CRM access as a single decision instead of two separate app certifications.  
   **Expect:** Note saved.
10. Save the composite account screenshot, the cert decision, and the tier-level curl proof under `~/iiq-lab-evidence/sandbox/240/`.

## If it fails

- **Logical app aggregation returns no composite accounts** — the correlation key doesn't actually match between tiers (e.g. email vs username); align the identity attribute before re-aggregating.
- **Cert shows the logical app but rows are empty** — tier apps weren't re-aggregated after your last change; refresh both, then re-aggregate the logical app.
- **Revoke provisions against the logical app and errors** — confirm the certification's remediation settings reference the tier app, not the logical one.

## You are done when

A logical certification decision remediates against the correct real tier account, confirmed on that tier's live data.

## Control note

- **Control:** Composite-view certification with correct tier-level remediation.  
- **Owner:** IAM Engineering + App Owners (Wire, CRM).  
- **SLA (lab):** Revoke lands on real tier same cert cycle.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/240/` — composite account, cert decision, tier-level proof.

## Quick check

1. Can a logical application provision on its own? → No — composite/read-only; plans route to the real tier.  
2. What must match across tiers for composite accounts to build? → The correlation key attribute (e.g. `username`).  
3. What did the logical view save the certifier from doing? → Opening two separate app certifications and manually correlating rows.

## Navigate

- Previous: Lesson 239
- Next: Lesson 241
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
