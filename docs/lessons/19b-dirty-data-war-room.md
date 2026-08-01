# Lesson 19b — Dirty Data War Room

**Level:** Intermediate  
**Track:** Correlation  
**Time:** 60–75 minutes  
**Prereq:** Lessons 17–19; `MNB-IT-Access` / `MNB-AWS-Cloud` aggregated  
**Lab data:** `lab-data/scenarios/bad-row/*`; IT/AWS CSVs; uncorrelated account views  
**Path:** Core (01–50)

---

## Learning objectives

You will be able to:

- Run an incident-style war room that combines uncorrelated accounts + orphan risk in one narrative
- Classify findings: correlate / disable / exception / data-fix (HR)
- Use `apply-bad-row.sh` style diagnosis to refuse poisoned HR while still remediating IT orphans
- Produce a single Meridian incident packet (roster, owners, SLA, evidence)
- Explain why create-identities on targets is never the cleanup button

---

## Why this matters

**Business.** Real weeks do not separate “Lesson 19 uncorrelated” from “Lesson 20 orphans.” A Sev-2 drops: *privileged AWS accounts with no owner, plus HR sent a broken delta.* Meridian needs one incident commander story.

**Control / audit.** Examiners sample the uncorrelated queue and terminated-with-access reports together. Control owners: IAM Ops (queue), HR Ops (keys), app owners (disable). This lesson forces that collaboration in the lab.

---

## Concepts

### One incident, two queues

| Queue | Question | Primary persona examples |
| --- | --- | --- |
| Uncorrelated accounts | Which account has no cube? | Vendor-mail AWS, typo `employeeId` |
| Orphan / dormant | Which cube is inactive but still privileged? | `samir.hassan` residuals (before rehire) |
| Poisoned HR intake | Which delta must we refuse? | `bad-row` pack |

### Classification board (reuse Lesson 19)

| Class | When | Owner |
| --- | --- | --- |
| Correlate | Associate key proves the human | IAM Ops |
| Disable | Privileged + no HR human | App owner + IAM |
| Exception | Service account with sponsor + review date | App owner |
| Data-fix | Person exists; `userId`/`employeeId` drifted | HR Ops |

### Wrong way

Enable create-identities on `MNB-AWS-Cloud` to “clear the queue,” or upsert a bad HR row to “make the joiner appear.” Both create ghost people and exam findings.

```
War room clock starts
    │
    ├── Diagnose inbound HR deltas (refuse bad-row)
    ├── Export uncorrelated privileged accounts
    ├── Cross-check terminated / inactive cubes with access
    └── File tickets: Correlate / Disable / Exception / Data-fix
```

---

## How it works

| Artifact | Contents |
| --- | --- |
| `war-room-roster.csv` (binder) | Account, app, ents, class, owner, due |
| Diagnose log | Terminal output from `--diagnose` |
| Cube screenshots | Before/after for one correlate + one disable decision |
| Residual risk | What remains open at T+24h |

---

## Before you start

- [ ] Lessons 17–19 correlation config in place (`employeeId` → `userId`)
- [ ] AWS and IT apps aggregated at least once
- [ ] Bad-row scenarios present under `lab-data/scenarios/bad-row/`
- [ ] Do not wipe shared lab cubes without a restore plan

---

## Lab procedure

### Task 1 — Open the war room with a scenario statement

Write the incident header:

```text
INC-MNB-DATA-19b
Title: Privileged uncorrelated + HR delta quality failure
Commander: <you>
Scribe: binder
SLA: classify all critical ents in 2 lab hours; no poisoned HR apply
```

**Expected result:** Incident header in binder before clicking IIQ.

### Task 2 — Refuse poisoned HR (5 minutes)

```bash
./tools/lab/scripts/scenarios/apply-bad-row.sh
./tools/lab/scripts/scenarios/apply-hr-delta.sh --diagnose \
  lab-data/scenarios/bad-row/hr-delta-shifted-columns.csv
```

