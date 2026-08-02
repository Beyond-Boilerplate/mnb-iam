# Lesson 28 — Privileged Access Role Design

**Level:** Advanced  
**Track:** Roles  
**Time:** 60–75 minutes  
**Prereq:** Lesson 27; AWS_ADMIN and PRIV_BREAK entitlements exist in dictionary/apps  

**Lab data:**
- `~/iiq-lab-data/reference/entitlement-dictionary.csv` (AWS_ADMIN, PRIV_BREAK)
- Cloud account extract / MNB-AWS-Cloud; approval expectations for later LCM lessons
- Personas: `amelia.brooks` (must never receive privilege); `raj.external` (contractor AWS risk); break-glass path for Lesson 37

---

> **Verify:** Lab lesson — create request-only `MNB-Role-CloudAdmin` and `MNB-Role-BreakGlass`. Academy **Verify now** checks those Bundles (+ optional `MNB-IT-CloudAdmin`).

## Learning objectives

You will be able to:

- Create two-tier privileged packs: **`MNB-IT-CloudAdmin`** / **`MNB-Role-CloudAdmin`** and **`MNB-IT-BreakGlass`** / **`MNB-Role-BreakGlass`**
- Keep entitlements on type **it**; keep requestable + zero auto-assign on type **business**
- Prove neither privileged business role is granted by birthright or job Match Lists
- Define approval expectations (Technology Director + Security for break-glass)
- Place privileged **business** roles on a **monthly** certification scope list
- Publish a privileged access runbook: joiners never auto-get; leavers revoke same day

---

## Why this matters

**Business.** Privileged access needs time bounds, approvals, and monitoring. Standing cloud admin for convenience is a governance failure mode—especially when contractors like `raj.external` hold `AWS_ADMIN` past SOW end. Break-glass without logging and approval is theater: outages tempt shared passwords; Meridian needs a governed emergency path instead (Lesson 37).

**Control / audit.** Privileged roles are rare, owned, frequently certified, and excluded from birthright. Examiners ask for the privileged inventory, approval path, and revocation SLA. This lesson designs the IIQ role objects and control narrative; Lessons 35–37 wire request/approval flows.

---

## Concepts

### Request-only by design (same two-tier as Lessons 24–25)

Birthright and job Match Lists must never auto-grant CloudAdmin or BreakGlass—including for `CLD01`. Job creates eligibility to **request**, not standing privilege. Stock IIQ still forbids Entitlements on type **business**—privileged packs use IT + business like everything else:

```
Birthright / job Match Lists ──✗──► MNB-Role-CloudAdmin / MNB-Role-BreakGlass
Access request (future) ──► approvals ──► Assigned business role
                                              └── Required ──► MNB-IT-* ──► entitlement
```

| Business role (requestable) | Required IT pack | Entitlement | Auto-assign | Cert frequency | Approvers (intent) |
| --- | --- | --- | --- | --- | --- |
| `MNB-Role-CloudAdmin` | `MNB-IT-CloudAdmin` | AWS_ADMIN | No | Monthly | Manager + Technology / Cloud owner |
| `MNB-Role-BreakGlass` | `MNB-IT-BreakGlass` | PRIV_BREAK | No | Monthly (or per-use) | Technology Director + Security |

### Standing vs break-glass

**CloudAdmin** may be standing but tightly controlled (manager + tech owner, monthly cert, same-day leaver revoke). **BreakGlass** is emergency, time-bounded (≤8 hours lab standard), heavily logged, Security-approved—with PAM integration noted even if not implemented in lab. Standing break-glass accounts are forbidden.

### Negative proof matters

`amelia.brooks` (teller birthright) must never gain these **business** roles after refresh. If she does, an accidental Match List exists—fix before Lessons 35–37 teach the request path. Also confirm `MNB-IT-ELDAP` / job IT packs still lack AWS_ADMIN and PRIV_BREAK (Lesson 26).

---

## How it works

Privileged objects are Bundles like any other—but with **no** Assignment Rule on the business role, requestable = Yes, and stricter operational controls. LCM later creates IdentityRequests; this lesson freezes objects and policy intent.

