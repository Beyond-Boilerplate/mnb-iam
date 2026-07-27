# Lesson 35 — Access Request Catalog

**Level:** Intermediate  
**Track:** Requests  
**Time:** 60–90 minutes  
**Prereq:** Lessons 10 (entitlement dictionary), 28 (privileged roles); Lifecycle lessons 29–34 recommended  

**Lab data:**
- `lab-data/reference/entitlement-dictionary.csv` — `CRM`, `DWRP` requestable; `AWS_ADMIN`, `PRIV_BREAK` controlled
- Roles from prior lessons: e.g. `MNB-Role-RelationshipManager`, developer packs
- **Requires LCM:** import `init-lcm.xml` via `iiq console` if Access Request menus are missing ([LOCAL_SETUP.md](../LOCAL_SETUP.md))

---

## Learning objectives

You will be able to:

1. Mark appropriate Meridian entitlements/roles as **requestable** (`CRM`, `DWRP`) for the LCM catalog.
2. Keep critical items (`AWS_ADMIN`, `PRIV_BREAK`) hidden or strongly controlled—not casual self-service.
3. Submit an access request (self or on-behalf) for a CRM-aligned user and observe the IdentityRequest.
4. Verify catalog display names match the entitlement dictionary.
5. Explain why birthright items should not clutter the request catalog.
6. Confirm LCM prerequisites when Manage Access / Access Request UI is unavailable.

---

## Why this matters

**Business:** If Relationship Managers cannot request CRM safely, they share passwords or open shadow SaaS. A clean catalog makes IAM the path of least resistance.

**Control / audit:** Requestable ≠ approved. The catalog is the front door; approvals (Lesson 36) and SoD (Lessons 39–40) are the locks. Control owner: IAM Governance with app owners. Examiner question: *Which privileged entitlements are excluded from self-service, and how is that enforced?*

---

## Concepts

### Catalog design matrix

| Entitlement / role | Risk | Catalog stance | Typical requester |
| --- | --- | --- | --- |
| `CRM` | medium | Requestable | RM / CML staff |
| `DWRP` | medium | Requestable | Developers / SRE |
| `ELDAP` | medium | Usually birthright—not catalog noise | — |
| `AWS_ADMIN` | critical | Not casual; hidden or break-glass/privileged path | Technology only |
| `PRIV_BREAK` | critical | Emergency path only (Lesson 37) | On-call + Security |
| `WIRE_INIT` / `WIRE_APPR` | critical | Optional requestable with Treasury owner—not birthright | Payments |

### LCM request flow

```text
User/Manager opens Access Request (LCM)
        │
        ▼
Select requestable roles/entitlements from catalog
        │
        ▼
IdentityRequest object created
        │
        ▼
Approval work items (Lesson 36)
        │
        ▼
Provisioning plan / ticket (lab may be stubbed)
```

**IIQ terms:** *Requestable* managed attribute / role flag controls catalog visibility. *IdentityRequest* is the audit object for the ask. *LCM* (Lifecycle Manager) supplies the Manage Access UI—without `init-lcm.xml` / feature activation, menus may be empty.

---

## Before you start

- [ ] IIQ at `http://localhost:8080/identityiq`.
- [ ] Confirm LCM: **Manage Access** / Access Request (or equivalent) visible. If not:

```bash
./iiq console
```

```text
import init-lcm.xml
quit
```

- [ ] Entitlements aggregated; dictionary descriptions from Lesson 10 applied where possible.
- [ ] Pick a target identity who needs CRM but may lack it (e.g. an RM without CRM, or use on-behalf for training user)—do not break `sofia.torres` freeze state unnecessarily; prefer `nina.cruz` / `amelia.brooks` / a test identity as appropriate.
- [ ] Notebook for catalog decisions.

---

## Lab procedure

### Task 1 — Align catalog with the entitlement dictionary

1. Open `~/iiq-lab-data/reference/entitlement-dictionary.csv`.
2. Note display names for `CRM` (Salesforce CRM) and `DWRP` (Dev Workstation / Repo).
3. In IIQ, open **Applications** → entitlement / **Managed Attribute** views (or Global Settings → entitlements—use search if labels differ).
4. For `CRM` and `DWRP`, set **Requestable** = true (or equivalent). Ensure description/display name matches dictionary language.

**Expected result:** CRM and DWRP appear as business-friendly requestable items, not raw codes only.

**If it fails:** Edit managed attribute XML via Debug only if UI lacks the flag; keep `MNB-` naming discipline.

---

### Task 2 — Guard AWS_ADMIN and PRIV_BREAK

1. Locate managed attributes / roles for `AWS_ADMIN` and `PRIV_BREAK` (and roles `MNB-Role-CloudAdmin` / `MNB-Role-BreakGlass` if created in Lesson 28).
2. Set **Requestable** = false for casual catalog, **or** requestable only with warning + restricted population (document which approach you chose).
3. Meridian training standard: **not casually requestable**. Break-glass uses Lesson 37 path with ticket comment—not a friendly tile next to CRM.

