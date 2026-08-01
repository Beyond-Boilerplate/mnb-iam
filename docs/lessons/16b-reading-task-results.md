# Lesson 16b — Reading Task Results & Early Provisioning Signals

**Level:** Intermediate  
**Track:** Applications  
**Time:** 40–55 minutes  
**Prereq:** Lesson 16 (multi-app strategy); mid-16 checkpoint recommended  
**Lab data:** Task Results from Aggregate/Refresh; optional IdentityRequest if LCM already used  
**Path:** Core (01–50)

---

## Learning objectives

You will be able to:

- Read an Aggregate and a Refresh Task Result like an on-call engineer
- Explain what “accounts scanned / created / updated / failures” imply for Meridian
- Locate where provisioning outcomes show up later (IdentityRequest / plan)—even if your lab has not provisioned yet
- Write a mini debug playbook for “aggregation said success but the cube looks wrong”
- Connect Task Result literacy to Lesson 47 without waiting until Ops week

---

## Why this matters

**Business.** After Lesson 16 you run a factory: HR → apps → refresh. When `priya.wire` is missing Wire Portal or `nina.joiner` has no cube, leadership does not want a lecture on connectors—they want the Task Result line that proves where the pipeline broke.

**Control / audit.** Examiners and hiring managers ask: *Can you prove the job ran and what it did?* Green UI tiles are not evidence. Task Results are. Lesson 47 deepens provisioning plans; this lesson installs the reading skill on the critical path.

---

## Concepts

### Aggregation result vs refresh result

| Task type | Proves | Does not prove |
| --- | --- | --- |
| Account Aggregation | File/API was read; accounts created/updated/unchanged | Roles assigned; manager hierarchy fixed |
| Refresh MNB Attributes | Link → identity promotion ran | Target apps were provisioned |
| Refresh MNB Roles | Assignment rules evaluated | Entitlements removed on the target |

### “Success” with zero updates is still a signal

Zero created/updated can mean “feed unchanged” **or** “wrong file path that still opens yesterday’s copy,” **or** “filter excluded everyone.” Always pair counters with a spot-check persona (`helen.ross`, `amelia.brooks`).

### Provisioning preview (forward link)

A **provisioning plan** is the structured create/modify/disable list IIQ will execute. You will induce safe failures in Lesson 47. For now, know the chain:

```
Trigger (request / cert / leaver)
   → IdentityRequest
   → Provisioning plan
   → Connector / Task Result
   → Re-aggregate to prove target state
```

If your lab has no IdentityRequest yet, still open the menu path and note “none yet — expected before Lesson 35.”

---

## How it works

```
Aggregate MNB-HR Task Result
        │  counters + errors
        ▼
Aggregate app tasks (IT / Wire / …)
        │
        ▼
Refresh MNB Attributes / Managers / Roles
        │
        ▼
Spot-check personas on cubes
        │
        └── Optional: IdentityRequest → plan (Lesson 35+/47)
```

---

## Before you start

- [ ] Apps from Lessons 09–16 exist (at least `MNB-HR` + `MNB-IT-Access`)
- [ ] You can open Monitor → Task Results
- [ ] Notebook for counters

---

## Lab procedure

### Task 1 — Read the latest HR aggregation result

1. Open Task Results → find `Aggregate MNB-HR` (or your HR aggregate name).
2. Record: status, start/end, accounts scanned/created/updated/failures.
3. Copy the first warning/error line if any (or write “none”).
4. Spot-check Identity Warehouse for `helen.ross` and `amelia.brooks`.

**Expected result:** Binder table of counters + two personas confirmed.

**If it fails:** Run Aggregate MNB-HR once, then re-open the new result.

### Task 2 — Read a non-HR aggregation result

> **Counters vs cubes.** Target aggregates should show accounts/entitlements **created/updated**, not a spike of new identities. “Success” does not mean every HR cube now shows that app—correlation is Lessons 17–18. Prove accounts under **Application → Accounts** if a persona cube looks bare.

