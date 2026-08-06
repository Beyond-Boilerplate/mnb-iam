# Lesson 233 — Live Aggregation Runbook

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~40 minutes  
**Prereq:** Lessons 207–210  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 16 / 54

> **Why:** Aggregate targets before HR and you correlate accounts to identities that don't exist yet — the orphan links break Lesson 219's leaver logic and Lesson 214's correlation. Document the aggregation sequence before calling refresh done — "we ran it eventually" is how silent orphans stick.

## What this is

By this lesson you have six live apps — `MNB-Workday`, `MNB-OpenLDAP`, `MNB-ActiveDirectory-Live`, `MNB-CoreBanking`, `MNB-WirePortal`, `MNB-Salesforce-CRM-Live`, `MNB-Okta` — each aggregating on its own schedule. A bank ops team doesn't run these ad hoc; they run a fixed nightly sequence: authoritative source first, Refresh Identity Cubes, then every downstream target, then a final refresh to promote entitlements. You write that sequence as a real runbook, run it clean, then break the order on purpose to see the orphan symptom yourself.

## Know these

| Step | Why it's ordered here |
| --- | --- |
| 1. Aggregate `MNB-Workday` | HCM is authoritative for identity existence |
| 2. Refresh Identity Cubes | Promotes HR attrs (`employeeNumber`, manager) targets correlate against |
| 3. Aggregate directories + JDBC + Wire/CRM/Okta | Each depends on the cube already having the right key |
| 4. Refresh Identity Cubes again | Promotes newly-linked entitlements onto the cube |

```text
HCM (Workday) → Refresh → directories/AD → CoreBanking → Wire/CRM/Okta → Refresh
```

**Wrong way:** Aggregating targets before HR "to save time" — creates uncorrelated native accounts that silently sit as orphans until someone notices in a certification.

## Intent

- Write a 5-line runbook: HR → Refresh → directories → JDBC → Wire/CRM/Okta → Refresh.
- Execute it once end-to-end with zero orphaned accounts.
- Schedule any app still manual-only as a recurring Task.
- Deliberately break the order once and capture the orphan symptom, then fix it.

## Before you start

- [ ] All six apps (207–210) aggregate successfully standalone
- [ ] `./tools/lab/enterprise/hcm-scenario.sh` available for a fresh joiner
- [ ] Know a recent joiner or `helen.ross` to spot-check
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/233`

## Do this

1. Write the runbook in your evidence notes: `1) Aggregate MNB-Workday  2) Refresh Identity Cubes  3) Aggregate MNB-OpenLDAP + MNB-ActiveDirectory-Live  4) Aggregate MNB-CoreBanking  5) Aggregate MNB-WirePortal + MNB-Salesforce-CRM-Live + MNB-Okta, then Refresh Identity Cubes again`.  
   **Expect:** A 5-line checklist you can hand to anyone.
2. Execute it via **Monitor → Tasks → New Task** or **Applications → Aggregate**, in that exact sequence — wait for each Task Result to show Complete before starting the next.  
   **Expect:** All six tasks Complete, none run in parallel.
3. Open **Identities → Identity Warehouse**, spot-check `helen.ross` or a recent joiner.  
   **Expect:** Every expected link (OpenLDAP, AD-Live, CoreBanking, Wire, CRM, Okta) shows correlated, none orphaned.
4. Check **Monitor → Tasks → Task Schedule** for any of the six apps missing a recurring schedule.  
   **Expect:** Add a nightly schedule for anything still manual-only, so the runbook survives without you.
5. Break it on purpose: run `./tools/lab/enterprise/hcm-scenario.sh joiner` for a fresh worker you haven't pulled into IIQ, then aggregate `MNB-CoreBanking` or `MNB-Salesforce-CRM-Live` for them **before** aggregating `MNB-Workday`.  
   **Expect:** Target aggregation completes without error — the trap is that it looks fine.
6. **Applications → Application Definition → \<target\> → Accounts**, find the new native account.  
   **Expect:** Shows **uncorrelated** — no linked Identity. This is the orphan symptom.
7. Now run step 1's HR aggregation and Refresh, then re-aggregate the target.  
   **Expect:** The account correlates on the next pass — proof the fix is "aggregate HR first," not "wait longer."
8. Save the runbook, clean-run proof, and orphan-then-fixed screenshots under `~/iiq-lab-evidence/sandbox/233/`.

## If it fails

- **Orphan never correlates even after HR aggregation** — correlation rule (214) may key off an attribute the HR record didn't populate; check `employeeNumber`/`userId` both sides.
- **Task Schedule tab missing for an app** — it was only aggregated ad hoc earlier; create fresh via **New Task → Account Aggregation**.
- **Parallel aggregation "works fine" anyway** — lab data is small; order matters more as volume grows. Treat as a correctness rule, not a lab artifact.

## You are done when

You've executed your own runbook clean once, and reproduced + fixed the orphan-account symptom by breaking the order on purpose.

## Control note

- **Control:** Aggregation sequencing / orphan-account prevention.  
- **Owner:** IAM Operations.  
- **SLA (lab):** Nightly sequence enforced via Task Schedule, not tribal memory.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/233/` — runbook text, clean-run screenshot, orphan before/after.

## Quick check

1. What must aggregate before any target? → HCM (`MNB-Workday`).  
2. What does an orphan account look like in IIQ? → Native account, uncorrelated, no linked Identity.  
3. Why refresh twice? → Once to promote HR attrs before correlation, once to promote new entitlements after.

## Navigate

- Previous: Lesson 232
- Next: Lesson 234
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
