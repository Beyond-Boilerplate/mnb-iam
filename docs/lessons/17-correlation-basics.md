# Lesson 17 — Account Correlation Basics

**Level:** Intermediate  
**Track:** Correlation  
**Time:** 60–75 min  
**Prereq:** Lesson 16 (pipeline run); Lesson 16b (Task Results) recommended; `MNB-IT-Access` from Lesson 09; `MNB-HR` populated  

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
- Defend Meridian’s correlation key hierarchy to an examiner without inventing fuzzy matches

---

## Why this matters

**Business.** An account that is not attached to a person has no manager, no joiner/mover/leaver, and no certification owner. When Meridian’s IT inventory dump includes `AWS_ADMIN` and `WIRE_*` rows sitting uncorrelated, that privilege is real access with nobody accountable — the classic orphan path that later becomes a fraud or exam finding.

**Control / audit.** Examiners ask: *How do you bind application accounts to HR identities?* Meridian’s answer must be a documented correlation key hierarchy (employeeId primary, email secondary), create-identities prohibited on targets, and evidence of residual uncorrelated accounts under remediation SLA (Lesson 19). “We matched on display name” fails the exam.

---

**Meridian ID map:** HR native key is `userId`. IT dumps use `employeeId` with the **same values** as HR `userId`. Promote/correlate accordingly—do not invent a separate HR `employeeId` column.

## Concepts

### What correlation actually does

**Correlation** is the set of matching rules that link an **account** (a `Link` object on an application) to an existing **identity** cube. It runs during Account Aggregation (and related reprocess paths): for each account, IIQ evaluates configured attribute equalities (and optionally custom rules) against the identity warehouse.

An **uncorrelated account** exists on the application but is not linked to any identity. It is still real access — just invisible to manager-centric views, certifications, and most lifecycle workflows until remediated. Uncorrelated is a control metric, not a UI annoyance.

### Authoritative vs target — who creates people

`MNB-HR` is **authoritative**: its aggregation creates and updates identity cubes (the person). Target apps like `MNB-IT-Access` **must correlate onto** those people — they must never mint duplicate cubes for unmatched inventory rows. The naive alternative — “create identities from IT Access so nothing looks uncorrelated” — produces ghost people with no HR truth, no manager, and no trustworthy leaver signal.

### Meridian’s key preference (and why name matching fails)

At Meridian, the stable bridge from any target to HR is the employee number:

```
Strongest ──► employeeId (account) = userId (identity from HR)
Next      ──► email (account) = email (identity)
Avoid     ──► display name / fuzzy / first+last alone (false merges)
```

| Account attr (`MNB-IT-Access`) | Identity attr (`MNB-HR`) | Notes |
| --- | --- | --- |
| `employeeId` | `userId` | Primary — IT dump key equals HR `userId`; survives mailbox changes |
| `email` | `email` | Secondary; fails for `raj.external` vendor mail |
| `userName` | `name` / uid | Useful if aligned; confirm before relying |

**Real-life Meridian example.** `priya.wire` (MNB00090) has matching associate key (`userId` on HR / `employeeId` on IT) and corporate email on both sides. Correlation attaches her ELDAP / WIRE_INIT / ACH_OPS inventory to her cube so `rachel.evans` can see and certify it. Contrast `raj.external`: his mailbox is `raj.contractor@vendor-mail.invalid`. Email-only correlation leaves him orphaned even when IT `employeeId=MNB00093` matches HR `userId` — which is why associate-id must be first.

### Wrong way vs bank-ready way

| Approach | What happens under exam |
| --- | --- |
| Email-only correlation | Contractors and aliases fail; coverage looks “good” until privileged orphans appear |
| Name / first+last matching | False merges (two Reeds, shared nicknames) — certifications attest the wrong human |
| Create-identities on targets | Ghost cubes; leavers never fire from HR |
| employeeId then exact email; create off | Residual uncorrelated is measurable and remediable |

---

## How it works

