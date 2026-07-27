# Lesson 21 — Manager Hierarchy & Reassignment

**Level:** Intermediate  
**Track:** Correlation  
**Time:** 45–60 minutes  
**Prereq:** Lesson 20 (orphan/dormant hunting); MNB-HR aggregated with manager identity attribute mapped  
**Lab data:** `~/iiq-lab-data/HRApplications.txt` (source of `managerId`); personas `priya.wire`, `rachel.evans`

---

## Learning objectives

You will be able to:

- Trace a `managerId` chain from HR through the identity cube to a live manager identity
- Explain why empty `managerId` on executives is intentional vs broken mid-chain managers
- Simulate a manager field change, re-aggregate HR, refresh identities, and verify the cube
- Document the certification and approval routing risk when a manager terminates or is wrong
- Define a Meridian fallback certifier policy for broken hierarchy chains
- State the production rule: HR owns managerId; IIQ must not invent permanent overrides

---

## Why this matters

**Business.** Approvals, access reviews, and escalations all assume every identity has a correct manager. At Meridian National Bank, a wrong managerId means wire exceptions for `priya.wire` land on the wrong inbox and quarterly certifications stall while IAM chases “who owns this person?”

**Control / audit.** Examiners ask who reviews employee access. Your answer is “the line manager resolved from authoritative HR.” Broken chains are a control failure, not a UI quirk. Evidence is a verified chain plus a documented fallback when HR data is incomplete — never a silent admin edit on the cube.

---

## Concepts

### How IIQ gets a manager

IdentityIQ resolves **manager** from an identity attribute typically populated from MNB-HR `managerId` (the employeeId of the manager). During aggregation and refresh, that value is correlated to another identity cube. Certifications and many approval schemas use that link for routing work items.

**Real-life Meridian example.** Priya’s HR row carries `managerId=MNB00005`. After Aggregate MNB-HR + Refresh, her cube’s Manager field resolves to `rachel.evans`. Wire Portal access reviews and many approval schemas therefore land with Rachel — the Payments Ops manager who actually owns Priya’s line of work.

### Intentional tops vs broken chains

Empty `managerId` is not automatically a defect. Lab executives and branch tops (Rachel, Sanjay-style leaders) intentionally have empty manager fields — the chain has to end somewhere. A **broken chain** is a non-empty `managerId` that does not resolve to a live identity, or a blank manager on a mid-level specialist who is not an exec. Those break cert launches with “no certifier.”

### Reassignment is an HR event, reflected in IIQ

When someone changes managers, the durable fix is updating HR `managerId`, then running Account Aggregation for MNB-HR and Identity Refresh. Hand-editing the cube’s Manager field “for today’s cert” creates dual sources of truth that diverge again on the next HR load (Lesson 22 hygiene).

### Fallback certifiers for campaign survival

| Situation | Risk | Meridian response |
| --- | --- | --- |
| Manager terminated; HR still points reports at them | Open certs / approvals stall or route to inactive identity | Fallback certifier (Security IAM queue or named successor) + HR correction SLA |
| Non-exec blank managerId | Campaign cannot assign reviewer | Defect to HR; population `MNB-Pop-Broken-Manager-Chain` |
| Admin invents manager in IIQ only | Next HR aggregate overwrites or conflicts | Forbidden — HR owns the value |

The wrong way is to launch a manager certification campaign and “fix” missing reviewers by assigning everything to `spadmin` or Helen Ross permanently. That passes the send button and fails the exam: reviewers must be accountable line management, with a **named temporary fallback** and an HR SLA to repair the chain — not a permanent IAM dump queue.

**Examiner question:** “If Priya’s manager left yesterday, who certifies her Wire Portal access today?” You need a runbook answer before campaign launch.

---

## How it works

```
HR row: priya.wire (MNB00090)
  managerId = MNB00005
       │
       ▼  Aggregate MNB-HR + Refresh
Identity: priya.wire
  manager ──► rachel.evans (MNB00005)
                 managerId = (empty)  ← intentional chain top
```

```
        [empty]
           │
    rachel.evans (MNB00005)
      ┌────┴────┐
priya.wire   marcus.approve  (examples; both managerId=MNB00005)
```

| Term | Meaning at Meridian |
| --- | --- |
| `managerId` | HR employeeId of the person’s manager (authoritative) |
| Manager link | IIQ identity attribute pointing at another Identity |
| Broken chain | Non-empty managerId that does not resolve, or mid-level empty when not an exec |
| Fallback certifier | Named role/person (e.g. Security queue or successor) when chain fails |
| Reassignment | Updating HR managerId then aggregating + refreshing so work items route correctly |

