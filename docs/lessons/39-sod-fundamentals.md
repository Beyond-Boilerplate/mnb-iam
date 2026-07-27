# Lesson 39 — SoD Fundamentals for Banking

**Level:** Intermediate  
**Track:** Policies  
**Time:** 60–75 minutes  
**Prereq:** Applications and entitlements onboarded (esp. Wire, SAP, AWS); Lesson 38 helpful for evidence habits  

**Lab data:**
- `lab-data/reference/sod-matrix.csv` → `~/iiq-lab-data/reference/sod-matrix.csv`
- Implement first: `WIRE_INIT`+`WIRE_APPR`, `SAP_FI`+`AWS_ADMIN`
- Policy names: `MNB-SOD-Wire-DualControl`, `MNB-SOD-Finance-Cloud`
- Expected violator for finance-cloud: `jordan.reed` (if still entitled)

---

## Learning objectives

You will be able to:

1. Read and explain every pair in Meridian’s `sod-matrix.csv` in bank language.
2. Implement entitlement SoD policies `MNB-SOD-Wire-DualControl` and `MNB-SOD-Finance-Cloud`.
3. Write business rationales Risk will accept (not only technical codes).
4. Run **Refresh MNB Identities** with policy checking and observe violations.
5. Identify which lab persona violates finance-cloud SoD.
6. State when SoD policies evaluate in IdentityIQ.

---

## Why this matters

**Business.** Separation of duties is how banks prevent one person from moving money alone or bypassing finance controls via cloud admin. If `priya.wire` also held `WIRE_APPR`, she could initiate and approve her own wires. If `jordan.reed` keeps `SAP_FI` and `AWS_ADMIN`, he can change the books and erase the trail.

**Control / audit.** Policies make toxic combinations visible and actionable. Mitigation is not ignorance — exceptions need owners and expirations (Lesson 41). Control owner: Risk (`anthony.powell` / CRO org) with IAM tooling ownership. Examiner question: *Show the SoD matrix, the IIQ policies, and open violations.*

---

## Concepts

### What SoD means in IdentityIQ

A **Separation of Duties (SoD) policy** declares two entitlement (or role) sets that must not coexist on one identity. When both are present, IIQ creates a **PolicyViolation** — a finding, not a silent flag.

Meridian’s business source of truth is `sod-matrix.csv`. IIQ policies are the enforceable projection of that matrix. Never invent pairs in IIQ that Risk has not approved in the matrix.

### Meridian SoD matrix (lab)

| Entitlement A | Entitlement B | Business rationale | Lab watch persona |
| --- | --- | --- | --- |
| `WIRE_INIT` | `WIRE_APPR` | Payment dual control — initiate vs approve | `priya.wire` / `marcus.approve` (clean split) |
| `SAP_FI` | `AWS_ADMIN` | Finance system of record + cloud bypass | `jordan.reed` (**violation**) |
| `IBSI` | `ECOM` | Digital banking support + channel promotion | `kai.nguyen` (stretch) |
| `GL_POST` | `SOX_VIEW` | Post journals and attest own controls | Finance stretch |
| `CORE` | `AWS_ADMIN` | Core ops + infrastructure escape hatch | Ops stretch |
| `ACH_OPS` | `WIRE_INIT` | Cross-rail payment initiation concentration | `priya.wire` holds both — risk discussion |

### Policy objects to create now

| Policy name | Pair | Type |
| --- | --- | --- |
| `MNB-SOD-Wire-DualControl` | `WIRE_INIT` + `WIRE_APPR` | Entitlement SoD |
| `MNB-SOD-Finance-Cloud` | `SAP_FI` + `AWS_ADMIN` | Entitlement SoD |

### Clean vs dirty personas

| Persona | Entitlements | Wire SoD | Finance-cloud SoD |
| --- | --- | --- | --- |
| `priya.wire` | `WIRE_INIT` (+ `ACH_OPS`) | Clean vs `WIRE_APPR` | N/A |
| `marcus.approve` | `WIRE_APPR` | Clean vs `WIRE_INIT` | N/A |
| `jordan.reed` | `SAP_FI` + `AWS_ADMIN` | N/A | **Violation** |
| `kai.nguyen` | `IBSI` + `ECOM` (if present) | N/A | Digital SoD stretch |

The wrong way: delete a policy because violations are noisy. That hides risk. Mitigate or revoke (Lesson 41).

---

## How it works

