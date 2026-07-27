# Lesson 17 — Account Correlation Basics

**Level:** Intermediate  
**Track:** Correlation  
**Time:** 60–75 min  
**Prereq:** Lesson 16 (pipeline run); `MNB-IT-Access` from Lesson 09; `MNB-HR` populated  

**Lab data:**
- Application under test: **MNB-IT-Access** (from `EmployeeData.txt` / `apps/MNB-IT-Access.csv`)
- Authoritative identities: **MNB-HR**
- Personas: `priya.wire`, `jordan.reed`; watch `raj.external` for email mismatch

---

## Learning objectives

You will be able to:

- Explain what **account correlation** does and why uncorrelated accounts are unowned access
- Configure correlation on **MNB-IT-Access** using **employeeId** then **email**
- Re-run Account Aggregation and Identity Refresh so links materialize
- Verify linked IT accounts on `priya.wire`
- List uncorrelated accounts and recognize vendor-email failures as expected edge cases

---

## Why this matters

**Business.** An account that is not attached to a person has no manager, no joiner/mover/leaver, and no certification owner. In a bank, that is orphan privilege—especially on inventory dumps that include AWS_ADMIN and WIRE_*.

**Control / audit.** Examiners ask: *How do you bind application accounts to HR identities?* Meridian’s answer must be a documented correlation key hierarchy with evidence of residual uncorrelated accounts under remediation SLA (Lesson 19).

---

## Concepts

**Correlation.** Matching rules that link an **account** on an application to an existing **identity** cube using attribute equality (and optionally rules).

**Uncorrelated account.** Account exists on the application but is not linked to any identity. Still real access—just invisible to manager-centric views until remediated.

**Meridian key preference:**

```
Strongest ──► employeeId (account) = employeeId (identity from HR)
Next      ──► email (account) = email (identity)
Avoid     ──► display name / fuzzy / first+last alone (false merges)
```

| Account attr (`MNB-IT-Access`) | Identity attr (`MNB-HR`) | Notes |
| --- | --- | --- |
| `employeeId` | `employeeId` | Primary |
| `email` | `email` | Secondary; fails for `raj.external` vendor mail |
| `userName` | `name` / uid | Useful if aligned; confirm before relying |

```
Account Aggregation reads rows
        │
        ▼
Correlation engine attempts match
        │
        ├── match → account appears on identity cube
        └── no match → uncorrelated account list
```

**Authoritative vs target correlation.** `MNB-HR` creates identities (accounts on HR are the person). Target apps like `MNB-IT-Access` **must correlate onto** those people—never create duplicates.

---

## Before you start

- [ ] `MNB-HR` aggregated; cubes exist for Meridian staff
- [ ] `MNB-IT-Access` application exists and has been aggregated at least once
- [ ] You can open application account lists and identity Accounts tabs
- [ ] Notebook ready for key order and uncorrelated counts
- [ ] Do not enable create-identities on `MNB-IT-Access`

---

## Lab procedure

### Task 1 — Baseline: who is uncorrelated today?

1. Open application `MNB-IT-Access` → Accounts (or Uncorrelated Accounts view / equivalent filter).
2. Note approximate count of uncorrelated accounts (may be high if correlation never configured).
3. Search identity `priya.wire` → Accounts tab. Note whether an `MNB-IT-Access` account is already linked.
4. Record baseline numbers in binder: *Before correlation config: U=___ ; Priya linked? Y/N*.

**Expected result:** Baseline captured so you can prove improvement after configuration.

**If it fails:** If the app has zero accounts, run `Aggregate MNB-IT-Access` first (Lesson 09/16).

---

### Task 2 — Choose and document correlation keys

1. Confirm HR identities expose `employeeId` and `email` (Lesson 05 schema).
2. Confirm IT Access schema exposes `employeeId` and `email`.
3. Write Meridian standard:

```text
MNB-IT-Access correlation order:
1) account.employeeId → identity.employeeId
2) account.email → identity.email
```

4. Explicitly reject “email only” as the sole enterprise standard (Raj case).

**Expected result:** Documented key hierarchy before clicking UI.

---

### Task 3 — Configure correlation on MNB-IT-Access

1. Open `MNB-IT-Access` application configuration → **Correlation** (or Account Correlation / equivalent menu path).
2. Add attribute assignment(s):
   - `employeeId` (application) to `employeeId` (identity)
   - `email` (application) to `email` (identity)
3. If the UI supports ordered attempts, put **employeeId first**.
4. Ensure “create new identities from unmatched accounts” remains **disabled**.
5. Save.

**Expected result:** Correlation config saved on `MNB-IT-Access` with employeeId + email mappings.

**If it fails:** Attribute names must match schema exactly—fix typos like `EmployeeId` vs `employeeId`.

---

### Task 4 — Re-aggregate and refresh

