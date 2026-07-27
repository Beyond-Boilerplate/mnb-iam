# Lesson 40 — Payment Dual-Control Policy Deep Dive

**Level:** Advanced  
**Track:** Policies  
**Time:** 60–75 minutes  
**Prereq:** Lesson 39 (`MNB-SOD-Wire-DualControl` enabled); Wire Portal apps aggregated  

**Lab data:**
- Clean split: `priya.wire` (`WIRE_INIT`) / `marcus.approve` (`WIRE_APPR`)
- Sources: `lab-data/apps/MNB-WirePortal-Initiators.csv`, `MNB-WirePortal-Approvers.csv`, `MNB-WirePortal.csv`
- Matrix row: `WIRE_INIT`,`WIRE_APPR` in `reference/sod-matrix.csv`
- Exception signer: `rachel.evans` (Payments Operations Manager)

---

## Learning objectives

You will be able to:

1. Validate that `priya.wire` and `marcus.approve` remain **clean** under `MNB-SOD-Wire-DualControl`.
2. Safely **induce** a wire dual-control violation in the lab (temporary bad combination).
3. Detect the violation via Refresh / policy UI and open the finding.
4. Decide revoke vs mitigate; prefer revoke for payments SoD.
5. Write exception rules (max life, compensating control, `rachel.evans` signoff).
6. Clear the induced violation and leave the shared lab clean.

---

## Why this matters

**Business.** Payments SoD failures are existential — one identity with initiate and approve can complete fraudulent wires. Priya and Marcus exist as a staffing model: she creates instructions; he approves them. Collapse that split and Meridian’s dual-control story collapses with it.

**Control / audit.** Treasury owns the dual-control business rule; IAM owns detection. Exceptions without expiry are fake compliance. Control owner: Payments (`rachel.evans`) + Risk; IAM executes tooling. Examiner question: *Show a clean baseline, a detected violation, and how exceptions expire.*

---

## Concepts

### Baseline clean design

```text
priya.wire     ── WIRE_INIT ──► create instructions
marcus.approve ── WIRE_APPR ──► approve instructions
        │
        └── MNB-SOD-Wire-DualControl flags ANY identity with BOTH
```

| Identity | employeeId | Entitlement | SoD status |
| --- | --- | --- | --- |
| `priya.wire` | `MNB00090` | `WIRE_INIT` | Clean |
| `marcus.approve` | `MNB00091` | `WIRE_APPR` | Clean |

Note: Priya also holds `ACH_OPS` in IT inventory — related matrix pair for stretch, not this policy’s left/right set.

### Revoke vs mitigate for payments

| Path | When | Meridian rule |
| --- | --- | --- |
| **Revoke** | Default for any wire SoD hit | Remove one side immediately |
| **Mitigate** | Rare, temporary only | ≤ 30 days + compensating control + `rachel.evans` signoff + Risk informed |
| Standing exception | Never | Prohibited |

The wrong way: mitigate with blank expiry “until staffing recovers.” That is permanent dual-control bypass under a different name.

### Induce → detect → decide → clear

Lab learning requires inducing a bad state — then restoring. Shared labs that leave induced violations poison the next learner and the exam evidence story.

---

## How it works

```text
Baseline clean (Priya INIT / Marcus APPR)
    │
    ▼
Temporarily grant both WIRE_INIT + WIRE_APPR to test identity
    │
    ▼
Account Aggregation (if file-based) + Refresh MNB Identities (policy check)
    │
    ▼
PolicyViolation on MNB-SOD-Wire-DualControl
    │
    ├── Revoke (preferred) ──► clear violation
    └── Mitigate ≤ 30 days + compensating control + rachel.evans signoff
    │
    ▼
Restore lab files / entitlements to clean split
    │
    ▼
Re-baseline: no open induced violations
```

| Artifact | Purpose |
| --- | --- |
| Baseline screenshots | Prove clean split before induction |
| `exception-rules.txt` | Treasury-owned exception standard |
| Induced violation screenshot | Detection works |
| Revoke clearance | Preferred remediation path |
| Restore confirmation | Shared lab hygiene |

