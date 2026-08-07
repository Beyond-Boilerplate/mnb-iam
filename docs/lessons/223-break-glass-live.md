# Lesson 223 — Break-Glass Access Drill

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~65 minutes  
**Prereq:** Lesson 222  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 37

> **Why:** Emergency access has to be time-boxed and auditable, or “break glass” is just a permanent backdoor with a dramatic name.

## What this is

**Break-glass** (also called emergency / fire-call access) is what ops uses when production is on fire at 2 a.m. and waiting for a two-day Manager→Owner chain would make the outage worse.

It is still **governed** access — just with different rules:

| Routine access (Lesson 222) | Break-glass |
| --- | --- |
| Business justification | **Incident id** (`INC-…`) |
| Unhurried Manager → Owner | **Accelerated** approval |
| Long-lived until mover/leaver/cert | **Short sunset** then revoke |
| Looks like normal Mailpit mail | Mail must show the **INC** reference |

You can build a break-glass Bundle from scratch or reuse seeded `MNB-Bundle-BreakGlass-Cloud` if enterprise seed imported it. Either way, **read** the role — don’t inherit a template unread.

**Credential custody** (vault checkout, not Slack passwords) is a later privileged lesson — IIQ grants membership; PAM holds the password.

## Know these

```text
Request (INC-xxx justification — not business prose)
  → accelerated approval (single-step or back-to-back 222 chain)
  → provision on live target
  → Mailpit shows INC reference
  → sunset window (5–10 min in lab)
  → deliberate revoke + provision refresh
  → re-aggregate confirms entitlement gone
  → IdentityRequest timeline: grant → revoke
```

| Term | Plain English |
| --- | --- |
| **Break-glass** | Emergency elevated access with compensating controls |
| **Sunset / time-box** | Access dies at a planned time — not “when someone remembers” |
| **Incident reference** | Ticket id that ties grant to an outage/IR record |
| **Accelerated approval** | Faster path than routine — still audited |
| **Revocation** | Explicit removal + provisioning, same class as mover cleanup |

- **Wrong way:** Approving break-glass through the exact same unhurried Manager→Owner pace as routine access — a slow “emergency” isn’t one.
- **Wrong way:** Granting without an INC id — auditors can’t tie access to an incident.
- **Wrong way:** Leaving access after the window — temporary access that never expires is permanent access.
- **Wrong way:** Confusing IIQ membership with password custody — vault/PAM owns secrets.

## Intent

- Build (or reuse) a break-glass Bundle distinct from normal Wire/CRM request roles.
- Request it with an incident id through an accelerated but auditable approval.
- Confirm entitlement provisions immediately; Mailpit shows the INC.
- Schedule and execute revocation within a short lab sunset; prove it’s gone on the live target.

## Before you start