1. Paste FINDINGS into the incident packet.  
2. Tickets to HR Ops: blank `userId`, status contradiction, column shift.  
3. Confirm you did **not** upsert.

**Expected result:** “HR intake blocked” section with diagnose evidence.

### Task 3 — Uncorrelated privileged sweep

1. Open uncorrelated accounts for `MNB-AWS-Cloud` and `MNB-IT-Access`.  
2. Build a roster of at least 3 accounts (or all if fewer). Prefer anything with `AWS_ADMIN` / wire-like ents.  
3. For each, attempt associate-key match to HR (`employeeId` ↔ `userId`).  
4. Classify using the board (include `raj.external` vendor-mail case).

**Expected result:** Roster table with class + owner per row.

**If it fails:** If everything is correlated, invent a controlled scratch: copy one CSV row with a typo `employeeId` into a personal scratch app—or walk the classification hypothetically and mark “lab already clean.”

### Task 4 — Orphan intersection

1. Open `samir.hassan` (terminated in baseline) **or** another inactive cube with Links.  
2. List residual entitlements still attached.  
3. Add at least one orphan row to the same roster (`Disable` / leaver residual).  
4. Note: if you already ran `apply-rehire.sh` for Samir, use another terminated persona (`anita.ross`, …) or document rehire state.

**Expected result:** Roster contains both uncorrelated and orphan rows—one incident narrative.

### Task 5 — Execute one safe remediation

Pick **one**:

- **Correlate** a clearly matched account (document proof: `employeeId`=`userId`), or  
- **Ticket Disable** for a privileged orphan with owner `christopher.hayes` / app owner, or  
- **Exception** for a service-looking account with 30-day review.

Do not mass-delete. Capture before/after.

**Expected result:** One completed remediation action + evidence.

### Task 6 — Close the war room

Write residual risk:

```text
Open items: …
Accepted risk: …
Next review: …
```

---

## Acceptance criteria

- [ ] Incident header + diagnose evidence (no bad upsert)  
- [ ] Roster with ≥3 rows spanning uncorrelated and orphan thinking  
- [ ] One remediation executed or formally ticketed  
- [ ] Residual risk paragraph  

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Empty uncorrelated | Correlation already strong | Use scratch typo or hypothetical rows |
| Raj missing | AWS not aggregated | Aggregate MNB-AWS-Cloud |
| Tempted to create-identities | Queue pressure | Re-read Wrong way |

---

## Training binder evidence

1. Diagnose terminal output  
2. Roster table  
3. One remediation screenshot  
4. Residual risk closeout  

**Control owner:** IAM Operations (+ HR Ops for data-fix)  
**Examiner question:** “Show a privileged account with no owner and what you did in 24 hours.”

---

## Knowledge check

1. Why is create-identities on AWS the wrong cleanup?  
2. What class is “HR has the person but keys drifted”?  
3. Why include orphans in an uncorrelated war room?  
4. What does a column-shifted HR file do to managersAssociateID?

### Answers

1. It mints privileged ghost cubes outside HR authority.  
2. Data-fix (HR Ops).  
3. Same exam narrative: access without a living control relationship.  
4. Silently corrupts hierarchy and approvals.

---

## Further reading

- Lessons 18–20  
- [`lab-data/scenarios/README.md`](../../lab-data/scenarios/README.md)  
- [SailPoint docs](https://documentation.sailpoint.com/) — search “uncorrelated accounts”

---

## Stretch lab

Apply `apply-rehire.sh` for Samir in a sandbox copy of HR, aggregate, and document how a rehire changes the orphan story (residuals vs clean rehire).

---

## Summary

- Dirty data is an incident, not two disconnected tutorials.  
- Refuse poisoned HR; classify privileged leftovers; prove one fix.  
- Create-identities on targets is never the broom.

**Previous:** [Lesson 19 — Uncorrelated Account Remediation](19-uncorrelated-remediation.md)  
**Next:** [Lesson 20 — Orphan & Dormant Access Hunting](20-orphan-dormant-hunting.md)