**Expected result:** Written decision: “AWS_ADMIN / PRIV_BREAK excluded from standard self-service catalog.”

**If it fails:** If you cannot unset requestable, document compensating control (approval always Security + hide via QuickLink population).

---

### Task 3 — Mark relationship / developer request packs

1. If `MNB-Role-RelationshipManager` (or CRM IT role) exists, mark requestable for users not covered by birthright.
2. Optionally mark a developer optional entitlement pack requestable for `DWRP`.
3. Ensure birthright-only items (base employee ELDAP role) are **not** requestable to reduce noise.

**Expected result:** Catalog shows business-needed requestables; birthright baseline absent from shopping list.

**If it fails:** Entitlement-level requestable CRM/DWRP alone is enough for this lesson.

---

### Task 4 — Submit a CRM access request

1. Open LCM **Manage Access** / **Access Request** (or equivalent).
2. Choose identity: prefer an RM-aligned user missing CRM, or request on-behalf as `spadmin` for training.
3. Add `CRM` (or RM requestable role) to the cart.
4. Enter business justification: e.g. `Commercial RM book access — training request`.
5. Submit.

**Expected result:** Confirmation with request id; IdentityRequest created; approval work item may appear for manager (complete in Lesson 36 if pending).

**If it fails:** Verify LCM import; check QuickLink populations include your user; try `spadmin` on-behalf request.

---

### Task 5 — Track the IdentityRequest

1. Navigate to Access Requests / Identity Requests search (or Debug → IdentityRequest).
2. Open your request; note state (Pending Approval / Executing / End).
3. Record request id, requester, target identity, items requested, timestamp.

**Expected result:** You can point to one IdentityRequest object that proves the CRM ask—even if approvals are unfinished.

**If it fails:** Lesson 38 deep-dives tracking; for now capture any request id / work item id.

---

### Task 6 — UX note for Risk

1. Browse the catalog as an end user would.
2. Confirm dictionary names appear (not only `CRM`).
3. Confirm AWS/PRIV_BREAK are not one-click adjacent to CRM without friction.
4. Write one UX sentence for the binder: “Catalog encourages safe requests and discourages privileged browsing.”

**Expected result:** Screenshot of catalog showing CRM/DWRP present and privileged items absent or clearly segregated.

---

## Acceptance criteria

- [ ] `CRM` and `DWRP` marked requestable with dictionary-aligned names.
- [ ] `AWS_ADMIN` / `PRIV_BREAK` not casually requestable (documented control).
- [ ] At least one access request submitted.
- [ ] IdentityRequest (or work item) id recorded.
- [ ] LCM prerequisite verified or remediated (`init-lcm.xml`).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No Access Request menu | LCM not initialized | `import init-lcm.xml`; check license/feature notes |
| Entitlement not in catalog | Not requestable / wrong app | Set requestable; refresh; check populations |
| Only technical names | Dictionary not applied | Update managed attribute display name |
| AWS visible to everyone | Flag left true | Unset requestable; restrict QuickLink |
| Request fails immediately | Missing approval scheme / workflow | Use default LCM; fix in Lesson 36 |

---

## Training binder evidence

1. Dictionary excerpt for CRM/DWRP.
2. Managed attribute screenshots (requestable flags).
3. Written AWS/PRIV_BREAK exclusion decision.
4. Access request confirmation / IdentityRequest id.
5. Catalog UX screenshot.

---

## Knowledge check

1. What should be requestable for Meridian RMs and developers in this lesson?
2. What must not be casually requestable?
3. Where do you track the submitted ask?
4. Does requestable mean the access is already approved?
5. What import enables LCM starter objects in the lab?

### Answers

1. `CRM` and `DWRP` (and related request packs)—not birthright clutter.
2. `AWS_ADMIN` and `PRIV_BREAK` (and similar critical privilege).
3. IdentityRequest / Access Request search (and related work items).
4. No—requestable only means visible to request; approvals and SoD still apply.
5. `init-lcm.xml` via `iiq console`.

---

## Stretch lab

1. Add `WIRE_INIT` as requestable with **Treasury owner** (`rachel.evans`) approval only—never manager-only.
2. Create separate QuickLinks: “Standard Access” vs “Privileged Access.”
3. Hide birthright roles from catalog via requestable flags audit report.

---

## Summary

- You built a Meridian request catalog that promotes CRM/DWRP self-service.
- You excluded casual AWS/break-glass browsing from that catalog.
- You submitted and located an IdentityRequest as the audit spine for later lessons.

---

**Previous:** [Lesson 34 — Rapid Offboarding Incident Drill](34-rapid-offboarding-drill.md)  
**Next:** [Lesson 36 — Approval Chains & Escalations](36-approval-chains.md)
