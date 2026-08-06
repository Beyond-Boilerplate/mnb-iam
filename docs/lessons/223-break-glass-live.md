# Lesson 223 — Break-Glass Access Drill

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~50 minutes  
**Prereq:** Lesson 222  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 37

> **Why (1–2 lines):** Emergency access has to be time-boxed and auditable, or "break glass" is just a permanent backdoor with a dramatic name.

## What this is

You can build a break-glass Bundle from scratch or reuse the seeded `MNB-Bundle-BreakGlass-Cloud` if `seed-enterprise.sh` ran. Either way, emergency-access decisions — who can request it, how short-lived it is, who's notified — are what a real bank's security team owns; don't inherit a template unread. You'll force an accelerated approval with an incident reference, schedule revocation, prove Mailpit caught the emergency notification, and confirm access disappears on schedule. **Credential custody** (vault checkout, not Slack/spreadsheet) is Lesson [255](255-privileged-vault-checkout.md) — IIQ grants membership; PAM holds the password.

## Know these

```text
Request (INC-xxx justification, not business language)
  → accelerated approval (skip or fast-track the 2-step chain)
  → provision on live target → Mailpit shows INC reference
  → sunset window elapses → deliberate revoke → re-aggregate confirms gone
```

**Wrong way:** Approving break-glass through the exact same unhurried Manager→Owner chain as routine access — speed with compensating controls elsewhere is the point; a slow "emergency" approval isn't one.

## Intent

- Build a break-glass Bundle distinct from normal access roles — short-lived by design.
- Request it with an incident id, routed through an accelerated but auditable approval.
- Confirm the entitlement provisions on a live target immediately after approval.
- Schedule and verify automatic revocation; confirm Mailpit shows both grant and emergency-path notification.

## Before you start

- [ ] Lesson 222's approval workflow pattern understood (for comparison)
- [ ] A disposable persona available (`lab.joiner1`/`lab.leaver1` or fresh)
- [ ] Mailpit UI: `http://localhost:8025`
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/223`

## Do this

1. Create `it`-type Bundle `MNB-Bundle-BreakGlass-CoreBanking`, requestable, mapped to a real live entitlement not otherwise gated behind normal approval — e.g. elevated `MNB-CoreBanking` access, or reuse `WIRE_APPR`. Description: "Time-boxed emergency access — INC required, auto-revoke."  
   **Expect:** Role exists, requestable, mapped to a live target entitlement.

2. Pick a short, observable sunset window (5–10 minutes) instead of a real-world hours-long one.  
   **Why:** You need to watch the revocation happen live within this lesson.  
   **Expect:** Window documented.

3. Submit the request as a disposable persona with justification `INC-LAB-001 — emergency Core Banking access during on-call incident` instead of normal business language.  
   **Expect:** Request created with the incident reference in the justification field.

4. Route it through an accelerated approval — a dedicated single-step emergency approval, or approve both Manager and Owner steps back-to-back immediately if reusing Lesson 222's chain.  
   **Expect:** Approved fast, deliberately skipping the routine two-step pace.

5. Check Mailpit for a notification distinguishable from routine access — the incident reference should be visible in subject/body.  
   **Expect:** `INC-LAB-001` visible in the mail, not generic wording.

6. Re-aggregate the relevant application and confirm the entitlement provisioned immediately.  
   **Expect:** Account link shows the new entitlement right away.

7. Schedule the revoke: a scheduled task/certification tied to your sunset window, or a manual role removal you trigger yourself once the window elapses.  
   **Expect:** A deliberate, planned removal — not "someone eventually notices."

8. When the window elapses, execute the revocation and re-aggregate again.  
   **Expect:** Entitlement gone from the live account.

9. Pull the `IdentityRequest` audit trail (same technique as Lesson 222) and confirm it shows incident reference, accelerated approval timestamp, provisioning timestamp, and revocation timestamp in one record.  
   **Expect:** Full timeline in a single place you can hand to incident response.

## If it fails

- **No accelerated approval path exists** — acceptable if you approve both steps immediately yourself; the required proof is short sunset + revocation, not necessarily a distinct workflow object.
- **Entitlement provisions but you can't find it again to revoke** — you didn't capture the `IdentityRequest` id or account link at grant time; check the target application's account list directly.
- **Revocation removes role assignment but live entitlement stays** — same class as Lesson 218's mover cleanup: role removal computes a plan, a provisioning-enabled refresh plus re-aggregation is what actually clears the target.
- **Mailpit shows a grant indistinguishable from routine access** — if the incident reference doesn't appear anywhere in the mail, this break-glass path isn't auditable; fix the request justification/template before calling this done.

## You are done when

You've granted a break-glass entitlement with an incident reference, confirmed a Mailpit notification tied to that incident, watched the entitlement provision live, and executed/confirmed its revocation within your chosen sunset window.

## Control note

- **Control:** Emergency (break-glass) access with mandatory time-box.  
- **Owner:** Security Ops (approval) + IAM Ops (revocation enforcement).  
- **SLA (lab):** 5–10 minute sunset; production windows are typically 4–24 hours with mandatory review.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/223/` — request justification, Mailpit incident mail, grant/revoke timestamps.

## Quick check

1. What must the justification field contain instead of business language? → An incident reference (e.g. `INC-LAB-001`).  
2. What proves this wasn't just fast routine access? → The incident id visible in the Mailpit notification.  
3. What does IIQ *not* own in break-glass? → Credential custody — that's PAM/vault (Lesson 255).

## Navigate

- Previous: Lesson 222  
- Next: Lesson 224  
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md) · Vault checkout: [255](255-privileged-vault-checkout.md)