```text
sod-matrix.csv (business source of truth)
        │
        ▼
IIQ Policy objects (MNB-SOD-*)
        │
        ▼
Refresh MNB Identities (policy checking enabled)
   or continuous / policy scan task if configured
        │
        ▼
PolicyViolation objects + work items / reports
        │
        ├── Wire dual-control: expect clean Priya/Marcus
        └── Finance-cloud: expect jordan.reed (if ents present)
```

| Operation | Where it happens | What you see |
| --- | --- | --- |
| Define conflict | Policy editor left/right sets | `MNB-SOD-*` enabled |
| Evaluate | Refresh with “check policies” | Violations created/updated |
| Triage | Policy Violations UI | Open findings by identity |
| Act | Lesson 40–41 | Revoke or mitigate with expiry |

**IIQ terms:** *Policy* defines conflicting entitlements/roles. *PolicyViolation* is the finding on an identity. Evaluation commonly runs during identity refresh with “check policies” (or equivalent) enabled — confirm your task options.

---

## Before you start

- [ ] IIQ up; policy editor accessible (`spadmin`).
- [ ] Wire, SAP, AWS entitlements exist as managed attributes / account groups.
- [ ] `~/iiq-lab-data/reference/sod-matrix.csv` present.
- [ ] Refresh task `Refresh MNB Identities` exists.
- [ ] Note Jordan may have been partially disabled in Lesson 31 — restore entitlements in lab files if you need a live violation demo, or use historical evidence.

---

## Lab procedure

### Task 1 — Read the SoD matrix end-to-end

Risk will not accept “toxic combo” slang. Translate every row into language a Treasury or Finance VP understands.

1. Open `~/iiq-lab-data/reference/sod-matrix.csv`.
2. For each row, write one sentence a Treasury or Finance VP would understand.
3. Mark the two pairs you will implement first: wire dual control and finance-cloud.
4. Flag stretch pairs: `IBSI`+`ECOM` (`kai.nguyen`), `ACH_OPS`+`WIRE_INIT` (Priya holds both — risk discussion).

**Expected result:** Annotated matrix notes with business language for all six pairs.

**If it fails:** Re-copy `lab-data/reference` to `~/iiq-lab-data/reference/`.

### Task 2 — Write rationales for the two policies

Paste-ready rationales belong in the policy description — examiners read them.

1. Draft:

```text
MNB-SOD-Wire-DualControl
Rationale: No single identity may both create and approve wire instructions.
Compensating control if exception: dual review outside system + 30-day max (Lesson 40/41).

MNB-SOD-Finance-Cloud
Rationale: SAP Finance privilege combined with AWS Admin enables record change plus
infrastructure bypass/evidence destruction. Forbidden without CRO-approved mitigation.
```

2. Get “Risk tone” right — avoid only “toxic combo” slang.

**Expected result:** Rationale paragraphs ready to paste into policy descriptions.

### Task 3 — Create `MNB-SOD-Wire-DualControl`

This policy encodes the Priya/Marcus staffing model as an enforceable rule.

1. Navigate to **Setup → Policies** (or equivalent Policies menu).
2. Create new **SOD / Separation of Duties** policy (entitlement conflict).
3. Name: `MNB-SOD-Wire-DualControl`.
4. Add left set: `WIRE_INIT`; right set: `WIRE_APPR` (applications = Wire Portal / IT inventory — match how entitlements are stored).
5. Paste business rationale into description.
6. Set severity high/critical per lab options.
7. Save / enable policy.

**Expected result:** Policy object exists and lists the wire initiate/approve conflict.

**If it fails:** Confirm entitlement names exactly match aggregated values; use role SOD only if you packaged wire into roles.

### Task 4 — Create `MNB-SOD-Finance-Cloud`

Jordan’s toxic pair becomes a first-class finding when this policy is live.

1. Create second policy `MNB-SOD-Finance-Cloud`.
2. Conflict: `SAP_FI` vs `AWS_ADMIN`.
3. Description = finance-cloud rationale.
4. Enable and save.

**Expected result:** Two `MNB-SOD-*` policies visible in policy list.

**If it fails:** Check SAP and AWS apps actually expose those entitlement values on accounts.

### Task 5 — Run policy check via Refresh

Policies do nothing until evaluation runs. Refresh with policy checking is the lab’s evaluation path.