**IIQ terms:** *PolicyViolation* work items may offer revoke/mitigate. *Mitigation* must include expiration and compensating control text.

---

## Before you start

- [ ] `MNB-SOD-Wire-DualControl` exists and is enabled (Lesson 39).
- [ ] Wire entitlements aggregated for Priya and Marcus.
- [ ] Choose induction method: (A) temporary entitlement on a **test** user, or (B) briefly add second wire entitlement to a copy of Marcus/Priya — prefer disposable test identity.
- [ ] Evidence folder `~/iiq-lab-data/evidence/wire-sod-L40/`.
- [ ] Plan restore steps **before** inducing.

---

## Lab procedure

### Task 1 — Validate clean baseline (Priya / Marcus)

You cannot prove detection without proving the staffing model was clean first.

1. Open identity `priya.wire`; confirm `WIRE_INIT` present and `WIRE_APPR` absent.
2. Open identity `marcus.approve`; confirm `WIRE_APPR` present and `WIRE_INIT` absent.
3. Open Policy Violations filtered to `MNB-SOD-Wire-DualControl`.
4. Confirm neither Priya nor Marcus appears (or only closed historical items).

**Expected result:** Written baseline: “Priya/Marcus clean under wire dual-control at `<timestamp>`.”

**If it fails:** Fix data — remove accidental dual entitlements; re-aggregate wire apps; refresh.

### Task 2 — Write exception rules before you induce

Exception policy written after the violation is rationalization. Write rules first.

1. Draft Meridian exception standard:

```text
Wire SoD exception (MNB-SOD-Wire-DualControl)
- Preferred response: Revoke one side immediately (usually remove approve from initiator or vice versa).
- Mitigation only with:
  - rachel.evans (Payments Ops) written approval
  - Compensating control (e.g. dual manual review log, reduced limits)
  - Maximum life: 30 days (no auto-renew without new signoff)
  - Risk informed
- Standing exceptions: prohibited
```

2. Store as `exception-rules.txt` in the evidence folder.

**Expected result:** Exception rules exist before any lab violation is created.

### Task 3 — Induce a violation safely

Prefer a disposable test identity so shared Priya/Marcus stay clean for other learners.

1. Pick target: create/use lab test user `wire.sodtest` **or** temporarily add `WIRE_APPR` to `priya.wire` in a **private copy** of the wire CSV (restore later).
2. Ensure both `WIRE_INIT` and `WIRE_APPR` appear on that single identity after Account Aggregation.
3. Do **not** induce on production-like shared leadership users.
4. Record induction timestamp and method in `induce-log.txt`.

**Expected result:** One identity intentionally holds both wire entitlements; log explains how to reverse.

**If it fails:** Use Debug to add entitlement link only if you know how — CSV + Aggregate is the supported training path.

### Task 4 — Detect the violation

Detection without screenshots is hearsay. Capture the PolicyViolation object.

1. Run **Refresh MNB Identities** with policy checking enabled.
2. Open Policy Violations → filter `MNB-SOD-Wire-DualControl`.
3. Open the violation; screenshot identity, policy, conflicting entitlements.
4. Confirm Priya/Marcus baseline still clean if you used a separate test user.

**Expected result:** Clear PolicyViolation object for the induced identity.

**If it fails:** Confirm both entitlements on cube; policy enabled; correct entitlement names.

### Task 5 — Decide: revoke (preferred) then optional mitigate demo

Payments default is revoke. Mitigate is a documented exception path — not the happy path.

1. **Revoke path (required):** Remove one conflicting entitlement (prefer removing `WIRE_APPR` from an initiator-shaped user). Re-aggregate if file-based. Refresh. Confirm violation clears.
2. **Mitigate path (optional demo on a second induction):** Open violation → Mitigate → set **≤ 30 days** expiry → comment compensating control → note `rachel.evans` approval ticket `MNB-PMT-EXC-40xx`.
3. Record which path you took and why revoke is default for payments.

