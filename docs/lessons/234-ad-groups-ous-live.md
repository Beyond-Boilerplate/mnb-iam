# Lesson 234 — AD Groups & OUs on Samba

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~60 minutes  
**Prereq:** Lesson 205  
**Stack:** `./tools/lab/docker/up.sh --enterprise --with=ad`

**Maps to classic track:** 57

> **Why:** Real AD governance is about group membership, not the account object — "does this person have Domain Admins" matters more than "does this person have an account." A cert that only reviews accounts misses the actual entitlement.

## What this is

Lesson 205 proved you could read Samba AD accounts through `MNB-ActiveDirectory-Live`. This lesson creates a real AD security group with `samba-tool`, brings it into IIQ as a managed entitlement, assigns it through a role/request so IIQ provisions the membership back onto the directory, and verifies with the same CLI tool an auditor would trust.

## Know these

| Object | Role |
| --- | --- |
| `samba-tool group add` | Creates the security group on the live DC |
| `samba-tool group addmembers` | Seeds/edits real membership |
| Managed Attribute (Requestable/Group) | What makes a group a *governed* entitlement, not just a visible attribute |
| `samba-tool group listmembers` | The audit-trusted verification command |

**Wrong way:** Treating group aggregation as "just another account attribute" — if the connector's group-aggregation option is off, membership entitlements never appear for certification at all.

## Intent

- Create a new AD group on the live Samba DC.
- Aggregate groups into IIQ and mark the group as a governed entitlement.
- Assign the group to Helen via role or direct request and provision it.
- Confirm membership landed on the directory with `samba-tool group listmembers`.
- Remove the membership through IIQ and confirm the directory reflects the removal too.

## Before you start

- [ ] Lesson 205 `MNB-ActiveDirectory-Live` aggregating cleanly
- [ ] `docker exec` access to the Samba container confirmed
- [ ] `helen.ross` and `priya.wire` identities present
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/234`

## Do this

1. Create the group: `docker exec -it mnb-samba-ad samba-tool group add MNB-Portal-Users`.  
   **Expect:** Group created with no pre-existing membership noise (a new group, not a reused one).
2. Seed a starting member: `docker exec -it mnb-samba-ad samba-tool group addmembers MNB-Portal-Users helen.ross`.  
   **Expect:** Group aggregates with at least one row.
3. **Applications → Application Definition → MNB-ActiveDirectory-Live → Aggregate**, with group/entitlement aggregation enabled (check **Aggregate Groups** or run the dedicated group task).  
   **Expect:** Task Result shows group objects imported.
4. **Applications → Manage Entitlement Catalog** (or **Define → Managed Attributes**), find `MNB-Portal-Users`, mark it **Requestable**/**Group**.  
   **Expect:** This is what turns it into a governed entitlement instead of a visible-only attribute.
5. Assign it to `priya.wire` — either via a birthright role's provisioning policy (216-style) or **Manage Access → Request Access** — then approve/provision.  
   **Expect:** Provisioning transaction completes successfully.
6. Confirm: `docker exec -it mnb-samba-ad samba-tool group listmembers MNB-Portal-Users`.  
   **Expect:** Lists both `helen.ross` and `priya.wire`.
7. Remove Priya's assignment in IIQ (unassign the role, or revoke via a mini-certification), let it provision.  
   **Expect:** Re-run `listmembers` — Priya is gone, Helen remains. A connector that can add but not remove members is only half-built for governance.
8. Save both `listmembers` outputs (before/after Priya's removal) under `~/iiq-lab-evidence/sandbox/234/`.

## If it fails

- **`samba-tool` not found / wrong container name** — confirm with `docker compose -f docker-compose.iiq.yml -f docker-compose.enterprise.yml ps` and adjust `mnb-samba-ad`.
- **Group doesn't appear in IIQ after aggregation** — confirm `Aggregate Groups`/`Iterate Group Members` is enabled; account-only aggregation skips group objects.
- **Provisioning removes account instead of just membership** — check the generated `ProvisioningPlan` for an `AttributeRequest` on `memberOf`/`member` (add/remove), not a full account delete.

## You are done when

Group membership provisions both directions — IIQ add reaches Samba, IIQ remove reaches Samba — confirmed with `samba-tool group listmembers`.

## Control note

- **Control:** AD group entitlement governance (add + remove both provable).  
- **Owner:** IAM Engineering / AD Ops.  
- **SLA (lab):** Membership change reflected on directory same request cycle.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/234/` — `listmembers` before/after.

## Quick check

1. What makes a group a *governed* entitlement vs a visible attribute? → Marked Requestable/Group in the Managed Attribute catalog.  
2. Which CLI command is the audit-trusted verification? → `samba-tool group listmembers`.  
3. Why prove removal, not just addition? → A connector that only adds is half-built for governance.

## Navigate

- Previous: Lesson 233
- Next: Lesson 235
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