1. Run Account Aggregation task `Aggregate MNB-IT-Access`.
2. Run `Refresh MNB Identities` (or your standard refresh).
3. Optional: if your build offers a dedicated correlation reprocess, use it—otherwise aggregation + refresh is the lab path.
4. Record task results.

**Expected result:** Tasks succeed; many previously uncorrelated accounts now link to HR cubes.

**If it fails:** Re-check correlation mappings; confirm HR has `employeeId` populated on identities.

---

### Task 5 — Verify priya.wire linkage

1. Open identity `priya.wire` (MNB00090).
2. Accounts tab: confirm `MNB-IT-Access` account linked.
3. Entitlements: expect directory/wire-related access from inventory (e.g. ELDAP, WIRE_INIT, ACH_OPS per lab dump)—exact set per `EmployeeData.txt`.
4. Screenshot for binder.

**Expected result:** Priya’s IT inventory account is on her cube—manager-visible access.

**If it fails:** Check her `employeeId`/`email` on both HR and the IT account; fix data mismatch only if you introduced one—do not invent HR rows.

---

### Task 6 — Spot-check jordan.reed

1. Open `jordan.reed`.
2. Confirm IT Access account links and shows toxic inventory entitlements (`SAP_FI`, `AWS_ADMIN`, etc. as present in dump).
3. Note these may **also** exist on platform apps from Lessons 12–13—inventory vs platform can overlap; that is OK for lab learning.

**Expected result:** Jordan linked; toxic entitlements visible for later SoD.

---

### Task 7 — Inspect remaining uncorrelated accounts

1. Return to `MNB-IT-Access` uncorrelated list.
2. Look for `raj.external` / vendor email `raj.contractor@vendor-mail.invalid`.
3. Explain in notebook: email secondary key fails; employeeId should still match **if** configured first—if Raj remains uncorrelated, proceed to Lesson 18 for rule precision and troubleshooting.
4. Capture uncorrelated count **after** config: *After: U=___*.

**Expected result:** Uncorrelated population shrinks; remaining cases are explainable (vendor mail, data typos, contractors) rather than “we never configured correlation.”

**If it fails:** If nothing correlated, mappings are wrong or aggregation did not re-run—do not flip authoritative.

---

### Task 8 — Control narrative

1. Write:

```text
Control: Account correlation for MNB-IT-Access
Keys: employeeId primary, email secondary
Create identities: prohibited on target
Evidence: before/after uncorrelated counts; priya.wire account screenshot
Residual risk: vendor emails / orphans → Lesson 19 remediation SLA
```

**Expected result:** Audit-ready correlation statement for Meridian inventory app.

---

## Acceptance criteria

- [ ] Correlation configured on `MNB-IT-Access` (employeeId + email)
- [ ] Aggregate + Refresh re-run after config
- [ ] `priya.wire` shows linked IT Access account
- [ ] Before/after uncorrelated counts recorded
- [ ] Create-identities still disabled
- [ ] Control narrative written

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Nothing correlates | Wrong attribute names / not saved | Fix mapping; re-aggregate |
| Everyone correlated except vendor emails | Email-only effective order | Ensure employeeId is first |
| Duplicate identities appeared | Create-identities on | Disable; merge/cleanup carefully |
| Priya linked but entitlements empty | Entitlement attr not configured (Lesson 09) | Fix schema; re-aggregate |
| Correlated to wrong person | Weak key (name) used | Remove fuzzy keys; use employeeId |

---

## Training binder evidence

1. Screenshot of correlation configuration
2. Before/after uncorrelated counts
3. `priya.wire` Accounts tab with `MNB-IT-Access`
4. `jordan.reed` entitlements snapshot
5. Correlation control narrative

Examiner question: *“What is your primary correlation key and why not email alone?”*

---

## Knowledge check

1. What is an uncorrelated account?
2. What is Meridian’s preferred primary correlation key?
3. Why can email-only correlation fail for `raj.external`?
4. Should `MNB-IT-Access` create identities for unmatched accounts?
5. Which verification persona proves a happy-path link in this lesson?

### Answers

1. An application account not linked to any identity cube—unowned from a manager/cert perspective.
2. `employeeId`.
3. His account email is `raj.contractor@vendor-mail.invalid`, not the corporate identity email pattern.
4. No.
5. `priya.wire`.

---

## Stretch lab

- Apply the same employeeId/email correlation pattern to `MNB-WirePortal` and `MNB-CoreBanking`.
- Write Meridian’s one-paragraph enterprise correlation standard for all target apps.

---

## Summary

- Correlation attaches IT inventory accounts to HR people using **employeeId** then **email**.
- `priya.wire` validates the happy path; residuals feed advanced rules and remediation.
- Uncorrelated accounts are now a measured control metric, not an unknown.

---

**Previous:** [Lesson 16 — Multi-App Aggregation Strategy](16-multi-app-aggregation-strategy.md)  
**Next:** [Lesson 18 — Correlation Rules & Edge Cases](18-correlation-rules-advanced.md)
