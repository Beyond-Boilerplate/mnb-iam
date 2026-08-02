# Lesson 26 — IT Role Packaging & Least Privilege

**Level:** Intermediate  
**Track:** Roles  
**Time:** 45–60 minutes  
**Prereq:** Lesson 25 job roles created (IT packs + business roles)  

**Lab data:**
- Role catalog from Lessons 23–25
- `~/iiq-lab-data/reference/entitlement-dictionary.csv`
- `~/iiq-lab-data/reference/sod-matrix.csv`

---

> **Verify:** Lab lesson — remediate IT pack composition (remove toxic ents, update descriptions). Academy **Verify now** checks `MNB-IT-ELDAP` / `MNB-IT-Developer` / `MNB-IT-WireInit` and related roles.

## Learning objectives

You will be able to:

- Inventory Meridian’s **IT** packs (where entitlements live) and the **business** roles that Require them
- Audit each IT pack against least-privilege justification—and catch toxic Required Role links
- Split toxic or convenience bundles (especially anything pairing AWS_ADMIN with developer packs)
- Keep **CloudAdmin** as a standalone requestable privileged role (built fully in Lesson 28)
- Write business-readable descriptions managers can certify
- Obtain a fictional Risk sign-off line for composition changes

---

## Why this matters

**Business.** Packaging reduces request friction but can smuggle privilege. “Developers also need cloud admin sometimes” is how SoD and least privilege die—and how `diego.hayes` quietly inherits production keys he only needs twice a year. Every entitlement in an **IT** role needs a reason tied to the job—not convenience.

**Control / audit.** Role composition changes are change-controlled. Examiners sample **IT** packs for toxic combinations (see `sod-matrix.csv`) and confirm **business** roles do not sneak privilege via Required Roles. Evidence = composition table + justification + Risk approval. Silent XML edits fail exams.

---

## Concepts

### IT packs are the composition control surface

Lessons 24–25 put entitlements on type **it** and assignment on type **business**. Least-privilege review therefore starts on **IT** objects—and then walks each business role’s **Required Roles** list so privilege cannot hide one layer up.

```
BAD:  MNB-IT-Developer = {DWRP, ODS, AWS_ADMIN}
      MNB-Role-Developer ──Requires──► MNB-IT-Developer

GOOD: MNB-IT-Developer = {DWRP, ODS}
      MNB-IT-CloudAdmin = {AWS_ADMIN}     ← request-only business role in Lesson 28
      MNB-Role-Developer ──Requires──► MNB-IT-Developer   (only)
```

| IT pack (v0) | Allowed ents | Forbidden in same IT pack | Required by (business) |
| --- | --- | --- | --- |
| `MNB-IT-ELDAP` | ELDAP | Any critical payment/cloud/finance | `MNB-Birthright-Employee` |
| `MNB-IT-Developer` | DWRP, ODS | AWS_ADMIN, SAP_FI, WIRE_* | `MNB-Role-Developer` |
| `MNB-IT-CRM` | CRM (± ODS) | WIRE_INIT, AWS_ADMIN | `MNB-Role-RelationshipManager` |
| `MNB-IT-WireInit` | WIRE_INIT | WIRE_APPR | `MNB-Role-WireInitiator` |
| `MNB-IT-CloudAdmin` (Lesson 28) | AWS_ADMIN | DWRP “for convenience”, SAP_FI | Future `MNB-Role-CloudAdmin` |

### The wrong way under exam

The naive approach: Technology opens a ticket—“add AWS_ADMIN to Developer, SREs are drowning.” IAM edits **`MNB-IT-Developer`** overnight (or worse, tries to paste AWS onto the business role and hits the Entitlements warning). Next quarter, Risk certifies Developer as a desk pack while half the engineers hold standing cloud admin. Dual control on **composition** exists so that path cannot happen quietly.

### Descriptions are part of the control

