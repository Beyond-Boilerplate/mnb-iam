# Lesson 85 — Logical Applications

**Level:** Intermediate  
**Track:** Connectors — Infra, Logical, PAM  
**Time:** 90–120 min  
**Prereq:** Lesson 84 — Windows Local Connector; Lesson 14 (`MNB-WirePortal`) and Lesson 40 (SoD) strongly recommended  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (Logical composite row)
- Repo: `lab-data/connectors/features-string-glossary.md` (`COMPOSITE`)
- Repo: `lab-data/apps/MNB-WirePortal.csv` (tier-1 component)
- Runtime: `~/iiq-lab-data/connectors/logical/`

---

## Learning objectives

You will be able to:

- Explain what a **Logical** (composite) application is, how the `COMPOSITE` feature works, and how it differs from a real connector
- Design Meridian logical apps (`MNB-Logical-*`) that project entitlements from multiple underlying applications — starting with a **Wire Dual Control View** over `WIRE_INIT` / `WIRE_APPR`
- Configure account and entitlement mapping so dual-control SoD stays visible to examiners and SoD engines
- Decide when a logical surface helps certification owners vs when it hides risk
- Complete a lab-without-live-target composition using existing Delimited / tier-1 apps when composite runtime is limited

---

## Why this matters

**Business.** Payment dual control at Meridian is one *business* capability that spans more than one *technical* system. `priya.wire` initiates wires in the Wire Portal; `marcus.approve` approves them; both may also sit in AD payment groups; someday a core banking flag may join the picture. When `rachel.evans` (payments business owner) opens a certification, she should see “payments dual-control access,” not a scavenger hunt across connector jargon. Last year a cert campaign listed only AD groups while Wire Portal entitlements lived elsewhere — Marcus’s approval entitlement was never reviewed as part of the payments package. That is how dual-control drift becomes invisible.

**Control / audit.** Logical apps improve owner UX *or* smear SoD boundaries if poorly designed. Examiners care that **initiate** and **approve** remain separable, requestable, and certifiable as distinct controls. Meridian uses logical apps carefully for a **certification / request surface** — never to collapse SoD, never as an authoritative HR source, and never as a substitute for a real connector when you need live inventory from a target system.

---

## Concepts

### What a logical (composite) application is

A **Logical application** (also called a composite application in some IdentityIQ versions) does **not** talk to a target system. It has no API, no IQService path, no aggregation protocol of its own. Instead it **projects** accounts and entitlements that already exist on one or more **tier-1** applications into a single business-facing surface.

In the featuresString glossary this appears as **`COMPOSITE`**: the application composes other applications rather than connecting outward.

| Approach | What it does | When Meridian uses it |
| --- | --- | --- |
| **Real connector** (`MNB-WirePortal`, `MNB-ActiveDirectory`, `MNB-Google-Workspace`) | Aggregates / provisions a live (or file) target | Inventory truth, provisioning, Task Result evidence |
| **Logical / composite** (`MNB-Logical-*`) | Projects tier-1 accounts/entitlements into one cert/request UX | Business packaging of a capability that spans systems |
| **Wrong substitute** | “We’ll just certify AD and ignore the portal” | Never — that is a blind spot, not a design |

Real-life anchor: `rachel.evans` should certify **Wire Dual Control View** once per campaign. Remediation still lands on `MNB-WirePortal` (and later AD) — the logical layer does not invent a new provisioning path.

### Entitlement projection vs merging (the SoD trap)

**Projection** means: the logical app *exposes* `WIRE_INIT` and `WIRE_APPR` as separate logical entitlements, each mapped to the same-named tier-1 entitlement on `MNB-WirePortal`. A holder of both still triggers SoD (Lesson 40). Certification lines stay separate. Requests stay separate.

**Merging** means: inventing one logical entitlement `PaymentsFull` that maps to both. That looks cleaner in a catalog — and destroys dual control in one stroke. Auditors will ask whether anyone can both initiate and approve; if your logical app only shows a single “payments” grant, you cannot answer.

```
Naive (forbidden at Meridian)
  MNB-Logical-Payments-Rail
        └── PaymentsFull  →  WIRE_INIT + WIRE_APPR   ← SoD erased

Correct (projection)
  MNB-Logical-Payments-Rail   ("Wire Dual Control View")
        ├── WIRE_INIT  →  MNB-WirePortal / WIRE_INIT
        └── WIRE_APPR  →  MNB-WirePortal / WIRE_APPR
```

### Correlation at the logical layer

