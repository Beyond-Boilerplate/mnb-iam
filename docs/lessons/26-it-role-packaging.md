# Lesson 26 — IT Role Packaging & Least Privilege

**Level:** Intermediate  
**Track:** Roles  
**Time:** 45–60 minutes  
**Prereq:** Lesson 25 job roles created  

**Lab data:**
- Role catalog from Lessons 23–25
- `~/iiq-lab-data/reference/entitlement-dictionary.csv`
- `~/iiq-lab-data/reference/sod-matrix.csv`

---

## Learning objectives

You will be able to:

- Audit each Meridian role’s entitlements against least-privilege justification
- Split toxic or convenience bundles (especially anything pairing AWS_ADMIN with developer packs)
- Keep **CloudAdmin** as a standalone requestable privileged role (built fully in Lesson 28)
- Write business-readable role descriptions managers can certify
- Obtain a fictional Risk sign-off line for composition changes
- Reject “add AWS to Developer so SREs stop filing tickets” with a documented counter-proposal

---

## Why this matters

**Business.** Packaging reduces request friction but can smuggle privilege. “Developers also need cloud admin sometimes” is how SoD and least privilege die—and how `diego.hayes` quietly inherits production keys he only needs twice a year. Every entitlement in a role needs a reason tied to the job—not convenience.

**Control / audit.** Role composition changes are change-controlled. Examiners sample roles for toxic combinations (see `sod-matrix.csv`): WIRE_INIT+WIRE_APPR, Developer+AWS_ADMIN, birthright with SAP_FI. Evidence = composition table + justification + Risk approval. Silent XML edits fail exams.

---

## Concepts

### Least privilege as a packaging rule

**Least privilege:** Grant the minimum entitlements required for the role’s stated job function.

**Toxic bundle:** A role that encodes an SoD conflict or privilege far beyond the job (e.g. DWRP + AWS_ADMIN + SAP_FI in one pack).

```
BAD:  MNB-Role-Developer = {DWRP, ODS, AWS_ADMIN}
GOOD: MNB-Role-Developer = {DWRP, ODS}
      MNB-Role-CloudAdmin = {AWS_ADMIN}   ← request-only, separate
```

| Role | Allowed ents (v0) | Forbidden in same role |
| --- | --- | --- |
| Birthright Employee | ELDAP | Any critical payment/cloud/finance |
| Developer | DWRP, ODS | AWS_ADMIN, SAP_FI, WIRE_* |
| RelationshipManager | CRM (± ODS) | WIRE_INIT, AWS_ADMIN |
| WireInitiator | WIRE_INIT | WIRE_APPR |
| CloudAdmin | AWS_ADMIN | DWRP “for convenience”, SAP_FI |

### The wrong way under exam

The naive approach: Technology opens a ticket—“add AWS_ADMIN to Developer, SREs are drowning.” IAM “helps” overnight. Next quarter, Risk certifies Developer as a business pack while half the engineers hold standing cloud admin. Dual control on **composition** exists so that path cannot happen quietly.

### Descriptions are part of the control

Managers certify what they understand. “Bundle for DWRP/ODS managed attrs” fails UAT. “Tools for building and supporting internal applications—not cloud account admin, not wire money movement” succeeds. Role descriptions are examiner-facing prose, not developer comments.

---

## How it works

Composition review is a governance loop outside the refresh engine: inventory → SoD scan → remediate → describe → sign off → change-control.

```
Role Bundles in IIQ
        │
        ▼
Composition inventory (Role | Ents | Justification)
        │
        ▼
SoD / privilege scan (sod-matrix.csv + dictionary risk)
        │
   ┌────┴────┐
   Clean     Findings ──► remove toxic ents / split roles
   │
   ▼
Business descriptions + requestable flags
        │
        ▼
Risk sign-off + change-control note
```

| Artifact | Owner | Cadence |
| --- | --- | --- |
| Composition table | IAM Engineering | Every catalog change |
| SoD scan results | IAM + Risk | Before go-live; quarterly review |
| Decision log (reject/accept packs) | Risk | Per proposal |
| Change ticket | IAM implementer | Per composition edit |