Managers certify **business** role names and descriptions. Engineers maintain **IT** pack descriptions that say exactly which entitlements are inside. Both must stay human-readable: “Tools for building and supporting internal applications—not cloud account admin, not wire money movement.”

---

## How it works

Composition review is a governance loop outside the refresh engine: inventory IT packs → check business Required links → SoD scan → remediate → describe → sign off → change-control.

```
Setup → Roles (Role Viewer)
        │
        ├── IT Bundles (Entitlements / profiles)
        └── Business Bundles (Required Roles + Assignment)
        │
        ▼
Composition inventory (Business | Required IT | Ents | Justification)
        │
        ▼
SoD / privilege scan (sod-matrix.csv + dictionary risk)
    ── Clean / Findings ──► fix IT pack or break Required link
        │
        ▼
Descriptions + requestable flags + Risk sign-off
```

| Artifact | Owner | Cadence |
| --- | --- | --- |
| Composition table | IAM Engineering | Every catalog change |
| SoD scan results | IAM + Risk | Before go-live; quarterly review |
| Decision log (reject/accept packs) | Risk | Per proposal |
| Change ticket | IAM implementer | Per IT composition edit |

---

## Before you start

- [ ] Roles from Lessons 24–25 exist in IIQ (IT + business pairs)
- [ ] `~/iiq-lab-data/reference/sod-matrix.csv` and entitlement dictionary available
- [ ] Binder section `MNB-Role-Composition-Review`
- [ ] Do not implement full privileged roles yet—design the split now (Lesson 28 creates them)

### Where to edit compositions (IIQ 8.x)

| Goal | Path |
| --- | --- |
| Open catalog | **Setup → Roles** → **Role Viewer** |
| Edit IT entitlements | Select `MNB-IT-*` → edit → **Entitlements → Add** / remove (Simple or **Advanced View**) → **Submit** |
| Edit who gets a pack | Select `MNB-Role-*` / birthright → **Required Roles** and **Assignment Rule** only — ignore Entitlements warning |
| Do **not** | Use Business/IT Role Mining to “fix” composition — mining is out of scope |

---

## Lab procedure

### Task 1 — Inventory role compositions (two columns that matter)

You cannot defend what you have not listed. Inventory **both** layers.

1. **Setup → Roles** → open each `MNB-IT-*` from Lessons 24–25.
2. For each IT pack, list: IT role | Entitlements | Justification (one line each entitlement).
3. Open each `MNB-Birthright-*` and `MNB-Role-*` business role.
4. Extend the table: Business role | Required IT role(s) | Job / birthright rule | Notes.
5. Flag any entitlement without a justification, or any business role with an empty Required Roles list.

**Expected result:** Complete composition table: Business → Required IT → Entitlements for all roles so far.

**If it fails:** Debug → Object Browser → `Bundle` → read `<Profile>` on IT roles and `<Requirements>` on business roles.

### Task 2 — SoD and privilege scan

1. Open `sod-matrix.csv`.
2. For each **IT** pack, check whether any SoD pair is co-packaged.
3. For each **business** role, confirm Required Roles do not pull two sides of a dual-control pair (e.g. WireInit + WireAppr).
4. Check critical entitlements (WIRE_*, AWS_ADMIN, SAP_FI, CORE, PRIV_BREAK) for inappropriate homes.
5. Mark findings: Clean / Remediations required.

**Expected result:** `MNB-IT-WireInit` = WIRE_INIT only; `MNB-IT-Developer` lacks AWS_ADMIN; `MNB-IT-ELDAP` lacks criticals.

**If it fails:** Remediations become Task 3—do not leave findings untracked.

### Task 3 — Split CloudAdmin from developer convenience

Standing cloud admin is privileged access, not a developer amenity—even for CLD01/SRE01.

1. Open **`MNB-IT-Developer`** (not the business role).
2. If **AWS_ADMIN** appears under Entitlements, **remove** it → **Submit**.
3. Confirm `MNB-Role-Developer` Required Roles still lists only `MNB-IT-Developer` (no shadow cloud IT pack).
4. Record future objects: `MNB-IT-CloudAdmin` + `MNB-Role-CloudAdmin` (Lesson 28) as the only AWS_ADMIN path.
5. Write rationale: “Cloud administration is privileged standing access; not a developer birthright.”