```
Dictionary / app entitlements
   AWS_ADMIN, PRIV_BREAK (critical)
        │
        ▼
IT:     MNB-IT-CloudAdmin / MNB-IT-BreakGlass   (Entitlements panel)
Business: MNB-Role-CloudAdmin / MNB-Role-BreakGlass
   requestable=YES, Assignment Rule=NONE, Required → matching IT
        │
        ├── Refresh ──► Amelia / job roles: no privileged business assign
        ├── LCM request (Lessons 35–37) ──► approvals ──► assign business role
        └── Monthly cert scope + same-day leaver revoke
```

| Control | CloudAdmin | BreakGlass |
| --- | --- | --- |
| Catalog stance | Privileged / not casual CRM neighbor | Emergency path only |
| Approvers | Manager + `christopher.hayes` (tech) | Tech Director + Security (`helen.ross`) |
| TTL | Standing with monthly re-justify | ≤8 hours, same-day revoke |
| Joiner | Never auto | Never auto |
| Leaver | Same calendar day | Same calendar day |

---

## Before you start

- [ ] Lesson 26 confirmed AWS_ADMIN not inside Developer/birthright **IT** packs
- [ ] AWS_ADMIN entitlement aggregatable from MNB-AWS-Cloud (or IT inventory)
- [ ] PRIV_BREAK present in dictionary (create managed attribute if missing)
- [ ] You know the Lesson 24 UI recipe: **Setup → Roles → Create New → Role**

### UI recipe (privileged — IT first)

| Step | Choice |
| --- | --- |
| Create | **Setup → Roles** → **Create New → Role** (not mining) |
| IT pack | Type **it** → **Entitlements → Add** (Simple or **Advanced View**) → critical ent only → Submit |
| Business role | Type **business** → ignore Entitlements warning → **Required Roles** → IT pack → **no** Assignment Rule → requestable **Yes** → Submit |

---

## Lab procedure

### Task 1 — Confirm privileged entitlements

You cannot package what does not exist as a managed attribute. Confirm critical labeling first.

1. **Applications → Entitlement Catalog** (or app entitlements) → verify **AWS_ADMIN** (critical).
2. Verify or create **PRIV_BREAK** with display name “Break-Glass Admin” and risk critical.
3. Record application owners: cloud platform owner; Security for break-glass.

**Expected result:** Both entitlements visible with critical risk labeling.

**If it fails:** Aggregate cloud app; add managed attribute manually from dictionary—do not skip PRIV_BREAK.

### Task 2 — Create CloudAdmin (`MNB-IT-CloudAdmin` + `MNB-Role-CloudAdmin`)

**2a — IT pack**

1. **Setup → Roles** → **Create New → Role**.
2. Name `MNB-IT-CloudAdmin`, Type **it**, Owner `spadmin` (lab; production: Technology / Cloud).
3. Description: `IT pack: AWS_ADMIN only. Privileged. Never Required by birthright or job packs.`
4. **Entitlements → Add** → **AWS_ADMIN** only → Submit profile → **Submit** role.

**2b — Business role (request-only)**

1. **Create New → Role** → Name `MNB-Role-CloudAdmin`, Type **business**.
2. Description: `Standing AWS account administration. Not birthright. Requires approved access request and monthly review.`
3. Ignore Entitlements warning. **Modify Required Roles** → add **`MNB-IT-CloudAdmin`** only.
4. **Assignment Rule:** leave **empty / none** (including no CLD01 Match List).
5. Mark **requestable = Yes** (Available in Access Request / equivalent).
6. Owner: Technology / Cloud platform. **Submit**.

**Expected result:** Business role requestable, Requires `MNB-IT-CloudAdmin`, composition = AWS_ADMIN on the IT pack, no auto-assign on refresh.

**If it fails:** Accidental Match List → delete it; refresh a CLD01 user and confirm no CloudAdmin assignment. Tried to put AWS_ADMIN on the business role → move it to the IT pack.

