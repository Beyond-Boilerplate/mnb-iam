# Lesson 225 — Work Violations & Mitigations

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~50 minutes  
**Prereq:** Lesson 224  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 41–42

> **Why (1–2 lines):** A violation with no owner, no expiry, and no evidence is indistinguishable from a violation nobody ever looked at.

## What this is

A Policy Violation without a lifecycle is just a flag that sits there forever. This lesson takes the live violation from Lesson 224 (Marcus holding both `WIRE_INIT` and `WIRE_APPR`) through the full disposition path: assign, decide (mitigate vs. remediate), attach a ticket and expiry, confirm it surfaces in reporting while active, then let the mitigation expire and confirm it resurfaces for a real decision instead of quietly disappearing. Lesson 224 proved detection; this proves disposition is real and time-bound.

## Know these

```text
Open violation (queue-level, not just on the cube)
  → Mitigate (ticket id + short expiry) or Remediate (remove access outright)
  → visible in report/analytics while active
  → expiry lapses → re-scan → reopens automatically
  → final decision: remediate for real, or re-mitigate with justification
```

**Wrong way:** Mitigating with no ticket id or rationale — indistinguishable from an unaddressed violation to an auditor.

## Intent

- Find the open violation from Lesson 224 in the Policy Violations queue, not just on Marcus's cube.
- Mitigate with a ticket id and a short, observable expiry rather than an open-ended waiver.
- Confirm the mitigated violation is visible in a report/analytics view while active.
- Let the mitigation expire and confirm it returns to open — proving expiry isn't cosmetic.

## Before you start

- [ ] Lesson 224's SoD policy active and violation reproducible
- [ ] `marcus.approve` holds `WIRE_APPR` and can be re-assigned `MNB-Bundle-Wire-Initiator`
- [ ] Access to **Setup → Policy Violations** queue (spadmin or compliance capability)
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/225`

## Do this

1. If Lesson 224's violation was already resolved, re-create it: assign `MNB-Bundle-Wire-Initiator` to `marcus.approve` again, then re-run the policy scan.  
   **Expect:** A fresh, open violation exists.

2. Open **Setup → Policy Violations**, filter to open/unmitigated, find the one referencing `MNB-Policy-SOD-Wire-DualControl` for Marcus.  
   **Why:** A real compliance analyst works from the queue, not persona-by-persona.  
   **Expect:** Violation found from the queue view alone.

3. Choose **Mitigate** (not Remediate — remediation removes access, defeating this drill's purpose). Attach a ticket reference (`INC-LAB-224`) and a short, observable expiry (a few minutes out).  
   **Why:** Short window lets you watch it lapse within this lesson, same reasoning as Lesson 223.  
   **Expect:** Mitigation saved with ticket id and expiry.

4. Confirm the mitigation comment captures *why* this is acceptable short-term (e.g. "Wire desk coverage gap during Q3 rotation — approved by Sanjay Kapoor, expires end of shift").  
   **Expect:** Rationale present, not just a ticket number.

5. Confirm the violation now shows **mitigated** (not resolved/closed) with ticket id and expiry visible.  
   **Expect:** Status distinct from both "open" and "closed."

6. Pull the Policy Violation report or analytics dashboard and confirm this mitigated violation appears with its ticket id and expiry intact.  
   **Why:** This is the artifact you need when proving a violation was opened, owned, and closed.  
   **Expect:** Row present with full metadata.

7. Wait for the expiry to elapse, then re-run the policy scan (or the scheduled task your build uses for expired-mitigation re-evaluation).  
   **Expect:** Violation flips back to **open** — if it silently stays mitigated forever, expiry enforces nothing.

8. Make a final decision: remediate for real (remove `MNB-Bundle-Wire-Initiator`) or mitigate again with a longer, justified window and a fresh ticket.  
   **Expect:** An explicit decision recorded — not left open by inaction.

## If it fails

- **Can't find the violation in the queue even though it's on Marcus's cube** — check both "identity risk" and dedicated Policy Violations views; confirm status isn't filtered out by a default "open only" toggle.
- **Mitigate option greyed out** — you're logged in without the capability that owns violation disposition; use spadmin or the compliance capability.
- **Expiry doesn't reopen the violation** — expired-mitigation re-evaluation usually needs a scheduled task; confirm one ran after the expiry, or manually trigger the scan again.
- **Report view doesn't show ticket id/expiry** — you're looking at a summary-only report; drill into violation detail from the report itself.
- **Final remediation doesn't remove the live entitlement** — same as Lessons 218/223: role removal computes a plan, a provisioning-enabled refresh plus re-aggregation is what makes it disappear from the target.

## You are done when

Marcus's SoD violation has gone through a real mitigate-with-expiry cycle, was visible with its ticket id in a report while active, reopened automatically once expired, and ended in an explicit final decision.

## Control note

- **Control:** SoD violation disposition and time-boxed waivers.  
- **Owner:** Compliance/SoD reviewers + Treasury Controls.  
- **SLA (lab):** Minutes; production mitigation windows are typically 30–90 days with mandatory re-review.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/225/` — mitigation ticket/expiry, report export, reopen proof, final decision.

## Quick check

1. Why Mitigate instead of Remediate first? → Practices a time-boxed waiver instead of removing access outright.  
2. What proves expiry isn't cosmetic? → The violation automatically reopens once the window lapses.  
3. What makes a mitigation audit-worthy? → Ticket id, expiry, and a written rationale — not just a status change.

## Navigate

- Previous: Lesson 224  
- Next: Lesson 226  
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