**Expected result:** Zero job / birthright IT packs contain AWS_ADMIN after this lesson.

### Task 4 — Business descriptions pass

1. Rewrite each **business** role description so a branch manager understands it.
2. Bad: “Bundle for DWRP/ODS managed attrs.”
3. Good: “Tools for building and supporting internal applications and reporting—not cloud account admin, not wire money movement.”
4. Update IT pack descriptions to name the entitlements plainly (e.g. “DWRP + ODS only”).
5. **Setup → Roles** → edit each role → update Description → **Submit**.

**Expected result:** Descriptions readable in a certification UI without IAM jargon overload.

### Task 5 — Requestable vs automatic flags

Flags live mainly on **business** roles (what users see in LCM). IT packs stay non-requestable building blocks.

1. Birthright business role: not requestable.
2. Job business roles (Dev/RM/WireInitiator): automatic via assignment—typically not requestable (avoid duplicates); document Meridian choice.
3. Privileged (CloudAdmin/BreakGlass): requestable later; never automatic; never Required by a job pack.
4. Optional add-ons (extra ODS IT pack): requestable **business** candidates that Require a small IT pack.

**Expected result:** Flag matrix Business role | Automatic | Requestable | Required IT | Notes.

### Task 6 — Peer review (Risk sign-off)

1. Add a binder line: “Reviewed by Risk (lab): ________ Date: ________.”
2. List remediations completed (AWS split on IT pack, description updates).
3. Attach the two-layer composition table as the review artifact.

**Expected result:** Sign-off line present (instructor or peer can initial).

### Task 7 — Change control note

1. Write: IT composition edits require ticket + IAM implementer + Risk approver.
2. Ban “quick Add entitlement on `MNB-IT-*`” in production without review.
3. Ban “bypass IT pack—stuff ents on business role” (unsupported on stock types anyway).

**Expected result:** One-paragraph change-control statement in binder.

### Task 8 — Packaging decision log (worked example)

Walk a real pressure scenario so the reject path is muscle memory.

1. Proposal: “Add AWS_ADMIN to `MNB-IT-Developer` (or to `MNB-Role-Developer`) so SREs stop filing tickets.”
2. Record decision: **Reject** — violates least privilege and Lesson 28 privileged model.
3. Counter-proposal: CLD01/SRE01 users may **request** `MNB-Role-CloudAdmin` (→ `MNB-IT-CloudAdmin`) with manager + tech owner approval; standing membership still monthly-certified.
4. Log the decision with date, requester (fictional), and Risk outcome.

**Expected result:** Decision log entry showing a rejected toxic pack and the approved request path instead.

**If it fails:** If CloudAdmin objects are not created yet, still log the reject and point to Lesson 28.

### Task 9 — Entitlement justification deep-dive

1. Pick `MNB-IT-WireInit` / `MNB-Role-WireInitiator` and write a three-line justification:
   - Why WIRE_INIT belongs on the IT pack (job WIR01 initiates payments)
   - Why WIRE_APPR must stay out of that IT pack and off that business role’s Required list (dual control with `marcus.approve`)
   - Why ELDAP is not duplicated here (belongs in `MNB-IT-ELDAP` / birthright)
2. Repeat in shorter form for Developer (DWRP vs AWS_ADMIN on `MNB-IT-Developer`).

**Expected result:** Two justification blurbs ready to paste into role documentation / ADR appendix.

---

## Acceptance criteria