IdentityIQ’s correlation engine evaluates configured mappings when accounts are aggregated (or when a dedicated correlation reprocess runs). Matched accounts become Links on the identity; unmatched accounts remain on the application’s uncorrelated list.

```
Account Aggregation reads MNB-IT-Access rows
        │
        ▼
Correlation engine (ordered attribute maps)
        │
        ├── employeeId match → Link on identity cube
        ├── else email match → Link on identity cube
        └── no match → uncorrelated account list
                │
                ▼
Identity Refresh updates manager-visible cube state
```

| Stage | IIQ object / task | What you prove |
| --- | --- | --- |
| Configure maps | Application → Correlation | employeeId first, email second, create-identities OFF |
| Ingest accounts | Account Aggregation `Aggregate MNB-IT-Access` | Accounts created/updated; correlation attempted |
| Compile cubes | `Refresh MNB Identities` | Links visible on Accounts tabs |
| Measure residual | Uncorrelated Accounts view | Before/after counts for the control narrative |

One consequence worth remembering: correlation does not “fix” bad source data. If `employeeId` is blank or mistyped on the account, the account stays uncorrelated — correctly. Remediation (Lesson 19) and precision rules (Lesson 18) pick up from there.

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq` as `spadmin`
- [ ] `MNB-HR` aggregated; cubes exist for Meridian staff
- [ ] `MNB-IT-Access` application exists and has been aggregated at least once
- [ ] You can open application account lists and identity Accounts tabs
- [ ] Notebook ready for key order and uncorrelated counts
- [ ] Do not enable create-identities on `MNB-IT-Access`

---

## Lab procedure

### Task 1 — Baseline: who is uncorrelated today?

Before changing configuration, capture the “before” state. Auditors and your future self need proof that correlation improved something — not that you clicked Save once.

> **Carry-forward from Lessons 09–16.** High uncorrelated counts, missing target apps on HR cubes, and occasional login-named orphan cubes (create-identities left ON during onboard) are **normal** starting points—not proof that aggregation failed. This lesson is where you wire `employeeId` → HR `userId` (and email fallback) so accounts land on the right cubes. Do **not** “baseline clean” by enabling create-identities.

1. Open application `MNB-IT-Access` → Accounts (or Uncorrelated Accounts view / equivalent filter).
2. Note approximate count of uncorrelated accounts (may be high if correlation never configured).
3. Search identity `priya.wire` → Accounts tab. Note whether an `MNB-IT-Access` account is already linked. Also search by display/`userId` style if your HR cubes use that naming.
4. Optionally note orphan cubes named like logins (`aisha.murphy`) vs HR cubes (`Aisha Murphy` / `MNB00013`)—those are remediation candidates after correlation, not a reason to skip this lesson.
5. Record baseline numbers in binder: *Before correlation config: U=___ ; Priya linked? Y/N ; orphan login cubes noted? Y/N*.

**Expected result:** Baseline captured so you can prove improvement after configuration.

**If it fails:** If the app has zero accounts, run `Aggregate MNB-IT-Access` first (Lesson 09/16).

### Task 2 — Choose and document correlation keys

Enterprises that skip this step end up with silent UI experiments and no standard. Write the hierarchy first; configure second.

1. Confirm HR identities expose `userId` and `email` (Lesson 05 schema).
2. Confirm IT Access schema exposes `employeeId` and `email`.
3. Write Meridian standard:

```text
MNB-IT-Access correlation order:
1) account.employeeId → identity.userId
2) account.email → identity.email
```

4. Explicitly reject “email only” as the sole enterprise standard (Raj case — Lesson 18).

**Expected result:** Documented key hierarchy before clicking UI.

### Task 3 — Configure correlation on MNB-IT-Access

This is the control configuration examiners will ask to see screenshots of. Keep create-identities disabled — that checkbox is how inventory dumps become fake people.

1. Open `MNB-IT-Access` application configuration → **Correlation** (or Account Correlation / equivalent menu path).
2. Add attribute assignment(s):
   - `employeeId` (application) to `userId` (identity)
   - `email` (application) to `email` (identity)
3. If the UI supports ordered attempts, put **employeeId first**.
4. Ensure “create new identities from unmatched accounts” remains **disabled**.
5. Save.

**Expected result:** Correlation config saved on `MNB-IT-Access` with `employeeId`→`userId` + email mappings.

**If it fails:** Attribute names must match schema exactly—fix typos like `EmployeeId` vs `employeeId`.

### Task 4 — Re-aggregate and refresh

Correlation mappings alone do not rewrite existing Links. You must re-ingest accounts and refresh cubes so the warehouse reflects the new rules.

1. Run Account Aggregation task `Aggregate MNB-IT-Access`.
2. Run `Refresh MNB Identities` (or your standard refresh).
3. Optional: if your build offers a dedicated correlation reprocess, use it—otherwise aggregation + refresh is the lab path.
4. Record task results (accounts scanned, created, updated, errors).

**Expected result:** Tasks succeed; many previously uncorrelated accounts now link to HR cubes.

**If it fails:** Re-check correlation mappings; confirm HR has `userId` populated on identities.

### Task 5 — Verify priya.wire linkage

Priya is the happy-path proof: corporate email, clean employeeId, wire-relevant inventory. If she does not link, stop debugging Raj and fix the configuration.

1. Open identity `priya.wire` (MNB00090).
2. Accounts tab: confirm `MNB-IT-Access` account linked.
3. Entitlements: expect directory/wire-related access from inventory (e.g. ELDAP, WIRE_INIT, ACH_OPS per lab dump)—exact set per `EmployeeData.txt`.
4. Screenshot for binder.

**Expected result:** Priya’s IT inventory account is on her cube—manager-visible access.

**If it fails:** Check her `userId` (HR) / `employeeId` (IT) and `email` on both sides; fix data mismatch only if you introduced one—do not invent HR rows.

### Task 6 — Spot-check jordan.reed

Jordan carries toxic inventory entitlements that later SoD lessons will use. Confirm correlation attached *his* access to *his* cube — not a false merge onto another Reed.

1. Open `jordan.reed`.
2. Confirm IT Access account links and shows toxic inventory entitlements (`SAP_FI`, `AWS_ADMIN`, etc. as present in dump).
3. Note these may **also** exist on platform apps from Lessons 12–13—inventory vs platform can overlap; that is OK for lab learning.

**Expected result:** Jordan linked; toxic entitlements visible for later SoD.

### Task 7 — Inspect remaining uncorrelated accounts

Residuals after a good config should be explainable (vendor mail, typos, missing keys) — not “we never configured correlation.”

1. Return to `MNB-IT-Access` uncorrelated list.
2. Look for `raj.external` / vendor email `raj.contractor@vendor-mail.invalid`.
3. Explain in notebook: email secondary key fails; employeeId should still match **if** configured first—if Raj remains uncorrelated, proceed to Lesson 18 for rule precision and troubleshooting.
4. Capture uncorrelated count **after** config: *After: U=___*.

**Expected result:** Uncorrelated population shrinks; remaining cases are explainable rather than “we never configured correlation.”

**If it fails:** If nothing correlated, mappings are wrong or aggregation did not re-run—do not flip authoritative.

### Task 8 — Control narrative

Write the one-page statement you would hand an examiner. Counts and a Priya screenshot make it evidence; prose alone does not.

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

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “account correlation” and “correlation configuration” for your IIQ version’s application correlation UI and attribute assignment behavior.
- [SailPoint Community (Compass)](https://community.sailpoint.com/) — search “uncorrelated accounts” for practitioner threads on residual metrics and create-identities pitfalls.
- [NIST SP 800-53 Rev. 5 — AC / IA family overview](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — background on account management and identification/authentication controls that examiners map to “owned access.”
- [FFIEC Information Technology Examination Handbook — Information Security](https://ithandbook.ffiec.gov/it-booklets/information-security.aspx) — how banking examiners expect access to be attributable to known individuals.
- [OWASP Identity Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Identity_and_Access_Management_Cheat_Sheet.html) — industry primer on identity lifecycle hygiene, including binding accounts to people.

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