Logical accounts are not a second population of people. They are **views** of tier-1 accounts. Correlation typically follows the tier-1 native identity (Wire Portal account id / username) onto the same IdentityIQ cube. If Priya’s Wire Portal account is correlated to `priya.wire`, her logical account appears on the same cube after the composite refresh path runs. Create-identities stays **OFF** — a logical app must never birth identities.

### When *not* to use a logical app

| Situation | Prefer instead |
| --- | --- |
| You need live SaaS/cloud inventory | Real connector (Lessons 74–76, etc.) |
| One system, one risk domain, one owner | Certify the tier-1 app directly |
| Spanning unrelated domains (wires + AWS + SAP) | Separate logical apps — or none |
| Hiding SoD by combining conflicting entitlements | Never — redesign |

---

## How it works

```
Tier-1 Account Aggregation (must succeed first)
        │
        ▼
MNB-WirePortal accounts + WIRE_INIT / WIRE_APPR
        │  optional: MNB-ActiveDirectory payment groups (Phase 2)
        ▼
Logical / COMPOSITE processing (version-specific refresh / aggregation)
        │
        ▼
MNB-Logical-Payments-Rail  ("Wire Dual Control View")
        │
        ├── Certification campaigns (business language for rachel.evans)
        ├── Access requests (INIT and APPR still distinct)
        └── SoD engine still evaluates underlying entitlement names
```

| Layer | Object | Responsibility |
| --- | --- | --- |
| Tier-1 | `MNB-WirePortal` | Truth for wire entitlements; remediation target |
| Tier-1 (optional) | AD payment groups | Directory grants that also gate portal SSO |
| Logical | `MNB-Logical-Payments-Rail` | Cert / request packaging; projection only |
| Policy | SoD (Lesson 40) | Still keyed to `WIRE_INIT` vs `WIRE_APPR` |

Aggregation dependency is absolute: empty tier-1 → empty logical. There is no “logical-only” inventory.

---

## Real-world setup (outside the logical shell)

Logical apps are IIQ objects, but production readiness still depends on work *outside* the composite form:

1. **Tier-1 connectors healthy** — Wire Portal (or its production native connector) aggregating on schedule; AD Direct if Phase 2 includes payment groups.
2. **Business capability charter** — one paragraph: what “payments dual control” means, which systems are in, which are out (exclude SAP Finance and AWS — different risk domains).
3. **Owner model** — business owner on the logical app (`rachel.evans`); technical owners remain on each tier-1 app for connector failures.
4. **SoD and request catalog review** — confirm SoD policies still reference underlying entitlement names; requestable items stay split.
5. **Certification design** — application-owner campaign targets the logical app; remediation instructions point operators to tier-1 apps.