One operational consequence: mover events (Lesson 30) often change **both** department/job **and** managerId. Treating manager as a one-off IIQ edit while HR still points at Rachel means the next nightly Aggregate MNB-HR silently undoes your “fix” — and any open approvals may already have routed wrong.

---

## Before you start

- [ ] IIQ reachable at `http://localhost:8080/identityiq` (homelab URL alternate if configured)
- [ ] Logged in as `spadmin` (or lab admin)
- [ ] `~/iiq-lab-data/HRApplications.txt` present and MNB-HR Account Aggregation has succeeded recently
- [ ] Identity attribute for manager mapped from HR (Lesson 05)
- [ ] Notebook ready for chain diagrams and control statements

---

## Lab procedure

### Task 1 — Locate Priya’s HR managerId

Start in the authoritative file, not the cube. If HR and IIQ disagree later, you need a known baseline from source.

1. Open `~/iiq-lab-data/HRApplications.txt` (or repo `lab-data/HRApplications.txt`).
2. Find the row for `priya.wire` / `MNB00090`.
3. Record: `employeeId`, `managerId`, `departmentCode`, `jobCode`, `jobTitle`.

**Expected result:** Baseline row shows `managerId=MNB00005`, `departmentCode=TRS`, `jobCode=WIR01`, title Wire Specialist.

**If it fails:** Confirm you did not already apply the Lesson 30 mover delta (that file switches manager to `MNB00006`).

### Task 2 — Resolve the manager identity in IIQ

Prove the promotion path worked: HR employeeId of the manager became a live Manager link on the cube.

1. Open **Identities → Identity Warehouse** (or equivalent).
2. Search `priya.wire` and open the cube.
3. Confirm the Manager field resolves to Rachel Evans / `rachel.evans` / `MNB00005`.
4. Open `rachel.evans`. Note whether Manager is empty.

**Expected result:** `priya.wire` → `rachel.evans`. Rachel’s manager is empty (intentional top for this payments branch in lab data).

**If it fails:** Re-run Account Aggregation for MNB-HR and Refresh MNB Identities; verify manager attribute promotion on the application schema.

### Task 3 — Draw a three-node chain (where data allows)

Hierarchy is easier to defend when you can sketch it. Add at least one peer under Rachel so the diagram is not a single edge.

1. From Priya, walk manager → manager’s manager if present.
2. Pick two additional active employees who report to Rachel (search HR for `managerId,MNB00005` or browse cubes).
3. Sketch in your notebook:

```
        [empty]
           │
    rachel.evans (MNB00005)
      ┌────┴────┐
priya.wire   marcus.approve  (examples)
```

**Expected result:** One clear diagram showing Priya under Rachel; at least one peer under the same manager.

**If it fails:** Use `marcus.approve` (also `managerId=MNB00005` in baseline HR) as the second leaf.

### Task 4 — Classify empty managerId

Train yourself to separate intentional tops from data defects before you open tickets against executives.

1. Open HR rows for leaders `MNB00001`–`MNB00008` (or search cubes for empty manager).
2. Mark each empty managerId as **intentional executive top** or **data defect**.
3. Search for any **non-executive** with blank managerId—those are defects.

**Expected result:** Rachel / Sanjay / Emily-style leaders documented as intentional tops; zero unexplained blank managers among specialists.

**If it fails:** Export a population “Active employees, manager is null” and triage each row with HR.

### Task 5 — Simulate a manager change (lab only)

Prove the reassignment path end-to-end: edit HR, aggregate, refresh, verify — then restore so Lesson 30 and peers stay consistent.

1. **Backup** `~/iiq-lab-data/HRApplications.txt`.
2. Change `priya.wire`’s `managerId` temporarily to `MNB00006` (`sanjay.kapoor`)—do **not** change dept/job yet (that is Lesson 30).
3. Run **Account Aggregation** task for **MNB-HR**.
4. Run **Refresh MNB Identities** (or equivalent refresh with manager correlation / identity attributes enabled).
5. Re-open `priya.wire` and confirm Manager is now Sanjay Kapoor.
6. **Restore** baseline `managerId=MNB00005` (or leave changed only if you will continue into Lesson 30 immediately—note the state in your binder).

**Expected result:** After aggregate + refresh, cube manager matches the HR file you just wrote. After restore + re-pipeline, manager returns to Rachel.

**If it fails:** Confirm CSV/TXT column alignment; a shifted column silently breaks managerId.

### Task 6 — Broken-chain risk note for certifications

Tabletop the failure mode before campaigns exist. The control note is the artifact exams want.

1. Write a short control paragraph answering:
   - What happens to open manager certifications if Rachel terminates and HR still points people at her?
   - Who is Meridian’s fallback certifier for Treasury while HR corrects data?