1. Open the latest `Aggregate MNB-IT-Access` (or Core/Wire if IT missing).
2. Compare counters to HR—apps usually should not create identities (`Identities created` ≈ 0).
3. Note any failures tied to path or schema.
4. If `Identities created` > 0 on a target, flag create-identities / authoritative misconfig (Lessons 09–15).

**Expected result:** Written contrast: HR may create identities; targets should not. Cube Accounts tabs may still look incomplete.

### Task 3 — Read a refresh result

1. Open `Refresh MNB Attributes` (or your split refresh).
2. Confirm it completed after the aggregates in your runbook (Lesson 08 order).
3. On `sofia.torres`, confirm `exceptions` visibility if mapped (Lesson 05)—refresh is how LOA becomes searchable.

**Expected result:** Refresh timestamp noted after aggregates; one promoted attribute checked.

### Task 4 — Mini playbook: success but wrong cube

Write and keep this playbook (reuse in Lesson 47):

```text
1. Task Result success? counters? (Identities created on a target?)
2. Right file path / app? (Docker: /opt/iiq-lab-data/… not host Mac path)
3. Schema attribute present on Link / Application → Accounts?
4. Refresh MNB Attributes after aggregate?
5. Correlation (targets) vs authoritative create (HR only)?
   — Missing app on HR cube ≠ aggregate failed if app Accounts has the row
```

Walk one persona through the five questions.

### Task 5 — Provisioning signal recon

1. Navigate to Identity Requests / Work Items (or equivalent menu path).
2. If empty, screenshot empty state and label “pre-request track.”
3. If a request exists from exploration, open it and note whether a provisioning plan/status section is visible—do not force a failure yet (Lesson 47).

**Expected result:** You know where plans will appear later.

---

## Acceptance criteria

- [ ] HR + one app Task Result counters recorded  
- [ ] Refresh result reviewed  
- [ ] Five-line “success but wrong cube” playbook written  
- [ ] IdentityRequest menu path located (empty OK)

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No results | Tasks never executed | Run Aggregate + Refresh once |
| Refresh before aggregate | Runbook inverted | Re-run in Lesson 08 order |
| Persona missing attrs | Maps not promoted | Lesson 05 + Refresh MNB Attributes |
| Target success but empty HR cube Accounts | Correlation deferred | Check Application → Accounts; Lessons 17–18 |
| Target Identities created > 0 | Create-identities ON | Disable; document orphans for Lesson 19 |

---

## Training binder evidence

1. Two Task Result screenshots (Aggregate + Refresh)  
2. Playbook text  
3. Persona spot-check notes  

**Control owner:** IAM Operations  
**Examiner question:** “Prove last night’s HR job ran and what it changed.”

---

## Knowledge check

1. Does Aggregate success prove birthright assignment?  
2. Why can “0 updated” still be a problem?  
3. Where do provisioning plans show up for a request?  
4. Which refresh promotes `exceptions=LOA` onto the cube?

### Answers

1. No—roles need Refresh MNB Roles / assignment evaluation.  
2. Wrong/stale file, filters, or silent no-op.  
3. IdentityRequest / provisioning UI (Lesson 35+/47).  
4. Refresh MNB Attributes after HR aggregate (with schema maps).

---

## Further reading

- [SailPoint IdentityIQ docs](https://documentation.sailpoint.com/) — search “Task Result” and “Provisioning plan.”  
- Lesson 47 — full induce-failure lab  
- Lesson 08 — runbook order  

---

## Stretch lab

After Lesson 35, return here and attach one IdentityRequest screenshot to this binder page—close the loop early.

---

## Summary

- Task Results are the pipeline’s evidence.  
- Counters need persona spot-checks.  
- Provisioning literacy starts now; deep failure labs come in Lesson 47.

**Previous:** [Mid-capstone — Apps](mid-16-apps-capstone.md) · [Lesson 16](16-multi-app-aggregation-strategy.md)  
**Next:** [Lesson 17 — Account Correlation Basics](17-correlation-basics.md)