---

## Before you start

- [ ] Roles from Lessons 24–25 exist in IIQ
- [ ] `~/iiq-lab-data/reference/sod-matrix.csv` and entitlement dictionary available
- [ ] Binder section `MNB-Role-Composition-Review`
- [ ] Do not implement full privileged roles yet—design the split now (Lesson 28 creates them)

---

## Lab procedure

### Task 1 — Inventory role compositions

You cannot defend what you have not listed. Start with a complete table.

1. Open each `MNB-Birthright-*` and `MNB-Role-*` object.
2. Build table: Role | Entitlements | Job rule | Justification (one line each entitlement).
3. Flag any entitlement without a justification.

**Expected result:** Complete composition table for all roles created so far.

**If it fails:** Export Bundle XML from Debug and list `<Profile>`/`<References>` equivalents.

### Task 2 — SoD and privilege scan

1. Open `sod-matrix.csv`.
2. For each role, check whether any SoD pair is co-packaged.
3. Check critical entitlements (WIRE_*, AWS_ADMIN, SAP_FI, CORE, PRIV_BREAK) for inappropriate homes.
4. Mark findings: Clean / Remediations required.

**Expected result:** WireInitiator contains only WIRE_INIT; Developer lacks AWS_ADMIN; birthright lacks criticals.

**If it fails:** Remediations become Task 3—do not leave findings untracked.

### Task 3 — Split CloudAdmin from developer convenience

Standing cloud admin is privileged access, not a developer amenity—even for CLD01/SRE01.

1. If any role contains AWS_ADMIN beside DWRP/ODS, **remove** AWS_ADMIN now.
2. Record future object: `MNB-Role-CloudAdmin` (Lesson 28) as the only AWS_ADMIN pack.
3. Write rationale: “Cloud administration is privileged standing access; not a developer birthright.”

**Expected result:** Zero job roles contain AWS_ADMIN after this lesson.

### Task 4 — Business descriptions pass

1. Rewrite each role description so a branch manager understands it.
2. Bad: “Bundle for DWRP/ODS managed attrs.”
3. Good: “Tools for building and supporting internal applications and reporting—not cloud account admin, not wire money movement.”
4. Update IIQ role descriptions accordingly.

**Expected result:** Descriptions readable in a certification UI without IAM jargon overload.

### Task 5 — Requestable vs automatic flags

1. Birthright: not requestable.
2. Job roles (Dev/RM/WireInitiator): typically automatic via assignment—optionally not requestable to avoid duplicates; document Meridian choice.
3. Privileged (CloudAdmin/BreakGlass): requestable later; never automatic.
4. Optional add-ons (extra ODS): requestable candidates.

**Expected result:** Flag matrix Role | Automatic | Requestable | Notes.

### Task 6 — Peer review (Risk sign-off)

1. Add a binder line: “Reviewed by Risk (lab): ________ Date: ________.”
2. List remediations completed (AWS split, description updates).
3. Attach composition table as the review artifact.

**Expected result:** Sign-off line present (instructor or peer can initial).

### Task 7 — Change control note

1. Write: composition edits require ticket + IAM implementer + Risk approver.
2. Ban “quick add entitlement to role” in production without review.

**Expected result:** One-paragraph change-control statement in binder.

### Task 8 — Packaging decision log (worked example)

Walk a real pressure scenario so the reject path is muscle memory.

1. Proposal: “Add AWS_ADMIN to `MNB-Role-Developer` so SREs stop filing tickets.”
2. Record decision: **Reject** — violates least privilege and Lesson 28 privileged model.
3. Counter-proposal: CLD01/SRE01 users may **request** `MNB-Role-CloudAdmin` with manager + tech owner approval; standing membership still monthly-certified.
4. Log the decision with date, requester (fictional), and Risk outcome.

**Expected result:** Decision log entry showing a rejected toxic pack and the approved request path instead.