2. Propose: Security IAM queue **or** `rachel.evans` successor / Payments Ops backup—name one primary and one secondary.

**Expected result:** Notebook entry titled `MNB-Ctrl-Manager-Fallback` with primary/secondary and SLA (e.g. HR updates managers **before** termination effective date when possible).

**If it fails:** Treat this as a tabletop—IIQ need not have a live cert campaign yet (campaigns arrive later).

### Task 7 — Do not invent managers in IIQ

Close with the non-negotiable production rule. Temporary cube edits create Lesson 22 flip-flops.

1. Confirm you did **not** hand-edit manager on the cube as a permanent fix.
2. Record the rule: **HR owns managerId; IIQ reflects it.**

**Expected result:** Explicit line in evidence: “No IIQ-only manager overrides in production pattern.”

---

## Acceptance criteria

- [ ] Documented chain: `priya.wire` → `rachel.evans` (MNB00005)
- [ ] Exec empty managerId classified as intentional vs defect
- [ ] Manager change simulation completed (or reasoned skip with instructor approval) with aggregate + refresh
- [ ] Fallback certifier named for broken chains
- [ ] Control statement: HR updates managers before terminations when possible

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Manager blank on Priya | Attribute not promoted / refresh skipped | Map managerId → identity manager; re-aggregate; refresh |
| Manager shows employeeId string only | Correlation to Identity failed | Ensure manager identities exist from HR; check type/format of managerId |
| Wrong manager after restore | Stale HR file or wrong copy path | Confirm IIQ app file path points at `~/iiq-lab-data/` |
| Peer has different manager than HR | Manual cube edit or dual sources | Re-aggregate HR; remove non-authoritative manager sources (Lesson 22) |
| Cert preview shows “no certifier” | Broken chain | Apply fallback population/owner policy before launch |

---

## Training binder evidence

- Screenshot: `priya.wire` identity with Manager = Rachel Evans
- Screenshot: `rachel.evans` with empty manager (annotated “chain top”)
- Hand-drawn or digital hierarchy sketch (3+ nodes)
- Control note `MNB-Ctrl-Manager-Fallback` with primary/secondary and SLA
- Before/after note from managerId simulation (include restore confirmation)

**Control owner:** HR Operations (data) + IAM Engineering (IIQ mapping)  
**Evidence retention:** Keep with correlation track artifacts for exam binder

---

## Knowledge check

1. What HR field drives Meridian’s manager link for `priya.wire`?
2. Why do certifications need accurate managers?
3. Is an empty `managerId` on `rachel.evans` automatically a defect?
4. What two IIQ tasks must run after editing HR managerId?
5. Who should own permanent manager corrections—IIQ admin or HR?

### Answers

1. `managerId` = `MNB00005` (Rachel Evans).
2. Manager certifications and many approvals route to the resolved manager; wrong managers = wrong reviewers and stalled campaigns.
3. No—lab executives/tops intentionally have empty managerId; mid-level blanks are defects.
4. Account Aggregation for MNB-HR, then Refresh MNB Identities (with manager/identity attribute processing enabled).
5. HR owns the authoritative value; IIQ must not permanently invent managers that HR does not know.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “manager correlation,” “identity attributes,” and “certification owner” for hierarchy resolution and fallback patterns.
- [SailPoint Community (Compass)](https://community.sailpoint.com/) — search “broken manager chain” / “fallback certifier” for campaign launch failures peers have hit.
- [NIST SP 800-53 Rev. 5 — AC-5 / AC-6](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — separation of duties and least privilege context for who should review access (line management).
- [FFIEC Information Security Booklet](https://ithandbook.ffiec.gov/it-booklets/information-security.aspx) — expectations that access reviews are performed by accountable management, not orphaned queues.
- [ISACA — Identity and Access Management fundamentals](https://www.isaca.org/resources) — search “access certification” / “manager attestation” for industry framing of review routing.

---

## Stretch lab

- Define a population **MNB-Pop-Broken-Manager-Chain**: active employees where manager is null **and** jobCode is not in the leadership set.
- Draft XML/notes for a certification fallback owner = Security when population matches.
- Tabletop: manager terminates Friday; list Friday/Monday IAM actions before Monday cert send.

---

## Summary

- Manager hierarchy is an operational dependency for approvals and certifications, not a cosmetic field.
- Lab baseline: `priya.wire` → `rachel.evans`; empty manager on Rachel is a chain top.
- Broken chains need HR remediation plus a named fallback certifier—never silent IIQ inventions.

---

**Previous:** [Lesson 20 — Orphan & Dormant Access Hunting](20-orphan-dormant-hunting.md)  
**Next:** [Lesson 22 — Identity Attribute Sync Hygiene](22-attribute-sync-hygiene.md)
