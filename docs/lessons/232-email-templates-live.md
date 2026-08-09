# Lesson 232 — Tune Email Templates Live

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~60 minutes  
**Prereq:** Lessons 203, 217, 222, 226  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 49

> **Why:** Templates are how bank language reaches inboxes — a broken token prints literal `$` garbage in front of the person you’re trying to notify. Joiner/leaver “missing mail” is often a missing template step, not broken SMTP.

## What this is

An **EmailTemplate** is the object between IIQ’s internal event (`workItemAssignment`, `certificationStart`, custom workflow `sendEmail`) and what a Meridian employee reads. Stock subjects say “You have a new task”; a bank wants branded wording, correct tokens, and no leaked internal jargon.

Mailpit ([http://localhost:8025](http://localhost:8025)) shows **exactly** what SMTP received — resolved tokens or literal `$placeholders`.

You already proved SMTP in Lesson 203. Gaps you may have noted:

| Lesson | Honest gap |
| --- | --- |
| 217 Joiner | No welcome mail step in `MNB-Workflow-Joiner` |
| 219 Leaver | Termination mail often missing |
| 222 Approvals | Assignment mail depends on template + identity email |

This lesson tunes a **live** certification / work-item template, then optionally closes the joiner welcome gap with a real send (or documents it as still out of band).

Classic 49 taught template tokens; here Preview is not enough — you re-trigger a real event.

## Know these

```text
Identify which EmailTemplate the event calls
  → Edit subject + body (Meridian wording + tokens)
  → Save
  → Trigger REAL event (cert launch / approval / workflow sendEmail)
  → Mailpit: tokens resolved
  → Break a token on purpose → Mailpit shows fail-render
  → Fix → re-trigger → resolves again
```

| Term | Plain English | Meridian example |
| --- | --- | --- |
| **EmailTemplate** | Named subject/body with `$tokens` | Certification assignment mail |
| **Token** | Placeholder replaced at send time | `$certification.name`, `$requestee.name` |
| **Preview** | Editor sandbox render | Can lie vs live workflow context |
| **Live binding** | Variables the workflow actually passes | Why Preview ≠ proof |
| **Welcome / term mail** | Lifecycle notification | Often missing until you add a sendEmail step |

- **Wrong way:** Trusting Preview alone — live token binding can still be broken.
- **Wrong way:** Editing a similarly named template the workflow never calls.
- **Wrong way:** Blaming SMTP (Lesson 203) when the workflow has **no** email step (217/219 gap).

## Intent

- Identify and edit the cert-launch (or work-item assignment) template with Meridian wording.
- Trigger a **real** event; confirm Mailpit shows resolved tokens.
- Break a token deliberately, see fail-render, then fix.
- Close or honestly document the joiner welcome-mail gap from Lesson 217.

## Before you start

- [ ] Lesson 203 Mailpit SMTP confirmed (`mailpit:1025`)
- [ ] Ability to re-trigger a small Targeted or Manager cert (Lesson 226 / 228 pattern)
- [ ] Optional: disposable joiner or `lab.joiner1` if you add welcome mail
- [ ] Mailpit: [http://localhost:8025](http://localhost:8025)
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/232
```

## Do this

### Task 1 — Identify the live template

1. **Setup → Notifications → Email Templates** (or **Global Settings → Email Templates**)
2. Cross-check against a Lesson 226 launch mail subject in Mailpit — open the template whose subject matches
3. Note the exact template **name** (not only display text)

- **Why:** editing the wrong template wastes the whole lesson.
- **Expect:** correct template identified.

Screenshot subject before edit under evidence.

### Task 2 — Edit subject and footer

1. Set **Subject** to something like:

```text
Meridian National Bank — Access Certification Assigned: $certification.name
```

2. Add a **Body** footer:

```text
Meridian National Bank | Identity & Access | Do not reply to this address.
```

3. **Save**

- **Expect:** template saved with new text.

> **Tip:** Keep one known-good token (`$certification.name` or `$requestee.name`) — don’t invent tokens the event never passes.

### Task 3 — Trigger a real event (not Preview)

Generate a **small** Targeted Certification (Lesson 228 pattern: one identity or contractors filter) **or** re-launch a tight Manager cert.

- **Why:** Preview can render correctly while live binding is still broken.
- **Expect:** a real launch, not a Preview click.

### Task 4 — Confirm Mailpit resolves tokens

Open Mailpit; find the newest message.

- **Expect:** new subject + footer; `$certification.name` resolved to the campaign name — **no** literal `$` tokens.

Save before/after subject screenshots.

### Task 5 — Break a token on purpose

1. Change `$certification.name` to `$certificaton.name` (typo)  
2. Save → re-trigger a small cert launch  
3. Check Mailpit  

- **Expect:** token prints literally or blank — proof you can spot broken tokens before shipping.

### Task 6 — Fix and re-prove

Restore the correct token → re-trigger → confirm resolve again.

- **Expect:** campaign name back.

### Task 7 — Close the joiner welcome-mail gap (or document it)

Lesson 217 noted welcome mail as missing. Pick one:

**Option A — Document only (minimum)**

```text
MNB-Workflow-Joiner has no sendEmail / EmailTemplate step.
SMTP (203) is fine; lifecycle welcome is a content/workflow gap, not Mailpit.
```

**Option B — Add a welcome send (stretch)**

1. Create or clone an EmailTemplate e.g. `MNB-Email-Joiner-Welcome` with Meridian wording and `$identity.displayName` / `$identity.name` (use tokens your step can pass)
2. Add a **sendEmail** (or notification) step to `MNB-Workflow-Joiner` **after** Log Joiner, before or after Refresh — wire the template name exactly
3. Hire or manually launch the joiner for a disposable identity
4. Confirm Mailpit shows the welcome message

- **Why:** separates “SMTP broken” from “workflow never sends.”
- **Expect:** either the written gap note, or a Mailpit welcome for a disposable joiner.

> **Watch out:** Do not terminate shared personas to test leaver mail — use disposable ids (Lesson 219).

### Task 8 — Clean up

Revert any throwaway debug templates; leave the Meridian subject/footer if you want them for later certs.

- **Expect:** pack stays clean for Lesson 233+.

## If it fails

| Symptom | Fix |
| --- | --- |
| Edited template never fires | Workflow/notification still points at another template name — match Task 1’s name |
| Token is `$null` / blank | Variable not in scope at that step — use a guaranteed token or pass the arg from the workflow |
| Mailpit shows old content | Sort by newest; check timestamp — Mailpit does not cache |
| Joiner still has no mail after Option B | Confirm sendEmail step saved and workflow re-launched; Create triggers don’t re-fire on old cubes |
| Blaming SMTP | If work-item mail works but joiner doesn’t, the gap is the workflow — not Lesson 203 |

## You are done when

- [ ] Custom template text visible in Mailpit with tokens resolved  
- [ ] You’ve seen the same token fail-render when broken  
- [ ] Joiner welcome gap closed **or** documented as workflow content (not SMTP)  

## Control note

- **Control:** Notification content accuracy for governance + lifecycle events  
- **Owner:** IAM Ops (templates/workflows) + Communications/Compliance (wording)  
- **SLA (lab):** Same session; production template changes usually need content review  
- **Evidence:** `~/iiq-lab-evidence/sandbox/232/` — before/broken/after subjects; welcome gap note or Mailpit welcome  

## Quick check

1. Why isn’t Preview enough? → Live token binding can differ from Preview’s context  
2. What does a broken token look like in Mailpit? → Literal `$token` or blank  
3. Why did Lesson 217 often show no welcome mail? → No email step in the joiner workflow — not necessarily SMTP  
4. What should you clean up before leaving? → Throwaway debug templates  

## Feedback

Could you tell SMTP failure apart from “workflow never sends” in one sentence? If a token stayed blank after Task 6, note which event you triggered and which template name the workflow actually references.

## Navigate

- Previous: [Lesson 231](231-audit-reports-live.md)
- Next: [Lesson 233](233-aggregation-strategy-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
