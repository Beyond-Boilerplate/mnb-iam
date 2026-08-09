# Lesson 234 — AD Groups & OUs on Samba

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~65 minutes  
**Prereq:** Lessons 205, 221–222  
**Stack:** `./tools/lab/docker/up.sh --enterprise --with=ad`

**Maps to classic track:** 57

> **Why:** Real AD governance is about **group membership** and **where** the account lives (OU) — “Domain Admins” and “wrong OU” matter more than “account exists.” A cert that only reviews accounts misses the entitlement.

## What this is

Lesson 205 proved you could read Samba AD accounts through `MNB-ActiveDirectory-Live`. This lesson goes further:

1. Create a **security group** with `samba-tool`  
2. Aggregate it into IIQ as a **managed entitlement**  
3. Provision membership **add** and **remove** through IIQ  
4. Verify with `samba-tool` (auditor-trusted CLI)  
5. Observe **OU** placement — accounts live under an Organizational Unit; movers/leavers often require OU + group changes together

**OU (Organizational Unit):** a container in the directory tree (e.g. `OU=Employees,DC=…`). Groups are entitlements; OUs are location. Confusing them is a common beginner mistake.

Classic 57 taught AD groups; here both add and remove must hit the live DC.

## Know these

```text
samba-tool group add
  → Account Group Aggregation on MNB-ActiveDirectory-Live
  → Managed Attribute requestable
  → Request / role assign → provision member add
  → samba-tool group listmembers  (proof)
  → Remove in IIQ → provision member remove
  → listmembers again (Priya gone, Helen remains)
```

| Object | Role |
| --- | --- |
| `samba-tool group add` | Creates the security group on the live DC |
| `samba-tool group addmembers` | Seeds real membership (optional baseline) |
| Managed Attribute (Requestable/Group) | Makes a group a *governed* entitlement |
| `samba-tool group listmembers` | Audit-trusted verification |
| **OU** | Directory container for accounts — not an entitlement by itself |

- **Wrong way:** Account-only aggregation with group aggregation off — memberships never appear for certs.
- **Wrong way:** Proving add but not remove — half a connector for governance.
- **Wrong way:** Treating OU moves as “just another group” — different object class / plan shape.

## Intent

- Create `MNB-Portal-Users` on Samba; aggregate groups into IIQ; mark requestable.
- Assign to Priya via request/role; confirm membership with `samba-tool`.
- Remove Priya via IIQ; confirm directory removal.
- Note Helen’s OU (or account DN) so you can explain OU vs group to an auditor.

## Before you start

- [ ] Stack includes Samba: `--with=ad`
- [ ] Lesson 205 `MNB-ActiveDirectory-Live` aggregating cleanly
- [ ] `docker exec` access to the Samba container
- [ ] `helen.ross` and `priya.wire` present; Lesson 222 LCM path available for requests
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/234
```

## Do this

### Task 1 — Create the AD group

```bash
docker exec -it mnb-samba-ad samba-tool group add MNB-Portal-Users
```

- **Why:** govern a group you created — not a mystery seed group.
- **Expect:** group created with no pre-existing membership noise.

> **Watch out:** Wrong container name? Check `docker ps` for the Samba service and adjust `mnb-samba-ad`.

### Task 2 — Seed a baseline member (optional but useful)

```bash
docker exec -it mnb-samba-ad samba-tool group addmembers MNB-Portal-Users helen.ross
```

- **Expect:** Helen is a member before IIQ provisions Priya — gives you a stay-vs-leave contrast in Task 7.

### Task 3 — Aggregate groups into IIQ

1. **Applications → Application Definition → MNB-ActiveDirectory-Live**  
2. Run aggregation with **groups** enabled (Aggregate Groups / dedicated Account Group Aggregation task — same lesson as OpenLDAP in 216)  
3. Confirm Task Result imports group objects  

- **Why:** account aggregation alone will **not** fill the entitlement catalog for groups.
- **Expect:** `MNB-Portal-Users` visible in Entitlement Catalog / Managed Attributes.

### Task 4 — Mark the group requestable

**Applications → Entitlement Catalog** (or Manage → Managed Attributes) → `MNB-Portal-Users` → enable **Requestable** / Group options.

- **Why:** turns a visible attribute into a governed catalog item (Lesson 221 pattern).
- **Expect:** searchable in Request Access (or assignable via a small IT Bundle).

### Task 5 — Provision membership add for Priya

Assign via **Request Access** (approve with Lesson 222 path) **or** a small IT Bundle required entitlement + direct assign + provision refresh.

- **Expect:** Provisioning Transaction **Committed** for membership add (not account create/delete).

### Task 6 — Prove on the DC

```bash
docker exec -it mnb-samba-ad samba-tool group listmembers MNB-Portal-Users
```

- **Expect:** lists both `helen.ross` and `priya.wire`.

Save output under evidence.

### Task 7 — Provision membership remove

1. Remove Priya’s assignment in IIQ (unassign role / revoke entitlement)  
2. Refresh with **provisioning**  
3. Re-run `listmembers`  

- **Expect:** Priya **gone**, Helen **remains**.

> **Tip:** If IIQ deleted the whole AD account instead of removing membership, open the ProvisioningPlan — you want `AttributeRequest` on `memberOf`/`member` (Remove), not account Delete.

### Task 8 — OU awareness (read-only proof)

1. In IIQ or with Samba tools, note Helen’s account **DN** / OU (e.g. under `OU=…`)  
2. Write one evidence line:

```text
Group MNB-Portal-Users = entitlement (membership).
OU on Helen's DN = container location, not the same as group membership.
Mover/leaver often needs BOTH group revoke and OU/disable handling.
```

- **Why:** title promises OUs — students must not leave thinking “OU = group.”
- **Expect:** written distinction under evidence.

Optional stretch: move a disposable test account to another OU with `samba-tool user move` and re-aggregate — observe DN change without treating it as an entitlement cert row.

## If it fails

| Symptom | Fix |
| --- | --- |
| `samba-tool` / wrong container | `docker ps` → correct Samba container name |
| Group missing after agg | Enable Aggregate Groups / group task — account-only skips groups |
| Provision deletes account | Plan shape wrong — membership AttributeRequest, not Delete |
| Priya never appears in listmembers | PT Failed — check AD connector credentials / DN; retry after Lesson 230 triage |
| Request Access can’t find group | Mark requestable (Task 4) or wrap in IT Bundle |

## You are done when

- [ ] Group membership add **and** remove confirmed with `samba-tool group listmembers`  
- [ ] Written OU vs group distinction  
- [ ] Provisioning Transaction shows membership change, not accidental account delete  

## Control note

- **Control:** AD group entitlement governance (add + remove) + OU awareness  
- **Owner:** IAM Engineering / AD Ops  
- **SLA (lab):** Membership change reflected same request cycle  
- **Evidence:** `~/iiq-lab-evidence/sandbox/234/` — listmembers before/after; OU note  

## Quick check

1. What makes a group a governed entitlement? → Requestable/Group in Managed Attribute catalog  
2. Audit-trusted verification command? → `samba-tool group listmembers`  
3. Why prove removal? → Add-only connectors are half-built for governance  
4. OU vs group in one line? → OU = where the account lives; group = entitlement membership  

## Feedback

Could you explain OU vs group to a new hire without this page? If remove deleted the account, paste the plan operation you saw (AttributeRequest vs Delete) — that diagnosis is the skill.

## Navigate

- Previous: [Lesson 233](233-aggregation-strategy-live.md)
- Next: [Lesson 235](235-ldap-provision-stretch.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
