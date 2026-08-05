# Lesson 232 — Tune Email Templates Live

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~50 minutes  
**Prereq:** Lesson 203  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 49

> **Why (1–2 lines):** Templates are how bank language reaches inboxes — a broken token prints literal `$` garbage in front of the person you're trying to notify.

## What this is

`EmailTemplate` objects are the only thing standing between IIQ's internal event names (`workItemAssignment`, `certificationStart`) and what a Meridian employee actually reads. Stock templates say generic things like "You have a new task"; a bank wants "Meridian National Bank — Access Certification Assigned" with the right footer and no leaked internal jargon. Because Mailpit renders every token exactly as SMTP receives it, this is the fastest way to see whether your substitutions (`$requestee.name`, `$certification.name`) actually resolve or print as literal placeholders.

## Know these

```text
EmailTemplate edit (subject + body tokens) → Save
  → trigger REAL event (not Preview) → Mailpit shows resolved tokens
  → break a token on purpose → re-trigger → Mailpit shows it fail-render
  → fix → re-trigger → resolves again
```

**Wrong way:** Trusting Preview alone — Preview can render correctly while the live token binding at launch time is still broken in that workflow context.

## Intent

- Edit the Access Request or Certification email template with real Meridian wording.
- Trigger the underlying event live rather than using Preview.
- Confirm Mailpit shows the edited subject/body with tokens resolved.
- Break a token deliberately, see it render wrong, then fix it.

## Before you start

- [ ] Lesson 203 Mailpit SMTP settings confirmed working
- [ ] Lesson 226 or 228 pattern available to re-trigger a cert launch
- [ ] Mailpit UI: `http://localhost:8025`
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/232`

## Do this

1. **Setup → Notifications → Email Templates** (or **Global Settings → Email Templates**). Open the template that fires on cert launch — cross-check against Lesson 226's launch mail subject to identify it exactly.  
   **Expect:** Correct template identified, not a similarly-named one.

2. Edit **Subject** to `Meridian National Bank — Access Certification Assigned: $certification.name`; add a footer to **Body**: `Meridian National Bank | Identity & Access | Do not reply to this address.` Save.  
   **Expect:** Template saved with new text.

3. Trigger the real event: generate a small Targeted Certification (Lesson 228's pattern) scoped to one identity, or re-launch a manager cert.  
   **Why:** Preview can render correctly while live token binding is still broken.  
   **Expect:** A real launch, not a Preview click.

4. Open Mailpit; confirm the new subject and footer appear, with `$certification.name` resolved to the actual campaign name.  
   **Expect:** No literal `$` tokens visible.

5. Deliberately break a token — change `$certification.name` to `$certificaton.name` (typo) — save, re-trigger, check Mailpit.  
   **Expect:** Token prints literally or blank instead of the campaign name — proof you can spot broken tokens before shipping.

6. Fix the typo back, re-trigger, confirm it resolves again.  
   **Expect:** Campaign name back to resolving correctly.

7. Delete or revert any throwaway debug templates created while investigating.  
   **Expect:** Pack stays clean for the next lesson.

## If it fails

- **Edited template never fires** — you may be editing a template not actually referenced by this workflow; check the workflow's `Notification`/`sendEmail` step for the exact template name it calls.
- **Token prints as `$null` or blank** — the variable isn't in scope at that step; check the workflow/rule passes that argument, or use a token IIQ guarantees is in scope (`$requestee.name`, `$certification.name`).
- **Mailpit shows old cached content** — Mailpit doesn't cache; you're looking at an older message — sort by newest and recheck the timestamp.

## You are done when

Custom template text is visible in Mailpit with tokens resolved, and you've seen the same token fail-render when broken.

## Control note

- **Control:** Notification content accuracy for governance events.  
- **Owner:** IAM Ops (template content) + Communications/Compliance (wording sign-off).  
- **SLA (lab):** Same session; production template changes typically go through a content review before deployment.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/232/` — before/broken/after Mailpit subject-line screenshots.

## Quick check

1. Why isn't Preview sufficient proof a template works? → Live token binding at launch can differ from Preview's context.  
2. What does a broken token look like in Mailpit? → Literal `$token.name` text or a blank value, not the resolved data.  
3. What should you clean up before leaving this lesson? → Any throwaway debug templates created while investigating.

## Navigate

- Previous: Lesson 231  
- Next: Lesson 233  
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