**Expected result:** At least one cleared violation via revoke; mitigate rules documented even if mitigate UI is brief.

**If it fails:** Manual entitlement remove + refresh is acceptable revoke evidence.

### Task 6 — Clear lab and Treasury signoff note

Leave the lab as clean as you found it — induced violations are training artifacts, not production state.

1. Restore wire CSV / entitlements to original Priya INIT / Marcus APPR split.
2. Re-aggregate wire applications; Refresh; confirm no open induced violations.
3. Write Treasury signoff note template:

```text
Exception approver: rachel.evans@meridiannb.com
Required fields: identity, entitlements, compensating control, expiry, ticket
```

4. Confirm baseline clean again (Task 1 quick re-check).

**Expected result:** Shared lab returned to clean dual-control design; restore proven in screenshots.

---

## Acceptance criteria

- [ ] Priya/Marcus validated clean before and after.
- [ ] Exception rules written (30-day max, `rachel.evans` signoff).
- [ ] Violation induced, detected, and documented.
- [ ] Revoke path executed; violation cleared.
- [ ] Lab restored; no leftover open induced violations.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Priya already violating | Bad data merge | Remove APPR from Priya; re-aggregate |
| Induce not detected | Policy check off | Enable on Refresh; verify policy |
| Violation won’t clear | Entitlement still on cube | Remove both sides of conflict correctly; refresh |
| Mitigate without expiry | UI default open-ended | Force 30-day date; reject eternal mitigations |
| Shared lab broken | Forgot restore | Re-copy wire CSVs from `lab-data/apps/` |

---

## Training binder evidence

1. Baseline clean screenshots (Priya / Marcus).
2. `exception-rules.txt` with rachel.evans requirement.
3. Induced violation screenshot.
4. Revoke clearance screenshot.
5. Restore confirmation / re-baseline.
6. Optional mitigate demo with expiry.

---

## Knowledge check

1. What is the preferred response to a wire SoD hit?
2. What is the maximum exception life in this lesson’s standard?
3. Who signs wire SoD exceptions?
4. Why must induced violations be cleared before you leave the lab?
5. Are Priya and Marcus supposed to violate `MNB-SOD-Wire-DualControl` in the baseline?
6. What compensating-control elements must a mitigation comment include?

### Answers

1. Revoke one side of the conflicting pair immediately.
2. 30 days (renewal needs new signoff).
3. `rachel.evans` (Payments Operations Manager), with Risk informed.
4. Shared labs and exam evidence must not show fake ongoing fraud risk; restore protects the next learner.
5. No — they are the clean dual-control split.
6. Compensating control description, expiry, approver/ticket, and Risk awareness.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “policy violation mitigate” and “SOD policy.”
- [SailPoint Community](https://community.sailpoint.com/) — search “wire dual control SOD” / payment SoD patterns.
- [FFIEC Information Technology Examination Handbook](https://ithandbook.ffiec.gov/) — search dual control and funds transfer security expectations.
- [NIST SP 800-53 AC-5 — Separation of Duties](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) — control language for initiate/approve separation.
- [ISACA — Segregation of Duties primers](https://www.isaca.org/) — search “segregation of duties” for exception-governance language Risk committees use.

---

## Stretch lab

1. Extend policy coverage or add `MNB-SOD-ACH-Wire` for `ACH_OPS`+`WIRE_INIT` and discuss Priya’s residual concentration risk.
2. Wire a violation work item email template to Treasury.
3. Pre-stage Lesson 41 by leaving **one** mitigated (expiring) non-wire violation only if the lab is private — never on shared wire users.

---

## Summary

- You proved Priya/Marcus embody payment dual control under `MNB-SOD-Wire-DualControl`.
- You induced, detected, revoked, and cleared a wire SoD violation safely.
- You documented Treasury-owned exception rules with hard expiry.

---

**Previous:** [Lesson 39 — SoD Fundamentals for Banking](39-sod-fundamentals.md)  
**Next:** [Lesson 41 — Policy Violations & Mitigation](41-policy-violations-mitigation.md)
