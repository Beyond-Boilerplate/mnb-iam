# Lesson 225 — Work Violations & Mitigations

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~70 minutes  
**Prereq:** Lesson 224  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 41–42

> **Why:** A violation with no owner, no expiry, and no evidence is indistinguishable from a violation nobody ever looked at.

## What this is

Lesson 224 proved **detection**: Marcus holding both wire powers creates a Policy Violation.

Detection alone is not a control. Compliance needs a **disposition lifecycle**:

| Disposition | Meaning | Typical when |
| --- | --- | --- |
| **Open** | Found; nobody finished deciding | After scan |
| **Mitigate** | Temporary waiver — ticket + **expiry** | Short coverage gap |
| **Remediate** | Remove the conflicting access | Permanent fix |
| **Reopened** | Mitigation expired; conflict still true | After expiry + re-scan |

**Risk / severity (why some violations jump the queue):** SoD policies can carry a higher **risk** weight than soft rules (e.g. unused-account hygiene). Wire dual-control is a **high-risk** finding — treat it ahead of cosmetic policy noise. In the queue UI, sort/filter by risk or policy name so Marcus’s wire conflict isn’t buried under lower-severity rows.

**Identity / entitlement risk scores** (classic 42) are a **prioritization signal** for certs, huddles, and which violations you open first. They do **not** auto-revoke, replace SoD evaluation, or delay a leaver SLA while you “wait for score refresh.”

You will take Marcus’s SoD violation through: find in the **queue** → mitigate with ticket + short expiry → see it in a report → let expiry lapse → confirm it reopens → make a final decision.

Classic 41–42 taught violation handling and risk; here expiry must be observable in-session (minutes, not 90 days).

## Know these

```text
Open violation (Policy Violations queue — not only on the cube)
  → Mitigate (ticket id + short expiry + rationale)
       OR Remediate (remove access outright)
  → visible in report/analytics while mitigated
  → expiry lapses → re-scan / re-eval → reopens
  → final decision: remediate for real, or re-mitigate with fresh ticket
```

| Term | Plain English |
| --- | --- |
| **Policy Violation** | IIQ record that an identity broke a Policy constraint |
| **Queue** | Compliance work list across *all* identities |
| **Mitigation** | Time-boxed acceptance with owner + ticket |
| **Remediation** | Remove the conflicting entitlement/role |
| **Expiry** | When the waiver dies — must reopen if conflict remains |
| **Risk / severity** | How urgent the finding is — Wire SoD outranks soft hygiene |
| **Identity risk score** | Composite priority number from critical ents + open violations (+ unused signals) |

```text
Critical ents + open SoD violations
        │
        ▼
 Identity risk score (Refresh / risk config)
        │
        ├──► Sort Policy Violations / cert work items
        ├──► Weekly IAM huddle top-N
        └──► NOT auto-revoke / NOT SoD replacement / NOT leaver delay
```

| Scores **should** | Scores must **never** |
| --- | --- |
| Jump Wire SoD ahead of soft hygiene | Auto-revoke or auto-disable on threshold |
| Scope targeted certs when a population’s median spikes | Replace SoD policy evaluation (Lesson 224) |
| Feed “who do we look at first?” | Delay terminate/disable while waiting for refresh |

- **Wrong way:** Mitigating with no ticket id or rationale — looks like an unaddressed violation to an auditor.
- **Wrong way:** Open-ended mitigation with no expiry — a permanent waiver in disguise.
- **Wrong way:** Working only from Marcus’s cube — real analysts work the queue.
- **Wrong way:** Assuming expiry “just works” without a re-evaluation scan/task.
- **Wrong way:** Treating every open violation as equal priority — high-risk SoD waits behind noise.
- **Wrong way:** Wiring automation that revokes when score crosses a number — false positives break the bank (classic 42).

## Intent

- Find the open violation from Lesson 224 in the Policy Violations queue.
- Mitigate with ticket id, rationale, and a short observable expiry.
- Confirm the mitigated row appears in a report with metadata intact.
- Let expiry lapse; prove reopen; record an explicit final decision.

## Before you start