You will capture all five in the lab worksheets even when you only compose from Delimited File tier-1 apps.

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq` as `spadmin`
- [ ] `MNB-WirePortal` exists (Lesson 14) or recreate quickly from `lab-data/apps/MNB-WirePortal.csv`
- [ ] Glossary entry for `COMPOSITE` read
- [ ] Personas `priya.wire` and `marcus.approve` correlated if Wire Portal has been aggregated
- [ ] Binder folder ready: `~/iiq-lab-data/connectors/logical/`

---

## Lab procedure

### Task 1 — Capability charter and naming

Every logical app starts with a one-capability rule. “All finance” is how SoD dies; “payments dual-control view” is how it survives.

1. Write the Meridian capability statement: *Govern payment initiation and approval access as one business application for owner certifications — without collapsing SoD.*
2. Name the app: `MNB-Logical-Payments-Rail`. Human subtitle for cert UI notes: **Wire Dual Control View**.
3. In-scope tier-1: start with `MNB-WirePortal` only. Phase 2 note: AD groups such as `MNB-Wire-Initiators` / `MNB-Wire-Approvers` (names illustrative — confirm against your AD inventory).
4. Explicitly **exclude** SAP Finance, AWS IAM, and Google Workspace from this logical app.
5. Owners: business `rachel.evans`; technical contacts remain Wire Portal / AD owners.

**Expected result:** One-paragraph charter + in/out list + naming card in the binder.

**If it fails:** Wire Portal–only composition is sufficient for this lesson; Phase 2 stays a note.

### Task 2 — Create `MNB-Logical-Payments-Rail`

In production this shell is the object certifications and request catalogs will reference for years — rename carefully.

1. Applications → Add New → **Logical** (or **Composite**) application type — or equivalent menu path in your build.
2. Name: `MNB-Logical-Payments-Rail`. Description: “Composite cert surface — Wire Dual Control View; projects WIRE_INIT / WIRE_APPR; never authoritative.”
3. Owner: `rachel.evans`. Not authoritative. Create identities: **OFF**.
4. Confirm features / type indicates composite / logical behavior (`COMPOSITE` in glossary terms). Save.

**Expected result:** Named logical application object exists.

**If it fails:** If the UI type is missing in your build, create an Application named exactly `MNB-Logical-Payments-Rail`, document type **Logical** in Description, and complete all mapping in the binder worksheet — the teaching goal is composition design, not a specific wizard.

### Task 3 — Account and entitlement mapping (preserve dual control)

This is the step where SoD is either preserved or destroyed. Map; do not merge.

1. Open Logical application configuration (Account Mapping / schema / composition — labels vary by version).
2. Map logical account identity from `MNB-WirePortal` native identity → logical account on the same cube.
3. Expose entitlements **separately**:

| Logical entitlement | Display intent | Tier-1 app | Tier-1 attribute / value |
| --- | --- | --- | --- |
| `WIRE_INIT` | Wire initiate | `MNB-WirePortal` | entitlement `WIRE_INIT` |
| `WIRE_APPR` | Wire approve | `MNB-WirePortal` | entitlement `WIRE_APPR` |

4. Copy the same table into `~/iiq-lab-data/connectors/logical/MNB-Logical-Payments-Rail-map.md`.
5. Explicit anti-map: **do not** create `PaymentsFull`, `WireDual`, or any combined entitlement.

**Expected result:** Mapping table complete; INIT and APPR remain distinct on the logical surface.

**If it fails:** Binder-only mapping is accepted when UI wizards differ — still keep the named Application and the table.

### Task 4 — Aggregation / refresh path and cube check

Logical accounts appear only after tier-1 truth exists and your version’s composite processing runs.

1. Run **Account Aggregation** for `MNB-WirePortal` (or confirm a recent successful Task Result).
2. Run the aggregation / identity refresh path your version requires for Logical apps (often: refresh identities after tier-1 aggregate — use the menu path your build documents).
3. Open cubes for `priya.wire` and `marcus.approve`:
   - Priya should show initiate-side access (logical and/or tier-1 `WIRE_INIT`).
   - Marcus should show approval-side access (`WIRE_APPR`).
4. If logical accounts do not materialize offline: document the version-specific limitation and attach tier-1 cube screenshots as **lab-without-live-target** completion. The composition design still counts.

**Expected result:** Logical accounts visible **or** a written limitation note with tier-1 proof for both personas.

**If it fails:** Re-aggregate Wire Portal; refresh identities; confirm the app type is Logical/COMPOSITE; verify Priya/Marcus correlation on the tier-1 app first.

### Task 5 — Certification, requestability, and SoD control notes

A logical app that looks good but breaks control language fails the examiner conversation.

1. **Certification:** Application-owner campaigns may target `MNB-Logical-Payments-Rail` so `rachel.evans` sees business language (Wire Dual Control View).
2. **Requests:** Access requests must still present `WIRE_INIT` and `WIRE_APPR` as distinct requestable items — never a single “payments access” SKU.
3. **SoD:** Policies remain on underlying entitlement names (Lesson 40). Record: *Logical projection must not hide INIT+APPR violations.*
4. **Remediation:** Revoke instructions point operators to `MNB-WirePortal` (and AD in Phase 2), not to a fictional logical provisioner.

**Expected result:** Four control notes in the binder.

### Task 6 — Anti-patterns checklist (initial)

Mark each as **Avoid** and initial:

- [ ] One logical entitlement combining INIT+APPR
- [ ] Logical app spanning unrelated risk domains (cloud + wires + SAP)
- [ ] No tier-1 owner when the connector fails
- [ ] Authoritative logical app (logical is never HR truth)
- [ ] Using logical apps instead of fixing a broken real connector

**Expected result:** Checklist initialed and filed under `connectors/logical/`.

### Task 7 — Examiner question drill

*"Show me how payment initiate and approve are governed as one business capability without allowing one person to hold both unchecked."*

Write the three-part answer: (1) logical app `MNB-Logical-Payments-Rail` as the cert surface with separate projected entitlements, (2) SoD policy on `WIRE_INIT` vs `WIRE_APPR`, (3) cubes for Priya vs Marcus showing split holdings plus a certification line-item screenshot plan.

**Expected result:** Written examiner answer in the binder.

### Task 8 — Residual risk

Record `RR-LOGICAL-01`: *Logical apps do not replace tier-1 aggregation. If Wire Portal aggregation fails, the dual-control view goes stale while still looking “complete” to owners.* Compensating control: monitor tier-1 Task Results; fail closed on cert launch if tier-1 aggregation is older than SLA. Owner: Wire Portal technical owner + `rachel.evans` informed.

**Expected result:** Residual risk logged with owner and compensating control.

---

## Acceptance criteria

- [ ] Capability charter, naming (`MNB-Logical-Payments-Rail` / Wire Dual Control View), and in/out list written
- [ ] Logical application shell created (or documented placeholder with exact name)
- [ ] Mapping preserves `WIRE_INIT` vs `WIRE_APPR`; no combined entitlement
- [ ] Aggregation/refresh attempted; cubes checked or limitation documented with tier-1 proof
- [ ] Cert / request / SoD / remediation notes written
- [ ] Anti-patterns checklist, examiner answer, and `RR-LOGICAL-01` recorded

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Empty logical accounts | Tier-1 not aggregated or refresh skipped | Aggregate `MNB-WirePortal` first; run required identity refresh |
| Combined entitlement appears | Bad map / catalog shortcut | Split INIT/APPR; delete any `PaymentsFull`-style item |
| Owner confused by technical names | Missing or unused logical layer | Use logical app for cert UI; keep tier-1 for ops |
| Remediation fails from logical app | Logical has no provisioner | Remediate on Wire Portal / AD directly |
| `COMPOSITE` / Logical type missing | Wrong app type or module | Recreate as Logical, or binder-complete with Description note |
| SoD silent on dual holders | Policies keyed only to logical display names | Keep SoD on underlying entitlement names |

---

## Training binder evidence

- Capability charter + in/out list
- Application screenshot (or named placeholder note)
- Entitlement mapping table (`MNB-Logical-Payments-Rail-map.md`)
- Cube screenshots (Priya/Marcus) or limitation note with tier-1 proof
- Cert / request / SoD / remediation control notes
- Anti-patterns checklist, examiner answer, `RR-LOGICAL-01`

---

## Knowledge check

1. What featuresString concept applies to logical apps, and what does it mean in one sentence?
2. Name Meridian’s payments logical application and its business subtitle.
3. Why must `WIRE_INIT` and `WIRE_APPR` stay separate on the logical app?
4. Is a logical application authoritative for HR identities? Why or why not?
5. What must succeed before logical accounts can appear?
6. What risk does `RR-LOGICAL-01` call out?

### Answers

1. `COMPOSITE` — the application projects accounts/entitlements from other applications rather than connecting to an external target.
2. `MNB-Logical-Payments-Rail` — Wire Dual Control View.
3. To preserve payment dual-control SoD, distinct requestability, and separable certification line items.
4. No — logical apps never create identities; HR remains the authoritative source.
5. Successful tier-1 aggregation (e.g. `MNB-WirePortal`) plus the version’s logical/composite refresh processing.
6. Stale dual-control view when tier-1 aggregation fails while the logical cert surface still looks complete.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “logical application” or “composite application” for your version’s mapping and aggregation behavior.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — practical threads on composite account mapping and certification targeting.
- [FFIEC Information Security booklet](https://www.ffiec.gov/press/pr110669.htm) — dual-control and segregation-of-duties expectations that motivate keeping INIT/APPR separable (locate current booklet via FFIEC IT Handbook search for “Information Security”).
- [NIST SP 800-53 — Access Control (AC) family](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — separation of duties framing useful when defending projection vs merge designs.
- Repo: `lab-data/connectors/features-string-glossary.md` — `COMPOSITE` entry and related connector feature notes.

---

## Stretch lab

Phase-2 design: add AD groups `MNB-Wire-Initiators` and `MNB-Wire-Approvers` under the same logical app with a second mapping table — still without collapsing INIT/APPR. Draft how a single application-owner certification would show both portal entitlements and AD groups as separate line items, and note which system each revoke would target.

---

## Summary

- Logical apps compose tier-1 systems into a business certification/request surface; they are not connectors and not HR sources.
- Meridian’s `MNB-Logical-Payments-Rail` (Wire Dual Control View) projects `WIRE_INIT` and `WIRE_APPR` separately so dual-control SoD survives packaging.
- Lab completes with shell + mappings + control notes even when composite runtime is limited — tier-1 aggregation remains the truth.

---

**Previous:** [Lesson 84 — Windows Local Connector](84-windows-local-connector.md)  
**Next:** [Lesson 86 — PAM / CyberArk Module](86-pam-cyberark-module.md)