- [ ] Lesson 222 approval pattern understood (for contrast)
- [ ] Disposable persona available (`lab.joiner1` / `lab.leaver1` / fresh joiner — not Helen)
- [ ] A live elevated entitlement you can map (e.g. `WIRE_APPR`, elevated Core Banking, or BreakGlass Cloud pack)
- [ ] Mailpit: [http://localhost:8025](http://localhost:8025)
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/223
```

## Do this

### Task 1 — Create or open the break-glass Bundle

**Option A — Create**

1. **Setup → Roles → Create New**
2. Name: `MNB-Bundle-BreakGlass-CoreBanking` (or similar)
3. Type: `it` (or your pack’s emergency type)
4. `requestable=true`
5. Map to a **real** live entitlement not gated like normal Wire Initiator — e.g. elevated `MNB-CoreBanking` access or `WIRE_APPR`
6. Description:

```text
Time-boxed emergency access — INC required, auto-revoke.
```

**Option B — Reuse seed**

Open `MNB-Bundle-BreakGlass-Cloud` if present; confirm it maps to a live entitlement; set requestable if needed.

- **Expect:** Role exists, requestable, mapped to a live target entitlement.

### Task 2 — Pick a short, observable sunset

Choose **5–10 minutes** (not a production 8-hour window).

Write under evidence:

```text
Sunset window: 8 minutes starting at <HH:MM>
Revoke method: manual role removal + provision refresh (or scheduled task if you have one)
```

- **Why:** you need to watch revocation in this lesson.
- **Expect:** window documented before you grant.

### Task 3 — Request with an incident justification

As the disposable persona (or for them via request-on-behalf if your UI allows):

1. **Request Access** → break-glass Bundle  
2. Justification **must** include an incident id:

```text
INC-LAB-001 — emergency Core Banking access during on-call incident
```

3. Submit; note `IdentityRequest` id

- **Expect:** request created with INC in the justification field.

> **Watch out:** Soft business language (“need access for project”) fails this control — rewrite with INC-LAB-001.

### Task 4 — Accelerated approval

Approve fast on purpose:

- Dedicated single-step emergency approval **if** you have one, **or**
- Approve Manager + Owner back-to-back immediately (reuse Lesson 222 chain at emergency speed)

- **Why:** speed with compensating controls (INC + sunset) is the point.
- **Expect:** approved within minutes; timestamps show acceleration vs a leisurely 222 drill.

### Task 5 — Mailpit must show the INC

Open Mailpit; find the grant / assignment / completion mail.

- **Expect:** `INC-LAB-001` visible in subject or body — not generic “access approved” only.

If INC never appears in mail, fix justification/template before calling break-glass auditable.

Screenshot under evidence.

### Task 6 — Prove immediate provision

Re-aggregate the target app. Confirm the disposable user’s account shows the elevated entitlement.

- **Expect:** account link shows the new entitlement right away.

### Task 7 — Plan the revoke (don’t “eventually notice”)

Before the window ends, decide the revoke mechanism:

| Method | When to use |
| --- | --- |
| Manual role removal + Refresh with provisioning | Default for lab |
| Scheduled task / sunset rule | If your build has one |
| Certification revoke | Heavier — optional |

- **Expect:** a deliberate, planned removal written under evidence.

### Task 8 — Execute revoke when the window elapses

1. Wait until sunset (or simulate by executing at T+window)  
2. Remove the break-glass role / entitlement  
3. Refresh with **provisioning** on  
4. Re-aggregate the target  

- **Expect:** entitlement **gone** from the live account.

> **Tip:** Same class of failure as Lesson 218 — role removed in IIQ but target still has it means provisioning/re-agg was skipped.

### Task 9 — IdentityRequest timeline for IR

Open the IdentityRequest (and related work items). Confirm one record shows:

- Incident reference  
- Accelerated approval timestamp  
- Provisioning timestamp  
- Revocation timestamp  

- **Expect:** full timeline you could hand to incident response.

Save under `~/iiq-lab-evidence/sandbox/223/`.

## If it fails

| Symptom | Fix |
| --- | --- |
| No dedicated emergency workflow | Approve both 222 steps immediately — required proof is INC + short sunset + revoke, not a special object |
| Can’t find entitlement to revoke | Capture IdentityRequest id / account link at grant time; check target app account list |
| Role gone, live entitlement stays | Provisioning-enabled refresh + re-aggregation (Lesson 218 class) |
| Mailpit indistinguishable from routine | INC missing from mail — fix justification / EmailTemplate |
| Used Helen/Priya | Stop — use a disposable persona so later certs stay intact |

## You are done when

- [ ] Break-glass granted with INC justification
- [ ] Mailpit notification tied to that INC
- [ ] Entitlement provisioned live
- [ ] Revoked within your sunset window; live target confirms gone

## Control note

- **Control:** Emergency (break-glass) access with mandatory time-box
- **Owner:** Security Ops (approval) + IAM Ops (revocation enforcement)
- **SLA (lab):** 5–10 minute sunset; production windows are typically 4–24 hours with mandatory review
- **Evidence:** `~/iiq-lab-evidence/sandbox/223/` — request justification, Mailpit INC mail, grant/revoke timestamps
- **Out of scope here:** Credential custody / vault checkout (later privileged lesson)

## Quick check

1. What must the justification contain instead of business language? → An incident reference (e.g. `INC-LAB-001`)  
2. What proves this wasn’t just fast routine access? → INC visible in Mailpit + deliberate sunset/revoke  
3. What does IIQ *not* own in break-glass? → Credential custody — PAM/vault holds passwords  
4. Why a 5–10 minute window in lab? → So you can watch revoke happen in-session  

## Feedback

Could you explain break-glass vs routine access in three bullets (justification, speed, sunset)? If revoke cleared the role but not the live entitlement, note whether provisioning was on — that’s the usual miss.

## Navigate

- Previous: [Lesson 222](222-approvals-and-mail.md)
- Next: [Lesson 224](224-sod-wire-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