- [ ] Composition table completed: Business → Required IT → Entitlements for all current MNB roles
- [ ] No toxic SoD pair packaged inside a single **IT** role or via one business role’s Required list
- [ ] AWS_ADMIN removed from Developer / birthright / RM / WireInitiator IT packs
- [ ] Business (and IT) descriptions updated via **Setup → Roles**
- [ ] Risk sign-off line, change-control note, and packaging decision log recorded

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Editing business role Entitlements | Wrong layer | Edit `MNB-IT-*` Entitlements; business uses Required Roles only |
| Cloud engineers complain | Confusing job CLD01 with standing AWS_ADMIN | Allow request path (Lesson 28/35), not auto pack |
| Role “needs” SAP for testing | Convenience pressure | Separate non-prod IT pack—never prod SAP_FI in Dev |
| Descriptions still technical | Wrote for engineers | Pilot with a non-IAM reader |
| Duplicate access via role + direct ent | Mixed model | Prefer role assignment; remediate direct critical ents in certs |

---

## Training binder evidence

- `MNB-Role-Composition-Review` table (two-layer)
- Before/after screenshot of any AWS_ADMIN removal from `MNB-IT-Developer`
- Updated role description screenshots (business + IT)
- Requestable/automatic flag matrix
- Risk sign-off line + change-control paragraph + decision log (rejected Developer+AWS_ADMIN)

**Control owner:** IAM Engineering (implement) + Risk (approve)  
**SLA:** Critical composition defects (toxic packs) remediated within 2 business days of discovery

---

## Knowledge check

1. Why split CloudAdmin from Developer—and which object would you edit to remove a smuggled AWS_ADMIN today?
2. What belongs in a **business** role description vs an **IT** pack description?
3. Who signs role composition for Meridian?
4. Name one toxic packaging example from Meridian’s SoD thinking.
5. Should birthright be requestable?
6. What is the approved path when SREs need AWS_ADMIN?

### Answers

1. AWS_ADMIN is privileged standing access; bundling it into developer convenience violates least privilege. Remove it from **`MNB-IT-Developer`** (Entitlements), not from the business role’s unsupported Entitlements panel.
2. Business: desk language and boundaries for managers/certs. IT: exact entitlement list and technical scope.
3. Risk (approve) with IAM Engineering (draft/implement)—dual control on composition changes.
4. Examples: WIRE_INIT+WIRE_APPR in one IT pack; SAP_FI+AWS_ADMIN; Developer IT pack + AWS_ADMIN.
5. No—automatic only.
6. Request `MNB-Role-CloudAdmin` (→ dedicated IT pack) with manager + tech owner approval; certify monthly—do not auto-pack into Developer.

---

## Further reading

- [SailPoint IdentityIQ — Role Modeling](https://documentation.sailpoint.com/identityiq/help/roles_groups_and_populations/roles/role_modeling/index.html) — IT vs business types, profiles/entitlements, Required Roles.
- [SailPoint Community](https://community.sailpoint.com/) — search “least privilege roles” for packaging debates and toxic bundle war stories.
- [NIST SP 800-53 AC-6](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — least privilege; the control behind splitting CloudAdmin.
- [NIST SP 800-53 AC-5](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — separation of duties applied to role composition.
- [OWASP Access Control Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Access_Control_Cheat_Sheet.html) — practical least-privilege framing useful when writing role justifications.

---

## Stretch lab

- Introduce **required** vs **permitted** IT roles on a business role (core Dev Required; optional ODS Permitted) if your edition supports Permitted Roles cleanly.
- Map each critical entitlement to a maximum packaging rule (solo privileged IT pack vs job IT pack).
- Draft a quarterly role composition review checklist for production ops (always open `MNB-IT-*` first).

---

## Summary

- Least privilege is enforced on **IT** packs; business roles only choose who and which IT packs are Required.
- Split CloudAdmin; never ship toxic convenience bundles on `MNB-IT-Developer`.
- Composition is a controlled artifact with Risk sign-off—not a silent XML tweak.

---

**Previous:** [Lesson 25 — Department & Job-Based Roles](25-dept-job-roles.md)  
**Next:** [Lesson 27 — Role Detection vs Assignment](27-role-detection-vs-assignment.md)