### Task 3 — Create BreakGlass (`MNB-IT-BreakGlass` + `MNB-Role-BreakGlass`)

**3a — IT pack**

1. **Create New → Role** → `MNB-IT-BreakGlass`, Type **it**.
2. Entitlements: **PRIV_BREAK** only.
3. Description: `IT pack: PRIV_BREAK only. Emergency. Never birthright.`
4. **Submit**.

**3b — Business role (request-only)**

1. **Create New → Role** → `MNB-Role-BreakGlass`, Type **business**.
2. Description: `Emergency privileged access only. Dual approval Technology Director + Security. Time-bound. Full audit trail required.`
3. **Required Roles** → `MNB-IT-BreakGlass`.
4. Assignment Rule: **none**. Requestable: **Yes**.
5. Owner: Security. **Submit**.

**Expected result:** BreakGlass business role is request-only; IT pack is PRIV_BREAK singleton.

### Task 4 — Birthright / job exclusion proof

Examiners sample “does privilege leak into birthright or job packs?” Prove it does not—at **both** layers.

1. Open `MNB-IT-ELDAP`, `MNB-IT-Developer`, `MNB-IT-CRM`, `MNB-IT-WireInit` — confirm no AWS_ADMIN / PRIV_BREAK.
2. Open `MNB-Birthright-Employee` and job **business** roles — confirm Required Roles do **not** list CloudAdmin/BreakGlass IT packs.
3. **Setup → Tasks** → Refresh with assign ON scoped to / including `amelia.brooks`.
4. Open Amelia → **Roles** — confirm she does **not** gain `MNB-Role-CloudAdmin` or `MNB-Role-BreakGlass`.

**Expected result:** Documented proof: IT packs clean; business Required lists clean; Amelia without privileged assignment.

### Task 5 — Approval expectations (design now, wire later)

1. Write approval matrix (applies to the **business** role request):

| Role | Approver 1 | Approver 2 | Notes |
| --- | --- | --- | --- |
| CloudAdmin | Line manager | Cloud/Tech owner (`christopher.hayes`) | No self-approval |
| BreakGlass | Technology Director | Security (`helen.ross`) | Emergency justification mandatory |

2. Note Lessons 36–37 will implement chains; this lesson freezes intent.

**Expected result:** Approval matrix in binder titled `MNB-Priv-Approval-Intent`.

### Task 6 — Certification frequency list

1. Add both **business** roles (`MNB-Role-CloudAdmin`, `MNB-Role-BreakGlass`) to `MNB-Cert-Scope-Privileged-Monthly`.
2. Contrast: standard job business roles quarterly (future campaigns).
3. Record owner of the monthly campaign (Security / IAM).
4. Note contractors with AWS_ADMIN (`raj.external`) belong on the weekly privileged subset (Lesson 32)—even before role assignment exists. Detection of `MNB-IT-CloudAdmin` (Lesson 27) may help find them; it is not approval.

**Expected result:** Scope list artifact with two **business** role names and frequency Monthly (+ contractor AWS weekly note).

### Task 7 — Privileged runbook

1. Write runbook bullets:
   - Joiner: never auto-assigned CloudAdmin/BreakGlass business roles
   - Mover: privileged access re-justified within 5 business days
   - Leaver: revoke same calendar day as HR termination (Lesson 31)
   - Break-glass: ticket ID + start/end time + MFA/PAM note (Lesson 37)
   - Contractor: mandatory end date; weekly review while AWS_ADMIN active
   - Composition: edit `MNB-IT-*` only under change control (Lesson 26)
2. Store as `MNB-Runbook-Privileged-Access`.

**Expected result:** One-page runbook suitable for ops handoff.

### Task 8 — Optional detect-only note

1. Decide whether `MNB-IT-CloudAdmin` should participate in **detection** (analytical) while assignment stays request-only on the business role.
2. Prefer: detection helps find AWS_ADMIN holders; **Assigned** CloudAdmin only via request.

**Expected result:** Explicit detect-vs-assign note referencing Lesson 27.

---

## Acceptance criteria

