# Lesson 85 — Logical Applications

**Level:** Intermediate  
**Track:** Connectors — Infra, Logical, PAM  
**Time:** 60–90 min  
**Prereq:** Lesson 84 — Windows Local Connector  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (Logical composite)
- Repo: `lab-data/connectors/features-string-glossary.md` (`COMPOSITE`)
- Repo: `lab-data/apps/MNB-WirePortal.csv` (component example)
- Runtime: `~/iiq-lab-data/connectors/`

---

## Learning objectives

You will be able to:

- Explain **Logical** (composite) applications and the `COMPOSITE` feature
- Design Meridian logical app `MNB-Logical-Payments-Rail` composing Wire Portal + related targets
- Configure account/entitlement mapping rules at the logical layer (worksheet + UI where available)
- State when logical apps help certifications vs when they hide risk
- Complete lab-without-live-target composition without requiring all underlying connectors live

---

## Why this matters

**Business.** Payment dual control spans multiple technical systems (portal entitlements, AD groups, sometimes core flags). Business owners certify “payments access,” not connector jargon.

**Control / audit.** Logical apps can improve owner UX—or smear SoD boundaries if poorly designed. Examiners care that initiate vs approve remain separable. Meridian uses logical apps carefully for **certification surface**, not to bypass SoD.

---

## Concepts

Matrix: Logical composite → connector **Logical**, feature `COMPOSITE`.

```
MNB-Logical-Payments-Rail  (cert / request surface)
        │
        ├── MNB-WirePortal        (WIRE_INIT / WIRE_APPR)
        ├── MNB-ActiveDirectory   (optional payment AD groups)
        └── (future) core flag app
```

| Design rule | Meridian practice |
| --- | --- |
| One business capability | Payments rail—not “all finance” |
| Preserve SoD | Do not merge INIT+APPR into one logical entitlement |
| Owners | Business owner `rachel.evans`; technical owners stay on tier-1 apps |
| Aggregation | Depends on tier-1 Account Aggregation success |

**Lab-without-live-target:** Define composition worksheet + create Logical Application shell linking existing Delimited apps you already have (Wire Portal CSV is enough for structure).

---

## Before you start

- [ ] IIQ up
- [ ] `MNB-WirePortal` exists (Lesson 14) or recreate quickly from CSV
- [ ] Glossary entry for `COMPOSITE` read
- [ ] Personas `priya.wire`, `marcus.approve` correlated if Wire Portal aggregated
- [ ] Binder: `connectors/logical/`

---

## Lab procedure

### Task 1 — Decide composition scope

1. Write Meridian capability statement: “Govern payment initiation and approval access as one business application for owner certs—without collapsing SoD.”
2. List included tier-1 apps: start with `MNB-WirePortal` only; optionally note AD payment groups as Phase 2.
3. Explicitly exclude SAP Finance and AWS from this logical app (different risk domains).

**Expected result:** One-paragraph scope + in/out list.

**If it fails:** Wire Portal–only composition is sufficient for this lesson.

---

### Task 2 — Create `MNB-Logical-Payments-Rail`

1. Applications → Add New → **Logical** (or Composite) application type.
2. Name: `MNB-Logical-Payments-Rail`.
3. Owner: `rachel.evans`.
4. Description: “Composite cert surface for payment dual-control entitlements.”
5. Save shell.

**Expected result:** Logical application object exists.

**If it fails:** If UI type missing, create Application named exactly and document type Logical in Description; complete worksheet mapping.

---

### Task 3 — Map tier-1 accounts and entitlements

1. Open Logical application configuration (Account Mapping / Application schema—labels vary by version).
2. Map account identity from `MNB-WirePortal` native identity → logical account.
3. Expose entitlements `WIRE_INIT` and `WIRE_APPR` separately on the logical app (do not combine).
4. Document mapping table in binder:

| Logical entitlement | Tier-1 app | Tier-1 attribute |
| --- | --- | --- |
| WIRE_INIT | MNB-WirePortal | entitlement |
| WIRE_APPR | MNB-WirePortal | entitlement |

**Expected result:** Mapping table complete; SoD separation preserved.

**If it fails:** Binder-only mapping accepted when UI wizards differ—still create named Application.

---

### Task 4 — Aggregation and cube check (lab path)

1. Ensure **Account Aggregation** succeeded for `MNB-WirePortal`.
2. Run aggregation / refresh path required for Logical apps in your version (often refresh identities after tier-1 aggregate).
3. Open `priya.wire` and `marcus.approve` cubes; confirm logical account appears **or** document version-specific limitation.
4. If Logical aggregation unavailable offline: attach worksheet + screenshots of tier-1 accounts as lab-without-live-target completion.

**Expected result:** Logical accounts visible **or** documented limitation with tier-1 proof.

**If it fails:** Refresh MNB Identities; re-aggregate Wire Portal; check COMPOSITE feature on app.

---

### Task 5 — Certification and requestability notes

1. Write: Application owner cert campaigns may target `MNB-Logical-Payments-Rail` for business language.
2. Write: Access requests should still present INIT and APPR as distinct requestable items.
3. Write: SoD policy remains on underlying entitlement names (Lesson 40)—logical app must not hide violations.

**Expected result:** Three control notes in binder.

---

### Task 6 — Anti-patterns checklist

Mark each as Avoid:

- [ ] One logical entitlement “PaymentsFull” combining INIT+APPR
- [ ] Logical app spanning unrelated risk domains (cloud + wires)
- [ ] No tier-1 owner for remediation when connector fails
- [ ] Authoritative logical app (logical is never HR truth)

**Expected result:** Checklist initialed.

---

## Acceptance criteria

- [ ] Scope in/out documented
- [ ] `MNB-Logical-Payments-Rail` created
- [ ] Mapping preserves WIRE_INIT vs WIRE_APPR
- [ ] Aggregation/refresh path attempted or limitation documented
- [ ] Cert/request/SoD notes written
- [ ] Anti-patterns checklist completed

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Empty logical accounts | Tier-1 not aggregated | Aggregate Wire Portal first |
| Combined entitlement | Bad map | Split INIT/APPR |
| Owner confused by technical names | Missing logical layer | Use logical for cert UI only |
| Remediation fails | No tier-1 provision | Remediate on Wire Portal / AD directly |
| COMPOSITE missing | Wrong app type | Recreate as Logical |

---

## Training binder evidence

- Scope memo
- Application screenshot
- Entitlement mapping table
- Cube screenshots (Priya/Marcus) or limitation note
- Cert/request/SoD control notes
- Anti-patterns checklist

---

## Knowledge check

1. What featuresString concept applies to logical apps?
2. Name Meridian’s payments logical application.
3. Why must INIT and APPR stay separate on the logical app?
4. Is a logical application authoritative for HR?
5. What must succeed before logical accounts appear?

### Answers

1. `COMPOSITE`.  
2. `MNB-Logical-Payments-Rail`.  
3. To preserve payment dual-control SoD and distinct requestability.  
4. No.  
5. Tier-1 aggregation (e.g., `MNB-WirePortal`) and required refresh/logical processing.

---

## Stretch lab

Phase-2 design: add AD group `MNB-Wire-Initiators` under the same logical app with mapping notes—without implementing AD live.

---

## Summary

- Logical apps compose tier-1 systems into a business certification surface.
- Meridian’s payments logical app never collapses dual-control entitlements.
- Lab completes with shell + mappings even when composite runtime is limited.

---

**Previous:** [Lesson 84 — Windows Local Connector](84-windows-local-connector.md)  
**Next:** [Lesson 86 — PAM / CyberArk Module](86-pam-cyberark-module.md)