1. Open **Tasks** → **Refresh MNB Identities**.
2. Enable options equivalent to **Check policies** / refresh policy violations (wording varies — select policy-related checkboxes).
3. Run task; wait for success.
4. Open Policy Violations UI / identity risk / Advanced Analytics (use search for “PolicyViolation”).
5. Filter `MNB-SOD-*`.

**Expected result:** `MNB-SOD-Finance-Cloud` shows `jordan.reed` (if entitlements still present). Wire dual-control should **not** flag Priya or Marcus if they remain split.

**If it fails:** Re-aggregate SAP/AWS; confirm Jordan still has both ents; verify policy enabled; re-run refresh with policy check.

### Task 6 — Explain results to Risk (binder memo)

1. Write a short memo:

```text
To: Risk
Re: Initial SoD policy scan
- Policies live: MNB-SOD-Wire-DualControl, MNB-SOD-Finance-Cloud
- Wire split Priya/Marcus: clean
- Finance-cloud: jordan.reed violation (or cleared if Lesson 31 remediated—state which)
- Next: Lesson 40 deep dive + mitigation process
```

2. Attach policy screenshots and violation list.

**Expected result:** Memo suitable for training binder / mock Risk committee.

---

## Acceptance criteria

- [ ] All matrix pairs explained in business language.
- [ ] `MNB-SOD-Wire-DualControl` created and enabled.
- [ ] `MNB-SOD-Finance-Cloud` created and enabled.
- [ ] Refresh with policy checking completed.
- [ ] Violations reviewed; Jordan identified as finance-cloud case when entitlements present.
- [ ] Risk memo written.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No violations | Policy check off / ents missing | Enable check; re-aggregate; confirm Jordan |
| False wire hits on Priya | Wrong entitlements in policy | Ensure INIT vs APPR not swapped with roles |
| Policy won’t save | Missing left/right sets | Add both entitlement sides |
| Duplicate policies | Re-run of lesson | Rename or disable duplicates (`MNB-SOD-*`) |
| kai not flagged | IBSI+ECOM not built yet | Stretch only |

---

## Training binder evidence

1. Annotated `sod-matrix.csv` notes.
2. Screenshots of both `MNB-SOD-*` policies.
3. Refresh task success with policy check.
4. Violation list screenshot.
5. Risk memo.

---

## Knowledge check

1. Why does wire dual control exist?
2. Which persona violates finance-cloud SoD in the lab design?
3. When do policies typically evaluate?
4. Name the two policy objects you must create.
5. Is mitigation the same as deleting the policy?
6. Which persona is the stretch digital SoD case (`IBSI`+`ECOM`)?

### Answers

1. Prevent one person from both initiating and approving wire payments.
2. `jordan.reed` (`SAP_FI` + `AWS_ADMIN`).
3. During identity refresh with policy checking (and/or dedicated policy tasks if configured).
4. `MNB-SOD-Wire-DualControl` and `MNB-SOD-Finance-Cloud`.
5. No — mitigation accepts residual risk with controls/expiry; deleting the policy hides risk.
6. `kai.nguyen`.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “SOD policy” and “policy violation” for your version.
- [SailPoint Community](https://community.sailpoint.com/) — search “separation of duties policy” for entitlement vs role SOD patterns.
- [ISACA — Segregation of Duties / SOX ITGC primers](https://www.isaca.org/) — search “segregation of duties” for banking SoD language Risk expects.
- [NIST SP 800-53 AC-5 — Separation of Duties](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) — control family definition examiners map to your matrix.
- [FFIEC Information Technology Examination Handbook](https://ithandbook.ffiec.gov/) — search access controls / dual control for payment-system expectations.

---

## Stretch lab

1. Add `MNB-SOD-Digital-Channel` for `IBSI`+`ECOM` and observe `kai.nguyen`.
2. Discuss `ACH_OPS`+`WIRE_INIT` on Priya — policy vs compensating monitoring.
3. Export PolicyViolation objects from Debug for evidence pack format from Lesson 38.

---

## Summary

- You translated Meridian’s SoD matrix into IIQ policy objects with bank-ready rationales.
- You enabled policy checking on refresh and inspected violations.
- You established wire dual-control and finance-cloud as the first production-like controls.

---

**Previous:** [Lesson 38 — IdentityRequest Tracking & Auditing](38-identity-request-tracking.md)  
**Next:** [Lesson 40 — Payment Dual-Control Policy Deep Dive](40-payment-dual-control-policy.md)