**If it fails:** If CloudAdmin role is not created yet, still log the reject and point to Lesson 28 for object creation.

### Task 9 — Entitlement justification deep-dive

1. Pick `MNB-Role-WireInitiator` and write a three-line justification:
   - Why WIRE_INIT belongs (job WIR01 initiates payments)
   - Why WIRE_APPR must stay out (dual control with `marcus.approve`)
   - Why ELDAP is not duplicated here (belongs in birthright)
2. Repeat in shorter form for Developer (DWRP vs AWS_ADMIN).

**Expected result:** Two justification blurbs ready to paste into role documentation / ADR appendix.

---

## Acceptance criteria

- [ ] Composition table completed for all current MNB roles
- [ ] No toxic SoD pair packaged inside a single role
- [ ] AWS_ADMIN removed from Developer / birthright / RM / WireInitiator
- [ ] Business descriptions updated
- [ ] Risk sign-off line, change-control note, and packaging decision log recorded

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Cloud engineers complain | Confusing job CLD01 with standing AWS_ADMIN | Allow request path (Lesson 28/35), not auto pack |
| Role “needs” SAP for testing | Convenience pressure | Use non-prod roles / separate lab policy—never prod SAP_FI in Dev role |
| Descriptions still technical | Wrote for engineers | Pilot with a non-IAM reader |
| Duplicate access via role + direct ent | Mixed model | Prefer role assignment; remediate direct critical ents in certs |

---

## Training binder evidence

- `MNB-Role-Composition-Review` table
- Before/after note for any AWS_ADMIN removal
- Updated role description screenshots
- Requestable/automatic flag matrix
- Risk sign-off line + change-control paragraph + decision log (rejected Developer+AWS_ADMIN)

**Control owner:** IAM Engineering (implement) + Risk (approve)  
**SLA:** Critical composition defects (toxic packs) remediated within 2 business days of discovery

---

## Knowledge check

1. Why split CloudAdmin from Developer?
2. What belongs in a role description?
3. Who signs role composition for Meridian?
4. Name one toxic packaging example from Meridian’s SoD thinking.
5. Should birthright be requestable?
6. What is the approved path when SREs need AWS_ADMIN?

### Answers

1. AWS_ADMIN is privileged standing access; bundling it into developer convenience violates least privilege and SoD intent.
2. Business purpose, scope boundary (“does not include…”), and audience a manager understands.
3. Risk (approve) with IAM Engineering (draft/implement)—dual control on composition changes.
4. Examples: WIRE_INIT+WIRE_APPR in one role; SAP_FI+AWS_ADMIN; Developer+AWS_ADMIN.
5. No—automatic only.
6. Request `MNB-Role-CloudAdmin` with manager + tech owner approval; certify monthly—do not auto-pack into Developer.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “role profiles” and “required entitlements” for composition mechanics.
- [SailPoint Community](https://community.sailpoint.com/) — search “least privilege roles” for packaging debates and toxic bundle war stories.
- [NIST SP 800-53 AC-6](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — least privilege; the control behind splitting CloudAdmin.
- [NIST SP 800-53 AC-5](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — separation of duties applied to role composition.
- [OWASP Access Control Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Access_Control_Cheat_Sheet.html) — practical least-privilege framing useful when writing role justifications.

---

## Stretch lab

- Introduce **required** vs **optional** entitlements concept within a role (if IIQ edition supports) or via two roles: core Dev + optional ODS add-on.
- Map each critical entitlement to a maximum packaging rule (solo privileged role vs job pack).
- Draft a quarterly role composition review checklist for production ops.

---

## Summary

- Least privilege means every entitlement in a role has a job justification.
- Split CloudAdmin; never ship toxic convenience bundles.
- Composition is a controlled artifact with Risk sign-off—not a silent XML tweak.

---

**Previous:** [Lesson 25 — Department & Job-Based Roles](25-dept-job-roles.md)  
**Next:** [Lesson 27 — Role Detection vs Assignment](27-role-detection-vs-assignment.md)