- [ ] `MNB-IT-CloudAdmin` / `MNB-Role-CloudAdmin` and `MNB-IT-BreakGlass` / `MNB-Role-BreakGlass` created (two-tier)
- [ ] Entitlements only on IT packs; business roles requestable with **no** Assignment Rule
- [ ] No birthright/job auto-assignment to privileged business roles
- [ ] Approval intent matrix documented
- [ ] Monthly privileged cert scope list updated (business role names)
- [ ] Privileged access runbook written

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| *Entitlements not supported* on CloudAdmin | Type = business (expected) | Put AWS_ADMIN on `MNB-IT-CloudAdmin`; Required Roles link |
| CLD01 users auto-get CloudAdmin | Accidental Match List on business role | Remove rule; refresh; verify |
| PRIV_BREAK missing | Not in app extract | Create managed attribute / stub entitlement for IT pack |
| Managers can approve own CloudAdmin | Approval design gap | Ban self-approval in matrix; enforce in Lesson 36 |
| Break-glass standing forever | No time-bound process | Add expiry/SLA to runbook; later LCM sunset |

---

## Training binder evidence

- Screenshots: both IT packs (Entitlements) and both business roles (Required + requestable, empty Assignment Rule)
- Proof: Amelia / birthright / job packs without privileged roles or Required links
- `MNB-Priv-Approval-Intent` matrix
- `MNB-Cert-Scope-Privileged-Monthly` list
- `MNB-Runbook-Privileged-Access`

**Control owner:** Security (BreakGlass) + Technology (CloudAdmin) + IAM (IIQ objects)  
**SLA:** Leaver privileged revoke same day; break-glass dual approval before use

---

## Knowledge check

1. Who approves break-glass (intent)?
2. What is the cert frequency for privileged roles?
3. Are these roles birthright eligible?
4. Which object holds AWS_ADMIN—`MNB-Role-CloudAdmin` or `MNB-IT-CloudAdmin`?
5. What happens on joiner day regarding these roles?
6. How do standing CloudAdmin and BreakGlass differ on TTL?

### Answers

1. Technology Director **and** Security (dual approval).
2. Monthly (at minimum for standing privileged).
3. No.
4. **`MNB-IT-CloudAdmin`** (business role only Requires it and is requestable).
5. Joiners never auto-receive them—request/approval only when justified.
6. CloudAdmin may be standing with monthly cert; BreakGlass is emergency time-boxed (≤8h lab standard) with same-day revoke.

---

## Further reading

- [SailPoint IdentityIQ — Role Modeling](https://documentation.sailpoint.com/identityiq/help/roles_groups_and_populations/roles/role_modeling/index.html) — requestable business roles, Required IT packs, no auto-assignment.
- [SailPoint Community](https://community.sailpoint.com/) — search “break glass” / “privileged role certification” for monthly campaign patterns.
- [NIST SP 800-53 AC-6](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — least privilege for standing admin access.
- [NIST SP 800-53 AC-2(2)/AC-2(3)](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — automated audit and temporary accounts—language that maps to break-glass TTL.
- [CIS Controls v8 — Control 5 & 6](https://www.cisecurity.org/controls) — admin account inventory and access control management for privileged roles.

---

## Stretch lab

- Draft MFA / PAM requirement note attached to both **business** roles (“IIQ role is necessary but not sufficient”).
- Propose automatic sunset: BreakGlass **business** assignment expires in 8 hours unless extended.
- Build population of AWS_ADMIN account holders for the first monthly privileged campaign dry-run (include `raj.external`); optionally use Detected `MNB-IT-CloudAdmin` as a hunt aid.

---

## Summary

- Privileged access is still two-tier: IT holds the critical entitlement; business is request-only with no Match List.
- CloudAdmin and BreakGlass stay out of birthright and job automation at both layers.
- Approval intent and same-day leaver revoke are control commitments—not optional polish.

---

**Previous:** [Lesson 27 — Role Detection vs Assignment](27-role-detection-vs-assignment.md)  
**Next:** [Lesson 29 — Joiner Lifecycle](29-joiner-lifecycle.md)