- [ ] Lesson 224 SoD policy active; violation reproducible on `marcus.approve`
- [ ] Marcus can hold both `WIRE_APPR` and `MNB-Bundle-Wire-Initiator` again if you cleared him
- [ ] Access to **Setup → Policy Violations** (spadmin or compliance capability)
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/225
```

## Do this

### Task 1 — Recreate the violation if needed

If Lesson 224 already remediated Marcus:

1. Re-assign `MNB-Bundle-Wire-Initiator` to `marcus.approve`  
2. Re-run policy scan / Identity Refresh with check policies  

- **Expect:** a fresh, **open** violation exists.

### Task 2 — Find it from the queue (not the cube)

1. **Setup → Policy Violations** (wording may vary slightly by build)  
2. Filter to open / unmitigated  
3. Sort or filter so **high-risk / SOD** rows surface first if your build shows risk  
4. Optionally open Marcus’s identity risk / score view (if present) — note that a high score **prioritizes** review; it does **not** remove access by itself  
5. Find the row for Marcus + Wire dual-control policy  

- **Why:** a real compliance analyst works from the queue, not persona-by-persona — and prioritizes by risk/score without treating the number as enforcement.
- **Expect:** violation found from the queue view alone; you can say why it outranks a soft finding; you can state “score ≠ revoke.”

Screenshot under evidence.

> **Tip:** If the cube shows it but the queue doesn’t, check status filters (“open only”) and whether you’re on an identity-risk view vs dedicated Policy Violations.

### Task 3 — Mitigate (not Remediate) with ticket + short expiry

Choose **Mitigate**.

Fill:

| Field | Lab value |
| --- | --- |
| Ticket | `INC-LAB-224` |
| Expiry | A few **minutes** from now (watchable) |
| Comment / rationale | See Task 4 |

- **Why:** short window lets you watch expiry in this lesson (same idea as break-glass sunset).
- **Expect:** mitigation saved with ticket id and expiry.

> **Watch out:** Remediate first would remove access and skip the waiver drill — use Mitigate here.

### Task 4 — Write a real rationale

Comment example:

```text
Wire desk coverage gap during Q3 rotation — approved by Sanjay Kapoor,
expires end of shift. Dual control accepted temporarily with monitoring.
```

- **Why:** ticket number alone isn’t enough — auditors need *why*.
- **Expect:** rationale present, not just `INC-LAB-224`.

### Task 5 — Confirm mitigated status

Re-open the violation. Confirm status is **mitigated** (not open, not closed/resolved) with ticket + expiry visible.

- **Expect:** status distinct from both “open” and “closed.”

### Task 6 — Prove it in a report / analytics view

Pull the Policy Violation report or analytics dashboard. Confirm this mitigated violation appears with:

- Ticket id  
- Expiry  
- Identity (Marcus)  
- Policy name  

- **Why:** this is the artifact when proving a violation was opened, owned, and tracked.
- **Expect:** row present with full metadata — drill into detail if the summary view hides fields.

Export or screenshot under evidence.

### Task 7 — Let expiry lapse and re-evaluate

1. Wait until expiry passes  
2. Re-run policy scan / Identity Refresh with check policies  
   (or the scheduled task your build uses for expired-mitigation re-evaluation)  

- **Expect:** violation flips back to **open**. If it stays mitigated forever, expiry enforces nothing.

Screenshot reopen proof.

### Task 8 — Final decision

Pick explicitly:

| Decision | Action |
| --- | --- |
| **Remediate** | Remove `MNB-Bundle-Wire-Initiator` from Marcus; refresh with provisioning; re-scan → clear |
| **Re-mitigate** | New ticket + longer justified window + new rationale |

- **Expect:** an explicit decision recorded — not left open by inaction.

If you remediate, confirm live entitlement cleanup (provision + re-agg) like Lessons 218/223.

## If it fails

| Symptom | Fix |
| --- | --- |
| On cube but not in queue | Check identity-risk vs Policy Violations views; status filters |
| Mitigate greyed out | Need compliance capability / spadmin |
| Expiry doesn’t reopen | Trigger re-evaluation scan/task after expiry — don’t wait for magic |
| Report missing ticket/expiry | Open detail from the report, not summary-only |
| Final remediation doesn’t clear live entitlement | Provisioning refresh + re-aggregation |
| No violation to start | Repeat Lesson 224 Tasks 5–6 |

## You are done when

- [ ] Marcus’s SoD violation went through mitigate-with-expiry  
- [ ] Visible with ticket id in a report while mitigated  
- [ ] Reopened automatically after expiry + re-scan  
- [ ] Explicit final decision recorded  

## Control note

- **Control:** SoD violation disposition and time-boxed waivers  
- **Owner:** Compliance/SoD reviewers + Treasury Controls  
- **SLA (lab):** Minutes; production mitigation windows are typically 30–90 days with mandatory re-review  
- **Evidence:** `~/iiq-lab-evidence/sandbox/225/` — mitigation ticket/expiry, report export, reopen proof, final decision  

## Quick check

1. Why Mitigate instead of Remediate first? → Practice a time-boxed waiver instead of removing access outright  
2. What proves expiry isn’t cosmetic? → Violation reopens once the window lapses and you re-evaluate  
3. What makes a mitigation audit-worthy? → Ticket id, expiry, and written rationale  
4. Where should analysts work from? → The Policy Violations queue, not only identity cubes  
5. Why does Wire dual-control jump the queue? → Higher risk / severity than soft hygiene findings  
6. Do risk scores auto-revoke? → **No** — they prioritize certs/monitoring; humans (or SoD/leaver controls) enforce  

## Feedback

Could you explain mitigate vs remediate without looking back? If expiry didn’t reopen the violation, note whether you re-ran the scan after the clock — expired status alone often isn’t enough.

Name one reason Wire SoD should outrank a low-severity policy row before you start certs in Lesson 226. Could you explain “scores prioritize, never auto-revoke” in one sentence for an examiner?

## Navigate

- Previous: [Lesson 224](224-sod-wire-live.md)
- Next: [Lesson 226](226-manager-cert-mail.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
